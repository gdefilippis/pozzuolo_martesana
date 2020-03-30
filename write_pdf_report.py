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

from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Image,PageBreak,Table,ListFlowable,ListItem
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_JUSTIFY,TA_CENTER
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

from PyQt5 import QtGui, QtWidgets, uic
from PyQt5.QtWidgets import QFileDialog, QLabel, QDialogButtonBox, QMessageBox, QApplication, QComboBox
from PyQt5.QtCore import pyqtSignal

#The first_page function allows to get the first page of the pdf report
def first_page(logo,authors):

    first_page=[]

    #Add logo
    first_page.append(Image(logo, 8*inch, 3*inch))

    #Add vertical space
    first_page.append(Spacer(1, 50))

    #Set the style
    styles=getSampleStyleSheet()
    styles.add(ParagraphStyle(name='Center', alignment=TA_CENTER, leading=24))

    #Add title
    title='Appendix 1 - Characterization of the monitoring site located in Pozzuolo Martesana (Milan, northern Italy)'
    ptext='<font size=24>%s</font>' %title
    first_page.append(Paragraph(ptext, styles["Center"]))

    #Add vertical space
    first_page.append(Spacer(1, 100))

    #Add authors
    for author in authors:
        ptext='<font size=12>%s</font>' %author
        first_page.append(Paragraph(ptext, styles["Center"]))

    #Add vertical space
    first_page.append(Spacer(1, 30))

    #Add date
    date=datetime.today().strftime('%d/%m/%Y')
    ptext='<font size=12>%s</font>' %date
    first_page.append(Paragraph(ptext, styles["Center"]))

    #Add a page break
    first_page.append(PageBreak())

    return first_page


#The setting_section function allows to get the section
#related to geographical setting
def setting_section(image):

    setting_section=[]

    #Set the style
    styles=getSampleStyleSheet()
    styles.add(ParagraphStyle(name='Justify', alignment=TA_JUSTIFY, leading=24))

    #Add title
    title='Geographical setting'
    ptext='<font size=24>%s</font>' %title
    setting_section.append(Paragraph(ptext, styles["Justify"]))

    #Add vertical space
    setting_section.append(Spacer(1, 30))

    #Add text
    ptext='<font size=12>The monitoring site of Pozzuolo Martesana is located east of Milan and it is managed by CAP Holding S.p.A. . \
        The monitoring site is equipped for the analysis of deposition, infiltration and redistribution of atmospheric contaminants in the unsaturated zone, under the scientific coordination of Università degli Studi di Milano.</font>'
    setting_section.append(Paragraph(ptext, styles["Justify"]))

    #Add text
    ptext='<font size=12>The following figure reports a geological sketch of the study area and a sketch of the instruments installed at the monitoring site.</font>'
    setting_section.append(Paragraph(ptext, styles["Justify"]))

    #Add plot
    img=Image(image, 6*inch, 4*inch)
    setting_section.append(img)

        #Add a page break
    setting_section.append(PageBreak())

    return setting_section


#The climate_section function allows to get the section
#related to climate data (rainfall and temperature)
def climate_section(rain_min_date,rain_max_date,rain_max_value,rain_avg_value,rain_sum_value,rain_plot_path,temp_min_date,temp_max_date,temp_min_value,temp_max_value,temp_avg_value,temp_sum_value,temp_plot_path,missing_flag):

    climate_section=[]

    #Set the style
    styles=getSampleStyleSheet()
    styles.add(ParagraphStyle(name='Justify', alignment=TA_JUSTIFY, leading=24))

    #Add title
    title='Analysis of climate data'
    ptext='<font size=24>%s</font>' %title
    climate_section.append(Paragraph(ptext, styles["Justify"]))

    #Add vertical space
    climate_section.append(Spacer(1, 30))

    #Add text
    ptext='<font size=12>The rainfall gauge station installed in the study area records rainfall values (in mm) with a time frequency of 10\' from %s to %s. \
        In this period, a maximum value of %s mm was recorded and a cumulated value of %s mm over the whole period.</font>' %(rain_min_date,rain_max_date,rain_max_value,rain_sum_value)
    climate_section.append(Paragraph(ptext, styles["Justify"]))

    #Add text
    ptext='<font size=12>The time series of rainfall values recorded by the gauge station is reported in the following plot.</font>'
    climate_section.append(Paragraph(ptext, styles["Justify"]))

    #Add plot
    img=Image(rain_plot_path, 7*inch, 5*inch)
    climate_section.append(img)

    #Add vertical space
    climate_section.append(Spacer(1, 80))

    if missing_flag=='no':
        #Add text
        ptext='<font size=12>The meteorological station installed in the study area records average air temperature (in °C) with a time frequency of 10\' from %s to %s. \
            In this period, a minumum value of %s °C, a maximum value of %s °C, and an average value of %s °C were recorded.</font>' %(temp_min_date,temp_max_date,temp_min_value,temp_max_value,temp_avg_value)
    else:
        #Add text
        ptext='<font size=12>The meteorological station installed in the study area records average air temperature (in °C) with a time frequency of 10\' from %s to %s. \
            In this period, some gaps occur, due to missing or untrusted air temperature values. \
            For the aims of the AquiMod model, such gaps will be filled using linearly interpolated air temperature data. </font>' %(temp_min_date,temp_max_date)
    climate_section.append(Paragraph(ptext, styles["Justify"]))

    #Add text
    ptext='<font size=12>The time series of average air temperature values recorded by the gauge station is reported in the following plot.</font>'
    climate_section.append(Paragraph(ptext, styles["Justify"]))

    #Add plot
    img=Image(temp_plot_path, 7*inch, 5*inch)
    climate_section.append(img)

    #Add a page break
    climate_section.append(PageBreak())

    return climate_section


