from copy import *

class Logic:
    opcode = [ 'AND', 'OR', 'IMP', 'EQ', 'NOT' ]
    symb = [ '/\\', '\\/', '->', '=', '-' ]
    arity = [ -2, -2, 2, 2, 1 ]
    opdict = dict()
    class Op:
        pass
    op = Op()
    for i, o in enumerate(opcode):
        setattr(op, o, i)
        opdict[o] = i

    def __init__(self, exp):
        try:
            len(exp)
        except:
            raise Exception('Expression must be iterable')
        self.exp = Logic.normalize(exp)

    def AND(*args):
        return [ Logic.op.AND, *args ]

    def OR(*args):
        return [ Logic.op.OR, *args ]

    def IMP(a, b):
        return [ Logic.op.IMP, a, b ]

    def EQ(a, b):
        return [ Logic.op.EQ, a, b ]

    def NOT(e):
        return [ Logic.op.NOT, e ]

    def islist(exp):
        try:
            len(exp)
            return True
        except TypeError:
            return False

    def lisp(exp):
        return exp[0], exp[1:]

    def normalize(exp):
        if not Logic.islist(exp):
            raise Exception("Iterable type expected")

        car, cdr = Logic.lisp(exp)
        try:
            op = Logic.opdict[car.upper()]
        except KeyError:
            raise Exception("Invalid opcode '%s'"%op)

        a = Logic.arity[op]
        if a > 0:
            if len(cdr) != a:
                raise Exception("Opcode '%s' must have %d arguments"%(car, a))
        elif len(cdr) < -a:
            raise Exception("Opcode '%s' must have at least %d arguments"%(car, -a))

        norm = [op]
        for e in cdr:
            if Logic.islist(e):
                norm.append(Logic.normalize(e))
            else:
                if type(e) != type(int()):
                    raise Exception("Argument '%d' is not an integer")
                if e == 0:
                    raise Exception("Arguments cannot be zero")
                norm.append(e)
        return norm

    def convert_eq(exp):
        car, cdr = Logic.lisp(exp)
        if car == Logic.op.EQ:
            a = cdr[0]
            b = cdr[1]
            if Logic.islist(a):
                a = Logic.convert_eq(a)
            if Logic.islist(b):
                b = Logic.convert_eq(b)
            return [Logic.op.AND, [Logic.op.IMP, a, b], [Logic.op.IMP, copy(b), copy(a)]]
        else:
            for i, e in enumerate(cdr):
                if Logic.islist(e):
                    exp[i+1] = Logic.convert_eq(e)
            return exp

    def convert_imp(exp):
        car, cdr = Logic.lisp(exp)
        if car == Logic.op.IMP:
            a = cdr[0]
            b = cdr[1]
            if Logic.islist(a):
                a = Logic.convert_imp(a)
            if Logic.islist(b):
                b = Logic.convert_imp(b)
            return [Logic.op.OR, [Logic.op.NOT, a], b]
        else:
            for i, e in enumerate(cdr):
                if Logic.islist(e):
                    exp[i+1] = Logic.convert_imp(e)
            return exp

    def convert_not(exp):
        car, cdr = Logic.lisp(exp)
        if car == Logic.op.NOT:
            #assert(len(cdr) == 1)
            if Logic.islist(cdr[0]):
                exp = cdr[0]
                car, cdr = Logic.lisp(exp)
                if car == Logic.op.NOT:
                    ## Simplify NOT NOT
                    return cdr[0]
                elif car == Logic.op.AND:
                    exp[0] = Logic.op.OR
                    for i, e in enumerate(cdr):
                        exp[i+1] = [Logic.op.NOT, e]
                    return Logic.convert_not(exp)
                elif car == Logic.op.OR:
                    exp[0] = Logic.op.AND
                    for i, e in enumerate(cdr):
                        exp[i+1] = [Logic.op.NOT, e]
                    return Logic.convert_not(exp)
                else:
                    raise Exception("Operator '%s' should have been simplified by now"%Logic.opcode[car])
            else:
                ## Evaluate NOT
                return -cdr[0]
        else:
            for i, e in enumerate(cdr):
                if Logic.islist(e):
                    exp[i+1] = Logic.convert_not(e)
            return exp

    def distribute_or(exp):
        car, cdr = Logic.lisp(exp)
        if car == Logic.op.OR:
            for i, e in enumerate(cdr):
                if Logic.islist(e):
                    car, cdr2 = Logic.lisp(e)
                    if car == Logic.op.AND:
                        if i == 0:
                            ## distribute to the left
                            ai = cdr2
                            o = cdr[1]
                            oi = cdr[2:]
                            if len(oi):
                                reta = [0] * (1 + len(ai))
                                reta[0] = Logic.op.AND
                                for i, a in enumerate(ai):
                                    reta[i+1] = [Logic.op.OR, a, o]
                                reto = [0] * (2 + len(oi))
                                reto[0] = Logic.op.OR
                                reto[1] = reta
                                reto[2:] = oi
                                return Logic.distribute_or(reto)
                            else:
                                reta = [0] * (1 + len(ai))
                                reta[0] = Logic.op.AND
                                for i, a in enumerate(ai):
                                    reta[i+1] = [Logic.op.OR, a, o]
                                return Logic.distribute_or(reta)
                        else:
                            ## distribute to the right
                            o = cdr[0:i]
                            oi = cdr[i+1:]
                            ai = cdr2
                            print(i, o, oi, ai)
                            reta = [0] * (1 + len(ai))
                            for i, a in enumerate(ai):
                                reta[i+1] = [Logic.op.OR, *o, a]
                            if len(oi):
                                reto = [0] * (2 + len(oi))
                                reto[0] = Logic.op.OR
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
        if car == Logic.op.OR:
            for i, e in enumerate(cdr):
                if Logic.islist(e):
                    car, cdr2 = Logic.lisp(e)
                    if car == Logic.op.OR:
                        ## i is in cdr, make it point in exp
                        i += 1
                        j = len(cdr2)
                        ret = [ 0 ] * (len(exp) + j - 1)
                        ret[0] = Logic.op.OR
                        ret[1:i] = exp[1:i]
                        ret[i:i+j] = cdr2 ## exp[i]
                        ret[i+j:] = exp[i+1:]
                        return Logic.associate_or(ret)
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
        if car == Logic.op.AND:
            for i, e in enumerate(cdr):
                if Logic.islist(e):
                    car, cdr2 = Logic.lisp(e)
                    if car == Logic.op.AND:
                        ## i is in cdr, make it point in exp
                        i += 1
                        j = len(cdr2)
                        ret = [ 0 ] * (len(exp) + j - 1)
                        ret[0] = Logic.op.AND
                        ret[1:i] = exp[1:i]
                        ret[i:i+j] = cdr2 ## exp[i]
                        ret[i+j:] = exp[i+1:]
                        return Logic.associate_and(ret)
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
        if car == Logic.op.AND:
            for e in cdr:
                if Logic.islist(e):
                    car, cdr2 = Logic.lisp(e)
                    if car != Logic.op.OR:
                        return False
                    for e2 in cdr2:
                        if Logic.islist(e2):
                            return False
            return True
        elif car == Logic.op.OR:
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
        while not Logic.is_cnf(exp):
            exp = Logic.distribute_or(exp)
            exp = Logic.associate_or(exp)
            exp = Logic.associate_and(exp)
        return exp

    def STR(exp):
        if Logic.islist(exp):
            car, cdr = Logic.lisp(exp)
            if Logic.arity[car] == 2:
                return '(' + Logic.STR(cdr[0]) + ' ' + Logic.symb[car] + ' ' + Logic.STR(cdr[1]) + ')'
            elif Logic.arity[car] == 1:
                return Logic.symb[car] + Logic.STR(cdr[0])
            elif Logic.arity[car] == -2:
                s = '(' + Logic.STR(cdr[0])
                for e in cdr[1:]:
                    s += ' ' + Logic.symb[car] + ' ' + Logic.STR(e) 
                s += ')'
                return s
            else:
                raise Exception('Unexpected arity')
        else:
            return str(exp)

