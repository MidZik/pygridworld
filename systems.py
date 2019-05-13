# -*- coding: utf-8 -*-
"""
Created on Tue May  7 04:17:43 2019

@author: MidZik
"""

import components as com
from ECS.ECS import EntityManager
import util

import numpy as np

"""
MOVEMENT SYSTEM
"""

class _MovementInfo:
    def __init__(self):
        self.map_index = None
        self.child_nodes = []
        self.parent_node = None
        self.is_entry_node = False
        self.entity_id = None
        self.entity_position = None
        self.net_force = 0
        self.finalized = False
        self.accepted_child = None

_sign = lambda x: (1, -1)[x < 0]

def movement_system(em: EntityManager):
    world = em.scomponents_map[com.SWorld]
    change_tracker = em.scomponents_map[com.SChangeTracker]
    
    movement_nodes = {}
    movement_entry_nodes = []
    
    cmaps = em.component_maps
    moveable_map = cmaps[com.Moveable]
    position_map = cmaps[com.Position]
    
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

def _add_movement_info(movement_nodes, movement_entry_nodes, eid, world: com.SWorld, com_moveable: com.Moveable, com_position: com.Position):
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
        cur_movement_info = _MovementInfo()
        cur_movement_info.map_index = cur_map_index
        cur_movement_info.entity_id = eid
        movement_nodes[cur_map_index] = cur_movement_info
    
    new_movement_info = None
    if new_map_index in movement_nodes:
        new_movement_info = movement_nodes[cur_map_index]
    else:
        new_movement_info = _MovementInfo()
        new_movement_info.map_index = new_map_index
        new_movement_info.entity_id = world._map[new_map_index]
        movement_nodes[new_map_index] = new_movement_info
        movement_entry_nodes.append(new_movement_info)
        new_movement_info.is_entry_node = True
    
    cur_movement_info.net_force = net_force
    cur_movement_info.entity_position = com_position
    
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

def _traverse_and_resolve_movement(entry_node: _MovementInfo):
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
        previous_cycle_node : _MovementInfo = entry_node
        current_cycle_node : _MovementInfo = entry_node.parent_node
        while not current_cycle_node.finalized:
            current_cycle_node.accepted_child = previous_cycle_node
            current_cycle_node.finalized = True
            
            for child in current_cycle_node.child_nodes:
                if child != previous_cycle_node:
                    traversal_queue.append(child)
            
            previous_cycle_node = current_cycle_node
            current_cycle_node = current_cycle_node.parent_node
    elif entry_node.entity_id != None:
        # reject children case (entity exists and is not moving)
        entry_node.accepted_child = None
        entry_node.finalized = True
        
        for child in entry_node.child_nodes:
            traversal_queue.append(child)
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
            
            traversal_queue.append(child)
        
        entry_node.accepted_child = highest_child
        entry_node.finalized = True
    
    # Normal handling for non-cycle non-entry nodes
    # If the parent node has accepted me, accept the child with the highest force. (If tied, accept none)
    # If the parent node did not accept me, do not accept any child.
    
    while traversal_queue:
        cur_node = traversal_queue.pop(0)
        
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
                
                traversal_queue.append(child)
            
            cur_node.accepted_child = highest_child
            cur_node.finalized = True
        else:
            cur_node.accepted_child = None
            cur_node.finalized = True
            
            for child in cur_node.child_nodes:
                traversal_queue.append(child)

def _traverse_and_execute_movement(world: com.SWorld, change_tracker: com.SChangeTracker, entry_node: _MovementInfo):
    if not entry_node.is_entry_node:
        print('ERR: execution of movement graph did not start from entry node, execution resolution')
        return
    
    cur_node = entry_node
    
    while cur_node.accepted_child != None and world._map[cur_node.map_index] != cur_node.accepted_child.entity_id:
        world._map[cur_node.map_index] = cur_node.accepted_child.entity_id
        cur_node.accepted_child.entity_position.x = world.get_map_index_x(cur_node.map_index)
        cur_node.accepted_child.entity_position.y = world.get_map_index_y(cur_node.map_index)
        
        util.mark_component_changed(change_tracker, cur_node.accepted_child.entity_position)
        
        cur_node = cur_node.accepted_child
    
    # special case: if any nodes were moved, we need to make sure the last node of the tree clears out its position if necessary (since it wasn't iterated over)
    if cur_node.accepted_child == None and cur_node != entry_node:
        world._map[cur_node.map_index] = None


"""
CHANGE NOTIFICATION SYSTEM
"""