#The pore_section function allows to get the section
#related to pore pressure data
def pore_section(T3_min_date,T3_max_date,T3_max_value,T3_max_value_date,T5_max_value,T5_max_value_date,T8_max_value,T8_max_value_date,pore_plot_path,missing_flag):

    pore_section=[]

    #Set the style
    styles=getSampleStyleSheet()
    styles.add(ParagraphStyle(name='Justify', alignment=TA_JUSTIFY, leading=24))

    #Add title
    title='Analysis of data recorded by the tensiometers'
    ptext='<font size=24>%s</font>' %title
    pore_section.append(Paragraph(ptext, styles["Justify"]))

    #Add vertical space
    pore_section.append(Spacer(1, 30))

    if missing_flag=='no':
        #Add text
        ptext='<font size=12>The tensiometers installed show soil pore pressure values (in cBar) recorded at different depths with a frequency of 10\' from %s to %s. \
                                Specifically, the tensiometer T3 is installed at a depth of 40-48 cm below the ground surface, the tensiometer T5 is installed at a depth of 37-45 cm below the ground surface and the tensiometer T8 is installed at a depth of 20-28 cm below the ground surface.\
                                In the period considered here, peaks of pore pressures were recorded at different depths.</font>'
    else:
        #Add text
        ptext='<font size=12>The tensiometers installed show soil pore pressure values (in cBar) recorded at different depths with a frequency of 10\' from %s to %s. \
                                Specifically, the tensiometer T3 is installed at a depth of 40-48 cm below the ground surface, the tensiometer T5 is installed at a depth of 37-45 cm below the ground surface and the tensiometer T8 is installed at a depth of 20-28 cm below the ground surface.\
                                In the period considered here, peaks of pore pressures were recorded at different depths.\
                                Furthermore, some gaps occur, due to missing or untrusted pore pressure values.</font>' %(T3_min_date,T3_max_date)
    pore_section.append(Paragraph(ptext, styles["Justify"]))

    #Add text
    ptext='<font size=12>Time series of pore pressure measured by the three sensors are displayed in the following plot, along with the time series of rainfall in the same time period.</font>'
    pore_section.append(Paragraph(ptext, styles["Justify"]))

    #Add plot
    img=Image(pore_plot_path, 7*inch, 5*inch)
    pore_section.append(img)

    #Add a page break
    pore_section.append(PageBreak())

    return pore_section


