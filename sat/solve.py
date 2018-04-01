import sys
import numpy as np
import pycosat
import itertools as it

def debug(*args):
    print(*args, file=sys.stderr)

def output(sol):
    c_subject_value = [0] * NC
    c_group_value = [0] * NC
    c_slot_value = [0] * NC
    c_teacher_value = [0] * NC
    idx = np.where(np.asarray(sol, dtype='i4') > 0)[0]
    for i, j in enumerate(idx):
        t, c, s = literal.tuple(sol[j])
        c_teacher_value[i] = teacher_value[t]
        c_group_value[i] = group_value[course_group[c]]
        c_subject_value[i] = subject_value[course_subject[c]]
        c_slot_value[i] = slot_value[s]
    debug('course_teacher = ', c_teacher_value, ';')
    debug('course_group = ', c_group_value, ';')
    debug('course_subject = ', c_subject_value, ';')
    debug('course_slot = ', c_slot_value, ';')

def solve(cnf, a = False):
#    debug(cnf)
    if not a:
        sol = pycosat.solve(cnf)
        debug(sol)
        debug(np.count_nonzero(np.asarray(sol) > 0), 'courses')
        return sol
    else:
        sol = list()
        for s in pycosat.itersolve(cnf):
            #assert(np.count_nonzero(np.asarray(sol) > 0) == NC)
            #debug(sol)
            sol.append(s)
        return sol

