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

import os
import csv
import datetime
from datetime import datetime
from dateutil.relativedelta import relativedelta

from PyQt5 import QtGui, QtWidgets, uic
from PyQt5.QtWidgets import QFileDialog, QLabel, QDialogButtonBox, QMessageBox, QApplication, QComboBox
from PyQt5.QtCore import pyqtSignal

from pozzuolo_martesana.utils import *

#The write_obs function allows to get time series of rain, potential evapotranspiration,
#groundwater level and groundwater abstraction rate, and to write the Observations.txt file
def write_obs(connection,combobox,first_date,last_date,time_step,AquiMod_path):

    #Access the rainfall table in the SpatiaLite DB just connected
    cursor = connection.execute('select * from rainfall')

    #Read all rows of the rainfall table
    #(rows is a list of tuples)
    rows=cursor.fetchall()

    #Get the first and the last days
    first=first_date.date()
    first_day=first.toString('yyyy-MM-dd')
    last=last_date.date()
    last_day=last.toString('yyyy-MM-dd')

    dates=[]
    #row iterates over the rows list
    for row in rows:
        #The model will start from first_day and will end in the last_day
        if str(row[2]).split(" ")[0]>=first_day and str(row[2]).split(" ")[0]<=last_day:
            #Update the dates list with the content of the third column (date_time).
            #Here, the date only is stored in the dates list
            dates.append(str(row[2]).split(" ")[0])

    #Remove duplicates from the dates list and sort the resulting list
    dates=sorted(list(set(dates)))

    #The ts_intervals dictionary contains starting and lasting dates
    #of the time-steps. It will be like:
    #{integer number:starting/lasting date of the time_step,...}
    ts_intervals={0:datetime.strptime(dates[0],'%Y-%m-%d')}

    #Time-step counter
    count=0
    #Inizialize date
    date=datetime.strptime(dates[0],'%Y-%m-%d')
    #While the current date is before the last day of the time series...
    while date<datetime.strptime(dates[-1],'%Y-%m-%d'):
        #If "Days" is selected from the combobox...
        if str(combobox.currentText())=="Days":
            #...then date is updated by summing the input number of days
            date=date+relativedelta(days=int(str(time_step.text())))
        #If "Months" is selected from the combobox...
        elif str(combobox.currentText())=="Months":
            #...then date is updated by summing the input number of months
            date=date+relativedelta(months=int(str(time_step.text())))
        #The time-step counter is increased by one
        count=count+1
        #date is updated
        date=date
        #If date is before the last day of the time series...
        if date<datetime.strptime(dates[-1],'%Y-%m-%d'):
            #...then the ts_intervals dictionary is updated
            ts_intervals[count]=date

    #ATTENTION: the last date in the ts_intervals dictionary could not correspond to the last day in the dates list.
    #In order to avoid this, the last day in the dates list is added in the ts_intervals dictionary

    #If the last element of the ts_intervals dictionary is not equal to the last day in the dates list...
    if ts_intervals[len(ts_intervals)-1] is not datetime.strptime(dates[-1],'%Y-%m-%d'):
        #...then the the last day in the dates list + 1 day is added as last element in the ts_intervals dictionary
        #NOTE: 1 day is added, in order the last day in the dates list to be taken into account in the following calculations
        ts_intervals[len(ts_intervals)]=datetime.strptime(dates[-1],'%Y-%m-%d')+relativedelta(days=1)

    #Get lasting dates of each time-step interval

    #The dates_series dictionary will be like:
    #{time-step number:lasting date of the time-step,...}
    dates_series={}
    #i iterates over the elements of the ts_intervals dictionary,
    #except for the last element
    for i in range(0,len(ts_intervals)-1):
        #The dates_series dictionary is updated with the elements of the ts_intervals dictionary
        dates_series[i]=ts_intervals[i]
    #The last element of the dates_series dictionary must be the last day in the dates list
    dates_series[len(ts_intervals)-1]=datetime.strptime(dates[-1],'%Y-%m-%d')

    #Get time series of rain, potential evapotranspiration, gw level and gw abstraction

    #error allows to check if rainfall data lack or are untrusted
    #(if so, the User must select a different time interval for the model)
    error=0
    for row in rows:
        if datetime.strptime(str(row[2]).split(" ")[0],'%Y-%m-%d')>=dates_series[0] and datetime.strptime(str(row[2]).split(" ")[0],'%Y-%m-%d')<=dates_series[len(dates_series)-1]:
            if row[4]==0 or row[4]==-1:
                error=1

    #rows is a list of tuples
    #Here, rows is converted to a list of lists
    rows2=[]
    for row in rows:
        rows2.append(list(row))

    #Sort the inner lists by the date_time field
    rows=sorted(rows2, key = lambda x: x[2])

    rain_series={}
    #First element of rain_series (i.e., the first date)
    rain=[]
    #row iterates over the rows list
    for row in rows:
        if datetime.strptime(str(row[2]).split(" ")[0],'%Y-%m-%d')==dates_series[0]:
            rain.append(float(row[3]))
    rain_series[0]=sum(rain) #NOTE: the value we measure each 10 minutes is a cumulated rain value, so sum(rain) is the daily rainfall

    #Remaining elements
    for i in range(1,len(dates_series)):
        rain=[]
        #row iterates over the rows list
        for row in rows:
            if datetime.strptime(str(row[2]).split(" ")[0],'%Y-%m-%d')>dates_series[i-1] and datetime.strptime(str(row[2]).split(" ")[0],'%Y-%m-%d')<=dates_series[i]:
                rain.append(float(row[3]))
        #If "Days" is selected from the combobox...
        if str(combobox.currentText())=="Days":
            rain_series[i]=sum(rain)/int((dates_series[i]-dates_series[i-1]).days) #NOTE: the value we measure each 10 minutes is a cumulated rain value, so sum(rain) is the daily rainfall
        #If "Months" is selected from the combobox...
        elif str(combobox.currentText())=="Months":
            rain_series[i]=sum(rain)/int(((dates_series[i]-dates_series[i-1]).days)/30) #NOTE: the value we measure each 10 minutes is a cumulated rain value, so sum(rain) is the daily rainfall

    #Potential evapotranspiration is calculated according to the Thornthwaite equation

    #Access the meteo_climate table in the SpatiaLite DB just connected
    cursor2 = connection.execute('select * from meteo_climate')

    #Read all rows of the meteo_climate table
    #(rows2 is a list of tuples)
    rows2=cursor2.fetchall()

    #Check quality_check and perform linear interpolation if missing data occur
    rows2=manage_rows('meteo_climate',rows2,2,3,12)

    pet_series={}
    temp_series={}
    #First element of temp_series and pet_series (i.e., the first date)
    temp=[]
    #row iterates over the rows2 list
    for row in rows2:
        if datetime.strptime(str(row[2]).split(" ")[0],'%Y-%m-%d')==dates_series[0]:
            temp.append(float(row[3]))
    temp_series[0]=sum(temp)/len(temp)
    I=(temp_series[0]/5)**1.514
    a=0.000000675*(I**3)-0.0000771*(I**2)+0.01792*I+0.493
    l=(8/12)*(30/30) #Assumed 8 h of solar radiation, 30 days per month
    pet_series[0]=16*(((10*temp_series[0])/I)**a)*l #This is mm/month
    pet_series[0]=pet_series[0]/30 #This is mm/day

    #Remaining elements
    for i in range(1,len(dates_series)):
        temp=[]
        #row iterates over the rows2 list
        for row in rows2:
            if datetime.strptime(str(row[2]).split(" ")[0],'%Y-%m-%d')>dates_series[i-1] and datetime.strptime(str(row[2]).split(" ")[0],'%Y-%m-%d')<=dates_series[i]:
                temp.append(float(row[3]))
        temp_series[i]=sum(temp)/len(temp)
        I=(temp_series[i]/5)**1.514
        a=0.000000675*(I**3)-0.0000771*(I**2)+0.01792*I+0.493
        l=(8/12)*(30/30) #Assumed 8 h of solar radiation, 30 days per month
        pet_series[i]=16*(((10*temp_series[i])/I)**a)*l #This is mm/month
        pet_series[i]=pet_series[i]/30 #This is mm/day

    #Groundwater level data

    #Check if the gw_level table containing groundwater level data exists
    #(If yes, it must contain the following fields: ID | sensor_name | date_time | gw_level | quality_check | notes)
    exists=1
    c = connection.cursor()
    c.execute(''' SELECT count(name) FROM sqlite_master WHERE type='table' AND name='gw_level' ''')
    if c.fetchone()[0]==1:
        exists=1
    else:
        exists=0

    #If the gw_level table does not exist...
    if exists==0:
        #...then create a time-series with -9999 except for the first value (this is required by AquiMod)
        gw_series={}
        gw_series[0]=117
        for i in range(1,len(dates_series)):
            gw_series[i]=-9999

    #If the gw_level table exists...
    if exists==1:

        #Access the gw_level table in the SpatiaLite DB just connected
        cursor3 = connection.execute('select * from gw_level')

        #Read all rows of the gw_level table
        #(rows3 is a list of tuples)
        rows3=cursor3.fetchall()

        #Check quality_check and perform linear interpolation if missing data occur
        rows3=manage_rows('gw_level',rows3,2,3,4)

        gw_series={}
        #First element of gw_series (i.e., the first date)
        gw=[]
        #row iterates over the rows3 list
        for row in rows3:
            if datetime.strptime(str(row[2]).split(" ")[0],'%Y-%m-%d')==dates_series[0]:
                gw.append(float(row[3]))
        gw_series[0]=sum(gw)/len(gw)

        #Remaining elements
        for i in range(1,len(dates_series)):
            gw=[]
            #row iterates over the rows3 list
            for row in rows3:
                if datetime.strptime(str(row[2]).split(" ")[0],'%Y-%m-%d')>dates_series[i-1] and datetime.strptime(str(row[2]).split(" ")[0],'%Y-%m-%d')<=dates_series[i]:
                    gw.append(float(row[3]))
            gw_series[i]=sum(gw)/len(gw)

    #Abstraction data

    #Check if the abstraction table containing abstraction data exists
    #(If yes, it must contain the following fields: ID | sensor_name | date_time | abs | quality_check | notes)
    exists2=1
    c = connection.cursor()
    c.execute(''' SELECT count(name) FROM sqlite_master WHERE type='table' AND name='abstraction' ''')
    if c.fetchone()[0]==1:
        exists2=1
    else:
        exists2=0

    #If the abstraction table does not exist...
    if exists2==0:
        #...then create a time-series with 0.0 (this is required by AquiMod)
        abs_series={}
        for i in range(0,len(dates_series)):
            abs_series[i]=0.0

    #If the abstraction table exists...
    if exists2==1:

        #Access the abstraction table in the SpatiaLite DB just connected
        cursor4 = connection.execute('select * from abstraction')

        #Read all rows of the abstraction table
        #(rows4 is a list of tuples)
        rows4=cursor4.fetchall()

        #Check quality_check and perform linear interpolation if missing data occur
        rows4=manage_rows('abstraction',rows4,2,3,4)

        abs_series={}
        #First element of abs_series (i.e., the first date)
        ab=[]
        #row iterates over the rows4 list
        for row in rows4:
            if datetime.strptime(str(row[2]).split(" ")[0],'%Y-%m-%d')==dates_series[0]:
                ab.append(float(row[3]))
        abs_series[0]=sum(ab)/len(ab)

        #Remaining elements
        for i in range(1,len(dates_series)):
            ab=[]
            #row iterates over the rows4 list
            for row in rows4:
                if datetime.strptime(str(row[2]).split(" ")[0],'%Y-%m-%d')>dates_series[i-1] and datetime.strptime(str(row[2]).split(" ")[0],'%Y-%m-%d')<=dates_series[i]:
                    ab.append(float(row[3]))
            abs_series[i]=sum(ab)/len(ab)

    #Write the Observations.txt file

    #Create the Observations.txt file in the AquiMod_files sub-folder
    with open(AquiMod_path+'Observations.txt', 'w', newline='') as obs:
        obs_file=csv.writer(obs, delimiter=' ')
        #Add the first row
        obs_file.writerow(['NUMBER','OF','OBSERVATIONS'])
        #Add the second row
        obs_file.writerow([len(dates_series)])
        #Add the third row
        obs_file.writerow(['DAY','MONTH','YEAR','RAIN','PET','GWL','ABS'])
        #Add all the other rows
        for i in range(0,len(dates_series)):
            obs_file.writerow([str(dates_series[i].day),str(dates_series[i].month),str(dates_series[i].year),str(rain_series[i]),str(pet_series[i]),str(gw_series[i]),str(abs_series[i])])

    return error


