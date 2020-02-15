#!/usr/bin/env python3

import sys
from ortools.sat.python import cp_model

days = ["Monday", "Tuesday", "Wednesday", "Thursday"]
Days = {}
for i, D in enumerate(days):
    Days[D] = i
times = ["17:30-18:40", "18:45-19:55", "20:00-21:10"]
slots = [ d + " " + t for d in days for t in times ]

rooms = ["big", "small"]
Rooms = {}
for i, R in enumerate(rooms):
    Rooms[R] = i

teachers_lead = [
        "David",
        "Tom-S.",
        "Kuba-Š.",
        "Peťa",
        "Tom-K.",
        "Jarda",
        "Quique",
        "Maťo",
        "Martin",
        "Michal",
        "Vojta-S.",
        "Standa",
        "Kolin",
        "Kepo",
        "Vojta-N.",
        "Kuba-B.",
        ]
teachers_follow = [
        "Terka",
        "Janča",
        "Ilča",
        "Pavli",
        "Bláža",
        "Silvia",
        "Ivča",
        "Linda",
        "Mária",
        "Poli",
        "Míša",
        "Zuzka",
        "Soňa",
	]
teachers_core = ["David", "Tom-S.", "Kuba-Š.", "Peťa", "Tom-K.", "Jarda", "Quique", "Martin", "Michal", "Kolin", "Kepo", "Terka", "Janča", "Ilča", "Pavli", "Silvia", "Linda", "Mária", "Soňa", "Poli"]
teachers_external = list((set(teachers_lead) | set(teachers_follow)) - set(teachers_core))
print(f"External teachers: {teachers_external}")
teachers_external_active = ["Standa", "Vojta-N.", "Kuba-B.", "Zuzka", "Míša"]
teachers_active = teachers_core + teachers_external_active
print(f"Active teachers: {teachers_active}")

teachers = teachers_lead + teachers_follow
Teachers = {}
for (i, t) in enumerate(teachers):
    Teachers[t] = i

courses_open = [
        "Shag/Balboa Open Training",
        "Lindy/Charleston Open Training",
        "Teachers Training",
        "Blues/Slow Open Training",
        "Balboa Closed Training",
        ]
courses_solo = [
        ]
courses_regular = [
        "LH 1 - Beginners /1",
        "LH 1 - Beginners /2",
        "LH 1 - Beginners EN",
        "LH 2 - Survival Guide",
        "LH 2 - Party Moves /1",
        "LH 2 - Party Moves /2",
        "LH 2.5 - Swing-out /1",
        "LH 2.5 - Swing-out /2",
        "LH 3 - Charleston 1",
        "LH 3 - Lindy Charleston EN",
        "LH 3 - Musicality",
        "LH 4 - Moves and Their Technique",
        "LH 4 - Swing-out Clinic",
        "LH 5 - Topic-less",
        "Balboa Beginners 2",
        "Balboa Advanced",
        "Airsteps 2",
        "Choreo Atelier - Airsteps Edition",
        "Collegiate Shag 2",
        ]
courses = courses_regular + courses_solo + courses_open
Courses = {}
for (i, c) in enumerate(courses):
    Courses[c] = i

# SPECIFIC HARD CONSTRAINTS

# teacher T:
#   can teach maximum N courses
#   should teach minimum N-1 courses
# default is optimization for average utilization - maximum is not strict in this case
t_util_desired = {}
# people not available
t_util_desired["Kepo"] = 0
t_util_desired["Poli"] = 0
# leads' desires
t_util_desired["David"] = 1
t_util_desired["Kolin"] = 1
t_util_desired["Quique"] = 1
t_util_desired["Jarda"] = 2
t_util_desired["Kuba-Š."] = 4
t_util_desired["Martin"] = 1
t_util_desired["Michal"] = 2
t_util_desired["Peťa"] = 1
t_util_desired["Tom-S."] = 3
t_util_desired["Tom-K."] = 1
# follows' desires
t_util_desired["Ilča"] = 5
t_util_desired["Terka"] = 3
t_util_desired["Janča"] = 6
t_util_desired["Linda"] = 2
t_util_desired["Mária"] = 2
t_util_desired["Silvia"] = 2
t_util_desired["Pavli"] = 1

