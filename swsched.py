#!/usr/bin/env python3

import sys
from ortools.sat.python import cp_model

days = ["Monday", "Tuesday", "Wednesday", "Thursday"]
times = ["17:30-18:40", "18:45-19:55", "20:00-21:10"]
slots = [ d + " " + t for d in days for t in times ]

rooms = ["big", "small"]

teachers_lead = [
        "David",
        "Tom-S.",
        "Kuba",
        "Peta",
        "Tom-K.",
        "Jarda",
        "Quique",
        "Mato",
        "Martin",
        "Michal",
        "Vojta",
        "Standa",
        "Kolin",
        "Kepo", #
        ]
teachers_follow = [
        "Terka",
        "Janca",
        "Ilca",
        "Pavli",
        "Blaza",
        "Silvia",
        "Ivca",
        "Linda",
        "Maria",
        "Poli", #
	]
teachers = teachers_lead + teachers_follow
Teachers = {}
for (i, t) in enumerate(teachers):
    Teachers[t] = i

courses_open = [
        "Shag/Balboa Open Training",
        "Teachers Training",
        "Blues/Slow Open Training",
        ]
courses_solo = [
        "Solo 1 - Improvisation",
        "Intensive Training",
        "Choreo Atelier - Ladies Edition",
        ]
courses_regular = [
        "LH 1 - Beginners (1)",
        "LH 1 - Beginners (2)",
        "LH 2 - Survival Guide (1)",
        "LH 2 - Survival Guide (2)",
        "LH 2 - Party Moves",
        "LH 3 - Cool Moves & Styling",
        "LH 3 - Musicality",
        "LH 4 - Let the Music Be with You",
        "LH 4 - Lindy Charleston",
        "LH 2.5 - Swing-out (1)",
        "LH 2.5 - Swing-out (2)",
        "LH 5 - Topic-less",
        "Charleston 2",
        "Airsteps 2",
        "Balboa Beginners",
        "Balboa Intermediate",
        "Collegiate Shag 1",
        ]
courses = courses_regular + courses_solo + courses_open
Courses = {}
for (i, c) in enumerate(courses):
    Courses[c] = i

# SPECIFIC HARD CONSTRAINTS

# teacher T can teach maximum N courses
t_max = {}
t_max["Kepo"] = 0
t_max["Poli"] = 0

# course C can be taught only by Ts
teachers_shag = ["Terka", "Linda", "Kepo", "Standa"]
teachers_balboa = ["Peta", "Jarda", "Poli", "Pavli", "Ilca"]
teachers_airsteps = ["Tom-S.", "Janca"]
ct_possible = {}
ct_possible["Collegiate Shag 1"] = teachers_shag
ct_possible["Balboa Beginners"] = teachers_balboa
ct_possible["Balboa Intermediate"] = teachers_balboa
ct_possible["Airsteps 2"] = teachers_airsteps

# teacher T must teach courses Cs
tc_strict = {}
tc_strict["Standa"] = ["Collegiate Shag 1"]