#The write_input function allows to write the Input.txt file
def write_input(AquiMod_path,soil_zone,unsat_zone,sat_zone,sim_mode,runs,obj_function,spinup,threshold,max_models):

    #Create the Input.txt file in the AquiMod_files sub-folder
    with open(AquiMod_path+'Input.txt', 'w', newline='') as input:
        input_file=csv.writer(input, delimiter=' ')
        #Add the first row
        input_file.writerow(['Component','IDs'])

        #Second/last row
        if soil_zone.isChecked():
            soil_ID=1
            soil_output='Y'
        else:
            soil_ID=0
            soil_output='N'
        if unsat_zone.isChecked():
            unsat_ID=1
            unsat_output='Y'
        else:
            unsat_ID=0
            unsat_output='N'
        if sat_zone.isChecked():
            sat_ID=3
            sat_output='Y'
        else:
            sat_ID=0
            sat_output='N'

        #Add the second row
        input_file.writerow([soil_ID,unsat_ID,sat_ID])
        #Blank line
        input_file.writerow([])
        #Add the forth row
        input_file.writerow(['Simulation','mode'])
        #Add the fifth row
        #If "evaluation" is selected from the sim_mode combo box...
        if str(sim_mode.currentText())=="evaluation":
            input_file.writerow(['e'])
        #If "calibration" is selected from the sim_mode combo box...
        elif str(sim_mode.currentText())=="calibration":
            input_file.writerow(['c'])
        #Blank line
        input_file.writerow([])

        #Add all the other rows
        input_file.writerow(['Number','of','runs'])
        input_file.writerow([str(runs.text())])
        #Blank line
        input_file.writerow([])
        input_file.writerow(['Objective','function'])
        #If "Nash-Sutcliffe Efficiency (NSE)" is selected from the obj_function combo box...
        if str(obj_function.currentText())=="Nash-Sutcliffe Efficiency (NSE)":
            input_file.writerow(['1'])
        #If "Root Mean Squared Error (RMSE)" is selected from the obj_function combo box...
        elif str(obj_function.currentText())=="Root Mean Squared Error (RMSE)":
            input_file.writerow(['2'])
        #If "Mean Absolute Percentage Error (MAPE)" is selected from the obj_function combo box...
        elif str(obj_function.currentText())=="Mean Absolute Percentage Error (MAPE)":
            input_file.writerow(['3'])
        #Blank line
        input_file.writerow([])
        input_file.writerow(['Spin-up','period'])
        input_file.writerow([str(spinup.text())])
        #Blank line
        input_file.writerow([])
        input_file.writerow(['Acceptable','model','threshold','(calibration','only)'])
        input_file.writerow([str(threshold.text())])
        #Blank line
        input_file.writerow([])
        input_file.writerow(['Maximum','number','of','acceptable','models','(calibration','only)'])
        input_file.writerow([str(max_models.text())])
        #Blank line
        input_file.writerow([])

        #Add the last two rows
        input_file.writerow(['Write','model','output','files'])
        input_file.writerow([soil_output,unsat_output,sat_output])


