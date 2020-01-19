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
        "20:00-21:10"
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
teachers = [ "SOLO", "OPEN" ] + teachers_lead + teachers_follow
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

# on day D at slot S in room R teacher T teaches course C
lessons = {}
for s in range(len(slots)):
    for r in range(len(rooms)):
        for t in range(len(teachers)):
            for c in range(len(courses)):
                lessons[(s,r,t,c)] = model.NewBoolVar("s%ir%it%ic%i" % (s,r,t,c))

# one teacher can teach just one course at any given timeslot (except for SOLO and OPEN)
for t in range(2, len(teachers)):
    for s in range(len(slots)):
        model.Add(sum(lessons[(s,r,t,c)] for r in range(len(rooms)) for c in range(len(courses))) <= 1)

# one course takes place just in one time in one room
for s in range(len(slots)):
    for r in range(len(rooms)):
        # prevent more courses in same time and room
        sum_records = sum(lessons[(s,r,t,c)] for t in range(len(teachers)) for c in range(len(courses)))
        hit = model.NewBoolVar("")
        model.Add(sum_records == 2).OnlyEnforceIf(hit)
        model.Add(sum_records == 0).OnlyEnforceIf(hit.Not())
        # prevent one course from being in multiple times or rooms
        for c in range(len(courses)): # one course does not span more 
            sum_courses = sum(lessons[(s,r,t,c)] for t in range(len(teachers)))
            hit = model.NewBoolVar("")
            model.Add(sum_courses == 2).OnlyEnforceIf(hit)
            model.Add(sum_courses == 0).OnlyEnforceIf(hit.Not())


# every regular course is taught by two teachers and solo course by one teacher
for c in range(len(courses)):
    if courses[c] in courses_regular:
        # one leader must teach
        model.Add(sum(lessons[(s,r,Teachers[T],c)] for s in range(len(slots)) for r in range(len(rooms)) for T in teachers_lead) == 1)
        # one follow must teach
        model.Add(sum(lessons[(s,r,Teachers[T],c)] for s in range(len(slots)) for r in range(len(rooms)) for T in teachers_follow) == 1)
        # SOLO and OPEN must not teach
        model.Add(sum(lessons[(s,r,0,c)] for s in range(len(slots)) for r in range(len(rooms))) == 0)
        model.Add(sum(lessons[(s,r,1,c)] for s in range(len(slots)) for r in range(len(rooms))) == 0)
    elif courses[c] in courses_solo: # solo course
        # one real teacher must teach
        model.Add(sum(lessons[(s,r,t,c)] for s in range(len(slots)) for r in range(len(rooms)) for t in range(2, len(teachers))) == 1)
        # SOLO must teach, OPEN must NOT teach
        model.Add(sum(lessons[(s,r,0,c)] for s in range(len(slots)) for r in range(len(rooms))) == 1)
        model.Add(sum(lessons[(s,r,1,c)] for s in range(len(slots)) for r in range(len(rooms))) == 0)
    elif courses[c] in courses_open:
        # SOLO and OPEN must teach
        model.Add(sum(lessons[(s,r,0,c)] for s in range(len(slots)) for r in range(len(rooms))) == 1)
        model.Add(sum(lessons[(s,r,1,c)] for s in range(len(slots)) for r in range(len(rooms))) == 1)
    else:
        sys.exit(10) # TODO proper fail

# OPTIMIZATION

PENALTY_OVERWORK = 100
PENALTY_DAYS = 1000
PENALTY_SPLIT = 500
penalties_overwork = []
penalties_days = []
penalties_split = []
teach_slots = 2*len(courses_regular) + len(courses_solo)
util_avg = teach_slots // (len(teachers)-2) + 1
print(f"Utilization plan average: {util_avg}")
for t in range(2, len(teachers)):
    # number of lessons t teaches
    teaches = model.NewIntVar(0, len(slots), "TT:%i" % t)
    model.Add(teaches == sum(lessons[(s,r,t,c)] for s in range(len(slots)) for r in range(len(rooms)) for c in range(len(courses))))
    # teaching should be split evenly
    util_diff = model.NewIntVar(-util_avg, len(slots), "Tud:%i" % t)
    model.Add(util_diff == teaches - util_avg)
    excess = model.NewIntVar(0, len(slots), "TE:%i" % t)
    model.AddMaxEquality(excess, [util_diff, 0])
    excess_sq = model.NewIntVar(0, len(slots)**2, "TEs:%i" % t)
    model.AddMultiplicationEquality(excess_sq, [excess, excess])
    penalties_overwork.append(excess_sq)
    # nobody should come to studio more days then necessary
    tds = []
    tsplits = []
    for d in range(len(days)):
        td = model.NewBoolVar("td:t%id%i" % (t,d))
        # td == True iff teacher t teaches some coursed on day
        model.Add(sum(lessons[(s,r,t,c)] for s in range(d*len(times), (d+1)*len(times)) for r in range(len(rooms)) for c in range(len(courses))) >= 1).OnlyEnforceIf(td)
        model.Add(sum(lessons[(s,r,t,c)] for s in range(d*len(times), (d+1)*len(times)) for r in range(len(rooms)) for c in range(len(courses))) == 0).OnlyEnforceIf(td.Not())
        tds.append(td)
        # tsplit == True iff teacher t teaches just the first and the last course in day d
        tsubsplits = []
        for i in range(len(times)):
            tsubsplit = model.NewBoolVar("tsubsplit:t%id%ii%i" % (t,d,i))
            model.Add(sum(lessons[(s,r,t,c)] for s in [d*len(times)+i] for r in range(len(rooms)) for c in range(len(courses))) == 1).OnlyEnforceIf(tsubsplit)
            model.Add(sum(lessons[(s,r,t,c)] for s in [d*len(times)+i] for r in range(len(rooms)) for c in range(len(courses))) == 0).OnlyEnforceIf(tsubsplit.Not())
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
        for t in range(1, len(teachers)): # do not print SOLO's courses
        #for t in range(len(teachers)):
            for c in range(len(courses)):
                if solver.Value(lessons[(s,r,t,c)]):
                    print(f"{slots[s]} in {rooms[r]} room, {teachers[t]} teaches {courses[c]}")