# course C can be taught only by Ts
teachers_lh1 = list(set(teachers_active) - set(["Peťa", "Standa", "Terka", "Pavli"]))
teachers_lh2 = list(set(teachers_active) - set(["Peťa", "Standa", "Terka", "Linda", "Pavli"]))
teachers_lh2_5 = list(set(teachers_core) - set(["Peťa", "Terka", "Linda", "Pavli"]))
teachers_lh3 = list(set(teachers_core) - set(["David", "Jarda", "Peťa", "Terka", "Pavli"]))
teachers_lh4 = list(set(teachers_core) - set(["David", "Jarda", "Peťa", "Pavli"]))
teachers_lh5 = ["Kuba-Š.", "Kolin", "Terka", "Janča", "Mária", "Silvia", "Soňa"]
teachers_airsteps = ["Tom-S.", "Janča"]
teachers_shag = ["Terka", "Linda", "Kepo", "Standa"]
teachers_balboa = ["Peťa", "Jarda", "Poli", "Pavli", "Ilča"]
ct_possible = {}
for C in courses:
    if C not in courses_open:
        if C.startswith("LH 1 "):
            ct_possible[C] = teachers_lh1
        elif C.startswith("LH 2 "):
            ct_possible[C] = teachers_lh2
        elif C.startswith("LH 2.5 "):
            ct_possible[C] = teachers_lh2_5
        elif C.startswith("LH 3 "):
            ct_possible[C] = teachers_lh3
        elif C.startswith("LH 4 "):
            ct_possible[C] = teachers_lh4
        elif C.startswith("LH 5 "):
            ct_possible[C] = teachers_lh5
        elif "Airsteps" in C:
            ct_possible[C] = teachers_airsteps
        elif "Collegiate Shag" in C:
            ct_possible[C] = teachers_shag
        elif "Balboa" in C:
            ct_possible[C] = teachers_balboa

# course C takes place in room R
cr_strict = {}
cr_strict["Airsteps 2"] = "big"
#cr_strict["Collegiate Shag 1"] = "big"
cr_strict["Collegiate Shag 2"] = "big"

# teacher T must teach courses Cs
tc_strict = {}
tc_strict["Standa"] = ["Collegiate Shag 2"]

# teacher T1 must not teach a course with teacher T2
tt_not_together = [
        ("Kuba-Š.", "Soňa"),
        ("Michal", "Ilča"),
        ]


# course Cx must happen on different day and at different time than Cy
courses_different = [
        ["LH 1 - Beginners /1", "LH 1 - Beginners /2", "LH 1 - Beginners EN"],
        ["LH 2 - Party Moves /1", "LH 2 - Party Moves /2"],
        ["LH 2.5 - Swing-out /1", "LH 2.5 - Swing-out /2"],
        ["LH 3 - Charleston 1", "LH 3 - Lindy Charleston EN"],
        ]

# course C1, C2, (C3) should happend on the same day in different times
courses_same = [
        ["Collegiate Shag 2", "Shag/Balboa Open Training"],
        ["Balboa Beginners 2", "Balboa Advanced", "Balboa Closed Training"],
        #("Collegiate Shag 1", "Airsteps 2"),
        #("Balboa Beginners", "Shag/Balboa Open Training"),
        #("Balboa Intermediate", "Shag/Balboa Open Training"),
        ]


model = cp_model.CpModel()

# VARIABLES

# course C takes place in slot S in room R
src = {}
for s in range(len(slots)):
    for r in range(len(rooms)):
        for c in range(len(courses)):
            src[(s,r,c)] = model.NewBoolVar("CSR:s%ir%ic%i" % (s,r,c))
# course C is taught by teacher T
tc = {}
for c in range(len(courses)):
    for t in range(len(teachers)):
        tc[(t,c)] = model.NewBoolVar("CT:t%ic%i" % (t,c))
# teacher T teaches in slot S course C
tsc = {}
for s in range(len(slots)):
    for t in range(len(teachers)):
        for c in range(len(courses)):
            tsc[(t,s,c)] = model.NewBoolVar("TS:t%is%ic%i" % (t,s,c))
# teacher T teaches in slot S
ts = {}
for s in range(len(slots)):
    for t in range(len(teachers)):
        ts[(t,s)] = model.NewBoolVar("TS:t%is%i" % (t,s))
# teacher T teaches on day D
td = {}
for d in range(len(days)):
    for t in range(len(teachers)):
        td[(t,d)] = model.NewBoolVar("TD:t%id%i" % (t,d))