#The write_evaluation function allows to write the *_eval.txt file
def write_evaluation(AquiMod_path,soil_zone,field_capacity_min,wilting_point_min,root_min,depletion_min,baseflow_min,perturb_soil,unsat_zone,max_ts,shape_par_min,scale_par_min,perturb_unsat,sat_zone,deltaX,SS_min,K_min,bottom,perturb_sat):

    #Create a subfolder (Evaluation) within the subfolder AquiMod_files
    #(if it does not exist yet, otherwise it is rewritten)
    eval_path = AquiMod_path+'Evaluation/'
    if not os.path.exists(eval_path):
        os.makedirs(eval_path)

    if soil_zone.isChecked():
        #Create the FAO_eval.txt file in the Evaluation sub-folder
        with open(eval_path+'FAO_eval.txt', 'w', newline='') as FAO_eval:
            FAO_eval_file=csv.writer(FAO_eval, delimiter=' ')
            #Add the first row
            FAO_eval_file.writerow(['FieldCapacity(-)','WiltingPoint(-)','MaxRootDepth(mm)','DepletionFactor(-)','BaseflowIndex(-)'])
            #Add all the other rows
            #ATTENTION: the min value only is read for each parameter!
            #           Each parameter will be perturbed by the perturbation amount defined by the User!
            field_capacity=float(field_capacity_min.text())
            wilting_point=float(wilting_point_min.text())
            root=float(root_min.text())
            depletion=float(depletion_min.text())
            baseflow=float(baseflow_min.text())
            FAO_eval_file.writerow([str(field_capacity),str(wilting_point),str(root),str(depletion),str(baseflow)])
            perturb_soil=int(perturb_soil.text())/100
            FAO_eval_file.writerow([str(field_capacity+(field_capacity*perturb_soil)),str(wilting_point),str(root),str(depletion),str(baseflow)])
            FAO_eval_file.writerow([str(field_capacity-(field_capacity*perturb_soil)),str(wilting_point),str(root),str(depletion),str(baseflow)])
            FAO_eval_file.writerow([str(field_capacity),str(wilting_point+(wilting_point*perturb_soil)),str(root),str(depletion),str(baseflow)])
            FAO_eval_file.writerow([str(field_capacity),str(wilting_point-(wilting_point*perturb_soil)),str(root),str(depletion),str(baseflow)])
            FAO_eval_file.writerow([str(field_capacity),str(wilting_point),str(root+(root*perturb_soil)),str(depletion),str(baseflow)])
            FAO_eval_file.writerow([str(field_capacity),str(wilting_point),str(root-(root*perturb_soil)),str(depletion),str(baseflow)])
            FAO_eval_file.writerow([str(field_capacity),str(wilting_point),str(root),str(depletion+(depletion*perturb_soil)),str(baseflow)])
            FAO_eval_file.writerow([str(field_capacity),str(wilting_point),str(root),str(depletion-(depletion*perturb_soil)),str(baseflow)])
            FAO_eval_file.writerow([str(field_capacity),str(wilting_point),str(root),str(depletion),str(baseflow+(baseflow*perturb_soil))])
            FAO_eval_file.writerow([str(field_capacity),str(wilting_point),str(root),str(depletion),str(baseflow-(baseflow*perturb_soil))])

    if unsat_zone.isChecked():
        #Create the Weibull_eval.txt file in the Evaluation sub-folder
        with open(eval_path+'Weibull_eval.txt', 'w', newline='') as Weibull_eval:
            Weibull_eval_file=csv.writer(Weibull_eval, delimiter=' ')
            #Add the first row
            Weibull_eval_file.writerow(['k(-)','lambda(-)','n(timesteps)'])
            #Add all the other rows
            #ATTENTION: the min value only is read for each parameter (except max_ts)!
            #           Each parameter (except max_ts) will be perturbed by the perturbation amount defined by the User!
            max_ts=int(max_ts.text())
            shape=float(shape_par_min.text())
            scale=float(scale_par_min.text())
            Weibull_eval_file.writerow([str(shape),str(scale),str(max_ts)])
            perturb_unsat=int(perturb_unsat.text())/100
            Weibull_eval_file.writerow([str(shape+(shape*perturb_unsat)),str(scale),str(max_ts)])
            Weibull_eval_file.writerow([str(shape-(shape*perturb_unsat)),str(scale),str(max_ts)])
            Weibull_eval_file.writerow([str(shape),str(scale+(scale*perturb_unsat)),str(max_ts)])
            Weibull_eval_file.writerow([str(shape),str(scale-(scale*perturb_unsat)),str(max_ts)])

    if sat_zone.isChecked():
        #Create the Q1K1S1_eval.txt file in the Evaluation sub-folder
        with open(eval_path+'Q1K1S1_eval.txt', 'w', newline='') as Q1K1S1_eval:
            Q1K1S1_eval_file=csv.writer(Q1K1S1_eval, delimiter=' ')
            #Add the first row
            Q1K1S1_eval_file.writerow(['Aquifer','Length(m)','SpecificYield(%)','K1(m/day)','z1(m)','Alpha(-)'])
            #Add all the other rows
            #ATTENTION: the min value only is read for each parameter (except deltaX and bottom)!
            #           Each parameter (except deltaX and bottom) will be perturbed by the perturbation amount defined by the User!
            deltaX=float(deltaX.text())
            SS=float(SS_min.text())
            K=float(K_min.text())
            bottom=float(bottom.text())
            Q1K1S1_eval_file.writerow([str(deltaX),str(SS),str(K),str(bottom),'1'])
            perturb_sat=int(perturb_sat.text())/100
            Q1K1S1_eval_file.writerow([str(deltaX),str(SS+(SS*perturb_sat)),str(K),str(bottom),'1'])
            Q1K1S1_eval_file.writerow([str(deltaX),str(SS-(SS*perturb_sat)),str(K),str(bottom),'1'])
            Q1K1S1_eval_file.writerow([str(deltaX),str(SS),str(K+(K*perturb_sat)),str(bottom),'1'])
            Q1K1S1_eval_file.writerow([str(deltaX),str(SS),str(K-(K*perturb_sat)),str(bottom),'1'])


