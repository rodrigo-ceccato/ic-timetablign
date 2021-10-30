#!usr/bin/python3.7
import copy
import pandas as pd
import numpy as np
from collections import Counter as counter # count ocourrences of items
from random import randint
from gurobipy import *

class modelManager:
    '''Class for keeping track of the ILP model'''
    model: gurobipy.Model = None
    modelData: dict = None
    t_assign: dict = None
    c_assign: dict = None
    time_frames_list: list = None

    def __init__(self, modelData: dict):
        self.modelData = modelData

    #TODO: implement body
    def addTeacherCourseArc(self, t,c):
        print(f'Adding {t} to {c} arc')

    #TODO: implement body
    def removeTeacherCourseArc(self,t,c):
        print(f'Removing {t} to {c} arc')

        t_assign = self.t_assign
        m = self.model

        m.addConstr(t_assign[t,c] == 0)

    #TODO: implement body
    def lockTeacherToCourse(self,t,c):
        print(f'Locking {t} to {c}')

    #TODO: implement body
    def lockCourseToTimeframe(self, c, tf):
        print(f'Locking {c} to timeframe {tf}')

    def exportPreferenceResult(self, path='./output'):
        assignment_arc =  self.modelData['assignmentArcs']
        curr_arc = {t : [] for t in self.modelData['teachers']}

        complied_prerefence_counter = counter()

        for (t,c),pref_value in assignment_arc.items():
            if self.t_assign[(t,c)].getAttr("x") > 0.5:        
                curr_arc[t].append(c)
                complied_prerefence_counter.update({pref_value})
        
        print(complied_prerefence_counter)



    def exportSolution(self, path='./output'):
        # get the timeslots of each course
        assigned_tf = {c:tf for (c,tf),value in self.c_assign.items() if value.getAttr("X") > 0.5}
        courses_time_slot = {c: self.time_frames_list[assigned_tf[c]] for c in self.modelData['courses']}

        #names dictionary
        weekDayName = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado']
        timeSlotName = ['08h00', '10h00', '14h00', '16h00', '19h00', '21h00']

        solution = {}
        for t in self.modelData['teachers']:
            # get courses teached by this teacher
            curr_t_arcs = [((assigned_t,c),mVar) for ((assigned_t,c),mVar) in self.t_assign.items() if assigned_t == t]
            t_courses = [c for (assigned_t,c),var_value in curr_t_arcs if var_value.getAttr("x") > 0.5]

            hour_frame = ['']*36
            # get hour table
            for i,weekName in enumerate(weekDayName):
                for j,timeName in enumerate(timeSlotName):
                    avaliability = '-     -'

                    index = i*(len(timeSlotName)) + j
                    # no teaching at saturdays
                    if index >= 32:
                        avaliability = '-xxxxx-'

                    else:
                        curr_forbidden_slot = self.modelData['teacherForbiddenTimeSlot'][t]
                        is_forbidden_slot = curr_forbidden_slot[index]

                        if is_forbidden_slot is 1:
                            avaliability = '-xxxxx-'

                        for course in t_courses:
                            if courses_time_slot[course][index] == 1:
                                avaliability = course
                        
                    hour_frame[index] = avaliability

            # add frame to solutio
            solution[t] = hour_frame

        infoColumn = []
        weekColumns = [[],[],[],[],[],[]]

        for (t, t_tf) in solution.items():
            infoColumn.append(t)
            infoColumn.extend(timeSlotName)
            
            for i in range(6):
                new_info = (t_tf[(i*6) : ((i*6)+6)])
                weekColumns[i].append(weekDayName[i])
                weekColumns[i].extend(new_info)


        d = []
        d.append(infoColumn)
        d.extend(weekColumns)

        df = pd.DataFrame(d, dtype=str)
        df = df.T


        df.to_csv(path+'/solution.csv', index = None, header=False)
        html = df.to_html(index = None, header=False)
        with open(path+'/solution.html', "w", encoding="utf-8") as file:
            file.write(html)


    def callSolver(self):
        '''Call Gurobi solver for already built ILP model'''

        m = self.model
        modelData = self.modelData
        t_assign = self.t_assign

        if m is None:
            print("ERROR: attemp to solve ILP model not built!")
            exit(0)
        
        m.Params.LogFile="./output/gurobi.log"

        # print lp model
        m.update()
        m.write("output/debug.lp")

        m.optimize()


        if m.status == GRB.Status.INF_OR_UNBD:
            # Turn presolve off to determine whether model is infeasible
            # or unbounded
            m.setParam(GRB.Param.Presolve, 0)
            m.optimize()

        elif m.status == GRB.Status.OPTIMAL:
            print('Optimal objective: %g' % m.objVal)
            m.write('output/model.sol')
            print('\nGlobal Preference Value: %g' % m.objVal)
            for t in modelData['teachers']:
                print('\nTeacher %s:' %  t)
                t_couses = [c for (assigned_t,c),modelVar in t_assign.items() if assigned_t == t and modelVar.getAttr("x") > 0.5]
                print(t_couses)

        elif m.status != GRB.Status.INFEASIBLE:
            print('Optimization was stopped with status %d' % m.status)

        else:
            # Model is infeasible - compute an Irreducible Inconsistent Subsystem (IIS)
            print('Model is infeasible')
            m.computeIIS()
            m.write("output/model.ilp")
            print("IIS written to file 'model.ilp'")

    def getModel(self):
        '''Build Gurobi model from parsed data'''
        
        modelData=self.modelData

        # model
        m = Model("ic-timetabling")

        # get data from input dict
        teachers = modelData['teachers']
        courses  = modelData['courses']
        teacher_forbidden_time_slot  = modelData['teacherForbiddenTimeSlot']
        assignment_arc, preference   = multidict (modelData['assignmentArcs'])
        course_time_slot = modelData['courseTimeSlot']
        course_credits   = modelData['courseCredits']
        max_credits      = modelData['teacherMaxCredit']
        min_credits      = modelData['teacherMinCredit']

        ########## PRE PROCESSING #########
        print("Started data pre-processing...")

        # creates time-frames table to group the ones that are equal
        course_tf = {key: list() for (key, value) in course_time_slot.items()}
        time_frames_list = []
        for course in courses:
            for time_frame in course_time_slot[course]:
                if time_frame not in time_frames_list:
                    time_frames_list.append(time_frame)

                # save time-frame index associated with course
                course_tf[course].append(time_frames_list.index(time_frame))


        # builds list of intersecting time-frames O(n^2)
        conflict_frames_pairs_list = []
        for i in range(len(time_frames_list)):
            for j in range(i+1, len(time_frames_list)):
                # get all possible pairs and check if there are conflicts
                list_a = time_frames_list[i]
                list_b = time_frames_list[j]

                conflicts = [1 if (a + b > 1) else 0 for a,b in zip(list_a,list_b)]

                if sum(conflicts) > 0:
                    conflict_frames_pairs_list.append((i,j))


        # associate a forbidden frame with a teacher's forbiden slot
        teacher_forbidden_tf = {teacher: list() for teacher in teachers}
        for teacher in teachers:
            curr_teacher_fs = teacher_forbidden_time_slot[teacher]
            for tf_index, tf in enumerate(time_frames_list):
                if not all([True if (x + y < 2) else False for x, y in zip(tf, curr_teacher_fs)]):
                    teacher_forbidden_tf[teacher].append(tf_index)


        # gets a dictionary of teacher preferences
        course_teachables = {c: list() for c in courses}
        for (t,c) in assignment_arc:
            course_teachables[c].append(t)


        print("Finished data pre-processing...")
        ####### END OF PRE PROCESSING ######



        #################### MODEL VARIABLES ###########################
        print("Adding model vars...")

        # teacher-course assignment variables
        t_assign = {}
        for arc in assignment_arc:
            t_assign[arc] = m.addVar(vtype=GRB.BINARY, name=f'x_{arc[0]}_{arc[1]}')


        # course-time-slot assignment variavles
        c_assign = {}
        for c in courses:
            for tf in course_tf[c]:
                c_assign[(c,tf)] = m.addVar(vtype=GRB.BINARY, name=f'y_{c}_tf-{tf}')


        # assign teacher to time-frame
        z_assign = {}
        for t in teachers:
            for tf in range(len(time_frames_list)):
                z_assign[(t, tf)] = m.addVar(vtype=GRB.BINARY, name=f'z_{t}_tf-{tf}')



        #################### MODEL CONSTRAINTS ###########################
        print("Adding model constraints...")

        # each course must be assigned to exactly ONE time slot
        for c in courses:
            m.addConstr(sum(c_assign[c,tf] for tf in course_tf[c]) == 1, name=f'{c}-exact-1-time-frame')


        # no teacher lectures two courses at the same time
        for t in teachers:
            for (tf_a, tf_b) in conflict_frames_pairs_list:
                z_a = z_assign[t, tf_a]
                z_b = z_assign[t, tf_b]

                m.addConstr(z_a + z_b <= 1, name=f'{t}-tf-{tf_a}-or-{tf_b}')


        # limit how much credits a given teacher gets
        for t in teachers:
            curr_t_courses = [c for c in courses if (t,c) in t_assign]
            m.addConstr(sum(t_assign[t,c]*course_credits[c] for c in curr_t_courses) <= max_credits[t],
                                                                name=f'{t}-max-cred-{max_credits[t]}')

            m.addConstr(sum(t_assign[t,c]*course_credits[c] for c in curr_t_courses) >= min_credits[t],
                                                                name=f'{t}-min-cred-{min_credits[t]}')



        # respect teachers forbidden time slots
        for t in teachers:
            m.addConstr(sum(z_assign[t, ff] for ff in teacher_forbidden_tf[t]) == 0, name=f'{t}-forbbids')


        # coupling constraints
        for(t,c),t_var in t_assign.items():
            for tf in course_tf[c]:
                # t_var corresponds to (t,c) decision var
                m.addConstr(z_assign[t,tf] >= t_var + c_assign[c,tf]  - 1, name=f'z_{t}_{tf}_{c}')


        # course is assigned to exactly ONE teacher
        for c in courses:
            m.addConstr(sum(t_assign[t,c] for t in course_teachables[c] ) == 1, name=f'1-teacher-per-course-{t}-{c}')



        ############ MODEL OBJECTIVE FUNCTION ###################
        m.setObjective(sum(t_assign[arc]*preference[arc] for arc in assignment_arc), GRB.MAXIMIZE)

        # update class attr data
        self.model = m
        self.t_assign = t_assign
        self.c_assign = c_assign
        self.time_frames_list = time_frames_list

        return m, t_assign, c_assign, time_frames_list
