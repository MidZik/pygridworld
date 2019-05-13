# -*- coding: utf-8 -*-
"""
Created on Tue May  7 04:13:16 2019

@author: MidZik
"""

from ECS.ECS import Component, Signal
from pcg import pcg_basic

import numpy as np
from itertools import tee
from copy import deepcopy

class SWorld(Component):
    __slots__ = ('width', 'height', '_map')
    
    def __init__(self):
        super().__init__()
        self.resize(10, 10)
    
    def get_map_data(self, x, y):
        return self._map[(y % self.height) * self.width + x % self.width]
    
    def set_map_data(self, x, y, data):
        self._map[(y % self.height) * self.width + x % self.width] = data
    
    def resize(self, width, height):
        self.width = width
        self.height = height
        self._map = [None for i in range(width * height)]
    
    def get_map_index(self, x, y):
        return (y % self.height) * self.width + x % self.width
    
    def get_map_index_x(self, map_index):
        return map_index % self.width
    
    def get_map_index_y(self, map_index):
        return map_index // self.width

class SNewEntityQueue(Component):
    __slots__ = ('queue',)
    
    def __init__(self):
        super().__init__()
        self.queue = []

class SEvents(Component):
    __slots__ = ('queue','_sig_event')
    
    def __init__(self):
        super().__init__()
        self.queue = []
        self._sig_event = Signal()
    
    def queue_event(self, name, details, level):
        self.queue.append((name, details, level))

class SChangeTracker(Component):
    __slots__ = ('changed_components',)
    
    def __init__(self):
        super().__init__()
        
        # Array of WEAKREFs to components
        self.changed_components = []

class SChildCreation(Component):
    __slots__ = ('pending_child_creators',)
    
    def __init__(self):
        super().__init__()
        
        self.pending_child_creators = []

class SJudge(Component):
    __slots__ = ('next_judgement_tick', 'ticks_between_judgements')
    
    def __init__(self):
        super().__init__()
        
        self.next_judgement_tick = 1000
        self.ticks_between_judgements = 1000

class Moveable(Component):
    __slots__ = ('x_force', 'y_force')
    
    def __init__(self):
        super().__init__()
        self.x_force = 0
        self.y_force = 0

class Name(Component):
    __slots__ = ('major_name','minor_name')
    
    def __init__(self):
        super().__init__()
        self.major_name = 'maj'
        self.minor_name = 'min'

class Position(Component):
    __slots__ = ('x', 'y')
    
    def __init__(self):
        super().__init__()
        self.x = 0
        self.y = 0

class RNG(Component):
    __slots__ = ('rng',)
    
    def __init__(self):
        super().__init__()
        self.rng = pcg_basic.pcg32_random_t()
    
    def __getstate__(self):
        return {'rngstate': self.rng.state,
                'rnginc': self.rng.inc}
    
    def copy_state_from(self, other):
        self.rng.state = other.rng.state
        self.rng.inc = other.rng.inc

class Scorable(Component):
    __slots__ = ('score',)
    
    def __init__(self):
        super().__init__()
        self.score = 0

class DisplayData(Component):
    __slots__ = ('imagepath','blend')
    
    def __init__(self):
        super().__init__()
        self.imagepath = None
        self.blend = (255, 255, 255)

class RandomMover(Component):
    __slots__ = ()

class Predation(Component):
    __slots__ = ('no_predation_until_tick',)
    
    def __init__(self):
        super().__init__()
        self.no_predation_until_tick = 0

def _pairwise(iterable):
    """i -> (i0, i1), (i1, i2), (i2, i3), ..."""
    a, b = tee(iterable)
    next(b, None)
    return zip(a, b)
    
class SimpleBrain(Component):
    __slots__= ('neurons', 'synapses', 'child_mutation_chance', 'child_mutation_strength')
    
    def __init__(self):
        super().__init__()
        layers = [26, 8, 4] # do not include bias neurons
        neurons = []
        synapses = []
        
        for ncount in layers[:-1]:
            # every layer except the last one has a bias neuron
            neurons.append(np.ones((1, ncount + 1)))
        # last layer has no bias neuron
        neurons.append(np.zeros((1, layers[-1])))
        
        for a_count, b_count in _pairwise(layers):
            synapses.append(np.zeros((a_count + 1, b_count)))
        
        self.neurons = neurons
        self.synapses = synapses
        self.child_mutation_chance = 0.5 # the chance any individual synapse will be modified.
        self.child_mutation_strength = 0.2 # the range of modification allowed (e.g. if 0.2, it can change +/- 0.1)
    
    def copy_state_from(self, other: 'SimpleBrain'):
        self.child_mutation_chance = other.child_mutation_chance
        self.child_mutation_strength = other.child_mutation_strength
        self.neurons = deepcopy(other.neurons)
        self.synapses = deepcopy(other.synapses)

class SimpleBrainSeer(Component):
    __slots__ = ('neuron_offset', 'sight_radius')
    
    def __init__(self):
        super().__init__()
        self.neuron_offset = 1
        self.sight_radius = 2

class SimpleBrainMover(Component):
    __slots__ = ('neuron_offset',)
    
    def __init__(self):
        super().__init__()
        self.neuron_offset = 0

