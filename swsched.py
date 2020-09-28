#!/usr/bin/env python3

import sys
import csv
from ortools.sat.python import cp_model

VERBOSE = True

def debug(m):
    if not VERBOSE:
        return
    print(f"DEBUG: {m}")

def warn(m):
    print(f"WARNING: {m}")

def error(m):
    print(f"ERROR: {m}")
    sys.exit(1)

days = ["Monday", "Tuesday", "Wednesday", "Thursday"]
Days = {}
for i, D in enumerate(days):
    Days[D] = i
times = ["17:30-18:40", "18:45-19:55", "20:00-21:10"]
slots = [ d + " " + t for d in days for t in times ]

rooms = [
    "big",
    #"small",
    "koli-3",
    "koli-4",
]
Rooms = {}
for i, R in enumerate(rooms):
    Rooms[R] = i

venues = ["mosilana", "koliste"]
Venues = {}
for i, V in enumerate(venues):
    Venues[V] = i

# name, role, community
TEACHERS = [
    ("David", "lead", False),
    ("Tom-S.", "lead", False),
    ("Kuba-Š.", "lead", False),
    ("Peťa", "lead", False),
    ("Tom-K.", "lead", False),
    ("Jarin", "lead", False),
    ("Quique", "lead", False),
    ("Maťo", "lead", True),
    ("Martin", "lead", False),
    ("Michal", "lead", False),
    ("Vojta-S.", "lead", True),
    ("Standa", "lead", False),
    ("Kolin", "lead", False),
    ("Kepo", "lead", False),
    ("Vojta-N.", "lead", True),
    ("Kuba-B.", "lead", True),
    ("Zbyňa", "lead", False),
    #("Radek-Š.", "lead", False),
    ("FANTOMAS", "lead", False), # TODO
    ("BATMAN", "lead", False), # TODO
    ("CHUCK", "lead", False), # TODO
    ("Terka", "follow", False),
    ("Janča", "follow", False),
    ("Ilča", "follow", False),
    ("Pavli", "follow", False),
    ("Poli", "follow", False),
    ("Lili", "follow", False),
    ("Mária", "follow", False),
    ("Silvia", "follow", False),
    ("Blaženka", "follow", True),
    ("Ivča", "follow", True),
    ("Míša-L.", "follow", True),
    ("Zuzka", "follow", True),
    ("Soňa", "follow", False),
    #("Marie", "follow", False),
    #("Pavla-Š.", "follow", False),
    ("Míša-Z.", "follow", True),
    ("SUPERGIRL", "follow", False), # TODO
    ("XENA", "follow", False), # TODO
    ("STORM", "follow", False), # TODO
    ]
FAKE_TEACHERS = ["FANTOMAS", "BATMAN", "CHUCK", "SUPERGIRL", "XENA", "STORM"]

teachers = [t[0] for t in TEACHERS]
teachers_lead = [t[0] for t in TEACHERS if t[1] == "lead"]
teachers_follow = [t[0] for t in TEACHERS if t[1] == "follow"]
assert(set(teachers) == set(teachers_lead + teachers_follow))
assert(len(set(teachers_lead) & set(teachers_follow)) == 0)
teachers_core = [t[0] for t in TEACHERS if not t[2]]
teachers_community = [t[0] for t in TEACHERS if t[2]]
print(f"Core teachers: {teachers_core}")
print(f"Community teachers: {teachers_community}")
assert(set(teachers) == set(teachers_core + teachers_community))
assert(len(set(teachers_core) & set(teachers_community)) == 0)

Teachers = {}
for (i, t) in enumerate(teachers):
    Teachers[t] = i

rooms_venues = {
    #"small": "mosilana",
    "big": "mosilana",
    "koli-3": "koliste",
    "koli-4": "koliste",
    }

courses_open = [
    "Lindy/Charleston Open Training",
    "Blues/Slow Open Training",
    "Balboa Teachers Training",
    ]
courses_solo = [
    "Solo",
    "Teachers Training",
    "Shag/Balboa Open Training",
    ]
