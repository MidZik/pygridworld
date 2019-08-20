# -*- coding: utf-8 -*-
"""
Created on Thu May  2 03:03:18 2019

@author: MidZik
"""

import gridworld as gw
import numpy as np


class DisplayData:
    __slots__ = ('image_path', 'blend')

    def __init__(self):
        self.image_path = None
        self.blend = (255, 255, 255)


def create_brain_entity(em: gw.EntityManager, x, y, seed, seq):
    eid = em.create()

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

    meta = em.assign_or_replace_PyMeta(eid)
    display_data = DisplayData()
    display_data.image_path = None
    display_data.blend = (0, 255, 0)
    meta["DisplayData"] = display_data

    return eid


def create_predator(em: gw.EntityManager, x, y, seed, seq):
    eid = em.create()

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

    meta = em.assign_or_replace_PyMeta(eid)
    display_data = DisplayData()
    display_data.image_path = 'assets/PredatorEntity.png'
    display_data.blend = (255, 0, 0)
    meta["DisplayData"] = display_data

    return eid


def mutate_brain(brain: gw.SimpleBrain, rng):
    mutation_chance = brain.child_mutation_chance
    mutation_strength = brain.child_mutation_strength

    synapse_array: np.nparray
    for synapse_array in brain.synapses:
        synapse_unraveled = np.reshape(synapse_array, -1)
        for index in range(len(synapse_unraveled)):
            mutation_occurs = rng.randd() <= mutation_chance
            mutation_amount = (rng.randd() - 0.5) * mutation_strength
            synapse_unraveled[index] += mutation_occurs * mutation_amount

        # after all mutations, clamp synapses so they stay in [-1,1] range
        np.clip(synapse_array, -1.0, 1.0, out=synapse_array)


def judge_and_proliferate(em: gw.EntityManager):
    srng = em.get_singleton_RNG()
    world = em.get_singleton_SWorld()

    # judge stats
    stat_entity_scores = {}
    log_entity_details = {}
    stat_winners = []
    stat_losers = []
    judge_stats = {
        'entity_scores': stat_entity_scores,
        'entity_details_log': log_entity_details,
        'winners': stat_winners,
        'losers': stat_losers
    }

    scorables = []
    for eid in em.get_matching_entities(["GridWorld::Component::Scorable"]):
        scorables.append((eid, em.get_Scorable(eid)))

    sorted_scorables = sorted(scorables, key=lambda x: x[1].score, reverse=True)

    for index, (eid, scorable) in enumerate(sorted_scorables):
        stat_entity_scores[eid] = scorable.score

        try:
            name: gw.Name = em.get_Name(eid)
        except ValueError:
            log_entity_details[eid] = {}
        else:
            log_entity_details[eid] = {
                'maj_name': name.major_name,
                'min_name': name.minor_name
            }

        if index < 6:
            # top 6 scorables are the winners that live and reproduce
            stat_winners.append(eid)

            scorable.score = 0
        else:
            # the remaining entities are losers and will be removed
            # (cannot remove entities here because we are iterating over the
            # sorted scorables, not in storage order)
            stat_losers.append(eid)

    # After all entities are judged, remove the losers.
    for loser_eid in stat_losers:
        try:
            position = em.get_Position(loser_eid)
            world.set_map_data(position.x, position.y, gw.null)
        except ValueError:
            pass

        em.destroy(loser_eid)

    # Entity creation is next, create a list of available spaces to put entities into.
    available_spaces = []
    for x in range(world.width):
        for y in range(world.height):
            if world.get_map_data(x, y) == gw.null:
                available_spaces.append((x, y))

    # create duplicate entities from winners, modifying them slightly
    for parent_eid in stat_winners:
        child_eid = gw.duplicate_entity(em, parent_eid)

        parent_rng = em.get_RNG(parent_eid)

        child_rng = em.get_RNG(child_eid)
        child_rng.seed(parent_rng.randi(), parent_rng.randi())

        new_pos = available_spaces.pop(child_rng.randi() % len(available_spaces))
        position = em.get_Position(child_eid)
        position.x = new_pos[0]
        position.y = new_pos[1]
        world.set_map_data(position.x, position.y, child_eid)

        brain = em.get_SimpleBrain(child_eid)
        mutate_brain(brain, child_rng)

        name = em.get_Name(child_eid)
        name.minor_name = f'T{em.tick}-P{parent_eid}'

    # finally, part of the judge's duty is to queue brand new entities for creation
    for i in range(3):
        eid = em.create()

        new_brain = em.assign_or_replace_SimpleBrain(eid)
        synapse_array: np.nparray
        for synapse_array in new_brain.synapses:
            synapse_unraveled = np.reshape(synapse_array, -1)
            for index in range(len(synapse_unraveled)):
                synapse_unraveled[index] = (srng.randd() < 0.5) * (srng.randd() - 0.5) * 2

        em.assign_or_replace_SimpleBrainSeer(eid)

        em.assign_or_replace_SimpleBrainMover(eid)

        new_pos = available_spaces.pop(srng.randi() % len(available_spaces))
        position = em.assign_or_replace_Position(eid)
        position.x = new_pos[0]
        position.y = new_pos[1]
        world.set_map_data(position.x, position.y, eid)

        em.assign_or_replace_Moveable(eid)

        rng = em.assign_or_replace_RNG(eid)
        rng.seed(srng.randi(), srng.randi())

        em.assign_or_replace_Scorable(eid)

        name = em.assign_or_replace_Name(eid)
        name.major_name = f"T{em.tick}-{i}"
        name.minor_name = f"T{em.tick}-Eve"

    return judge_stats


def setup_test_em():
    em = gw.EntityManager()

    world = em.set_singleton_SWorld()
    world.reset_world(20, 20)

    rng = em.set_singleton_RNG()
    rng.seed(54321669, 12345667)

    for i in range(5):
        create_brain_entity(em, i, i, rng.randi(), rng.randi())
        create_predator(em, i + 2, i + 5, rng.randi(), rng.randi())

    for i in range(6):
        create_predator(em, i + 5, i + 9, rng.randi(), rng.randi())

    # After populating the world, need to refresh the world data
    gw.rebuild_world(em)

    return em


def run_perf_test():
    em = setup_test_em()

    em.multiupdate(10000)


def run_epochs(em, n, on_judge=None):
    for i in range(n):
        gw.multiupdate(em, 25000)
        judge_results = judge_and_proliferate(em)
        if on_judge:
            on_judge(judge_results)
