# -*- coding: utf-8 -*-
"""
Created on Wed May  1 17:50:18 2019

@author: MidZik
"""

import weakref
import typing

class Signal:
    __slots__ = ('_slots')
    
    def __init__(self):
        self._slots = []
    
    def connect(self, slot, *binds):
        """
        Connects a method to the signal. Whenever the signal is emitted,
        all connected methods will be fired immediately.
        """
        print(binds)
        self._slots.insert(0, (weakref.ref(slot.__self__), slot.__func__, binds))
    
    def emit(self, *args):
        for i in range(len(self._slots) - 1, -1, -1):
            slot = self._slots[i]
            obj = slot[0]()
            if obj:
                slot[1](obj, *args, *slot[2])
            else:
                # slot object was deleted earlier, remove it.
                del self._slots[i]

class Component:
    __slots__ = ('_marked_as_changed','_sig_changed')
    
    def __init__(self):
        self._marked_as_changed = False
        self._sig_changed = Signal()
    
    # The following functions are quick defaults,
    # if speed is necessary or the state is complex and isn't directly
    # stored in slots, these should be overridden.
    def __getstate__(self):
        return {a: getattr(self, a) for a in self.__slots__ if not a.startswith('_')}
    
    def copy_state_from(self, other):
        for attr in self.__slots__:
            if not attr.startswith('_'):
                setattr(self, attr, getattr(other, attr))

CT = typing.TypeVar('CT', bound=Component)

class EntityManager:
    def __init__(self):
        self.tick = 0
        
        self.in_update = False
        
        self._next_entity_id = 0
        
        self.systems = []
        self.component_maps = {}
        self.scomponents_map = {}
        
        self.sig_update_complete = Signal()
    
    def update(self):
        self.in_update = True
        self.tick += 1
        
        for system in self.systems:
            system(self)
        
        self.in_update = False
        self.sig_update_complete.emit()
    
    def create_component(self, eid, c_class: typing.Type[CT]) -> CT:
        if not c_class in self.component_maps:
            self.component_maps[c_class] = {}
        
        new_com = c_class()
        assert(isinstance(new_com, Component))
        
        self.component_maps[c_class][eid] = new_com
        return new_com
    
    def create_scomponent(self, sc_class: typing.Type[CT]) -> CT:
        new_scom = sc_class()
        assert(isinstance(new_scom, Component))
        
        self.scomponents_map[sc_class] = new_scom
        return new_scom
    
    def create_entity(self) -> int:
        eid = self._next_entity_id
        self._next_entity_id += 1
        return eid
    
    def delete_entity(self, eid):
        # remove all components belonging to the entity
        for cmap in self.component_maps.values():
            try:
                del cmap[eid]
            except LookupError:
                pass
    