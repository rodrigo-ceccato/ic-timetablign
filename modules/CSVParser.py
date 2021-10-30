#!/usr/bin/env python
# coding: utf-8

# # First, we import all the raw data

# In[136]:


import pandas as pd
from datetime import datetime as dtime

courses_df = pd.read_csv("input/disciplinas")

courses_tf_df = pd.read_csv("input/horarios_disciplinas",  na_filter=False)

assignment_arc_df = pd.read_csv("input/preferencias")


# ## Get teachers list

# In[137]:


# get the list of all teachers
# since the header has no name, we will index it by
# its location (column 0)
teachers_column = list(assignment_arc_df.iloc[:,0])

# now we remove repetitions
teachers_list = list(set(teachers_column))

print(teachers_list)


# ## Get courses list

# In[138]:


# trim whitespace
courses_list = [c.strip() for c in list(courses_df.iloc[:,0])]
print(courses_list)


# In[139]:


def raw_tf_to_time_slot_tuple(raw_string):
    # time-slot for the whole week
    # each day has 6 time-slots
    week_slots = [0] * (6 * 7)
    
    # this generator removes empity items
    raw_slots = (x for x in raw_string.split(" ") if x)
    
    # gets the week slot for each raw_slot
    for tslot in raw_slots:
        slot_info = tslot.split(":")
                
        # specific to this data notation
        week_day   = int(slot_info[0]) - 1 # so Sunday = 0
        hour_value = slot_info[1]
        
        hour_to_slot_dict = {
            '8': int(0),
            '08': int(0),
            '9': int(0),
            '09': int(0),
            
            '10': int(1),
            '11': int(1),
            
            '14': int(2),
            '15': int(2),
            
            '16': int(3),
            '17': int(3),
            
            '19': int(4),
            '20': int(4),
            
            '21': int(5),
            '22': int(5),
        }
        
        hour_slot = hour_to_slot_dict[hour_value]
        
        slot_index = (week_day * 6) + hour_slot # since Sunday = 0
        
        week_slots[slot_index] = 1
        
        #print(f"h={hour_value} wd={week_day} -> slot={slot_index}") # debug only

    
    # starts at monday, ends at saturday (12pm)
    trimmed_slots = week_slots[6:38]
    
    return tuple(trimmed_slots)
 
    
# get list of courses name and time-frame strings
courses_tf_name_list = [c.strip()  for c  in list(courses_tf_df.iloc[:,0])]
raw_tf_list          = [tf.strip() for tf in list(courses_tf_df.iloc[:,1])]


courses_tf_tuple_list = []
for i in range(len(courses_tf_name_list)):
    curr_course_name = courses_tf_name_list[i]
    curr_raw_tf      = raw_tf_list[i]
        
    parsed_tf = raw_tf_to_time_slot_tuple(curr_raw_tf)
    
    courses_tf_tuple_list.append((curr_course_name, [parsed_tf]))
    

course_tf_dict = {c : tfs for (c, tfs) in courses_tf_tuple_list}
for item in course_tf_dict.items():
    print(item)


# ## Get preference arc

# In[140]:


from gurobipy import * # to use multidicts

# list each column of the dataframe
t = assignment_arc_df.iloc[:,0]
c = assignment_arc_df.iloc[:,1]
p = assignment_arc_df.iloc[:,2]

# (teacher, course) : preference_value
assignment_arc_dict = {(t[i],c[i]) : p[i] for i in range(len(assignment_arc_df))}

for item in assignment_arc_dict.items():
    print(item)


# ### Check the information and give the user some warnings

# In[141]:


# get every list of courses
# idealy, they are equal

a = [c for (t,c),p in assignment_arc_dict.items()]
b = [item[0] for item in courses_tf_tuple_list]

id_name = {0 : "preference", 1 : "time-frame-list"}

for index,lists in enumerate([a,b]):
    for item in lists:
        if item not in courses_list:
            print(f"WARNING: {item} in {id_name[index]}, but not in course list")
            
            for c in courses_list:
                if item in c:
                    print(f"    Maybe you meant {c}?")
        

print("Course list: ")
print(courses_list)


# ## Build our model info dictionary

# In[142]:


modelData = {}
modelData['teachers'] = teachers_list
modelData['courses'] = courses_list
modelData['assignmentArcs'] = assignment_arc_dict
modelData['courseTimeSlot'] = course_tf_dict


# dummy data (not on set yet)
modelData['teacherForbiddenTimeSlot'] = {t : [0]*32 for t in teachers_list}
modelData['teacherMaxCredit'] = {t : 200 for t in teachers_list}
modelData['teacherMinCredit'] = {t :   1 for t in teachers_list}
modelData['courseCredits']    = {t :   1 for t in courses_list}


# In[144]:


for item in modelData.items():
    print(item)
    print()
def getModelData():
    return modelData

