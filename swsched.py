#!/usr/bin/env python3

import sys
import csv
from ortools.sat.python import cp_model
from pprint import pprint

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

class Input:
    def init_constants(self):
        self.days = ["Monday", "Tuesday", "Wednesday", "Thursday"]
        self.Days = {}
        for i, D in enumerate(self.days):
            self.Days[D] = i

        self.times = ["17:30-18:40", "18:45-19:55", "20:00-21:10"]

        self.slots = [ d + " " + t for d in self.days for t in self.times ]

        self.rooms = [
            "big",
            #"small",
            "koli-3",
            "koli-4",
        ]
        self.Rooms = {}
        for i, R in enumerate(self.rooms):
            self.Rooms[R] = i

        self.venues = ["mosilana", "koliste"]
        self.Venues = {}
        for i, V in enumerate(self.venues):
            self.Venues[V] = i

        # name, role, community
        self.TEACHERS = [
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
            ("LEAD-1", "lead", False), # TODO
            ("LEAD-2", "lead", False), # TODO
            ("LEAD-3", "lead", False), # TODO
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
            ("FOLL-1", "follow", False), # TODO
            ("FOLL-2", "follow", False), # TODO
            ("FOLL-3", "follow", False), # TODO
            ]
        self.FAKE_TEACHERS = ["LEAD-1", "LEAD-2", "LEAD-3", "FOLL-1", "FOLL-2", "FOLL-3"]

        self.rooms_venues = {
            #"small": "mosilana",
            "big": "mosilana",
            "koli-3": "koliste",
            "koli-4": "koliste",
            }

        self.courses_open = [
            "Lindy/Charleston Open Training",
            "Blues/Slow Open Training",
            "Balboa Teachers Training",
            ]
        self.courses_solo = [
            "Solo",
            "Teachers Training",
            "Shag/Balboa Open Training",
            ]
        self.courses_regular = [
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


        self.teachers = [t[0] for t in self.TEACHERS]
        self.teachers_lead = [t[0] for t in self.TEACHERS if t[1] == "lead"]
        self.teachers_follow = [t[0] for t in self.TEACHERS if t[1] == "follow"]
        assert(set(self.teachers) == set(self.teachers_lead + self.teachers_follow))
        assert(len(set(self.teachers_lead) & set(self.teachers_follow)) == 0)
        self.teachers_core = [t[0] for t in self.TEACHERS if not t[2]]
        self.teachers_community = [t[0] for t in self.TEACHERS if t[2]]
        debug(f"Core teachers: {self.teachers_core}")
        debug(f"Community teachers: {self.teachers_community}")
        assert(set(self.teachers) == set(self.teachers_core + self.teachers_community))
        assert(len(set(self.teachers_core) & set(self.teachers_community)) == 0)

        self.Teachers = {}
        for (i, t) in enumerate(self.teachers):
            self.Teachers[t] = i

        self.people = self.teachers

        self.courses = self.courses_regular + self.courses_solo + self.courses_open
        self.Courses = {}
        for (i, c) in enumerate(self.courses):
            self.Courses[c] = i

        self.TEACHER_NAMES = {
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
            "Kuba-Š.": "Kuba Šůstek",
        }

        self.COURSES_IGNORE = [
            #"Balboa Intermediate",
            "LH 1 - English",
            "",
        ]


    def translate_teacher_name(self, name):
        name = name.strip()
        if name in self.teachers:
            return name
        name_nospace = name.replace(" ", "-")
        if name_nospace in self.teachers:
            return name_nospace
        for k in self.TEACHER_NAMES:
            if name in self.TEACHER_NAMES[k]:
                return k
        error(f"Unknown teacher name {name}")

    def check_course(self, course):
        for c in self.courses:
            if c.startswith(course):
                return
        error(f"Unknown course: '{course}'")

    def read_input(self, filename="input.csv"):
        result = {}
        with open(filename, mode="r") as f:
            reader = csv.DictReader(f)
            n = 0
            input_courses = [] # courses
            for row in reader:
                n += 1
                if n == 1:
                    # check courses when handling the first row
                    columns = list(row.keys())
                    for col in columns:
                        if col.startswith("What courses would you like to teach?"):
                            course = col.split("[")[1].split("]")[0]
                            if course in self.COURSES_IGNORE:
                                continue
                            self.check_course(course)
                            # problematic: Balboa Beginners 2
                            input_courses.append(course)
                # handle the input data
                name = self.translate_teacher_name(row["Who are you?"])
                debug(f"Reading: name {name}")
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
                for c in input_courses:
                    courses_teach[c] = int(row[f"What courses would you like to teach? [{c}]"][0])
                d["courses_teach"] = courses_teach
                d["courses_attend"] = row["What courses and trainings would you like to attend?"].split(";")
                for c in d["courses_attend"]:
                    if c in self.COURSES_IGNORE:
                        d["courses_attend"].remove(c)
                for c in d["courses_attend"]:
                    self.check_course(c)
                teach_together = row["Who would you like to teach with?"]
                if teach_together == "":
                    teach_together = []
                if teach_together:
                    if name == "Janča":
                        d["teach_together"] = ["Kepo", "Maťo", "Kuba-Š.", "Jarin"]
                        # TODO what about teaching as lead?
                    elif name == "Jarin":
                        d["teach_together"] = ["Ilča"]
                    elif name == "Ilča":
                        d["teach_together"] = ["Kuba-Š.", "Jarin", "Vojta-S."]
                    elif name == "Kuba-B.":
                        d["teach_together"] = ["Janča", "Ilča", "Lili"]
                    elif name == "Kuba-Š.":
                        d["teach_together"] = ["Ilča"] # TODO community teachers
                    elif name == "Vojta-S.":
                        d["teach_together"] = ["Ilča"]
                    elif name in ["Maťo", "Ivča", "Blaženka"]: # "ignore list"
                        d["teach_together"] = []
                    else:
                        error(f"Unhandled teach_together preference {name}: {teach_together}")
                else:
                    d["teach_together"] = []

                d["teach_not_together"] = [self.translate_teacher_name(x) for x in row["Are there any people you cannot teach with?"].split() if x not in ["-", "No", "není"]]
                result[name] = d
        debug(f"Number of lines: {n}")
        #print(f"Column names: {columns}")
        return result

    def init_form(self):
        self.input_data = self.read_input()
        for t in self.input_data.keys():
            if t not in self.teachers:
                error(f"teacher name {t} needs translation")
        pprint(self.input_data)

    # SPECIFIC HARD CONSTRAINTS
    def init_rest(self):
        # HARD teacher T can teach maximum N courses
        self.t_util_max = {}
        # teacher T wants to teach N courses
        self.t_util_ideal = {}
        # HARD teacher T1 must not teach a course with teacher T2
        self.tt_not_together = []
        # HARD teacher T cannot do anything in slots Ss
        self.ts_pref = {}
        # teacher T preference about teaching course C (HARD if 0)
        self.tc_pref = {}

        # course C can be taught only by Ts
        self.ct_possible = {}
        for C in self.courses:
            if C not in self.courses_open:
                if C.startswith(("LH 1 ", "LH 2 ", "LH 2.5 ", "LH 3 ")):
                    #ct_possible[C] = list(set(teachers) - set(["Standa", "Míša-Z."]))
                    self.ct_possible[C] = list(set(self.teachers) - set(["Míša-Z."]))
                elif C.startswith("LH 4"):
                    self.ct_possible[C] = list(set(self.teachers_core) - set(["Peťa", "Standa"]))
                elif C.startswith("LH 5"):
                    self.ct_possible[C] = ["Kuba-Š.", "Ilča"]
                elif C.startswith("Airsteps"):
                    self.ct_possible[C] = ["Tom-S.", "Janča"]
                elif C.startswith("Collegiate Shag"):
                    self.ct_possible[C] = ["Terka", "Lili", "Standa", "Míša-Z."]
                elif C.startswith("Saint Louis Shag"):
                    self.ct_possible[C] = ["Terka", "Janča", "Maťo"]
                elif C.startswith("Balboa"):
                    self.ct_possible[C] = ["Peťa", "Jarin", "Kuba-Š.", "Pavli", "Ilča", "Poli"]
                elif C.startswith("Balboa"):
                    self.ct_possible[C] = ["Peťa", "Jarin", "Kuba-Š.", "Pavli", "Ilča", "Poli"]
                elif C.startswith("Solo"):
                    self.ct_possible[C] = ["Kepo", "Kuba-Š.", "Janča", "Pavli"]
                elif C.startswith("Blues"):
                    self.ct_possible[C] = ["Tom-K.", "Ilča"]
                elif C.startswith("SlowBal"):
                    self.ct_possible[C] = ["Pavli", "Jarin"]
                elif C.startswith("Teachers Training"):
                    self.ct_possible[C] = ["Pavli", "Kuba-Š."]
                elif C.startswith("Shag/Balboa Open Training"):
                    self.ct_possible[C] = ["Standa"]
                elif C.startswith("PJ Group"):
                    self.ct_possible[C] = ["Kepo", "Janča"]
                else:
                    warn(f"No initial set of teachers for course {C}")
                self.ct_possible[C] += self.FAKE_TEACHERS

        # translate input data to variables understood by the rest of the script
        for T in self.input_data:
            debug(f"Teacher {T}")
            data = self.input_data[T]
            self.t_util_max[T] = data["ncourses_max"]
            if self.t_util_max[T] > 0:
                self.t_util_ideal[T] = data["ncourses_ideal"]
                courses_teach = data["courses_teach"]
                courses_pref = {}
                for (Cgen, v) in courses_teach.items():
                    for Cspec in self.courses_regular + self.courses_solo:
                        if Cspec.startswith(Cgen):
                            courses_pref[Cspec] = v
                            if v == 0:
                                # HARD preference
                                if T in self.ct_possible[Cspec]:
                                    self.ct_possible[Cspec].remove(T)
                                    assert(T not in self.ct_possible[Cspec])
                            elif v <= 3:
                                pass
                            else:
                                error(f"Unexpected course preference value: teacher {T} course {Cgen} value {v}")
                self.tc_pref[T] = courses_pref
                for d in data["teach_not_together"]:
                    self.tt_not_together.append((t, d))
            self.ts_pref[T] = data["slots"]
            assert(len(self.ts_pref[T]) == len(self.slots))
            # attendance done directly through input_data

            # course C must not take place in room R
            # TODO improve - some of these actualy fake course-venues constraints
            self.cr_not = {}
            # there is no reception in Mosilana, so we want LH1 to take place in Koliste
            self.cr_not["LH 1 - Beginners /1"] = "big"
            self.cr_not["LH 1 - Beginners /2"] = "big"
            self.cr_not["LH 1 - Beginners /3"] = "big"
            self.cr_not["Teachers Training"] = "big" # must not be in mosilana
            self.cr_not["Lindy/Charleston Open Training"] = "big" # must not be in mosilana
            self.cr_not["Blues/Slow Open Training"] = "big" # must not be in mosilana

            # course C must take place in room R
            # PJ in Mosilana
            self.cr_strict = {}
            self.cr_strict["PJ Group /1"] = "big"
            self.cr_strict["PJ Group /2"] = "big"
            self.cr_strict["PJ Group /3"] = "big"

            # teacher T must teach courses Cs
            self.tc_strict = {}

            # course Cx must happen on different day and at different time than Cy (and Cz)
            self.courses_different = [
                ["LH 1 - Beginners /1", "LH 1 - Beginners /2", "LH 1 - Beginners /3"],
                #["LH 1 - Beginners /1", "LH 1 - Beginners /2"],
                ["LH 2.5 - Swingout /1", "LH 2.5 - Swingout /2"],
                ]

            # course Cx must happen on different day time than Cy (and Cz)
            self.courses_diffday = [
                #["PJ Group /1", "PJ Group /2"],
                ]

            # course C1, C2, (C3) should happen
            #  * on the same day
            #  * in different times
            #  * following each other
            #  * in the same venue
            self.courses_same = [
                ["Collegiate Shag 2", "Shag/Balboa Open Training"],
                #["Balboa Intermediate", "Shag/Balboa Open Training"],
                #["Balboa Beginners", "Balboa Teachers Training"],
                #["Balboa Intermediate", "Balboa Teachers Training"],
                ["Balboa Beginners", "Balboa Intermediate", "Balboa Teachers Training"],
                ["Blues", "Blues/Slow Open Training"],
                ["PJ Group /1", "PJ Group /3"], # faking two slot class
                ]

I = Input()
I.init_constants()
I.init_form()
I.init_rest()

model = cp_model.CpModel()

# VARIABLES

# course C takes place in slot S in room R
src = {}
for s in range(len(I.slots)):
    for r in range(len(I.rooms)):
        for c in range(len(I.courses)):
            src[(s,r,c)] = model.NewBoolVar("CSR:s%ir%ic%i" % (s,r,c))
# course C is taught by teacher T
tc = {}
for c in range(len(I.courses)):
    for t in range(len(I.teachers)):
        tc[(t,c)] = model.NewBoolVar("CT:t%ic%i" % (t,c))
# teacher T teaches in slot S course C
tsc = {}
for s in range(len(I.slots)):
    for t in range(len(I.teachers)):
        for c in range(len(I.courses)):
            tsc[(t,s,c)] = model.NewBoolVar("TS:t%is%ic%i" % (t,s,c))
# teacher T teaches in slot S
ts = {}
for s in range(len(I.slots)):
    for t in range(len(I.teachers)):
        ts[(t,s)] = model.NewBoolVar("TS:t%is%i" % (t,s))
# person P attends course C
ac = {}
for p in range(len(I.people)):
    for c in range(len(I.courses)):
        ac[(p,c)] = model.NewBoolVar("")
# person P teaches or attends course C
pc = {}
for p in range(len(I.people)):
    for c in range(len(I.courses)):
        pc[(p,c)] = model.NewBoolVar("")
# person P attends or teaches course C in slot S
psc = {}
for p in range(len(I.people)):
    for s in range(len(I.slots)):
        for c in range(len(I.courses)):
            psc[(p,s,c)] = model.NewBoolVar("")
# person P occupied (attends or teaches) in slot S
ps = {}
for s in range(len(I.slots)):
    for p in range(len(I.people)):
        ps[(p,s)] = model.NewBoolVar("PS:p%is%i" % (p,s))
# teacher T teaches on day D
td = {}
for d in range(len(I.days)):
    for t in range(len(I.teachers)):
        td[(t,d)] = model.NewBoolVar("TD:t%id%i" % (t,d))
# person P is occupied (teaches or attends courses) on day D
pd = {}
for d in range(len(I.days)):
    for p in range(len(I.people)):
        pd[(p,d)] = model.NewBoolVar("")
# course C takes place in slot S
cs = []
for c in range(len(I.courses)):
    cs.append(model.NewIntVar(0, len(I.slots)-1, ""))
# room R is in venue V
rv = []
for r in range(len(I.rooms)):
    rv.append(model.NewIntVar(0, len(I.venues)-1, ""))
    model.Add(rv[r] == I.Venues[I.rooms_venues[I.rooms[r]]])
# teacher T teaches in slot S course C in venue V
tscv = {}
for t in range(len(I.teachers)):
    for s in range(len(I.slots)):
        for c in range(len(I.courses)):
            for v in range(len(I.venues)):
                tscv[(t,s,c,v)] = model.NewBoolVar("")

# teacher T teaches in venue V on day D
# TODO do it wrt. attending courses - cannot teach in Koliste, attend in Mosilana, and teach again in Koliste
tdv = {}
for t in range(len(I.teachers)):
    for d in range(len(I.days)):
        for v in range(len(I.venues)):
            tdv[(t,d,v)] = model.NewBoolVar("")

# teacher T teaches course C in slot S iff course C takes place at slot S and is taught by teacher T
# inferring CTS info
for s in range(len(I.slots)):
    for c in range(len(I.courses)):
        hit = model.NewBoolVar("") # course C is at slot S
        model.Add(sum(src[(s,r,c)] for r in range(len(I.rooms))) == 1).OnlyEnforceIf(hit)
        model.Add(sum(src[(s,r,c)] for r in range(len(I.rooms))) == 0).OnlyEnforceIf(hit.Not())
        model.Add(cs[c] == s).OnlyEnforceIf(hit)
        model.Add(cs[c] != s).OnlyEnforceIf(hit.Not())
        for t in range(len(I.teachers)):
            model.AddBoolAnd([hit, tc[(t,c)]]).OnlyEnforceIf(tsc[(t,s,c)])
            model.AddBoolOr([hit.Not(), tc[(t,c)].Not()]).OnlyEnforceIf(tsc[(t,s,c)].Not())
# inferring TS info
for s in range(len(I.slots)):
    for t in range(len(I.teachers)):
        model.Add(sum(tsc[(t,s,c)] for c in range(len(I.courses))) == 1).OnlyEnforceIf(ts[(t,s)])
        model.Add(sum(tsc[(t,s,c)] for c in range(len(I.courses))) == 0).OnlyEnforceIf(ts[(t,s)].Not())
# construct AC info (person P attends course C)
for p in range(len(I.people)):
    if I.people[p] in I.input_data:
        courses_attend = I.input_data[I.people[p]]["courses_attend"]
    else:
        courses_attend = []
    for c in range(len(I.courses)):
        if [x for x in courses_attend if I.courses[c].startswith(x)]:
            model.Add(ac[(p,c)] == 1)
        else:
            model.Add(ac[(p,c)] == 0)
# construct PC info (person P attends or teaches course C)
for p in range(len(I.people)):
    for c in range(len(I.courses)):
        model.AddBoolOr([tc[(p,c)], ac[(p,c)]]).OnlyEnforceIf(pc[(p,c)])
        model.AddBoolAnd([tc[(p,c)].Not(), ac[(p,c)].Not()]).OnlyEnforceIf(pc[(p,c)].Not())
# inferring PSC info - person P attends or teaches course C in slot S
for s in range(len(I.slots)):
    for c in range(len(I.courses)):
        hit = model.NewBoolVar("") # course C is at slot S
        model.Add(cs[c] == s).OnlyEnforceIf(hit)
        model.Add(cs[c] != s).OnlyEnforceIf(hit.Not())
        for p in range(len(I.people)):
            model.AddBoolAnd([hit, pc[(p,c)]]).OnlyEnforceIf(psc[(p,s,c)])
            model.AddBoolOr([hit.Not(), pc[(p,c)].Not()]).OnlyEnforceIf(psc[(p,s,c)].Not())
# inferring PS info - person P attends or teaches course in slot S
for s in range(len(I.slots)):
    for p in range(len(I.people)):
        model.Add(sum(psc[(p,s,c)] for c in range(len(I.courses))) == 1).OnlyEnforceIf(ps[(p,s)])
        model.Add(sum(psc[(p,s,c)] for c in range(len(I.courses))) == 0).OnlyEnforceIf(ps[(p,s)].Not())
# inferring TD info
for d in range(len(I.days)):
    for t in range(len(I.teachers)):
        model.Add(sum(ts[(t,s)] for s in range(d*len(I.times), (d+1)*len(I.times))) >= 1).OnlyEnforceIf(td[(t,d)])
        model.Add(sum(ts[(t,s)] for s in range(d*len(I.times), (d+1)*len(I.times))) == 0).OnlyEnforceIf(td[(t,d)].Not())
# inferring PD info
for d in range(len(I.days)):
    for p in range(len(I.people)):
        model.Add(sum(ps[(p,s)] for s in range(d*len(I.times), (d+1)*len(I.times))) >= 1).OnlyEnforceIf(pd[(p,d)])
        model.Add(sum(ps[(p,s)] for s in range(d*len(I.times), (d+1)*len(I.times))) == 0).OnlyEnforceIf(pd[(p,d)].Not())

# inferring TDV info
for s in range(len(I.slots)):
    for c in range(len(I.courses)):
        for v in range(len(I.venues)):
            hit = model.NewBoolVar("") # course C is at slot S in venue V
            model.Add(sum(src[(s,r,c)] for r in range(len(I.rooms)) if I.rooms_venues[I.rooms[r]] == I.venues[v]) == 1).OnlyEnforceIf(hit)
            model.Add(sum(src[(s,r,c)] for r in range(len(I.rooms)) if I.rooms_venues[I.rooms[r]] == I.venues[v]) == 0).OnlyEnforceIf(hit.Not())
            for t in range(len(I.teachers)):
                model.AddBoolAnd([hit, tc[(t,c)]]).OnlyEnforceIf(tscv[(t,s,c,v)])
                model.AddBoolOr([hit.Not(), tc[(t,c)].Not()]).OnlyEnforceIf(tscv[(t,s,c,v)].Not())
for t in range(len(I.teachers)):
    for d in range(len(I.days)):
        for v in range(len(I.venues)):
            model.Add(sum(tscv[(t,s,c,v)] for s in range(d*len(I.times),(d+1)*len(I.times)) for c in range(len(I.courses))) >= 1).OnlyEnforceIf(tdv[(t,d,v)])
            model.Add(sum(tscv[(t,s,c,v)] for s in range(d*len(I.times),(d+1)*len(I.times)) for c in range(len(I.courses))) == 0).OnlyEnforceIf(tdv[(t,d,v)].Not())
# inferring CV info
cv = []
for c in range(len(I.courses)):
    cv.append(model.NewIntVar(0, len(I.venues)-1, ""))
    for v in range(len(I.venues)):
        hit = model.NewBoolVar("")
        model.Add(sum(src[(s,r,c)] for s in range(len(I.slots)) for r in range(len(I.rooms)) if I.rooms_venues[I.rooms[r]] == I.venues[v]) >= 1).OnlyEnforceIf(hit)
        model.Add(sum(src[(s,r,c)] for s in range(len(I.slots)) for r in range(len(I.rooms)) if I.rooms_venues[I.rooms[r]] == I.venues[v]) == 0).OnlyEnforceIf(hit.Not())
        model.Add(cv[c] == v).OnlyEnforceIf(hit)
        model.Add(cv[c] != v).OnlyEnforceIf(hit.Not())

# number of lessons teacher T teaches
teach_num = {}
for t in range(len(I.teachers)):
    teach_num[t] = model.NewIntVar(0, len(I.slots), "Tteach_num:%i" % t)
    model.Add(teach_num[t] == sum(tc[(t,c)] for c in range(len(I.courses))))
# number of slots person P occupies (teaches or attends)
occupied_num = {}
for p in range(len(I.people)):
    occupied_num[p] = model.NewIntVar(0, len(I.slots), "")
    model.Add(occupied_num[p] == sum(ps[(p,s)] for s in range(len(I.slots))))

# prevent teachers from teaching in two rooms in the same time
for t in range(len(I.teachers)):
    for s in range(len(I.slots)):
        model.Add(sum(tsc[(t,s,c)] for c in range(len(I.courses))) <= 1)

# one course takes place at one time in one room
for c in range(len(I.courses)):
    model.Add(sum(src[(s,r,c)] for s in range(len(I.slots)) for r in range(len(I.rooms))) == 1)

# at one time in one room, there is maximum one course
for s in range(len(I.slots)):
    for r in range(len(I.rooms)):
        model.Add(sum(src[(s,r,c)] for c in range(len(I.courses))) <= 1)

# every regular course is taught by two teachers and solo course by one teacher
for c in range(len(I.courses)):
    if I.courses[c] in I.courses_regular:
        model.Add(sum(tc[(I.Teachers[T],c)] for T in I.teachers_lead) == 1)
        model.Add(sum(tc[(I.Teachers[T],c)] for T in I.teachers_follow) == 1)
    elif I.courses[c] in I.courses_solo:
        model.Add(sum(tc[(I.Teachers[T],c)] for T in I.teachers) == 1)
    elif I.courses[c] in I.courses_open:
        model.Add(sum(tc[(I.Teachers[T],c)] for T in I.teachers) == 0)
    else:
        assert(False)

# SPECIFIC CONSTRAINTS

if False:
    # unspecified teachers teach arbitrary number of courses
    for (T, n) in I.t_util_max.items():
        model.Add(sum(tc[(I.Teachers[T],c)] for c in range(len(I.courses))) <= n)
else:
    # unspecified teachers teach no courses
    for T in I.teachers:
        if T not in I.FAKE_TEACHERS:
            debug(f"Teacher max: {T} {I.t_util_max.get(T,-1)}")
            model.Add(sum(tc[(I.Teachers[T],c)] for c in range(len(I.courses))) <= I.t_util_max.get(T, 0))

# community teachers that must teach
for T in ["Zuzka", "Vojta-N.", "Míša-L.", "Kuba-B."]:
    if I.t_util_max.get(T, 0) >= 1:
        model.Add(sum(tc[(I.Teachers[T],c)] for c in range(len(I.courses))) >= 1)
    else:
        warn(f"community teacher {T} should teach, but has not utilization preferences")

if I.tc_strict:
    debug("strict assignments present")
    strict_assignments = []
    for (T, Cs) in I.tc_strict.items():
        t = I.Teachers[T]
        for C in Cs:
            c = I.Courses[C]
            strict_assignments.append(tc[(t,c)])
    model.AddBoolAnd(strict_assignments)

teachers_all = set(range(len(I.teachers)))
for (C, Ts) in I.ct_possible.items():
    c = I.Courses[C]
    teachers_can = []
    for T in Ts:
        t = I.Teachers[T]
        teachers_can.append(t)
    teachers_not = teachers_all - set(teachers_can)
    # no other teacher can teach C
    model.Add(sum(tc[(t,c)] for t in teachers_not) == 0)

for T1, T2 in I.tt_not_together:
    for c in range(len(I.courses)):
        model.Add(sum(tc[(t,c)] for t in [I.Teachers[T1], I.Teachers[T2]]) < 2)

# TODO: this should be loosened, also wrt. attending
# teacher T does not teach in two venues in the same day
for t in range(len(I.teachers)):
    for d in range(len(I.days)):
        model.Add(sum(tdv[(t,d,v)] for v in range(len(I.venues))) <= 1)

# strict courses schedule
# Teachers training must be at Thursday evening
model.Add(cs[I.Courses["Teachers Training"]] == 11)
# nothing else happens in parallel with Teachers Training
model.Add(sum(src[(11,r,c)] for r in range(len(I.rooms)) for c in range(len(I.courses))) == 1)
# Shag/Balboa open is AFTER Collegiate Shag 2 (combined with courses_same
model.Add(cs[I.Courses["Collegiate Shag 2"]]+1 == cs[I.Courses["Shag/Balboa Open Training"]])
# PJ training must happen on Tuesday and Thursday
model.Add(cs[I.Courses["PJ Group /1"]] >= 3)
model.Add(cs[I.Courses["PJ Group /1"]] <= 5)
model.Add(cs[I.Courses["PJ Group /2"]] >= 9)
model.Add(cs[I.Courses["PJ Group /2"]] <= 11)

# teachers HARD slot preferences
for T in I.teachers:
    if T in I.ts_pref: # TODO what about people without preferences?
        for s, v in enumerate(I.ts_pref[T]):
            if v == 0:
                model.Add(ts[(I.Teachers[T], s)] == 0)

# same courses should not happen in same days and also not in same times
# it should probably not be a strict limitation, but it is much easier to write
for Cs in I.courses_different:
    daylist = [] # days
    timelist = [] # times
    assert(2 <= len(Cs) <= min(len(I.days), len(I.times)))
    for C in Cs:
        day = model.NewIntVar(0, len(I.days)-1, "")
        time = model.NewIntVar(0, len(I.times)-1, "")
        model.AddDivisionEquality(day, cs[I.Courses[C]], len(I.times))
        model.AddModuloEquality(time, cs[I.Courses[C]], len(I.times))
        daylist.append(day)
        timelist.append(time)
    model.AddAllDifferent(daylist)
    model.AddAllDifferent(timelist)

# courses that should not happen in same days
for Cs in I.courses_diffday:
    daylist = [] # days
    assert(2 <= len(Cs) <= len(I.days))
    for C in Cs:
        day = model.NewIntVar(0, len(I.days)-1, "")
        model.AddDivisionEquality(day, cs[I.Courses[C]], len(I.times))
        model.AddModuloEquality(time, cs[I.Courses[C]], len(I.times))
        daylist.append(day)
    model.AddAllDifferent(daylist)

# courses that should follow each other in the same day in the same venue
for Cs in I.courses_same:
    daylist = [] # days
    timelist = [] # times
    venuelist = [] # venues
    assert(2 <= len(Cs) <= len(I.times))
    for C in Cs:
        day = model.NewIntVar(0, len(I.days)-1, "")
        time = model.NewIntVar(0, len(I.times)-1, "")
        venue = model.NewIntVar(0, len(I.venues)-1, "")
        model.AddDivisionEquality(day, cs[I.Courses[C]], len(I.times))
        model.AddModuloEquality(time, cs[I.Courses[C]], len(I.times))
        model.Add(venue == cv[I.Courses[C]])
        daylist.append(day)
        timelist.append(time)
        venuelist.append(venue)
    model.AddAllowedAssignments(daylist, [[d] * len(Cs) for d in range(len(I.days))])
    model.AddAllowedAssignments(venuelist, [[v] * len(Cs) for v in range(len(I.venues))])
    if len(Cs) == len(I.times):
        # filling whole day
        model.AddAllDifferent(timelist)
    elif len(Cs) == len(I.times) - 1:
        # filling 2 out of three slots
        assert(len(Cs) == 2)
        model.AddAllowedAssignments(timelist, [ [0,1], [1,0], [1,2], [2,1] ])
    else:
        # should not happen
        assert(False)

for (C, R) in I.cr_not.items():
    model.Add(sum(src[(s,I.Rooms[R],I.Courses[C])] for s in range(len(I.slots))) == 0)

for (C, R) in I.cr_strict.items():
    model.Add(sum(src[(s,I.Rooms[R],I.Courses[C])] for s in range(len(I.slots))) == 1)

# community teachers must teach max 2 courses
for T in I.teachers_community:
    model.Add(sum(tc[(I.Teachers[T],c)] for c in range(len(I.courses))) <= 2)
# community teachers must teach together with core teachers
for C in I.courses_regular:
    model.Add(sum(tc[(I.Teachers[T],I.Courses[C])] for T in I.teachers_community) <= 1)
# community teachers cannot teach solo courses
for C in I.courses_solo:
    model.Add(sum(tc[(I.Teachers[T],I.Courses[C])] for T in I.teachers_community) == 0)


# Rather specific constraints:

# Damian
damian = True
if damian and I.t_util_max.get("Pavli", 0) >= 2 and I.t_util_max.get("Tom-K.", 0) >= 1:
    model.Add(sum(tc[(I.Teachers["Tom-K."],c)] for c in range(len(I.courses))) == 1)
    model.Add(sum(tc[(I.Teachers["Pavli"],c)] for c in range(len(I.courses))) == 2)
    model.Add(sum(tscv[(I.Teachers["Tom-K."],s,c,I.Venues["mosilana"])] for s in range(len(I.slots)) for c in range(len(I.courses))) == 0)
    model.Add(sum(tscv[(I.Teachers["Pavli"],s,c,I.Venues["mosilana"])] for s in range(len(I.slots)) for c in range(len(I.courses))) == 0)
    damianday = model.NewIntVar(0, len(I.days)-1, "damianday")
    for d in range(len(I.days)):
        hit = model.NewBoolVar("")
        model.Add(damianday == d).OnlyEnforceIf(hit)
        model.Add(damianday != d).OnlyEnforceIf(hit.Not())
        model.Add(ts[(I.Teachers["Tom-K."],d*len(I.times)+0)] == 1).OnlyEnforceIf(hit)
        model.Add(ts[(I.Teachers["Pavli"],d*len(I.times)+1)] == 1).OnlyEnforceIf(hit)
        model.Add(ts[(I.Teachers["Pavli"],d*len(I.times)+2)] == 1).OnlyEnforceIf(hit)

# OPTIMIZATION

# "name" -> coeff
PENALTIES = {
    "utilization": 100, # squared
    "days": 300,
    "occupied_days": 50,
    "split": 300,
    "slotpref_bad": 300,
    "slotpref_slight": 50,
    "coursepref_bad": 300,
    "coursepref_slight": 50,
    "mosilana": 300,
    "attend_free": 100,
    "teach_together": 100,
    "faketeachers": 100000,
}

penalties = {} # penalties data (model variables)
penalties_analysis = {} # deeper analysis functions for penalties

for (name, coeff) in PENALTIES.items():
    if coeff == 0:
        warn(f"Penalties: skipping '{name}'")
        continue
    if name == "utilization":
        # teaching should be as close to preferences as possible
        penalties_utilization = []
        for T in I.t_util_ideal:
            t = I.Teachers[T]
            util_ideal = I.t_util_ideal[T]
            MAX_DIFF = 10 # set according to preferences form
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
            for T in I.teachers:
                if T in I.t_util_ideal:
                    t = I.Teachers[T]
                    util_ideal = I.t_util_ideal[T]
                    util_real = sum(tc[(t,c)] for c in range(len(I.courses)))
                    if util_real != util_ideal:
                        debug(f"analysis utilization - {T} wanted {util_ideal}, teaches {util_real}")
                        result.append(f"{T}/{util_real}r-{util_ideal}i")
            return result
        penalties_analysis[name] = analysis
    elif name == "days":
        # nobody should come more days then necessary
        penalties_days = []
        for t in range(len(I.teachers)):
            teaches_days = model.NewIntVar(0, len(I.days), "TD:%i" % t)
            model.Add(teaches_days == sum(td[(t,d)] for d in range(len(I.days))))
            teaches_minus_1 = model.NewIntVar(0, len(I.days), "Tm1:%i" % t)
            teaches_some = model.NewBoolVar("Ts:%i" % t)
            model.Add(teach_num[t] >= 1).OnlyEnforceIf(teaches_some)
            model.Add(teach_num[t] == 0).OnlyEnforceIf(teaches_some.Not())
            model.Add(teaches_minus_1 == teach_num[t] - 1).OnlyEnforceIf(teaches_some)
            model.Add(teaches_minus_1 == 0).OnlyEnforceIf(teaches_some.Not())
            should_teach_days = model.NewIntVar(0, len(I.days), "TDs:%i" % t)
            model.AddDivisionEquality(should_teach_days, teaches_minus_1, len(I.times)) # -1 to compensate rounding down
            days_extra = model.NewIntVar(0, len(I.days), "Tdd:%i" % t)
            model.Add(days_extra == teaches_days - should_teach_days - 1).OnlyEnforceIf(teaches_some) # -1 to compensate rounding down
            model.Add(days_extra == 0).OnlyEnforceIf(teaches_some.Not())
            days_extra_sq = model.NewIntVar(0, len(I.days)**2, "Tdds:%i" % t)
            model.AddMultiplicationEquality(days_extra_sq, [days_extra, days_extra])
            penalties_days.append(days_extra_sq)
        penalties[name] = penalties_days
        def analysis(src, tc):
            result = []
            for t in range(len(I.teachers)):
                cs = []
                for c in range(len(I.courses)):
                    if tc[(t,c)]:
                        cs.append(c)
                n_courses = sum(tc[(t,c)] for c in range(len(I.courses)))
                assert(len(cs) == n_courses)
                n_days = 0
                for d in range(len(I.days)):
                    if sum(src[(s,r,c)] for s in range(d*len(I.times), (d+1)*len(I.times)) for r in range(len(I.rooms)) for c in cs):
                        n_days += 1
                if n_days*len(I.times) - n_courses >= len(I.times):
                    result.append(f"{I.teachers[t]} {n_courses}c/{n_days}d")
            return result
        penalties_analysis[name] = analysis
    elif name == "occupied_days":
        # nobody should come more days then necessary - including attending courses
        penalties_occupied_days = []
        for p in range(len(I.people)):
            occupied_days = model.NewIntVar(0, len(I.days), "")
            model.Add(occupied_days == sum(pd[(p,d)] for d in range(len(I.days))))
            occupied_some = model.NewBoolVar("")
            model.Add(occupied_num[p] >= 1).OnlyEnforceIf(occupied_some)
            model.Add(occupied_num[p] == 0).OnlyEnforceIf(occupied_some.Not())
            occupied_minus_1 = model.NewIntVar(0, len(I.days), "")
            model.Add(occupied_minus_1 == occupied_num[p] - 1).OnlyEnforceIf(occupied_some)
            model.Add(occupied_minus_1 == 0).OnlyEnforceIf(occupied_some.Not())
            should_occupy_days = model.NewIntVar(0, len(I.days), "")
            model.AddDivisionEquality(should_occupy_days, occupied_minus_1, len(I.times)) # -1 to compensate rounding down
            occupied_days_extra = model.NewIntVar(0, len(I.days), "")
            model.Add(occupied_days_extra == occupied_days - should_occupy_days - 1).OnlyEnforceIf(occupied_some) # -1 to compensate rounding down
            model.Add(occupied_days_extra == 0).OnlyEnforceIf(occupied_some.Not())
            occupied_days_extra_sq = model.NewIntVar(0, len(I.days)**2, "")
            model.AddMultiplicationEquality(occupied_days_extra_sq, [occupied_days_extra, occupied_days_extra])
            penalties_occupied_days.append(occupied_days_extra_sq)
        penalties[name] = penalties_occupied_days
        def analysis(src, tc):
            result = []
            for p in range(len(I.people)):
                occupied_courses = []
                for c in range(len(I.courses)):
                    if tc[(p,c)] or (I.people[p] in I.input_data and [x for x in I.input_data[I.people[p]]["courses_attend"] if I.courses[c].startswith(x)]):
                        occupied_courses.append(c)
                n_courses = len(occupied_courses)
                n_days = 0
                for d in range(len(I.days)):
                    if sum(src[(s,r,c)] for s in range(d*len(I.times), (d+1)*len(I.times)) for r in range(len(I.rooms)) for c in occupied_courses):
                        n_days += 1
                if n_days*len(I.times) - n_courses >= len(I.times):
                    result.append(f"{I.people[p]} {n_courses}c/{n_days}d")
            return result
        penalties_analysis[name] = analysis
    elif name == "split":
        # teacher should not wait between lessons
        penalties_split = []
        for t in range(len(I.teachers)):
            days_split = model.NewIntVar(0, len(I.days), "TDsplit:%i" % t)
            tsplits = []
            for d in range(len(I.days)):
                # tsplit == True iff teacher t teaches just the first and the last course in day d
                tsubsplits = []
                for i in range(len(I.times)):
                    tsubsplit = model.NewBoolVar("tsubsplit:t%id%ii%i" % (t,d,i))
                    model.Add(sum(ts[(t,s)] for s in [d*len(I.times)+i]) == 1).OnlyEnforceIf(tsubsplit)
                    model.Add(sum(ts[(t,s)] for s in [d*len(I.times)+i]) == 0).OnlyEnforceIf(tsubsplit.Not())
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
            for t in range(len(I.teachers)):
                cs = []
                for c in range(len(I.courses)):
                    if tc[(t,c)]:
                        cs.append(c)
                n = 0
                for d in range(len(I.days)):
                    if (
                            sum(src[(d*len(I.times),r,c)]  for r in range(len(I.rooms)) for c in cs) >= 1
                            and sum(src[(d*len(I.times)+1,r,c)]  for r in range(len(I.rooms)) for c in cs) == 0
                            and sum(src[(d*len(I.times)+2,r,c)]  for r in range(len(I.rooms)) for c in cs) >= 1
                            ):
                        n += 1
                if n > 0:
                    result.append(f"{I.teachers[t]}/{n}")
            return result
        penalties_analysis[name] = analysis
    elif name == "slotpref_bad":
        # slots preferences
        penalties_slotpref_bad = []
        for T in I.teachers:
            if T in I.ts_pref:
                prefs = I.ts_pref[T]
                if set([1,2]) <= set(prefs) or set([1,3]) <= set(prefs):
                    # teacher T strongly prefers some slots over others
                    slots_bad = [s for s in range(len(I.slots)) if prefs[s] == 1]
                    penalties_slotpref_bad.append(sum(ts[(I.Teachers[T],s)] for s in slots_bad))
        penalties[name] = penalties_slotpref_bad
        def analysis(src, tc):
            result = []
            for t in range(len(I.teachers)):
                T = I.teachers[t]
                cs = []
                for c in range(len(I.courses)):
                    if tc[(t,c)]:
                        cs.append(c)
                bad_slots = []
                n = 0
                if T in I.ts_pref:
                    prefs = I.ts_pref[T]
                    if set([1,2]) <= set(prefs) or set([1,3]) <= set(prefs):
                        for s in range(len(I.slots)):
                            if I.ts_pref[T][s] == 1:
                                if sum(src[(s,r,c)] for r in range(len(I.rooms)) for c in cs) >= 1:
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
        for T in I.teachers:
            if T in I.ts_pref:
                prefs = I.ts_pref[T]
                if set([2,3]) <= set(prefs):
                    # teacher T slightly prefers some slots over others
                    slots_bad = [s for s in range(len(I.slots)) if prefs[s] == 2]
                    penalties_slotpref_slight.append(sum(ts[(I.Teachers[T],s)] for s in slots_bad))
        penalties[name] = penalties_slotpref_slight
        def analysis(src, tc):
            result = []
            for t in range(len(I.teachers)):
                T = I.teachers[t]
                cs = []
                for c in range(len(I.courses)):
                    if tc[(t,c)]:
                        cs.append(c)
                bad_slots = []
                n = 0
                if T in I.ts_pref:
                    prefs = I.ts_pref[T]
                    if set([2,3]) <= set(prefs):
                        for s in range(len(I.slots)):
                            if I.ts_pref[T][s] == 2:
                                if sum(src[(s,r,c)] for r in range(len(I.rooms)) for c in cs) >= 1:
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
        for T in I.teachers:
            if T in I.tc_pref:
                spv = set(I.tc_pref[T].values())
                if set([1,2]) <= spv and set([1,3]) <= spv:
                    # teacher T strongly prefers some courses over others
                    courses_bad = [C for C in I.courses_regular+I.courses_solo if I.tc_pref[T].get(C, -1) == 1]
                    penalties_coursepref.append(sum(tc[(I.Teachers[T],I.Courses[C])] for C in courses_bad))
        penalties[name] = penalties_coursepref
        def analysis(src, tc):
            result = []
            for t in range(len(I.teachers)):
                T = I.teachers[t]
                courses_bad = []
                if T in I.tc_pref:
                    spv = set(I.tc_pref[T].values())
                    if set([1,2]) <= spv and set([1,3]) <= spv:
                        # teacher T strongly prefers some courses over others
                        courses_bad = [C for C in I.courses_regular+I.courses_solo if I.tc_pref[T].get(C, -1) == 1 and tc[(t,I.Courses[C])]]
                if courses_bad:
                    debug(f"analysis coursepref_bad - teacher {T} courses {courses_bad}")
                    result.append(f"{T}/{len(courses_bad)}")
            return result
        penalties_analysis[name] = analysis
    elif name == "coursepref_slight":
        # slots preferences
        penalties_coursepref = []
        for T in I.teachers:
            if T in I.tc_pref:
                if set([2,3]) <= set(I.tc_pref[T].values()):
                    # teacher T strongly prefers some courses over others
                    courses_bad = [C for C in I.courses_regular+I.courses_solo if I.tc_pref[T].get(C, -1) == 2]
                    penalties_coursepref.append(sum(tc[(I.Teachers[T],I.Courses[C])] for C in courses_bad))
        penalties[name] = penalties_coursepref
        def analysis(src, tc):
            result = []
            for t in range(len(I.teachers)):
                T = I.teachers[t]
                courses_bad = []
                if T in I.tc_pref:
                    if set([2,3]) <= set(I.tc_pref[T].values()):
                        # teacher T strongly prefers some courses over others
                        courses_bad = [C for C in I.courses_regular+I.courses_solo if I.tc_pref[T].get(C, -1) == 2 and tc[(t,I.Courses[C])]]
                if courses_bad:
                    debug(f"analysis coursepref_slight teacher {T} courses {courses_bad}")
                    result.append(f"{T}/{len(courses_bad)}")
            return result
        penalties_analysis[name] = analysis
    elif name == "faketeachers":
        penalties_faketeachers = []
        # fake teachers
        for T in I.FAKE_TEACHERS:
            if T in I.teachers:
                penalties_faketeachers.append(sum(tc[(I.Teachers[T],c)] for c in range(len(I.courses))))
        penalties[name] = penalties_faketeachers
    elif name == "mosilana": # penalty for not using koliste
        util_koliste = model.NewIntVar(0, 2*len(I.slots), "") # utilization of Koliste
        model.Add(util_koliste == sum(src[(s,r,c)] for s in range(len(I.slots)) for r in range(len(I.rooms)) if I.rooms_venues[I.rooms[r]] == "koliste" for c in range(len(I.courses))))
        free_koliste = model.NewIntVar(0, 2*len(I.slots), "") # free slots in Koliste
        model.Add(free_koliste == 2*len(I.slots)-util_koliste-1) # -1 for Teachers Training
        penalties[name] = [free_koliste]
    elif name == "attend_free": # penalty if interested in attending cannot attend (they teach something else in the same time)
        # courses that some teachers would like to attend
        courses_attend = [I.input_data[T]["courses_attend"] for T in I.input_data]
        courses_attend = [item for sl in courses_attend for item in sl] # flatten sublists
        courses_attend = list(set(courses_attend)) # unique course names
        debug(f"attend_free: courses_attend {courses_attend}")
        for C in courses_attend:
            debug(f"attend_free: courses {C}")
            teachers_attend = []
            for T in I.input_data:
                if C in I.input_data[T]["courses_attend"]:
                    teachers_attend.append(T)
            debug(f"attend_free: teachers_attend {teachers_attend}")
            #t = I.Teachers[T]
            penalties_attend_free = []
            for s in range(len(I.slots)):
                hit = model.NewBoolVar("")
                model.Add(cs[I.Courses[C]] == s).OnlyEnforceIf(hit)
                model.Add(cs[I.Courses[C]] != s).OnlyEnforceIf(hit.Not())
                penalty_slot = model.NewIntVar(0, len(teachers_attend)-1, "") # penalty for the slot
                model.Add(penalty_slot == sum(ts[(I.Teachers[T],s)] for T in teachers_attend)).OnlyEnforceIf(hit)
                model.Add(penalty_slot == 0).OnlyEnforceIf(hit.Not())
                penalties_attend_free.append(penalty_slot)
        penalties[name] = penalties_attend_free
    elif name == "teach_together": # penalty if interested in teaching with Ts but teaches with noone
        penalties_teach_together = []
        # teachers with teach_together preferences
        Ts = [T for T in I.input_data if I.input_data[T]["teach_together"]]
        for T in Ts:
            debug(f"teach_together: {T} + {I.input_data[T]['teach_together']}")
            t = I.Teachers[T]
            success_list = []
            for c in range(len(I.courses)):
                hit_self = model.NewBoolVar("")
                hit_other = model.NewBoolVar("")
                success = model.NewBoolVar("")
                model.Add(tc[(t,c)] == 1).OnlyEnforceIf(hit_self)
                model.Add(tc[(t,c)] == 0).OnlyEnforceIf(hit_self.Not())
                model.Add(sum(tc[(I.Teachers[To],c)] for To in I.input_data[T]["teach_together"]) >= 1).OnlyEnforceIf(hit_other)
                model.Add(sum(tc[(I.Teachers[To],c)] for To in I.input_data[T]["teach_together"]) == 0).OnlyEnforceIf(hit_other.Not())
                model.AddBoolAnd([hit_self, hit_other]).OnlyEnforceIf(success)
                model.AddBoolOr([hit_self.Not(), hit_other.Not()]).OnlyEnforceIf(success.Not())
                success_list.append(success)
            nobody = model.NewBoolVar("")
            model.Add(sum(success_list) == 0).OnlyEnforceIf(nobody)
            model.Add(sum(success_list) >= 1).OnlyEnforceIf(nobody.Not())
            penalties_teach_together.append(nobody)
        penalties[name] = penalties_teach_together
        def analysis(src, tc):
            result = []
            Ts = [T for T in I.input_data if I.input_data[T]["teach_together"]]
            for T in Ts:
                debug(f"analysis teach_together: teacher {T}")
                t = I.Teachers[T]
                teachers_prefered = [I.Teachers[To] for To in I.input_data[T]["teach_together"]]
                debug(f"analysis teach_together: teachers_prefered {teachers_prefered}")
                teach_courses = [c for c in range(len(I.courses)) if tc[(t,c)]]
                debug(f"analysis teach_together: teach_courses {teach_courses}")
                success_courses = []
                for c in teach_courses:
                    if sum(tc[to,c] for to in teachers_prefered) >= 1:
                        success_courses.append(c)
                #success_courses = [c for c in teach_courses for to in teachers_prefered if sum([(to,c)]) >= 1]
                debug(f"analysis teach_together: success_courses {[I.courses[x] for x in success_courses]}")
                if not success_courses:
                    result.append(f"{T}")
            return result
        penalties_analysis[name] = analysis

penalties_values = []
for (name, l) in penalties.items():
    penalties_values.append(PENALTIES[name] * sum(l))

model.Minimize(sum(penalties_values))

print(model.ModelStats())
print()

def print_solution(src, tc, penalties, objective=None, utilization=True):
    if objective:
        print(f"Objective value: {objective}")
    for s in range(len(I.slots)):
        for r in range(len(I.rooms)):
            for c in range(len(I.courses)):
                if src[(s,r,c)]:
                    Ts = []
                    if I.courses[c] in I.courses_open:
                        Ts.append("OPEN\t")
                    elif I.courses[c] in I.courses_solo:
                        for t in range(len(I.teachers)):
                            #if solver.Value(tc[(t,c)]):
                            if tc[(t,c)]:
                                Ts.append(I.teachers[t] + "\t")
                                break
                    elif I.courses[c] in I.courses_regular:
                        for t in range(len(I.teachers)):
                            if tc[(t,c)]:
                                Ts.append(I.teachers[t])
                    if len(Ts) == 2 and Ts[0] in I.teachers_follow:
                        Ts[0], Ts[1] = Ts[1], Ts[0]
                    print(f"{I.slots[s]}\t {I.rooms[r]}\t{'+'.join(Ts)}\t{I.courses[c]}")
    if penalties:
        print("Penalties:")
        total = 0
        for (name, t) in penalties.items():
            coeff, v = t
            total += coeff * v
            if v == 0 or name not in penalties_analysis:
                print(f"{name}: {v} * {coeff} = {v*coeff}")
            else:
                print(f"{name}: {v} * {coeff} = {v*coeff} ({', '.join(penalties_analysis[name](src, tc))})")
    if utilization:
        debug("UTILIZATION:")
        tn = {}
        for t in range(len(I.teachers)):
            tn[I.teachers[t]] = sum(tc[t,c] for c in range(len(I.courses)))
        for v in sorted(set(tn.values())):
            print(f"{v}: {', '.join(t for t in tn if tn[t] == v)}")
    print(f"TOTAL: {total}")


class ContinuousSolutionPrinter(cp_model.CpSolverSolutionCallback):
    def __init__(self):
        self.count = 0
        cp_model.CpSolverSolutionCallback.__init__(self)

    def OnSolutionCallback(self):
        self.count += 1
        result_src = {}
        for s in range(len(I.slots)):
            for r in range(len(I.rooms)):
                for c in range(len(I.courses)):
                        result_src[(s,r,c)] = self.Value(src[(s,r,c)])
        result_tc = {}
        for t in range(len(I.teachers)):
            for c in range(len(I.courses)):
                result_tc[(t,c)] = self.Value(tc[(t,c)])
        for p in range(len(I.people)):
            m = f"ps/pd analysis: {I.people[p]}\t"
            m += " slots "
            for s in range(len(I.slots)):
                if self.Value(ps[(p,s)]):
                    m += "1"
                else:
                    m += "0"
            m += " num "
            m += f"{self.Value(occupied_num[p])}"
            m += " days "
            for d in range(len(I.days)):
                if self.Value(pd[(p,d)]):
                    m += "1"
                else:
                    m += "0"
            debug(m)
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

solver = cp_model.CpSolver()
#solver.parameters.max_time_in_seconds = 20.0
status = solver.SolveWithSolutionCallback(model, ContinuousSolutionPrinter())
statusname = solver.StatusName(status)
print(f"Solving finished in {solver.WallTime()} seconds with status {status} - {statusname}")
if statusname not in ["FEASIBLE", "OPTIMAL"]:
    error(f"Solution NOT found - status {statusname}")

print()
print(f"Teachers' utilization:")
for n in range(len(I.slots)):
    Ts = []
    for T in I.teachers:
        if solver.Value(teach_num[I.Teachers[T]]) == n:
            Ts.append(T)
    if Ts:
        print(f"{n}: {' '.join(Ts)}")
