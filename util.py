# -*- coding: utf-8 -*-
"""
Created on Fri May  3 00:24:45 2019

@author: MidZik
"""
from itertools import tee
import components as com
from ECS.ECS import EntityManager

def mark_component_changed(change_tracker: com.SChangeTracker, component):
    """Marks a component as changed, and adds it to the change tracker queue"""
    if not component._marked_as_changed:
        component._marked_as_changed = True
        change_tracker.changed_components.append(component)

def get_entities_in_radius(world: com.SWorld, x, y, radius):
    """Returns a list of all non-None map data in a given radius of a position.
    
    Data is returned in a strict order: Top to bottom, then left to right."""
    result = []
    
    for cur_y_offset in range(-radius, radius + 1):
        cur_x_radius = radius - abs(cur_y_offset)
        for cur_x_offset in range(-cur_x_radius, cur_x_radius + 1):
            map_data = world.get_map_data(x + cur_x_offset, y + cur_y_offset)
            if map_data is not None:
                result.append((cur_x_offset, cur_y_offset, map_data))
    
    return result

def get_map_data_in_radius(world: com.SWorld, x, y, radius):
    """Returns a list of all map data in a given radius of a position.
    
    Data is returned in a strict order: Top to bottom, then left to right."""
    result = []
    
    for cur_y_offset in range(-radius, radius + 1):
        cur_x_radius = radius - abs(cur_y_offset)
        for cur_x_offset in range(-cur_x_radius, cur_x_radius + 1):
            map_data = world.get_map_data(x + cur_x_offset, y + cur_y_offset)
            result.append((cur_x_offset, cur_y_offset, map_data))
    
    return result

def put_entity_in_world(world: com.SWorld, eid, position: com.Position):
    cur_data = world.get_map_data(position.x, position.y)
    if cur_data is not None:
        raise Exception('Cannot put position int world; world already contains entity at position.')
    
    # normalize the position
    position.x = position.x % world.width
    position.y = position.y % world.height
    world.set_map_data(position.x, position.y, eid)

def can_create_entity(em: EntityManager, com_dict):
    world: com.SWorld = em.scomponents_map[com.SWorld]
    
    try:
        position = com_dict[com.Position]
    except LookupError:
        pass
    else:
        if world.get_map_data(position.x, position.y) is not None:
            return False
    
    return True

def create_entity(em: EntityManager, com_dict) -> int:
    world = em.scomponents_map[com.SWorld]
    eid = em.create_entity()
    for com_class, component in com_dict.items():
        new_com = em.create_component(eid, com_class)
        new_com.copy_state_from(component)
        if isinstance(new_com, com.Position):
            put_entity_in_world(world, eid, new_com)
        new_com._sig_changed.emit()
    
    return eid

def pairwise(iterable):
    """i -> (i0, i1), (i1, i2), (i2, i3), ..."""
    a, b = tee(iterable)
    next(b, None)
    return zip(a, b)