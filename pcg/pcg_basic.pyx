#!python3.7
#cython: cdivision=True,language_level=3

from libc.stdint cimport uintptr_t, uint32_t, uint64_t, UINT32_MAX
from libc.stdlib cimport malloc, free

RAND_MAX = UINT32_MAX
_RAND_MAX_plusone_double = <double>RAND_MAX + 1.0

cdef class pcg32_random_t:
    cdef public uint64_t state # all values valid
    cdef public uint64_t inc   # must always be odd
    
    def seed(self, uint64_t initstate, uint64_t initseq):
        self.state = 0u
        self.inc = (initseq << 1u) | 1u
        self.randi()
        self.state += initstate
        self.randi()
    
    def randi(self) -> uint32_t:
        """Returns a random integer i, 0 <= i <= UINT32_MAX, under a uniform distribution."""
        cdef uint64_t oldstate = self.state
        self.state = oldstate * 6364136223846793005ULL + self.inc
        cdef uint32_t xorshifted = ((oldstate >> 18u) ^ oldstate) >> 27u
        cdef uint32_t rot = oldstate >> 59u
        return (xorshifted >> rot) | (xorshifted << ((-rot) & 31u))
    
    def randd(self) -> double:
        """Returns a random double d, 0.0 <= d < 1.0, under a uniform distribution.
        
        Uses a 32 bit generator, so not every valid d in the range is possible."""
        cdef uint64_t oldstate = self.state
        self.state = oldstate * 6364136223846793005ULL + self.inc
        cdef uint32_t xorshifted = ((oldstate >> 18u) ^ oldstate) >> 27u
        cdef uint32_t rot = oldstate >> 59u
        return ((xorshifted >> rot) | (xorshifted << ((-rot) & 31u))) / _RAND_MAX_plusone_double