courses_regular = [
    "LH 1 - Beginners /1",
    "LH 1 - Beginners /2",
    "LH 1 - Beginners /3",
    "LH 2 - Party Moves",
    "LH 2 - Survival Guide",
    "LH 2.5 - Swingout /1",
    "LH 2.5 - Swingout /2",
    "LH 3 - Musicality",
    "LH 3 - Charleston",
    "LH 3 - Cool Moves and Styling",
    "LH 4 - TODO /1",
    "LH 4 - TODO /2",
    "LH 5",
    "Balboa Beginners",
    "Balboa Intermediate",
    #"SlowBal",
    "Airsteps 2",
    "Collegiate Shag 1",
    "Collegiate Shag 2",
    "Saint Louis Shag 2",
    "Blues",
    #"Lindy 45",
    #"Solo 45",
    "PJ Group /1",
    "PJ Group /2",
    "PJ Group /3",
    ]
courses = courses_regular + courses_solo + courses_open
Courses = {}
for (i, c) in enumerate(courses):
    Courses[c] = i

TEACHER_NAMES = {
    "Zuzka": "Zuzana Rabčanová",
    "Míša-L.": "Michaela Lysková",
    "Ilča": "Ili",
    "Blaženka": "Blažena",
    "Kolin": "Ko1iN",
    "Maťo": "Martin Danko",
    "Míša-Z.": "Michaela Zejdova",
    "Kuba-B.": "Jakub Brandejs",
    "Peťa": "Pete",
    "Ivča": "Ivča Dvořáková",
    "Martin": "Martin Matuszek",
    "Tom-S.": "Tom S",
    "Vojta-S.": "Vojta Semerák",
}

def translate_teacher_name(name):
    name = name.strip()
    if name in teachers:
        return name
    name_nospace = name.replace(" ", "-")
    if name_nospace in teachers:
        return name_nospace
    for k in TEACHER_NAMES:
        if name in TEACHER_NAMES[k]:
            return k
    return f"UNKNOWN {name}"

def check_course(course):
    for c in courses:
        if c.startswith(course):
            return
    error(f"Unknown course: '{course}'")

COURSES_IGNORE = [
    #"Balboa Intermediate",
    "LH 1 - English",
]

def read_input(filename="input.csv"):
    result = {}
    with open(filename, mode="r") as f:
        reader = csv.DictReader(f)
        n = 0
        cs = [] # courses
        for row in reader:
            if n == 0:
                columns = list(row.keys())
                for col in columns:
                    if col.startswith("What courses would you like to teach?"):
                        course = col.split("[")[1].split("]")[0]
                        if course in COURSES_IGNORE:
                            continue
                        check_course(course)
                        # problematic: Balboa Beginners 2
                        cs.append(course)
            else:
                name = translate_teacher_name(row["Who are you?"])
                d = {}
                d["ncourses_ideal"] = int(row["How many courses would you ideally like to teach?"])
                d["ncourses_max"] = int(row["How many courses are you able to teach at most?"])
                slots = []
                for day in ["Mon", "Tue", "Wed", "Thu"]:
                    for time in ["17:30", "18:45", "20:00"]:
                        slots.append(int(row[f"What days and times are convenient for you? [{day} {time}]"][0]))
                d["slots"] = slots
                d["mosilana"] = row["Are you fine with teaching in Mosilana?"] == "Yes"
                courses_teach = {}
                for c in cs:
                    if c in COURSES_IGNORE:
                        continue
                    courses_teach[c] = int(row[f"What courses would you like to teach? [{c}]"][0])
                d["courses_teach"] = courses_teach
                d["courses_attend"] = row["What courses and trainings would you like to attend?"].split(";")
                for c in d["courses_attend"]:
                    if c in COURSES_IGNORE:
                        d["courses_attend"].remove(c)
                for c in d["courses_attend"]:
                    check_course(c)
                # TODO - translate names and actually respect it
                d["teach_together"] = row["Who would you like to teach with?"].split()
                d["teach_not_together"] = [translate_teacher_name(x) for x in row["Are there any people you cannot teach with?"].split() if x not in ["-", "No", "není"]]
                result[name] = d
            n += 1
    debug(f"Number of lines: {n}")
    #print(f"Column names: {columns}")
    return result

