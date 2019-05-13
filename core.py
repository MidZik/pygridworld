# -*- coding: utf-8 -*-
"""
Created on Thu May  2 03:03:18 2019

@author: MidZik
"""

from ECS import ECS
import systems as sys
import components as com
import util

def create_brain_entity(em: ECS.EntityManager, x, y):
    coms = []
    
    coms.append(com.Moveable())
    coms.append(com.Scorable())
    
    name = com.Name()
    name.major_name = f"I({x},{y})"
    name.minor_name = "Eve"
    coms.append(name)
    
    coms.append(com.SimpleBrain())
    coms.append(com.SimpleBrainMover())
    coms.append(com.SimpleBrainSeer())
    
    display_data = com.DisplayData()
    display_data.imagepath = 'assets/DefaultEntity.png'
    coms.append(display_data)
    
    rng = com.RNG()
    rng.rng.seed(x + y + 65123, x + y + 16384)
    coms.append(rng)
    
    position = com.Position()
    position.x = x
    position.y = y
    coms.append(position)
    
    util.create_entity(em, {type(c): c for c in coms})

def create_predator(em: ECS.EntityManager, x, y):
    coms = []
    
    coms.append(com.Moveable())
    coms.append(com.Predation())
    coms.append(com.RandomMover())
    
    display_data = com.DisplayData()
    display_data.blend = (255, 0, 0)
    display_data.imagepath = 'assets/PredatorEntity.png'
    coms.append(display_data)
    
    rng = com.RNG()
    rng.rng.seed(x + y + 2850, x + y + 75228)
    coms.append(rng)
    
    position = com.Position()
    position.x = x
    position.y = y
    coms.append(position)
    
    util.create_entity(em, {type(c): c for c in coms})

def print_com_state(em: ECS.EntityManager, eid, com_class):
    print(em.component_maps[com_class][eid].__getstate__())

def multiupdate(em, count):
    for i in range(count):
        em.update()

def setup_test_em():
    em = ECS.EntityManager()
    
    em.systems.append(sys.simple_brain_seer_system)
    em.systems.append(sys.simple_brain_calc)
    em.systems.append(sys.simple_brain_mover_system)
    em.systems.append(sys.random_movement_system)
    em.systems.append(sys.movement_system)
    em.systems.append(sys.predation_system)
    em.systems.append(sys.judge_system)
    em.systems.append(sys.child_creation_system)
    em.systems.append(sys.event_system)
    em.systems.append(sys.new_entity_system)
    em.systems.append(sys.change_notification_system)
    
    em.create_scomponent(com.SWorld)
    em.create_scomponent(com.SChangeTracker)
    em.create_scomponent(com.SChildCreation)
    em.create_scomponent(com.SEvents)
    em.create_scomponent(com.SJudge)
    em.create_scomponent(com.SNewEntityQueue)
    srng = em.create_scomponent(com.RNG)
    srng.rng.seed(54321,12345)
    
    for i in range(5):
        create_brain_entity(em, i, i)
        create_predator(em, i + 2, i + 5)
    
    return em

def run_perf_test():
    em = setup_test_em()
    
    multiupdate(em, 10000)