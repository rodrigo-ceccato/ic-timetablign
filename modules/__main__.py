#!usr/bin/python3.7
from gurobipy import *

import gui
import modelBuilder
import CSVParser

# load initial data from CSV
modelData = CSVParser.getModelData()

# instanciate a model mananger
mManager = modelBuilder.modelManager(modelData)
mManager.getModel()
mManager.callSolver()
mManager.exportSolution()
mManager.exportPreferenceResult()

# pass model manager to GUI module
#windowMananger = gui.windowMananger(mManager)
