# -*- coding: utf-8 -*-
"""
Created on Fri May  3 18:24:23 2019

@author: MidZik
"""

import core
import threading

from weakref import WeakValueDictionary
import pyglet
import matplotlib.pyplot as plt

_image_cache = WeakValueDictionary()

_entity_batch = pyglet.graphics.Batch()

_entity_object_map = {}

fps_display = pyglet.clock.ClockDisplay()


class PositionEntityObject:
    def __init__(self, display_data):
        if display_data and display_data.image_path:
            image_path = display_data.image_path
        else:
            image_path = 'assets/DefaultEntity.png'
        
        try:
            image = _image_cache[image_path]
        except LookupError:
            image = pyglet.image.load(image_path)
            image.anchor_x = image.width // 2
            image.anchor_y = image.height // 2
            _image_cache[image_path] = image

        if display_data:
            self.color = display_data.blend
        else:
            self.color = (255, 255, 255)
        self.image = image
        self.sprite = None

        self.position = (0, 0)

    def update_sprite(self):
        if not self.sprite:
            self.sprite = pyglet.sprite.Sprite(self.image, batch=_entity_batch)
            self.sprite.color = self.color

        self.sprite.update(self.position[0] * 40 + 20, self.position[1] * 40 + 20)
    
    def __del__(self):
        if self.sprite:
            self.sprite.delete()
        

class WorldWindow(pyglet.window.Window):
    def __init__(self, em):
        super().__init__(resizable=True, width=800, height=800)
        self.window_lock = threading.Lock()
        self.em = em
        self.update_from_em()
    
    def on_draw(self):
        self.window_lock.acquire()

        for peo in _entity_object_map.values():
            peo.update_sprite()

        self.clear()
        _entity_batch.draw()
        fps_display.draw()

        self.window_lock.release()
    
    def update_from_em(self):
        self.window_lock.acquire()

        matching_eids = self.em.get_matching_entities(["GridWorld::Component::Position"])
        
        for eid in matching_eids:
            position = self.em.get_Position(eid)

            try:
                entity_obj = _entity_object_map[eid]
            except LookupError:
                try:
                    display_data = self.em.get_PyMeta(eid)["DisplayData"]
                except (ValueError, LookupError):
                    display_data = None
                
                entity_obj = PositionEntityObject(display_data)
                _entity_object_map[eid] = entity_obj
            
            entity_obj.position = (position.x, position.y)
        
        # clear out expired sprites
        for eid in list(_entity_object_map.keys()):
            try:
                if not self.em.has_Position(eid):
                    # EID valid, but no longer has position
                    del _entity_object_map[eid]
            except KeyError:
                # EID no longer valid
                del _entity_object_map[eid]

        self.window_lock.release()

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
        
        plt.show()
    
    def process_judgement(self, judgement_stats):
        entity_scores = judgement_stats['entity_scores']
        entity_details_log = judgement_stats['entity_details_log']
        winners = judgement_stats['winners']
        losers = judgement_stats['losers']

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
    test_em = core.setup_test_em()
    test_em_runner = core.EntityManagerRunner(test_em)
    
    # some debug plotting stuff
    plotter = _Plotter(test_em)

    window = WorldWindow(test_em)

    def blah(delta):
        pass

    def on_loop_finished():
        window.update_from_em()

    def on_judgement_occurred(judgement):
        global old_perf
        plotter.process_judgement(judgement)
        plotter.plot_all()

    try:
        pyglet.clock.schedule_interval(blah, 1/30)
        test_em_runner.judgement_occurred.connect(on_judgement_occurred)
        test_em_runner.loop_finished.connect(on_loop_finished)
        test_em_runner.start()
        pyglet.app.run()
    finally:
        pyglet.app.exit()
        window.close()