#The moisture_section function allows to get the section
#related to soil moisture data
def moisture_section(ADD0_min_date,ADD0_max_date,ADD0_max_value,ADD0_max_value_date,ADD1_max_value,ADD1_max_value_date,ADD2_max_value,ADD2_max_value_date,ADD3_max_value,ADD3_max_value_date,ADD4_max_value,ADD4_max_value_date,ADD5_max_value,ADD5_max_value_date,pore_plot1_path,pore_plot2_path,missing_flag):

    moisture_section=[]

    #Set the style
    styles=getSampleStyleSheet()
    styles.add(ParagraphStyle(name='Justify', alignment=TA_JUSTIFY, leading=24))

    #Add title
    title='Analysis of data recorded by soil moisture sensors'
    ptext='<font size=24>%s</font>' %title
    moisture_section.append(Paragraph(ptext, styles["Justify"]))

    #Add vertical space
    moisture_section.append(Spacer(1, 30))

    #Add text
    ptext='<font size=12>The soil moisture sensors installed show values of volumetric water content (in percentage) at different depths with a frequency of 10\' from %s to %s.\
                            Specifically, sensors TDR_0, TDR_1 and TDR_2 are installed at the same point at depths of 20 cm, 40 cm and 80 cm below the ground surface, respectively. Similarly, sensors TDR_3, TDR_4 and TDR_5 are installed at the same point at depths of 20 cm, 40 cm and 80 cm below the ground surface, respectively.</font>' %(ADD0_min_date,ADD0_max_date)
    moisture_section.append(Paragraph(ptext, styles["Justify"]))

    if missing_flag=='no':
        #Add text
        ptext='<font size=12>Regarding sensors TDR_0, TDR_1 and TDR_2, peaks of soil moisture were recorded at different depths.\
                                The TDR_0 sensor recorded a maximum value of %s on %s. The TDR_1 sensor recorded a maximum value of %s on %s. The TDR_2 sensor recorded a maximum value of %s on %s.</font>' %(round(ADD0_max_value,2),ADD0_max_value_date,round(ADD1_max_value,2),ADD1_max_value_date,round(ADD2_max_value,2),ADD2_max_value_date)
    else:
        #Add text
        ptext='<font size=12>Regarding sensors TDR_0, TDR_1 and TDR_2, peaks of soil moisture were recorded at different depths.\
                                Furthermore, some gaps occur in the considered period, due to missing or untrusted pore pressure values.</font>'

    moisture_section.append(Paragraph(ptext, styles["Justify"]))

    #Add text
    ptext='<font size=12>Time series of soil moisture measured in the same time period by these three sensors are displayed in the following plot.</font>'
    moisture_section.append(Paragraph(ptext, styles["Justify"]))

    #Add plot
    img=Image(pore_plot1_path, 7*inch, 5*inch)
    moisture_section.append(img)

    #Add vertical space
    moisture_section.append(Spacer(1, 30))

    if missing_flag=='no':
        #Add text
        ptext='<font size=12>Similarly, sensors TDR_3, TDR_4 and TDR_5 recorded peaks of soil moisture at different depths.\
                                The TDR_3 sensor recorded a maximum value of %s on %s. The TDR_4 sensor recorded a maximum value of %s on %s. The TDR_5 sensor recorded a maximum value of %s on %s.</font>' %(round(ADD3_max_value,2),ADD3_max_value_date,round(ADD4_max_value,2),ADD4_max_value_date,round(ADD5_max_value,2),ADD5_max_value_date)
    else:
        #Add text
        ptext='<font size=12>Similarly, sensors TDR_3, TDR_4 and TDR_5 recorded peaks of soil moisture at different depths.\
                                Also, some gaps occur in the considered period, due to missing or untrusted pore pressure values.</font>'
    moisture_section.append(Paragraph(ptext, styles["Justify"]))

    #Add text
    ptext='<font size=12>Time series of soil moisture measured in the same time period by these three sensors are displayed in the following plot.</font>'
    moisture_section.append(Paragraph(ptext, styles["Justify"]))

    #Add plot
    img=Image(pore_plot2_path, 7*inch, 5*inch)
    moisture_section.append(img)

    #Add a page break
    moisture_section.append(PageBreak())

    return moisture_section