def change_notification_system(em: EntityManager):
    change_tracker = em.scomponents_map[com.SChangeTracker]
    
    for component in change_tracker.changed_components:
        if component._marked_as_changed:
            component._sig_changed.emit()
            component._marked_as_changed = False
    
    change_tracker.changed_components.clear()


"""
EVENT SYSTEM
"""

def event_system(em: EntityManager):
    events = em.scomponents_map[com.SEvents]
    queue = events.queue
    events.queue = []
    
    for event in queue:
        events._sig_event.emit(event)


"""
NEW ENTITY SYSTEM
"""

def new_entity_system(em: EntityManager):
    new_entity_queue: com.SNewEntityQueue = em.scomponents_map[com.SNewEntityQueue]
    world: com.SWorld = em.scomponents_map[com.SWorld]
    
    queue = new_entity_queue.queue
    new_entity_queue.queue = []
    
    pending_add_queue = []
    visited_positions = {}
    
    for com_dict in queue:
        if not util.can_create_entity(em, com_dict):
            continue
        
        try:
            position = com_dict[com.Position]
        except LookupError:
            pass
        else:
            map_index = world.get_map_index(position.x, position.y)
            
            if map_index in visited_positions:
                visited_positions[map_index] = False # not valid anymore
                continue
            else:
                visited_positions[map_index] = True # valid for now
        
        pending_add_queue.append(com_dict)
    
    for com_dict in pending_add_queue:
        try:
            position = com_dict[com.Position]
        except LookupError:
            pass
        else:
            map_index = world.get_map_index(position.x, position.y)
            
            if visited_positions[map_index] == False:
                # multiple entities tried to get added to this position,
                # so instead none of them get added
                continue
        
        util.create_entity(em, com_dict)


"""
RANDOM MOVEMENT SYSTEM
"""

def random_movement_system(em: EntityManager):
    random_mover_map = em.component_maps[com.RandomMover]
    moveable_map = em.component_maps[com.Moveable]
    rng_map = em.component_maps[com.RNG]
    
    for eid, random_mover in random_mover_map.items():
        try:
            moveable = moveable_map[eid]
            rng = rng_map[eid].rng
            
            if rng.randi() % 2 == 0:
                # move vertically
                moveable.y_force += rng.randi() % 7 - 3
            else:
                # move horizontally
                moveable.x_force += rng.randi() % 7 - 3
        except LookupError:
            print('WARN: Random Mover missing required components')
            continue

"""
PREDATIION SYSTEM
"""

def predation_system(em: EntityManager):
    world: com.SWorld = em.scomponents_map[com.SWorld]
    change_tracker: com.SChangeTracker = em.scomponents_map[com.SChangeTracker]
    events: com.SEvents = em.scomponents_map[com.SEvents]
    
    cmaps = em.component_maps
    predation_map = cmaps[com.Predation]
    position_map = cmaps[com.Position]
    rng_map = cmaps[com.RNG]
    scorable_map = cmaps[com.Scorable]
    
    predation: com.Predation
    for eid, predation in predation_map.items():
        try:
            position = position_map[eid]
            rng = rng_map[eid].rng
        except LookupError:
            continue
        
        # this is to limit how quickly a predator can eat.
        # if it predated recently, there is some time before it eats again
        if em.tick < predation.no_predation_until_tick:
            continue
            
        # get all adjacent scorable entities in the world
        scorables_found = []
        predate_event_locations = []
        nearby_entities = util.get_entities_in_radius(world, position.x, position.y, 1)
        
        nearby_nonself_entities = [(relx, rely, e) for (relx, rely, e) in nearby_entities if relx != 0 or rely != 0]
        
        for relx, rely, near_eid in nearby_nonself_entities:
            try:
                scorables_found.append(scorable_map[near_eid])
            except LookupError:
                pass
            else:
                event_location = (relx/2 + position.x,
                                  rely/2 + position.y)
                predate_event_locations.append(event_location)
        
        # pick a random adjacent scorable and reduce its score by 1
        # also don't predate for a bit
        if scorables_found:
            random_index = rng.randi() % len(scorables_found)
            scorable = scorables_found[random_index]
            scorable.score -= 1
            util.mark_component_changed(change_tracker, scorable)
            predation.no_predation_until_tick = em.tick + 20
            events.queue_event("predation", {"location": predate_event_locations[random_index]}, 0) 

"""
SIMPLE BRAIN SEER SYSTEM
"""