from pprint import pprint

input_data = read_input()
for t in input_data.keys():
    if t not in teachers:
        error(f"teacher name {t} needs translation")
pprint(input_data)

# SPECIFIC HARD CONSTRAINTS

# HARD teacher T can teach maximum N courses
t_util_max = {}
# teacher T wants to teach N courses
t_util_ideal = {}
# HARD teacher T1 must not teach a course with teacher T2
tt_not_together = []
# HARD teacher T cannot do anything in slots Ss
ts_pref = {}
# teacher T preference about teaching course C (HARD if 0)
tc_pref = {}

# course C can be taught only by Ts
ct_possible = {}
for C in courses:
    if C not in courses_open:
        if C.startswith(("LH 1 ", "LH 2 ", "LH 2.5 ", "LH 3 ")):
            #ct_possible[C] = list(set(teachers) - set(["Standa", "Míša-Z."]))
            ct_possible[C] = list(set(teachers) - set(["Míša-Z."]))
        elif C.startswith("LH 4"):
            ct_possible[C] = list(set(teachers_core) - set(["Peťa", "Standa"]))
        elif C.startswith("LH 5"):
            ct_possible[C] = ["Kuba-Š.", "Ilča"]
        elif C.startswith("Airsteps"):
            ct_possible[C] = ["Tom-S.", "Janča"]
        elif C.startswith("Collegiate Shag"):
            ct_possible[C] = ["Terka", "Lili", "Standa", "Míša-Z."]
        elif C.startswith("Saint Louis Shag"):
            ct_possible[C] = ["Terka", "Janča", "Maťo"]
        elif C.startswith("Balboa"):
            ct_possible[C] = ["Peťa", "Jarin", "Kuba-Š.", "Pavli", "Ilča", "Poli"]
        elif C.startswith("Balboa"):
            ct_possible[C] = ["Peťa", "Jarin", "Kuba-Š.", "Pavli", "Ilča", "Poli"]
        elif C.startswith("Solo"):
            ct_possible[C] = ["Kepo", "Kuba-Š.", "Janča", "Pavli"]
        elif C.startswith("Blues"):
            ct_possible[C] = ["Tom-K.", "Ilča"]
        elif C.startswith("SlowBal"):
            ct_possible[C] = ["Pavli", "Jarin"]
        elif C.startswith("Teachers Training"):
            ct_possible[C] = ["Pavli", "Kuba-Š."]
        elif C.startswith("Shag/Balboa Open Training"):
            ct_possible[C] = ["Standa"]
        elif C.startswith("PJ Group"):
            ct_possible[C] = ["Kepo", "Janča"]
        else:
            warn(f"No initial set of teachers for course {C}")
        ct_possible[C] += FAKE_TEACHERS

for T in input_data:
    debug(f"Teacher {T}")
    data = input_data[T]
    n_max = data["ncourses_max"]
    t_util_max[T] = n_max
    if n_max > 0:
        t_util_ideal[T] = data["ncourses_ideal"]
        courses_teach = data["courses_teach"]
        courses_pref = {}
        for (Cgen, v) in courses_teach.items():
            for Cspec in courses_regular + courses_solo:
                if Cspec.startswith(Cgen):
                    courses_pref[Cspec] = v
                    if v == 0:
                        # HARD preference
                        if T in ct_possible[Cspec]:
                            ct_possible[Cspec].remove(T)
                            assert(T not in ct_possible[Cspec])
                    elif v <= 3:
                        pass
                    else:
                        error(f"Unexpected course preference value: teacher {T} course {Cgen} value {v}")
        tc_pref[T] = courses_pref
        for d in data["teach_not_together"]:
            tt_not_together.append((t, d))
    ts_pref[T] = data["slots"]
    assert(len(ts_pref[T]) == len(slots))
    # attendance
    #TODO