#The aquimod_section function allows to get the section
#related to general settings of the AquiMod model
def aquimod_section(simulation_mode,obs_dates,obs_delta):

    aquimod_section=[]

    #Set the style
    styles=getSampleStyleSheet()
    styles.add(ParagraphStyle(name='Justify', alignment=TA_JUSTIFY, leading=24))

    #Add title
    title='Numerical model'
    ptext='<font size=24>%s</font>' %title
    aquimod_section.append(Paragraph(ptext, styles["Justify"]))

    #Add vertical space
    aquimod_section.append(Spacer(1, 30))

    #Add text
    ptext='<font size=12>In order to model the aquifer within the study area, including the unsaturated zone, the AquiMode code was applied.\
                            The code was run in "%s" mode, in order to obtain an estimate of the water level over the simulation period.\
                            The climate data available were discretized in time, according to the following scheme, starting from 04/02/2019:</font>' %(simulation_mode)
    aquimod_section.append(Paragraph(ptext, styles["Justify"]))

    #data contains all the elements of each row of the time discretization table
    data= [['Time-step','From','To','Length (days)']]
    data.append([1,obs_dates[0],obs_dates[1],obs_delta[1]])
    #i iterates over the length of the obs_dates list minus one
    for i in range(1,len(obs_dates)-1):
        #Update the data list
        day=str(int(obs_dates[i][0:2])+1)
        if len(day)==1:
            day='0'+str(int(obs_dates[i][0:2])+1)
        starting_date=day+obs_dates[i][2:len(obs_dates)+1]
        data.append([i+1,starting_date,obs_dates[i+1],obs_delta[i+1]])
    #Build the table
    t=Table(data)
    aquimod_section.append(t)

    #Add vertical space
    aquimod_section.append(Spacer(1, 50))

    return aquimod_section


#The soil_section function allows to get the section
#related to the water budget of the soil component
def soil_section(rain_tot2,runoff_tot2,evap_tot2,rech_soil_tot2,deficit_tot,soil_tdelta,soil_plot_path):

    soil_section=[]

    #Set the style
    styles=getSampleStyleSheet()
    styles.add(ParagraphStyle(name='Justify', alignment=TA_JUSTIFY, leading=24))

    #Add title
    title='Soil water budget'
    ptext='<font size=24>%s</font>' %title
    soil_section.append(Paragraph(ptext, styles["Justify"]))

    #Add vertical space
    soil_section.append(Spacer(1, 30))

    #Add text
    ptext='<font size=12>The soil water budget includes the following components:</font>'
    soil_section.append(Paragraph(ptext, styles["Justify"]))

    #Bullet list
    budget_components=ListFlowable(
    [
        ListItem(Paragraph("rainfall (inflow term)",styles['Normal'])
                 ,value='circle'
                 ),
        ListItem(Paragraph("runoff (outflow term)",styles['Normal'])
                 ,value='circle'
                 ),
        ListItem(Paragraph("evapotranspiration (outflow term)",styles['Normal'])
                 ,value='circle'
                 ),
        ListItem(Paragraph("percolation to the water table (outflow term)",styles['Normal'])
                 ,value='circle'
                 )
        ],
    bulletType='bullet',
    start='circle'
    )
    soil_section.append(budget_components)

    #Add vertical space
    soil_section.append(Spacer(1, 30))

    #Add text
    ptext='<font size=12>According to model results, over the simulation period (%s days long), the total rainfall was %s mm.\
                            We can also estimate: %s mm of runoff, %s mm of evapotranspiration and %s mm of percolation to the water table.\
                            This results in a water deficit of %s mm.</font>' %(soil_tdelta,rain_tot2,runoff_tot2,evap_tot2,rech_soil_tot2,deficit_tot)
    soil_section.append(Paragraph(ptext, styles["Justify"]))

    #Add plot
    img=Image(soil_plot_path, 7*inch, 5*inch)
    soil_section.append(img)

    #Add vertical space
    soil_section.append(Spacer(1, 30))

    return soil_section


#The unsat_section function allows to get the section
#related to the water budget of the unsat component
def unsat_section(rech_unsat2,unsat_tdelta,unsat_plot_path):

    unsat_section=[]

    #Set the style
    styles=getSampleStyleSheet()
    styles.add(ParagraphStyle(name='Justify', alignment=TA_JUSTIFY, leading=24))

    #Add title
    title='Water balance of the unsaturated zone'
    ptext='<font size=24>%s</font>' %title
    unsat_section.append(Paragraph(ptext, styles["Justify"]))

    #Add vertical space
    unsat_section.append(Spacer(1, 30))

    #Add text
    ptext='<font size=12>According to what was simulated over the whole period (%s days), an overall effective infiltration of %s mm towards the saturated zone was simulated.\
                            The following plot shows the time variation of the simulated effective infiltration, compared to the rainfall.</font>' %(unsat_tdelta,rech_unsat2)
    unsat_section.append(Paragraph(ptext, styles["Justify"]))

    #Add plot
    img=Image(unsat_plot_path, 7*inch, 5*inch)
    unsat_section.append(img)

    #Add vertical space
    unsat_section.append(Spacer(1, 30))

    return unsat_section


