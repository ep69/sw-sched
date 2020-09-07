#!/usr/bin/env python3

import sys
from ortools.sat.python import cp_model

days = ["Monday", "Tuesday", "Wednesday", "Thursday"]
Days = {}
for i, D in enumerate(days):
    Days[D] = i
times = ["17:30-18:40", "18:45-19:55", "20:00-21:10"]
slots = [ d + " " + t for d in days for t in times ]

rooms = ["big", "small", "koli-1", "koli-2"]
Rooms = {}
for i, R in enumerate(rooms):
    Rooms[R] = i

venues = ["mosilana", "koliste"]
Venues = {}
for i, V in enumerate(venues):
    Venues[V] = i

# name, active?, role, community
TEACHERS = [
    ("David", False, "lead", False),
    ("Tom-S.", True, "lead", False),
    ("Kuba-Š.", True, "lead", False),
    ("Peťa", True, "lead", False),
    ("Tom-K.", True, "lead", False),
    ("Jarin", True, "lead", False),
    ("Quique", False, "lead", False),
    ("Maťo", True, "lead", True),
    ("Martin", False, "lead", False),
    ("Michal", True, "lead", False),
    ("Vojta-S.", True, "lead", True),
    ("Standa", True, "lead", False),
    ("Kolin", False, "lead", False),
    ("Kepo", True, "lead", False),
    ("Vojta-N.", True, "lead", True),
    ("Kuba-B.", True, "lead", True),
    ("Zbyňa", False, "lead", False),
    ("Radek-Š.", True, "lead", False),
    ("FANTOMAS", True, "lead", False), # TODO
    ("Terka", True, "follow", False),
    ("Janča", True, "follow", False),
    ("Ilča", True, "follow", False),
    ("Pavli", True, "follow", False),
    ("Poli", False, "follow", False),
    ("Linda", True, "follow", False),
    ("Mária", True, "follow", False),
    ("Silvia", True, "follow", False),
    ("Bláža", True, "follow", True),
    ("Ivča", True, "follow", True),
    ("Míša-L.", True, "follow", True),
    ("Zuzka", True, "follow", True),
    ("Soňa", False, "follow", False),
    ("Marie", False, "follow", False),
    ("Pavla-Š.", True, "follow", False),
    ("Míša-Z.", True, "follow", True),
    ("SUPERGIRL", True, "follow", False), # TODO
    ]
TEACHERS = [t for t in TEACHERS if t[1]] # forget inactive teachers

teachers = [t[0] for t in TEACHERS if t[1]] # all active teachers
teachers_lead = [t[0] for t in TEACHERS if t[2] == "lead"]
teachers_follow = [t[0] for t in TEACHERS if t[2] == "follow"]
assert(set(teachers) == set(teachers_lead + teachers_follow))
assert(len(set(teachers_lead) & set(teachers_follow)) == 0)
teachers_core = [t[0] for t in TEACHERS if not t[3]]
teachers_community = [t[0] for t in TEACHERS if t[3]]
print(f"Core teachers: {teachers_core}")
print(f"Community teachers: {teachers_community}")
assert(set(teachers) == set(teachers_core + teachers_community))
assert(len(set(teachers_core) & set(teachers_community)) == 0)

Teachers = {}
for (i, t) in enumerate(teachers):
    Teachers[t] = i

rooms_venues = {
    "small": "mosilana",
    "big": "mosilana",
    "koli-1": "koliste",
    "koli-2": "koliste",
    }

courses_open = [
    "Lindy/Charleston Open Training",
    "Blues/Slow Open Training",
    "Balboa Closed Training",
    ]
courses_solo = [
    "Solo",
    "Teachers' Training",
    "Shag/Balboa Open Training",
    ]