#pprint(ct_possible)

# course C must not take place in room R
# TODO improve - some of these actualy fake course-venues constraints
cr_not = {}
# there is no reception in Mosilana, so we want LH1 to take place in Koliste
cr_not["LH 1 - Beginners /1"] = "big"
cr_not["LH 1 - Beginners /2"] = "big"
cr_not["LH 1 - Beginners /3"] = "big"
cr_not["Teachers Training"] = "big" # must not be in mosilana
cr_not["Lindy/Charleston Open Training"] = "big" # must not be in mosilana
cr_not["Blues/Slow Open Training"] = "big" # must not be in mosilana

# course C must take place in room R
# PJ in Mosilana
cr_strict = {}
cr_strict["PJ Group /1"] = "big"
cr_strict["PJ Group /2"] = "big"
cr_strict["PJ Group /3"] = "big"

# teacher T must teach courses Cs
tc_strict = {}
#tc_strict["Kuba-Š."] = ["LH 2 - Party Moves", "LH 5", "Teachers Training"]
#tc_strict["Tom-K."] = ["Blues"]
#tc_strict["Jarin"] = ["SlowBal", "Lindy 45"]
#tc_strict["Kepo"] = ["Solo", "PJ Group /1", "PJ Group /2", "PJ Group /3"]
#tc_strict["Janča"] = ["PJ Group /1", "PJ Group /2", "PJ Group /3"]
#tc_strict["Pavli"] = ["SlowBal"]
#tc_strict["Ilča"] = ["Blues", "LH 5"]
#tc_strict["Ivča"] = ["Lindy 45"]
#tc_strict["Míša-L."] = ["LH 2 - Party Moves"]
#tc_strict["Radek-Š."] = ["Solo 45", "LH 4 - TODO /1"]
#tc_strict["Pavla-Š."] = ["Solo 45", "LH 4 - TODO /1"]
#tc_strict["Terka"] = ["Collegiate Shag 2"]
#tc_strict["Míša-Z."] = ["Collegiate Shag 1"]
#tc_strict["Standa"] = ["Shag/Balboa Open Training"]
#tc_strict["Peťa"] = ["Balboa Intermediate"]

# teacher T wants to teach with community teacher
#t_withnew = ["Janča"]