#The sat_section function allows to get the section
#related to the simulated hydraulic head
def sat_section(gw_level,sat_plot_path):

    sat_section=[]

    #Set the style
    styles=getSampleStyleSheet()
    styles.add(ParagraphStyle(name='Justify', alignment=TA_JUSTIFY, leading=24))

    #Add title
    title='Simulated hydraulic head'
    ptext='<font size=24>%s</font>' %title
    sat_section.append(Paragraph(ptext, styles["Justify"]))

    #Add vertical space
    sat_section.append(Spacer(1, 30))

    #Add text
    ptext='<font size=12>The simulated hydraulic head ranges between %s m above mean sea level and %s m above mean sea level, during the considered period.\
                            The following plot shows the time variation of the simulated hydraulic head.</font>' %(max(gw_level),min(gw_level))
    sat_section.append(Paragraph(ptext, styles["Justify"]))

    #Add plot
    img=Image(sat_plot_path, 7*inch, 5*inch)
    sat_section.append(img)

    #Add vertical space
    sat_section.append(Spacer(1, 30))

    return sat_section


#The sat_section2 function allows to get the section
#related to the simulated vs observed hydraulic head
def sat_section2(gw_level,gwl,sat_plot_path):

    sat_section=[]

    #Set the style
    styles=getSampleStyleSheet()
    styles.add(ParagraphStyle(name='Justify', alignment=TA_JUSTIFY, leading=24))

    #Add title
    title='Simulated vs observed hydraulic head'
    ptext='<font size=24>%s</font>' %title
    sat_section.append(Paragraph(ptext, styles["Justify"]))

    #Add vertical space
    sat_section.append(Spacer(1, 30))

    #Add text
    ptext='<font size=12>The simulated hydraulic head ranges between %s m above mean sea level and %s m above mean sea level (msl), during the considered period.\
                            The following plot shows the time variation of the simulated vs observed hydraulic head.</font>' %(max(gw_level),min(gw_level))
    sat_section.append(Paragraph(ptext, styles["Justify"]))

    #Add plot
    img=Image(sat_plot_path, 7*inch, 5*inch)
    sat_section.append(img)

    #Add text
    ptext='<font size=12>Here is an analysis of residuals (i.e., simulated minus observed hydraulic head for each time-step).</font>'
    sat_section.append(Paragraph(ptext, styles["Justify"]))

    #data contains all the elements of each row of the residuals table
    data= [['Time-step','Simulated value (m msl)','Observed value (m msl)','Residual (m)']]
    #i iterates over the length of the gw_level list
    for i in range(len(gw_level)):
        #Update the data list
        data.append([i+1,gw_level[i],gwl[i],round(gw_level[i]-gwl[i],2)])
    #Build the table
    t=Table(data)
    sat_section.append(t)

    #Add vertical space
    sat_section.append(Spacer(1, 30))

    return sat_section


#The discussion_section function allows to get the section
#related to the discussion of model error
def discussion_section(perc):

    discussion_section=[]

    #Set the style
    styles=getSampleStyleSheet()
    styles.add(ParagraphStyle(name='Justify', alignment=TA_JUSTIFY, leading=24))

    #Add title
    title='Error percentage'
    ptext='<font size=24>%s</font>' %title
    discussion_section.append(Paragraph(ptext, styles["Justify"]))

    #Add vertical space
    discussion_section.append(Spacer(1, 30))

    #Add text
    ptext='<font size=12>A preliminary evaluation about the error which affects the model results presented in the above sections was made. \
                            Such error was calculated according to the percentage of missing/untrusted air temperature values in the meteo_climate table, for each time-step.</font>'
    discussion_section.append(Paragraph(ptext, styles["Justify"]))

    flag='no'
    #k and v iterate over keys and values of the perc dictionary
    for k,v in perc.items():
        #If missing/untrusted values occur...
        if v!=0:
            flag='yes'
            #Add text
            ptext='<font size=12>The error is worth about %s percent in time-step %s.</font>' %(v,k)
            discussion_section.append(Paragraph(ptext, styles["Justify"]))

    if flag=='yes':
        #Add text
        ptext='<font size=12>It must be noted that this is a preliminary evaluation of the error. A thorough post-processing analysis must be conducted, using more robust uncertainty indicators.</font>'
        discussion_section.append(Paragraph(ptext, styles["Justify"]))
    else:
        #Add text
        ptext='<font size=12>In this application, no missing/untrusted air temperature values occur in the meteo_climate table.</font>'
        discussion_section.append(Paragraph(ptext, styles["Justify"]))

    return discussion_section
