%
% Parameters
%

% Time is in base 100
int: MAX_TIME = max(DAYS)*2400;
set of int: TIME = 0..MAX_TIME;
TIME: H_null = 2400;
% Times slots: first element is start time, second element is duration
set of int: SLOTS;
array[SLOTS, 1..2] of TIME: slot;
% Days have various hour configurations: this is the number of different
% configurations
set of int: DAY_TYPES;
% These are the day hour configurations
array[DAY_TYPES, SLOTS] of bool: day_slot_valid;
% Days of a week
set of int: DAYS;
array[DAYS] of DAY_TYPES: day;

% The levels
enum level;
% The subjects
enum subject;
% Map level and subject to number of hours there are taught
set of int: DURATIONS;
array[DURATIONS, int] of TIME: duration_types;
array[level, subject] of DURATIONS: level_subject_duration;
% Number of classes per level
array[level] of int: level_classes;

% The teachers
enum teacher;
% Map teacher to taught subject
% For now one subject per teacher
array[teacher] of subject: teacher_subject;
% Minimum number of hours a teacher has to teach
array[teacher] of int: teacher_min_hours;
% Maximum number of hours a teacher can teach
array[teacher] of int: teacher_max_hours;

%
% Input data checks
%
% TODO: check null termination of duration_types array
%% TODO

%
% Constructed data
%

% Let's build the weekly schedule of slots
set of int: WEEK_SLOTS = 1 .. sum(d in DAYS)(sum(s in SLOTS)(day_slot_valid[day[d], s]));
array[WEEK_SLOTS] of TIME: week_slot_start_time = [
	slot[s, 1] + (d - 1) * H_null | d in DAYS, s in SLOTS where day_slot_valid[day[d], s]
];
array[WEEK_SLOTS] of TIME: week_slot_duration = [
	slot[s, 2] | d in DAYS, s in SLOTS where day_slot_valid[day[d], s]
];
array[WEEK_SLOTS] of DAYS: week_slot_day = [
	d | d in DAYS, s in SLOTS where day_slot_valid[day[d], s]
];

% Let's introduce the notion of course.
% Index set for courses
set of int: COURSES = 1 .. sum(
	[ level_classes[l] *
		sum([duration_types[level_subject_duration[l, s], i] != 0 | s in subject, i in index_set_2of2(duration_types)]) | l in level]
);
array[COURSES] of TIME: course_duration = [
	duration_types[level_subject_duration[l, s], d]
	| l in level, c in 1..level_classes[l], s in subject,
		d in index_set_2of2(duration_types) where duration_types[level_subject_duration[l, s], d] != 0
];
array[COURSES] of subject: course_subject = [
	s
	| l in level, c in 1..level_classes[l], s in subject,
		d in index_set_2of2(duration_types) where duration_types[level_subject_duration[l, s], d] != 0
];
array[COURSES] of level: course_level = [
	l
	| l in level, c in 1..level_classes[l], s in subject,
		d in index_set_2of2(duration_types) where duration_types[level_subject_duration[l, s], d] != 0
];
array[COURSES] of int: course_class = [
	c
	| l in level, c in 1..level_classes[l], s in subject,
		d in index_set_2of2(duration_types) where duration_types[level_subject_duration[l, s], d] != 0
];
%constraint assert(false, "\(card(index_set_2of2(duration_types))) \(card(COURSES)) != \(length(course_duration)) \(course_duration)");
%constraint assert(false, "\(course_valid)\n\(course_duration)\n\(course_subject)");

%
% Variables
%

% Every course must be assigned to a slot: here is the mapping
array[COURSES] of var WEEK_SLOTS: course_slot;
% Every course must have a teacher: here is the mapping
array[COURSES] of var teacher: course_teacher;

%
% Constraints
%

include "globals.mzn";

% A teacher can only teach the subjects he/she knows
constraint forall(c in COURSES) (teacher_subject[course_teacher[c]] = course_subject[c]);

% A teacher can only teach one course at a time
constraint
forall (t in teacher) (
	disjunctive(
		[week_slot_start_time[course_slot[c]]
			| c in COURSES where course_teacher[c] = t],
		[week_slot_duration[course_slot[c]] * (course_teacher[c] = t)
			| c in COURSES])
);

