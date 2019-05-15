# -*- coding: utf-8 -*-
"""
Created on Fri May  3 18:24:23 2019

@author: MidZik
"""

import core
import components as com
from ECS import ECS

from weakref import WeakValueDictionary
import pyglet
import matplotlib.pyplot as plt

_image_cache = WeakValueDictionary()

_entity_batch = pyglet.graphics.Batch()

_entity_object_map = {}

fps_display = pyglet.clock.ClockDisplay()

class PositionEntityObject:
    def __init__(self, display_data: com.DisplayData):
        if display_data and display_data.imagepath:
            imagepath = display_data.imagepath
        else:
            imagepath = 'assets/DefaultEntity.png'
        
        try:
            image = _image_cache[imagepath]
        except LookupError:
            image = pyglet.image.load(imagepath)
            image.anchor_x = image.width // 2
            image.anchor_y = image.height // 2
            _image_cache[imagepath] = image
        
        self.sprite = pyglet.sprite.Sprite(image, batch=_entity_batch)
        if display_data:
            self.sprite.color = display_data.blend
    
    def __del__(self):
        self.sprite.delete()
        

class WorldWindow(pyglet.window.Window):
    def __init__(self, em: ECS.EntityManager):
        super().__init__(resizable=True, width=800, height=800)
        self.em = em
        #em.sig_update_complete.connect(self.on_em_update_complete)
        self.update_from_em()
    
    def on_draw(self):
        self.clear()
        _entity_batch.draw()
        fps_display.draw()
    
    def update_from_em(self):
        cmaps = self.em.component_maps
        position_map = cmaps[com.Position]
        display_data_map = cmaps[com.DisplayData]
        
        for eid, position in position_map.items():
            try:
                entity_obj = _entity_object_map[eid]
            except LookupError:
                try:
                    display_data = display_data_map[eid]
                except LookupError:
                    display_data = None
                
                entity_obj = PositionEntityObject(display_data)
                _entity_object_map[eid] = entity_obj
            
            entity_obj.sprite.update(position.x * 40 + 20, position.y * 40 + 20)
        
        # clear out expired sprites
        for eid in list(_entity_object_map.keys()):
            if not eid in position_map:
                del _entity_object_map[eid]

class _Plotter:
    def __init__(self, em: ECS.EntityManager):
        plt.ion()
        self.em = em
        self.fig = plt.figure()
        self.majname_data = {}
        self.pop_plots = {}
        self.tick_data = [0]
        self.winner_mean_score_data = [0]
        self.all_mean_score_data = [0]
        
        plt.subplot(211)
        self.winners_mean_score_plot, = plt.plot(self.tick_data, self.winner_mean_score_data, label='winners')
        self.all_mean_score_plot, = plt.plot(self.tick_data, self.all_mean_score_data, label='all')
        plt.xlabel('Tick')
        plt.ylabel('Score')
        plt.title('Judge Stats')
        
        self.log_pop_counts(em)
        self.plot_pop_counts()
        
        plt.show()
    
    def on_event(self, event_data):
        name = event_data[0]
        
        if name == 'judgement':
            details = event_data[1]
            entity_scores = details['entity_scores']
            entity_details_log = details['entity_details_log']
            winners = details['winners']
            losers = details['losers']
            
            winner_total = sum(entity_scores[eid] for eid in winners)
            loser_total = sum(entity_scores[eid] for eid in losers)
            total = winner_total + loser_total
            
            winner_mean = winner_total / len(winners)
            total_mean = total / len(entity_scores)
            
            self.tick_data.append(self.em.tick)
            self.winner_mean_score_data.append(winner_mean)
            self.all_mean_score_data.append(total_mean)
            
            self.log_pop_counts(self.em)
            
            if self.em.tick % 50000 == 0:
                plt.subplot(211)
                self.winners_mean_score_plot.set_data(self.tick_data, self.winner_mean_score_data)
                self.all_mean_score_plot.set_data(self.tick_data, self.all_mean_score_data)
                
                ax = plt.gca()
                ax.relim()
                ax.autoscale_view()
                
                self.plot_pop_counts()
                
                self.fig.canvas.draw()
                self.fig.canvas.flush_events()
    
    def log_pop_counts(self, em: ECS.EntityManager):
        name_map = em.component_maps[com.Name]
        
        name: com.Name
        for eid, name in name_map.items():
            maj = name.major_name
            
            try:
                x,y = self.majname_data[maj]
            except LookupError:
                x = []
                y = []
                self.majname_data[maj] = (x, y)
            
            if not x or x[-1] != em.tick:
                x.append(em.tick)
                y.append(0)
            
            y[-1] += 1
    
    def plot_pop_counts(self):
        plt.subplot(212)
        for maj, (x, y) in self.majname_data.items():
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

if __name__ == '__main__':
    test_em = core.setup_test_em()
    
    # some debug plotting stuff
    plotter = _Plotter(test_em)
    
    events: com.SEvents = test_em.scomponents_map[com.SEvents]
    events._sig_event.connect(plotter.on_event)
    
    window = WorldWindow(test_em)
    
#    @window.event
#    def on_mouse_press(x, y, button, mods):
#        pass
    
    def test_update(dt):
        core.multiupdate(test_em, 200)
        window.update_from_em()
    try:
        pyglet.clock.schedule(test_update)
        
        pyglet.app.run()
    finally:
        pyglet.clock.unschedule(test_update)
        pyglet.app.exit()
        window.close()
