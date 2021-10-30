#!usr/bin/python3.7
from functools import partial # build function wrappers
import modelBuilder
import tkinter as tk
from tkinter import *

def create_window(root):
    window = tk.Toplevel(root)

def drawTeacherInfo(aFrame, aTeacher, aModel, aRoot, mManager):
    currentTeacherCourses = aModel.teachers_dict[aTeacher]['courses']
    listFrame = Frame(aFrame)
    listFrame.grid(column=0,row=1)
    Label(aFrame, text=aTeacher).grid(column=0,row=0)

    scrollbar = Scrollbar(listFrame)
    scrollbar.pack(side = RIGHT)
    mylist = Listbox(listFrame, yscrollcommand = scrollbar.set )
    for c in currentTeacherCourses:
        prefLevel = mManager.modelData['assignmentArcs'][(aTeacher, c)]
        mylist.insert(END, (c + f'({prefLevel})'))

    mylist.pack( side = LEFT, fill = BOTH )
    scrollbar.config( command = mylist.yview )

    buttonFrame = Frame(aFrame)
    buttonFrame.grid(column=0,row=2)
    Button(buttonFrame, text="Force", command = lambda: mManager.lockTeacherToCourse(aTeacher,'dummy')).grid(row=0,column=0)
    Button(buttonFrame, text="Add", command = lambda: addCourse(aTeacher, aModel, mylist, aRoot)).grid(row=0,column=1)
    Button(buttonFrame, text="Remove", command = lambda: mManager.removeTeacherCourseArc(aTeacher,mylist.get(ACTIVE))).grid(row=0,column=2)

def addCourse(aTeacher, aModel, mylist, aRoot):
    window = tk.Toplevel(aRoot)
    currentTeacherCourses = aModel.teachers_dict[aTeacher]['courses']
    print(currentTeacherCourses)
    coursesToBeAdded = [c for c in aModel.getAllCourses() if c not in currentTeacherCourses]

    scrollbar = Scrollbar(window)
    scrollbar.pack(side = RIGHT)
    mylist = Listbox(window, yscrollcommand = scrollbar.set )
    for c in coursesToBeAdded:
        mylist.insert(END, c)

    mylist.pack( side = LEFT, fill = BOTH )
    scrollbar.config( command = mylist.yview )

def drawTimeTable(aFrame, aTeacher, aModel, aRoot, mManager):
    currentTeacherCourses = aModel.teachers_dict[aTeacher]['courses']
    courses_time_slot = aModel.courses_time_slot

    #names dictionary
    weekDayName = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado']
    timeSlotName = ['08h00', '10h00', '14h00', '16h00', '19h00', '21h00']

    timeNameFrame = Frame(aFrame)
    for j,timeName in enumerate(timeSlotName):
        Button(timeNameFrame, text=timeName, state=DISABLED).grid(column=0)
    timeNameFrame.grid(row=1,column=0)

    for i,weekName in enumerate(weekDayName):
        tk.Label(aFrame, text=weekName, borderwidth=1).grid(row=0,column=i+1)
        timeUseFrame = Frame(aFrame)

        for j,timeName in enumerate(timeSlotName):
            avaliability = '-     -'
            
            # TODO: refactor modelData acedd
            index = i*(len(timeSlotName)) + j

            # no teaching at saturdays
            if index >= 32:
                avaliability = '-xxxxx-'

            else:
                curr_forbidden_slot = mManager.modelData['teacherForbiddenTimeSlot'][aTeacher]
                is_forbidden_slot = curr_forbidden_slot[index]

                if is_forbidden_slot is 1:
                    avaliability = '-xxxxx-'
            
            

            for course in currentTeacherCourses:
                index = i*(len(timeSlotName)) + j
                if courses_time_slot[course][index] == 1:
                    avaliability = course

            create_window_wrapper = partial(create_window, aRoot)
            Button(timeUseFrame, text=avaliability, width=10, command=create_window_wrapper).grid(row=j, column=0)
            Label(timeUseFrame, text='  '        ).grid(row=j, column=1)

        timeUseFrame.grid(row=1,column=i+1)


class windowMananger():
    def __init__(self, mManager):
        print('Starting window mananger...')
        self.mManager = mManager
        self.solvedModel = modelInfo()

        # solve ILP model
        self.mManager.getModel()
        self.mManager.callSolver()

        self.addData(mManager.modelData, mManager.t_assign, mManager.c_assign, mManager.time_frames_list)

        # display solved model
        self.show()

    def show(self):
        buildMainWindow(self.mManager, self.solvedModel, self)

    def addData(self, modelData, assigned, c_assign, course_tf):
        print("Receving new data...")
        solvedModel = self.solvedModel.addData(modelData, assigned, c_assign, course_tf)

    def rebuildMainWindow(self, root):
        root.destroy()
        print('Re-solving model...')
        self.mManager.callSolver()
        self.addData(self.mManager.modelData, self.mManager.t_assign, self.mManager.c_assign, self.mManager.time_frames_list)
        buildMainWindow(self.mManager, self.solvedModel, self)

