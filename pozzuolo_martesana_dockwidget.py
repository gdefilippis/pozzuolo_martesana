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
import sqlite3
import csv
import datetime
from datetime import datetime, timedelta
import numpy as np

import matplotlib
from matplotlib import pyplot
from matplotlib import dates

from reportlab.platypus import SimpleDocTemplate

from PyQt5 import QtGui, QtWidgets, uic
from PyQt5.QtWidgets import QFileDialog, QLabel, QDialogButtonBox, QMessageBox, QApplication, QComboBox
from PyQt5.QtCore import pyqtSignal

from pozzuolo_martesana.write_AquiMod_files import *
from pozzuolo_martesana.write_pdf_report import *
from pozzuolo_martesana.read_AquiMod_files import *

FORM_CLASS, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), 'pozzuolo_martesana_dockwidget_base.ui'))


class pozzuolo_martesanaDockWidget(QtWidgets.QDockWidget, FORM_CLASS):

    closingPlugin = pyqtSignal()

    def __init__(self, parent=None):
        """Constructor."""
        super(pozzuolo_martesanaDockWidget, self).__init__(parent)
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)

        #####################Select the SpatiaLite DB to be updated#####################
        #When clicking the browse_DB button, the loadDB function below is recalled
        self.browse_DB.clicked.connect(self.loadDB)
        #When clicking the browse_tensio button, the loadFile1 function below is recalled
        self.browse_tensio.clicked.connect(self.loadFile1)
        #When clicking the browse_meteo button, the loadFile2 function below is recalled
        self.browse_meteo.clicked.connect(self.loadFile2)
        #When clicking the browse_moist button, the loadFile3 function below is recalled
        self.browse_moist.clicked.connect(self.loadFile3)

        ############################Update the SpatiaLite DB#############################
        #If the 'OK' button of the buttonBox_1 is clicked, the updateDB function below is recalled
        self.buttonBox_1.button(QDialogButtonBox.Ok).clicked.connect(self.updateDB)

        ############################Write AquiMod input files############################
        #The combobox is filled with the items "Giorni" and "Mesi"
        self.combobox.addItems(["Days","Months"])
        #The sim_mode combo box is filled with the items "evaluation" and "calibration"
        self.sim_mode.addItems(["evaluation","calibration"])
        #The obj_function combo box is filled
        self.obj_function.addItems(["Nash-Sutcliffe Efficiency (NSE)","Root Mean Squared Error (RMSE)","Mean Absolute Percentage Error (MAPE)"])
        #If the 'OK' button of the buttonBox_2 is clicked, the AquiMod function below is recalled
        self.buttonBox_2.button(QDialogButtonBox.Ok).clicked.connect(self.AquiMod)

        #################################Write a report##################################
        #When clicking the browse_logo button, the loadLogo function below is recalled
        self.browse_logo.clicked.connect(self.loadLogo)
        #When clicking the browse_img button, the loadImg function below is recalled
        self.browse_img.clicked.connect(self.loadImg)
        #If the 'OK' button of the buttonBox_3 is clicked, the writeReport function below is recalled
        self.buttonBox_3.button(QDialogButtonBox.Ok).clicked.connect(self.writeReport)

    def closeEvent(self, event):
        self.closingPlugin.emit()
        event.accept()


##############################Load the SpatiaLite DB to be updated##############################
##############################  and the files needed to update it ##############################

    def loadDB(self):

        #getOpenFileName is a method of the QFileDialog class which allows to open a dialog window with
        #the heading "Select the SpatiaLite DB to be queried/updated".
        #The argument "" makes this dialog window to open always at the same path, while '*.sqlite' allows
        #to filter sqlite files.
        #The getOpenFileName method returns the sqlite file selected
        #I use self.DB (and not just DB) because I will need this variable in the functions below
        self.DB=QFileDialog.getOpenFileName(self,"Select the SpatiaLite DB to be queried/updated", "", '*.sqlite')

        #The path_DB bar fills with the whole path of the selected sqlite file
        #(setText is a method of the QLabel class which holds the label's text)
        #ATTENTION: self.DB is a tuple like ('path_to_SpatiaLite_DB','*.sqlite').
        #Here, the path_DB bar holds just the first element of this tuple (i.e., 'path_to_SpatiaLite_DB')
        self.path_DB.setText(self.DB[0])

        #Open DB connection and read tables
        self.checkDBPath()


    def loadFile1(self):

        #getOpenFileName is a method of the QFileDialog class which allows to open a dialog window with
        #the heading "Select the file containing measurements taken from tensiometers".
        #The argument "" makes this dialog window to open always at the same path, while '*.dat' allows
        #to filter dat files.
        #The getOpenFileName method returns the dat file selected
        #I use self.tensio (and not just tensio) because I will need this variable in the functions below
        self.tensio=QFileDialog.getOpenFileName(self,"Select the file containing measurements taken from tensiometers", "", '*.dat')

        #The path_tensio bar fills with the whole path of the selected dat file
        #(setText is a method of the QLabel class which holds the label's text)
        #ATTENTION: self.tensio is a tuple like ('path_to_dat_file','*.dat').
        #Here, the path_tensio bar holds just the first element of this tuple (i.e., 'path_to_dat_file')
        self.path_tensio.setText(self.tensio[0])

        #If the path_tensio bar is not empty...
        if len(str(self.path_tensio.text()))!=0:
            #Get a list of headers and lines of the tensio file
            self.tensio_headers,self.tensio_content=self.readDatFiles(self.tensio[0])


    def loadFile2(self):

        #getOpenFileName is a method of the QFileDialog class which allows to open a dialog window with
        #the heading "Select the file containing meteo-climate data".
        #The argument "" makes this dialog window to open always at the same path, while '*.dat' allows
        #to filter dat files.
        #The getOpenFileName method returns the dat file selected
        #I use self.meteo (and not just meteo) because I will need this variable in the functions below
        self.meteo=QFileDialog.getOpenFileName(self,"Select the file containing meteo-climate data", "", '*.dat')

        #The path_meteo bar fills with the whole path of the selected dat file
        #(setText is a method of the QLabel class which holds the label's text)
        #ATTENTION: self.meteo is a tuple like ('path_to_dat_file','*.dat').
        #Here, the path_meteo bar holds just the first element of this tuple (i.e., 'path_to_dat_file')
        self.path_meteo.setText(self.meteo[0])

        #If the path_meteo bar is not empty...
        if len(str(self.path_meteo.text()))!=0:
            #Get a list of headers and lines of the meteo file
            self.meteo_headers,self.meteo_content=self.readDatFiles(self.meteo[0])


    def loadFile3(self):

        #getOpenFileName is a method of the QFileDialog class which allows to open a dialog window with
        #the heading "Select the file containing soil moisture data".
        #The argument "" makes this dialog window to open always at the same path, while '*.txt' allows
        #to filter dat files.
        #The getOpenFileName method returns the txt file selected
        #I use self.moist (and not just moist) because I will need this variable in the functions below
        self.moist=QFileDialog.getOpenFileName(self,"Select the file containing soil moisture data", "", '*.txt')

        #The path_moist bar fills with the whole path of the selected txt file
        #(setText is a method of the QLabel class which holds the label's text)
        #ATTENTION: self.moist is a tuple like ('path_to_txt_file','*.txt').
        #Here, the path_moist bar holds just the first element of this tuple (i.e., 'path_to_txt_file')
        self.path_moist.setText(self.moist[0])

        #If the path_moist bar is not empty...
        if len(str(self.path_moist.text()))!=0:
            #Get a list of headers and lines of the moist file
            self.moist_content=self.readTxtFiles(self.moist[0])


    #The checkDBPath function checks if the path_DB bar is empty or not
    #(no input nor output parameters)
    def checkDBPath(self):

        #If the path_DB bar is empty...
        if len(str(self.path_DB.text()))==0:
            #...then a warning appears
            QMessageBox.warning(self, self.tr('Attention!'), self.tr('You must select the SpatiaLite DB to be queried/updated!'))
            #...and nothing more is done
            return
        #If the path_bar is not empty...
        else:
            #...connect the SpatiaLite DB whose path is read from the path_DB bar
            self.connection = sqlite3.connect(str(self.path_DB.text()))

        #Read all tables to be updated in the SpatiaLite DB just connected
        self.rows_rainfall,self.count_rainfall=self.readTable('select * from rainfall')
        self.rows_meteo,self.count_meteo=self.readTable('select * from meteo_climate')
        self.rows_pressure,self.count_pressure=self.readTable('select * from pore_pressure')
        self.rows_moist,self.count_moist=self.readTable('select * from unsat_props')


    #The readTable function allows to read all tables to be updated in the SpatiaLite DB just connected
    #(input parameters: tablename, i.e., the name of the table to be updated in the SpatiaLite DB)
    #(output parameters: rows, i.e., a list of tuples which is the content of the selected table;
    #                    count, i.e., the number of rows in the selected table)
    def readTable(self,tablename):

        #Access the tablename table in the SpatiaLite DB just connected
        cursor=self.connection.execute(tablename)
        #Read all rows of the tablename table
        #(rows is a list of tuples)
        rows=cursor.fetchall()

        #Count all rows in the tablename table
        count=0
        #row iterates over the rows list
        for row in rows:
            #The count counter is updated
            count=count+1

        return rows,count


    #The readDatFiles function allows to read all lines in the *.dat files and
    #to select the line of headers and the lines of data
    #(input parameters: file, i.e., the path of the *.dat file to be read)
    #(output parameters: headers, i.e., a list of headers in the selected *.dat file;
    #                    lista2, i.e., a list of lists, where each sub-list is a line
    #                    containing data in the selected *.dat file)
    def readDatFiles(self,file):

        content=[]
        #Open the .*dat file just selected
        with open(file) as datfile:
            #DictReader is a class of the csv method which reads a csv file and
            #returns a dictionary whose keys are given by the headers of the fields
            #ATTENTION: in the case of our *.dat files, the headers of the fields are in
            #the second line! The first, the third and the forth lines are to be deleted!
            reader=csv.DictReader(datfile,delimiter=';')
            #row iterates over the rows of the datfile (each row becomes
            #a dictionary, where the keys are the headers in the first line)
            for row in reader:
                #Update the content list
                #ATTENTION: content will be something like:
                #[{first line: second line},{first line: third line},{first line: forth line},{first line: data},{first line: data},...]
                content.append(dict(row))
                #Extract the correct headers from the second line of the datfile
                headers=list(content[0].values())
        #Delete the first three elements from the content list
        #(i.e., {first line: second line}, {first line: third line} and {first line: forth line})
        del content[:3]

        lista=[]
        #d iterates over the dictionaries within the content list
        for d in content:
            #The lista list is updated with the values of
            #these dictionaries within the content list
            #ATTENTION: each element of the lista list will be like: ['2018-06-19 16:30:00,0,0.819,1.126,-1.126,3.719,-1.296,0.307,-0.034,1.945']
            lista.append(list(d.values()))

        lista2=[]
        #l iterates over the lista list
        for l in lista:
            #The lista2 list is updated with l elements, but the strings '2018-06-19 16:30:00,0,0.819,1.126,-1.126,3.719,-1.296,0.307,-0.034,1.945'
            #are splitted by commas. As such, each element of the lista2 list will be like: ['2018-06-19 16:30:00','0','0.819','1.126','-1.126','3.719','-1.296','0.307','-0.034','1.945']
            lista2.append(l[0].split(","))

        #Do the same for the headers list
        headers=headers[0].split(",")

        return headers,lista2


    #The readTxtFiles function allows to read all lines of data in the *.txt file
    #(input parameters: file, i.e., the path of the *.txt file to be read)
    #(output parameters: lista, i.e., a list of lists, where each sub-list is a line
    #                    containing data in the selected *.txt file)
    def readTxtFiles(self,file):

        content=[]
        #Open the .*txt file just selected
        with open(file) as txtfile:
            #DictReader is a class of the csv method which reads a csv file and
            #returns a dictionary whose keys are given by the headers of the fields
            #ATTENTION: in the case of our *.txt files, the headers of the fields
            #are not available!
            reader=csv.DictReader(txtfile,delimiter='\t')
            #row iterates over the rows of the txtfile (each row becomes
            #a dictionary, where the keys are taken from the first line)
            for row in reader:
                #Update the content list
                #ATTENTION: content will be something like:
                #[{first element of the first line: first element of the second line},{second element of the first line: second element of the second line},{third element of the first line: third element of the second line},...,
                #{first element of the first line: first element of the third line},{second element of the first line: second element of the third line},{third element of the first line: third element of the third line},...]
                content.append(dict(row))

        lista=[]
        #x iterates over the dictionaries within the content list
        for x in content:
            #Update the lista list with sub-lists, which are
            #nothing but the lists of values of x dictionaries
            lista.append(list(x.values()))

        return lista


