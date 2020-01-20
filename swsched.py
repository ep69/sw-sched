#!/usr/bin/env python3

import sys
from ortools.sat.python import cp_model

days = [
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        ]

times = [
        "17:30-18:40",
        "18:45-19:55",
        "20:00-21:10",
        ]

slots = [ d + " " + t for d in days for t in times ]

rooms = [
        "big",
        "small"
        ]

teachers_lead = [
        "David",
        "Tom S.",
        "Kuba",
        "Peta",
        "Tom K.",
        "Jarda",
        "Quique",
        "Mato",
        "Martin",
        "Michal",
        "Vojta",
        "Standa",
        "Kolin",
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

model = cp_model.CpModel()

# Variables

# course C takes place in slot S in room R
csr = {}
for s in range(len(slots)):
    for r in range(len(rooms)):
        for c in range(len(courses)):
            csr[(s,r,c)] = model.NewBoolVar("CSR:s%ir%ic%i" % (s,r,c))
# course C is taught by teacher T
ct = {}
for c in range(len(courses)):
    for t in range(len(teachers)):
        ct[(t,c)] = model.NewBoolVar("CT:t%ic%i" % (t,c))
# teacher T teaches in slot S course C
cts = {}
for s in range(len(slots)):
    for t in range(len(teachers)):
        for c in range(len(courses)):
            cts[(t,s,c)] = model.NewBoolVar("TS:t%is%ic%i" % (t,s,c))
# teacher T teaches in slot S
st = {}
for s in range(len(slots)):
    for t in range(len(teachers)):
        st[(t,s)] = model.NewBoolVar("TS:t%is%i" % (t,s))

# teacher T teaches in slot S course C iff course C takes place at slot S and is taught by teacher T
# inferring CTS info
for s in range(len(slots)):
    for c in range(len(courses)):
        cs = model.NewBoolVar("") # course C is at slot S
        model.Add(sum(csr[(s,r,c)] for r in range(len(rooms))) == 1).OnlyEnforceIf(cs)
        model.Add(sum(csr[(s,r,c)] for r in range(len(rooms))) == 0).OnlyEnforceIf(cs.Not())
        for t in range(len(teachers)):
            model.AddBoolAnd([cs, ct[(t,c)]]).OnlyEnforceIf(cts[(t,s,c)])
            model.AddBoolOr([cs.Not(), ct[(t,c)].Not()]).OnlyEnforceIf(cts[(t,s,c)].Not())
# inferring TS info
for s in range(len(slots)):
    for t in range(len(teachers)):
        model.Add(sum(cts[(t,s,c)] for c in range(len(courses))) == 1).OnlyEnforceIf(st[(t,s)])
        model.Add(sum(cts[(t,s,c)] for c in range(len(courses))) == 0).OnlyEnforceIf(st[(t,s)].Not())

# prevent teachers from teaching in two rooms in the same time
for t in range(len(teachers)):
    for s in range(len(slots)):
        model.Add(sum(cts[(t,s,c)] for c in range(len(courses))) <= 1)

# one course takes place at one time in one room
for c in range(len(courses)):
    model.Add(sum(csr[(s,r,c)] for s in range(len(slots)) for r in range(len(rooms))) == 1)

# at one time in one room, there is maximum one course
for s in range(len(slots)):
    for r in range(len(rooms)):
        model.Add(sum(csr[(s,r,c)] for c in range(len(courses))) <= 1)

# every regular course is taught by two teachers and solo course by one teacher
for c in range(len(courses)):
    if courses[c] in courses_regular:
        model.Add(sum(ct[(Teachers[T],c)] for T in teachers_lead) == 1)
        model.Add(sum(ct[(Teachers[T],c)] for T in teachers_follow) == 1)
    elif courses[c] in courses_solo:
        model.Add(sum(ct[(Teachers[T],c)] for T in teachers) == 1)
    elif courses[c] in courses_open:
        model.Add(sum(ct[(Teachers[T],c)] for T in teachers) == 0)
    else:
        sys.exit(10) # TODO

# OPTIMIZATION

PENALTY_OVERWORK = 100
PENALTY_DAYS = 1000
PENALTY_SPLIT = 500
penalties_overwork = []
penalties_days = []
penalties_split = []
teach_slots = 2*len(courses_regular) + len(courses_solo)
util_avg = teach_slots // (len(teachers)) + 1
print(f"Utilization plan average: {util_avg}")
for t in range(len(teachers)):
    # number of lessons t teaches
    teaches = model.NewIntVar(0, len(slots), "Tteaches:%i" % t)
    model.Add(teaches == sum(ct[(t,c)] for c in range(len(courses))))
    # teaching should be split evenly
    util_diff = model.NewIntVar(-util_avg, len(slots), "Tud:%i" % t)
    model.Add(util_diff == teaches - util_avg)
    excess = model.NewIntVar(0, len(slots), "Texcess:%i" % t)
    model.AddMaxEquality(excess, [util_diff, 0])
    excess_sq = model.NewIntVar(0, len(slots)**2, "Texcesssq:%i" % t)
    model.AddMultiplicationEquality(excess_sq, [excess, excess])
    penalties_overwork.append(excess_sq)
    # nobody should come to studio more days then necessary
    tds = []
    tsplits = []
    for d in range(len(days)):
        td = model.NewBoolVar("td:t%id%i" % (t,d))
        # td == True iff teacher t teaches some courses on day d
        model.Add(sum(st[(t,s)] for s in range(d*len(times), (d+1)*len(times))) >= 1).OnlyEnforceIf(td)
        model.Add(sum(st[(t,s)] for s in range(d*len(times), (d+1)*len(times))) == 0).OnlyEnforceIf(td.Not())
        tds.append(td)
        # tsplit == True iff teacher t teaches just the first and the last course in day d
        tsubsplits = []
        for i in range(len(times)):
            tsubsplit = model.NewBoolVar("tsubsplit:t%id%ii%i" % (t,d,i))
            model.Add(sum(st[(t,s)] for s in [d*len(times)+i]) == 1).OnlyEnforceIf(tsubsplit)
            model.Add(sum(st[(t,s)] for s in [d*len(times)+i]) == 0).OnlyEnforceIf(tsubsplit.Not())
            tsubsplits.append(tsubsplit)
        tsplit = model.NewBoolVar("tsplit:t%id%i" % (t,d))
        model.AddBoolAnd([tsubsplits[0], tsubsplits[1].Not(), tsubsplits[2]]).OnlyEnforceIf(tsplit)
        model.AddBoolOr([tsubsplits[0].Not(), tsubsplits[1], tsubsplits[2].Not()]).OnlyEnforceIf(tsplit.Not())
        tsplits.append(tsplit)
    teaches_days = model.NewIntVar(0, len(days), "TD:%i" % t)
    model.Add(teaches_days == sum(tds))
    teaches_minus_1 = model.NewIntVar(0, len(days), "Tm1:%i" % t)
    teaches_some = model.NewBoolVar("Ts:%i" % t)
    model.Add(teaches >= 1).OnlyEnforceIf(teaches_some)
    model.Add(teaches == 0).OnlyEnforceIf(teaches_some.Not())
    model.Add(teaches_minus_1 == teaches - 1).OnlyEnforceIf(teaches_some)
    model.Add(teaches_minus_1 == 0).OnlyEnforceIf(teaches_some.Not())
    should_teach_days = model.NewIntVar(0, len(days), "TDs:%i" % t)
    model.AddDivisionEquality(should_teach_days, teaches_minus_1, len(times)) # -1 to compensate rounding down
    days_extra = model.NewIntVar(0, len(days), "Tdd:%i" % t)
    model.Add(days_extra == teaches_days - should_teach_days - 1).OnlyEnforceIf(teaches_some) # -1 to compensate rounding down
    model.Add(days_extra == 0).OnlyEnforceIf(teaches_some.Not())
    days_extra_sq = model.NewIntVar(0, len(days)**2, "Tdds:%i" % t)
    model.AddMultiplicationEquality(days_extra_sq, [days_extra, days_extra])
    penalties_days.append(days_extra_sq)
    days_split = model.NewIntVar(0, len(days), "TDsplit:%i" % t)
    model.Add(days_split == sum(tsplits))
    penalties_split.append(days_split)


model.Minimize(
        sum(penalties_overwork[i] * PENALTY_OVERWORK for i in range(len(penalties_overwork)))
        + sum(penalties_days[i] * PENALTY_DAYS for i in range(len(penalties_days)))
        + sum(penalties_split[i] * PENALTY_SPLIT for i in range(len(penalties_split)))
        )


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
            if solver.Value(csr[(s,r,c)]):
                print("%s in %s room: %s" % (slots[s],rooms[r],courses[c]))

for t in range(len(teachers)):
    for c in range(len(courses)):
        if solver.Value(ct[(t,c)]):
                print("%s taught by %s" % (courses[c],teachers[t]))
