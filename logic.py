from copy import *

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

class AND_op:
    arity = -2
    symb = '/\\'
    func = AND
    def assoc(e, *arg):
        e.extend(arg)

class OR_op:
    arity = -2
    symb = '\\/'
    func = OR 
    def assoc(self, *args):
        self.arg.extend(args)

class IMP_op:
    arity = 2
    symb = '->'
    func = IMP

class EQ_op:
    arity = 2
    symb = '='
    func = EQ

class NOT_op:
    arity = 1
    symb = '-'
    func = NOT

def STR(exp):
    if Logic.islist(exp):
        op, arg = Logic.lisp(exp)
        if op.arity == 2:
            return '(' + STR(arg[0]) + ' ' + op.symb + ' ' + STR(arg[1]) + ')'
        elif op.arity == 1:
            return op.symb + STR(arg[0])
        elif op.arity == -2:
            s = '(' + STR(arg[0])
            for e in arg[1:]:
                s += ' ' + op.symb + ' ' + STR(e) 
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
        return exp[0], exp[1:]

    def convert_eq(exp):
        """ exp is a list """
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
        """ exp is a list """
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
        """ exp is a list """
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
        car, cdr = Logic.lisp(exp)
        if car.func == OR:
            for i, e in enumerate(cdr):
                if Logic.islist(e):
                    car, cdr2 = Logic.lisp(e)
                    if car.func == AND:
                        if i == 0:
                            ## distribute to the left
                            ai = cdr2
                            o = cdr[1]
                            oi = cdr[2:]
                            if len(oi):
                                reta = [0] * (1 + len(ai))
                                reta[0] = AND_op
                                for i, a in enumerate(ai):
                                    reta[i+1] = [OR, a, o]
                                reto = [0] * (2 + len(oi))
                                reto[0] = OR_op
                                reto[1] = reta
                                reto[2:] = oi
                                return Logic.distribute_or(reto)
                            else:
                                reta = [0] * (1 + len(ai))
                                reta[0] = AND_op
                                for i, a in enumerate(ai):
                                    reta[i+1] = [OR_op, a, o]
                                return Logic.distribute_or(reta)
                        else:
                            ## distribute to the right
                            o = cdr[0:i]
                            oi = cdr[i+1:]
                            ai = cdr2
                            print(i, o, oi, ai)
                            reta = [0] * (1 + len(ai))
                            for i, a in enumerate(ai):
                                reta[i+1] = [OR_op, *o, a]
                            if len(oi):
                                reto = [0] * (2 + len(oi))
                                reto[0] = OR_op
                                reto[1] = reta
                                reto[2:] = oi
                                print(reto)
                                return Logic.distribute_or(reto)
                            else:
                                print(reta)
                                return Logic.distribute_or(reta)
            return exp
        else:
            for i, e in enumerate(cdr):
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

    def cnf(exp):
        if not Logic.islist(exp):
            return exp
        exp = Logic.convert_eq(exp)
        exp = Logic.convert_imp(exp)
        exp = Logic.convert_not(exp)
        if not Logic.islist(exp):
            return exp
        #while not Logic.is_cnf(exp):
        if 1:
            print(STR(exp))
            #exp = Logic.distribute_or(exp)
            exp = Logic.associate_or(exp)
            exp = Logic.associate_and(exp)
        return exp

import unittest

class TestSexpression(unittest.TestCase):
    def test_not(self):
        s = NOT(1)
        print(STR(s))
        s = Logic.cnf(s)
        print(STR(s))
        self.assertTrue(s == -1)
    
        s = NOT(NOT(1))
        print(STR(s))
        s = Logic.cnf(s)
        print(STR(s))
        self.assertTrue(s == 1)
        
        s = NOT(AND(1,2))
        print(STR(s))
        s = Logic.cnf(s)
        print(STR(s))
        self.assertTrue(s == OR(-1,-2))
        
        s = NOT(AND(-1,-2))
        print(STR(s))
        s = Logic.cnf(s)
        print(STR(s))
        self.assertTrue(s == OR(1,2))
    
        s = NOT(OR(1,2))
        print(STR(s))
        s = Logic.cnf(s)
        print(STR(s))
        self.assertTrue(s == AND(-1,-2))
        
        s = NOT(OR(-1,-2))
        print(STR(s))
        s = Logic.cnf(s)
        print(STR(s))
        self.assertTrue(s == AND(1,2))
        
        s = NOT(IMP(1,2))
        print(STR(s))
        s = Logic.cnf(s)
        print(STR(s))
        self.assertTrue(s == AND(1,-2))
        
        s = NOT(EQ(1,2))
        print(STR(s))
        s = Logic.cnf(s)
        print(STR(s))
        self.assertTrue(s == OR(AND(1,-2),AND(2,-1)))

    def test_associate(self):
        s = AND(1,AND(2,3))
        print(STR(s))
        s = Logic.cnf(s)
        print(STR(s))
        self.assertTrue(s == AND(1,2,3))
    
        s = AND(AND(2,3), 1)
        print(STR(s))
        s = Logic.cnf(s)
        print(STR(s))
        self.assertTrue(s == AND(2,3,1))
    
        s = AND(1,AND(2,3),4)
        print(STR(s))
        s = Logic.cnf(s)
        print(STR(s))
        self.assertTrue(s == AND(1,2,3,4))
    
        s = OR(1,OR(2,3))
        print(STR(s))
        s = Logic.cnf(s)
        print(STR(s))
        self.assertTrue(s == OR(1,2,3))
    
        s = OR(OR(2,3), 1)
        print(STR(s))
        s = Logic.cnf(s)
        print(STR(s))
        self.assertTrue(s == OR(2,3,1))
    
        s = OR(1,OR(2,3),4)
        print(STR(s))
        s = Logic.cnf(s)
        print(STR(s))
        self.assertTrue(s == OR(1,2,3,4))
    

if __name__ == '__main__':
    unittest.main()

    s = AND(1,2,3)
    print(s)
    print(STR(s))

    s = AND(1,OR(2,3),-4,-5)
    print(s)
    print(STR(s))

    try:
        s = NOT(1,-5)
    except:
        print('Raised as expected')

    s = OR(AND(2,3), 1)
    print(STR(s))
    s = Logic.cnf(s)
    print(STR(s))

    s = OR(1,AND(2,3))
    print(STR(s))
    s = Logic.cnf(s)
    print(STR(s))

    s = OR(1,AND(2,3),4)
    print(STR(s))
    s = Logic.cnf(s)
    print(STR(s))

    s = EQ(1,-2)
    print(STR(s))
    s = Logic.cnf(s)
    print(STR(s))
    s = EQ(3,EQ(1,-2))
    print(STR(s))
    s = Logic.cnf(s)
    print(STR(s))

    s = NOT(AND(1,-2))
    print(STR(s))
    s = Logic.cnf(s)
    print(STR(s))
    s = NOT(OR(1,-2))
    print(STR(s))
    s = Logic.cnf(s)
    print(STR(s))
