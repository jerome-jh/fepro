import sys
import numpy as np
import itertools as it

def debug(*args):
    print(*args, file=sys.stderr)

class Variable:
    ## Variables have a unique integer id. Offset is updated consequently
    offset = 1
    def reset():
        Variable.offset = 1

    def __init__(self, vect, prefix='x'):
        """ vect[0] is the slower varying index, vect[N-1] the faster varying index """
        N = len(vect)
        base = np.ndarray((N+1,), dtype='u4')
        base[0] = 1
        base[1:] = np.flipud(np.asarray(vect, dtype='u4'))
        self.base = np.flipud(np.cumprod(base, dtype='u4'))
        self.vect = vect
        self.prefix = prefix
        self.offset = Variable.offset
        Variable.offset = self.max()

    def cardinal(self):
        return int(self.base[0])

    def max(self):
        return self.cardinal() + self.offset

    def range(self):
        return range(self.offset, self.max())

    def last(self):
        return self.max() - 1

    def vnumber(self, vect):
        assert(len(vect) == len(self.vect))
        ## Convert to Python int (otherwise this is a Numpy int)
        return int(np.dot(self.base[1:], vect) + self.offset)

    def number(self, *args):
        return self.vnumber(args)

    def vname(self, vect):
        return self.prefix + str(super.vnumber(vect))

    def name(self, *args):
        return self.vname(args)

    def index(self, n):
        assert(n >= self.offset and n < self.offset + self.cardinal())
        N = self.base.shape[0]-1
        idx = np.ndarray((N,), dtype='u4')
        n -= self.offset
        for i in range(N-1, -1, -1):
            idx[i] = n % self.vect[i]
            n = (n - idx[i]) // self.vect[i]
        return idx

    def __iter__(self):
        """ Iterate other indices """
        return it.product(*map(range, self.vect))

    def check(self):
        """ Debug function: check consistency of self.index and self.number """
        i = self.offset
        for tu in self:
            assert(self.vnumber(tu) == i)
            assert(self.vnumber(tu) < self.max())
            i += 1
        assert(i == self.max())
        tu = iter(self)
        for i in range(self.offset, self.max()):
            assert(np.all(self.index(i) == np.asarray(tu.__next__(), dtype='u4')))

    def debug(self):
        for i,j,k in v:
            debug((i,j,k),v.number(i,j,k))
        for n in range(self.offset, self.offset + v.cardinal()):
            debug(n,v.index(n))

if __name__ == '__main__':
    v = Variable((4, 2, 2))
    v.check()
    v = Variable((4, 2, 2), offset=1)
    v.check()
