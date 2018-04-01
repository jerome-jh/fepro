import sys
import numpy as np
import itertools as it
import s_expression.s_expression as se
from collections import OrderedDict
import sat.solve

np.set_printoptions(threshold=np.nan)

def debug(*args):
    print(*args, file=sys.stderr)

def expect_all(ll, name_list):
    """ Verify all names occur as 'key' in entity """
    v = [False] * len(name_list)
    for e in ll:
        for i, n in enumerate(name_list):
            if e[0] == n:
                v[i] = True
    r = True
    for b in v:
        r = r and b
    return r

def to_dict(ll):
    """ Turn a subtree into a dictionnary """
    d = OrderedDict()
    if type(ll[0]) != type([]):
        ## Very ugly!
        ll = [ll]
    for e in ll:
        car = e[0]
        cdr = e[1:]
        if len(cdr) == 1:
            d[car] = cdr[0]
        else:
            d[car] = cdr
    return d

def merge_dict(d1, d2):
    """ Merge dictionaries for Python3.4 that does not have the {**d1, **d2}
        syntax.
        If dictionaries have keys in common, values from d2 overwrite those from
        d1. """
    for k, v in d2.items():
        d1[k] = v

def mextend(l, iter_of_iter):
    for i in iter_of_iter:
        l.extend(i)

def mcat(s, iter_of_str):
    for i in iter_of_str:
        s += i
    return s

