# Credit to https://github.com/MostAwesomeDude/java-random

import time
import math

class Random(object):
    """
    An implementation of the Java SE 6 random number generator.

    Java's RNG is based on a classic Knuth-style linear congruential formula,
    as described in
    http://download.oracle.com/javase/6/docs/api/java/util/Random.html. This
    makes it quite trivial to reimplement and port to other platforms.

    This class should be bit-for-bit compatible with any Java RNG.

    This class is not thread-safe. For deterministic behavior, lock or
    synchronize all accesses to this class per-instance.
    """

    def __init__(self, seed = None):
        """
        Create a new random number generator.
        """

        if seed is None:
            seed = int(time.time() * 1000)
        self.seed = seed

        self.nextNextGaussian = None

    def setSeed(self, seed):
        """
        Explicit setter for seed, for compatibility with Java.
        """

        self.seed = seed

    @property
    def seed(self):
        return self._seed

    @seed.setter
    def seed(self, seed):
        self._seed = (seed ^ 0x5deece66d) & ((1 << 48) - 1)

    def next(self, bits):
        """
        Generate the next random number.

        As in Java, the general rule is that this method returns an int that
        is `bits` bits long, where each bit is nearly equally likely to be 0
        or 1.
        """

        if bits < 1:
            bits = 1
        elif bits > 32:
            bits = 32

        self._seed = (self._seed * 0x5deece66d + 0xb) & ((1 << 48) - 1)
        retval = self._seed >> (48 - bits)

        # Python and Java don't really agree on how ints work. This converts
        # the unsigned generated int into a signed int if necessary.
        if retval & (1 << 31):
            retval -= (1 << 32)

        return retval

    def nextInt(self, n = None):
        """
        Return a random int in [0, `n`).

        If `n` is not supplied, a random 32-bit integer will be returned.
        """

        if n is None:
            return self.next(32)

        if n <= 0:
            raise ValueError("Argument must be positive!")

        # This tricky chunk of code comes straight from the Java spec. In
        # essence, the algorithm tends to have much better entropy in the
        # higher bits of the seed, so this little bundle of joy is used to try
        # to reject values which would be obviously biased. We do have an easy
        # out for power-of-two n, in which case we can call next directly.

        # Is this a power of two?
        if not (n & (n - 1)):
            return (n * self.next(31)) >> 31

        bits = self.next(31)
        val = bits % n
        while (bits - val + n - 1) < 0:
            bits = self.next(31)
            val = bits % n

        return val