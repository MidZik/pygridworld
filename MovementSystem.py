# -*- coding: utf-8 -*-
"""
Created on Thu May  2 17:30:46 2019

@author: MidZik
"""

from ECS import ECS
import Core
from Util import ChangeUtil

class MovementInfo:
    def __init__(self):
        self.map_index = None
        self.child_nodes = []
        self.parent_node = None
        self.is_entry_node = False
        self.entity_id = None
        self.entity_pos = None
        self.net_force = 0
        self.finalized = False
        self.accepted_child = None

_sign = lambda x: (1, -1)[x < 0]

def movement_system(em: ECS.EntityManager):
    world = em.get_scomponent(Core.SComWorld)
    change_tracker = em.get_scomponent(Core.SComChangeTracker)
    
    movement_nodes = {}
    movement_entry_nodes = []
    
    cmaps = em.component_maps
    moveable_map = cmaps[Core.ComMoveable]
    position_map = cmaps[Core.ComPosition]
    
    for eid, moveable in moveable_map.items():
        try:
            position = position_map[eid]
        except LookupError:
            continue
        
        _add_movement_info(movement_nodes, movement_entry_nodes, eid, world, moveable, position)
    
    for entry_node in movement_entry_nodes:
        _traverse_and_resolve_movement(entry_node)
    
    for entry_node in movement_entry_nodes:
        _traverse_and_execute_movement(world, change_tracker, entry_node)
    
    for moveable in moveable_map.values():
        moveable.x_force = 0
        moveable.y_force = 0

def _add_movement_info(movement_nodes, movement_entry_nodes, eid, world: Core.SComWorld, com_moveable: Core.ComMoveable, com_position: Core.ComPosition):
    abs_x_force = abs(com_moveable.x_force)
    abs_y_force = abs(com_moveable.y_force)
    
    if abs_x_force - abs_y_force == 0:
        return
    
    cancellation = min(abs_x_force, abs_y_force)
    
    true_x_force = (abs_x_force - cancellation) * _sign(com_moveable.x_force)
    true_y_force = (abs_y_force - cancellation) * _sign(com_moveable.y_force)
    
    new_x = com_position.x
    new_y = com_position.y
    net_force = 0
    if true_x_force > 0:
        new_x += 1
        net_force = true_x_force
    elif true_x_force < 0:
        new_x -= 1
        net_force = -true_x_force
    elif true_y_force > 0:
        new_y += 1
        net_force = true_y_force
    elif true_y_force < 0:
        new_y -= 1
        net_force = -true_y_force
    
    cur_map_index = world.get_map_index(com_position.x, com_position.y)
    new_map_index = world.get_map_index(new_x, new_y)
    
    cur_movement_info = None
    if cur_map_index in movement_nodes:
        cur_movement_info = movement_nodes[cur_map_index]
    else:
        cur_movement_info = MovementInfo()
        cur_movement_info.map_index = cur_map_index
        cur_movement_info.entity_id = eid
        movement_nodes[cur_map_index] = cur_movement_info
    
    new_movement_info = None
    if new_map_index in movement_nodes:
        new_movement_info = movement_nodes[cur_map_index]
    else:
        new_movement_info = MovementInfo()
        new_movement_info.map_index = new_map_index
        new_movement_info.entity_id = world._map[new_map_index]
        movement_nodes[new_map_index] = new_movement_info
        movement_entry_nodes.append(new_movement_info)
        new_movement_info.is_entry_node = True
    
    cur_movement_info.net_force = net_force
    cur_movement_info.entity_pos = com_position
    
    if cur_movement_info.parent_node != new_movement_info:
        # erase self from old parent, if we have one
        if cur_movement_info.parent_node != None:
            cur_movement_info.parent_node.child_nodes.remove(cur_movement_info)
        
        cur_movement_info.parent_node = new_movement_info
        new_movement_info.child_nodes.append(cur_movement_info)
    
    # Verify that our graph has just one entry node by searching for an entry node among our parents.
    search_node = cur_movement_info.parent_node
    
    while not search_node.is_entry_node and search_node != cur_movement_info:
        search_node = search_node.parent_node
    
    if search_node != cur_movement_info and cur_movement_info.is_entry_node:
        # found an entry node that is not ourself, and we used to be an entry node,
        # so remove ourselves as an entry node
        cur_movement_info.is_entry_node = False
        movement_entry_nodes.remove(cur_movement_info)
    elif search_node == cur_movement_info and not cur_movement_info.is_entry_node:
        # we did not find an entry node among our parents and arrived back to ourselves, and we are not an entry node,
        # which means we created a cycle with no entry node. So we make ourselves into an entry node.
        cur_movement_info.is_entry_node = True
        movement_entry_nodes.append(cur_movement_info)