class Problem:
    def __init__(self):
        self.teacher = list()
        self.level = list()
        self.day_type = OrderedDict()
        self.day = list()
        self.level = OrderedDict()
        self.group = OrderedDict()

    def add_teacher(self, ll):
        r = expect_all(ll, ['name', 'subject'])
        if not r:
            raise Exception('teacher ' + str(ll) + ' is missing required fields')
        self.teacher.append(to_dict(ll))

    def add_day_type(self, ll):
        r = expect_all(ll, ['name', 'slot'])
        if not r:
            raise Exception('day_type ' + str(ll) + ' is missing required fields')
        d = to_dict(ll)
        self.day_type[d['name']] = d['slot']

    def add_day(self, ll):
        r = expect_all(ll, ['name', 'type'])
        self.day.append(to_dict(ll))

    def add_level(self, ll):
        r = expect_all(ll, ['name', 'subject'])
        if not r:
            raise Exception('level ' + str(ll) + ' is missing required fields')
        d = to_dict(ll)
        self.level[d['name']] = to_dict(d['subject'])

    def add_group(self, ll):
        r = expect_all(ll, ['name', 'level'])
        if not r:
            raise Exception('group ' + str(ll) + ' is missing required fields')
        d = to_dict(ll)
        v = OrderedDict()
        v['level'] = d['level']
        self.group[d['name']] = v

    def resolve_day(self):
        """ Map day to slot, resolving day_type """
        n_day = len(self.day)
        for v in self.day:
            v['slot'] = self.day_type[v['type']]
        self.n_day = n_day
        self.day_type = None
        debug('%d days'%self.n_day)
        #debug(self.day)

    def resolve_group(self):
        """ Map group to subject, resolving level """
        for k, v in self.group.items():
            self.group[k]['subject'] = self.level[v['level']]
        self.level = None

    def comp_slot(self):
        """ Build the list of slots available """
        slot = list()
        for v1 in self.day:
            for v2 in v1['slot']:
                s = dict()
                s['day'] = v1['name']
                s['start_time'] = v2[0]
                s['duration'] = v2[1]
                slot.append(s)
        self.n_slot = len(slot)
        self.slot = slot
        debug('%d slots'%self.n_slot)

    def comp_slot_day(self):
        """ Build the slot to day mapping matrix """
        self.slot_day = np.ndarray((self.n_slot, self.n_day), dtype='b')
        for i, j in it.product(range(self.n_slot), range(self.n_day)):
            self.slot_day[i,j] = self.slot[i]['day'] == self.day[j]['name']
        #debug(self.slot_day)

    def comp_slot_overlap(self):
        """ Build the matrix indicating slots that overlap.
            A slot is not considered to overlap with itself, so the diagonal
            is all zeros. The matrix is symetric. """
        N = self.n_slot
        overlap = np.zeros((N,N), dtype='b')
        ## Slots cannot overlap from one day to another, so treat day by day
        s = 0
        for d in self.day:
            for i, j in it.product(range(len(d['slot'])), range(len(d['slot']))):
                if i == j:
                    ## A slot is not considered overlapping with itself
                    continue
                s1, d1 = d['slot'][i]
                s2, d2 = d['slot'][j]
                ## if s1 + d1 == s2, we dont consider there is overlap
                if s1 + d1 > s2 and s2 + d2 > s1:
                    overlap[s+i,s+j] = True
                    overlap[s+j,s+i] = True
            s += len(d['slot'])
        assert(s == N)
        #debug(overlap)
        self.n_slot = N
        self.slot_overlap = overlap

    def comp_slot_overlap_2(self):
        N = self.n_slot
        overlap = np.zeros((N,N), dtype='b')
        for i, j in it.product(range(N), range(N)):
            if i == j:
                ## A slot is not considered overlapping with itself
                continue
            if self.slot[i]['day'] != self.slot[j]['day']:
                ## Slots cannot overlap from one day to another
                continue
            s1 = self.slot[i]['start_time']
            d1 = self.slot[i]['duration']
            s2 = self.slot[j]['start_time']
            d2 = self.slot[j]['duration']
            ## if s1 + d1 == s2, we dont consider there is overlap
            if s1 + d1 > s2 and s2 + d2 > s1:
                 overlap[i,j] = True
                 overlap[j,i] = True
        assert(overlap.shape == self.slot_overlap.shape)
        assert(np.all(overlap == self.slot_overlap))

    def comp_teacher_subject(self):
        """ Build the teacher to subject matrix """
        ## We would actually like an OrderedSet
        subject = OrderedDict()
        for t in self.teacher:
            for s in t['subject']:
                subject[s] = 0
        subject = subject.keys()
        ## Check there is teacher for every subject
        for g in self.group.values():
            for s in g['subject'].keys():
                if s not in subject:
                    raise Exception("no teacher for subject '%s' (%s)"%(s, subject))
        N = len(self.teacher)
        M = len(subject)
        tm = np.zeros((N, M), dtype='b')
        for i, t in enumerate(self.teacher):
            for j, s in enumerate(subject):
                if s in t['subject']:
                    tm[i,j] = True
        debug('%d teachers'%N)
        debug('%d subjects'%M)
        #debug(tm)
        self.n_teacher = N
        self.n_subject = M
        self.subject = subject
        self.teacher_subject = tm

    def comp_course(self):
        """ Build the list of courses that must be given """
        course = list()
        for k1, v1 in self.group.items():
            for k2, v2 in v1['subject'].items():
                for v3 in v2:
                    c = dict()
                    c['group'] = k1
                    c['level'] = v1['level']
                    c['subject'] = k2
                    c['duration'] = v3
                    course.append(c)
        self.n_course = len(course)
        self.course = course
        debug('%d courses'%self.n_course)

    def comp_course_slot(self):
        """ Compute the course slot mapping matrix """
        N = self.n_course
        M = self.n_slot
        cs = np.zeros((N, M), dtype='b')
        for i, c in enumerate(self.course):
            for j, s in enumerate(self.slot):
                cs[i,j] = (c['duration'] == s['duration'])
        self.course_slot = cs

    def comp_course_teacher(self):
        """ Compute the course to teacher mapping matrix """
        N = self.n_course
        M = self.n_teacher
        ct = np.zeros((N, M), dtype='b')
        for i, c in enumerate(self.course):
            for j, t in enumerate(self.teacher):
                ct[i,j] = (c['subject'] in t['subject'])
        self.course_teacher = ct
        #debug(self.course_teacher)

    def comp_teacher_overlap(self):
        """ Courses given by specific teacher cannot overlap """
        pass

    def build(self):
        """ Build various tables from the input data """
        self.resolve_day()
        self.resolve_group()
        self.comp_slot()
        self.comp_slot_day()
        self.comp_slot_overlap()
        self.comp_slot_overlap_2()
        self.comp_teacher_subject()
        self.comp_course()
        self.comp_course_slot()
        self.comp_course_teacher()

    def flatten(self):
        """ Turn the problem into a (big) bunch of booleans """
        self.comp_teacher_overlap()

    def to_mzn(self):
        pass

    def __str__(self):
        return '\n'.join((str(self.teacher), str(self.level), str(self.day_type), str(self.day), str(self.group)))

class SatBuild:
    def __init__(self, problem):
        self.pb = problem
        self.var = SatVariable((pb.n_teacher, pb.n_course, pb.n_slot))
        cnf = list()
        mextend(cnf, self.forall())
        mextend(cnf, self.overlap())
        cnf.extend(self.all_course())
        cnf.extend(self.at_most_one())
        self.cnf = cnf
        debug(self.var.cardinal(), 'variables')
        debug(len(cnf), 'total clauses')

    def all_course(self):
        ## All courses must happen, whatever teacher or slot
        pb = self.pb
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
            if not pb.course_teacher[c, t]:
                cl_ts.append([-self.var.number(t,c,s)])
            ## course duration and slot duration must match
            if not pb.course_slot[c, s]:
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
                    cl_to.append([-self.var.number(t, c1, s1), -self.var.number(t, c2, s2)])
                ## Class slots cannot overlap
                for c, t1, t2 in it.product(range(NC), range(NT), range(NT)):
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