if __name__ == '__main__':
    s = Logic.AND(1,2,3)
    print(s)
    print(Logic.STR(s))
    s = Logic.AND(1,Logic.OR(2,3),-4,-5)
    print(s)
    print(Logic.STR(s))
    try:
        s = Logic.NOT(1,-5)
    except:
        print('Raised as expected')

    s = Logic.AND(1,Logic.AND(2,3))
    print(s)
    print(Logic.STR(s))
    s = Logic.cnf(s)
    print(Logic.STR(s))

    s = Logic.AND(Logic.AND(2,3), 1)
    print(s)
    print(Logic.STR(s))
    s = Logic.cnf(s)
    print(Logic.STR(s))

    s = Logic.AND(1,Logic.AND(2,3),4)
    print(s)
    print(Logic.STR(s))
    s = Logic.cnf(s)
    print(Logic.STR(s))

    s = Logic.OR(1,Logic.OR(2,3))
    print(s)
    print(Logic.STR(s))
    s = Logic.cnf(s)
    print(Logic.STR(s))

    s = Logic.OR(Logic.OR(2,3), 1)
    print(s)
    print(Logic.STR(s))
    s = Logic.cnf(s)
    print(Logic.STR(s))

    s = Logic.OR(1,Logic.OR(2,3),4)
    print(s)
    print(Logic.STR(s))
    s = Logic.cnf(s)
    print(Logic.STR(s))

    s = Logic.OR(Logic.AND(2,3), 1)
    print(s)
    print(Logic.STR(s))
    s = Logic.cnf(s)
    print(s)
    print(Logic.STR(s))

    s = Logic.OR(1,Logic.AND(2,3))
    print(Logic.STR(s))
    s = Logic.cnf(s)
    print(Logic.STR(s))

    s = Logic.OR(1,Logic.AND(2,3),4)
    print(Logic.STR(s))
    s = Logic.cnf(s)
    print(Logic.STR(s))

    s = Logic.EQ(1,-2)
    print(s)
    print(Logic.STR(s))
    s = Logic.cnf(s)
    print(Logic.STR(s))
    s = Logic.EQ(3,Logic.EQ(1,-2))
    print(s)
    print(Logic.STR(s))
    s = Logic.cnf(s)
    print(Logic.STR(s))

    s = Logic.NOT(1)
    print(s)
    print(Logic.STR(s))
    s = Logic.cnf(s)
    print(Logic.STR(s))
    
    s = Logic.NOT(Logic.NOT(1))
    print(s)
    print(Logic.STR(s))
    s = Logic.cnf(s)
    print(s)
    print(Logic.STR(s))
    
    s = Logic.NOT(Logic.AND(1,-2))
    print(s)
    print(Logic.STR(s))
    s = Logic.cnf(s)
    print(Logic.STR(s))
    s = Logic.NOT(Logic.OR(1,-2))
    print(s)
    print(Logic.STR(s))
    s = Logic.cnf(s)
    print(Logic.STR(s))