def _traverse_and_resolve_movement(entry_node: MovementInfo):
    if not entry_node.is_entry_node:
        print('ERR: resolution of movement graph did not start from entry node, halting resolution')
        return
    
    traversal_queue = []
    
    # special handling for the entry node
    # If it has a parent, this indicates a cycle. Traverse the PARENTS until we return to the entry node, accepting the previous node in the cycle.
    #         Children outside of the cycle will be rejected, regardless if they had a higher force value, because a cycle is "accepted" by all parties.
    # If it has no entity, it will accept the child with the highest force. (If tied, accepts none)
    # If it has an entity (and no parent), it will not accept any child.
    
    if entry_node.parent_node != None:
        # cycle case
        previous_cycle_node : MovementInfo = entry_node
        current_cycle_node : MovementInfo = entry_node.parent_node
        while not current_cycle_node.finalized:
            current_cycle_node.accepted_child = previous_cycle_node
            current_cycle_node.finalized = True
            
            for child in current_cycle_node.child_nodes:
                if child != previous_cycle_node:
                    traversal_queue.push_back(child)
            
            previous_cycle_node = current_cycle_node
            current_cycle_node = current_cycle_node.parent_node
    elif entry_node.entity_id != None:
        # reject children case (entity exists and is not moving)
        entry_node.accepted_child = None
        entry_node.finalized = True
        
        for child in entry_node.child_nodes:
            traversal_queue.push_back(child)
    else:
        # accept most forceful child case (or none if there is a tie)
        highest_force = -1
        highest_child = None
        
        for child in entry_node.child_nodes:
            if child.net_force > highest_force:
                highest_child = child
                highest_force = child.net_force
            elif child.net_force == highest_force:
                highest_child = None
            
            traversal_queue.push_back(child)
        
        entry_node.accepted_child = highest_child
        entry_node.finalized = True
    
    # Normal handling for non-cycle non-entry nodes
    # If the parent node has accepted me, accept the child with the highest force. (If tied, accept none)
    # If the parent node did not accept me, do not accept any child.
    
    while not traversal_queue.empty():
        cur_node = traversal_queue.pop_front()
        
        # sanity check, may not be necessary
        if cur_node.finalized:
            print('WARN: Sanity check 1 failed during movement graph resolution')
            continue
        
        if cur_node.parent_node.accepted_child == cur_node:
            highest_force = -1
            highest_child = None
            
            for child in cur_node.child_nodes:
                if child.net_force > highest_force:
                    highest_child = child
                    highest_force = child.net_force
                elif child.net_force == highest_force:
                    highest_child = None
                
                traversal_queue.push_back(child)
            
            cur_node.accepted_child = highest_child
            cur_node.finalized = True
        else:
            cur_node.accepted_child = None
            cur_node.finalized = True
            
            for child in cur_node.child_nodes:
                traversal_queue.push_back(child)

def _traverse_and_execute_movement(world: Core.SComWorld, change_tracker: Core.SComChangeTracker, entry_node: MovementInfo):
    if not entry_node.is_entry_node:
        print('ERR: execution of movement graph did not start from entry node, execution resolution')
        return
    
    cur_node = entry_node
    
    while cur_node.accepted_child != None and world.map[cur_node.map_index] != cur_node.accepted_child.entity_id:
        world.map[cur_node.map_index] = cur_node.accepted_child.entity_id
        cur_node.accepted_child.entity_position.x = world.get_map_index_x(cur_node.map_index)
        cur_node.accepted_child.entity_position.y = world.get_map_index_y(cur_node.map_index)
        
        ChangeUtil.mark_component_changed(change_tracker, cur_node.accepted_child.entity_position)
        
        cur_node = cur_node.accepted_child
    
    # special case: if any nodes were moved, we need to make sure the last node of the tree clears out its position if necessary (since it wasn't iterated over)
    if cur_node.accepted_child == None and cur_node != entry_node:
        world.map[cur_node.map_index] = None