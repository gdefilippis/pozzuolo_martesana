# -*- coding: utf-8 -*-
"""
/***************************************************************************
 pozzuolo_martesanaDockWidget
                                 A QGIS plugin
 This plugin allows to manage field data collected at the Pozzuolo Martesana (Milan, Italy) test site
                             -------------------
        begin                : 2019-03-30
        git sha              : $Format:%H$
        copyright            : (C) 2019 by Giovanna De Filippis - ECHN-Italy
        email                : giovanna.df1989@libero.it
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

import datetime
from datetime import datetime

from PyQt5 import QtGui, QtWidgets, uic
from PyQt5.QtWidgets import QFileDialog, QLabel, QDialogButtonBox, QMessageBox, QApplication, QComboBox
from PyQt5.QtCore import pyqtSignal

#The readInputFile function allows to read the Input.txt file for AquiMod
def readInputFile(path_input_file):

    #Open the Input.txt file
    with open(path_input_file,'r') as input:
        #input_content is a string reporting the content of the Input.txt file
        #(it is a string like 'first_line\nsecond_line\nthird_line\n...')
        input_content=input.read()
    #The full input_content string is splitted when the '\n' character is found
    #(input_lines is a list whose elements are the lines of the Input.txt file)
    input_lines=input_content.split('\n')
    #Read the simulation mode ('e' for evaluation and 'c' for calibration)
    #(fifth line of the Input.txt file and fifth element of the input_lines list)
    simulation_mode=input_lines[4]
    #Read the 23rd line of the Input.txt file (the 23rd element of the input_lines list)
    #(this is a string like 'Y Y Y', where Y means Yes and the three Y indicate that the
    #output files for the soil, unsaturated zone and saturatd zone, respectively, were generated)
    soil_output=input_lines[22][0]
    unsat_output=input_lines[22][2]
    sat_output=input_lines[22][4]

    #Explicit simulation_mode
    if simulation_mode=='e':
        simulation_mode='evaluation'
    if simulation_mode=='c':
        simulation_mode='calibration'

    return simulation_mode,soil_output,unsat_output,sat_output


#The readObsFile function allows to read the Observations.txt file for AquiMod
def readObsFile(path_obs_file):

    obs_dates=[]
    rain=[]
    pet=[]
    gwl=[]
    abs=[]
    #Open the Observations.txt file
    with open(path_obs_file,'r') as obs:
        #Read all rows of this file (all rows will be stored in a unique string
        #with '\n' characters to denote new lines)
        obs_content=obs.read()
    #Transform the obs_content string into a list, whose
    #elements are single lines of the Observations.txt file
    obs_lines=obs_content.split('\n')
    obs_lines2=[]
    #x iterates over the elements of the obs_lines list
    for x in obs_lines:
        #Each line of the Observations.txt file is transformed
        #into a list, whose elements are the single values in that
        #line (each value in a line is separated by a ' ' character)
        obs_lines2.append(x.split(' '))
    #The last empty line is removed from the obs_lines2 list
    obs_lines2.remove([''])
    #i iterates over the obs_lines2 list, skipping the first three elements,
    #which correspond to the first three lines of the Observations.txt file
    for i in range(3,len(obs_lines2)):
        #The soil_dates, rain, pet, gwl and abs lists are updated
        obs_dates.append(obs_lines2[i][0]+'/'+obs_lines2[i][1]+'/'+obs_lines2[i][2])
        rain.append(float(obs_lines2[i][3]))
        pet.append(float(obs_lines2[i][4]))
        gwl.append(float(obs_lines2[i][5]))
        abs.append(float(obs_lines2[i][6]))

	#Get the number of days between a time-step and the following
	#(this will be useful to calculate mean values of rainfall)
    obs_dates2=[]
    #i iterates over elements of the obs_dates list
    for i in range(0,len(obs_dates)):
        #Split obs_dates[i] to get a list like x=['dd','mm','YYYY']
        x=obs_dates[i].split('/')
        #Convert the elements of the obs_date list from strings to datetime objects
        obs_dates2.append(datetime(int(x[2]),int(x[1]),int(x[0])))
        #Convert the date format of obs_dates[i] to dd/mm/YYYY
        #If the date format is d/mm/YYYY or d/m/YYYY...
        if len(x[0])!=2:
            #...the a 0 is added to get 0d/mm/YYYY or 0d/m/YYYY
            x[0]='0'+x[0]
        #If the date format is d/m/YYYY or dd/m/YYYY...
        if len(x[1])!=2:
            #...the a 0 is added to get d/0m/YYYY or dd/0m/YYYY
            x[1]='0'+x[1]
        #Get again the string obs_dates[i] (which is now in the format dd/mm/YYYY)
        obs_dates[i]=x[0]+'/'+x[1]+'/'+x[2]
    #Make the difference between dates in the obs_dates2 list
    #(the first element is 0, i.e., the difference between the first date and itself)
    obs_delta=[0]
    #i iterates over elements of the obs_dates2 list starting from the second date
    for i in range(1,len(obs_dates2)):
        #Calculate the difference between each date and the previous one
        delta=str(obs_dates2[i]-obs_dates2[i-1])
        #Make delta to be like '100' (cut what is after the space), convert to integer and add to the obs_delta list
        obs_delta.append(int(delta.split(' ',1)[0]))


    return obs_dates,rain,pet,gwl,abs,obs_delta


#The readSoilFile function allows to read the FAO_TimeSeries1.out file
def readSoilFile(path_output):

    soil_dates=[]
    runoff=[]
    evap=[]
    deficit=[]
    rech_soil=[]
    #Open the FAO_TimeSeries1.out file
    with open(path_output+'FAO_TimeSeries1.out') as soil_file:
        #Read all rows of this file (all rows will be stored in a unique string
        #with '\n' characters to denote new lines)
        soil_content=soil_file.read()
    #Transform the soil_content string into a list, whose
    #elements are single lines of the FAO_TimeSeries1.out file
    soil_lines=soil_content.split('\n')
    soil_lines2=[]
    #x iterates over the elements of the soil_lines list
    for x in soil_lines:
        #Each line of the FAO_TimeSeries1.out file is transformed
        #into a list, whose elements are the single values in that
        #line (each value in a line is separated by a '\t' character)
        soil_lines2.append(x.split('\t'))
    #The last empty line is removed from the soil_lines2 list
    soil_lines2.remove([''])
    #i iterates over the soil_lines2 list, skipping the first element,
    #which corresponds to the heading of the FAO_TimeSeries1.out file
    for i in range(1,len(soil_lines2)):
        #The last element is removed from each line (this corresponds to an
        #empy space at the end of each line of the FAO_TimeSeries1.out file)
        soil_lines2[i].remove('')
    #i iterates over the soil_lines2 list, skipping the first element,
    #which corresponds to the heading of the FAO_TimeSeries1.out file
    for i in range(1,len(soil_lines2)):
        #The soil_dates, runoff, evap, deficit and rech_soil lists are updated
        soil_dates.append(soil_lines2[i][0]+'/'+soil_lines2[i][1]+'/'+soil_lines2[i][2])
        runoff.append(float(soil_lines2[i][3]))
        evap.append(float(soil_lines2[i][4]))
        deficit.append(float(soil_lines2[i][5]))
        rech_soil.append(float(soil_lines2[i][6]))

    #Get the number of days between a time-step and the following
	#(this will be useful to calculate mean values of runoff,evaporation and recharge)
    soil_dates2=[]
    #i iterates over elements of the soil_dates list
    for i in range(0,len(soil_dates)):
        #Split soil_dates[i] to get a list like x=['dd','mm','YYYY']
        x=soil_dates[i].split('/')
        #Convert the elements of the obs_date list from strings to datetime objects
        soil_dates2.append(datetime(int(x[2]),int(x[1]),int(x[0])))
        #Convert the date format of soil_dates[i] to dd/mm/YYYY
        #If the date format is d/mm/YYYY or d/m/YYYY...
        if len(x[0])!=2:
            #...the a 0 is added to get 0d/mm/YYYY or 0d/m/YYYY
            x[0]='0'+x[0]
        #If the date format is d/m/YYYY or dd/m/YYYY...
        if len(x[1])!=2:
            #...the a 0 is added to get d/0m/YYYY or dd/0m/YYYY
            x[1]='0'+x[1]
        #Get again the string soil_dates[i] (which is now in the format dd/mm/YYYY)
        soil_dates[i]=x[0]+'/'+x[1]+'/'+x[2]
    #Make the difference between dates in the soil_dates2 list
    #(the first element is 0, i.e., the difference between the first date and itself)
    soil_delta=[0]
    #i iterates over elements of the soil_dates2 list starting from the second date
    for i in range(1,len(soil_dates2)):
        #Calculate the difference between each date and the previous one
        delta=str(soil_dates2[i]-soil_dates2[i-1])
        #Make delta to be like '100' (cut what is after the space), convert to integer and add to the soil_delta list
        soil_delta.append(int(delta.split(' ',1)[0]))
    #Calculate the total length of the simulation
    soil_tdelta=sum(soil_delta)

    return soil_dates,runoff,evap,deficit,rech_soil,soil_delta,soil_tdelta


#The readUnsatFile function allows to read the Weibull_TimeSeries1.out file
def readUnsatFile(path_output):

    unsat_dates=[]
    rech_unsat=[]
    #Open the Weibull_TimeSeries1.out file
    with open(path_output+'Weibull_TimeSeries1.out') as unsat_file:
        #Read all rows of this file (all rows will be stored in a unique string
        #with '\n' characters to denote new lines)
        unsat_content=unsat_file.read()
    #Transform the unsat_content string into a list, whose
    #elements are single lines of the Weibull_TimeSeries1.out file
    unsat_lines=unsat_content.split('\n')
    unsat_lines2=[]
    #x iterates over the elements of the unsat_lines list
    for x in unsat_lines:
        #Each line of the Weibull_TimeSeries1.out file is transformed
        #into a list, whose elements are the single values in that
        #line (each value in a line is separated by a '\t' character)
        unsat_lines2.append(x.split('\t'))
    #The last empty line is removed from the unsat_lines2 list
    unsat_lines2.remove([''])
    #i iterates over the unsat_lines2 list, skipping the first element,
    #which corresponds to the heading of the Weibull_TimeSeries1.out file
    for i in range(1,len(unsat_lines2)):
        #The last element is removed from each line (this corresponds to an
        #empy space at the end of each line of the Weibull_TimeSeries1.out file)
        unsat_lines2[i].remove('')
    #i iterates over the unsat_lines2 list, skipping the first element,
    #which corresponds to the heading of the Weibull_TimeSeries1.out file
    for i in range(1,len(unsat_lines2)):
        #The unsat_dates and rech_unsat lists are updated
        unsat_dates.append(unsat_lines2[i][0]+'/'+unsat_lines2[i][1]+'/'+unsat_lines2[i][2])
        rech_unsat.append(float(unsat_lines2[i][3]))

    #Get the number of days between a time-step and the following
	#(this will be useful to calculate mean values of recharge)
    unsat_dates2=[]
    #i iterates over elements of the unsat_dates list
    for i in range(0,len(unsat_dates)):
        #Split unsat_dates[i] to get a list like x=['dd','mm','YYYY']
        x=unsat_dates[i].split('/')
        #Convert the elements of the obs_date list from strings to datetime objects
        unsat_dates2.append(datetime(int(x[2]),int(x[1]),int(x[0])))
        #Convert the date format of unsat_dates[i] to dd/mm/YYYY
        #If the date format is d/mm/YYYY or d/m/YYYY...
        if len(x[0])!=2:
            #...the a 0 is added to get 0d/mm/YYYY or 0d/m/YYYY
            x[0]='0'+x[0]
        #If the date format is d/m/YYYY or dd/m/YYYY...
        if len(x[1])!=2:
            #...the a 0 is added to get d/0m/YYYY or dd/0m/YYYY
            x[1]='0'+x[1]
        #Get again the string unsat_dates[i] (which is now in the format dd/mm/YYYY)
        unsat_dates[i]=x[0]+'/'+x[1]+'/'+x[2]
    #Make the difference between dates in the unsat_dates2 list
    #(the first element is 0, i.e., the difference between the first date and itself)
    unsat_delta=[0]
    #i iterates over elements of the unsat_dates2 list starting from the second date
    for i in range(1,len(unsat_dates2)):
        #Calculate the difference between each date and the previous one
        delta=str(unsat_dates2[i]-unsat_dates2[i-1])
        #Make delta to be like '100' (cut what is after the space), convert to integer and add to the unsat_delta list
        unsat_delta.append(int(delta.split(' ',1)[0]))
    #Calculate the total length of the simulation
    unsat_tdelta=sum(unsat_delta)

    return unsat_dates,rech_unsat,unsat_delta,unsat_tdelta


#The readSatFile function allows to read the Q1K1S1_TimeSeries1.out file
def readSatFile(path_output):

    sat_dates=[]
    discharge=[]
    gw_level=[]
    #Open the Q1K1S1_TimeSeries1.out file
    with open(path_output+'Q1K1S1_TimeSeries1.out') as sat_file:
        #Read all rows of this file (all rows will be stored in a unique string
        #with '\n' characters to denote new lines)
        sat_content=sat_file.read()
    #Transform the sat_content string into a list, whose
    #elements are single lines of the Q1K1S1_TimeSeries1.out file
    sat_lines=sat_content.split('\n')
    sat_lines2=[]
    #x iterates over the elements of the sat_lines list
    for x in sat_lines:
        #Each line of the Q1K1S1_TimeSeries1.out file is transformed
        #into a list, whose elements are the single values in that
        #line (each value in a line is separated by a '\t' character)
        sat_lines2.append(x.split('\t'))
    #The last empty line is removed from the sat_lines2 list
    sat_lines2.remove([''])
    #i iterates over the sat_lines2 list, skipping the first element,
    #which corresponds to the heading of the Q1K1S1_TimeSeries1.out file
    for i in range(1,len(sat_lines2)):
        #The last element is removed from each line (this corresponds to an
        #empy space at the end of each line of the Q1K1S1_TimeSeries1.out file)
        sat_lines2[i].remove('')
    #i iterates over the sat_lines2 list, skipping the first element,
    #which corresponds to the heading of the Q1K1S1_TimeSeries1.out file
    for i in range(1,len(sat_lines2)):
        #The sat_dates, discharge and gw_level lists are updated
        sat_dates.append(sat_lines2[i][0]+'/'+sat_lines2[i][1]+'/'+sat_lines2[i][2])
        discharge.append(float(sat_lines2[i][3]))
        gw_level.append(float(sat_lines2[i][4]))

    #i iterates over elements of the sat_dates list
    for i in range(0,len(sat_dates)):
        #Split sat_dates[i] to get a list like x=['dd','mm','YYYY']
        x=sat_dates[i].split('/')
        #Convert the date format of sat_dates[i] to dd/mm/YYYY
        #If the date format is d/mm/YYYY or d/m/YYYY...
        if len(x[0])!=2:
            #...the a 0 is added to get 0d/mm/YYYY or 0d/m/YYYY
            x[0]='0'+x[0]
        #If the date format is d/m/YYYY or dd/m/YYYY...
        if len(x[1])!=2:
            #...the a 0 is added to get d/0m/YYYY or dd/0m/YYYY
            x[1]='0'+x[1]
        #Get again the string sat_dates[i] (which is now in the format dd/mm/YYYY)
        sat_dates[i]=x[0]+'/'+x[1]+'/'+x[2]

    return sat_dates,discharge,gw_level