cs = []
# course C takes place in slot S
for c in range(len(courses)):
    cs.append(model.NewIntVar(0, len(slots)-1, ""))

# teacher T teaches in slot S course C iff course C takes place at slot S and is taught by teacher T
# inferring CTS info
for s in range(len(slots)):
    for c in range(len(courses)):
        hit = model.NewBoolVar("") # course C is at slot S
        model.Add(sum(src[(s,r,c)] for r in range(len(rooms))) == 1).OnlyEnforceIf(hit)
        model.Add(sum(src[(s,r,c)] for r in range(len(rooms))) == 0).OnlyEnforceIf(hit.Not())
        model.Add(cs[c] == s).OnlyEnforceIf(hit)
        model.Add(cs[c] != s).OnlyEnforceIf(hit.Not())
        for t in range(len(teachers)):
            model.AddBoolAnd([hit, tc[(t,c)]]).OnlyEnforceIf(tsc[(t,s,c)])
            model.AddBoolOr([hit.Not(), tc[(t,c)].Not()]).OnlyEnforceIf(tsc[(t,s,c)].Not())
# inferring TS info
for s in range(len(slots)):
    for t in range(len(teachers)):
        model.Add(sum(tsc[(t,s,c)] for c in range(len(courses))) == 1).OnlyEnforceIf(ts[(t,s)])
        model.Add(sum(tsc[(t,s,c)] for c in range(len(courses))) == 0).OnlyEnforceIf(ts[(t,s)].Not())
for d in range(len(days)):
    for t in range(len(teachers)):
        model.Add(sum(ts[(t,s)] for s in range(d*len(times), (d+1)*len(times))) >= 1).OnlyEnforceIf(td[(t,d)])
        model.Add(sum(ts[(t,s)] for s in range(d*len(times), (d+1)*len(times))) == 0).OnlyEnforceIf(td[(t,d)].Not())

# number of lessons teacher T teaches
teach_num = {}
for t in range(len(teachers)):
    teach_num[t] = model.NewIntVar(0, len(slots), "Tteach_num:%i" % t)
    model.Add(teach_num[t] == sum(tc[(t,c)] for c in range(len(courses))))

# prevent teachers from teaching in two rooms in the same time
for t in range(len(teachers)):
    for s in range(len(slots)):
        model.Add(sum(tsc[(t,s,c)] for c in range(len(courses))) <= 1)

# one course takes place at one time in one room
for c in range(len(courses)):
    model.Add(sum(src[(s,r,c)] for s in range(len(slots)) for r in range(len(rooms))) == 1)

# at one time in one room, there is maximum one course
for s in range(len(slots)):
    for r in range(len(rooms)):
        model.Add(sum(src[(s,r,c)] for c in range(len(courses))) <= 1)

# every regular course is taught by two teachers and solo course by one teacher
for c in range(len(courses)):
    if courses[c] in courses_regular:
        model.Add(sum(tc[(Teachers[T],c)] for T in teachers_lead) == 1)
        model.Add(sum(tc[(Teachers[T],c)] for T in teachers_follow) == 1)
    elif courses[c] in courses_solo:
        model.Add(sum(tc[(Teachers[T],c)] for T in teachers) == 1)
    elif courses[c] in courses_open:
        model.Add(sum(tc[(Teachers[T],c)] for T in teachers) == 0)
    else:
        assert(False)

# SPECIFIC CONSTRAINTS

for (T, n) in t_util_desired.items():
    model.Add(sum(tc[(Teachers[T],c)] for c in range(len(courses))) <= n)

# only active teachers teach
for t in range(len(teachers)):
    if teachers[t] not in teachers_active:
        model.Add(sum(tc[(t,c)] for c in range(len(courses))) == 0)

if tc_strict:
    strict_assignments = []
    for (T, Cs) in tc_strict.items():
        t = Teachers[T]
        for C in Cs:
            c = Courses[C]
            strict_assignments.append(tc[(t,c)])
    model.AddBoolAnd(strict_assignments)

ts_all = set(range(len(teachers)))
for (C, Ts) in ct_possible.items():
    c = Courses[C]
    ts_can = []
    for T in Ts:
        t = Teachers[T]
        ts_can.append(t)
    ts_not = ts_all - set(ts_can)
    # no other teacher can teach C
    model.Add(sum(tc[(t,c)] for t in ts_not) == 0)

