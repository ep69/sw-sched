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
teachers = [ "nobody" ] + teachers_lead + teachers_follow
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
courses = courses_regular + courses_solo
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

# one teacher can teach just one course at any given timeslot (except for 'nobody')
for t in range(1, len(teachers)):
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
        # 'nobody' must not teach
        model.Add(sum(lessons[(s,r,0,c)] for s in range(len(slots)) for r in range(len(rooms))) == 0)
    else: # solo course
        # one real teacher must teach
        model.Add(sum(lessons[(s,r,t,c)] for s in range(len(slots)) for r in range(len(rooms)) for t in range(1, len(teachers))) == 1)
        # 'nobody' must teach
        model.Add(sum(lessons[(s,r,0,c)] for s in range(len(slots)) for r in range(len(rooms))) == 1)

print(model.ModelStats())
print()


solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = 20.0
status = solver.SearchForAllSolutions(model, cp_model.ObjectiveSolutionPrinter())
statusname = solver.StatusName(status)
print(f"Solving finished in {solver.WallTime()} seconds with status {status} - {statusname}")
if statusname not in ["FEASIBLE", "OPTIMAL"]:
    print("Solution NOT found")
    sys.exit(1)

print()
print("SOLUTION:")
for s in range(len(slots)):
    for r in range(len(rooms)):
        for t in range(1, len(teachers)): # do not print nobody's courses
            for c in range(len(courses)):
                if solver.Value(lessons[(s,r,t,c)]):
                    print(f"{slots[s]} in {rooms[r]} room, {teachers[t]} teaches {courses[c]}")

