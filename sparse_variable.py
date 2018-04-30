import sys
import numpy as np
import itertools as it

def debug(*args):
    print(*args, file=sys.stderr)

class SparseVariable:
    ## Variables have a unique integer id. Instances are chained so
    ## that offset can be calculated and there is no hole in variable numbering
    head_var = None
    tail_var = None

    def reset():
        SparseVariable.head_var = None
        SparseVariable.tail_var = None

    def update():
        if type(SparseVariable.head_var) != type(None):
            var = SparseVariable.head_var
        while type(var.next_var) != type(None):
            n = var.next_var
            n.offset = var.last()
            var = n

    def tot_last():
        SparseVariable.update()
        return SparseVariable.tail_var.last()

    def __init__(self, vect, name):
        vect = np.asarray(vect, dtype='u4')
        N = vect.shape[0]
        M = np.product(vect)
        self.name = name
        ## Mapping from tuple to variable number
        self.array = np.zeros(vect, dtype='u4')
        assert(np.all(self.array.shape == vect))
        ## Reverse mapping: variable number to tuple
        self.reverse = -np.ones([M, N], dtype='i4')
        self.next_var = None
        ## Update chaining
        if type(SparseVariable.head_var) == type(None):
            self.offset = 0
            SparseVariable.head_var = self
            SparseVariable.tail_var = self
        else:
            self.offset = SparseVariable.tail_var.last()
            SparseVariable.tail_var.next_var = self
            SparseVariable.tail_var = self
        self.current = 1

    def vnew(self, vect):
        vect = np.asarray(vect, dtype='u4')
        assert(len(vect) == len(self.array.shape))
        if self.array[tuple(vect)]:
            ## Variable already exists
            return self.array[tuple(vect)]
        self.array[tuple(vect)] = self.current
        self.reverse[self.current - 1] = vect
        self.current += 1
        return self.current

    def new(self, *args):
        return self.vnew(args)

    def vnumber(self, vect):
        assert(len(vect) == len(self.array.shape))
        ## Convert to Python int (otherwise this is a Numpy int)
        return int(self.array[tuple(vect)] + self.offset)

    def number(self, *args):
        return self.vnumber(args)

    def index(self, n):
        assert(n > self.offset and n < self.max())
        return tuple(map(int, self.reverse[n - 1 - self.offset]))

    def max(self):
        return self.offset + self.current

    def range(self):
        return range(1 + self.offset, self.max())

    def last(self):
        return self.max() - 1

    def __iter__(self):
        """ Iterate over indices """
        return it.product(*map(range, self.array.shape))

    def is_sparse(self):
        return bool(np.count_nonzero(self.array == 0))

    def cardinal(self):
        return np.product(self.array.shape)

    def debug(self):
        debug(self.array.shape)
        debug(self.offset, self.current)
        debug(self.array)
        debug(self.reverse)

if __name__ == '__main__':
    v1 = SparseVariable((4, 2, 2), 'x')
    #v1.check()
    v1.new(0, 0, 0)
    assert(v1.vnumber((0,0,0)) == 1)
    v1.vnew((2, 1, 1))
    assert(v1.number(2,1,1) == 2)
    #v1.debug()
    #debug(v1.index(1))
    assert(v1.index(1) == (0,0,0))
    assert(v1.index(2) == (2,1,1))
    assert(v1.is_sparse())

    v2 = SparseVariable((2, 2), 'd')
    #SparseVariable.update()
    v2.new(0,0)
    v2.new(0,1)
    assert(v2.number(0,0) == 3)
    assert(v2.vnumber((0,1)) == 4)
    assert(v2.index(3) == (0,0))
    assert(v2.index(4) == (0,1))
    assert(v2.is_sparse())
    v2.new(1,0)
    v2.new(1,1)
    assert(not v2.is_sparse())

    v3 = SparseVariable((3,3,3), 'y')
    assert(v3.is_sparse())
    for i,j,k in v3:
        v3.new(i,j,k)
        assert(v3.index(v3.number(i,j,k)) == (i,j,k))
    assert(not v3.is_sparse())
    for l in v3.range():
        assert(v3.vnumber(v3.index(l)) == l)
    assert(v3.number(2,2,2) == 27 + 4 + 2)