for T1, T2 in tt_not_together:
    for c in range(len(courses)):
        model.Add(sum(tc[(t,c)] for t in [Teachers[T1], Teachers[T2]]) < 2)

# Teachers' time preferences
# TODO: find a better place for this part

# teacher T availability at day D:
#   0 cannot
#   1 barely
#   2 fine (default)
#   3 great
td_pref = {}
td_pref[("Quique", "Monday")] = 0
td_pref[("Quique", "Wednesday")] = 0
td_pref[("Kuba-Š.", "Monday")] = 1
td_pref[("Kuba-Š.", "Thursday")] = 1
td_pref[("Martin", "Thursday")] = 0
td_pref[("Michal", "Monday")] = 0
td_pref[("Michal", "Tuesday")] = 1
td_pref[("Michal", "Thursday")] = 0
td_pref[("Tom-S.", "Monday")] = 0
td_pref[("Tom-S.", "Thursday")] = 1
td_pref[("Tom-K.", "Monday")] = 0
td_pref[("Tom-K.", "Wednesday")] = 1
td_pref[("Vojta-N.", "Monday")] = 1
td_pref[("Vojta-N.", "Tuesday")] = 0
td_pref[("Terka", "Monday")] = 1
td_pref[("Terka", "Wednesday")] = 0
td_pref[("Janča", "Monday")] = 1
td_pref[("Linda", "Tuesday")] = 0
td_pref[("Linda", "Wednesday")] = 0
td_pref[("Mária", "Monday")] = 0
td_pref[("Mária", "Thursday")] = 0
td_pref[("Pavli", "Monday")] = 0
td_pref[("Pavli", "Wednesday")] = 1
td_pref[("Soňa", "Monday")] = 0
td_pref[("Soňa", "Tuesday")] = 1
td_pref[("Soňa", "Wednesday")] = 0
td_pref[("Zuzka", "Monday")] = 0
td_pref[("Míša", "Wednesday")] = 0
td_pref[("Míša", "Thursday")] = 1

#td_pref[("Tom-S.", "Thursday")] = 0 # acroyoga
#td_pref[("Tom-S.", "Monday")] = 3

# teacher T availability at time X (0 - first slot, 1 - second slot, 2 - third slot):
#   0 cannot
#   1 barely
#   2 fine (default)
#   3 great
ttime_pref = {}
ttime_pref[("Jarda", 2)] = 1
ttime_pref[("Martin", 0)] = 0
ttime_pref[("Peťa", 2)] = 0
ttime_pref[("Tom-S.", 2)] = 1
ttime_pref[("Linda", 2)] = 1
ttime_pref[("Mária", 2)] = 0
ttime_pref[("Silvia", 1)] = 0
ttime_pref[("Silvia", 2)] = 0
ttime_pref[("Zuzka", 0)] = 0
ttime_pref[("Míša", 2)] = 1

# strict teacher-slot constraints:
# Standa cannot teach the first Tuesday slot
model.Add(ts[(Teachers["Standa"],3)] == 0)
# David can teach only in the middle slot on Tuesday (not preferred) and Wednesday (preferred)
# TODO: particular slot preferences
model.Add(sum(ts[(Teachers["David"],s)] for s in range(len(slots)) if s not in [4,7]) == 0)
# Kolin can teach only in the middle slot on Thursday
model.Add(sum(ts[(Teachers["Kolin"],s)] for s in range(len(slots)) if s not in [10]) == 0)


# strict courses schedule
# Teachers training must be at Thursday evening
model.Add(cs[Courses["Teachers Training"]] == 11)
# Balboa Training must be at Wednesday evening
model.Add(cs[Courses["Balboa Closed Training"]] == 8)
# Blues Training must not be on Monday
model.Add(cs[Courses["Blues/Slow Open Training"]] > 2)
for (T,D), n in td_pref.items():
    if n == 0: # T cannot teach on day D
        model.Add(td[(Teachers[T], Days[D])] == 0)