# course Cx must happen on different day and at different time than Cy (and Cz)
courses_different = [
    ["LH 1 - Beginners /1", "LH 1 - Beginners /2", "LH 1 - Beginners /3"],
    #["LH 1 - Beginners /1", "LH 1 - Beginners /2"],
    ["LH 2.5 - Swingout /1", "LH 2.5 - Swingout /2"],
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
    #["Balboa Intermediate", "Shag/Balboa Open Training"],
    #["Balboa Beginners", "Balboa Teachers Training"],
    #["Balboa Intermediate", "Balboa Teachers Training"],
    ["Balboa Beginners", "Balboa Intermediate", "Balboa Teachers Training"],
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

if False:
    # unspecified teachers teach arbitrary number of courses
    for (T, n) in t_util_max.items():
        model.Add(sum(tc[(Teachers[T],c)] for c in range(len(courses))) <= n)
else:
    # unspecified teachers teach no courses
    for T in teachers:
        if T not in FAKE_TEACHERS:
            debug(f"Teacher max: {T} {t_util_max.get(T,-1)}")
            model.Add(sum(tc[(Teachers[T],c)] for c in range(len(courses))) <= t_util_max.get(T, 0))

# community teachers that must teach
for T in ["Zuzka", "Vojta-N.", "Míša-L.", "Kuba-B."]:
    if t_util_max.get(T, 0) >= 1:
        model.Add(sum(tc[(Teachers[T],c)] for c in range(len(courses))) >= 1)
    else:
        warn(f"community teacher {T} should teach, but has not utilization preferences")

if tc_strict:
    debug("strict assignments present")
    strict_assignments = []
    for (T, Cs) in tc_strict.items():
        t = Teachers[T]
        for C in Cs:
            c = Courses[C]
            strict_assignments.append(tc[(t,c)])
    model.AddBoolAnd(strict_assignments)

teachers_all = set(range(len(teachers)))
for (C, Ts) in ct_possible.items():
    c = Courses[C]
    teachers_can = []
    for T in Ts:
        t = Teachers[T]
        teachers_can.append(t)
    teachers_not = teachers_all - set(teachers_can)
    # no other teacher can teach C
    model.Add(sum(tc[(t,c)] for t in teachers_not) == 0)

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
#td_pref = {}
#td_pref[("Tom-S.", "Monday")] = 0
#td_pref[("Tom-S.", "Tuesday")] = 3
#td_pref[("Tom-K.", "Tuesday")] = 0
#td_pref[("Tom-K.", "Wednesday")] = 3
#td_pref[("Tom-K.", "Thursday")] = 0
#td_pref[("Maťo", "Tuesday")] = 3
#td_pref[("Maťo", "Wednesday")] = 3
#td_pref[("Michal", "Monday")] = 0
#td_pref[("Radek-Š.", "Monday")] = 0
#td_pref[("Radek-Š.", "Wednesday")] = 0
#td_pref[("Terka", "Thursday")] = 0
#td_pref[("Janča", "Monday")] = 3
#td_pref[("Janča", "Tuesday")] = 3
#td_pref[("Janča", "Wednesday")] = 3
#td_pref[("Ilča", "Tuesday")] = 3
#td_pref[("Ilča", "Wednesday")] = 3
#td_pref[("Ilča", "Thursday")] = 3
#td_pref[("Pavli", "Tuesday")] = 0
#td_pref[("Pavli", "Wednesday")] = 3
#td_pref[("Pavli", "Thursday")] = 0
#td_pref[("Lili", "Tuesday")] = 3
#td_pref[("Lili", "Wednesday")] = 0
#td_pref[("Lili", "Thursday")] = 3
#td_pref[("Zuzka", "Tuesday")] = 0
#td_pref[("Zuzka", "Thursday")] = 3
#td_pref[("Pavla-Š.", "Monday")] = 0
#td_pref[("Pavla-Š.", "Wednesday")] = 0
#td_pref[("Míša-Z.", "Wednesday")] = 0

# teacher T availability at time X (0 - first slot, 1 - second slot, 2 - third slot):
#   0 cannot
#   1 barely
#   2 fine (default)
#   3 great
#ttime_pref = {}
#ttime_pref[("Jarin", 2)] = 1
#ttime_pref[("Peťa", 0)] = 3
#ttime_pref[("Peťa", 2)] = 0
#ttime_pref[("Tom-S.", 0)] = 3
#ttime_pref[("Tom-S.", 1)] = 3
#ttime_pref[("Radek-Š.", 0)] = 0
#ttime_pref[("Lili", 2)] = 1
#ttime_pref[("Mária", 2)] = 0 # TODO
#ttime_pref[("Silvia", 2)] = 0 # TODO
#ttime_pref[("Zuzka", 0)] = 0
#ttime_pref[("Pavla-Š.", 0)] = 0

# strict teacher-slot constraints:
# Standa cannot teach the first Tuesday slot
model.Add(ts[(Teachers["Standa"],3)] == 0)
# Vojta-N. wants to hang out with students, so prefers NOT to teach right before Teachers Training
model.Add(ts[(Teachers["Vojta-N."],10)] == 0)
# Ilča cannot teach on Wednesday evening
model.Add(ts[(Teachers["Ilča"],8)] == 0)
# Kuba "teaches" Teachers Training
#model.Add(ts[(Teachers["Kuba-Š."],11)] == 0)

# strict courses schedule
# Teachers training must be at Thursday evening
model.Add(cs[Courses["Teachers Training"]] == 11)
# nothing else happens in parallel with Teachers Training
model.Add(sum(src[(11,r,c)] for r in range(len(rooms)) for c in range(len(courses))) == 1)
# Balboa Training must be at Wednesday evening
#model.Add(cs[Courses["Balboa Teachers Training"]] == 8)
# Blues Training must not be on Monday
#model.Add(cs[Courses["Blues/Slow Open Training"]] > 2)
# Shag/Balboa open is AFTER Collegiate Shag 2 (combined with courses_same
model.Add(cs[Courses["Collegiate Shag 2"]]+1 == cs[Courses["Shag/Balboa Open Training"]])
# Balboa Teachers Training does not take place in the last evening slot so Poli can attend
c = Courses["Balboa Teachers Training"]
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

# teachers HARD slot preferences
for T in teachers:
    if T in ts_pref: # TODO what about people without preferences?
        for s, v in enumerate(ts_pref[T]):
            if v == 0:
                model.Add(ts[(Teachers[T], s)] == 0)

# strict time preferences
#for (T,t), n in ttime_pref.items():
#    if n == 0: # T cannot teach on day D
#        for d in range(len(days)):
#            model.Add(ts[(Teachers[T], d*len(times)+t)] == 0)

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
if damian and t_util_max.get("Pavli", 0) >= 2 and t_util_max.get("Tom-K.", 0) >= 1:
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
    "utilization": 100, # squared
    "days": 300,
    "split": 300,
    #"daypref_bad": 300,
    #"daypref_slight": 50,
    #"timepref_bad": 300,
    #"timepref_slight": 50,
    "slotpref_bad": 300,
    "slotpref_slight": 50,
    "coursepref_bad": 300,
    "coursepref_slight": 50,
    #"rent": 5000,
    "mosilana": 300,
    "balboa_closed": 100,
    "faketeachers": 100000,
}

