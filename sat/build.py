import sys
import numpy as np
import itertools as it
from variable import *
import logic

def debug(*args):
    print(*args, file=sys.stderr)

def mextend(l, iter_of_iter):
    for i in iter_of_iter:
        l.extend(i)

class CNF:
    def equal(p, q):
        """ Return p == q in CNF """
        return [[-p, q], [-q, p]]

    def equal_and(p, qi):
        """ Return p == q1 and q2 and ... and qn in CNF """
        clause = list()
        cl = [p]
        for q in qi:
            cl.append(-q)
            clause.append([-p, q])
        clause.append(cl)
        return clause

    def equal_or(p, qi):
        """ Return p == q1 or q2 or ... or qn in CNF """
        clause = list()
        cl = [-p]
        for q in qi:
            cl.append(q)
            clause.append([-q, p])
        clause.append(cl)
        return clause

class SatVariable(Variable):
    def __init__(self, vect):
        super().__init__(vect, prefix='')

class SatBuild:
    def __init__(self, pb):
        self.pb = pb
        self.var = SatVariable((pb.n_teacher, pb.n_course, pb.n_slot))
        print(self.var.range())
        cnf = list()
        ## Satisfaction variables
        mextend(cnf, self.forall())
        mextend(cnf, self.overlap())
        cnf.extend(self.all_course())
        cnf.extend(self.at_most_one())
        ## Optimizing variables
        self.day = SatVariable((pb.n_teacher, pb.n_day))
        print(self.day.range())
        cl = self.teacher_day_2()
        cnf.extend(cl)
        self.start_slot = SatVariable((pb.n_teacher, pb.n_slot))
        print(self.start_slot.range())
        print('Start slot vars', self.day.max(), self.start_slot.max())
        self.end_slot = SatVariable((pb.n_teacher, pb.n_slot))
        print(self.end_slot.range())
        print('Start slot vars', self.start_slot.max(), self.end_slot.max())
        cnf.extend(self.teacher_day_start_slot())
        cnf.extend(self.teacher_day_end_slot())
        self.cnf = cnf
        debug(self.var.cardinal() + self.start_slot.cardinal() + self.end_slot.cardinal(), 'variables')
        debug(self.end_slot.max())
        debug(len(cnf), 'total clauses')

    def all_course(self):
        ## All courses must happen, whatever teacher or slot
        clause = list()
        NS, NT, NC = (self.pb.n_slot, self.pb.n_teacher, self.pb.n_course)
        for c in range(NC):
            cl = list()
            for t, s in it.product(range(NT), range(NS)):
                cl.append(self.var.number(t, c, s))
            clause.append(cl)
        debug(len(clause), 'clauses all courses')
        assert(len(clause) == NC)
        return clause

    def forall(self):
        cl_ts = list()
        cl_cd = list()
        for t, c, s in self.var:
            ## Teacher teaches the subject he/she knows
            if not self.pb.course_teacher[c, t]:
                cl_ts.append([-self.var.number(t,c,s)])
            ## course duration and slot duration must match
            if not self.pb.course_slot[c, s]:
                cl_cd.append([-self.var.number(t,c,s)])
        debug(len(cl_ts), 'clauses teacher - subject mapping')
        debug(len(cl_cd), 'clauses course duration - slot duration mapping')
        return (cl_ts, cl_cd)

    def overlap(self):
        cl_to = list()
        cl_go = list()
        NS, NT, NC = (self.pb.n_slot, self.pb.n_teacher, self.pb.n_course)
        for s1, s2 in it.product(range(NS), range(NS)):
            ## overlap[s][s] is always false
            if self.pb.slot_overlap[s1][s2]:
                ## Teacher slots cannot overlap
                for t, c1, c2 in it.product(range(NT), range(NC), range(NC)):
                    if c1 != c2:
                        cl_to.append([-self.var.number(t, c1, s1), -self.var.number(t, c2, s2)])
                ## Class slots cannot overlap
                for c, t1, t2 in it.product(range(NC), range(NT), range(NT)):
                    if t1 != t2:
                        cl_go.append([-self.var.number(t1, c, s1), -self.var.number(t2, c, s2)])
        debug(len(cl_to), 'clauses teacher no overlap')
        debug(len(cl_go), 'clauses class no overlap')
        return (cl_to, cl_go)

    def at_most_one(self):
        ## A course must only be given once
        clause = list()
        NS, NT, NC = (self.pb.n_slot, self.pb.n_teacher, self.pb.n_course)
        for c in range(NC):
            for t1, s1, t2, s2 in it.product(range(NT), range(NS), range(NT), range(NS)):
                if t1 != t2 or s1 != s2:
                    clause.append([-self.var.number(t1, c, s1), -self.var.number(t2, c, s2)])
        debug(len(clause), 'clauses courses only once')
        return clause

    def teacher_day(self):
        ## Minimize total days worked
        NS, NT, NC = (self.pb.n_slot, self.pb.n_teacher, self.pb.n_course)
        clause = list()
        for t, d in self.day:
            cl = [ -self.day.number(t,d) ]
            for s, c in it.product(range(NS), range(NC)):
                if self.pb.slot_day[s, d]:
                    cl.append(self.var.number(t,c,s))
                    cl2 = [ -self.var.number(t,c,s), self.day.number(t,d) ]
                    clause.append(cl2)
            clause.append(cl)
        debug(len(clause), 'day clauses')
        return clause

    def teacher_day_2(self):
        """ Minimize total days worked """
        NS, NT, NC = (self.pb.n_slot, self.pb.n_teacher, self.pb.n_course)
        clause = list()
        for t, d in self.day:
            q = [self.var.number(t,c,s) for s, c in it.product(range(NS), range(NC))]
            clause.extend(CNF.equal_or(self.day.number(t,d), q))
        debug(len(clause), 'day clauses')
        return clause

    def teacher_day_start_slot(self):
        ## Set of booleans, one of them is true indicating the first busy slot
        ## of the day
        NS, NT, NC = (self.pb.n_slot, self.pb.n_teacher, self.pb.n_course)
        clause = list()
        for t, s in self.start_slot:
            ## List all the courses that are mappable to this slot
            first = [ self.var.number(t, c, s) for c in range(NC) ]
            idx = np.where(self.pb.slot_order[:,s])[0]
            if len(idx):
                ## Slot has other slots before him: if this is the first slot
                ## none of them should be true
                before = [ -self.var.number(t, c, s2) for s2 in idx for c in range(NC) ]
                ## This slot is first if one of the courses occupies it and
                ## none of the slots before is busy
                exp = logic.EQ(self.start_slot.number(t, s), logic.AND(logic.OR(*first), *before))
            else:
                ## Slot is the first in the day: it is the starting slot if
                ## actually busy
                exp = logic.EQ(self.start_slot.number(t, s), logic.OR(*first))
            exp = logic.CNF(exp)
            clause.extend(logic.to_sat(exp))
        debug(len(clause), 'first slot clauses')
        return clause

    def teacher_day_end_slot(self):
        ## Set of booleans, one of them is true indicating the last busy slot
        ## of the day
        NS, NT, NC = (self.pb.n_slot, self.pb.n_teacher, self.pb.n_course)
        clause = list()
        for t, s in self.end_slot:
            ## List all the courses that are mappable to this slot
            last = [ self.var.number(t, c, s) for c in range(NC) ]
            idx = np.where(self.pb.slot_order[s])[0]
            if len(idx):
                ## Slot has other slots after him: if this is the last slot
                ## none of them should be true
                after = [ -self.var.number(t, c, s2) for s2 in idx for c in range(NC) ]
                ## This slot is last if one of the courses occupies it and
                ## none of the slots after is busy
                exp = logic.EQ(self.end_slot.number(t, s), logic.AND(logic.OR(*last), *after))
            else:
                ## Slot is the last in the day: it is the ending slot if
                ## actually busy
                exp = logic.EQ(self.end_slot.number(t, s), logic.OR(*last))
            exp = logic.CNF(exp)
            clause.extend(logic.to_sat(exp))
        debug(len(clause), 'end slot clauses')
        return clause

#            for s2 in range(s+1, NS):
#                if self.pb.slot_order[s, s2]:
#                    ## s is before s2 in the same day
#                    pass 
#                elif self.pb.slot_order[s2, s]:
#                    ## s2 is before s in the same day
#                    pass

    def to_dimacs(self):
        ## Conjunction of all the constraints
        N = len(self.cnf)
        s = 'p cnf ' + str(self.var.cardinal()) + ' ' + str(N) + '\n'
        for i in range(N):
            cl = self.cnf[i]
            for j in range(len(cl)):
                s += str(cl[j]) + ' '
            s += '0\n'
        return s

    def __str__(self):
        return self.to_dimacs()