for Cs in courses_different:
    daylist = [] # days
    timelist = [] # times
    assert(2 <= len(Cs) <= min(len(days), len(times)))
    for C in Cs:
        day = model.NewIntVar(0, len(days)-1, "")
        time = model.NewIntVar(0, len(times)-1, "")
        model.AddDivisionEquality(day, cs[Courses[C]], len(times))
        model.AddModuloEquality(time, cs[Courses[C]], len(times))
        daylist.append(day)
        timelist.append(time)
    model.AddAllDifferent(daylist)
    model.AddAllDifferent(timelist)

# it should probably not be a strict limitation, but it is much easier to write
for Cs in courses_same:
    daylist = [] # days
    timelist = [] # times
    assert(2 <= len(Cs) <= len(times))
    for C in Cs:
        day = model.NewIntVar(0, len(days)-1, "")
        time = model.NewIntVar(0, len(times)-1, "")
        model.AddDivisionEquality(day, cs[Courses[C]], len(times))
        model.AddModuloEquality(time, cs[Courses[C]], len(times))
        daylist.append(day)
        timelist.append(time)
    model.AddAllowedAssignments(daylist, [[d] * len(Cs) for d in range(len(days))])
    if len(Cs) == len(times):
        # filling whole day
        model.AddAllDifferent(timelist)
    elif len(Cs) == len(times) - 1:
        # filling 2 out of three slots
        assert(len(Cs) == 2)
        model.AddAllowedAssignments(timelist, [ [0,1], [1,0], [1,2], [2,1] ])
    else:
        # should not happen
        assert(False)

for (C, R) in cr_strict.items():
    model.Add(sum(src[(s,Rooms[R],Courses[C])] for s in range(len(slots))) == 1)

# external teachers must teach exactly 1 course
for T in teachers_external_active:
    model.Add(sum(tc[(Teachers[T],c)] for c in range(len(courses))) == 1)
# external teachers must teach together with core teachers
for C in courses_regular:
    model.Add(sum(tc[(Teachers[T],Courses[C])] for T in teachers_external) <= 1)
# external teachers cannot teach solo courses
for C in courses_solo:
    model.Add(sum(tc[(Teachers[T],Courses[C])] for T in teachers_external) == 0)


# Rather specific constraints:

# course has to take place at specific slot and room
#model.Add(src[(0,Rooms["big"],Courses["Airsteps 2"])] == 1)

# course has to take place at specific slot
#model.Add(sum(src[(0,r,Courses["Collegiate Shag 1"])] for r in range(len(rooms))) == 1)


# Damian
damian = True
if damian:
    for T in "Tom-K.", "Pavli":
        model.Add(sum(tc[(Teachers[T],c)] for c in range(len(courses))) == 1)
    damianday = model.NewIntVar(0, len(days)-1, "damianday")
    for d in range(len(days)):
        hit = model.NewBoolVar("")
        model.Add(damianday == d).OnlyEnforceIf(hit)
        model.Add(damianday != d).OnlyEnforceIf(hit.Not())
        model.Add(ts[(Teachers["Tom-K."],d*len(times)+0)] == 1).OnlyEnforceIf(hit)
        model.Add(ts[(Teachers["Pavli"],d*len(times)+1)] == 1).OnlyEnforceIf(hit)

# OPTIMIZATION

PENALTY_OVERWORK = 101 # squared
PENALTY_UNDERWORK = 31
PENALTY_DAYS = 1009 # squared
PENALTY_SPLIT = 503
PENALTY_DAYPREF_SLIGHT = 53
PENALTY_DAYPREF_BAD = 1013
PENALTY_TIMEPREF_SLIGHT = 59
PENALTY_TIMEPREF_BAD = 1019

penalties = [] # list of all penalties

