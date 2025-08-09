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
import pathlib
from tempfile import TemporaryDirectory
from unittest import mock
from PySide6.QtCore import QSettings
from spinetoolbox.config import DEFAULT_WORK_DIR
from spinetoolbox.widgets.settings_widget import SettingsWidget
from tests.mock_helpers import TestCaseWithQApplication, create_toolboxui, q_object


class TestSettingsWidget(TestCaseWithQApplication):
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

    def test_default_work_directory_is_used_if_nothing_else_is_specified(self):
        with q_object(SettingsWidget(self._toolbox)) as settings_widget:
            self.assertEqual(settings_widget.ui.lineEdit_work_dir.text(), "")
            self.assertEqual(settings_widget.ui.lineEdit_work_dir.placeholderText(), DEFAULT_WORK_DIR)
            settings_widget.close()

    def test_work_directory_controls_are_properly_enabled(self):
        with q_object(SettingsWidget(self._toolbox)) as settings_widget:
            self.assertTrue(settings_widget.ui.open_work_dir_button.isEnabled())
            self.assertTrue(settings_widget.ui.work_dir_cleanup_button.isEnabled())
            settings_widget.ui.lineEdit_work_dir.setText("no such dir")
            self.assertFalse(settings_widget.ui.open_work_dir_button.isEnabled())
            self.assertFalse(settings_widget.ui.work_dir_cleanup_button.isEnabled())
            settings_widget.close()

    def test_work_directory_cleanup_button(self):
        with TemporaryDirectory() as temp_dir:
            tmp_path = pathlib.Path(temp_dir)
            (tmp_path / "file1").touch()
            subdir = tmp_path / "sub"
            subdir.mkdir()
            (subdir / "file2").touch()
            self._toolbox.set_work_directory(temp_dir)
            with q_object(SettingsWidget(self._toolbox)) as settings_widget:
                self.assertEqual(settings_widget.ui.lineEdit_work_dir.text(), temp_dir)
                with mock.patch("spinetoolbox.widgets.settings_widget.QMessageBox") as message_box_constructor:
                    mock_message_box = mock.MagicMock()
                    message_box_constructor.return_value = mock_message_box
                    button = object()
                    add_button = mock.MagicMock()
                    add_button.return_value = button
                    mock_message_box.addButton = add_button
                    clicked_button = mock.MagicMock()
                    clicked_button.return_value = button
                    mock_message_box.clickedButton = clicked_button
                    settings_widget.ui.work_dir_cleanup_button.click()
                settings_widget.close()
            self.assertEqual(list(tmp_path.iterdir()), [])
