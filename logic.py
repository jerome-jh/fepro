from copy import *

""" Requires Python >= 3.5, syntax error otherwise """
#import sys
#if sys.version_info[0] < 3 or sys.version_info[1] < 5:
#    print('This module requires at least python3.5')

def AND(*arg):
    assert(len(arg) >= -AND_op.arity)
    return [AND_op, *arg]

def OR(*arg):
    assert(len(arg) >= -OR_op.arity)
    return [OR_op, *arg]

def IMP(a, b):
    return [IMP_op, a, b]

def EQ(a, b):
    return [EQ_op, a, b]

def NOT(a):
    return [NOT_op, a]

def CNF(exp):
    if not Logic.islist(exp):
        return exp
    exp = Logic.convert_eq(exp)
    exp = Logic.convert_imp(exp)
    exp = Logic.convert_not(exp)
    if not Logic.islist(exp):
        return exp
    #while not Logic.is_cnf(exp):
    if 1:
        exp = Logic.distribute_or(exp)
        exp = Logic.associate_or(exp)
        exp = Logic.associate_and(exp)
    return exp

class AND_op:
    arity = -2
    symb = '/\\'
    wolf_symb = 'And'
    func = AND
    def assoc(e, *arg):
        e.extend(arg)

class OR_op:
    arity = -2
    symb = '\\/'
    wolf_symb = 'Or'
    func = OR 
    def assoc(self, *args):
        self.arg.extend(args)

class IMP_op:
    arity = 2
    symb = '->'
    wolf_symb = 'Implies'
    func = IMP

class EQ_op:
    arity = 2
    symb = '='
    wolf_symb = 'Equivalent'
    func = EQ

class NOT_op:
    arity = 1
    symb = '-'
    wolf_symb = 'Not'
    func = NOT

def math_str(exp):
    """ Print exp in usual mathematical notation """
    if Logic.islist(exp):
        op, arg = Logic.lisp(exp)
        if op.arity == 2:
            return '(' + math_str(arg[0]) + ' ' + op.symb + ' ' + math_str(arg[1]) + ')'
        elif op.arity == 1:
            return op.symb + math_str(arg[0])
        elif op.arity == -2:
            s = '(' + math_str(arg[0])
            for e in arg[1:]:
                s += ' ' + op.symb + ' ' + math_str(e) 
            s += ')'
            return s
        else:
            raise Exception('Unexpected arity')
    else:
        return str(exp)

def code_str(exp):
    """ Print exp as equivalent code using this module API """
    if Logic.islist(exp):
        op, arg = Logic.lisp(exp)
        if op.arity == 2:
            return op.func.__name__ + '(' + code_str(arg[0]) + ',' + code_str(arg[1]) + ')'
        elif op.arity == 1:
            return op.func.__name__ + '(' + code_str(arg[0]) + ')'
        elif op.arity == -2:
            s = op.func.__name__ + '(' + code_str(arg[0])
            for e in arg[1:]:
                s += ',' + code_str(e) 
            s += ')'
            return s
        else:
            raise Exception('Unexpected arity')
    else:
        return str(exp)

def wolf_str(exp):
    """ Tentative output to the so called Wolfram "language"
        This is useful for checking validity of the output
        But the language itself is so picky and unpredictable that careful
        human inspection is required every time. """
    if Logic.islist(exp):
        op, arg = Logic.lisp(exp)
        if op.arity == 2:
            return op.wolf_symb + '[' + wolf_str(arg[0]) + ',' + wolf_str(arg[1]) + ']'
        elif op.arity == 1:
            return op.wolf_symb + '[' + wolf_str(arg[0]) + ']'
        elif op.arity == -2:
            s = op.wolf_symb + '[' + wolf_str(arg[0])
            for e in arg[1:]:
                s += ',' + wolf_str(e) 
            s += ']'
            return s
        else:
            raise Exception('Unexpected arity')
    else:
        if (exp < 0):
            return wolf_str(NOT(-exp))
        else:
            return chr(ord('a') + exp - 1)
            #return 'Symbol["x%d"]'%(exp)

def dimacs_str(exp):
    ##TODO
    if Logic.islist(exp):
        op, arg = Logic.lisp(exp)
        if op.arity == 2:
            return '(' + dimacs_str(arg[0]) + ' ' + op.symb + ' ' + dimacs_str(arg[1]) + ')'
        elif op.arity == 1:
            return op.symb + dimacs_str(arg[0])
        elif op.arity == -2:
            s = '(' + dimacs_str(arg[0])
            for e in arg[1:]:
                s += ' ' + op.symb + ' ' + dimacs_str(e) 
            s += ')'
            return s
        else:
            raise Exception('Unexpected arity')
    else:
        return str(exp)

