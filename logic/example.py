from logic import *

if __name__ == '__main__':
    s = EQ(2,3)
    c = AND(OR(-2,3),OR(-3,2))
    assert(is_cnf(c))
    assert(CNF(s) == c)
    e = EQ(s,c)
    ## e is a tautology, but since there is no simplification being done
    ## it results in a fairly long equation ;)
    print(math_str(CNF(e)))