if PENALTY_OVERWORK > 0 or PENALTY_UNDERWORK > 0:
    # teaching should be split evenly
    penalties_overwork = []
    penalties_underwork = []
    # disregarding people with t_util_desired set (roughly - subtracting also number of courses from "defaul pool")
    #util_avg = (2*len(courses_regular) + len(courses_solo) - sum(t_util_desired.values()) - EXTERNAL_MAX) \
    #   // (len(teachers_core) - len(t_util_desired)) \
    #   + 1
    for T in teachers_core:
        t = Teachers[T]
        min_diff = -max(list(t_util_desired.values()) + [1])
        max_diff = len(courses_regular) + len(courses_solo)
        util_diff = model.NewIntVar(min_diff, max_diff, "")
        # ideal utilization - either what teacher specifies, or average
        util_ideal = t_util_desired.get(T, 1)
        model.Add(util_diff == teach_num[t] - util_ideal)
        if PENALTY_OVERWORK > 0:
            util_excess = model.NewIntVar(0, max_diff, "")
            model.AddMaxEquality(util_excess, [util_diff, 0])
            util_excess_sq = model.NewIntVar(0, max_diff**2, "Texcesssq:%i" % t)
            model.AddMultiplicationEquality(util_excess_sq, [util_excess, util_excess])
            penalties_overwork.append(util_excess_sq)
        if PENALTY_UNDERWORK > 0:
            # we consider -1 difference ok - e.g., if teacher wants to teach 4 courses, it is ok to teach 3
            util_diff_incr = model.NewIntVar(min_diff+1, max_diff+1, "")
            model.Add(util_diff_incr == util_diff + 1)
            util_lack = model.NewIntVar(min_diff, 0, "")
            model.AddMinEquality(util_lack, [util_diff_incr, 0])
            util_lack_abs = model.NewIntVar(0, abs(min_diff), "")
            model.AddAbsEquality(util_lack_abs, util_lack)
            penalties_underwork.append(util_lack_abs)
    penalties.append(sum(penalties_overwork) * PENALTY_OVERWORK + sum(penalties_underwork) * PENALTY_UNDERWORK)

if PENALTY_DAYS > 0:
    # nobody should come to studio more days then necessary
    penalties_days = []
    for t in range(len(teachers)):
        teaches_days = model.NewIntVar(0, len(days), "TD:%i" % t)
        model.Add(teaches_days == sum(td[(t,d)] for d in range(len(days))))
        teaches_minus_1 = model.NewIntVar(0, len(days), "Tm1:%i" % t)
        teaches_some = model.NewBoolVar("Ts:%i" % t)
        model.Add(teach_num[t] >= 1).OnlyEnforceIf(teaches_some)
        model.Add(teach_num[t] == 0).OnlyEnforceIf(teaches_some.Not())
        model.Add(teaches_minus_1 == teach_num[t] - 1).OnlyEnforceIf(teaches_some)
        model.Add(teaches_minus_1 == 0).OnlyEnforceIf(teaches_some.Not())
        should_teach_days = model.NewIntVar(0, len(days), "TDs:%i" % t)
        model.AddDivisionEquality(should_teach_days, teaches_minus_1, len(times)) # -1 to compensate rounding down
        days_extra = model.NewIntVar(0, len(days), "Tdd:%i" % t)
        model.Add(days_extra == teaches_days - should_teach_days - 1).OnlyEnforceIf(teaches_some) # -1 to compensate rounding down
        model.Add(days_extra == 0).OnlyEnforceIf(teaches_some.Not())
        days_extra_sq = model.NewIntVar(0, len(days)**2, "Tdds:%i" % t)
        model.AddMultiplicationEquality(days_extra_sq, [days_extra, days_extra])
        penalties_days.append(days_extra_sq)
    penalties.append(sum(penalties_days) * PENALTY_DAYS)

if PENALTY_SPLIT > 0:
    # teacher should not wait between lessons
    penalties_split = []
    for t in range(len(teachers)):
        days_split = model.NewIntVar(0, len(days), "TDsplit:%i" % t)
        tsplits = []
        for d in range(len(days)):
            # tsplit == True iff teacher t teaches just the first and the last course in day d
            tsubsplits = []
            for i in range(len(times)):
                tsubsplit = model.NewBoolVar("tsubsplit:t%id%ii%i" % (t,d,i))
                model.Add(sum(ts[(t,s)] for s in [d*len(times)+i]) == 1).OnlyEnforceIf(tsubsplit)
                model.Add(sum(ts[(t,s)] for s in [d*len(times)+i]) == 0).OnlyEnforceIf(tsubsplit.Not())
                tsubsplits.append(tsubsplit)
            tsplit = model.NewBoolVar("tsplit:t%id%i" % (t,d))
            model.AddBoolAnd([tsubsplits[0], tsubsplits[1].Not(), tsubsplits[2]]).OnlyEnforceIf(tsplit)
            model.AddBoolOr([tsubsplits[0].Not(), tsubsplits[1], tsubsplits[2].Not()]).OnlyEnforceIf(tsplit.Not())
            tsplits.append(tsplit)
        model.Add(days_split == sum(tsplits))
        penalties_split.append(days_split)
    penalties.append(sum(penalties_split) * PENALTY_SPLIT)

