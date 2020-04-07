# -*- coding: utf-8 -*-
"""
Created on Fri May  3 18:24:23 2019

@author: Matt Idzik (MidZik)
"""

from multiprocessing import Process, Pipe
from multiprocessing.connection import Connection
from threading import Thread

from weakref import WeakValueDictionary
import pyglet




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
        self.fps_display = pyglet.clock.ClockDisplay()

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


def window_app(conn: Connection):
    window = WorldWindow()

    def update(dt):
        if conn.poll():
            frame_data = conn.recv()
            conn.send(True)
            window.update_frame_data(frame_data)

    try:
        pyglet.clock.schedule_interval(update, 1 / 30)
        pyglet.app.run()
    finally:
        pyglet.app.exit()
        window.close()
        conn.send(False)


class WorldWindowProcess:
    def __init__(self):
        self._conn, child_conn = Pipe()
        self._process = Process(target=window_app, args=(child_conn,), daemon=True)
        self._continue_frame_data_provider_thread = False
        self._frame_sender_thread: Thread = None

    def _frame_sender_loop(self, frame_data_provider):
        process_conn = self._conn
        frame_data = {}
        gui_requesting_frame = True

        # in case the previous frame request message wasn't consumed,
        # consume it here now
        if process_conn.poll():
            gui_requesting_frame = process_conn.recv()

        while gui_requesting_frame and self._continue_frame_data_provider_thread:
            frame_data_provider(frame_data)
            process_conn.send(frame_data)
            frame_data.clear()
            gui_requesting_frame = process_conn.recv()

    def start_process(self):
        self._process.start()

    def start_frame_sender_thread(self, frame_data_provider):
        self._continue_frame_data_provider_thread = True
        self._frame_sender_thread = Thread(target=self._frame_sender_loop, args=(frame_data_provider,))
        self._frame_sender_thread.start()

    def stop_and_join_frame_data_thread(self):
        self._continue_frame_data_provider_thread = False
        self._frame_sender_thread.join()