#####################################Update the SpatiaLite DB#####################################

    def updateDB(self):

        self.progressBar_1.setMinimum(0)
        self.progressBar_1.setMaximum(0)
        self.progressBar_1.setValue(0)

        QApplication.processEvents()

        #If the path_DB bar is empty...
        if len(str(self.path_DB.text()))==0:
            #...then a warning appears
            QMessageBox.warning(self, self.tr('Attention!'), self.tr('You must select the SpatiaLite DB to be queried/updated!'))
            #...and nothing more is done
            return

        #If none of the three required files are selected...
        if len(str(self.path_tensio.text()))==0 and len(str(self.path_meteo.text()))==0 and len(str(self.path_moist.text()))==0:
            #...then a warning appears
            QMessageBox.warning(self, self.tr('Attention!'), self.tr('You must select at least one file!'))
            #...and nothing more is done
            return

        #If the path_tensio bar is not empty...
        if len(str(self.path_tensio.text()))!=0:
            #Update the pore_pressure table
            self.update_pore_pressure()

        #If the path_meteo bar is not empty...
        if len(str(self.path_meteo.text()))!=0:
            #Update the rainfall table
            self.update_rainfall()
            #Update the meteo_climate table
            self.update_meteo()

        #If the path_moist bar is not empty...
        if len(str(self.path_moist.text()))!=0:
            #Update the unsat_props table
            self.update_moist()

        self.progressBar_1.setMaximum(100)


    def update_pore_pressure(self):

        #Access the pore_pressure table in the SpatiaLite DB just connected
        cursor = self.connection.execute('select * from pore_pressure')

        #If the pore_pressure table is empty...
        if self.count_pressure==0:
            #id is a row counter
            id=self.count_pressure
            #x iterates over the list tensio_content (x is a list itself)
            for x in self.tensio_content:
                #The id counter is increased by one
                id=id+1
                #A new row is added into the pore_pressure table
                cursor.execute("INSERT INTO pore_pressure VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (str(id), 'T1,T2,T3,T4,T5,T6,T7,T8', x[0], x[2], x[3], x[4], x[5], x[6], x[7], x[8], x[9], x[10], ''))
                #Commit changes
                self.connection.commit()
            #An information window appears once done
            QMessageBox.information(self, self.tr('Information!'), self.tr('Table pore_pressure has been updated!'))

        #If the pore_pressure table has as many rows as the length of the tensio_content list...
        elif len(self.tensio_content)==self.count_pressure:
            #An information window appears
            QMessageBox.information(self, self.tr('Information!'), self.tr('Table pore_pressure is already updated!'))

        #If the tensio_content list has more elements than the rows of the pore_pressure table...
        elif len(self.tensio_content)>self.count_pressure:
            #id is a row counter
            id=self.count_pressure
            #dates is a list of dates already present in the pore_pressure table
            dates=[]
            #row iterates over the rows_pressure list
            #(i.e., row iterates over the rows of the pore_pressure table)
            for row in self.rows_pressure:
                #The dates list is updated
                dates.append(row[2])
            #x iterates over the tensio_content list (x is a list itself)
            for x in self.tensio_content:
                #If a date of the tensio_content list is not in the dates list...
                if x[0] not in dates:
                    #The id counter is increased by one
                    id=id+1
                    #A new row is added into the pore_pressure table
                    cursor.execute("INSERT INTO pore_pressure VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (str(id), 'T1,T2,T3,T4,T5,T6,T7,T8', x[0], x[2], x[3], x[4], x[5], x[6], x[7], x[8], x[9], x[10], ''))
                    #Commit changes
                    self.connection.commit()
            #An information window appears once done
            QMessageBox.information(self, self.tr('Information!'), self.tr('Table pore_pressure has been updated!'))


    def update_rainfall(self):

        #Access the rainfall table in the SpatiaLite DB just connected
        cursor = self.connection.execute('select * from rainfall')

        #If the rainfall table is empty...
        if self.count_rainfall==0:
            #id is a row counter
            id=self.count_rainfall
            #x iterates over the list meteo_content (x is a list itself)
            for x in self.meteo_content:
                #The id counter is increased by one
                id=id+1
                #A new row is added into the rainfall table
                cursor.execute("INSERT INTO rainfall VALUES (?, ?, ?, ?, ?, ?)", (str(id), 'rain gauge', x[0], x[11], x[12], ''))
                #Commit changes
                self.connection.commit()
            #An information window appears once done
            QMessageBox.information(self, self.tr('Information!'), self.tr('Table rainfall has been updated!'))

        #If the rainfall table has as many rows as the length of the meteo_content list...
        elif len(self.meteo_content)==self.count_rainfall:
            #An information window appears
            QMessageBox.information(self, self.tr('Information!'), self.tr('Table rainfall is already updated!'))

        #If the meteo_content list has more elements than the rows of the rainfall table...
        elif len(self.meteo_content)>self.count_rainfall:
            #id is a row counter
            id=self.count_rainfall
            #dates is a list of dates already present in the rainfall table
            dates=[]
            #row iterates over the rows_rainfall list
            #(i.e., row iterates over the rows of the rainfall table)
            for row in self.rows_rainfall:
                #The dates list is updated
                dates.append(row[2])
            #x iterates over the meteo_content list (x is a list itself)
            for x in self.meteo_content:
                #If a date of the meteo_content list is not in the dates list...
                if x[0] not in dates:
                    #The id counter is increased by one
                    id=id+1
                    #A new row is added into the rainfall table
                    cursor.execute("INSERT INTO rainfall VALUES (?, ?, ?, ?, ?, ?)", (str(id), 'rain gauge', x[0], x[11], x[12], ''))
                    #Commit changes
                    self.connection.commit()
            #An information window appears once done
            QMessageBox.information(self, self.tr('Information!'), self.tr('Table rainfall has been updated!'))


    def update_meteo(self):

        #Access the meteo_climate table in the SpatiaLite DB just connected
        cursor = self.connection.execute('select * from meteo_climate')

        #If the meteo_climate table is empty...
        if self.count_meteo==0:
            #id is a row counter
            id=self.count_meteo
            #x iterates over the list meteo_content (x is a list itself)
            for x in self.meteo_content:
                #The id counter is increased by one
                id=id+1
                #A new row is added into the meteo_climate table
                cursor.execute("INSERT INTO meteo_climate VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (str(id), 'weather station', x[0], x[2], x[3], x[4], x[5], x[6], x[7], x[8], x[9], x[10], x[12], ''))
                #Commit changes
                self.connection.commit()
            #An information window appears once done
            QMessageBox.information(self, self.tr('Information!'), self.tr('Table meteo_climate has been updated!'))

        #If the meteo_climate table has as many rows as the length of the meteo_content list...
        elif len(self.meteo_content)==self.count_meteo:
            #An information window appears
            QMessageBox.information(self, self.tr('Information!'), self.tr('Table meteo_climate is already updated!'))

        #If the meteo_content list has more elements than the rows of the meteo_climate table...
        elif len(self.meteo_content)>self.count_meteo:
            #id is a row counter
            id=self.count_meteo
            #dates is a list of dates already present in the meteo_climate table
            dates=[]
            #row iterates over the rows_meteo list
            #(i.e., row iterates over the rows of the meteo_climate table)
            for row in self.rows_meteo:
                #The dates list is updated
                dates.append(row[2])
            #x iterates over the meteo_content list (x is a list itself)
            for x in self.meteo_content:
                #If a date of the meteo_content list is not in the dates list...
                if x[0] not in dates:
                    #The id counter is increased by one
                    id=id+1
                    #A new row is added into the meteo_climate table
                    cursor.execute("INSERT INTO meteo_climate VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (str(id), 'weather station', x[0], x[2], x[3], x[4], x[5], x[6], x[7], x[8], x[9], x[10], x[12], ''))
                    #Commit changes
                    self.connection.commit()
            #An information window appears once done
            QMessageBox.information(self, self.tr('Information!'), self.tr('Table meteo_climate has been updated!'))


    def update_moist(self):

        #Access the unsat_props table in the SpatiaLite DB just connected
        cursor = self.connection.execute('select * from unsat_props')

        #If the unsat_props table is empty...
        if self.count_moist==0:
            #id is a row counter
            id=self.count_moist
            #x iterates over the list moist_content (x is a list itself)
            for x in self.moist_content:
                #The id counter is increased by one
                id=id+1
                #Change the date format (from dd/mm/YYYY hh:mm:ss to YYYY-mm-dd hh:mm:ss)
                date=x[0][6:10]+'-'+x[0][3:5]+'-'+x[0][0:2]+x[0][10:]
                #A new row is added into the unsat_props table
                cursor.execute("INSERT INTO unsat_props VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (str(id), 'TDR_0,TDR_1,TDR_2,TDR_3,TDR_4,TDR_5', date, x[1], x[2], x[3], x[4], x[5], x[6], x[7], x[8], x[9], x[10], x[11], x[12], x[13], x[14], x[15], x[16], x[17], x[18], x[19], ''))
                #Commit changes
                self.connection.commit()
            #An information window appears once done
            QMessageBox.information(self, self.tr('Information!'), self.tr('Table unsat_props has been updated!'))

        #If the unsat_props table has as many rows as the length of the moist_content list...
        elif len(self.moist_content)==self.count_moist:
            #An information window appears
            QMessageBox.information(self, self.tr('Information!'), self.tr('Table unsat_props is already updated!'))

        #If the moist_content list has more elements than the rows of the unsat_props table...
        elif len(self.moist_content)>self.count_moist:
            #id is a row counter
            id=self.count_moist
            #dates is a list of dates already present in the unsat_props table
            dates=[]
            #row iterates over the rows_moist list
            #(i.e., row iterates over the rows of the unsat_props table)
            for row in self.rows_moist:
                #The dates list is updated
                dates.append(row[2])
            #x iterates over the moist_content list (x is a list itself)
            for x in self.moist_content:
                #Change the date format (from dd/mm/YYYY hh:mm:ss to YYYY-mm-dd hh:mm:ss)
                date=x[0][6:10]+'-'+x[0][3:5]+'-'+x[0][0:2]+x[0][10:]
                #If a date of the moist_content list is not in the dates list...
                if date not in dates:
                    #The id counter is increased by one
                    id=id+1
                    #A new row is added into the unsat_props table
                    cursor.execute("INSERT INTO unsat_props VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (str(id), 'TDR_0,TDR_1,TDR_2,TDR_3,TDR_4,TDR_5', date, x[1], x[2], x[3], x[4], x[5], x[6], x[7], x[8], x[9], x[10], x[11], x[12], x[13], x[14], x[15], x[16], x[17], x[18], x[19], ''))
                    #Commit changes
                    self.connection.commit()
            #An information window appears once done
            QMessageBox.information(self, self.tr('Information!'), self.tr('Table unsat_props has been updated!'))


#####################################Write AquiMod input files####################################

    def AquiMod(self):

        self.progressBar_2.setMinimum(0)
        self.progressBar_2.setMaximum(0)
        self.progressBar_2.setValue(0)

        QApplication.processEvents()

        #If the path_DB bar is empty...
        if len(str(self.path_DB.text()))==0:
            #...then a warning appears
            QMessageBox.warning(self, self.tr('Attention!'), self.tr('You must select the SpatiaLite DB containing data needed for the model!'))
            #...and nothing more is done
            return

        #Get the path of the folder where the SpatiaLite DB is located
        #(e.g., in the string 'C:/Users/db_file.sqlite', the string 'C:/Users/' is held)
        #(the rfind method allows to get the index of the last character indicated in parenthesis)
        self.path=self.path_DB.text()
        self.path=self.path[:self.path.rfind('/')+1]

        #Create a subfolder (AquiMod_files) within the folder where the SpatiaLite DB
        #is located (if it does not exist yet, otherwise it is rewritten)
        self.AquiMod_path = self.path+'AquiMod_files/'
        if not os.path.exists(self.AquiMod_path):
            os.makedirs(self.AquiMod_path)

        #Write the Observations.txt file
        error=write_obs(self.connection,self.combobox,self.first,self.last,self.time_step,self.AquiMod_path)

        if error==0:
            #Write the Input.txt file
            write_input(self.AquiMod_path,self.soil_zone,self.unsat_zone,self.sat_zone,self.sim_mode,self.runs,self.obj_function,self.spinup,self.threshold,self.max_models)
        else:
            #An information window appears once done
            QMessageBox.information(self, self.tr('Error!'), self.tr('The time interval you selected contains missing/untrusted rainfall data! The model cannot be run if missing/untrusted rainfall data occur! Please, select a first and last dates of simulation so no missing/untrusted rainfall data occur'))
            return

        #If "evaluation" is selected from the sim_mode combo box...
        if str(self.sim_mode.currentText())=="evaluation":
            #...then write the *_eval.txt files
            write_evaluation(self.AquiMod_path,self.soil_zone,self.field_capacity_min,self.wilting_point_min,self.root_min,self.depletion_min,self.baseflow_min,self.perturb_soil,self.unsat_zone,self.max_ts,self.shape_par_min,self.scale_par_min,self.perturb_unsat,self.sat_zone,self.deltaX,self.SS_min,self.K_min,self.bottom,self.perturb_sat)
        #If "calibration" is selected from the sim_mode combo box...
        elif str(self.sim_mode.currentText())=="calibration":
            #...then write the *_calib.txt files
            write_calibration(self.AquiMod_path,self.soil_zone,self.field_capacity_min,self.field_capacity_max,self.wilting_point_min,self.wilting_point_max,self.root_min,self.root_max,self.depletion_min,self.depletion_max,self.baseflow_min,self.baseflow_max,self.unsat_zone,self.shape_par_min,self.shape_par_max,self.scale_par_min,self.scale_par_max,self.max_ts,self.sat_zone,self.deltaX,self.SS_min,self.SS_max,self.K_min,self.K_max,self.bottom)

        #Create a subfolder (Output) within the subfolder AquiMod_files
        #(if it does not exist yet, otherwise it is rewritten)
        self.output_path = self.AquiMod_path+'Output/'
        if not os.path.exists(self.output_path):
            os.makedirs(self.output_path)

        #An information window appears once done
        QMessageBox.information(self, self.tr('Information!'), self.tr('The files needed to run the AquiMod model have been generated in folder '+self.AquiMod_path+'!'))

        self.progressBar_2.setMaximum(100)


##########################################Write a report##########################################

    def loadLogo(self):

        #getOpenFileName is a method of the QFileDialog class which allows to open a dialog window with
        #the heading "Select the logo".
        #The argument "" makes this dialog window to open always at the same path.
        #The getOpenFileName method returns the file selected
        logo_path=QFileDialog.getOpenFileName(self,"Select the logo", "")

        #The path_logo bar fills with the whole path of the selected file
        #(setText is a method of the QLabel class which holds the label's text)
        #ATTENTION: path_logo is a tuple like ('path_to_logo','All Files (*)').
        #Here, the path_logo bar holds just the first element of this tuple (i.e., 'path_to_logo')
        self.path_logo.setText(logo_path[0])

        #If the path_logo bar is empty...
        if len(str(self.path_logo.text()))==0:
            #...then a warning appears
            QMessageBox.warning(self, self.tr('Attention!'), self.tr('You must select a logo for the report!'))
            #...and nothing more is done
            return


    def loadImg(self):

        #getOpenFileName is a method of the QFileDialog class which allows to open a dialog window with
        #the heading "Select an image".
        #The argument "" makes this dialog window to open always at the same path.
        #The getOpenFileName method returns the file selected
        img_path=QFileDialog.getOpenFileName(self,"Select an image", "")

        #The path_img bar fills with the whole path of the selected file
        #(setText is a method of the QLabel class which holds the label's text)
        #ATTENTION: path_img is a tuple like ('path_to_img','All Files (*)').
        #Here, the path_img bar holds just the first element of this tuple (i.e., 'path_to_img')
        self.path_img.setText(img_path[0])

        #If the path_img bar is empty...
        if len(str(self.path_img.text()))==0:
            #...then a warning appears
            QMessageBox.warning(self, self.tr('Attention!'), self.tr('You must select an image for the report!'))
            #...and nothing more is done
            return


    def writeReport(self):

        self.progressBar_3.setMinimum(0)
        self.progressBar_3.setMaximum(0)
        self.progressBar_3.setValue(0)

        QApplication.processEvents()

        #If the path_DB bar is empty...
        if len(str(self.path_DB.text()))==0:
            #...then a warning appears
            QMessageBox.warning(self, self.tr('Attention!'), self.tr('You must select the SpatiaLite DB to be queried to produce the report!'))
        #If the path_logo bar is empty...
        if len(str(self.path_logo.text()))==0:
            #...then a warning appears
            QMessageBox.warning(self, self.tr('Attention!'), self.tr('You must select a logo for the report!'))
        #If the path_img bar is empty...
        if len(str(self.path_img.text()))==0:
            #...then a warning appears
            QMessageBox.warning(self, self.tr('Attention!'), self.tr('You must select an image for the report!'))

        #Get the path of the folder where the SpatiaLite DB is located
        #(e.g., in the string 'C:/Users/db_file.sqlite', the string 'C:/Users/' is held)
        #(the rfind method allows to get the index of the last character indicated in parenthesis)
        self.path=self.path_DB.text()
        self.path=self.path[:self.path.rfind('/')+1]

        #Create a subfolder (pdf_report) within the folder where the SpatiaLite DB
        #is located (if it does not exist yet, otherwise it is rewritten)
        self.report_path = self.path+'pdf_report/'
        if not os.path.exists(self.report_path):
            os.makedirs(self.report_path)
        #Create a subfolder (plots) within the subfolder pdf_report
        #(if it does not exist yet, otherwise it is rewritten)
        self.plots_path = self.report_path+'plots/'
        if not os.path.exists(self.plots_path):
            os.makedirs(self.plots_path)

        #Save a pdf file in the report_path subfolder
        pdf_report=SimpleDocTemplate(self.report_path+'pozzuolo_martesana.pdf')

        pdf_content=[]

        ###First page of the pdf report###

        #Read logo
        logo=str(self.path_logo.text())

        #Read authors
        #For more than one author...
        if ',' in str(self.authors.text()):
            #...get a list of authors like ['Name Surname (Entity)','Name Surname (Entity)','Name Surname (Entity)']
            authors=str(self.authors.text()).split(', ')
        #For just one author...
        else:
            author=''
            #NOTE: str(self.authors.text()) produces a list whose elements
            #      are single characters of the content of the authors line
            #      edit (e.g., ['N','a','m','e'])
            #letter iterates over such list
            for letter in str(self.authors.text()):
                #The whole sting is composed
                author=author+letter
            #The only string is added as an element to the authors list
            authors=[author]

        #Get the content of the first page of the pdf report
        first=first_page(logo,authors)

        #Add each element of the first list to the pdf_content list
        for x in first:
            pdf_content.append(x)

        ###Section related to the geographical setting###

        #Read image
        image=str(self.path_img.text())

        #Get the content of the section related to the geographical setting of the pdf report
        setting=setting_section(image)

        #Add each element of the setting list to the pdf_content list
        for x in setting:
            pdf_content.append(x)

        ###Section related to climate data (rainfall and air temperature)###

        #Save plot of rainfall values
        rain_dates,rain_values,ax1,rain_min_date,rain_max_date,rain_min_value,rain_max_value,rain_avg_value,rain_sum_value=self.simplePlot(self.rows_rainfall,2,3,4,'Rainfall (mm)')
        #Plot rainfall values with a blue line
        ax1.plot(rain_dates,rain_values,'b',linewidth=2)
        #Save the plot in the plots_path subfolder
        pyplot.savefig(self.plots_path+'rainfall.png')

        #Save plot of temperature values
        temp_dates,temp_values,ax2,temp_min_date,temp_max_date,temp_min_value,temp_max_value,temp_avg_value,temp_sum_value=self.simplePlot(self.rows_meteo,2,3,12,'Average air temperature (°C)')
        #Plot temperature values with dots
        ax2.plot(temp_dates,temp_values,'o',markersize=1)
        #Save the plot in the plots_path subfolder
        pyplot.savefig(self.plots_path+'temperature.png')

        missing_flag_climate='no'
        #Check if missing data occur in the meteo_climate table
        for row in self.rows_meteo:
            if row[12]==0 or row[12]==-1:
                missing_flag_climate='yes'

        #Get the content of the climate section of the pdf report
        climate=climate_section(rain_min_date,rain_max_date,rain_max_value,rain_avg_value,rain_sum_value,self.plots_path+'rainfall.png',temp_min_date,temp_max_date,temp_min_value,temp_max_value,temp_avg_value,temp_sum_value,self.plots_path+'temperature.png',missing_flag_climate)

        #Add each element of the climate list to the pdf_content list
        for x in climate:
            pdf_content.append(x)

        ###Section related to pore pressure###

        #Save statistics for pore pressure values measured by sensor T3
        T3_dates,T3_values,T3_min_date,T3_max_date,T3_min_value,T3_max_value,T3_min_value_date,T3_max_value_date,T3_avg_value=self.getStats(self.rows_pressure,2,5,11)
        #Save statistics for pore pressure values measured by sensor T5
        T5_dates,T5_values,T5_min_date,T5_max_date,T5_min_value,T5_max_value,T5_min_value_date,T5_max_value_date,T5_avg_value=self.getStats(self.rows_pressure,2,7,11)
        #Save statistics for pore pressure values measured by sensor T8
        T8_dates,T8_values,T8_min_date,T8_max_date,T8_min_value,T8_max_value,T8_min_value_date,T8_max_value_date,T8_avg_value=self.getStats(self.rows_pressure,2,10,11)

        #Get a composite plot of pore pressure values and rainfall values
        self.poreCompositePlot(T3_dates,T3_values,T5_values,T8_values,rain_values)

        missing_flag_pressure='no'
        #Check if missing data occur in the pore_pressure table
        for row in self.rows_pressure:
            if row[11]==0 or row[11]==-1:
                missing_flag_pressure='yes'

        #Get the content of the section related to pore pressure data of the pdf report
        pore=pore_section(T3_min_date,T3_max_date,T3_max_value,T3_max_value_date,T5_max_value,T5_max_value_date,T8_max_value,T8_max_value_date,self.plots_path+'pore_pressure.png',missing_flag_pressure)

        #Add each element of the pore list to the pdf_content list
        for x in pore:
            pdf_content.append(x)

        ###Section related to soil moisture###

        #Save statistics for soil moisture values measured by sensor ADD0
        ADD0_dates,ADD0_values,ADD0_min_date,ADD0_max_date,ADD0_min_value,ADD0_max_value,ADD0_min_value_date,ADD0_max_value_date,ADD0_avg_value=self.getStats(self.rows_moist,2,3,21)
        #Save statistics for soil moisture values measured by sensor ADD1
        ADD1_dates,ADD1_values,ADD1_min_date,ADD1_max_date,ADD1_min_value,ADD1_max_value,ADD1_min_value_date,ADD1_max_value_date,ADD1_avg_value=self.getStats(self.rows_moist,2,6,21)
        #Save statistics for soil moisture values measured by sensor ADD2
        ADD2_dates,ADD2_values,ADD2_min_date,ADD2_max_date,ADD2_min_value,ADD2_max_value,ADD2_min_value_date,ADD2_max_value_date,ADD2_avg_value=self.getStats(self.rows_moist,2,9,21)
        #Save statistics for soil moisture values measured by sensor ADD3
        ADD3_dates,ADD3_values,ADD3_min_date,ADD3_max_date,ADD3_min_value,ADD3_max_value,ADD3_min_value_date,ADD3_max_value_date,ADD3_avg_value=self.getStats(self.rows_moist,2,12,21)
        #Save statistics for soil moisture values measured by sensor ADD4
        ADD4_dates,ADD4_values,ADD4_min_date,ADD4_max_date,ADD4_min_value,ADD4_max_value,ADD4_min_value_date,ADD4_max_value_date,ADD4_avg_value=self.getStats(self.rows_moist,2,15,21)
        #Save statistics for soil moisture values measured by sensor ADD5
        ADD5_dates,ADD5_values,ADD5_min_date,ADD5_max_date,ADD5_min_value,ADD5_max_value,ADD5_min_value_date,ADD5_max_value_date,ADD5_avg_value=self.getStats(self.rows_moist,2,18,21)

        #Get two composite plots of soil moisture values and rainfall values
        self.moistCompositePlot(ADD0_dates,ADD0_values,ADD1_values,ADD2_values,"TDR_0 (20 cm below ground surface)","TDR_1 (40 cm below ground surface)","TDR_2 (80 cm below ground surface)",'unsat_props_1.png')
        self.moistCompositePlot(ADD3_dates,ADD3_values,ADD4_values,ADD5_values,"TDR_3 (20 cm below ground surface)","TDR_4 (40 cm below ground surface)","TDR_5 (80 cm below ground surface)",'unsat_props_2.png')

        missing_flag_moist='no'
        #Check if missing data occur in the unsat_props table
        for row in self.rows_moist:
            if row[21]==0 or row[21]==-1:
                missing_flag_moist='yes'

        #Get the content of the section related to soil moisture data of the pdf report
        moisture=moisture_section(ADD0_min_date,ADD0_max_date,ADD0_max_value,ADD0_max_value_date,ADD1_max_value,ADD1_max_value_date,ADD2_max_value,ADD2_max_value_date,ADD3_max_value,ADD3_max_value_date,ADD4_max_value,ADD4_max_value_date,ADD5_max_value,ADD5_max_value_date,self.plots_path+'unsat_props_1.png',self.plots_path+'unsat_props_2.png',missing_flag_moist)

        #Add each element of the moisture list to the pdf_content list
        for x in moisture:
            pdf_content.append(x)

        ###Section related to the AquiMod model###

        #Read the content of the Input.txt file
        simulation_mode,soil_output,unsat_output,sat_output=readInputFile(self.path+'AquiMod_files/Input.txt')

        #Read the content of the Observations.txt file
        obs_dates,rain,pet,gwl,abs,obs_delta=readObsFile(self.path+'AquiMod_files/Observations.txt')

        #Calculate the total rainfall for each time-step
        #(for the first time step the first element of the rain list is used)
        rain_tot=[rain[0]]
        #i iterates over the elements of the rain list, skipping the first one
        for i in range(1,len(rain)):
            #The rain_tot list is updated by multiplying each rain value by the length of the time-step
            rain_tot.append(rain[i]*obs_delta[i])
        #Calculate the total rainfall (mm over the whole simulation)
        rain_tot2=sum(rain_tot)

        #Get the content of the section related to the AquiMod model of the pdf report
        aquimod=aquimod_section(simulation_mode,obs_dates,obs_delta)

        #Add each element of the aquimod list to the pdf_content list
        for x in aquimod:
            pdf_content.append(x)

        #Tranform the path of the Output folder in order to have C:\\path/to/Output/folder
        #(this is needed in order to read correctly the .out files within it)
        path_output=self.path+'AquiMod_files/Output/'
        path_list=list(path_output)
        path_list[2]='\\'
        path_output="".join(path_list)

        #If an output file has been produced for the soil component...
        if soil_output=='Y':
            #Read the content of the FAO_TimeSeries1.out file
            soil_dates,runoff,evap,deficit,rech_soil,soil_delta,soil_tdelta=readSoilFile(path_output)
            #Calculate the total runoff, evaporation and recharge for each time-step
            #(for the first time step the first elements of the runoff, evap and rech_soil lists is used)
            runoff_tot=[runoff[0]]
            evap_tot=[evap[0]]
            rech_soil_tot=[rech_soil[0]]
            #i iterates over the elements of the runoff list, skipping the first one
            for i in range(1,len(runoff)):
                #The runoff_tot, evap_tot and rech_soil_tot lists are updated by multiplying each value by the length of the time-step
                runoff_tot.append(runoff[i]*soil_delta[i])
                evap_tot.append(evap[i]*soil_delta[i])
                rech_soil_tot.append(rech_soil[i]*soil_delta[i])
            #Calculate the total runoff, evaporation and recharge (mm over the whole simulation)
            runoff_tot2=sum(runoff_tot)
            evap_tot2=sum(evap_tot)
            rech_soil_tot2=sum(rech_soil_tot)

            #NOTE: deficit is already expressed in mm over the whole time-steps,
            #so we just need to sum all values to get the deficit over the whole simulation
            deficit_tot=sum(deficit)

            #Save a bar chart with the water budget of the soil component
            self.soilBarChart(rain_tot2,runoff_tot2,evap_tot2,rech_soil_tot2,deficit_tot)

            #Get the content of the section related to the soil component of the pdf report
            soil_component=soil_section(round(rain_tot2,2),round(runoff_tot2,2),round(evap_tot2,2),round(rech_soil_tot2,2),round(deficit_tot,2),soil_tdelta,self.plots_path+'soil_budget.png')

            #Add each element of the soil_component list to the pdf_content list
            for x in soil_component:
                pdf_content.append(x)

        #If an output file has been produced for the unsaturated zone component...
        if unsat_output=='Y':
            #Read the content of the Weibull_TimeSeries1.out file
            unsat_dates,rech_unsat,unsat_delta,unsat_tdelta=readUnsatFile(path_output)
            #Calculate the total recharge for each time-step
            #(for the first time step the first element of the rech_unsat list is used)
            rech_unsat_tot=[rech_unsat[0]]
            #i iterates over the elements of the rech_unsat list, skipping the first one
            for i in range(1,len(rech_unsat)):
                #The rech_unsat_tot list is updated by multiplying each value by the length of the time-step
                rech_unsat_tot.append(rech_unsat[i]*unsat_delta[i])
            #Calculate the total recharge (mm over the whole simulation)
            rech_unsat2=sum(rech_unsat_tot)

            #Save a plot with the values of the rech_unsat list vs rainfall
            self.unsatPlot(unsat_dates,rech_unsat,rain)

            #Get the content of the section related to the unsat component of the pdf report
            unsat_component=unsat_section(round(rech_unsat2,2),unsat_tdelta,self.plots_path+'effective_infiltration.png')

            #Add each element of the unsat_component list to the pdf_content list
            for x in unsat_component:
                pdf_content.append(x)

        #If an output file has been produced for the saturated zone component...
        if sat_output=='Y':
            #Read the content of the Q1K1S1_TimeSeries1.out file
            sat_dates,discharge,gw_level=readSatFile(path_output)

        #Check if the gw_level table containing groundwater level data exists
        exists=1
        connection = sqlite3.connect(str(self.path_DB.text()))
        c = connection.cursor()
        c.execute(''' SELECT count(name) FROM sqlite_master WHERE type='table' AND name='gw_level' ''')
        if c.fetchone()[0]==1:
            exists=1
        else:
            exists=0

        #If the gw_level table does not exist...
        if exists==0:

            #Save a plot with the values of the gw_level simulated
            self.satPlot(sat_dates,gw_level)

            #Get the content of the section related to the sat component of the pdf report
            sat_component=sat_section(gw_level,self.plots_path+'gw_level.png')

        #If the gw_level table exists...
        if exists==1:

            #Save a plot with the values of the gw_level simulated and observed
            self.satCompositePlot(sat_dates,gw_level,gwl)

            #Get the content of the section related to the sat component of the pdf report (including analysis of residuals)
            sat_component=sat_section2(gw_level,gwl,self.plots_path+'gw_level.png')

        #Add each element of the sat_component list to the pdf_content list
        for x in sat_component:
            pdf_content.append(x)

        #Calculate the percentage of missing temperature data for each time-step
        perc={}
        #Manage the dates in the obs_dates list
        new_obs_dates=[]
        #obs_dates is a list of the last dates (in string format) for each time-step
        #First date (i.e., starting date of the model)
        a=datetime.strptime(obs_dates[0], '%d/%m/%Y') #convert date to datetime with format %d/%m/%Y
        b=a.strftime('%Y-%m-%d') #change the format to %Y-%m-%d. The result is a string
        b=datetime.strptime(b, '%Y-%m-%d') ##convert b to datetime with format %Y-%m-%d
        new_obs_dates.append(b)
        #Remaining dates
        for i in range(1,len(obs_dates)):
            a=datetime.strptime(obs_dates[i], '%d/%m/%Y') #convert date to datetime with format %d/%m/%Y
            b=a.strftime('%Y-%m-%d') #change the format to %Y-%m-%d. The result is a string
            b=datetime.strptime(b, '%Y-%m-%d') ##convert b to datetime with format %Y-%m-%d
            b = b.replace(hour=23, minute=59) #set hour and minutes to 23:59
            new_obs_dates.append(b+timedelta(seconds=59)) #add 59 seconds
            #The new date will be datetime with format YYYY-mm-dd hh:mm:ss, where hh:mm:ss=23:59:59,
            #except for the first date of the model, which is YYYY-mm-dd hh:mm, where hh:mm=00:00
        #Calculate the percantage of missing values for the first time-step
        missing=[]
        #row iterates over the list of rows of the meteo_climate table
        for row in self.rows_meteo:
            #If the current row falls within the first time-step...
            if datetime.strptime(row[2],'%Y-%m-%d %H:%M:%S')>=new_obs_dates[0] and datetime.strptime(row[2],'%Y-%m-%d %H:%M:%S')<=new_obs_dates[1]:
                #Check the quality_check flag
                #For missing/untrusted temperature values...
                if row[12]==0 or row[12]==-1:
                    #Add 1 to the missing list
                    missing.append(1)
                #For trusted temperature values...
                else:
                    #Add 0 to the missing list
                    missing.append(0)
        #Count how many 1 (i.e., missing/untrusted data) are present in the list missing
        c=missing.count(1)
        #Calculate the percentage of missing/untrusted values for the current time-step
        p=round((c/len(missing))*100)
        #Update the perc dictionary for the first time-step
        perc[1]=p
        #Calculate the percantage of missing values for the remaining time-steps
        #i iterates over the length of the list new_obs_dates, starting from 1
        for i in range(1,len(new_obs_dates)-1):
            missing=[]
            #row iterates over the list of rows of the meteo_climate table
            for row in self.rows_meteo:
                #If the current row falls within the current time-step...
                if datetime.strptime(row[2],'%Y-%m-%d %H:%M:%S')>new_obs_dates[i] and datetime.strptime(row[2],'%Y-%m-%d %H:%M:%S')<=new_obs_dates[i+1]:
                    #Check the quality_check flag
                    #For missing/untrusted temperature values...
                    if row[12]==0 or row[12]==-1:
                        #Add 1 to the missing list
                        missing.append(1)
                    #For trusted temperature values...
                    else:
                        #Add 0 to the missing list
                        missing.append(0)
            #Count how many 1 (i.e., missing/untrusted data) are present in the list missing
            c=missing.count(1)
            #Calculate the percentage of missing/untrusted values for the current time-step
            p=round((c/len(missing))*100)
            #Update the perc dictionary
            perc[i+1]=p
            #The perc dictionary has the following format: perc={time-step number:percentage of missing/untrusted values, ...}

        #Get the content of the section related to the discussion of the pdf report
        discussion=discussion_section(perc)

        #Add each element of the discussion list to the pdf_content list
        for x in discussion:
            pdf_content.append(x)

        #Build the pdf report
        pdf_report.build(pdf_content)

        #An information window appears once done
        QMessageBox.information(self, self.tr('Information!'), self.tr('The report is ready!'))

        self.progressBar_3.setMaximum(100)


    #The simplePlot function allows to set simple plots with dates
    #on the x axis and values of a certain variable on the y axis
    def simplePlot(self,table,date_col,value_col,quality_check_col,y_label):

        #dates is a list of dates retrieved from the table
        dates=[]
        #values is a list of values of a certain variable retrieved from the table
        values=[]
        #table_content is a dictionary which will help in getting mean daily values of a certain variable
        table_content={}
        #Flag to check if missing values occur
        flag=0
        #row iterates over the list of rows of the table
        for row in table:
            #Edit the date format (from YYYY-mm-dd hh:mm:ss to dd/mm/YYYY)
            d=str(row[date_col]).split(' ', 1)[0] #Get YYYY-mm-dd only
            d=d[8:10]+'/'+d[5:7]+'/'+d[0:4]
            #The dates list is updated (make d a datetime object)
            dates.append(datetime.strptime(d,'%d/%m/%Y'))
            #Check the quality_check value
            if row[quality_check_col]==1:
                #The values list is updated
                values.append(float(row[value_col]))
                #The table_content dictionary is updated
                table_content[str(row[date_col])]=float(row[value_col])
            else:
                #The values list is updated with null value
                values.append(np.nan)
                #The table_content dictionary is updated with null value
                table_content[str(row[date_col])]=np.nan
                #Update the flag
                flag=1

        #Set the x axis of the plot between the minimum and the
        #maximum dates with two-months intervals between ticks
        years=matplotlib.dates.YearLocator(1)
        months=matplotlib.dates.MonthLocator(interval=1)
        #Format of the ticks labels (mm/YYYY)
        dfmt=matplotlib.dates.DateFormatter('%m/%Y')
        #Get the minimum and the maximum dates
        datemin=min(dates)
        datemax=max(dates)
        fig=pyplot.figure()
        ax=fig.add_subplot(111)
        ax.xaxis.set_major_locator(years)
        ax.xaxis.set_major_formatter(dfmt)
        ax.xaxis.set_minor_locator(months)
        ax.xaxis.set_minor_formatter(dfmt)
        ax.set_xlim(datemin,datemax)

        #Label of the y axis
        ax.set_ylabel(y_label)
        #Label of the x axis
        ax.set_xlabel('Time')
        #Avoid overlapping of x ticks
        pyplot.tight_layout()

        #daily_values is a dictionary which stores mean daily values of a certain variable
        daily_values={}

        sum=0.0
        count=0
        sum_value=0.0
        #d iterates over the dates list without duplicates (d is a datetime object)
        for date in list(set(dates)):
            #Convert d to a string (YYYY-mm-dd)
            d=date.strftime('%Y-%m-%d')
            #k and v iterated over keys and values of the table_content dictionary
            for k,v in table_content.items():
                #If the d string is in the k key...
                if d in k:
                    #...then the corresponding v value is added to the sum...
                    sum=sum+v
                    #...and the count counter is increased by one
                    count=count+1
            #The daily_values dictionary is updated
            daily_values[d]=round((sum/count),2)
            #The cumulated rainfall is updated
            sum_value=round(sum_value+sum,2)
            #sum and count are inizialized again
            sum=0.0
            count=0

        #If no missing data occur...
        if flag==0:

            #Extract info for statistics

            #Minimum and maximum dates
            #The following are strings with YYYY-mm-dd format
            min_date=min(list(daily_values.keys()))
            max_date=max(list(daily_values.keys()))
            #Convert minimum and maximum dates to dd/mm/YYYY format
            min_date=min_date[8:10]+'/'+min_date[5:7]+'/'+min_date[0:4]
            max_date=max_date[8:10]+'/'+max_date[5:7]+'/'+max_date[0:4]

            #Minimum and maximum values
            min_value=round(min(list(table_content.values())),2)
            max_value=round(max(list(table_content.values())),2)

            #Average value
            somma=0.0
            cont=0
            for v in list(daily_values.values()):
                somma=somma+v
                cont=cont+1
            avg_value=round((somma/cont),2)

        #If missing data occur...
        else:

            #Minimum and maximum dates
            #The following are strings with YYYY-mm-dd format
            min_date=min(list(daily_values.keys()))
            max_date=max(list(daily_values.keys()))
            #Convert minimum and maximum dates to dd/mm/YYYY format
            min_date=min_date[8:10]+'/'+min_date[5:7]+'/'+min_date[0:4]
            max_date=max_date[8:10]+'/'+max_date[5:7]+'/'+max_date[0:4]

            #All the other statistics are not needed
            min_value=0.0
            max_value=0.0
            avg_value=0.0
            sum_value=0.0

        return dates,values,ax,min_date,max_date,min_value,max_value,avg_value,sum_value


    #The getStats function allows to get data for composite plots
    def getStats(self,table,date_col,value_col,quality_check_col):

        #dates is a list of dates retrieved from the table
        dates=[]
        #values is a list of values of a certain variable retrieved from the table
        values=[]
        #Flag to check if missing values occur
        flag=0
        #row iterates over the list of rows of the table
        for row in table:
            #Edit the date format (from YYYY-mm-dd hh:mm:ss to dd/mm/YYYY)
            d=str(row[date_col]).split(' ', 1)[0] #Get YYYY-mm-dd only
            d=d[8:10]+'/'+d[5:7]+'/'+d[0:4]
            #The dates list is updated (make d a datetime object)
            dates.append(datetime.strptime(d,'%d/%m/%Y'))
            #Check the quality_check value
            if row[quality_check_col]==1:
                #The values list is updated
                values.append(float(row[value_col]))
            else:
                #The values list is updated with null value
                values.append(np.nan)
                #Update the flag
                flag=1

        #table_content is a dictionary which will help in getting mean daily values of a certain variable
        table_content={}

        #row iterates over the list of rows of the table
        for row in table:
            #The table_content dictionary is initiated
            table_content[str(row[date_col]).split(' ', 1)[0]]=[]

        #row iterates over the list of rows of the table
        for row in table:
            #Check the quality_check value
            if row[quality_check_col]==1:
                #The table_content dictionary is updated
                table_content[str(row[date_col]).split(' ', 1)[0]].append(float(row[value_col]))
            else:
                #The table_content dictionary is updated with null value
                table_content[str(row[date_col])]=np.nan
                #Update the flag
                flag=1

        #If no missing data occur...
        if flag==0:

            #Extract info for statistics

            #Minimum and maximum values and corresponding dates
            max_value=0.0
            min_value=0.0
            max_value_date=''
            min_value_date=''
            #v iterates over the list of values of the
            #table_content dictionary (v is a list)
            for v in list(table_content.values()):
                #Get the maximum and minimum values among all the elements of all the v lists
                if max(v)>max_value:
                    max_value=max(v)
                if min(v)<min_value:
                    min_value=min(v)
            #k and v iterate over the keys and values of the table_content dictionary
            for k,v in table_content.items():
                #Get the key (i.e., the date) of the corresponding maximum and minimum values
                if max_value in v:
                    max_value_date=k
                    #Edit the date format (from YYYY-mm-dd to dd/mm/YYYY)
                    max_value_date=max_value_date[8:10]+'/'+max_value_date[5:7]+'/'+max_value_date[0:4]
                if min_value in v:
                    min_value_date=k
                    #Edit the date format (from YYYY-mm-dd to dd/mm/YYYY)
                    min_value_date=min_value_date[8:10]+'/'+min_value_date[5:7]+'/'+min_value_date[0:4]

            #Minimum and maximum dates
            #The following are strings with YYYY-mm-dd format
            min_date=min(list(table_content.keys()))
            max_date=max(list(table_content.keys()))
            #Convert minimum and maximum dates to dd/mm/YYYY format
            min_date=min_date[8:10]+'/'+min_date[5:7]+'/'+min_date[0:4]
            max_date=max_date[8:10]+'/'+max_date[5:7]+'/'+max_date[0:4]

            #Daily values
            daily_values={}
            #k and v iterate over keys and values of the table_content dictionary
            for k,v in table_content.items():
                sum=0.0
                #x iterates over the v list
                for x in v:
                    #sum and is updated
                    sum=sum+x
                #The daily_values dictionary is updated
                daily_values[k]=round((sum/len(v)),2)

            #Average value
            somma=0.0
            #v iterates over the list of values of the daily_values dictionary
            for v in list(daily_values.values()):
                #somma is updated
                somma=somma+v
            avg_value=round((somma/len(list(daily_values.values()))),2)

        #If missing data occur...
        else:

            #Minimum and maximum dates
            #The following are strings with YYYY-mm-dd format
            min_date=min(list(table_content.keys()))
            max_date=max(list(table_content.keys()))
            #Convert minimum and maximum dates to dd/mm/YYYY format
            min_date=min_date[8:10]+'/'+min_date[5:7]+'/'+min_date[0:4]
            max_date=max_date[8:10]+'/'+max_date[5:7]+'/'+max_date[0:4]

            #All the other statistics are not needed
            min_value=0.0
            max_value=0.0
            min_value_date=0.0
            max_value_date=0.0
            avg_value=0.0

        return dates,values,min_date,max_date,min_value,max_value,min_value_date,max_value_date,avg_value


    #The poreCompositePlot function allows to save a composite plot of pore pressure and rainfall
    def poreCompositePlot(self,T3_dates,T3_values,T5_values,T8_values,rain_values):

        #Set the x axis of the plot between the minimum and the
        #maximum dates with two-months intervals between ticks
        years=matplotlib.dates.YearLocator(1)
        months=matplotlib.dates.MonthLocator(interval=1)
        #Format of the ticks labels (mm/YYYY)
        dfmt=matplotlib.dates.DateFormatter('%m/%Y')
        #Get the minimum and the maximum dates
        datemin=min(T3_dates)
        datemax=max(T3_dates)
        fig=pyplot.figure()
        ax=fig.add_subplot(111)
        ax.xaxis.set_major_locator(years)
        ax.xaxis.set_major_formatter(dfmt)
        ax.xaxis.set_minor_locator(months)
        ax.xaxis.set_minor_formatter(dfmt)
        ax.set_xlim(datemin,datemax)

        ax.plot(T3_dates,T3_values,'o',color='blue',markersize=1,label="T3 (40-48 cm below ground surface)")
        ax.plot(T3_dates,T5_values,'o',color='orange',markersize=1,label="T5 (37-45 cm below ground surface)")
        ax.plot(T3_dates,T8_values,'o',color='grey',markersize=1,label="T8 (20-28 cm below ground surface)")
        #Label of the y axis
        ax.set_ylabel('Pore pressure (cBar)')
        #Label of the x axis
        ax.set_xlabel('Time')
        ax.legend(title="Left axis",bbox_to_anchor=(0.2,-0.1),loc="upper center")

        #Composite plot with rainfall values
        ax3=ax.twinx()
        ax3.xaxis.set_major_locator(years)
        ax3.xaxis.set_major_formatter(dfmt)
        ax3.xaxis.set_minor_locator(months)
        ax3.xaxis.set_minor_formatter(dfmt)
        ax3.set_xlim(datemin,datemax)
        ax3.xaxis.set_ticks_position('top')
        ax3.invert_yaxis()

        ax3.plot(T3_dates,rain_values,'r',linewidth=2,label="Rainfall")
        #Label of the y axis
        ax3.set_ylabel('Rainfall (mm)')
        #Label of the x axis
        ax3.set_xlabel('Time')
        ax3.legend(title="Right axis",bbox_to_anchor=(0.6,-0.1),loc="upper center")

        #Avoid overlapping of x ticks
        pyplot.tight_layout()

        #Save the plot in the plots_path subfolder (bbox_inches="tight"
        #is useful so that x labels are not cut off the area of the plot)
        pyplot.savefig(self.plots_path+'pore_pressure.png',bbox_inches="tight")


    #The moistCompositePlot function allows to save a composite plot of soil moisture
    def moistCompositePlot(self,dates,values1,values2,values3,label1,label2,label3,name):

        #Set the x axis of the plot between the minimum and the
        #maximum dates with two-months intervals between ticks
        years=matplotlib.dates.YearLocator(1)
        months=matplotlib.dates.MonthLocator(interval=1)
        #Format of the ticks labels (mm/YYYY)
        dfmt=matplotlib.dates.DateFormatter('%m/%Y')
        #Get the minimum and the maximum dates
        datemin=min(dates)
        datemax=max(dates)
        fig=pyplot.figure()
        ax=fig.add_subplot(111)
        ax.xaxis.set_major_locator(years)
        ax.xaxis.set_major_formatter(dfmt)
        ax.xaxis.set_minor_locator(months)
        ax.xaxis.set_minor_formatter(dfmt)
        ax.set_xlim(datemin,datemax)

        ax.plot(dates,values1,'o',color='blue',markersize=1,label=label1)
        ax.plot(dates,values2,'o',color='orange',markersize=1,label=label2)
        ax.plot(dates,values3,'o',color='grey',markersize=1,label=label3)
        #Label of the y axis
        ax.set_ylabel('Water content (%)')
        #Label of the x axis
        ax.set_xlabel('Time')
        ax.legend(bbox_to_anchor=(0.2,-0.1),loc="upper center")

        #Avoid overlapping of x ticks
        pyplot.tight_layout()

        #Save the plot in the plots_path subfolder (bbox_inches="tight"
        #is useful so that x labels are not cut off the area of the plot)
        pyplot.savefig(self.plots_path+name,bbox_inches="tight")


    #The soilBarChart function allows to save the water budget for the soil component
    def soilBarChart(self,rain_tot2,runoff_tot2,evap_tot2,rech_soil_tot2,deficit_tot):

        x=['Rainfall','Runoff','Evapotranspiration','Percolation',' ','Water deficit']

        negative_data=[0,-runoff_tot2,-evap_tot2,-rech_soil_tot2,0,0]
        positive_data=[rain_tot2,0,0,0,0,deficit_tot]

        fig=pyplot.figure()
        ax=fig.add_subplot(111)

        ax.bar(x,negative_data,width=1,color='b')
        ax.bar(x,positive_data,width=1,color='r')
        #Label of the y axis
        ax.set_ylabel('(mm)')
        #Label of the x axis
        ax.set_xlabel('Budget terms')
        #Set grid for y axis
        ax.yaxis.grid(True)
        #Rotate x labels
        ax.set_xticklabels(x,rotation=45)

        #Save the plot in the plots_path subfolder (bbox_inches="tight"
        #is useful so that x labels are not cut off the area of the plot)
        pyplot.savefig(self.plots_path+'soil_budget',bbox_inches="tight")


    #The unsatPlot function allows to save a composite plot of recharge to the saturated zone and rainfall
    def unsatPlot(self,unsat_dates,rech_unsat,rain):

        #Set the values of the axis
        x_axis1=unsat_dates
        y_axis1=rech_unsat
        y_axis2=rain

        fig=pyplot.figure()
        ax=fig.add_subplot(111)

        #Plot rain values
        ax.plot(x_axis1,y_axis2,'r',label="Rainfall")
        #Plot rech_unsat values
        ax.plot(x_axis1,y_axis1,'b',label="Effective infiltration")

        #Label of the y axis
        ax.set_ylabel('(mm)')
        #Label of the x axis
        ax.set_xlabel('Time')
        #Rotate x labels
        ax.set_xticklabels(x_axis1,rotation=45)
        ax.legend()

        #Save the plot in the plots_path subfolder (bbox_inches="tight"
        #is useful so that x labels are not cut off the area of the plot)
        pyplot.savefig(self.plots_path+'effective_infiltration.png',bbox_inches="tight")


    #The satPlot function allows to save a plot of groundwater level
    def satPlot(self,sat_dates,gw_level):

        #Set the values of the axis
        x_axis1=sat_dates
        y_axis1=gw_level

        fig=pyplot.figure()
        ax=fig.add_subplot(111)

        #Plot gw_level values
        ax.plot(x_axis1,y_axis1,'b')

        #Label of the y axis
        ax.set_ylabel('Groundwater level (m above mean sea level)')
        #Label of the x axis
        ax.set_xlabel('Time')
        #Rotate x labels
        ax.set_xticklabels(x_axis1,rotation=45)
        ax.legend()

        #Save the plot in the plots_path subfolder (bbox_inches="tight"
        #is useful so that x labels are not cut off the area of the plot)
        pyplot.savefig(self.plots_path+'gw_level.png',bbox_inches="tight")


    #The satCompositePlot function allows to save a plot of groundwater level simulated and observed
    def satCompositePlot(self,sat_dates,gw_level,gwl):

        #Set the values of the axis
        x_axis1=sat_dates
        y_axis1=gw_level
        y_axis2=gwl

        fig=pyplot.figure()
        ax=fig.add_subplot(111)

        #Plot gw_level simulated values
        ax.plot(x_axis1,y_axis1,'b',label="Simulated groundwater level")
        #Plot gw_level observed values
        ax.plot(x_axis1,y_axis2,'r',label="Observed groundwater level")

        #Label of the y axis
        ax.set_ylabel('Groundwater level (m above mean sea level)')
        #Label of the x axis
        ax.set_xlabel('Time')
        #Rotate x labels
        ax.set_xticklabels(x_axis1,rotation=45)
        ax.legend()

        #Save the plot in the plots_path subfolder (bbox_inches="tight"
        #is useful so that x labels are not cut off the area of the plot)
        pyplot.savefig(self.plots_path+'gw_level.png',bbox_inches="tight")
