# -*- coding: utf-8 -*-
"""
Created on Thu May  2 03:03:18 2019

@author: Matt Idzik (MidZik)
"""

import gridworld as gw
import numpy as np
import threading
import weakref
import inspect


class DisplayData:
    __slots__ = ('image_path', 'blend')

    def __init__(self):
        self.image_path = None
        self.blend = (255, 255, 255)


class Signal:
    __slots__ = ('_slots',)

    def __init__(self):
        self._slots = []

    def connect(self, slot, *binds):
        """
        Connects a method or function to the signal. Whenever the signal is emitted,
        all connected methods will be fired immediately.
        """
        if inspect.ismethod(slot):
            # Bound method case
            self._slots.insert(0, (weakref.ref(slot.__self__), slot.__func__, binds))
        else:
            # Function/callable case
            self._slots.insert(0, (None, slot, binds))

    def disconnect(self, slot):
        i = self._find_slot(slot)
        del self._slots[i]

    def emit(self, *args):
        for i in range(len(self._slots) - 1, -1, -1):
            slot = self._slots[i]
            ref = slot[0]
            func = slot[1]
            binds = slot[2]
            if ref:
                # Bound method case
                obj = ref()
                if obj:
                    func(obj, *args, *binds)
                else:
                    # slot object was deleted earlier, remove it.
                    del self._slots[i]
            else:
                # Function case
                func(*args, *binds)

    def _find_slot(self, slot):
        if inspect.ismethod(slot):
            # Bound method case
            expected_self = slot.__self__
            expected_func = slot.__func__
        else:
            # Function/callable case
            expected_self = None
            expected_func = slot

        for i, slot2 in enumerate(self._slots):
            found_self = slot2[0]
            if found_self:
                # If not none, this is a weakref that needs dereferencing
                found_self = found_self()

            found_func = slot2[1]

            if found_self is expected_self and found_func is expected_func:
                return i

        raise ValueError("Unable to find a connection with the given slot.")


