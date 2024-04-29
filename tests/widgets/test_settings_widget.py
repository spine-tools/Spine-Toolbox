######################################################################################################################
# Copyright (C) 2017-2023 Spine project consortium
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""Unit tests for the ``settings_widget`` module."""
import os
import unittest
from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication
from spinetoolbox.widgets.settings_widget import SettingsWidget
from tests.mock_helpers import create_toolboxui


class TestSettingsWidget(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not QApplication.instance():
            QApplication()

    def setUp(self):
        self._settings = QSettings("SpineProject", "Spine Toolbox tests")
        self._toolbox = create_toolboxui()
        self._toolbox._qsettings = self._settings

    def tearDown(self):
        self._settings.clear()

    def test_defaults_for_initially_empty_app_settings(self):
        widget = SettingsWidget(self._toolbox)
        widget.save_and_close()
        widget.deleteLater()
        self._settings.beginGroup("appSettings")
        try:
            self.assertEqual(self._settings.value("openPreviousProject"), "0")
            self.assertEqual(self._settings.value("showExitPrompt"), "2")
            self.assertEqual(self._settings.value("saveAtExit"), "prompt")
            self.assertEqual(self._settings.value("dateTime"), "2")
            self.assertEqual(self._settings.value("deleteData"), "0")
            self.assertEqual(self._settings.value("customOpenProjectDialog"), "true")
            self.assertEqual(self._settings.value("smoothZoom"), "false")
            self.assertEqual(self._settings.value("colorToolbarIcons"), "false")
            self.assertEqual(self._settings.value("colorPropertiesWidgets"), "false")
            self.assertEqual(self._settings.value("curvedLinks"), "false")
            self.assertEqual(self._settings.value("dragToDrawLinks"), "false")
            self.assertEqual(self._settings.value("roundedItems"), "false")
            self.assertEqual(self._settings.value("preventOverlapping"), "false")
            self.assertEqual(self._settings.value("dataFlowAnimationDuration"), "100")
            self.assertEqual(self._settings.value("bgChoice"), "solid")
            self.assertEqual(self._settings.value("bgColor"), widget.bg_color)
            self.assertEqual(self._settings.value("saveSpecBeforeClosing"), "1")
            self.assertEqual(self._settings.value("specShowUndo"), "2")
            self.assertEqual(self._settings.value("gamsPath"), "")
            self.assertEqual(self._settings.value("useJuliaKernel"), "0")
            self.assertEqual(self._settings.value("juliaPath"), "")
            self.assertEqual(self._settings.value("juliaProjectPath"), "")
            self.assertEqual(self._settings.value("juliaKernel"), "")
            self.assertEqual(self._settings.value("usePythonKernel"), "0")
            self.assertEqual(self._settings.value("pythonPath"), "")
            self.assertEqual(self._settings.value("pythonKernel"), "")
            self.assertEqual(self._settings.value("condaPath"), "")
        finally:
            self._settings.endGroup()
        self._settings.beginGroup("engineSettings")
        try:
            self.assertEqual(self._settings.value("remoteExecutionEnabled"), "false")
            self.assertEqual(self._settings.value("remoteHost"), "")
            self.assertEqual(self._settings.value("remotePort"), 49152)
            self.assertEqual(self._settings.value("remoteSecurityModel"), "")
            self.assertEqual(self._settings.value("remoteSecurityFolder"), "")
            self.assertEqual(self._settings.value("processLimiter"), "unlimited")
            self.assertEqual(self._settings.value("maxProcesses"), str(os.cpu_count()))
            self.assertEqual(self._settings.value("persistentLimiter"), "unlimited")
            self.assertEqual(self._settings.value("maxPersistentProcesses"), str(os.cpu_count()))
        finally:
            self._settings.endGroup()


if __name__ == "__main__":
    unittest.main()
