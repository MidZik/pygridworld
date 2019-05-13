# -*- coding: utf-8 -*-
"""
Created on Sun May  5 18:47:18 2019

@author: MidZik
"""

from distutils.core import setup
from Cython.Build import cythonize

setup(
    ext_modules = cythonize("pcg_basic.pyx")
)