penalties = {} # penalties data (model variables)
penalties_analysis = {} # deeper analysis functions for penalties

for (name, coeff) in PENALTIES.items():
    if coeff == 0:
        warn(f"Penalties: skipping '{name}'")
        continue
    if name == "utilization": # TODO
        # teaching should be split evenly
        penalties_utilization = []
        for T in t_util_ideal:
            t = Teachers[T]
            util_ideal = t_util_ideal[T]
            MAX_DIFF = 10
            min_diff = -MAX_DIFF
            max_diff = MAX_DIFF
            util_diff = model.NewIntVar(min_diff, max_diff, "")
            model.Add(util_diff == teach_num[t] - util_ideal)
            util_diff_abs = model.NewIntVar(0, abs(MAX_DIFF), "")
            model.AddAbsEquality(util_diff_abs, util_diff)
            util_diff_abs_sq = model.NewIntVar(0, abs(MAX_DIFF)**2, "")
            model.AddMultiplicationEquality(util_diff_abs_sq, [util_diff_abs, util_diff_abs])
            penalties_utilization.append(util_diff_abs_sq)
        penalties[name] = penalties_utilization
        def analysis(src, tc):
            result = []
            for T in teachers:
                if T in t_util_ideal:
                    t = Teachers[T]
                    util_ideal = t_util_ideal[T]
                    util_real = sum(tc[(t,c)] for c in range(len(courses)))
                    if util_real != util_ideal:
                        debug(f"analysis utilization - {T} wanted {util_ideal}, teaches {util_real}")
                        result.append(f"{T}/{util_real}r-{util_ideal}i")
            return result
        penalties_analysis[name] = analysis
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
#    elif name == "daypref_bad":
#        # day preferences
#        penalties_daypref_bad = []
#        for T in teachers:
#            t = Teachers[T]
#            prefs = []
#            for D in days:
#                prefs.append(td_pref.get((T,D), 2))
#            if set(prefs) - set([0, 2]): # teacher T prefers some days over others
#                if 1 in set(prefs): # some days are bad
#                    days_bad = [d for d in range(len(prefs)) if prefs[d] == 1]
#                    penalties_daypref_bad.append(sum(td[(t,d)] for d in days_bad))
#        penalties[name] = penalties_daypref_bad
#        def analysis(src, tc):
#            result = []
#            for t in range(len(teachers)):
#                cs = []
#                for c in range(len(courses)):
#                    if tc[(t,c)]:
#                        cs.append(c)
#                bad_days = []
#                for d in range(len(days)):
#                    if td_pref.get((teachers[t],days[d]), 2) == 1:
#                        if sum(src[(s,r,c)]  for s in range(d*len(times),(d+1)*len(times)) for r in range(len(rooms)) for c in cs) >= 1:
#                            bad_days.append(d)
#                if bad_days:
#                    result.append(f"{teachers[t]}/{','.join([days[d] for d in bad_days])}")
#            return result
#        penalties_analysis[name] = analysis
#    elif name == "daypref_slight":
#        # day preferences
#        penalties_daypref_slight = []
#        for T in teachers:
#            t = Teachers[T]
#            prefs = []
#            for D in days:
#                prefs.append(td_pref.get((T,D), 2))
#            if set(prefs) - set([0, 2]): # teacher T prefers some days over others
#                if set([2,3]) <= set(prefs):
#                    # days that are slightly less preferred
#                    days_slight_worse = [d for d in range(len(prefs)) if prefs[d] == 2]
#                    penalties_daypref_slight.append(sum(td[(t,d)] for d in days_slight_worse))
#        penalties[name] = penalties_daypref_slight
    elif name == "slotpref_bad":
        # slots preferences
        penalties_slotpref_bad = []
        for T in teachers:
            if T in ts_pref:
                prefs = ts_pref[T]
                if set([1,2]) <= set(prefs) or set([1,3]) <= set(prefs):
                    # teacher T strongly prefers some slots over others
                    slots_bad = [s for s in range(len(slots)) if prefs[s] == 1]
                    penalties_slotpref_bad.append(sum(ts[(Teachers[T],s)] for s in slots_bad))
        penalties[name] = penalties_slotpref_bad
        def analysis(src, tc):
            result = []
            for t in range(len(teachers)):
                T = teachers[t]
                cs = []
                for c in range(len(courses)):
                    if tc[(t,c)]:
                        cs.append(c)
                bad_slots = []
                n = 0
                if T in ts_pref:
                    prefs = ts_pref[T]
                    if set([1,2]) <= set(prefs) or set([1,3]) <= set(prefs):
                        for s in range(len(slots)):
                            if ts_pref[T][s] == 1:
                                if sum(src[(s,r,c)] for r in range(len(rooms)) for c in cs) >= 1:
                                    bad_slots.append(s)
                                    n += 1
                if bad_slots:
                    debug(f"analysis slotpref_bad - teacher {T} courses {cs} bad_slots {bad_slots}")
                    result.append(f"{T}/{n}-{','.join([str(s) for s in bad_slots])}")
            return result
        penalties_analysis[name] = analysis
    elif name == "slotpref_slight":
        # slots preferences
        penalties_slotpref_slight = []
        for T in teachers:
            if T in ts_pref:
                prefs = ts_pref[T]
                if set([2,3]) <= set(prefs):
                    # teacher T slightly prefers some slots over others
                    slots_bad = [s for s in range(len(slots)) if prefs[s] == 2]
                    penalties_slotpref_slight.append(sum(ts[(Teachers[T],s)] for s in slots_bad))
        penalties[name] = penalties_slotpref_slight
        def analysis(src, tc):
            result = []
            for t in range(len(teachers)):
                T = teachers[t]
                cs = []
                for c in range(len(courses)):
                    if tc[(t,c)]:
                        cs.append(c)
                bad_slots = []
                n = 0
                if T in ts_pref:
                    prefs = ts_pref[T]
                    if set([2,3]) <= set(prefs):
                        for s in range(len(slots)):
                            if ts_pref[T][s] == 2:
                                if sum(src[(s,r,c)] for r in range(len(rooms)) for c in cs) >= 1:
                                    bad_slots.append(s)
                                    n += 1
                if bad_slots:
                    debug(f"analysis slotpref_slight - teacher {T} courses {cs} bad_slots {bad_slots}")
                    result.append(f"{T}/{n}-{','.join([str(s) for s in bad_slots])}")
            return result
        penalties_analysis[name] = analysis
    elif name == "coursepref_bad":
        # slots preferences
        penalties_coursepref = []
        for T in teachers:
            if T in tc_pref:
                spv = set(tc_pref[T].values())
                if set([1,2]) <= spv and set([1,3]) <= spv:
                    # teacher T strongly prefers some courses over others
                    courses_bad = [C for C in courses_regular+courses_solo if tc_pref[T].get(C, -1) == 1]
                    penalties_coursepref.append(sum(tc[(Teachers[T],Courses[C])] for C in courses_bad))
        penalties[name] = penalties_coursepref
        def analysis(src, tc):
            result = []
            for t in range(len(teachers)):
                T = teachers[t]
                courses_bad = []
                if T in tc_pref:
                    spv = set(tc_pref[T].values())
                    if set([1,2]) <= spv and set([1,3]) <= spv:
                        # teacher T strongly prefers some courses over others
                        courses_bad = [C for C in courses_regular+courses_solo if tc_pref[T].get(C, -1) == 1 and tc[(t,Courses[C])]]
                if courses_bad:
                    debug(f"analysis coursepref_bad - teacher {T} courses {courses_bad}")
                    result.append(f"{T}/{len(courses_bad)}")
            return result
        penalties_analysis[name] = analysis
    elif name == "coursepref_slight":
        # slots preferences
        penalties_coursepref = []
        for T in teachers:
            if T in tc_pref:
                if set([2,3]) <= set(tc_pref[T].values()):
                    # teacher T strongly prefers some courses over others
                    courses_bad = [C for C in courses_regular+courses_solo if tc_pref[T].get(C, -1) == 2]
                    penalties_coursepref.append(sum(tc[(Teachers[T],Courses[C])] for C in courses_bad))
        penalties[name] = penalties_coursepref
        def analysis(src, tc):
            result = []
            for t in range(len(teachers)):
                T = teachers[t]
                courses_bad = []
                if T in tc_pref:
                    if set([2,3]) <= set(tc_pref[T].values()):
                        # teacher T strongly prefers some courses over others
                        courses_bad = [C for C in courses_regular+courses_solo if tc_pref[T].get(C, -1) == 2 and tc[(t,Courses[C])]]
                if courses_bad:
                    debug(f"analysis coursepref_slight teacher {T} courses {courses_bad}")
                    result.append(f"{T}/{len(courses_bad)}")
            return result
        penalties_analysis[name] = analysis
    elif name == "faketeachers":
        penalties_faketeachers = []
        # fake teachers
        for T in FAKE_TEACHERS:
            if T in teachers:
                penalties_faketeachers.append(sum(tc[(Teachers[T],c)] for c in range(len(courses))))
        penalties[name] = penalties_faketeachers
    elif name == "mosilana": # penalty for not using koliste
        util_koliste = model.NewIntVar(0, 2*len(slots), "") # utilization of Koliste
        model.Add(util_koliste == sum(src[(s,r,c)] for s in range(len(slots)) for r in range(len(rooms)) if rooms_venues[rooms[r]] == "koliste" for c in range(len(courses))))
        free_koliste = model.NewIntVar(0, 2*len(slots), "") # free slots in Koliste
        model.Add(free_koliste == 2*len(slots)-util_koliste-1) # -1 for Teachers Training
        penalties[name] = [free_koliste]
    elif name == "balboa_closed": # penalty if interested people cannot attend Balboa Teachers Training (they teach something else in the same time)
        # Poli is omitted as inactive
        baltrain_people = ["Peťa", "Jarin", "Kuba-Š.", "Maťo", "Ilča", "Pavli", "Ivča"]
        penalties_balboa_closed = []
        for s in range(len(slots)):
            hit = model.NewBoolVar("")
            model.Add(cs[Courses["Balboa Teachers Training"]] == s).OnlyEnforceIf(hit)
            model.Add(cs[Courses["Balboa Teachers Training"]] != s).OnlyEnforceIf(hit.Not())
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
    error("Solution NOT found")

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
