# -*- coding: utf-8 -*-
"""
Created on Fri May  3 18:24:23 2019

@author: MidZik
"""

from weakref import WeakValueDictionary
import core
import components as com
from ECS import ECS
import pyglet

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
        super().__init__(resizable=True)
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

if __name__ == '__main__':
    test_em = core.setup_test_em()
    
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
