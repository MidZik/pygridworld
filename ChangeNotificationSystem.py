# -*- coding: utf-8 -*-
"""
Created on Sat May  4 04:15:57 2019

@author: MidZik
"""

from ECS import ECS
import Core

def change_notification_system(em: ECS.EntityManager):
    change_tracker = em.get_scomponent(Core.SComChangeTracker)
    
    for component_ref in change_tracker.changed_components:
        component = component_ref()
        if component and component.marked_as_changed:
            component.sig_changed.emit()
            component.marked_as_changed = False