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

#The manage_rows function allows to check if missing data occur in a table
#(if so, linear interpolation is performed to fill the gap.
#NOTE: the missing value cannot be the first nor the last one in the table!)
def manage_rows(table,rows,datetime_field_index,value_field_index,quality_field_index):

    #rows is a list of tuples
    #Here, rows is converted to a list of lists
    rows2=[]
    for row in rows:
        rows2.append(list(row))

    #Sort the inner lists by the date_time field
    rows=sorted(rows2, key = lambda x: x[datetime_field_index])

    first_value=[]
    from_date=[]
    last_value=[]
    to_date=[]

    #i iterates over the length of the rows list, skipping the first and last inner lists
    for i in range(1,len(rows)-1):
        #Establish the known value and date right before the gaps
        if rows[i-1][quality_field_index]==1 and rows[i][quality_field_index]==0:
            first_value.append(rows[i-1][value_field_index])
            date1=rows[i-1][datetime_field_index]
            from_date.append(datetime.strptime(date1,'%Y-%m-%d %H:%M:%S'))
        if rows[i-1][quality_field_index]==1 and rows[i][quality_field_index]==-1:
            first_value.append(rows[i-1][value_field_index])
            date1=rows[i-1][datetime_field_index]
            from_date.append(datetime.strptime(date1,'%Y-%m-%d %H:%M:%S'))

    #i iterates over the length of the rows list, skipping the first and last inner lists
    for i in range(1,len(rows)-1):
        #Establish the known value and date right after the gaps
        if rows[i][quality_field_index]==0 and rows[i+1][quality_field_index]==1:
            last_value.append(rows[i+1][value_field_index])
            date2=rows[i+1][datetime_field_index]
            to_date.append(datetime.strptime(date2,'%Y-%m-%d %H:%M:%S'))
        if rows[i][quality_field_index]==-1 and rows[i+1][quality_field_index]==1:
            last_value.append(rows[i+1][value_field_index])
            date2=rows[i+1][datetime_field_index]
            to_date.append(datetime.strptime(date2,'%Y-%m-%d %H:%M:%S'))

    for j in range(len(from_date)):
        #i iterates over the length of the rows list, skipping the first and last inner lists
        for i in range(1,len(rows)-1):
            #Perform the linear interpolation for the missing/untrusted value
            if rows[i][quality_field_index]==0 or rows[i][quality_field_index]==-1:
                this_date=datetime.strptime(rows[i][datetime_field_index],'%Y-%m-%d %H:%M:%S')
                if rows[i-1][quality_field_index]==1:
                    #Calculate the difference (in minutes) between the date of the first missing value and the from_date
                    #NOTE: when the difference between two datetime objects is calculated, days and seconds are provided.
                    #      As such, here we convert the days and seconds in minutes
                    diff_dates2=(this_date-from_date[j]).days*1440+(this_date-from_date[j]).seconds/60
                if this_date>=from_date[j] and this_date<=to_date[j]:
                    #Calculate the difference between known values
                    diff_values=last_value[j]-first_value[j]
                    #Calculate the difference (in minutes) between the corresponding dates
                    #NOTE: when the difference between two datetime objects is calculated, days and seconds are provided.
                    #      As such, here we convert the days and seconds in minutes
                    diff_dates=(to_date[j]-from_date[j]).days*1440+(to_date[j]-from_date[j]).seconds/60
                    #Calculate the interpolated value
                    if diff_values==0.0:
                        rows[i][value_field_index]=rows[i-1][value_field_index]
                    else:
                        rows[i][value_field_index]=rows[i-1][value_field_index]+((diff_values/diff_dates)*diff_dates2)

    return rows