class modelInfo():
    def __init__(self):
        print("modelInfo instanciated...");

    def getTeachers(self):
        return list(self.teachers_dict.keys())

    def getAllCourses(self):
        return list(self.courses_time_slot.keys())

    def addData(self, modelData, assigned, c_assign, course_tf):
        print('Updating modelData...')
        self.teachers_dict = {}
        for t in modelData['teachers']:
            t_courses = [c for (assigned_t,c),modelVar in assigned.items() if assigned_t == t and modelVar.getAttr("x") > 0.5]
            self.teachers_dict[t] = dict({
                'name' : t,
                'courses' : t_courses
            })
        
        assigned_tf = {c:tf for (c,tf),value in c_assign.items() if value.getAttr("X") > 0.5}

        self.courses_time_slot = {c: course_tf[assigned_tf[c]] for c in modelData['courses']}

        # add saturday non-used times
        unused_slots = [0] * 4
        for course in self.courses_time_slot.keys():
            time_list = list(self.courses_time_slot[course])
            time_list.extend(unused_slots)
            self.courses_time_slot[course] = tuple(time_list)

class Scrollable(tk.Frame):
    def __init__(self, root):
        tk.Frame.__init__(self, root)
        self.canvas = tk.Canvas(root, borderwidth=0)
        self.frame = tk.Frame(self.canvas)
        self.vsb = tk.Scrollbar(root, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.vsb.set)

        self.vsb.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        self.canvas.create_window((4,4), window=self.frame, anchor="nw",
                                  tags="self.frame")

        self.frame.bind("<Configure>", self.onFrameConfigure)

    def onFrameConfigure(self, event):
        '''Reset the scroll region to encompass the inner frame'''
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))


def buildMainWindow(mManager, solvedModel, windowMananger):
    # creats window root
    root=tk.Tk()
    root.resizable(False, True)
    root.geometry('1080x600')

    # creates window base structure
    # ---------------------------------------
    # -                                     -
    # -   MAIN REGION                       -
    # -                                     -
    # -                                     -
    # -                                     -
    # ---------------------------------------
    # -   MENU BAR                          -
    # -                                     -
    # ---------------------------------------
    mainRegion = tk.Frame(root)
    mainRegion.pack(side=TOP,fill=BOTH,expand=True)
    menuBar = tk.Frame(root)
    menuBar.pack(side=BOTTOM)

    # place buttons on MENU BAR
    # -                                     -
    # ---------------------------------------
    # -   MENU BAR                          -
    # - [RERUN] [CONF.] [DIFF] [EXPORT]     -
    # ---------------------------------------

    rebuildWrapper = partial(windowMananger.rebuildMainWindow, root)
    Button(menuBar, text="Re-Run Solver", command = rebuildWrapper).grid(row=0,column=0)
    Button(menuBar, text="Show Conflicts").grid(row=0,column=1)
    Button(menuBar, text="Show DIFF").grid(row=0,column=2)
    Button(menuBar, text="Export Result").grid(row=0,column=3)


    # place main scrollable area
    # ---------------------------------------
    # -   MAIN REGION                   [X] -
    # -                                 [X] -
    # -                                 [X] -
    # -         scrollbar ---->         [ ] -
    # -                                 [ ] -
    # ---------------------------------------
    # -                                     -
    scrollableMainRegion = Scrollable(mainRegion)
    scrollableMainRegion.pack(side="top", fill="both", expand=True)

    # creates information cards, placed *inside* the MAIN REGION
    # MAIN REGION:
    # ---------------------------------------
    # - ______________________________  [X] -
    # - |     INFORMATION CARD       |  [X] -
    # - |     PLACEMENT              |  [X] -
    # - |                            |  [ ] -
    # - |____________________________|  [ ] -
    # ---------------------------------------

    # Card frame is splited in two:
    # - ______________________________      -
    # - | card    |  card            |      -
    # - | left    |  right           |      -
    # - | frame   |  frame           |      -
    # - |_________|__________________|      -

    for i,teacher in enumerate(solvedModel.getTeachers()):
        # creates this teacher interactive card
        currentCard = Frame(scrollableMainRegion.frame, pady=20)
        currentCard.grid(row=i, column=0)

        # creates and places the left and right side
        leftSide = Frame(currentCard)
        leftSide.grid(row=0, column=0)
        rightSide = Frame(currentCard)
        rightSide.grid(row=0, column=1)

        drawTimeTable(rightSide, teacher, solvedModel, root, mManager)
        drawTeacherInfo(leftSide, teacher, solvedModel, root, mManager)

    root.mainloop()