class Logic:
    def islist(exp):
        return type(exp) != type(int())

    def lisp(exp):
        """ This is suboptimal because Python does not support views on lists,
            so taking a slice actually creates a copy """
        return exp[0], exp[1:]

    def convert_eq(exp):
        """ exp must be a list """
        op, arg = Logic.lisp(exp)
        if op.func == EQ:
            a = arg[0]
            b = arg[1]
            if Logic.islist(a):
                a = Logic.convert_eq(a)
            if Logic.islist(b):
                b = Logic.convert_eq(b)
            return AND(IMP(a, b), IMP(copy(b), copy(a)))
        else:
            for i, a in enumerate(arg):
                if Logic.islist(a):
                    exp[i+1] = Logic.convert_eq(a)
            return exp

    def convert_imp(exp):
        """ exp must be a list """
        op, arg = Logic.lisp(exp)
        if op.func == IMP:
            a = arg[0]
            b = arg[1]
            if Logic.islist(a):
                a = Logic.convert_imp(a)
            if Logic.islist(b):
                b = Logic.convert_imp(b)
            return OR(NOT(a), b)
        else:
            for i, a in enumerate(arg):
                if Logic.islist(a):
                    exp[i+1] = Logic.convert_imp(a)
            return exp

    def convert_not(exp):
        """ exp must be a list """
        op, arg = Logic.lisp(exp)
        if op.func == NOT:
            #assert(len(arg) == 1)
            if Logic.islist(arg[0]):
                op2, arg2 = Logic.lisp(arg[0])
                if op2.func == NOT:
                    ## Simplify NOT NOT
                    return arg2[0]
                elif op2.func == AND:
                    return OR(*map(Logic.convert_not, map(NOT, arg2)))
                elif op2.func == OR:
                    return AND(*map(Logic.convert_not, map(NOT, arg2)))
                else:
                    raise Exception("Operator '%s' should have been simplified by now"%op2.symb)
            else:
                ## Evaluate NOT
                return -arg[0]
        else:
            for i, a in enumerate(arg):
                if Logic.islist(a):
                    exp[i+1] = Logic.convert_not(a)
            return exp

    def distribute_or(exp):
        """ exp must be a list """
        op, arg = Logic.lisp(exp)
        if op.func == OR:
            for i, e in enumerate(arg):
                if Logic.islist(e):
                    op, arg2 = Logic.lisp(e)
                    if op.func == AND:
                        if i == 0:
                            ## distribute to the left
                            ai = arg2
                            o = arg[1]
                            of = lambda x: OR(x,o)
                            oi = arg[2:]
                            if not len(oi):
                                return AND(*map(Logic.distribute_or, map(of, ai))) 
                            else:
                                reta = AND(*map(of, ai))
                                reto = OR(reta, *oi)
                                return Logic.distribute_or(reto)
                        else:
                            ## distribute to the right
                            o = arg[0:i]
                            ai = arg2
                            of = lambda x: OR(*o,x)
                            oi = arg[i+1:]
                            if not len(oi):
                                return AND(*map(Logic.distribute_or, map(of, ai)))
                            else:
                                reta = AND(*map(of, ai))
                                reto = OR(reta, *oi)
                                return Logic.distribute_or(reto)
            return exp
        else:
            for i, e in enumerate(arg):
                if Logic.islist(e):
                    exp[i+1] = Logic.distribute_or(e)
            return exp

    def associate_or(exp):
        car, cdr = Logic.lisp(exp)
        if car.func == OR:
            for i, e in enumerate(cdr):
                if Logic.islist(e):
                    car, cdr2 = Logic.lisp(e)
                    if car.func == OR:
                        return Logic.associate_or(OR(*cdr[0:i],*cdr2,*cdr[i+1:]))
                    else:
                        exp[i+1] = Logic.associate_or(e)
            return exp
        else:
            for i, e in enumerate(cdr):
                if Logic.islist(e):
                    exp[i+1] = Logic.associate_or(e)
            return exp

    def associate_and(exp):
        car, cdr = Logic.lisp(exp)
        if car.func == AND:
            for i, e in enumerate(cdr):
                if Logic.islist(e):
                    car, cdr2 = Logic.lisp(e)
                    if car.func == AND:
                        return Logic.associate_and(AND(*cdr[0:i],*cdr2,*cdr[i+1:]))
                    else:
                        exp[i+1] = Logic.associate_and(e)
            return exp
        else:
            for i, e in enumerate(cdr):
                if Logic.islist(e):
                    exp[i+1] = Logic.associate_and(e)
            return exp

    def is_cnf(exp):
        if not Logic.islist(exp):
            return True
        car, cdr = Logic.lisp(exp)
        if car.func == AND:
            for e in cdr:
                if Logic.islist(e):
                    car.func, cdr2 = Logic.lisp(e)
                    if car.func != OR:
                        return False
                    for e2 in cdr2:
                        if Logic.islist(e2):
                            return False
            return True
        elif car.func == OR:
            for e in cdr:
                if Logic.islist(e):
                    return False
            return True
        else:
            return False

import unittest

