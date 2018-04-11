from copy import *

""" Requires Python >= 3.5, syntax error otherwise """

__all__ = ['AND', 'OR', 'IMP', 'EQ', 'NOT', 'CNF', 'math_str', 'code_str', 'wolf_str', 'dimacs_str', 'is_cnf', 'count_variable', 'to_sat']

## TODO: check input for AND, OR, etc ... must be non zero integers

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
    if not islist(exp):
        return exp
    exp = convert_eq(exp)
    exp = convert_imp(exp)
    exp = convert_not(exp)
    if not islist(exp):
        return exp
    while not is_cnf(exp):
        #print('in:', code_str(exp))
        exp = associate_or(exp)
        #print(code_str(exp))
        exp = associate_and(exp)
        #print(code_str(exp))
        exp = distribute_or(exp)
        #print('out:', code_str(exp))
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
    if islist(exp):
        op, arg = lisp(exp)
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
    if islist(exp):
        op, arg = lisp(exp)
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
    if islist(exp):
        op, arg = lisp(exp)
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

def __count_variable(exp):
    s = set()
    if islist(exp):
        for i in range(1,len(exp)):
            if islist(exp[i]):
                s.update(__count_variable(exp[i]))
            else:
                if exp[i] < 0:
                    s.add(-exp[i])
                else:
                    s.add(exp[i])
    else:
        ## Can only occur at root of the tree
        if exp < 0:
            s.add(-exp)
        else:
            s.add(exp)
    return s

def count_variable(exp):
    s = __count_variable(exp)
    return len(s)

def dimacs_str(exp):
    if not is_cnf(exp):
        Exception('Expression is not CNF, cannot convert to DIMACS')
    ## Count number of variables
    nv = count_variable(exp)
    if islist(exp):
        car, cdr = lisp(exp)
        if car.func == AND:
            nc = len(cdr)
            s = 'p cnf %d %d\n'%(nv,nc)
            for e in cdr:
                car, cdr2 = lisp(e)
                for e2 in cdr2:
                    s += '%s '%e2
                s+= '0\n'
            return s
        elif car.func == OR:
            ## only one clause
            nc = 1
            s = 'p cnf %d 1\n'%nv
            for e in cdr:
                s += '%s '%e
            s += '0\n'
            return s
    else:
        ## Ultra degenerated case
        return 'p cnf 1 1\n%d 0\n'%exp

def to_sat(exp):
    """ Return a list of list, suitable for e.g. Pycosat input """
    if not is_cnf(exp):
        Exception('Expression is not CNF, cannot convert to sat')
    if islist(exp):
        car, cdr = lisp(exp)
        if car.func == AND:
            for i, e in enumerate(cdr):
                if islist(e):
                    cdr[i] = e[1:]
                else:
                    cdr[i] = [e]
            return cdr
        elif car.func == OR:
            ## only one clause
            return [cdr]
    else:
        ## Can only occur at root of the tree
        return [[exp]]

def islist(exp):
    return type(exp) != type(int())

def lisp(exp):
    """ This is suboptimal because Python does not support views on lists,
        so taking a slice actually creates a copy """
    return exp[0], exp[1:]

def convert_eq(exp):
    """ exp must be a list """
    op, arg = lisp(exp)
    if op.func == EQ:
        a = arg[0]
        b = arg[1]
        if islist(a):
            a = convert_eq(a)
        if islist(b):
            b = convert_eq(b)
        return AND(IMP(a, b), IMP(copy(b), copy(a)))
    else:
        for i, a in enumerate(arg):
            if islist(a):
                exp[i+1] = convert_eq(a)
        return exp

def convert_imp(exp):
    """ exp must be a list """
    op, arg = lisp(exp)
    if op.func == IMP:
        a = arg[0]
        b = arg[1]
        if islist(a):
            a = convert_imp(a)
        if islist(b):
            b = convert_imp(b)
        return OR(NOT(a), b)
    else:
        for i, a in enumerate(arg):
            if islist(a):
                exp[i+1] = convert_imp(a)
        return exp

def convert_not(exp):
    """ exp must be a list """
    op, arg = lisp(exp)
    if op.func == NOT:
        #assert(len(arg) == 1)
        if islist(arg[0]):
            op2, arg2 = lisp(arg[0])
            if op2.func == NOT:
                ## Simplify NOT NOT
                return arg2[0]
            elif op2.func == AND:
                return OR(*map(convert_not, map(NOT, arg2)))
            elif op2.func == OR:
                return AND(*map(convert_not, map(NOT, arg2)))
            else:
                raise Exception("Operator '%s' should have been simplified by now"%op2.symb)
        else:
            ## Evaluate NOT
            return -arg[0]
    else:
        for i, a in enumerate(arg):
            if islist(a):
                exp[i+1] = convert_not(a)
        return exp

def distribute_or(exp):
    """ exp must be a list """
    op, arg = lisp(exp)
    if op.func == OR:
        for i, e in enumerate(arg):
            if islist(e):
                op, arg2 = lisp(e)
                if op.func == AND:
                    if i == 0:
                        ## distribute to the left
                        ai = arg2
                        o = arg[1]
                        of = lambda x: OR(x,o)
                        oi = arg[2:]
                        if not len(oi):
                            return AND(*map(distribute_or, map(of, ai)))
                        else:
                            reta = AND(*map(of, ai))
                            reto = OR(reta, *oi)
                            return distribute_or(reto)
                    else:
                        ## distribute to the right
                        o = arg[0:i]
                        ai = arg2
                        of = lambda x: OR(*o,x)
                        oi = arg[i+1:]
                        if not len(oi):
                            return AND(*map(distribute_or, map(of, ai)))
                        else:
                            reta = AND(*map(of, ai))
                            reto = OR(reta, *oi)
                            return distribute_or(reto)
        return exp
    else:
        for i, e in enumerate(arg):
            if islist(e):
                exp[i+1] = distribute_or(e)
        return exp

def associate_or(exp):
    """ exp must be a list """
    car, cdr = lisp(exp)
    if car.func == OR:
        for i, e in enumerate(cdr):
            if islist(e):
                car, cdr2 = lisp(e)
                if car.func == OR:
                    return associate_or(OR(*cdr[0:i],*cdr2,*cdr[i+1:]))
                else:
                    exp[i+1] = associate_or(e)
        return exp
    else:
        for i, e in enumerate(cdr):
            if islist(e):
                exp[i+1] = associate_or(e)
        return exp

def associate_and(exp):
    """ exp must be a list """
    car, cdr = lisp(exp)
    if car.func == AND:
        for i, e in enumerate(cdr):
            if islist(e):
                car, cdr2 = lisp(e)
                if car.func == AND:
                    return associate_and(AND(*cdr[0:i],*cdr2,*cdr[i+1:]))
                else:
                    exp[i+1] = associate_and(e)
        return exp
    else:
        for i, e in enumerate(cdr):
            if islist(e):
                exp[i+1] = associate_and(e)
        return exp

def is_cnf(exp):
    if not islist(exp):
        return True
    car, cdr = lisp(exp)
    if car.func == AND:
        for e in cdr:
            if islist(e):
                car, cdr2 = lisp(e)
                if car.func != OR:
                    return False
                for e2 in cdr2:
                    if islist(e2):
                        return False
        return True
    elif car.func == OR:
        for e in cdr:
            if islist(e):
                return False
        return True
    else:
        return False

