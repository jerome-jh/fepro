import numpy as np
import itertools as it
#from variable import *
from sparse_variable import *
import logic

def nonzero(l):
    a = np.asarray(l)
    return list(map(int, a[np.nonzero(a)]))

class Model:
    def __init__(self, pb):
        self.pb = pb

        ## Clauses in CNF format
        self.cnf = list()

        ##
        ## Satisfaction constraints
        ##
        ## Variables for teacher, course and slot assignement
        self.var = SparseVariable((pb.n_teacher, pb.n_course, pb.n_slot), 'x')
        self.match()
        self.all_course()
        self.overlap()
        self.at_most_one()

        ##
        ## Optimization constraints
        ##
        ## For every teacher, tell if teacher works on specific day 
        self.day = SparseVariable((pb.n_teacher, pb.n_day), 'd')
        ## Start slot for every teacher: true if slot is the first slot of a day for teacher t
        self.start_slot = SparseVariable((pb.n_teacher, pb.n_slot), 'fs')
        ## End slot for every teacher: true if slot is the las slot of a day for teacher t
        self.end_slot = SparseVariable((pb.n_teacher, pb.n_slot), 'ls')

        cl1 = self.teacher_day()
        cl2 = self.teacher_day_2()
        #assert(cl1 == cl2)
        self.cnf.extend(cl1)
        self.teacher_day_start_slot()
        self.teacher_day_end_slot()

        SparseVariable.update()
        debug(SparseVariable.tot_last(), 'total variables')
        debug(len(self.cnf), 'total clauses')

        ##
        ## Optimization goal
        ##
        self.obj = list()
        self.objective()

    def all_course(self):
        ## All courses must happen, whatever teacher or slot
        clause = list()
        NS, NT, NC = (self.pb.n_slot, self.pb.n_teacher, self.pb.n_course)
        for c in range(NC):
            cl = list()
            for t, s in it.product(range(NT), range(NS)):
                if self.var.number(t, c, s):
                    cl.append(self.var.number(t, c, s))
            clause.append(cl)
        debug(len(clause), 'clauses all courses')
        assert(len(clause) == NC)
        self.cnf.extend(clause)

    def match(self):
        ## Match teacher and course subject
        ## Match course duration and slot duration
        for t, c, s in self.var:
            ## Teacher teaches the subject he/she knows
            ## course duration and slot duration must match
            if self.pb.course_teacher[c, t] and self.pb.course_slot[c, s]:
                self.var.new(t,c,s)
        debug(self.var.max(), 'variables')

    def overlap(self):
        cl_to = list()
        cl_go = list()
        NS, NT, NC = (self.pb.n_slot, self.pb.n_teacher, self.pb.n_course)
        for s1, s2 in it.product(range(NS), range(NS)):
            if self.pb.slot_overlap[s1][s2]:
                ## Must be careful not to add a constraint -x \/ -x
                ## Teacher slots cannot overlap
                for t, (c1, c2) in it.product(range(NT), it.combinations(range(NC), 2)):
                    if self.var.number(t, c1, s1) and self.var.number(t, c2, s2):
                        cl_to.append([-self.var.number(t, c1, s1), -self.var.number(t, c2, s2)])
                ## Class slots cannot overlap
                for c, (t1, t2) in it.product(range(NC), it.combinations(range(NT), 2)):
                    if self.var.number(t1, c, s1) and self.var.number(t2, c, s2):
                        cl_go.append([-self.var.number(t1, c, s1), -self.var.number(t2, c, s2)])
        debug(len(cl_to), 'clauses teacher no overlap')
        debug(len(cl_go), 'clauses class no overlap')
        self.cnf.extend(cl_to)
        self.cnf.extend(cl_go)

    def at_most_one(self):
        ## Make sure a course is not given multiple times
        clause = list()
        NS, NT, NC = (self.pb.n_slot, self.pb.n_teacher, self.pb.n_course)
        for c in range(NC):
            for (t1, t2) in it.product(range(NT), range(NT)):
                for (s1, s2) in it.combinations(range(NS), 2):
                    if self.var.number(t1, c, s1) and self.var.number(t2, c, s2):
                        clause.append([-self.var.number(t1, c, s1), -self.var.number(t2, c, s2)])
            for (s1, s2) in it.product(range(NS), range(NS)):
                for (t1, t2) in it.combinations(range(NT), 2):
                    if self.var.number(t1, c, s1) and self.var.number(t2, c, s2):
                        clause.append([-self.var.number(t1, c, s1), -self.var.number(t2, c, s2)])
        debug(len(clause), 'clauses courses only once')
        self.cnf.extend(clause)

    def teacher_day(self):
        """ Minimize total days worked """
        NS, NT, NC = (self.pb.n_slot, self.pb.n_teacher, self.pb.n_course)
        clause = list()
        for t, d in self.day:
            cl = [ -self.day.number(t,d) ]
            for s, c in it.product(range(NS), range(NC)):
                if self.pb.slot_day[s, d] and self.var.number(t,c,s):
                    cl.append(self.var.number(t,c,s))
                    cl2 = [ -self.var.number(t,c,s), self.day.number(t,d) ]
                    clause.append(cl2)
            clause.insert(0, cl)
        debug(len(clause), 'day clauses')
        #print(clause)
        return clause

    def teacher_day_2(self):
        """ Minimize total days worked """
        NS, NT, NC = (self.pb.n_slot, self.pb.n_teacher, self.pb.n_course)
        clause = list()
        for t, d in self.day:
            q = list()
            for s, c in it.product(range(NS), range(NC)):
                if self.pb.slot_day[s, d] and self.var.number(t,c,s):
                    q.append(self.var.number(t,c,s))
            clause.extend(logic.to_sat(logic.CNF(logic.EQ(self.day.number(t,d), logic.OR(*q)))))
        debug(len(clause), 'day clauses')
        #print(clause)
        return clause

    def teacher_day_start_slot(self):
        ## Set of booleans, one of them is true indicating the first busy slot
        ## of the day
        NS, NT, NC = (self.pb.n_slot, self.pb.n_teacher, self.pb.n_course)
        clause = list()
        for t, s in self.start_slot:
            self.start_slot.new(t, s)
            ## List all the courses that are mappable to this slot
            first = list()
            for c in range(NC):
                if self.var.number(t, c, s):
                    first.append(self.var.number(t, c, s))
            if not len(first):
                continue
            idx = np.where(self.pb.slot_order[:,s])[0]
            if len(idx):
                ## Slot has other slots before him: if this is the first slot
                ## none of them should be true
                before = list()
                for s2 in idx:
                    for c in range(NC):
                        if self.var.number(t, c, s2):
                            before.append(-self.var.number(t, c, s2))
                ## This slot is first if one of the courses occupies it and
                ## none of the slots before is busy
                if len(before):
                    if len(first) > 1:
                        exp = logic.EQ(self.start_slot.number(t, s), logic.AND(logic.OR(*first), *before))
                    else:
                        exp = logic.EQ(self.start_slot.number(t, s), logic.AND(first[0], *before))
            else:
                ## Slot is the first in the day: it is the starting slot if
                ## actually busy
                if len(first) > 1:
                    exp = logic.EQ(self.start_slot.number(t, s), logic.OR(*first))
                else:
                    ## TODO: optim here
                    exp = logic.EQ(self.start_slot.number(t, s), first[0])
            exp = logic.CNF(exp)
            clause.extend(logic.to_sat(exp))
        debug(len(clause), 'first slot clauses')
        self.cnf.extend(clause)

    def teacher_day_end_slot(self):
        ## Set of booleans, one of them is true indicating the last busy slot
        ## of the day
        NS, NT, NC = (self.pb.n_slot, self.pb.n_teacher, self.pb.n_course)
        clause = list()
        for t, s in self.end_slot:
            self.end_slot.new(t, s)
            ## List all the courses that are mappable to this slot
            last = list()
            for c in range(NC):
                if self.var.number(t, c, s):
                    last.append(self.var.number(t, c, s))
            if not len(last):
                continue
            idx = np.where(self.pb.slot_order[s])[0]
            if len(idx):
                ## Slot has other slots after him: if this is the last slot
                ## none of them should be true
                after = list()
                for s2 in idx:
                    for c in range(NC):
                        if self.var.number(t, c, s2):
                            after.append(-self.var.number(t, c, s2))
                ## This slot is last if one of the courses occupies it and
                ## none of the slots after is busy
                if len(after):
                    if len(last) > 1:
                        exp = logic.EQ(self.end_slot.number(t, s), logic.AND(logic.OR(*last), *after))
                    else:
                        exp = logic.EQ(self.end_slot.number(t, s), logic.AND(last[0], *after))
            else:
                ## Slot is the last in the day: it is the ending slot if
                ## actually busy
                if len(last) > 1:
                    exp = logic.EQ(self.end_slot.number(t, s), logic.OR(*last))
                else:
                    exp = logic.EQ(self.end_slot.number(t, s), last[0])
            exp = logic.CNF(exp)
            clause.extend(logic.to_sat(exp))
        debug(len(clause), 'end slot clauses')
        self.cnf.extend(clause)

    def objective(self):
        obj_d = list()
        for d in self.day.range():
            obj_d.append([2400, d])
        self.obj.extend(obj_d)

        obj_s = list()
        for x in self.start_slot.range():
            t, s = self.start_slot.index(x)
            f = self.pb.slot[s]['start_time']
            obj_s.append([-f, x])
        self.obj.extend(obj_s)

        obj_e = list()
        for x in self.end_slot.range():
            t, s = self.end_slot.index(x)
            f = self.pb.slot[s]['start_time'] + self.pb.slot[s]['duration']
            obj_e.append([f, x])
        self.obj.extend(obj_e)

    def get_var(self, n):
        for v in (self.var, self.day, self.start_slot, self.end_slot):
            if n in v.range():
                return v

    def to_mzn(self):
        s = ''
        ## Satisfaction
        for v in (self.var, self.day, self.start_slot, self.end_slot):
            s += 'int: N%s = %d;\n'%(v.name,v.cardinal())
            s += 'array[1..N%s] of var bool: %s;\n'%(v.name,v.name)
        for cl in self.cnf:
            s += 'constraint '
            delim = ''
            for o in cl:
                s += delim
                if o < 0:
                    v = self.get_var(-o)
                    s += 'not %s[%d]'%(v.name, -o - v.offset + 1)
                else:
                    v = self.get_var(o)
                    s += '%s[%d]'%(v.name, o - v.offset + 1)
                delim = ' \/ '
            s += ';\n'
        ## Objective
        s += "var int: obj;\nconstraint obj = 0"
        for o in self.obj:
            v = self.get_var(o[1])
            if o[0] < 0:
                s += " - %d * %s[%d]"%(-o[0], v.name, o[1] - v.offset + 1)
            else:
                s += " + %d * %s[%d]"%(o[0], v.name, o[1] - v.offset + 1)
        s += ";\nsolve minimize obj;\n"
        return s;

    def to_dimacs(self):
        """ Output satisfaction variables only """
        N = len(self.cnf)
        s = 'p cnf ' + str(self.var.last()) + ' ' + str(N) + '\n'
        for i in range(N):
            cl = self.cnf[i]
            for j in range(len(cl)):
                s += str(cl[j]) + ' '
            s += '0\n'
        return s

    def to_opb(self):
        ## SCIP requires the plus signs
        #s = '* #variable= %d #constraint= %d\nmin:'%(Variable.offset - 1, len(self.cnf))
        s = '* #variable= %d #constraint= %d\nmin:'%(self.end_slot.last(), len(self.cnf))
        for o in self.obj:
            v = self.get_var(o[1])
            if o[0] < 0:
                s += " %d x%d"%(o[0], o[1])
            else:
                s += " +%d x%d"%(o[0], o[1])
        s += ';\n'
        for cl in self.cnf:
            lim = 1
            for o in cl:
                if o < 0:
                    v = self.get_var(-o)
                    s += '-1 x%d '%(-o)
                    lim -= 1
                else:
                    v = self.get_var(o)
                    s += '+1 x%d '%(o)
            s += '>= %d;\n'%lim
        return s