# course C1 should happen right before or right after C2
cc_follow = [
        ("Collegiate Shag 1", "Airsteps 2"),
        ("Balboa Beginners", "Shag/Balboa Open Training"),
        ("Balboa Intermediate", "Shag/Balboa Open Training"),
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
cs = []
# course C takes place in slot S
for c in range(len(courses)):
    cs.append(model.NewIntVar(0, len(slots), ""))

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
        sys.exit(10) # TODO

# SPECIFIC CONSTRAINTS

for (T, n) in t_max.items():
    t = Teachers[T]
    model.Add(sum(tc[(t,c)] for c in range(len(courses))) <= n)

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

# OPTIMIZATION

penalties = [] # penalties to minimize
PENALTY_OVERWORK = 100 # squared
PENALTY_DAYS = 1000 # squared
PENALTY_SPLIT = 500
PENALTY_FOLLOW = 300
penalties_overwork = []
penalties_days = []
penalties_split = []
penalties_follow = []

if PENALTY_OVERWORK > 0:
    # teaching should be split evenly
    teach_slots = 2*len(courses_regular) + len(courses_solo)
    # TODO: some people might explicitly want more
    # disregarding people with t_max set (roughly - subtracting also number of courses from "defaul pool")
    util_avg = (teach_slots - sum(t_max.values())) // ((len(teachers)) - len(t_max)) + 1
    print(f"Maximum desired utilization: {util_avg}")
    for t in range(len(teachers)):
        util_diff = model.NewIntVar(-util_avg, len(slots), "")
        model.Add(util_diff == teach_num[t] - util_avg)
        excess = model.NewIntVar(0, len(slots), "")
        model.AddMaxEquality(excess, [util_diff, 0])
        excess_sq = model.NewIntVar(0, len(slots)**2, "Texcesssq:%i" % t)
        model.AddMultiplicationEquality(excess_sq, [excess, excess])
        penalties_overwork.append(excess_sq)
    penalties.append(sum(penalties_overwork[i] * PENALTY_OVERWORK for i in range(len(penalties_overwork))))

if PENALTY_DAYS > 0:
    for t in range(len(teachers)):
        # nobody should come to studio more days then necessary
        tds = []
        for d in range(len(days)):
            td = model.NewBoolVar("td:t%id%i" % (t,d))
            # td == True iff teacher t teaches some courses on day d
            model.Add(sum(ts[(t,s)] for s in range(d*len(times), (d+1)*len(times))) >= 1).OnlyEnforceIf(td)
            model.Add(sum(ts[(t,s)] for s in range(d*len(times), (d+1)*len(times))) == 0).OnlyEnforceIf(td.Not())
            tds.append(td)
        teaches_days = model.NewIntVar(0, len(days), "TD:%i" % t)
        model.Add(teaches_days == sum(tds))
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
    penalties.append(sum(penalties_days[i] * PENALTY_DAYS for i in range(len(penalties_days))))

if PENALTY_SPLIT > 0:
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
    penalties.append(sum(penalties_split[i] * PENALTY_SPLIT for i in range(len(penalties_split))))

if PENALTY_FOLLOW > 0:
    for C1, C2 in cc_follow:
        c1 = Courses[C1]
        c2 = Courses[C2]
        d1 = model.NewIntVar(0, len(days), "")
        d2 = model.NewIntVar(0, len(days), "")
        model.AddDivisionEquality(d1, cs[c1], len(times))
        model.AddDivisionEquality(d2, cs[c2], len(times))
        sameday = model.NewBoolVar("")
        model.Add(d1 == d2).OnlyEnforceIf(sameday)
        model.Add(d1 != d2).OnlyEnforceIf(sameday.Not())
        slot_diff = model.NewIntVar(-len(slots), len(slots), "")
        abs_slot_diff = model.NewIntVar(0, len(slots), "")
        model.Add(slot_diff == cs[c1] - cs[c2])
        model.AddAbsEquality(abs_slot_diff, slot_diff)
        asd1 = model.NewBoolVar("") # abs_slot_diff == 1
        model.Add(abs_slot_diff == 1).OnlyEnforceIf(asd1)
        model.Add(abs_slot_diff != 1).OnlyEnforceIf(asd1.Not())
        follows = model.NewBoolVar("") # follows
        model.AddBoolAnd([sameday, asd1]).OnlyEnforceIf(follows)
        model.AddBoolOr([sameday.Not(), asd1.Not()]).OnlyEnforceIf(follows.Not())
        penalties_follow.append(follows.Not())
    penalties.append(sum(penalties_follow[i] * PENALTY_FOLLOW for i in range(len(penalties_follow))))

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

for s in range(len(slots)):
    for r in range(len(rooms)):
        for c in range(len(courses)):
            if solver.Value(src[(s,r,c)]):
                print("%s in %s room: %s" % (slots[s],rooms[r],courses[c]))

for c in range(len(courses)):
    for t in range(len(teachers)):
        if solver.Value(tc[(t,c)]):
                print("%s taught by %s" % (courses[c],teachers[t]))
