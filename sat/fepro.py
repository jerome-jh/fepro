import sys
import numpy as np
import pycosat
import itertools as it

def debug(*args):
    print(*args, file=sys.stderr)

teacher_value = ('t0', 't1', 't2')
NT = len(teacher_value)
group_value = ('g0', 'g1')
n_group = len(group_value)
subject_value = ('m0', 'm1', 'm2')
n_subject = len(subject_value)

## Time slots
NS = 14
slot_value = [ 's%d'%i for i in range(NS) ]

## Teacher-subject valid combinations
teacher_subject = np.eye(NT, dtype='b')

def overlap(matrix, i, j):
    matrix[i][j] = True
    matrix[j][i] = True

O = np.zeros((NS, NS), dtype='b')
## s0: 4h of the morning
## s1, s2: 2 x 2h in the morning
## s3, s4, s5, s6: 4 x 4h in the morning
## s7 - s13: same for the afternoon
for off in (0, NS//2):
    for j in range(1, NS//2):
        overlap(O, 0 + off, j + off)
    overlap(O, 1 + off, 3 + off)
    overlap(O, 1 + off, 4 + off)
    overlap(O, 2 + off, 5 + off)
    overlap(O, 2 + off, 6 + off)
## O must be symetric
for i in range(NS):
    for j in range(NS):
        assert(O[i][j] == O[j][i])
## Diagonal is all false: slots do not overlap with themselves
for i in range(NS):
    assert(O[i][i] == False)
#debug(O)

## Slot ordering
slot_after = np.zeros((NS, NS), dtype='b')
## 1 if slot j is after slot i
slot_after = [

]

## Valid durations
duration_value = [4, 2, 1]
n_duration_value = len(duration_value)

slot_duration = np.array([2, 1, 1, 0, 0, 0, 0, 2, 1, 1, 0, 0, 0, 0])
#    # s0 - 4h
#    [False, False, True],
#    # s1,2 - 2h
#    [False, True, False],
#    [False, True, False],
#    # s3,6 - 1h
#    [True, False, False],
#    [True, False, False],
#    [True, False, False],
#    [True, False, False],
#    ## repeat
#    [False, False, True],
#    [False, True, False],
#    [False, True, False],
#    [True, False, False],
#    [True, False, False],
#    [True, False, False],
#    [True, False, False],
#])
assert(slot_duration.shape == (NS,))

group_subject_duration = [
    # g0
    [
        # m0
        [ 1, 0 ],
        # m1
        [ 0 ],
        # m2
        [ 0 ],
    ],
    # g1
    [
        # m0
        [ 2 ],
        # m1
        [ 1 ],
        # m2
        [ 0 ],
    ]
]
assert(len(group_subject_duration) == n_group)
for g in range(n_group):
    assert(len(group_subject_duration[g]) == n_subject)

## Number of courses
NC = 0
for g, s in it.product(range(n_group), range(n_subject)):
    NC += len(group_subject_duration[g][s])

course_duration = np.ndarray((NC,), dtype='u4')
course_subject = np.ndarray((NC,), dtype='u4')
course_group = np.ndarray((NC,), dtype='u4')
c = 0
for g, s in it.product(range(n_group), range(n_subject)):
    for i in range(len(group_subject_duration[g][s])):
        course_duration[c] = group_subject_duration[g][s][i]
        course_subject[c] = s
        course_group[c] = g
        c += 1

debug(NT, 'teachers')
debug(NC, 'courses')
debug(NS, 'slots')
debug(course_duration)
debug(course_subject)
debug(slot_duration)

class literal:
    dtype = 'i1'

    def name(t, c, s):
        return str(literal.number)

    def number(t, c, s):
        return t * NC * NS + c * NS + s + 1

    def tuple(n):
        n -= 1
        t = n // (NC * NS)
        c = (n % (NC * NS)) // NS
        s = (n % NS)
        return (t, c, s)

    def nb_var():
        return NT * NC * NS

def to_cnf():
    cnf = list()

    #debug([literal.number(t, c, s) for t, c, s in it.product(range(NT), range(NC), range(NS))])
    #debug([literal.tuple(n + 1) for n in range(literal.nb_var())])
    for n in range(literal.nb_var()):
        assert(literal.number(*literal.tuple(n)) == n)

    cl_ts = list()
    cl_cd = list()
    for t, c, s in it.product(range(NT), range(NC), range(NS)):
        ## Teacher teaches the subject he/she knows
        if not teacher_subject[t, course_subject[c]]:
            cl_ts.append([-literal.number(t,c,s)])
        ## course duration and slot duration must match
        if course_duration[c] != slot_duration[s]:
            cl_cd.append([-literal.number(t,c,s)])
    debug(len(cl_ts), 'clauses teacher - subject mapping')
    debug(len(cl_cd), 'clauses course duration - slot duration mapping')
    cnf.extend(cl_ts)
    cnf.extend(cl_cd)
    #assert(len(clause) == (NT * NC - 3) * NS)  ## Works only if teachers have only one subject

    cl_to = list()
    cl_go = list()
    for s1, s2 in it.product(range(NS), range(NS)):
        ## O[s][s] is always false
        if O[s1][s2]:
            ## Teacher slots cannot overlap
            for t, c1, c2 in it.product(range(NT), range(NC), range(NC)):
                cl_to.append([-literal.number(t, c1, s1), -literal.number(t, c2, s2)])
            ## Class slots cannot overlap
            for c, t1, t2 in it.product(range(NC), range(NT), range(NT)):
                cl_go.append([-literal.number(t1, c, s1), -literal.number(t2, c, s2)])
    debug(len(cl_to), 'clauses teacher no overlap')
    cnf.extend(cl_to)
    debug(len(cl_go), 'clauses class no overlap')
    cnf.extend(cl_go)

    ## All courses must happen, whatever teacher or slot
    clause = list()
    for c in range(NC):
        cl = list()
        for t, s in it.product(range(NT), range(NS)):
            cl.append(literal.number(t, c, s))
        clause.append(cl)
    debug(len(clause), 'clauses all courses')
    assert(len(clause) == NC)
    cnf.extend(clause)

    ## A course must only be given once
    clause = list()
    for c in range(NC):
        for t1, s1, t2, s2 in it.product(range(NT), range(NS), range(NT), range(NS)):
            if t1 != t2 or s1 != s2:
                clause.append([-literal.number(t1, c, s1), -literal.number(t2, c, s2)])
    debug(len(clause), 'clauses courses only once')
    cnf.extend(clause)

    ## TODO: no twice the same subject in a single day
    return cnf

def to_dimacs_cnf(nb_var, var_name, constraint):
    ## Conjunction of all the constraints
    print('p cnf', nb_var, len(constraint))
    for i in range(len(constraint)):
        for j in range(len(constraint[i]) // 2):
            sign = constraint[i][2*j]
            idx = constraint[i][2*j+1]
            print(var_name[idx], ' ', end='')
        print('0')

def to_list_cnf(nb_var, var_name, constraint):
    cnf = [ 0 ] * len(constraint)
    for i in range(len(constraint)):
        clause = [ 0 ] * (len(constraint[i]) // 2)
        for j in range(len(constraint[i]) // 2):
            sign = constraint[i][2*j]
            idx = constraint[i][2*j+1]
            clause[j] = int(var_name[idx])
        cnf[i] = clause
    return cnf

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

#debug(constraint)
cnf = to_cnf()
debug(literal.nb_var(), 'variables')
debug(len(cnf), 'clauses')
debug(cnf)

#to_dimacs_cnf(nb_var, var_name, constraint)
#cnf = to_list_cnf(nb_var, var_name, constraint)
#debug(cnf)

if 0:
    sol = pycosat.solve(cnf)
    debug(sol)
    debug(np.count_nonzero(np.asarray(sol) > 0), 'courses')

if 0:
    for sol in pycosat.itersolve(cnf):
        assert(np.count_nonzero(np.asarray(sol) > 0) == NC)
        output(sol)