class TestCNF(unittest.TestCase):
    def test_not(self):
        return
        s = NOT(1)
        print(math_str(s))
        s = CNF(s)
        print(math_str(s))
        self.assertTrue(s == -1)
    
        s = NOT(NOT(1))
        print(math_str(s))
        s = CNF(s)
        print(math_str(s))
        self.assertTrue(s == 1)
        
        s = NOT(AND(1,2))
        print(math_str(s))
        s = CNF(s)
        print(math_str(s))
        self.assertTrue(s == OR(-1,-2))
        
        s = NOT(AND(-1,-2))
        print(math_str(s))
        s = CNF(s)
        print(math_str(s))
        self.assertTrue(s == OR(1,2))
    
        s = NOT(OR(1,2))
        print(math_str(s))
        s = CNF(s)
        print(math_str(s))
        self.assertTrue(s == AND(-1,-2))
        
        s = NOT(OR(-1,-2))
        print(math_str(s))
        s = CNF(s)
        print(math_str(s))
        self.assertTrue(s == AND(1,2))
        
        s = NOT(IMP(1,2))
        print(math_str(s))
        s = CNF(s)
        print(math_str(s))
        self.assertTrue(s == AND(1,-2))
        
        s = NOT(EQ(1,2))
        print(math_str(s))
        s = CNF(s)
        print(math_str(s))
        self.assertTrue(s == OR(AND(1,-2),AND(2,-1)))

    def test_associate(self):
        return
        s = AND(1,AND(2,3))
        print(math_str(s))
        s = CNF(s)
        print(math_str(s))
        self.assertTrue(s == AND(1,2,3))
    
        s = AND(AND(2,3), 1)
        print(math_str(s))
        s = CNF(s)
        print(math_str(s))
        self.assertTrue(s == AND(2,3,1))
    
        s = AND(1,AND(2,3),4)
        print(math_str(s))
        s = CNF(s)
        print(math_str(s))
        self.assertTrue(s == AND(1,2,3,4))
    
        s = OR(1,OR(2,3))
        print(math_str(s))
        s = CNF(s)
        print(math_str(s))
        self.assertTrue(s == OR(1,2,3))
    
        s = OR(OR(2,3), 1)
        print(math_str(s))
        s = CNF(s)
        print(math_str(s))
        self.assertTrue(s == OR(2,3,1))
    
        s = OR(1,OR(2,3),4)
        print(math_str(s))
        s = CNF(s)
        print(math_str(s))
        self.assertTrue(s == OR(1,2,3,4))
    
    def test_distribute(self):
        s = OR(AND(2,3), 1)
        c = AND(OR(2,1),OR(3,1))
        self.assertTrue(CNF(s) == c)
    
        s = OR(1,AND(2,3))
        c = AND(OR(1,2),OR(1,3))
        self.assertTrue(CNF(s) == c)
    
        s = OR(1,2,AND(3,4))
        c = AND(OR(1,2,3),OR(1,2,4))
        self.assertTrue(CNF(s) == c)

        s = OR(AND(1,2),3,4)
        c = AND(OR(1,3,4),OR(2,3,4))
        self.assertTrue(CNF(s) == c)

        s = OR(1,AND(2,3),4)
        c = AND(OR(1,2,4),OR(1,3,4))
        self.assertTrue(CNF(s) == c)
    
        s = OR(1,2,AND(2,3),4,5)
        c = AND(OR(1,2,2,4,5),OR(1,2,3,4,5))
        self.assertTrue(CNF(s) == c)

        return
        s = EQ(1,-2)
        print(math_str(s))
        s = CNF(s)
        print(math_str(s))
        s = EQ(3,EQ(1,-2))
        print(math_str(s))
        s = CNF(s)
        print(math_str(s))
    
        s = NOT(AND(1,-2))
        print(math_str(s))
        s = CNF(s)
        print(math_str(s))
        s = NOT(OR(1,-2))
        print(math_str(s))
        s = CNF(s)
        print(math_str(s))

    def test_arity(self):
        try:
            s = NOT(1,-5)
        except:
            print('Raised as expected')

if __name__ == '__main__':

    unittest.main()

    s = AND(1,2,3)
    print(math_str(s))
    c = CNF(s)
    print(math_str(c))
    print(code_str(c))
    print(wolf_str(EQ(s,c)))

    s = AND(1,2,3)
    print(math_str(s))
    print(wolf_str(s))

    s = AND(1,OR(2,3),-4,-5)
    print(math_str(s))
    print(wolf_str(s))
    s = CNF(s)
    print(math_str(s))
    print(wolf_str(s))

    s = EQ(2,3)
    print(math_str(s))
    print(wolf_str(s))
    s = CNF(s)
    print(math_str(s))
    print(wolf_str(s))

    s = IMP(2,3)
    print(math_str(s))
    print(wolf_str(s))
    s = CNF(s)
    print(math_str(s))
    print(wolf_str(s))
