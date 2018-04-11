# Logic

This is a small Python package for doing symbolic boolean logic in Python. The main purpose is to calculate Conjunctive Normal Forms (CNF) of boolean equations within programs, when this is too difficult to do them offline with "pencil and paper".

As such this is an API and there no syntactic sugar such as operator
overloading. Still equations are fairly easy to enter and read.

Equations can be outputted in various string formats, including:
- standard mathematical notation
- Wolframalpha language
- Python code using this API
- DIMACS

They can also be converted into a "list of list" suitable for calling a SAT
solver, such as Pycosat.

# Example

```python
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
```