def simple_brain_seer_system(em: EntityManager):
    world: com.SWorld = em.scomponents_map[com.SWorld]
    
    cmaps = em.component_maps
    simple_brain_seer_map = cmaps[com.SimpleBrainSeer]
    simple_brain_map = cmaps[com.SimpleBrain]
    predation_map = cmaps[com.Predation]
    position_map = cmaps[com.Position]
    
    seer: com.SimpleBrainSeer
    for eid, seer in simple_brain_seer_map.items():
        try:
            brain: com.SimpleBrain = simple_brain_map[eid]
            position: com.Position = position_map[eid]
        except LookupError:
            continue
        
        input_neurons = brain.neurons[0]
        
        cur_neuron_offset = seer.neuron_offset
        map_data = util.get_map_data_in_radius(world, position.x, position.y, 2)
        for _, _, seen_eid in map_data:
            if seen_eid is None:
                # nothing seen
                input_neurons[0, cur_neuron_offset] = 0
                input_neurons[0, cur_neuron_offset + 1] = 0
            elif seen_eid in predation_map:
                # predator seen
                input_neurons[0, cur_neuron_offset] = 1
                input_neurons[0, cur_neuron_offset + 1] = 0
            else:
                # non-predator seen
                input_neurons[0, cur_neuron_offset] = 0
                input_neurons[0, cur_neuron_offset + 1] = 1
            cur_neuron_offset += 2 # iterate in sets of 2 (predator+nonpredator)

"""
SIMPLE BRAIN MOVER SYSTEM
"""

def simple_brain_mover_system(em: EntityManager):
    cmaps = em.component_maps
    simple_brain_map = cmaps[com.SimpleBrain]
    simple_brain_mover_map = cmaps[com.SimpleBrainMover]
    moveable_map = cmaps[com.Moveable]
    
    mover: com.SimpleBrainMover
    for eid, mover in simple_brain_mover_map.items():
        try:
            brain: com.SimpleBrain = simple_brain_map[eid]
            moveable: com.Moveable = moveable_map[eid]
        except LookupError:
            print('WARN: SimpleBrainMover component missing other required components')
            continue
        
        neuron_offset = mover.neuron_offset
        output_neurons = brain.neurons[-1]
        
        moveable.x_force += int(output_neurons[0, neuron_offset])
        moveable.x_force -= int(output_neurons[0, neuron_offset + 1])
        moveable.y_force += int(output_neurons[0, neuron_offset + 2])
        moveable.y_force -= int(output_neurons[0, neuron_offset + 3])

"""
SIMPLE BRAIN CALC SYSTEM
"""

def simple_brain_calc(em: EntityManager):
    change_tracker: com.SChangeTracker = em.scomponents_map[com.SChangeTracker]
    
    brain: com.SimpleBrain
    for eid, brain in em.component_maps[com.SimpleBrain].items():
        neurons_list = brain.neurons
        synapses_list = brain.synapses
        for index, synapses in enumerate(synapses_list):
            input_neurons = neurons_list[index]
            input_neurons[input_neurons < 0] = 0 # relu, assign 0 to all positions less than 0
            has_bias = (index != len(synapses_list) - 1)
            np.matmul(input_neurons, synapses_list[index], out=neurons_list[index+1][0,has_bias:])
        
        # for this calc, apply relu to the output as well
        output_neurons = neurons_list[-1]
        output_neurons[output_neurons < 0] = 0
        
        util.mark_component_changed(change_tracker, brain)

"""
CHILD CREATION SYSTEM
"""

def child_creation_system(em: EntityManager):
    new_entity_queue = em.scomponents_map[com.SNewEntityQueue].queue
    
    child_creation: com.SChildCreation = em.scomponents_map[com.SChildCreation]
    child_creators = child_creation.pending_child_creators
    child_creation.pending_child_creators = []
    
    cmaps = em.component_maps
    rng_map = cmaps[com.RNG]
    
    for eid in child_creators:
        try:
            creator_rng = rng_map[eid].rng
        except LookupError:
            print('WARN: Child creators are currently required to have an RNG component.')
            continue
        
        com_dict = {}
        for com_class, cmap in cmaps.items():
            try:
                creator_com = cmap[eid]
            except LookupError:
                continue
            
            child_com: com.Component = com_class()
            child_com.copy_state_from(creator_com)
            com_dict[com_class] = child_com
        
        # we have an exact copy of the child creator, now modify the components
        # as appropriate
        
        # RNG state is changed based on creator's rng
        # NOTE: Child creators are currently required to have an RNG component.
        child_rng_com = com_dict[com.RNG]
        child_rng = child_rng_com.rng
        child_rng.seed(creator_rng.randi(), creator_rng.randi())
        
        try:
            position = com_dict[com.Position]
        except LookupError:
            pass
        else:
            position.x = child_rng.randi()
            position.y = child_rng.randi()
        
        try:
            name: com.Name = com_dict[com.Name]
        except LookupError:
            pass
        else:
            name.minor_name = f'T{em.tick}-P{eid}'
        
        try:
            brain = com_dict[com.SimpleBrain]
        except LookupError:
            pass
        else:
            # mutate the brain
            mutation_chance = brain.child_mutation_chance
            mutation_strength = brain.child_mutation_strength
            
            synapse_array: np.nparray
            for synapse_array in brain.synapses:
                synapse_unravled = np.reshape(synapse_array, -1)
                for index in range(len(synapse_unravled)):
                    mutation_occurs = child_rng.randd() <= mutation_chance
                    mutation_amount = (child_rng.randd() - 0.5) * mutation_strength
                    synapse_unravled[index] += mutation_occurs * mutation_amount
                
                # after all mutations, clamp synapses so they stay in [-1,1] range
                np.clip(synapse_array, -1.0, 1.0, out=synapse_array)
        
        new_entity_queue.append(com_dict)