class MznBuild:
    def __init__(self, problem):
        self.pb = problem
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
        pb = self.pb
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
            if not pb.course_teacher[c, t]:
                cl_ts += 'constraint not %s;\n'%self.var.name(t,c,s)
            ## course duration and slot duration must match
            if not pb.course_slot[c, s]:
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
        cl = ''
        for t, d in self.day:
            cl += 'constraint %s ='%self.day.name(t,d)
            delim = ' '
            for s, c in it.product(range(NS), range(NC)):
                if self.pb.slot_day[s, d]:
                    cl += delim + '%s'%self.var.name(t,c,s)
                    delim = ' \/ '
            cl += ';\n'
        cld = 'array[1..%d] of var bool: d;\n'%self.day.cardinal()
        cld += cl
        cld += 'var 0..%d: n_day;\nconstraint n_day = sum(d);\n'%self.day.cardinal()
        debug(cl.count('\n'), 'day clauses')
        debug(cl.count('\/') + 3, 'variables in day clauses')
        return cld

    def __str__(self):
        return self.mzn

class Variable:
    def __init__(self, vect, prefix='x', offset=0):
        """ vect[0] is the slower varying index, vect[N-1] the faster varying index """
        N = len(vect)
        base = np.ndarray((N+1,), dtype='u4')
        base[0] = 1
        base[1:] = np.flipud(np.asarray(vect, dtype='u4'))
        self.base = np.flipud(np.cumprod(base, dtype='u4'))
        self.vect = vect
        self.offset = offset

    def cardinal(self):
        return self.base[0]

    def vnumber(self, vect):
        assert(len(vect) == len(self.vect))
        return np.dot(self.base[1:], vect) + self.offset

    def number(self, *args):
        return self.vnumber(args)

    def vname(self, vect):
        return self.prefix + str(super.vnumber(vect))

    def name(self, *args):
        return self.vname(args)

    def index(self, n):
        assert(n >= self.offset and n < self.offset + v.cardinal())
        N = self.base.shape[0]-1
        idx = np.ndarray((N,), dtype='u4')
        n -= self.offset
        for i in range(N-1, -1, -1):
            idx[i] = n % self.vect[i]
            n = (n - idx[i]) // self.vect[i]
        return idx

    def __iter__(self):
        """ Iterate other indices """
        return it.product(*map(range, self.vect))

    def check(self):
        """ Debug function: check consistency of self.index and self.number """
        i = self.offset
        for tu in self:
            assert(self.vnumber(tu) == i)
            i += 1
        tu = iter(self)
        for i in range(self.offset, self.offset + self.cardinal()):
            assert(np.all(self.index(i) == np.asarray(tu.__next__(), dtype='u4')))

    def debug(self):
        for i,j,k in v:
            debug((i,j,k),v.number(i,j,k))
        for n in range(self.offset, self.offset + v.cardinal()):
            debug(n,v.index(n))

class SatVariable(Variable):
    def __init__(self, vect):
        super().__init__(vect, offset=1, prefix='')

    def vnumber(self, vect):
        assert(len(vect) == len(self.vect))
        ## Convert to Python int (otherwise this is a Numpy int)
        return int(np.dot(self.base[1:], vect) + self.offset)

class MznVariable(Variable):
    def __init__(self, vect, prefix='x'):
        super().__init__(vect, offset=1, prefix=prefix)
        self.prefix = prefix

    def vname(self, vect):
        return '%s[%d]'%(self.prefix, super().vnumber(vect))

def load_tuple(filename):
    s = open(filename).read(-1)
    return eval(s.replace('\n','').replace('\r',''))

if __name__ == '__main__':
    if True:
        r = se.Parser().loadf(sys.argv[1])
        ll = r.to_list()
    else:
        ll = load_tuple(sys.argv[1])
    pb = Problem()
    for e in ll:
        if e[0] == 'teacher':
            pb.add_teacher(e[1])
        elif e[0] == 'level':
            pb.add_level(e[1:])
        elif e[0] == 'day_type':
            pb.add_day_type(e[1:])
        elif e[0] == 'day':
            pb.add_day(e[1:])
        elif e[0] == 'group':
            pb.add_group(e[1:])
    ## TODO: check uniqueness of teacher, level, etc...
    pb.build()
    #debug(pb)
    sol = MznBuild(pb)
    s = str(sol)
    f = open('sat.mzn', 'wt')
    f.write(s)
    f.close()

    sol = SatBuild(pb)
    #debug(sol.cnf)
    s = str(sol)
    f = open('sat.cnf', 'wt')
    f.write(s)
    f.close()
    
    if 1:
        sol = sat.solve.solve(sol.cnf, a=True)
        debug('%d solutions'%len(sol))
        if 1:
            debug(sol)

    v = Variable((4, 2, 2))
    v.check()
    v = Variable((4, 2, 2), offset=1)
    v.check()
