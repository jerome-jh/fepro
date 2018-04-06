
class Expression:
    opcode = [ 'AND', 'OR', 'XOR', 'IMP', 'EQ', 'NOT' ]
    arity = [ -2, -2, -2, 2, 2, 1 ]
    opdict = dict()

    def __init__(self, exp):
        try:
            len(exp)
        except:
            raise Exception('Expression must be iterable')
        self.exp = Expression.normalize(exp)

    def islist(exp):
        try:
            len(exp)
            return True
        except TypeError:
            return False

    def normalize(exp):
        if not Expression.islist(exp):
            raise Exception("Iterable type expected")

        car = exp[0]
        cdr = exp[1:]
        try:
            op = Expression.opdict[car.upper()]
        except KeyError:
            raise Exception("Invalid opcode '%s'"%op)

        a = Expression.arity[op]
        if a > 0:
            if len(cdr) != a:
                raise Exception("Opcode '%s' must have %d arguments"%(car, a))
        elif len(cdr) < -a:
            raise Exception("Opcode '%s' must have at least %d arguments"%(car, -a))

        norm = [op]
        for e in cdr:
            if Expression.islist(e):
                norm.append(Expression.normalize(e))
            else:
                if type(e) != type(int()):
                    raise Exception("Argument '%d' is not an integer")
                if e == 0:
                    raise Exception("Arguments cannot be zero")
                norm.append(e)
        return norm

    def convert_eq(exp):
        car = exp[0]
        cdr = exp[1:]
        if car == Expression.EQ:
            return Expression.convert_eq([Expression.AND, [Expression.IMP, cdr[0], cdr[1]], [Expression.IMP, cdr[1], cdr[0]]])
        else:
            for i, e in enumerate(cdr):
                if Expression.islist(e):
                    exp[i+1] = Expression.convert_eq(e)
            return exp

    def convert_imp(exp):
        car = exp[0]
        cdr = exp[1:]
        if car == Expression.IMP:
            return Expression.convert_imp([Expression.OR, [Expression.NOT, cdr[0]], cdr[1]])
        else:
            for i, e in enumerate(cdr):
                if Expression.islist(e):
                    exp[i+1] = Expression.convert_imp(e)
            return exp

    def convert_not(exp):
        car = exp[0]
        cdr = exp[1:]
        if car == Expression.NOT:
            if Expression.islist(cdr[0]):
                if cdr[0][0] == Expression.NOT:
                    ## Simplify NOT NOT
                    return cdr[0][1]
                elif cdr[0][0] == Expression.AND:
                    arg = [ Expression.OR ]
                elif cdr[0][0] == Expression.OR:
                    arg = [ Expression.AND ]
                ## TODO: could be done in place, in exp
                arg.extend([[Expression.NOT, x] for x in cdr[0][1:]])
                return Expression.convert_not(arg)
            else:
                ## Evaluate NOT
                return -cdr[0]
        else:
            for i, e in enumerate(cdr):
                if Expression.islist(e):
                    exp[i+1] = Expression.convert_not(e)
            return exp

    def to_cnf(self):
        self.exp = Expression.convert_eq(self.exp)
        self.exp = Expression.convert_imp(self.exp)
        self.exp = Expression.convert_not(self.exp)
        return self.exp

#    def __str__(self):


for i, o in enumerate(Expression.opcode):
    setattr(Expression, o, i)
    Expression.opdict[o] = i

if __name__ == '__main__':
    s = Expression(('AND',1,2,3))
    print(s.exp)
    s = Expression(('AND',1,('OR',2,3),-4,-5))
    print(s.exp)
    try:
        s = Expression(('NOT',1,-5))
    except Exception as e:
        print(str(e))
    s = Expression(('EQ',1,-2))
    print(s.exp)
    print(s.to_cnf())
    s = Expression(('EQ',1,('EQ', -2, 3)))
    print(s.exp)
    print(s.to_cnf())
    s = Expression(('NOT',1))
    print(s.exp)
    print(s.to_cnf())
    s = Expression(('NOT',('AND', 1, 2)))
    print(s.exp)
    print(s.to_cnf())
    s = Expression(('NOT',('OR', 1, 2)))
    print(s.exp)
    print(s.to_cnf())
