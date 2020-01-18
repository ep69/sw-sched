#!/usr/bin/env pytho3

from ortools.sat.python import cp_model

days = [
        "Monday",
        "Tuesday"
        ]

slots = [
        "17:30-18:40",
        "18:45-19:55",
        "20:00-21:10"
        ]

rooms = [
        "big",
        "small"
        ]

teachers = [
        "nobody",
        "David",
        "Terka",
        "Tom",
        "Janca"
        ]
Teachers = {}
for (i, t) in enumerate(teachers):
    Teachers[t] = i

solo_courses = [ "Solo Jazz" ]
normal_courses = [
        "LH1",
        "LH5",
        "Airsteps"
        ]
courses = normal_courses + solo_courses
Courses = {}
for (i, c) in enumerate(courses):
    Courses[c] = i



model = cp_model.CpModel()

# on day D at slot S in room R teacher T teaches course C
lessons = {}
for d in range(len(days)):
    for s in range(len(slots)):
        for r in range(len(rooms)):
            for t in range(len(teachers)):
                for c in range(len(courses)):
                    lessons[(d,s,r,t,c)] = model.NewBoolVar("d%is%ir%it%ic%i" % (d,s,r,t,c))

# one teacher can teach just one course at any given timeslot (except for 'nobody')
for t in range(1,len(teachers)):
    for d in range(len(days)):
        for s in range(len(slots)):
            model.Add(sum(lessons[(d,s,r,t,c)] for r in range(len(rooms)) for c in range(len(courses))) <= 1)

# one course takes place just in one time in one room
for d in range(len(days)):
    for s in range(len(slots)):
        for r in range(len(rooms)):
            # prevent more courses in same time and room
            sum_records = sum(lessons[(d,s,r,t,c)] for t in range(len(teachers)) for c in range(len(courses)))
            hit = model.NewBoolVar("")
            model.Add(sum_records == 2).OnlyEnforceIf(hit)
            model.Add(sum_records == 0).OnlyEnforceIf(hit.Not())
            # prevent one course from being in multiple times or rooms
            for c in range(len(courses)): # one course does not span more 
                sum_courses = sum(lessons[(d,s,r,t,c)] for t in range(len(teachers)))
                hit = model.NewBoolVar("")
                model.Add(sum_courses == 2).OnlyEnforceIf(hit)
                model.Add(sum_courses == 0).OnlyEnforceIf(hit.Not())


# every regular course is taught by two teachers and solo course by one teacher
for c in range(len(courses)):
    model.Add(sum(lessons[(d,s,r,t,c)] for d in range(len(days)) for s in range(len(slots)) for r in range(len(rooms)) for t in range(len(teachers))) == 2)
    if courses[c] in normal_courses:
        # 'nobody' must not teach
        model.Add(sum(lessons[(d,s,r,0,c)] for d in range(len(days)) for s in range(len(slots)) for r in range(len(rooms))) == 0)
    else: # solo course
        # 'nobody' must teach
        model.Add(sum(lessons[(d,s,r,0,c)] for d in range(len(days)) for s in range(len(slots)) for r in range(len(rooms))) == 1)

#for d in range(len(days)):
#    for s in range(len(slots)):
#        for r in range(len(rooms)):
#            # in one spacetime (day+slot+room) there is max. one course
#            #model.Add(sum(c
#            #model.Add(sum(lessons[(d,s,r,t,c)] for t in range(len(teachers)) for c in range(len(courses))) <= 2)
#            # every regular course is teached by exactly two teachers
#            model.Add(sum(lessons[(d,s,r,t,Courses[c])] for t in range(len(teachers)) for c in normal_courses) == 2)
#            # every solo course is teached by exactly one teacher
#            model.Add(sum(lessons[(d,s,r,t,Courses[c])] for t in range(len(teachers)) for c in solo_courses) == 1)
#            # teacher can be in one momen in one room teaching max. one course
#            for t in range(len(teachers)):
#                model.Add(sum(lessons[(d,s,r,t,c)] for c in range(len(courses))) <= 1)

#for c in range(len(courses)):
#    if courses[c] in solo_courses:
#        model.Add(sum(lessons[(d,s,r,t,c)] for d in range(len(days)) for s in range(len(slots)) for r in range(len(rooms)) for t in range(len(teachers))) <= 2)
#    else:
#        model.Add(sum(lessons[(d,s,r,t,c)] for d in range(len(days)) for s in range(len(slots)) for r in range(len(rooms)) for t in range(len(teachers))) <= 1)

solver = cp_model.CpSolver()
solver.Solve(model)

for d in range(len(days)):
    for s in range(len(slots)):
        for r in range(len(rooms)):
            for t in range(len(teachers)):
                for c in range(len(courses)):
                    if solver.Value(lessons[(d,s,r,t,c)]):
                        print("On %s at %s in %s room, %s teaches %s" % (days[d],slots[s],rooms[r],teachers[t],courses[c]))