if PENALTY_DAYPREF_SLIGHT > 0 or PENALTY_DAYPREF_BAD > 0:
    # day preferences
    penalties_daypref = []
    for T in teachers:
        t = Teachers[T]
        prefs = []
        for D in days:
            prefs.append(td_pref.get((T,D), 2))
        if set(prefs) - set([0, 2]): # teacher T prefers some days over others
            if PENALTY_DAYPREF_SLIGHT > 0:
                if set([2,3]) <= set(prefs):
                    # days that are slightly less preferred
                    days_slight_worse = [d for d in range(len(prefs)) if prefs[d] == 2]
                    penalties_daypref.append(sum(td[(t,d)] for d in days_slight_worse) * PENALTY_DAYPREF_SLIGHT)
            if PENALTY_DAYPREF_BAD > 0:
                if 1 in set(prefs):
                    # not preferred days
                    days_bad = [d for d in range(len(prefs)) if prefs[d] == 1]
                    penalties_daypref.append(sum(td[(t,d)] for d in days_bad) * PENALTY_DAYPREF_BAD)
    if penalties_daypref:
        penalties.append(sum(penalties_daypref))

if PENALTY_TIMEPREF_SLIGHT > 0 or PENALTY_TIMEPREF_BAD > 0:
    # time preferences
    penalties_timepref = []
    for T in teachers:
        t = Teachers[T]
        prefs = []
        for time in range(len(times)):
            prefs.append(ttime_pref.get((T,time), 2))
        if set(prefs) - set([0, 2]): # teacher T prefers some times over others
            if PENALTY_TIMEPREF_SLIGHT > 0:
                if set([2,3]) <= set(prefs):
                    # times that are slightly less preferred
                    times_slight_worse = [time for time in range(len(prefs)) if prefs[time] == 2]
                    slots_slight_worse = [d*len(times)+time for time in times_slight_worse for d in range(len(days))]
                    penalties_timepref.append(sum(ts[(t,s)] for s in slots_slight_worse) * PENALTY_TIMEPREF_SLIGHT)
            if PENALTY_TIMEPREF_BAD > 0:
                if 1 in set(prefs):
                    # not preferred times
                    times_bad = [time for time in range(len(prefs)) if prefs[time] == 1]
                    slots_bad = [d*len(times)+time for time in times_bad for d in range(len(days))]
                    penalties_timepref.append(sum(ts[(t,s)] for s in slots_bad) * PENALTY_TIMEPREF_BAD)
    if penalties_timepref:
        penalties.append(sum(penalties_timepref))


model.Minimize(sum(penalties))

print(model.ModelStats())
print()

solver = cp_model.CpSolver()
#solver.parameters.max_time_in_seconds = 20.0
#status = solver.Solve(model)
status = solver.SolveWithSolutionCallback(model, cp_model.ObjectiveSolutionPrinter())
statusname = solver.StatusName(status)
print(f"Solving finished in {solver.WallTime()} seconds with status {status} - {statusname}")
if statusname not in ["FEASIBLE", "OPTIMAL"]:
    print("Solution NOT found")
    sys.exit(1)

print()
print("SOLUTION:")
for s in range(len(slots)):
    for r in range(len(rooms)):
        for c in range(len(courses)):
            if solver.Value(src[(s,r,c)]):
                Ts = []
                if courses[c] in courses_open:
                    Ts.append("OPEN")
                elif courses[c] in courses_solo:
                    for t in range(len(teachers)):
                        if solver.Value(tc[(t,c)]):
                            Ts.append(teachers[t])
                            break
                elif courses[c] in courses_regular:
                    for t in range(len(teachers)):
                        if solver.Value(tc[(t,c)]):
                            Ts.append(teachers[t])
                if len(Ts) == 2 and Ts[0] in teachers_follow:
                    Ts[0], Ts[1] = Ts[1], Ts[2]
                print(f"{slots[s]} in {rooms[r]} room: {courses[c]} / {'+'.join(Ts)}")

print()
print(f"Teachers' utilization:")
for n in range(len(slots)):
    Ts = []
    for T in teachers_active:
        if solver.Value(teach_num[Teachers[T]]) == n:
            Ts.append(T)
    if Ts:
        print(f"{n}: {' '.join(Ts)}")