courses_regular = [
    "LH 1 - Beginners /1",
    "LH 1 - Beginners /2",
    "LH 1 - Beginners /3",
    "LH 2 - TODO /1",
    "LH 2 - TODO /2",
    "LH 2.5 - Swing-out /1",
    "LH 2.5 - Swing-out /2",
    "LH 3 - TODO /1",
    "LH 3 - TODO /2",
    "LH 3 - TODO /3",
    "LH 4 - TODO /1",
    "LH 4 - TODO /2",
    "LH 5 - TODO",
    "Balboa 1",
    "Balboa 2",
    "SlowBal",
    "Airsteps TODO",
    "Collegiate Shag 1",
    "Collegiate Shag 2",
    "Saint Louis Shag",
    "Blues",
    "Lindy 45",
    "Solo 45",
    "PJ Group /1",
    "PJ Group /2",
    "PJ Group /3",
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
# leads' desires
t_util_desired["Michal"] = 2
t_util_desired["Jarin"] = 2
t_util_desired["Kuba-Š."] = 6 # 3 # TODO
t_util_desired["Peťa"] = 1
t_util_desired["Tom-S."] = 2
t_util_desired["Tom-K."] = 1
t_util_desired["Kepo"] = 7 # PJ
t_util_desired["Radek-Š."] = 2
t_util_desired["Standa"] = 3
# follows' desires
t_util_desired["Terka"] = 3
t_util_desired["Janča"] = 9 # PJ
t_util_desired["Ilča"] = 6
t_util_desired["Pavli"] = 2
t_util_desired["Linda"] = 2
t_util_desired["Mária"] = 1
t_util_desired["Silvia"] = 2
t_util_desired["Pavla-Š."] = 2

# course C can be taught only by Ts
teachers_lh1 = list(set(teachers) - set(["Tom-S.", "Standa", "Terka", "Míša-Z."]))
teachers_lh2 = list(set(teachers) - set(["Peťa", "Standa", "Míša-Z."]))
teachers_lh2_5 = list(set(teachers) - set(["Peťa", "Standa", "Zuzka", "Míša-Z."]))
teachers_lh3 = list(set(teachers) - set(["Peťa", "Standa", "Zuzka", "Míša-Z."]))
teachers_lh4 = list(set(teachers_core) - set(["Peťa", "Standa"]))
teachers_lh5 = ["Kuba-Š.", "Ilča"]
teachers_airsteps = ["Tom-S.", "Janča"]
teachers_shag = ["Terka", "Linda", "Standa", "Míša-Z."]
teachers_sls = ["Terka", "Janča", "Maťo"]
teachers_balboa = ["Peťa", "Jarin", "Kuba-Š.", "Pavli", "Ilča"]
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
        elif "Saint Louis Shag" in C:
            ct_possible[C] = teachers_sls
        elif C.startswith("Balboa"):
            ct_possible[C] = teachers_balboa
ct_possible["Lindy 45"] = ["Jarin", "Ivča"]

# course C must not take place in room R
# TODO improve - some of these actualy fake course-venues constraints
cr_not = {}
cr_not["Airsteps TODO"] = "small"
cr_not["Collegiate Shag 1"] = "small"
cr_not["Collegiate Shag 2"] = "small"
cr_not["LH 1 - Beginners /1"] = "small"
cr_not["LH 1 - Beginners /2"] = "small"
cr_not["LH 1 - Beginners /3"] = "small"
cr_not["Teachers' Training"] = "big" # must not be in mosilana
cr_not["Lindy/Charleston Open Training"] = "big" # must not be in mosilana
cr_not["Blues/Slow Open Training"] = "big" # must not be in mosilana

# course C must take place in room R
# PJ in small room
cr_strict = {}
cr_strict["PJ Group /1"] = "big"
cr_strict["PJ Group /2"] = "big"
cr_strict["PJ Group /3"] = "big"

# teacher T must teach courses Cs
tc_strict = {}
tc_strict["Kuba-Š."] = ["LH 2 - TODO /1", "LH 5 - TODO", "Teachers' Training"]
tc_strict["Tom-K."] = ["Blues"]
tc_strict["Jarin"] = ["SlowBal", "Lindy 45"]
tc_strict["Kepo"] = ["Solo", "PJ Group /1", "PJ Group /2", "PJ Group /3"]
tc_strict["Janča"] = ["PJ Group /1", "PJ Group /2", "PJ Group /3"]
tc_strict["Pavli"] = ["SlowBal"]
tc_strict["Ilča"] = ["Blues", "LH 5 - TODO"]
tc_strict["Ivča"] = ["Lindy 45"]
tc_strict["Míša-L."] = ["LH 2 - TODO /1"]
tc_strict["Radek-Š."] = ["Solo 45", "LH 4 - TODO /1"]
tc_strict["Pavla-Š."] = ["Solo 45", "LH 4 - TODO /1"]
tc_strict["Terka"] = ["Collegiate Shag 2"]
tc_strict["Míša-Z."] = ["Collegiate Shag 1"]
tc_strict["Standa"] = ["Shag/Balboa Open Training"]
tc_strict["Peťa"] = ["Balboa 2"]


# teacher T1 must not teach a course with teacher T2
tt_not_together = [
        #("Kuba-Š.", "Soňa"),
        ("Michal", "Ilča"),
        ]

# teacher T wants to teach with community teacher
#t_withnew = ["Janča"]

# course Cx must happen on different day and at different time than Cy (and Cz)
courses_different = [
    ["LH 1 - Beginners /1", "LH 1 - Beginners /2", "LH 1 - Beginners /3"],
    #["LH 1 - Beginners /1", "LH 1 - Beginners /2"],
    ["LH 2.5 - Swing-out /1", "LH 2.5 - Swing-out /2"],
    ]

# course Cx must happen on different day time than Cy (and Cz)
courses_diffday = [
    #["PJ Group /1", "PJ Group /2"],
    ]

# course C1, C2, (C3) should happen
#  * on the same day
#  * in different times
#  * following each other
#  * in the same venue
courses_same = [
    ["Collegiate Shag 2", "Shag/Balboa Open Training"],
    #["Balboa 2", "Shag/Balboa Open Training"],
    #["Balboa 1", "Balboa Closed Training"],
    #["Balboa 2", "Balboa Closed Training"],
    ["Balboa 1", "Balboa 2", "Balboa Closed Training"],
    ["Solo 45", "Lindy 45"],
    ["Solo 45", "LH 4 - TODO /1"], # Sustkovi cannot travel to Brno twice a week
    ["Blues", "Blues/Slow Open Training"],
    ["PJ Group /1", "PJ Group /3"], # faking two slot class
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
# course C takes place in slot S
cs = []
for c in range(len(courses)):
    cs.append(model.NewIntVar(0, len(slots)-1, ""))
# room R is in venue V
rv = []
for r in range(len(rooms)):
    rv.append(model.NewIntVar(0, len(venues)-1, ""))
    model.Add(rv[r] == Venues[rooms_venues[rooms[r]]])
# teacher T teaches in slot S course C in venue V
tscv = {}
for t in range(len(teachers)):
    for s in range(len(slots)):
        for c in range(len(courses)):
            for v in range(len(venues)):
                tscv[(t,s,c,v)] = model.NewBoolVar("")

# teacher T teaches in venue V on day D
tdv = {}
for t in range(len(teachers)):
    for d in range(len(days)):
        for v in range(len(venues)):
            tdv[(t,d,v)] = model.NewBoolVar("")

# teacher T teaches course C in slot S iff course C takes place at slot S and is taught by teacher T
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

# inferring TDV info
for s in range(len(slots)):
    for c in range(len(courses)):
        for v in range(len(venues)):
            hit = model.NewBoolVar("") # course C is at slot S in venue V
            model.Add(sum(src[(s,r,c)] for r in range(len(rooms)) if rooms_venues[rooms[r]] == venues[v]) == 1).OnlyEnforceIf(hit)
            model.Add(sum(src[(s,r,c)] for r in range(len(rooms)) if rooms_venues[rooms[r]] == venues[v]) == 0).OnlyEnforceIf(hit.Not())
            for t in range(len(teachers)):
                model.AddBoolAnd([hit, tc[(t,c)]]).OnlyEnforceIf(tscv[(t,s,c,v)])
                model.AddBoolOr([hit.Not(), tc[(t,c)].Not()]).OnlyEnforceIf(tscv[(t,s,c,v)].Not())
for t in range(len(teachers)):
    for d in range(len(days)):
        for v in range(len(venues)):
            model.Add(sum(tscv[(t,s,c,v)] for s in range(d*len(times),(d+1)*len(times)) for c in range(len(courses))) >= 1).OnlyEnforceIf(tdv[(t,d,v)])
            model.Add(sum(tscv[(t,s,c,v)] for s in range(d*len(times),(d+1)*len(times)) for c in range(len(courses))) == 0).OnlyEnforceIf(tdv[(t,d,v)].Not())
# inferring CV info
cv = []
for c in range(len(courses)):
    cv.append(model.NewIntVar(0, len(venues)-1, ""))
    for v in range(len(venues)):
        hit = model.NewBoolVar("")
        model.Add(sum(src[(s,r,c)] for s in range(len(slots)) for r in range(len(rooms)) if rooms_venues[rooms[r]] == venues[v]) >= 1).OnlyEnforceIf(hit)
        model.Add(sum(src[(s,r,c)] for s in range(len(slots)) for r in range(len(rooms)) if rooms_venues[rooms[r]] == venues[v]) == 0).OnlyEnforceIf(hit.Not())
        model.Add(cv[c] == v).OnlyEnforceIf(hit)
        model.Add(cv[c] != v).OnlyEnforceIf(hit.Not())

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

# community teachers that must teach
for T in ["Zuzka", "Vojta-N.", "Míša-L.", "Kuba-B."]:
    model.Add(sum(tc[(Teachers[T],c)] for c in range(len(courses))) >= 1)

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

# teacher T does not teach in two venues in the same day
for t in range(len(teachers)):
    for d in range(len(days)):
        model.Add(sum(tdv[(t,d,v)] for v in range(len(venues))) <= 1)

# Teachers' time preferences
# TODO: find a better place for this part

# teacher T availability at day D:
#   0 cannot
#   1 barely
#   2 fine (default)
#   3 great
td_pref = {}
td_pref[("Tom-S.", "Monday")] = 0
td_pref[("Tom-S.", "Tuesday")] = 3
td_pref[("Tom-K.", "Tuesday")] = 0
td_pref[("Tom-K.", "Wednesday")] = 3
td_pref[("Tom-K.", "Thursday")] = 0
td_pref[("Maťo", "Tuesday")] = 3
td_pref[("Maťo", "Wednesday")] = 3
td_pref[("Michal", "Monday")] = 0
td_pref[("Radek-Š.", "Monday")] = 0
td_pref[("Radek-Š.", "Wednesday")] = 0
td_pref[("Terka", "Thursday")] = 0
td_pref[("Janča", "Monday")] = 3
td_pref[("Janča", "Tuesday")] = 3
td_pref[("Janča", "Wednesday")] = 3
td_pref[("Ilča", "Tuesday")] = 3
td_pref[("Ilča", "Wednesday")] = 3
td_pref[("Ilča", "Thursday")] = 3
td_pref[("Pavli", "Tuesday")] = 0
td_pref[("Pavli", "Wednesday")] = 3
td_pref[("Pavli", "Thursday")] = 0
td_pref[("Linda", "Tuesday")] = 3
td_pref[("Linda", "Wednesday")] = 0
td_pref[("Linda", "Thursday")] = 3
td_pref[("Zuzka", "Tuesday")] = 0
td_pref[("Zuzka", "Thursday")] = 3
td_pref[("Pavla-Š.", "Monday")] = 0
td_pref[("Pavla-Š.", "Wednesday")] = 0
td_pref[("Míša-Z.", "Wednesday")] = 0

# teacher T availability at time X (0 - first slot, 1 - second slot, 2 - third slot):
#   0 cannot
#   1 barely
#   2 fine (default)
#   3 great
ttime_pref = {}
ttime_pref[("Jarin", 2)] = 1
ttime_pref[("Peťa", 0)] = 3
ttime_pref[("Peťa", 2)] = 0
ttime_pref[("Tom-S.", 0)] = 3
ttime_pref[("Tom-S.", 1)] = 3
ttime_pref[("Radek-Š.", 0)] = 0
ttime_pref[("Linda", 2)] = 1
ttime_pref[("Mária", 2)] = 0 # TODO
ttime_pref[("Silvia", 2)] = 0 # TODO
ttime_pref[("Zuzka", 0)] = 0
ttime_pref[("Pavla-Š.", 0)] = 0

# strict teacher-slot constraints:
# Standa cannot teach the first Tuesday slot
model.Add(ts[(Teachers["Standa"],3)] == 0)
# Vojta-N. wants to hang out with students, so prefers NOT to teach right before Teachers' Training
model.Add(ts[(Teachers["Vojta-N."],10)] == 0)
# Ilča cannot teach on Wednesday evening
model.Add(ts[(Teachers["Ilča"],8)] == 0)
# Kuba "teaches" Teachers' Training
#model.Add(ts[(Teachers["Kuba-Š."],11)] == 0)

# strict courses schedule
# Teachers training must be at Thursday evening
model.Add(cs[Courses["Teachers' Training"]] == 11)
# nothing else happens in parallel with Teachers' Training
model.Add(sum(src[(11,r,c)] for r in range(len(rooms)) for c in range(len(courses))) == 1)
# Balboa Training must be at Wednesday evening
#model.Add(cs[Courses["Balboa Closed Training"]] == 8)
# Blues Training must not be on Monday
#model.Add(cs[Courses["Blues/Slow Open Training"]] > 2)
# Shag/Balboa open is AFTER Collegiate Shag 2 (combined with courses_same
model.Add(cs[Courses["Collegiate Shag 2"]]+1 == cs[Courses["Shag/Balboa Open Training"]])
# Balboa Closed Training does not take place in the last evening slot so Poli can attend
c = Courses["Balboa Closed Training"]
for d in range(len(days)):
    model.Add(cs[c] != d*len(times)+2)
# PJ training must happen on Tuesday and Thursday
model.Add(cs[Courses["PJ Group /1"]] >= 3)
model.Add(cs[Courses["PJ Group /1"]] <= 5)
model.Add(cs[Courses["PJ Group /2"]] >= 9)
model.Add(cs[Courses["PJ Group /2"]] <= 11)

#c = Courses["Lindy 45"]
#for d in range(len(days)):
#    model.Add(cs[c] != d*len(times)+0)

# strict day preferences
for (T,D), n in td_pref.items():
    if n == 0: # T cannot teach on day D
        model.Add(td[(Teachers[T], Days[D])] == 0)

# strict time preferences
for (T,t), n in ttime_pref.items():
    if n == 0: # T cannot teach on day D
        for d in range(len(days)):
            model.Add(ts[(Teachers[T], d*len(times)+t)] == 0)

# same courses should not happen in same days and also not in same times
# it should probably not be a strict limitation, but it is much easier to write
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

# courses that should not happen in same days
for Cs in courses_diffday:
    daylist = [] # days
    assert(2 <= len(Cs) <= len(days))
    for C in Cs:
        day = model.NewIntVar(0, len(days)-1, "")
        model.AddDivisionEquality(day, cs[Courses[C]], len(times))
        model.AddModuloEquality(time, cs[Courses[C]], len(times))
        daylist.append(day)
    model.AddAllDifferent(daylist)

# courses that should follow each other in the same day in the same venue
for Cs in courses_same:
    daylist = [] # days
    timelist = [] # times
    venuelist = [] # venues
    assert(2 <= len(Cs) <= len(times))
    for C in Cs:
        day = model.NewIntVar(0, len(days)-1, "")
        time = model.NewIntVar(0, len(times)-1, "")
        venue = model.NewIntVar(0, len(venues)-1, "")
        model.AddDivisionEquality(day, cs[Courses[C]], len(times))
        model.AddModuloEquality(time, cs[Courses[C]], len(times))
        model.Add(venue == cv[Courses[C]])
        daylist.append(day)
        timelist.append(time)
        venuelist.append(venue)
    model.AddAllowedAssignments(daylist, [[d] * len(Cs) for d in range(len(days))])
    model.AddAllowedAssignments(venuelist, [[v] * len(Cs) for v in range(len(venues))])
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

for (C, R) in cr_not.items():
    model.Add(sum(src[(s,Rooms[R],Courses[C])] for s in range(len(slots))) == 0)

for (C, R) in cr_strict.items():
    model.Add(sum(src[(s,Rooms[R],Courses[C])] for s in range(len(slots))) == 1)

# community teachers must teach max 2 courses
for T in teachers_community:
    model.Add(sum(tc[(Teachers[T],c)] for c in range(len(courses))) <= 2)
# community teachers must teach together with core teachers
for C in courses_regular:
    model.Add(sum(tc[(Teachers[T],Courses[C])] for T in teachers_community) <= 1)
# community teachers cannot teach solo courses
for C in courses_solo:
    model.Add(sum(tc[(Teachers[T],Courses[C])] for T in teachers_community) == 0)


# Rather specific constraints:

# course has to take place at specific slot and room
#model.Add(src[(0,Rooms["big"],Courses["Airsteps 2"])] == 1)

# course has to take place at specific slot
#model.Add(sum(src[(0,r,Courses["Collegiate Shag 1"])] for r in range(len(rooms))) == 1)


# Damian
damian = True
if damian:
    model.Add(sum(tc[(Teachers["Tom-K."],c)] for c in range(len(courses))) == 1)
    model.Add(sum(tc[(Teachers["Pavli"],c)] for c in range(len(courses))) == 2)
    model.Add(sum(tscv[(Teachers["Tom-K."],s,c,Venues["mosilana"])] for s in range(len(slots)) for c in range(len(courses))) == 0)
    model.Add(sum(tscv[(Teachers["Pavli"],s,c,Venues["mosilana"])] for s in range(len(slots)) for c in range(len(courses))) == 0)
    damianday = model.NewIntVar(0, len(days)-1, "damianday")
    for d in range(len(days)):
        hit = model.NewBoolVar("")
        model.Add(damianday == d).OnlyEnforceIf(hit)
        model.Add(damianday != d).OnlyEnforceIf(hit.Not())
        model.Add(ts[(Teachers["Tom-K."],d*len(times)+0)] == 1).OnlyEnforceIf(hit)
        model.Add(ts[(Teachers["Pavli"],d*len(times)+1)] == 1).OnlyEnforceIf(hit)
        model.Add(ts[(Teachers["Pavli"],d*len(times)+2)] == 1).OnlyEnforceIf(hit)

# OPTIMIZATION

# "name" -> coeff
PENALTIES = {
    "overwork": 100,
    "underwork": 100,
    "days": 300,
    "split": 300,
    "daypref_bad": 300,
    "daypref_slight": 50,
    "timepref_bad": 300,
    "timepref_slight": 50,
    "rent": 5000,
    "mosilana": 300,
    "balboa_closed": 100,
    "faketeachers": 10000,
}

penalties = {} # penalties data (model variables)
penalties_analysis = {} # deeper analysis functions for penalties

for (name, coeff) in PENALTIES.items():
    if coeff == 0:
        print(f"Penalties: skipping '{name}'")
        continue
    #if PENALTY_OVERWORK > 0 or PENALTY_UNDERWORK > 0:
    if name == "underwork":
        # teaching should be split evenly
        #penalties_overwork = []
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
            #if PENALTY_OVERWORK > 0:
            #    util_excess = model.NewIntVar(0, max_diff, "")
            #    model.AddMaxEquality(util_excess, [util_diff, 0])
            #    util_excess_sq = model.NewIntVar(0, max_diff**2, "Texcesssq:%i" % t)
            #    model.AddMultiplicationEquality(util_excess_sq, [util_excess, util_excess])
            #    penalties_overwork.append(util_excess_sq)
        #if PENALTY_UNDERWORK > 0:
            # we consider -1 difference ok - e.g., if teacher wants to teach 4 courses, it is ok to teach 3
            util_diff_incr = model.NewIntVar(min_diff+1, max_diff+1, "")
            model.Add(util_diff_incr == util_diff + 1)
            util_lack = model.NewIntVar(min_diff, 0, "")
            model.AddMinEquality(util_lack, [util_diff_incr, 0])
            util_lack_abs = model.NewIntVar(0, abs(min_diff), "")
            model.AddAbsEquality(util_lack_abs, util_lack)
            penalties_underwork.append(util_lack_abs)
        #penalties.append(sum(penalties_overwork) * PENALTY_OVERWORK + sum(penalties_underwork) * PENALTY_UNDERWORK)
        penalties[name] = penalties_underwork
    elif name == "days":
        # nobody should come more days then necessary
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
        penalties[name] = penalties_days
        def analysis(src, tc):
            result = []
            for t in range(len(teachers)):
                cs = []
                for c in range(len(courses)):
                    if tc[(t,c)]:
                        cs.append(c)
                n_courses = sum(tc[(t,c)] for c in range(len(courses)))
                assert(len(cs) == n_courses)
                n_days = 0
                for d in range(len(days)):
                    if sum(src[(s,r,c)] for s in range(d*len(times), (d+1)*len(times)) for r in range(len(rooms)) for c in cs):
                        n_days += 1
                if n_days*len(times) - n_courses >= len(times):
                    result.append(f"{teachers[t]} {n_courses}c/{n_days}d")
            return result
        penalties_analysis[name] = analysis
    elif name == "split":
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
        penalties[name] = penalties_split
        def analysis(src, tc):
            result = []
            for t in range(len(teachers)):
                cs = []
                for c in range(len(courses)):
                    if tc[(t,c)]:
                        cs.append(c)
                n = 0
                for d in range(len(days)):
                    if (
                            sum(src[(d*len(times),r,c)]  for r in range(len(rooms)) for c in cs) >= 1
                            and sum(src[(d*len(times)+1,r,c)]  for r in range(len(rooms)) for c in cs) == 0
                            and sum(src[(d*len(times)+2,r,c)]  for r in range(len(rooms)) for c in cs) >= 1
                            ):
                        n += 1
                if n > 0:
                    result.append(f"{teachers[t]}/{n}")
            return result
        penalties_analysis[name] = analysis
    elif name == "daypref_bad":
        # day preferences
        penalties_daypref_bad = []
        for T in teachers:
            t = Teachers[T]
            prefs = []
            for D in days:
                prefs.append(td_pref.get((T,D), 2))
            if set(prefs) - set([0, 2]): # teacher T prefers some days over others
                if 1 in set(prefs): # some days are bad
                    days_bad = [d for d in range(len(prefs)) if prefs[d] == 1]
                    penalties_daypref_bad.append(sum(td[(t,d)] for d in days_bad))
        penalties[name] = penalties_daypref_bad
        def analysis(src, tc):
            result = []
            for t in range(len(teachers)):
                cs = []
                for c in range(len(courses)):
                    if tc[(t,c)]:
                        cs.append(c)
                bad_days = []
                for d in range(len(days)):
                    if td_pref.get((teachers[t],days[d]), 2) == 1:
                        if sum(src[(s,r,c)]  for s in range(d*len(times),(d+1)*len(times)) for r in range(len(rooms)) for c in cs) >= 1:
                            bad_days.append(d)
                if bad_days:
                    result.append(f"{teachers[t]}/{','.join([days[d] for d in bad_days])}")
            return result
        penalties_analysis[name] = analysis
    elif name == "daypref_slight":
        # day preferences
        penalties_daypref_slight = []
        for T in teachers:
            t = Teachers[T]
            prefs = []
            for D in days:
                prefs.append(td_pref.get((T,D), 2))
            if set(prefs) - set([0, 2]): # teacher T prefers some days over others
                if set([2,3]) <= set(prefs):
                    # days that are slightly less preferred
                    days_slight_worse = [d for d in range(len(prefs)) if prefs[d] == 2]
                    penalties_daypref_slight.append(sum(td[(t,d)] for d in days_slight_worse))
        penalties[name] = penalties_daypref_slight
    elif name == "timepref_bad":
        # time preferences
        penalties_timepref_bad = []
        for T in teachers:
            t = Teachers[T]
            prefs = []
            for time in range(len(times)):
                prefs.append(ttime_pref.get((T,time), 2))
            if set(prefs) - set([0, 2]): # teacher T prefers some times over others
                if 1 in set(prefs):
                    # not preferred times
                    times_bad = [time for time in range(len(prefs)) if prefs[time] == 1]
                    slots_bad = [d*len(times)+time for time in times_bad for d in range(len(days))]
                    penalties_timepref_bad.append(sum(ts[(t,s)] for s in slots_bad))
        penalties[name] = penalties_timepref_bad
        def analysis(src, tc):
            result = []
            for t in range(len(teachers)):
                cs = []
                for c in range(len(courses)):
                    if tc[(t,c)]:
                        cs.append(c)
                bad_times = []
                for time in range(len(times)):
                    if ttime_pref.get((teachers[t],time), 2) == 1:
                        bad_times.append(time)
                n = 0
                bad_days = []
                for d in range(len(days)):
                    day_sum = sum(src[(d*len(times)+time,r,c)]  for time in bad_times for r in range(len(rooms)) for c in cs)
                    if day_sum >= 1:
                        n += day_sum
                        bad_days.append(d)
                if bad_days:
                    result.append(f"{teachers[t]}/{n}-{','.join([days[d] for d in bad_days])}")
            return result
        penalties_analysis[name] = analysis
    elif name == "timepref_slight":
        # time preferences
        penalties_timepref_slight = []
        for T in teachers:
            t = Teachers[T]
            prefs = []
            for time in range(len(times)):
                prefs.append(ttime_pref.get((T,time), 2))
            if set(prefs) - set([0, 2]): # teacher T prefers some times over others
                if set([2,3]) <= set(prefs):
                    # times that are slightly less preferred
                    times_slight_worse = [time for time in range(len(prefs)) if prefs[time] == 2]
                    slots_slight_worse = [d*len(times)+time for time in times_slight_worse for d in range(len(days))]
                    penalties_timepref_slight.append(sum(ts[(t,s)] for s in slots_slight_worse))
        penalties[name] = penalties_timepref_slight
    elif name == "rent": # we want to rent the small room so it should be empty
        # we want the small room to be empty so we can rent it
        smalltaken = model.NewBoolVar("")
        model.Add(sum(src[(s,Rooms["small"],c)] for s in range(len(slots)) for c in range(len(courses))) >= 1).OnlyEnforceIf(smalltaken)
        model.Add(sum(src[(s,Rooms["small"],c)] for s in range(len(slots)) for c in range(len(courses))) == 0).OnlyEnforceIf(smalltaken.Not())
        penalties[name] = [smalltaken]
    elif name == "faketeachers":
        penalties_faketeachers = []
        # FANTOMAS and SUPERGIRL
        if "FANTOMAS" in teachers:
            penalties_faketeachers.append(sum(tc[(Teachers["FANTOMAS"],c)] for c in range(len(courses))))
        if "SUPERGIRL" in teachers:
            penalties_faketeachers.append(sum(tc[(Teachers["SUPERGIRL"],c)] for c in range(len(courses))))
        penalties[name] = penalties_faketeachers
    elif name == "mosilana": # penalty for not using koliste
        util_koliste = model.NewIntVar(0, 2*len(slots), "") # utilization of Koliste
        model.Add(util_koliste == sum(src[(s,r,c)] for s in range(len(slots)) for r in range(len(rooms)) if rooms_venues[rooms[r]] == "koliste" for c in range(len(courses))))
        free_koliste = model.NewIntVar(0, 2*len(slots), "") # free slots in Koliste
        model.Add(free_koliste == 2*len(slots)-util_koliste-1) # -1 for Teachers' Training
        penalties[name] = [free_koliste]
    elif name == "balboa_closed": # penalty if interested people cannot attend Balboa Closed Training (they teach something else in the same time)
        # Poli is omitted as inactive
        baltrain_people = ["Peťa", "Jarin", "Kuba-Š.", "Maťo", "Ilča", "Pavli", "Ivča"]
        penalties_balboa_closed = []
        for s in range(len(slots)):
            hit = model.NewBoolVar("")
            model.Add(cs[Courses["Balboa Closed Training"]] == s).OnlyEnforceIf(hit)
            model.Add(cs[Courses["Balboa Closed Training"]] != s).OnlyEnforceIf(hit.Not())
            pbc = model.NewIntVar(0, len(baltrain_people)-1, "") # penalty for the slot
            model.Add(pbc == sum(ts[(Teachers[T],s)] for T in baltrain_people)).OnlyEnforceIf(hit)
            model.Add(pbc == 0).OnlyEnforceIf(hit.Not())
            penalties_balboa_closed.append(pbc)
        penalties[name] = penalties_balboa_closed

penalties_values = []
for (name, l) in penalties.items():
    penalties_values.append(PENALTIES[name] * sum(l))

model.Minimize(sum(penalties_values))

print(model.ModelStats())
print()

def print_solution(src, tc, penalties, objective=None):
    if objective:
        print(f"Objective value: {objective}")
    for s in range(len(slots)):
        for r in range(len(rooms)):
            for c in range(len(courses)):
                if src[(s,r,c)]:
                    Ts = []
                    if courses[c] in courses_open:
                        Ts.append("OPEN\t")
                    elif courses[c] in courses_solo:
                        for t in range(len(teachers)):
                            #if solver.Value(tc[(t,c)]):
                            if tc[(t,c)]:
                                Ts.append(teachers[t] + "\t")
                                break
                    elif courses[c] in courses_regular:
                        for t in range(len(teachers)):
                            if tc[(t,c)]:
                                Ts.append(teachers[t])
                    if len(Ts) == 2 and Ts[0] in teachers_follow:
                        Ts[0], Ts[1] = Ts[1], Ts[2]
                    print(f"{slots[s]}\t {rooms[r]}\t{'+'.join(Ts)}\t{courses[c]}")
    if penalties:
        print("Penalties:")
        total = 0
        for (name, t) in penalties.items():
            coeff, v = t
            total += coeff * v
            #print(f"{name}: {sum([solver.Value(p) for p in l])} * {PENALTIES[name]}")
            if v:
                if name in penalties_analysis:
                    print(f"{name}: {v} * {coeff} = {v*coeff} ({', '.join(penalties_analysis[name](src, tc))})")
                else:
                    print(f"{name}: {v} * {coeff} = {v*coeff}")
        print(f"TOTAL: {total}")

class ContinuousSolutionPrinter(cp_model.CpSolverSolutionCallback):
    def __init__(self):
        self.count = 0
        cp_model.CpSolverSolutionCallback.__init__(self)

    def OnSolutionCallback(self):
    #def on_solution_callback(self):
        result_src = {}
        for s in range(len(slots)):
            for r in range(len(rooms)):
                for c in range(len(courses)):
                        result_src[(s,r,c)] = self.Value(src[(s,r,c)])
        result_tc = {}
        for t in range(len(teachers)):
            for c in range(len(courses)):
                result_tc[(t,c)] = self.Value(tc[(t,c)])
        result_penalties = {}
        for (name, l) in penalties.items():
            v = sum([self.Value(p) for p in l])
            coeff = PENALTIES[name]
            result_penalties[name] = (coeff, v)
        print(f"No: {self.count}")
        print(f"Wall time: {self.WallTime()}")
        #print(f"Branches: {self.NumBranches()}")
        #print(f"Conflicts: {self.NumConflicts()}")
        print_solution(result_src, result_tc, result_penalties, self.ObjectiveValue())
        print()
        self.count += 1


solver = cp_model.CpSolver()
#solver.parameters.max_time_in_seconds = 20.0
#status = solver.Solve(model)
#status = solver.SolveWithSolutionCallback(model, cp_model.ObjectiveSolutionPrinter())
status = solver.SolveWithSolutionCallback(model, ContinuousSolutionPrinter())
statusname = solver.StatusName(status)
print(f"Solving finished in {solver.WallTime()} seconds with status {status} - {statusname}")
if statusname not in ["FEASIBLE", "OPTIMAL"]:
    print("Solution NOT found")
    sys.exit(1)

result_src = {}
for s in range(len(slots)):
    for r in range(len(rooms)):
        for c in range(len(courses)):
                result_src[(s,r,c)] = solver.Value(src[(s,r,c)])
result_tc = {}
for t in range(len(teachers)):
    for c in range(len(courses)):
        result_tc[(t,c)] = solver.Value(tc[(t,c)])
result_penalties = {}
for (name, l) in penalties.items():
    v = sum([solver.Value(p) for p in l])
    coeff = PENALTIES[name]
    result_penalties[name] = (coeff, v)
print()
print("SOLUTION:")
print_solution(result_src, result_tc, result_penalties)

print()
print(f"Teachers' utilization:")
for n in range(len(slots)):
    Ts = []
    for T in teachers:
        if solver.Value(teach_num[Teachers[T]]) == n:
            Ts.append(T)
    if Ts:
        print(f"{n}: {' '.join(Ts)}")

# TODO:
#  LH1 should really be in Koliste so new people can pay and get personal info
#  concept of course attendance preferences, i.e. teacher T would like to be student in course C (time, venue, connected time)
