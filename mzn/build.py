import sys
import numpy as np
import itertools as it
from variable import *
import logic

def debug(*args):
    print(*args, file=sys.stderr)

def mcat(s, iter_of_str):
    for i in iter_of_str:
        s += i
    return s

class MznVariable(Variable):
    def __init__(self, vect, prefix='x'):
        super().__init__(vect, prefix=prefix)

    def vname(self, vect):
        return '%s[%d]'%(self.prefix, super().vnumber(vect) - self.offset + 1)

class MznBuild:
    def __init__(self, pb):
        self.pb = pb
        self.var = MznVariable((pb.n_teacher, pb.n_course, pb.n_slot))
        mzn = ''
        mzn += 'int: NVAR = %d;\n'%self.var.cardinal()
        mzn += 'array[1..NVAR] of var bool: x;\n'
        ## Satisfaction constraints
        mzn = mcat(mzn, self.forall())
        mzn = mcat(mzn, self.overlap())
        mzn += self.all_course()
        mzn += self.at_most_one()
        ## Optimizing constraints
        self.day = MznVariable((pb.n_teacher, pb.n_day), prefix='d')
        mzn += self.teacher_day()

        self.start_slot = MznVariable((pb.n_teacher, pb.n_slot), prefix='fs')
        print('Start slot vars', self.day.max(), self.start_slot.max())
        self.end_slot = MznVariable((pb.n_teacher, pb.n_slot), prefix='ls')
        print('Start slot vars', self.start_slot.max(), self.end_slot.max())
        cl = self.teacher_day_start_slot()
        mzn += self.to_mzn(cl, self.start_slot)
        cl = self.teacher_day_end_slot()
        mzn += self.to_mzn(cl, self.end_slot)

        ## TODO: calculate upper bound
        opt = 'var int: cost;\nconstraint cost = 2400 * n_day'
        assert(self.start_slot.cardinal() == self.end_slot.cardinal())
        for x in self.start_slot.range():
            t, s = self.start_slot.index(x)
            f = pb.slot[s]['start_time']
            opt += ' - %d * %s'%(f,self.start_slot.name(t,s))
        for x in self.end_slot.range():
            t, s = self.end_slot.index(x)
            f = pb.slot[s]['start_time'] + pb.slot[s]['duration']
            opt += ' + %d * %s'%(f,self.end_slot.name(t,s))
        opt += ';\n'
        #self.mzn = mzn + 'solve satisfy;\n'
        mzn += opt
        mzn += 'solve minimize cost;\n'
        self.mzn = mzn
        debug(self.var.cardinal() + self.start_slot.cardinal() + self.end_slot.cardinal(), 'variables')
        debug(mzn.count('\n') - 2, 'total clauses')

    def all_course(self):
        ## All courses must happen, whatever teacher or slot
        clause = ''
        NS, NT, NC = (self.pb.n_slot, self.pb.n_teacher, self.pb.n_course)
        for c in range(NC):
            cl = 'constraint'
            delim = ' '
            for t, s in it.product(range(NT), range(NS)):
                cl += delim + '%s'%self.var.name(t, c, s)
                delim = ' \/ '
            cl += ';\n'
            clause += cl
        debug(clause.count('\n'), 'clauses all courses')
        return clause

    def forall(self):
        cl_ts = ''
        cl_cd = ''
        for t, c, s in self.var:
            ## Teacher teaches the subject he/she knows
            if not self.pb.course_teacher[c, t]:
                cl_ts += 'constraint not %s;\n'%self.var.name(t,c,s)
            ## course duration and slot duration must match
            if not self.pb.course_slot[c, s]:
                cl_cd += 'constraint not %s;\n'%self.var.name(t,c,s)
        debug(cl_ts.count('\n'), 'clauses teacher - subject mapping')
        debug(cl_cd.count('\n'), 'clauses course duration - slot duration mapping')
        return (cl_ts, cl_cd)

    def overlap(self):
        cl_to = ''
        cl_go = ''
        NS, NT, NC = (self.pb.n_slot, self.pb.n_teacher, self.pb.n_course)
        for s1, s2 in it.product(range(NS), range(NS)):
            ## overlap[s][s] is always false
            if self.pb.slot_overlap[s1][s2]:
                ## Teacher slots cannot overlap
                for t, c1, c2 in it.product(range(NT), range(NC), range(NC)):
                    if c1 != c2:
                        cl_to += 'constraint not %s \/ not %s;\n'%(self.var.name(t, c1, s1), self.var.name(t, c2, s2))
                ## Class slots cannot overlap
                for c, t1, t2 in it.product(range(NC), range(NT), range(NT)):
                    if t1 != t2:
                        cl_go += 'constraint not %s \/ not %s;\n'%(self.var.name(t1, c, s1), self.var.name(t2, c, s2))
        debug(cl_to.count('\n'), 'clauses teacher no overlap')
        debug(cl_go.count('\n'), 'clauses class no overlap')
        return (cl_to, cl_go)

    def at_most_one(self):
        ## A course must only be given once
        clause = ''
        NS, NT, NC = (self.pb.n_slot, self.pb.n_teacher, self.pb.n_course)
        for c in range(NC):
            for t1, s1, t2, s2 in it.product(range(NT), range(NS), range(NT), range(NS)):
                if t1 != t2 or s1 != s2:
                    clause += 'constraint not %s \/ not %s;\n'%(self.var.name(t1, c, s1), self.var.name(t2, c, s2))
        debug(clause.count('\n'), 'clauses courses only once')
        return clause

    def teacher_day(self):
        ## Minimize total days worked
        NS, NT, NC = (self.pb.n_slot, self.pb.n_teacher, self.pb.n_course)
        clause = ''
        for t, d in self.day:
            cl = 'constraint not %s'%self.day.name(t,d)
            delim = ' '
            for s, c in it.product(range(NS), range(NC)):
                if self.pb.slot_day[s, d]:
                    cl += ' \/ ' + '%s'%self.var.name(t,c,s)
                    cl2 = 'constraint not %s \/ %s;\n'%(self.var.name(t,c,s), self.day.name(t,d))
                    clause += cl2
            cl += ';\n'
            clause += cl
        clause = 'array[1..%d] of var bool: d;\n'%self.day.cardinal() + clause
        clause += 'var 0..%d: n_day;\nconstraint n_day = sum(d);\n'%self.day.cardinal()
        debug(clause.count('\n') - 3, 'day clauses')
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

    def get_var(self, n):
        for v in (self.var, self.day, self.start_slot, self.end_slot):
            if n in v.range():
                return v

    def to_mzn(self, clause, var):
        s = 'int: N%s = %d;\n'%(var.prefix, var.cardinal())
        s += 'array[1..N%s] of var bool: %s;\n'%(var.prefix,var.prefix)
        for cl in clause:
            s += 'constraint '
            delim = ''
            for o in cl:
                s += delim
                if o < 0:
                    v = self.get_var(-o)
                    s += 'not %s'%v.vname(v.index(-o))
                else:
                    v = self.get_var(o)
                    s += '%s'%v.vname(v.index(o))
                delim = ' \/ '
            s += ';\n'
        return s;

    def __str__(self):
        return self.mzn

