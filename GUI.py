# -*- coding: utf-8 -*-
"""
Created on Fri May  3 18:24:23 2019

@author: MidZik
"""

import core
from core import Signal

from threading import Lock

from collections import defaultdict

from weakref import WeakValueDictionary
import pyglet
import matplotlib.pyplot as plt

_image_cache = WeakValueDictionary()

fps_display = pyglet.clock.ClockDisplay()


class RenderData:
    __slots__ = ('x', 'y', 'image_path', 'color')

    def __init__(self, x, y, image_path, color):
        self.x = x
        self.y = y
        self.image_path = image_path
        self.color = color
        

class WorldWindow(pyglet.window.Window):
    def __init__(self, simulation):
        super().__init__(resizable=True, width=800, height=800)
        self.em = simulation.em
        self._latest_frame_data = {}
        self._sprite_cache = {}
        self._entity_batch = pyglet.graphics.Batch()
        self.update_from_em()
    
    def on_draw(self):
        current_frame_data = self._latest_frame_data
        sprite_cache = self._sprite_cache
        entity_batch = self._entity_batch
        for eid, render_data in current_frame_data.items():
            try:
                sprite = sprite_cache[eid]
            except LookupError:
                image_path = render_data.image_path
                try:
                    image = _image_cache[image_path]
                except LookupError:
                    image = pyglet.image.load(image_path)
                    image.anchor_x = image.width // 2
                    image.anchor_y = image.height // 2
                    _image_cache[image_path] = image
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
        fps_display.draw()
    
    def update_from_em(self):
        matching_eids = self.em.get_matching_entities(["GridWorld::Component::Position"])

        frame_data = {}
        
        for eid in matching_eids:
            position = self.em.get_Position(eid)

            try:
                display_data = self.em.get_PyMeta(eid)["DisplayData"]
                image_path = display_data.image_path or 'assets/DefaultEntity.png'

                color = display_data.blend
            except (ValueError, LookupError):
                image_path = None
                color = (255, 255, 255)

            frame_data[eid] = RenderData(position.x, position.y, image_path, color)

        self._latest_frame_data = frame_data


class PopulationLogger:
    """
    Logs the population counts of each species when evolution occurred.
    """
    def __init__(self, simulation):
        self.population_data = defaultdict(lambda: ([], []))

        self.data_updated = Signal()

        self.simulation = simulation
        simulation.evolution_occurred.connect(self._on_simulation_evolution_occurred)

    def _on_simulation_evolution_occurred(self, log):
        tick = log['tick']
        population_counts = defaultdict(lambda: 0)

        for entity_log in log['entity_details_log'].values():
            major_name = entity_log['maj_name']
            population_counts[major_name] += 1

        for major_name, population_count in population_counts.items():
            data = self.population_data[major_name]
            data[0].append(tick)
            data[1].append(population_count)

        self.data_updated.emit()


class SimulationScoreLogger:
    """
    Logs the score of the simulation when evolution occurred.
    Current score: Average of the top 6 scores.
    """
    def __init__(self, simulation):
        self.simulation_ticks = []
        self.simulation_scores = []

        self.data_updated = Signal()

        self.simulation = simulation
        simulation.evolution_occurred.connect(self._on_simulation_evolution_occurred)

    def _on_simulation_evolution_occurred(self, log):
        tick = log['tick']
        sorted_scores = sorted(log['entity_scores'].values(), reverse=True)

        if len(sorted_scores) < 6:
            return

        simulation_score = sum(sorted_scores[:6]) / 6

        self.simulation_ticks.append(tick)
        self.simulation_scores.append(simulation_score)

        self.data_updated.emit()


global_plt_lock = Lock()


class SimulationFigure:
    def __init__(self, simulation):
        global_plt_lock.acquire()
        self.min_pop_length_to_plot = 10

        self.population_logger = PopulationLogger(simulation)
        self.simulation_score_logger = SimulationScoreLogger(simulation)

        plt.ion()
        self.figure, (self.sim_score_axes, self.pop_axes) = plt.subplots(2, 1)

        self.pop_axes.set_title('Populations')
        self.sim_score_axes.set_title('Simulation Score')

        self.pop_plots = defaultdict(lambda: self.pop_axes.plot([], [])[0])
        self.sim_score_plot = self.sim_score_axes.plot([], [])[0]

        self.population_logger.data_updated.connect(self._on_population_logger_data_updated)
        self.simulation_score_logger.data_updated.connect(self._on_simulation_score_logger_data_updated)
        global_plt_lock.release()

    def _on_population_logger_data_updated(self):
        global_plt_lock.acquire()
        for major_name, (ticks, populations) in self.population_logger.population_data.items():
            if len(ticks) > self.min_pop_length_to_plot:
                self.pop_plots[major_name].set_data(ticks, populations)

        self.pop_axes.relim()
        self.pop_axes.autoscale_view()
        global_plt_lock.release()

    def _on_simulation_score_logger_data_updated(self):
        global_plt_lock.acquire()
        self.sim_score_plot.set_data(
            self.simulation_score_logger.simulation_ticks,
            self.simulation_score_logger.simulation_scores
        )

        self.sim_score_axes.relim()
        self.sim_score_axes.autoscale_view()
        global_plt_lock.release()


def main():
    simulation_threads = [
        core.SimulationThread(core.TestSimulation(999, 999)),
        core.SimulationThread(core.TestSimulation(9999, 9999)),
        core.SimulationThread(core.TestSimulation(99999, 99999))
    ]

    figures = []

    def update(dt):
        pass

    for sim_thread in simulation_threads:
        simulation = sim_thread.simulation
        figures.append(SimulationFigure(simulation))
        window = WorldWindow(simulation)

        def setup_signal_handlers(_simulation, _window):
            def on_update_done():
                _window.update_from_em()

            _simulation.iteration_finished.connect(on_update_done)

        setup_signal_handlers(simulation, window)

    try:
        plt.show()
        pyglet.clock.schedule_interval(update, 1 / 30)

        for sim_thread in simulation_threads:
            sim_thread.start()

        pyglet.app.run()
    finally:
        pyglet.app.exit()
        window.close()


if __name__ == '__main__':
    main()
