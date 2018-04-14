import sys
import numpy as np
import itertools as it
import s_expression.s_expression as se
from collections import OrderedDict
import sat.solve
import sat.build
import mzn.build
import logic
import variable

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
                    overlap[s+i,s+j] = True
                    continue
                s1, d1 = d['slot'][i]
                s2, d2 = d['slot'][j]
                ## if s1 + d1 == s2, we dont consider there is overlap
                if s1 + d1 > s2 and s2 + d2 > s1:
                    overlap[s+i,s+j] = True
                    overlap[s+j,s+i] = True
            s += len(d['slot'])
        assert(s == N)
        self.n_slot = N
        self.slot_overlap = overlap

    def comp_slot_overlap_2(self):
        N = self.n_slot
        overlap = np.zeros((N,N), dtype='b')
        for i, j in it.combinations(range(N), 2):
            #if i == j:
            #    ## A slot is not considered overlapping with itself
            #    continue
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
        for i in range(N):
            overlap[i,i] = True
        assert(overlap.shape == self.slot_overlap.shape)
        assert(np.all(overlap == self.slot_overlap))

    def comp_slot_order(self):
        """ Build the slot ordering matrix. Slots are only ordered within a
        single day. Slots that overlap are not ordered.
        slot_order[i,j] == True iff slot i is before slot j
                                iff slot j is after slot i"""
        N = self.n_slot
        slot_order = np.zeros((N, N), dtype='b')
        for s1, s2 in it.combinations(range(N), 2):
            if self.slot[s1]['day'] != self.slot[s2]['day']:
                ## Slots are in different days: we only order slots within a day
                continue
            if self.slot_overlap[s1, s2]:
                ## Overlapping slots are not ordered, since typically they are
                ## mutually excluded for a single teacher or a single group
                continue
            ## Start times cannot be equal here otherwise slots would overlap
            if self.slot[s1]['start_time'] < self.slot[s2]['start_time']:
                ## s1 is before s2
                slot_order[s1, s2] = True
            else:
                ## s2 is before s1
                slot_order[s2, s1] = True
        self.slot_order = slot_order
        #debug(slot_order)

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
        self.comp_slot_order()
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
    ## TODO: check no slot with duration == 0
    pb.build()
    #debug(pb)
    if 1:
        sol = mzn.build.MznBuild(pb)
        s = str(sol)
        f = open('sat.mzn', 'wt')
        f.write(s)
        f.close()

    variable.Variable.reset()

    if 1:
        sol = sat.build.SatBuild(pb)
        #debug(sol.cnf)
        s = str(sol)
        f = open('sat.cnf', 'wt')
        f.write(s)
        f.close()
    
    if 1:
        sol = sat.solve.solve(sol.cnf, a=True)
        debug('%d solutions'%len(sol))
        if 0:
            debug(sol)

