import sys
import numpy as np
import itertools as it
from variable import *

def debug(*args):
    print(*args, file=sys.stderr)

def mcat(s, iter_of_str):
    for i in iter_of_str:
        s += i
    return s

class MznVariable(Variable):
    def __init__(self, vect, prefix='x'):
        super().__init__(vect, offset=1, prefix=prefix)
        self.prefix = prefix

    def vname(self, vect):
        return '%s[%d]'%(self.prefix, super().vnumber(vect))

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
        #self.mzn = mzn + 'solve satisfy;\n'
        self.mzn = mzn + 'solve minimize n_day;\n'
        debug(self.var.cardinal(), 'variables')
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
                    cl_to += 'constraint not %s \/ not %s;\n'%(self.var.name(t, c1, s1), self.var.name(t, c2, s2))
                ## Class slots cannot overlap
                for c, t1, t2 in it.product(range(NC), range(NT), range(NT)):
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

    def __str__(self):
        return self.mzn