% Map courses to slots
constraint
forall (c in COURSES) (week_slot_duration[course_slot[c]] = course_duration[c]);

% A class cannot have two courses at the same time
constraint
forall (l in level, cl in 1..level_classes[l]) (
	disjunctive(
		[week_slot_start_time[course_slot[c]]
			| c in COURSES
			where (course_level[c] = l /\ course_class[c] = cl)],
		[week_slot_duration[course_slot[c]]
			| c in COURSES
			where (course_level[c] = l /\ course_class[c] = cl)])
);

% No twice the same subject per day for a single class
constraint
forall (c1 in COURSES)
	(forall (c2 in COURSES where c2 > c1)
		(course_subject[c1] = course_subject[c2] /\
		 course_level[c1] = course_level[c2] /\
	         course_class[c1] = course_class[c2]
		-> week_slot_day[course_slot[c1]] != week_slot_day[course_slot[c2]]));

% A class should have a single teacher for a given subject
constraint
forall (c1 in COURSES)
	(forall (c2 in COURSES where c2 > c1)
		(course_subject[c1] = course_subject[c2] /\
		 course_level[c1] = course_level[c2] /\
	         course_class[c1] = course_class[c2]
		-> course_teacher[c1] == course_teacher[c2]));

% TODO: Teacher cannot teach less than a certain amount
% TODO: Teacher cannot teach more than a certain amount

% Time amplitude per day per teacher
array[teacher, DAYS] of var TIME: teacher_day_begin_time;
array[teacher, DAYS] of var TIME: teacher_day_end_time;
array[teacher, DAYS] of var TIME: teacher_day_amplitude;

% Compute the first course in each day for every teacher. When a teacher has no
% course that day, result is MAX_TIME
constraint
forall (t in teacher, d in DAYS)
	(teacher_day_begin_time[t, d] =
		min([ if course_teacher[c] = t /\ week_slot_day[course_slot[c]] = d
			then week_slot_start_time[course_slot[c]]
			else MAX_TIME
			endif
			| c in COURSES]));

% Compute the last course + duration in each day for every teacher. When a teacher has no
% course that day, result is 0
constraint
forall (t in teacher, d in DAYS)
	(teacher_day_end_time[t, d] =
		max([(week_slot_start_time[course_slot[c]] + week_slot_duration[course_slot[c]])
			* (course_teacher[c] = t /\ week_slot_day[course_slot[c]] = d)
			| c in COURSES]));

% Compute time amplitude in a worked day for every teacher. When teacher does
% not work, result is 0
constraint
forall (t in teacher, d in DAYS)
	(teacher_day_amplitude[t, d] = (teacher_day_end_time[t, d] - teacher_day_begin_time[t, d])
					* (teacher_day_begin_time[t, d] != MAX_TIME));

% Objective 1: minimize total worked days
% Objective 2: minimize total day amplitudes, hence minimize 'holes'
% Both objectives are combined: we add 2400 for every worked day
var 0 .. (card(DAYS) * H_null + card(DAYS) * card(teacher) * H_null): total_amplitude = sum (t in teacher, d in DAYS) (H_null * (teacher_day_amplitude[t, d] != 0) + teacher_day_amplitude[t, d]);

var int: obj =  total_amplitude;
solve minimize obj;
%solve satisfy;
output [
	"course_level = ", show([course_level[c] | c in COURSES]), ";\n",
	"course_class = ", show([course_class[c] | c in COURSES]), ";\n",
	"course_subject = ", show([course_subject[c] | c in COURSES]), ";\n",
	"course_day = ", show([week_slot_day[course_slot[c]] | c in COURSES]), ";\n",
	"course_start_time = ", show([week_slot_start_time[course_slot[c]] | c in COURSES]), ";\n",
	"course_duration = ", show([course_duration[c] | c in COURSES]), ";\n",
	"teacher = ", show([course_teacher[c] | c in COURSES]), ";\n",
	"teacher_day_begin_time = \(teacher_day_begin_time)", ";\n",
	"teacher_day_end_time = \(teacher_day_end_time)", ";\n",
	"teacher_day_amplitude = \(teacher_day_amplitude)", ";\n",
	"obj = \(obj)", ";\n",
];
