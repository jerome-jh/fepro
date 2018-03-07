#!/usr/bin/python3

import re
import sys
import datetime
import numpy as np

def debug(*args):
    print(*args, file=sys.stderr)

def to_time(s):
    i = int(s)
    h = i // 100
    m = int((i % 100) * 60 / 100)
    return datetime.time(hour = h, minute = m)

def to_timedelta(s):
    i = int(s)
    h = i // 100
    m = int((i % 100) * 60 / 100)
    return datetime.timedelta(hours = h, minutes = m)

class html_output:
    def __init__(self, f):
        self.f = f
        self.print('<!DOCTYPE html><html><body>')
        self.print('<style>')
        self.print('table, th, td {')
        self.print('border: 1px solid black; border-collapse: collapse;')
        self.print('}')
        self.print('th { background-color: #dddddd; }')
        self.print('td.nocourse { background-color: #dddddd; }')
        self.print('</style>')
        self.print('<body>')

    def exit(self):
        self.print('</body></html>')

    def print(self, *args):
        print(*args, file=self.f, sep='')

    def start_schedule(self, title):
        self.print('<h3>', title, '</h3><table>')

    def end_schedule(self):
        for j, d in enumerate(self.axis_1):
            ## New row
            self.print('<tr>')
            ## Left header column
            self.print('<th>', str(d), '</th>')
            ## Output row of data
            for i in range(self.X):
                if self.data[i][j] != '':
                    self.print(self.data[i][j])
                else:
                    self.print('<td class="nocourse"></td>')
            self.print('</tr>')
        self.print('</table>')

    def set_axis(self, axis_0, axis_1):
        """ Axis 0 is the slower moving axis
            Axis 1 is the faster moving axis """
        self.X = len(axis_0)
        self.Y = len(axis_1)
        self.data = [[ '' ] * self.Y  for i in range(self.X)]
        ## Output table header
        self.print('<tr>')
        ## Empty upper left cell
        self.print('<th></th>')
        for d in axis_0:
            self.print('<th>', str(d), '</th>')
        self.print('</tr>')
        ## Keep axis_1
        self.axis_1 = axis_1

    def set_data(self, i, j, *args):
        s = ''
        for a in args:
            s = s + str(a) + '<br>'
        self.data[i][j] = '<td>' + s + '</td>'
        ##TODO: Check if same as upper or lower row and merge cells if yes

def schedule_debug(idx, courses):
    """ output the courses selected by the indices as a schedule """
    idx = courses.sort_by_day(idx)
    days = np.unique(courses.get_day(idx))
    for d in days:
        #debug('day:', d)
        idx2 = courses.select_day(d, idx)
        idx2 = courses.sort_by_start_time(idx2)
        for j in idx2:
            debug('start_time: ', courses.get_start_time(j))
            debug('start_time: ', courses.get_subject(j))
            debug('teacher: ', courses.get_teacher(j))
            debug('level: ', courses.get_level(j))

def schedule_by_row(out, idx, courses):
    days = np.unique(courses.get_day(idx))
    times = np.unique(courses.get_time(idx))
    out.set_axis(days, times) 

    idx = courses.sort_by_day(idx)
    actual_days = np.unique(courses.get_day(idx))
    for i, d in enumerate(days):
        #crappy
        if not d in actual_days:
            continue
        idx2 = courses.select_day(d, idx)
        idx2 = courses.sort_by_start_time(idx2)
        actual_times = courses.get_time(idx2)
        for j, t in enumerate(times):
            #crappy too
            for k, at in zip(idx2, actual_times):
                if t == at:
                    d = (courses.get_subject(k), courses.get_teacher(k), courses.get_level(k), courses.get_group(k))
                    #debug(i, j, *d)
                    out.set_data(i, j, *d)
                    break

def level_schedule(out, l, g, idx, courses):
    out.start_schedule('Level: %s Group: %d'%(l, g))
    schedule_by_row(out, idx, courses)
    out.end_schedule()

def all_level_schedule(out, courses):
    for l in courses.unique_level():
        idx = courses.select_level(l)
        group = np.unique(courses.get_group(idx))
        for g in group:
            idx2 = courses.select_group(g, idx)
            level_schedule(out, l, g, idx2, courses)

def teacher_schedule(out, t, courses):
    out.start_schedule('Teacher: %s'%t)
    idx = courses.select_teacher(t)
    schedule_by_row(out, idx, courses)
    out.end_schedule()

def all_teacher_schedule(out, courses):
    for t in courses.unique_teacher():
        teacher_schedule(out, t, courses)

