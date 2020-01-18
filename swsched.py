#!/usr/bin/env pytho3

from ortools.sat.python import cp_model

days = [
        "Monday",
        "Tuesday"
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
        "Tom",
        ]
teachers_follow = [
        "Terka",
        "Janca"
        ]
teachers = [ "nobody" ] + teachers_lead + teachers_follow
Teachers = {}
for (i, t) in enumerate(teachers):
    Teachers[t] = i

courses_solo = [ "Solo Jazz" ]
courses_regular = [
        "LH1",
        "LH5",
        "Airsteps"
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


solver = cp_model.CpSolver()
solver.Solve(model)

for s in range(len(slots)):
    for r in range(len(rooms)):
        for t in range(1, len(teachers)): # do not print nobody's courses
            for c in range(len(courses)):
                if solver.Value(lessons[(s,r,t,c)]):
                    print("%s in %s room, %s teaches %s" % (slots[s],rooms[r],teachers[t],courses[c]))

