from logic import *
import unittest
import pycosat

class TestCNF(unittest.TestCase):
    def test_basic(self):
        s = AND(1,2,3)
        c = AND(1,2,3)
        self.assertTrue(CNF(s) == c)
        self.assertTrue(is_cnf(c))

        s = OR(1,2,3)
        c = OR(1,2,3)
        self.assertTrue(CNF(s) == c)
        self.assertTrue(is_cnf(c))

        s = EQ(2,3)
        c = AND(OR(-2,3),OR(-3,2))
        self.assertTrue(CNF(s) == c)
        self.assertTrue(is_cnf(c))

        s = EQ(1,-2)
        c = AND(OR(-1,-2),OR(2,1))
        self.assertTrue(CNF(s) == c)
        self.assertTrue(is_cnf(c))

        s = IMP(2,3)
        c = OR(-2,3)
        self.assertTrue(CNF(s) == c)
        self.assertTrue(is_cnf(c))

    def test_not(self):
        s = NOT(1)
        c = -1
        self.assertTrue(CNF(s) == c)
        self.assertTrue(is_cnf(c))

        s = NOT(NOT(1))
        c = 1
        self.assertTrue(CNF(s) == c)
        self.assertTrue(is_cnf(c))

        s = NOT(AND(1,2))
        c = OR(-1,-2)
        self.assertTrue(CNF(s) == c)
        self.assertTrue(is_cnf(c))

        s = NOT(AND(1,-2))
        c = OR(-1,2)
        self.assertTrue(CNF(s) == c)
        self.assertTrue(is_cnf(c))

        s = NOT(AND(-1,-2))
        c = OR(1,2)
        self.assertTrue(CNF(s) == c)
        self.assertTrue(is_cnf(c))

        s = NOT(OR(1,2))
        c = AND(-1,-2)
        self.assertTrue(CNF(s) == c)
        self.assertTrue(is_cnf(c))

        s = NOT(OR(-1,-2))
        c = AND(1,2)
        self.assertTrue(CNF(s) == c)
        self.assertTrue(is_cnf(c))

        s = NOT(OR(-1,2))
        c = AND(1,-2)
        self.assertTrue(CNF(s) == c)
        self.assertTrue(is_cnf(c))

        s = NOT(IMP(1,2))
        c = AND(1,-2)
        self.assertTrue(CNF(s) == c)
        self.assertTrue(is_cnf(c))

        s = NOT(EQ(1,2))
        c = AND(OR(1,2),OR(1,-1),OR(-2,2),OR(-2,-1))
        self.assertTrue(CNF(s) == c)
        self.assertTrue(is_cnf(c))

    def test_associate(self):
        s = AND(1,AND(2,3))
        c = AND(1,2,3)
        self.assertTrue(CNF(s) == c)
        self.assertTrue(is_cnf(c))

        s = AND(AND(2,3), 1)
        c = AND(2,3,1)
        self.assertTrue(CNF(s) == c)
        self.assertTrue(is_cnf(c))

        s = AND(1,AND(2,3),4)
        c = AND(1,2,3,4)
        self.assertTrue(CNF(s) == c)
        self.assertTrue(is_cnf(c))

        s = OR(1,OR(2,3))
        c = OR(1,2,3)
        self.assertTrue(CNF(s) == c)
        self.assertTrue(is_cnf(c))

        s = OR(OR(2,3), 1)
        c = OR(2,3,1)
        self.assertTrue(CNF(s) == c)
        self.assertTrue(is_cnf(c))

        s = OR(1,OR(2,3),4)
        c = OR(1,2,3,4)
        self.assertTrue(CNF(s) == c)
        self.assertTrue(is_cnf(c))

    def test_distribute(self):
        s = OR(AND(2,3), 1)
        c = AND(OR(2,1),OR(3,1))
        self.assertTrue(CNF(s) == c)
        self.assertTrue(is_cnf(c))

        s = OR(1,AND(2,3))
        c = AND(OR(1,2),OR(1,3))
        self.assertTrue(CNF(s) == c)
        self.assertTrue(is_cnf(c))

        s = OR(1,2,AND(3,4))
        c = AND(OR(1,2,3),OR(1,2,4))
        self.assertTrue(CNF(s) == c)
        self.assertTrue(is_cnf(c))

        s = OR(AND(1,2),3,4)
        c = AND(OR(1,3,4),OR(2,3,4))
        self.assertTrue(CNF(s) == c)
        self.assertTrue(is_cnf(c))

        s = OR(1,AND(2,3),4)
        c = AND(OR(1,2,4),OR(1,3,4))
        self.assertTrue(CNF(s) == c)
        self.assertTrue(is_cnf(c))

        s = OR(1,2,AND(2,3),4,5)
        c = AND(OR(1,2,2,4,5),OR(1,2,3,4,5))
        self.assertTrue(CNF(s) == c)
        self.assertTrue(is_cnf(c))

    def test_eq(self):
        ## UNCHECKED!!!
        s = EQ(3,EQ(1,-2))
        c = AND(OR(-3,-1,-2),OR(-3,2,1),OR(1,-2,3),OR(1,-1,3),OR(2,-2,3),OR(2,-1,3))
        self.assertTrue(CNF(s) == c)
        self.assertTrue(is_cnf(c))

    def test_arity(self):
        try:
            s = NOT(1,-5)
        except:
            print('Raised as expected')

    def test_other(self):
        s = AND(1,OR(2,3),-4,-5)
        c = AND(1,OR(2,3),-4,-5)
        self.assertTrue(CNF(s) == c)
        self.assertTrue(is_cnf(c))

    def test_count(self):
        s = 1
        c = 1
        self.assertTrue(count_variable(s) == c)

        s = NOT(1)
        c = 1
        self.assertTrue(count_variable(s) == c)

        s = IMP(1,2)
        c = 2
        self.assertTrue(count_variable(s) == c)

        s = AND(OR(-3,-1,3),OR(-3,2,1),OR(1,-2,3),OR(1,-1,3),OR(2,-2,3),OR(2,-1,3))
        c = 3
        self.assertTrue(count_variable(s) == c)

        r = range(1,21)
        s = AND(*r)
        c = 20
        self.assertTrue(count_variable(s) == c)

    def test_dimacs(self):
        s = 1
        p = 'p cnf 1 1\n1 0\n'
        self.assertTrue(dimacs_str(s) == p)

        s = OR(*range(1,5))
        p = 'p cnf 4 1\n1 2 3 4 0\n'
        self.assertTrue(dimacs_str(s) == p)

        s = AND(OR(1,3),OR(-1,2),OR(2,3,-4))
        p = 'p cnf 4 3\n1 3 0\n-1 2 0\n2 3 -4 0\n'
        self.assertTrue(dimacs_str(s) == p)

        s = AND(OR(-2,-4),OR(-4,-6,-12),OR(-2,-4,-12))
        p = 'p cnf 4 3\n-2 -4 0\n-4 -6 -12 0\n-2 -4 -12 0\n'
        self.assertTrue(dimacs_str(s) == p)

    def test_to_sat(self):
        s = 1
        o = [[1]]
        self.assertTrue(to_sat(s) == o)
        pycosat.solve(o)

        s = OR(*range(1,5))
        o = [[1,2,3,4]]
        self.assertTrue(to_sat(s) == o)
        pycosat.solve(o)

        s = AND(OR(1,3),OR(-1,2),OR(2,3,-4))
        o = [[1,3],[-1,2],[2,3,-4]]
        self.assertTrue(to_sat(s) == o)
        pycosat.solve(o)

        s = AND(5,OR(1,3),-7,OR(-1,2),OR(2,3,-4),6)
        o = [[5],[1,3],[-7],[-1,2],[2,3,-4],[6]]
        self.assertTrue(to_sat(s) == o)
        pycosat.solve(o)

if __name__ == '__main__':
    unittest.main()