class TestSimulation:
    def __init__(self, init_state=123456789, init_seq=23456789, config={}):
        self.em = None
        self.seed = None
        self.config = dict(config)

        self.evolution_occurred = Signal()
        self.iteration_finished = Signal()

        self.ticks_between_evolutions = 25000

        self.reset_from_seed(init_state, init_seq)

    def reset_from_seed(self, init_state, init_seq):
        em = gw.EntityManager()

        world = em.set_singleton_SWorld()
        world.reset_world(20, 20)

        rng = em.set_singleton_RNG()
        rng.seed(init_state, init_seq)

        for i in range(5):
            self._create_brain_entity(em, i, i, rng.randi(), rng.randi(), self.config)
            self._create_predator_entity(em, i + 2, i + 5, rng.randi(), rng.randi())

        for i in range(6):
            self._create_predator_entity(em, i + 5, i + 9, rng.randi(), rng.randi())

        # After populating the world, need to refresh the world data
        gw.rebuild_world(em)

        self.em = em
        self.seed = (init_state, init_seq)

    def simulate(self, ticks, max_ticks_per_update=25000):
        em = self.em
        run_until_tick = em.tick + ticks
        while em.tick < run_until_tick:
            ticks_until_evolution = self.ticks_between_evolutions - em.tick % self.ticks_between_evolutions
            ticks_to_do = min(run_until_tick - em.tick, ticks_until_evolution, max_ticks_per_update)
            gw.multiupdate(em, ticks_to_do)
            if em.tick % self.ticks_between_evolutions == 0:
                evolution_log = self._log_and_evolve(em, self.config)
                self.evolution_occurred.emit(evolution_log)
            self.iteration_finished.emit()

    @staticmethod
    def _create_brain_entity(em: gw.EntityManager, x, y, seed, seq, config):
        eid = em.create()

        pos: gw.Position = em.assign_or_replace_Position(eid)
        pos.x = x
        pos.y = y

        em.assign_or_replace_Moveable(eid)

        em.assign_or_replace_Scorable(eid)

        name = em.assign_or_replace_Name(eid)
        name.major_name = f"I({x},{y})"
        name.minor_name = "Eve"

        brain = em.assign_or_replace_SimpleBrain(eid)
        brain.child_mutation_chance = config.get('child_mutation_chance', 0.5)
        brain.child_mutation_strength = config.get('child_mutation_strength', 0.2)

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

    @staticmethod
    def _create_predator_entity(em: gw.EntityManager, x, y, seed, seq):
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

    @staticmethod
    def _mutate_brain(brain: gw.SimpleBrain, rng):
        mutation_chance = brain.child_mutation_chance
        mutation_strength = brain.child_mutation_strength

        synapse_array: np.ndarray
        for synapse_array in brain.synapses:
            synapse_unraveled = np.reshape(synapse_array, -1, order='F')
            for index in range(len(synapse_unraveled)):
                mutation_occurs = rng.randd() <= mutation_chance
                mutation_amount = (rng.randd() - 0.5) * mutation_strength
                synapse_unraveled[index] += mutation_occurs * mutation_amount

            # after all mutations, clamp synapses so they stay in [-1,1] range
            np.clip(synapse_array, -1.0, 1.0, out=synapse_array)

    @staticmethod
    def _log_and_evolve(em: gw.EntityManager, config):
        srng = em.get_singleton_RNG()
        world = em.get_singleton_SWorld()

        stat_entity_scores = {}
        log_entity_details = {}
        stat_winners = []
        stat_losers = []
        log = {
            'tick': em.tick,
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
            TestSimulation._mutate_brain(brain, child_rng)

            name = em.get_Name(child_eid)
            name.minor_name = f'T{em.tick}-P{parent_eid}'

        # finally, part of the judge's duty is to queue brand new entities for creation
        for i in range(3):
            eid = em.create()

            new_brain = em.assign_or_replace_SimpleBrain(eid)
            new_brain.child_mutation_chance = config.get('child_mutation_chance', 0.5)
            new_brain.child_mutation_strength = config.get('child_mutation_strength', 0.2)
            synapse_array: np.ndarray
            for synapse_array in new_brain.synapses:
                synapse_unraveled = np.reshape(synapse_array, -1, order='F')
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

            meta = em.assign_or_replace_PyMeta(eid)
            display_data = DisplayData()
            display_data.image_path = None
            display_data.blend = (rng.randi() % 200 + 56, rng.randi() % 200 + 56, rng.randi() % 200 + 56)
            meta["DisplayData"] = display_data

        return log


class SimulationThread:
    thread_limit_semaphore = threading.Semaphore(6)

    def __init__(self, simulation):
        self.simulation = simulation

        self.ticks_per_loop = 1000
        self.iteration_finished = Signal()

        self._keep_running = False

        self._thread = None

    def start(self):
        if self.is_running():
            raise RuntimeError("Runner is already running, unable to start again.")

        self.thread_limit_semaphore.acquire()

        self._thread = threading.Thread(target=self._thread_run)

        self._keep_running = True
        self._thread.start()

    def stop(self):
        self._keep_running = False

    def join(self):
        self._thread.join()

    def is_running(self):
        return self._thread is not None and self._thread.is_alive()

    def _thread_run(self):
        while self._keep_running:
            self.simulation.simulate(self.ticks_per_loop)
            self.iteration_finished.emit()
        self.thread_limit_semaphore.release()


class TestSimulationGroup:
    def __init__(self, simulation_count, configuration):
        simulations = []

        rng = gw.RNG()
        rng.seed(3541690311527, 2554723005947)

        for i in range(simulation_count):
            simulation = TestSimulation(rng.randi(), rng.randi(), **configuration)

        self.simulations = simulations
        self.configuration = dict(configuration)


def create_simulations(count, configuration):
    rng = gw.RNG()
    rng.seed(3541690311527, 2554723005947)

    for i in range(count):
        yield TestSimulation(rng.randi(), rng.randi(), configuration)


class Tester:
    def __init__(self, simulation):
        from math import inf
        self.no_improvement_streak_limit = 100
        self.current_best = -inf
        self.current_no_improvement_streak = 0

        self._past_10_evaluations = []

        self.test_finished = Signal()

        self.simulation = simulation
        self._simulation_thread = SimulationThread(simulation)
        self._simulation_thread.ticks_per_loop = 25000

        simulation.evolution_occurred.connect(self._on_simulation_evolution_occurred)

    def start_test(self):
        self._simulation_thread.start()

    def join(self):
        self._simulation_thread.join()

    def _on_simulation_evolution_occurred(self, log):
        tick = log['tick']
        if tick <= 300000:
            # Simulations seem to be very volatile early,
            # so ignore the first few evolutions.
            return

        sorted_scores = sorted(log['entity_scores'].values(), reverse=True)

        if len(sorted_scores) < 6:
            # Only evaluate states where there exist at least 6 scorables
            return

        evaluation = sum(sorted_scores[:6]) / 6
        self._past_10_evaluations = [evaluation] + self._past_10_evaluations[:9]

        if len(self._past_10_evaluations) < 10:
            # The simulation's score is determined by the average of its last 10 evaluations.
            # So do not score it if there aren't 10 evaluations accumulated.
            return

        simulation_score = sum(self._past_10_evaluations) / len(self._past_10_evaluations)

        if simulation_score > self.current_best:
            self.current_best = simulation_score
            self.current_no_improvement_streak = 0
        else:
            self.current_no_improvement_streak += 1
            if self.current_no_improvement_streak >= self.no_improvement_streak_limit:
                # We decide that we've tested the simulation enough, and will use its current best as its
                # final score.
                self._simulation_thread.stop()
                self.test_finished.emit()


def run_configuration_test():
    configuration_results = {}

    testers = []

    for child_mutation_chance in (x/100 for x in range(10, 110, 10)):
        for child_mutation_strength in (x/100 for x in (10, 25, 50, 75, 100, 150, 200, 250, 300)):
            configuration = {
                'child_mutation_chance': child_mutation_chance,
                'child_mutation_strength': child_mutation_strength
            }
            print(f"Beginning config test {configuration}")

            simulations = create_simulations(5, configuration)

            for simulation in simulations:
                tester = Tester(simulation)
                tester.test_finished.connect(
                    _on_tester_test_finished,
                    configuration_results,
                    tester,
                    (child_mutation_chance, child_mutation_strength)
                )
                tester.start_test()
                testers.append(tester)

    for tester in testers:
        tester.join()

    print("Testing complete.")
    return configuration_results


def _on_tester_test_finished(configuration_results, tester, configuration_repr):
    result_key = (configuration_repr, tester.simulation.seed)
    configuration_results[result_key] = tester.current_best
    print(f"Intermediate result: {result_key}. best: {tester.current_best}")


def run_perf_test(total_ticks):
    simulation = TestSimulation(998899889, 665566555)

    simulation.simulate(total_ticks)