class Courses:
    """ Class acting as the courses database, allowing to select and retrieve
    particular courses. """

    input_dict = {
        'course_level': str,
        'course_class': int,
        'course_subject': str,
        'course_day': int,
        'course_start_time': to_timedelta,
        'course_duration': to_timedelta,
        #TODO: course_teacher
        'teacher': str
    }

    attributes = ['level', 'group', 'subject', 'day', 'start_time', 'duration', 'teacher']

    def __init__(self, *args):
        assert(len(Courses.attributes) == len(args))
        ## All arguments shall have the same size
        n_courses = [ arg.shape for arg in args ]
        assert(np.unique(n_courses).shape == (1,))
        n_courses = n_courses[0]
        ## Arguments shall be unidimensional
        assert(len(n_courses) == 1)
        self.N = n_courses[0]
        for att, arg in zip(Courses.attributes, args):
            setattr(self, att, arg)
        ## Compute end times and store them
        self.end_time = self.start_time + self.duration
        ## All known times, start and end
        self.time = np.concatenate((self.start_time, self.end_time))
        ## Caching dictionnary for attributes unique values
        self.unique = dict()
        #debug(self.N)
        #debug(self.teacher)

    def parse(f):
        regout = re.compile(r"^(\w+)\s*=\s*\[([\w\s,]*)\]\s*;$")
        regin = re.compile(r"\s*(\w+)\s*(?:[,$])")
        regobj = re.compile(r"^(\w+)\s*=\s*(\d+)\s*;$")
        regstat = re.compile(r"----------")
        ## TODO: crappy beyond that point
        for l in f:
            m = regout.match(l)
            if m:
                name = m.group(1)
                try:
                    values = list(map(Courses.input_dict[name], regin.findall(m.group(2))))
                    globals()[name] = values
                except KeyError:
                    debug("Unknown value", name)
            else:
                m = regstat.match(l)
                if m:
                    debug("status", l)
                else:
                    pass
                    #TODO
                    #raise(RuntimeError("Badly formatted input: " + l))

    def to_numpy():
        for n in Courses.input_dict.keys():
            v = globals()[n]
            t = Courses.input_dict[n]
            if t == int:
                globals()[n] = np.asarray(v, dtype='i4')
            elif t == to_time:
                globals()[n] = np.asarray(v, dtype='O')
            elif t == to_timedelta:
                globals()[n] = np.asarray(v, dtype='O')
            elif t == str:
                m = max([ len(s) for s in v ])
                globals()[n] = np.asarray(v, dtype='S%d'%m)
            else:
                raise(RuntimeError(n))

    def __select(self, attr, value, idx=None):
        """ Return indices where attribute has value

        idx: if not None, used to select a subset to start from
        """
        a = getattr(self, attr)
        if type(idx) != type(None):
            idx2 = np.where(a[idx] == value)[0]
            return idx[idx2]
        else:
            return np.where(a == value)[0]

    def __get(self, attr, idx):
        """ Return values of attribute at indices """
        a = getattr(self, attr)
        return a[idx]

    def __unique(self, attr):
        """ Return the sorted unique values of attribute

        TODO: would be nice to be able to select a subset """
        if attr not in self.unique.keys():
            a = getattr(self, attr)
            v, idx1 = np.unique(a, return_index=True)
            idx2 = np.argsort(a[idx1])
            self.unique[attr] = a[idx1[idx2]]
        return self.unique[attr]

    def __sort_by(self, attr, idx):
        """ Sort the attribute values selected by the indices """
        a = getattr(self, attr)
        return idx[np.argsort(a[idx])]

    def unique_teacher(self):
        return self.__unique('teacher')

    def select_teacher(self, v, idx=None):
        return self.__select('teacher', v, idx)

    def get_teacher(self, idx):
        return self.__get('teacher', idx)

    def unique_day(self):
        return self.__unique('day')

    def select_day(self, v, idx=None):
        return self.__select('day', v, idx)

    def get_day(self, idx):
        return self.__get('day', idx)

    def sort_by_day(self, idx):
        return self.__sort_by('day', idx)

    def unique_time(self):
        return self.__unique('time')

    def get_time(self, idx):
        return self.__get('time', idx)

    def get_start_time(self, idx):
        return self.__get('start_time', idx)

    def sort_by_start_time(self, idx):
        return self.__sort_by('start_time', idx)

    def get_duration(self, idx):
        return self.__get('duration', idx)

    def get_end_time(self, idx):
        return self.__get('end_time', idx)

    def unique_subject(self):
        return self.__unique('subject')

    def select_subject(self, v, idx=None):
        return self.__select('subject', v, idx)

    def get_subject(self, idx):
        return self.__get('subject', idx)

    def unique_level(self):
        return self.__unique('level')

    def select_level(self, v, idx=None):
        return self.__select('level', v, idx)

    def get_level(self, idx):
        return self.__get('level', idx)

    def select_group(self, v, idx=None):
        return self.__select('group', v, idx)

    def get_group(self, idx):
        return self.__get('group', idx)

def time_str(t):
    return (datetime.datetime(2000, 1, 1) + t).strftime("%H:%M")

if __name__ == "__main__":
    if len(sys.argv) == 2:
        f = open(sys.argv[1], 'r')
    else:
        f = sys.stdin
    Courses.parse(f)
    Courses.to_numpy()
    courses = Courses(course_level, course_class, course_subject, course_day, course_start_time, course_duration, teacher)

    out = html_output(sys.stdout)
    all_teacher_schedule(out, courses)
    all_level_schedule(out, courses)
    out.exit()

    if False:
        for t in courses.unique_time():
            debug(time_str(t))
        debug(courses.unique_teacher())
        ud = courses.unique_day()
        debug(courses.get_day(courses.select_day(ud[0])))
        debug(courses.get_day(courses.select_day(ud[-1])))
        debug(courses.get_teacher(courses.select_day(ud[-1])))

        tt = courses.unique_teacher()
        idx = courses.select_teacher(tt[0])
        debug(idx)
        debug(courses.get_teacher(idx))
        debug(courses.get_day(idx))
        #debug(end_times)

