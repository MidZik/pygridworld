# -*- coding: utf-8 -*-
"""
Created on Fri May  3 18:24:23 2019

@author: Matt Idzik (MidZik)
"""
from simma.simrunner import SimulationClient, RpcError
import json
from multiprocessing import Process
from weakref import WeakValueDictionary
import pyglet


def _get_asset_path(asset):
    return "../assets/" + asset


class RenderData:
    __slots__ = ('x', 'y', 'image_path', 'color')

    def __init__(self, x, y, image_path, color):
        self.x = x
        self.y = y
        self.image_path = image_path
        self.color = color
        

class WorldWindow(pyglet.window.Window):
    def __init__(self):
        super().__init__(resizable=True, width=800, height=800)
        self._latest_frame_data = {}
        self._sprite_cache = {}
        self._image_cache = WeakValueDictionary()
        self._entity_batch = pyglet.graphics.Batch()
        self.fps_display = pyglet.window.FPSDisplay(self)

    def update_frame_data(self, frame_data):
        self._latest_frame_data = frame_data
    
    def on_draw(self):
        current_frame_data = self._latest_frame_data
        sprite_cache = self._sprite_cache
        image_cache = self._image_cache
        entity_batch = self._entity_batch
        for eid, render_data in current_frame_data.items():
            try:
                sprite = sprite_cache[eid]
            except LookupError:
                image_path = render_data.image_path
                try:
                    image = image_cache[image_path]
                except LookupError:
                    image = pyglet.image.load(image_path)
                    image.anchor_x = image.width // 2
                    image.anchor_y = image.height // 2
                    image_cache[image_path] = image
                sprite = pyglet.sprite.Sprite(image, batch=entity_batch)
                sprite.color = render_data.color
                sprite_cache[eid] = sprite

            sprite.update(render_data.x * 40 + 20, render_data.y * 40 + 20)

        for eid, sprite in [(eid, sprite) for eid, sprite in sprite_cache.items() if eid not in current_frame_data]:
            # Delete all sprites that represent deleted entities
            sprite.delete()
            del sprite_cache[eid]

        self.clear()
        entity_batch.draw()
        self.fps_display.draw()


def window_app(address, token):
    sim_client = SimulationClient(SimulationClient.make_channel(address), token)

    window = WorldWindow()

    def update(dt):
        try:
            state_json, _ = sim_client.get_state_json()
            state_obj = json.loads(state_json)
        except RpcError:
            # grpc doesn't provide easy-to-use exceptions so for now just handle all grpc errors cleanly
            window.close()
            return
        frame_data = {}

        predators = set()
        for pred in state_obj["components"]["Predation"]:
            predators.add(pred["EID"])

        for pos in state_obj["components"]["Position"]:
            eid = pos["EID"]
            pos_com = pos["Com"]
            if eid in predators:
                frame_data[eid] = RenderData(
                    pos_com["x"],
                    pos_com["y"],
                    _get_asset_path('PredatorEntity.png'),
                    (255, 0, 0))
            else:
                frame_data[eid] = RenderData(
                    pos_com["x"],
                    pos_com["y"],
                    _get_asset_path('DefaultEntity.png'),
                    (0, 200, 50))
        window.update_frame_data(frame_data)

    try:
        pyglet.clock.schedule_interval(update, 1 / 20)
        pyglet.app.run()
    finally:
        pyglet.app.exit()
        window.close()


def create_gui_process(address, token):
    return Process(target=window_app, args=(address, token), daemon=True)
