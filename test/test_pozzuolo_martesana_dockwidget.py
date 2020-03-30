# coding=utf-8
"""DockWidget test.

.. note:: This program is free software; you can redistribute it and/or modify
     it under the terms of the GNU General Public License as published by
     the Free Software Foundation; either version 2 of the License, or
     (at your option) any later version.

"""

__author__ = 'giovanna.df1989@libero.it'
__date__ = '2019-03-30'
__copyright__ = 'Copyright 2019, Giovanna De Filippis - ECHN-Italy'

import unittest

from PyQt5.QtGui import QDockWidget

from pozzuolo_martesana_dockwidget import pozzuolo_martesanaDockWidget

from utilities import get_qgis_app

QGIS_APP = get_qgis_app()


class pozzuolo_martesanaDockWidgetTest(unittest.TestCase):
    """Test dockwidget works."""

    def setUp(self):
        """Runs before each test."""
        self.dockwidget = pozzuolo_martesanaDockWidget(None)

    def tearDown(self):
        """Runs after each test."""
        self.dockwidget = None

    def test_dockwidget_ok(self):
        """Test we can click OK."""
        pass

if __name__ == "__main__":
    suite = unittest.makeSuite(pozzuolo_martesanaDialogTest)
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)