"""
JUDGE SYSTEM
Makes changes to the world based on entity scores.
(Kills poor performers, expands good performers, etc)
"""

def judge_system(em: EntityManager):
    judge: com.SJudge = em.scomponents_map[com.SJudge]
    
    if em.tick < judge.next_judgement_tick:
        return
    
    judge.next_judgement_tick = em.tick + judge.ticks_between_judgements
    
    srng = em.scomponents_map[com.RNG].rng
    world: com.SWorld = em.scomponents_map[com.SWorld]
    child_creation: com.SChildCreation = em.scomponents_map[com.SChildCreation]
    new_entity_queue: com.SNewEntityQueue = em.scomponents_map[com.SNewEntityQueue]
    events: com.SEvents = em.scomponents_map[com.SEvents]
    
    cmaps = em.component_maps
    position_map = cmaps[com.Position]
    
    # judge stats
    stat_entity_scores = {}
    stat_winners = []
    stat_losers= []
    judge_stats = {
            'entity_scores': stat_entity_scores,
            'winners': stat_winners,
            'losers': stat_losers
            }
    
    scorables = []
    
    scorable: com.Scorable
    for eid, scorable in cmaps[com.Scorable].items():
        scorables.append((eid, scorable))
    
    sorted_scorables = sorted(scorables, key=lambda x: x[1].score, reverse=True)
    
    for index, (eid, scorable) in enumerate(sorted_scorables):
        stat_entity_scores[eid] = scorable.score
        
        if index < 4:
            # top 4 scorables are the winners that live and reproduce
            stat_winners.append(eid)
            
            child_creation.pending_child_creators.append(eid)
            
            scorable.score = 0
        else:
            # the remaining entities are losers and are immediately removed from the world
            stat_losers.append(eid)
            
            # need to manually remove loser from map cache
            position = position_map[eid]
            world.set_map_data(position.x, position.y, None)
            
            em.delete_entity(eid)
    
    # finally, part of the judge's duty is to queue brand new entities for creation
    for i in range(2):
        new_entity = {}
        
        # current brain creation scheme: give all synapses a random value between -1 and 1.
        new_brain = com.SimpleBrain()
        synapse_array: np.nparray
        for synapse_array in new_brain.synapses:
            synapse_unravled = np.reshape(synapse_array, -1)
            for index in range(len(synapse_unravled)):
                synapse_unravled[index] = (srng.randd() - 0.5) * 2
        new_entity[com.SimpleBrain] = new_brain
        
        new_entity[com.SimpleBrainMover] = com.SimpleBrainMover()
        
        new_entity[com.SimpleBrainSeer] = com.SimpleBrainSeer()
        
        new_pos = com.Position()
        new_pos.x = srng.randi()
        new_pos.y = srng.randi()
        new_entity[com.Position] = new_pos
        
        new_entity[com.Moveable] = com.Moveable()
        
        new_rng = com.RNG()
        new_rng.rng.seed(srng.randi(), srng.randi())
        new_entity[com.RNG] = new_rng
        
        new_display_data = com.DisplayData()
        new_display_data.blend = (srng.randi() % 256, srng.randi() % 256, srng.randi() % 256)
        new_entity[com.DisplayData] = new_display_data
        
        new_entity[com.Scorable] = com.Scorable()
        
        new_name = com.Name()
        new_name.major_name = f"T{em.tick}-{i}"
        new_name.minor_name = f"T{em.tick}-Eve"
        new_entity[com.Name] = new_name
        
        new_entity_queue.queue.append(new_entity)
    
    events.queue_event('judgement', judge_stats, 1)
