######################################################################################################################
# Copyright (C) 2017-2020 Spine project consortium
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""
Contains unit tests for the SpineDatapackageWidget class.

:author: A. Soininen
:date:   16.3.2020
"""

import unittest
from unittest import mock
from PySide2.QtWidgets import QApplication
from spinetoolbox.widgets.spine_datapackage_widget import SpineDatapackageWidget


class TestSpineDatapackageWidget(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not QApplication.instance():
            QApplication()

    def test_closeEvent(self):
        widget = SpineDatapackageWidget(mock.MagicMock())
        widget.qsettings = mock.NonCallableMagicMock()
        widget.closeEvent()
        qsettings_save_calls = widget.qsettings.setValue.call_args_list
        self.assertEqual(len(qsettings_save_calls), 5)
        saved_dict = {saved[0][0]: saved[0][1] for saved in qsettings_save_calls}
        self.assertIn("dataPackageWidget/windowSize", saved_dict)
        self.assertIn("dataPackageWidget/windowPosition", saved_dict)
        self.assertIn("dataPackageWidget/windowState", saved_dict)
        self.assertIn("dataPackageWidget/windowMaximized", saved_dict)
        self.assertIn("dataPackageWidget/n_screens", saved_dict)


if __name__ == '__main__':
    unittest.main()
