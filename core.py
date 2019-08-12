# -*- coding: utf-8 -*-
"""
Created on Thu May  2 03:03:18 2019

@author: MidZik
"""

import gridworld as gw

def create_brain_entity(em: gw.EntityManager, x, y, seed, seq):
    eid = em.create();
    
    pos: gw.Position = em.assign_or_replace_Position(eid)
    pos.x = x
    pos.y = y
    
    em.assign_or_replace_Moveable(eid)
    
    em.assign_or_replace_Scorable(eid)
    
    name = em.assign_or_replace_Name(eid)
    name.major_name = f"I({x},{y})"
    name.minor_name = "Eve"
    
    em.assign_or_replace_SimpleBrain(eid)
    
    em.assign_or_replace_SimpleBrainSeer(eid)
    
    em.assign_or_replace_SimpleBrainMover(eid)
    
    rng = em.assign_or_replace_RNG(eid)
    rng.seed(seed, seq)

def create_predator(em: gw.EntityManager, x, y, seed, seq):
    eid = em.create();
    
    pos: gw.Position = em.assign_or_replace_Position(eid)
    pos.x = x
    pos.y = y
    
    em.assign_or_replace_Moveable(eid)
    
    name = em.assign_or_replace_Name(eid)
    name.major_name = f"I({x},{y})"
    name.minor_name = "PREDATOR"
    
    em.assign_or_replace_RandomMover(eid)
    
    em.assign_or_replace_Predation(eid)
    
    rng = em.assign_or_replace_RNG(eid)
    rng.seed(seed, seq)

def setup_test_em():
    em = gw.EntityManager()
    
    world = em.assign_or_replace_singleton_SWorld()
    world.reset_world(20, 20)
    
    
    rng = em.assign_or_replace_singleton_RNG()
    rng.seed(54321669,12345667)
    
    for i in range(5):
        create_brain_entity(em, i, i, rng.rand(), rng.rand())
        create_predator(em, i + 2, i + 5, rng.rand(), rng.rand())
    
    for i in range(6):
        create_predator(em, i + 5, i + 9, rng.rand(), rng.rand())
    
    # After populating the world, need to refresh the world data
    gw.rebuild_world(em)
    
    return em

def run_perf_test():
    em = setup_test_em()
    
    em.multiupdate(10000)