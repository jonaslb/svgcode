"""Gcode basics."""
import numpy as np
from copy import copy
from random import randrange, random


def _gto(n, x, y, S=None, F=None):
    s = ""
    f = ""
    if S is not None:
        s = " S{S:2f}".format(S=S)
    if F is not None:
        f = " F{F}".format(F=F)
    return f"G{n} X{x:.4f} Y{y:.4f}" + s + f


def _g0to(p, S=None, F=None):
    x, y = p
    return _gto(0, x, y, S=S, F=F)


def _g1to(p, S=None, F=None):
    x, y = p
    return _gto(1, x, y, S=S, F=F)


class GCodeG1():
    def __init__(self, *points, F=None, S=None):
        """Points must include the start!"""
        self.points = np.array(points)
        self.F = F
        self.S = S

    def mutate(self):
        self.points = np.flip(self.points, axis=0)


class GCodeCollection(list):
    def tostring(self, pre="G90\nG21", post="M2", pre_line="M3", post_line="M5"):
        p = np.array((0., 0.))
        strings = [pre]
        strings.append(_g0to(p))
        for line in self:
            start = line.points[0, :]
            if not np.all(start == p):
                strings.append(_g0to(start))
            strings.append(pre_line)
            for point in line.points[1:, :]:
                strings.append(_g1to(point, S=line.S, F=line.F))
            strings.append(post_line)
            p = point
        strings.append(_g0to((0, 0)))
        strings.append(post)
        return "\n".join(strings)

    def travel_length(self):
        """Only count G0 moves because G1 moves are 'necessary'."""
        p = np.array((0., 0.))
        L = 0
        for l in self:
            L += np.linalg.norm(l.points[0]-p)
            p = l.points[-1]
        L += np.linalg.norm(p)
        return L

    def mutate(self):
        mutated = copy(self)
        r = random()
        if r < 0.2:
            i0 = randrange(len(self))
            mutated[i0].mutate()
        i1, i2 = [randrange(len(self)) for _ in range(2)]
        mutated[i1], mutated[i2] = mutated[i2], mutated[i1]
        return mutated

    def optimize(self, generations=1000, gen_start=20, multiply=5):
        """Essentially the travelling salesman problem with the added bonus of not having A->B == B->A.
        It is a todo to make it work well. For now its extremely wasteful and inefficient but gives
        modest improvements."""
        print(f"Pre-mutation: {self.travel_length()}")
        pop = [self]
        pop += [self.mutate() for _ in range(gen_start - 1)]
        for iteration in range(generations):
            # Multiply
            new = [c.mutate() for c in pop for _ in range(multiply)]
            pop += new
            # Cull
            pop = sorted(pop, key=lambda c: c.travel_length())
            pop = pop[:gen_start]
        print(f"Post-mutation: {pop[0].travel_length()}")
        return pop[0]
