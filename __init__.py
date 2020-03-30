# -*- coding: utf-8 -*-
"""
/***************************************************************************
 pozzuolo_martesana
                                 A QGIS plugin
 This plugin allows to manage field data collected at the Pozzuolo Martesana (Milan, Italy) test site
                             -------------------
        begin                : 2019-03-30
        copyright            : (C) 2019 by Giovanna De Filippis - ECHN-Italy
        email                : giovanna.df1989@libero.it
        git sha              : $Format:%H$
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 This script initializes the plugin, making it known to QGIS.
"""


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load pozzuolo_martesana class from file pozzuolo_martesana.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .pozzuolo_martesana import pozzuolo_martesana
    return pozzuolo_martesana(iface)