#The write_calibration function allows to write the *_calib.txt file
def write_calibration(AquiMod_path,soil_zone,field_capacity_min,field_capacity_max,wilting_point_min,wilting_point_max,root_min,root_max,depletion_min,depletion_max,baseflow_min,baseflow_max,unsat_zone,shape_par_min,shape_par_max,scale_par_min,scale_par_max,max_ts,sat_zone,deltaX,SS_min,SS_max,K_min,K_max,bottom):

    #Create a subfolder (Calibration) within the subfolder AquiMod_files
    #(if it does not exist yet, otherwise it is rewritten)
    calib_path = AquiMod_path+'Calibration/'
    if not os.path.exists(calib_path):
        os.makedirs(calib_path)

    if soil_zone.isChecked():
        #Create the FAO_calib.txt file in the Calibration sub-folder
        with open(calib_path+'FAO_calib.txt', 'w', newline='') as FAO_calib:
            FAO_calib_file=csv.writer(FAO_calib, delimiter=' ')
            #Add all the needed rows
            FAO_calib_file.writerow(['Field','Capacity(-)'])
            FAO_calib_file.writerow([str(field_capacity_min.text()),str(field_capacity_max.text())])
            #Blank line
            FAO_calib_file.writerow([])
            FAO_calib_file.writerow(['Wilting','Point(-)'])
            FAO_calib_file.writerow([str(wilting_point_min.text()),str(wilting_point_max.text())])
            #Blank line
            FAO_calib_file.writerow([])
            FAO_calib_file.writerow(['Root','Depth(mm)'])
            FAO_calib_file.writerow([str(root_min.text()),str(root_max.text())])
            #Blank line
            FAO_calib_file.writerow([])
            FAO_calib_file.writerow(['Depletion','Factor(-)'])
            FAO_calib_file.writerow([str(depletion_min.text()),str(depletion_max.text())])
            #Blank line
            FAO_calib_file.writerow([])
            FAO_calib_file.writerow(['Baseflow','index(-)'])
            FAO_calib_file.writerow([str(baseflow_min.text()),str(baseflow_max.text())])

    if unsat_zone.isChecked():
        #Create the Weibull_calib.txt file in the Calibration sub-folder
        with open(calib_path+'Weibull_calib.txt', 'w', newline='') as Weibull_calib:
            Weibull_calib_file=csv.writer(Weibull_calib, delimiter=' ')
            #Add all the needed rows
            Weibull_calib_file.writerow(['k(-)'])
            Weibull_calib_file.writerow([str(shape_par_min.text()),str(shape_par_max.text())])
            #Blank line
            Weibull_calib_file.writerow([])
            Weibull_calib_file.writerow(['lambda(-)'])
            Weibull_calib_file.writerow([str(scale_par_min.text()),str(scale_par_max.text())])
            #Blank line
            Weibull_calib_file.writerow([])
            Weibull_calib_file.writerow(['n(timsteps)'])
            Weibull_calib_file.writerow([str(max_ts.text()),str(max_ts.text())])

    if sat_zone.isChecked():
        #Create the Q1K1S1_calib.txt file in the Calibration sub-folder
        with open(calib_path+'Q1K1S1_calib.txt', 'w', newline='') as Q1K1S1_calib:
            Q1K1S1_calib_file=csv.writer(Q1K1S1_calib, delimiter=' ')
            #Add all the needed rows
            Q1K1S1_calib_file.writerow(['Aquifer','Length(m)'])
            Q1K1S1_calib_file.writerow([str(deltaX.text()),str(deltaX.text())])
            #Blank line
            Q1K1S1_calib_file.writerow([])
            Q1K1S1_calib_file.writerow(['Specific','Yield(%)'])
            Q1K1S1_calib_file.writerow([str(SS_min.text()),str(SS_max.text())])
            #Blank line
            Q1K1S1_calib_file.writerow([])
            Q1K1S1_calib_file.writerow(['K1(m/day)'])
            Q1K1S1_calib_file.writerow([str(K_min.text()),str(K_max.text())])
            #Blank line
            Q1K1S1_calib_file.writerow([])
            Q1K1S1_calib_file.writerow(['z1(m)'])
            Q1K1S1_calib_file.writerow([str(bottom.text()),str(bottom.text())])
            #Blank line
            Q1K1S1_calib_file.writerow([])
            Q1K1S1_calib_file.writerow(['Alpha(-)'])
            Q1K1S1_calib_file.writerow(['1','1'])
