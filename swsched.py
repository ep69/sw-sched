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
print(slots)

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
teachers = teachers_lead + teachers_follow
Teachers = {}
for (i, t) in enumerate(teachers):
    Teachers[t] = i

courses_regular = [
        "LH1",
        "LH5",
        "Airsteps"
        ]
courses_solo = [
        "Solo Jazz"
        ]
courses = courses_regular + courses_solo
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
            csr[(s,r,c)] = model.NewBoolVar("CS:s%ir%ic%i" % (s,r,c))
# course C is taught by teacher T
ct = {}
for c in range(len(courses)):
    for t in range(len(teachers)):
        ct[(t,c)] = model.NewBoolVar("CT:t%ic%i" % (t,c))

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
    else:
        model.Add(sum(ct[(Teachers[T],c)] for T in teachers) == 1)

# one teacher can teach just one course at any given timeslot
#for t in range(len(teachers)):
#    for s in range(len(slots)):
#        model.Add(sum(csr[(s,r,c)] * ct[(t,c)] for r in range(len(rooms)) for c in range(len(courses))) <= 1)
# TODO
teaches_slot = {}
for t in range(len(teachers)):
    for s in range(len(slots)):
        ts = model.NewBoolVar("")
        teaches_slot[(t,s)] = model.NewBoolVar("TS:t%is%i" % (t,s))
        model.AddBoolAnd(csr[(s,r,c)] and ct[(t,c)] for r in range(len(rooms)) for c in range(len(courses))).OnlyEnforceIf(ts)
        model.Add(sum(csr[(s,r,c)] and ct[(t,c)] for r in range(len(rooms)) for c in range(len(courses))) == 1).OnlyEnforceIf(ts)
        model.Add(sum(csr[(s,r,c)] and ct[(t,c)] for r in range(len(rooms)) for c in range(len(courses))) != 1).OnlyEnforceIf(ts.Not())
        teaches_slot[t,s] = ts
for t in range(len(teachers)):
    model.Add(sum(teaches_slot[t,s] for s in range(len(slots))) <= 1)

solver = cp_model.CpSolver()
solver.Solve(model)

for s in range(len(slots)):
    for r in range(len(rooms)):
        for c in range(len(courses)):
            if solver.Value(csr[(s,r,c)]):
                print("%s in %s room: %s" % (slots[s],rooms[r],courses[c]))

for t in range(len(teachers)):
    for c in range(len(courses)):
        if solver.Value(ct[(t,c)]):
                print("%s taught by %s" % (courses[c],teachers[t]))
