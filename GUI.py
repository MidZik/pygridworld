# -*- coding: utf-8 -*-
"""
Created on Fri May  3 18:24:23 2019

@author: MidZik
"""

import core

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
    def __init__(self, em):
        super().__init__(resizable=True, width=800, height=800)
        self.em = em
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


class _Plotter:
    def __init__(self, em):
        plt.ion()
        self.em = em
        self.fig = plt.figure()
        
        self.majname_pop_data = {}
        self.pop_plots = {}
        
        self.majname_median_data = {}
        self.median_plots = {}
        
        self.tick_data = [0]
        self.winner_mean_score_data = [0]
        self.all_mean_score_data = [0]
        
        self.plot_aggregate_scores()
        plt.xlabel('Tick')
        plt.ylabel('Score')
        plt.title('Judge Stats')
        
        self.log_pop_counts(em)
        self.plot_pop_counts()
        
        self.plot_median_scores()
    
    def process_evolution_log(self, evo_log):
        entity_scores = evo_log['entity_scores']
        entity_details_log = evo_log['entity_details_log']
        winners = evo_log['winners']
        losers = evo_log['losers']

        maj_scores = {}

        for eid, score in entity_scores.items():
            maj_name = entity_details_log[eid]['maj_name']
            try:
                maj_score = maj_scores[maj_name]
            except LookupError:
                maj_score = []
                maj_scores[maj_name] = maj_score

            maj_score.append(score)

        for maj_name, maj_score in maj_scores.items():
            maj_sorted_score = sorted(maj_score)
            median = maj_sorted_score[len(maj_sorted_score)//2]

            try:
                x, y = self.majname_median_data[maj_name]
            except LookupError:
                x = []
                y = []
                self.majname_median_data[maj_name] = (x, y)

            x.append(self.em.tick)
            y.append(median)

        winner_total = sum(entity_scores[eid] for eid in winners)
        loser_total = sum(entity_scores[eid] for eid in losers)
        total = winner_total + loser_total

        winner_mean = winner_total / len(winners)
        total_mean = total / len(entity_scores)

        self.tick_data.append(self.em.tick)
        self.winner_mean_score_data.append(winner_mean)
        self.all_mean_score_data.append(total_mean)

        self.log_pop_counts(self.em)

    def log_pop_counts(self, em):
        named_scorables_eids = em.get_matching_entities(["GridWorld::Component::Name", "GridWorld::Component::Scorable"])

        for eid in named_scorables_eids:
            name = em.get_Name(eid)
            maj = name.major_name
            
            try:
                x,y = self.majname_pop_data[maj]
            except LookupError:
                x = []
                y = []
                self.majname_pop_data[maj] = (x, y)
            
            if not x or x[-1] != em.tick:
                x.append(em.tick)
                y.append(0)
            
            y[-1] += 1
    
    def plot_pop_counts(self):
        plt.figure(self.fig.number)
        plt.subplot(222, label="populations")
        for maj, (x, y) in self.majname_pop_data.items():
            # only plot populations that have lived a non-trivial amount of time
            if len(x) >= 10:
                try:
                    plot = self.pop_plots[maj]
                except LookupError:
                    plot, = plt.plot(x, y)
                    self.pop_plots[maj] = plot
                else:
                    plot.set_data(x, y)
        
        ax = plt.gca()
        ax.relim()
        ax.autoscale_view()
    
    def plot_aggregate_scores(self):
        plt.figure(self.fig.number)
        plt.subplot(221, label="scores")
        
        try:
            self.winners_mean_score_plot.set_data(self.tick_data, self.winner_mean_score_data)
            self.all_mean_score_plot.set_data(self.tick_data, self.all_mean_score_data)
        except AttributeError:
            self.winners_mean_score_plot, = plt.plot(self.tick_data, self.winner_mean_score_data, label='winners')
            self.all_mean_score_plot, = plt.plot(self.tick_data, self.all_mean_score_data, label='all')
        
        ax = plt.gca()
        ax.relim()
        ax.autoscale_view()
    
    def plot_median_scores(self):
        plt.figure(self.fig.number)
        plt.subplot(224, label="median scores")
        
        for maj, (x, y) in self.majname_median_data.items():
            # only plot medians that have lived a non-trivial amount of time
            if len(x) >= 10:
                try:
                    plot = self.median_plots[maj]
                except LookupError:
                    plot, = plt.plot(x, y)
                    self.median_plots[maj] = plot
                else:
                    plot.set_data(x, y)
        
        ax = plt.gca()
        ax.relim()
        ax.autoscale_view()

    def plot_all(self):
        self.plot_aggregate_scores()

        self.plot_pop_counts()

        self.plot_median_scores()

        self.fig.canvas.draw()
        self.fig.canvas.flush_events()


if __name__ == '__main__':
    ems = [core.setup_test_em(999, 999), core.setup_test_em(9999, 9999), core.setup_test_em(99999, 99999)]
    collection = core.RunnerCollection(ems)
    import threading
    plot_lock = threading.Lock()

    def update(dt):
        pass

    for runner in collection._runners:
        em = runner.em
        plotter = _Plotter(em)
        window = WorldWindow(em)

        def setup_signal_handlers(r, p, w):
            def on_loop_finished():
                w.update_from_em()

            def on_evolution_occurred(evo_log):
                p.process_evolution_log(evo_log)
                plot_lock.acquire()
                p.plot_all()
                plot_lock.release()

            r.evolution_occurred.connect(on_evolution_occurred)
            r.loop_finished.connect(on_loop_finished)

        setup_signal_handlers(runner, plotter, window)

    try:
        plt.show()
        pyglet.clock.schedule_interval(update, 1 / 30)
        collection.run_until_epoch_async(100)
        pyglet.app.run()
    finally:
        pyglet.app.exit()
        window.close()
