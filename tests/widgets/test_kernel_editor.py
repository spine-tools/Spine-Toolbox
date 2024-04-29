######################################################################################################################
# Copyright (C) 2017-2022 Spine project consortium
# Copyright Spine Toolbox contributors
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""Unit tests for the ``kernel_editor`` module."""
import json
import pathlib
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import MagicMock, patch
import venv
from PySide6.QtWidgets import QApplication, QMessageBox, QWidget
from spine_engine.utils.helpers import resolve_default_julia_executable
from spinetoolbox.widgets.kernel_editor import KernelEditorBase


class MockSettingsWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.qsettings = MagicMock()


class TestKernelEditorBase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not QApplication.instance():
            QApplication()

    def setUp(self):
        self._settings_widget = MockSettingsWidget()

    def tearDown(self):
        self._settings_widget.deleteLater()

    def test_is_package_installed(self):
        self.assertTrue(KernelEditorBase.is_package_installed(sys.executable, "PySide6"))
        self.assertFalse(KernelEditorBase.is_package_installed(sys.executable, "nonexistenttestpackageXYZ"))

    def test_make_python_kernel(self):
        if sys.platform != "win32":
            # This test seems to hang on Ubuntu host when running as GitHub action.
            # We might open a dialog somewhere and wait for user input which never comes.
            self.skipTest("Test disabled on non-Windows systems.")
        with TemporaryDirectory() as environment_dir:
            venv.create(environment_dir, system_site_packages=True)
            python_exec = "python.exe" if sys.platform == "win32" else "python"
            python_path = pathlib.Path(environment_dir, "Scripts", python_exec)
            kernel_name = "spinetoolbox_test_make_python_kernel"
            with patch("spinetoolbox.widgets.kernel_editor.QMessageBox") as mock_message_box, patch.object(
                KernelEditorBase, "_python_interpreter_name", return_value=str(python_path)
            ), patch.object(KernelEditorBase, "_python_kernel_name", return_value=kernel_name), patch.object(
                KernelEditorBase, "_python_kernel_display_name", return_value="Test kernel"
            ):
                mock_message_box.exec.return_value = QMessageBox.StandardButton.Ok
                editor = KernelEditorBase(self._settings_widget, "python")
                self.assertTrue(editor.make_python_kernel())
                while editor._install_package_process is not None:
                    QApplication.processEvents()
                self.assertFalse(editor._ipykernel_install_failed)
                self.assertTrue(KernelEditorBase.is_package_installed(str(python_path), "ipykernel"))
                while editor._install_kernel_process is not None:
                    QApplication.processEvents()
                editor.close()
            completion = subprocess.run(
                [str(python_path), "-m", "jupyter", "kernelspec", "remove", "-f", kernel_name], capture_output=True
            )
            self.assertEqual(completion.returncode, 0)

    def test_make_julia_kernel(self):
        """Makes a new Julia kernel if Julia is in PATH and the base project (@.) has
        IJulia installed. Test Julia kernel is removed in the end if available."""
        julia_exec = resolve_default_julia_executable()
        if not julia_exec:
            self.skipTest("Julia not found in PATH.")
        kernel_name = "spinetoolbox_test_make_julia_kernel"
        # with TemporaryDirectory() as julia_project_dir:
        with patch("spinetoolbox.widgets.kernel_editor.QMessageBox") as mock_message_box, patch.object(
            KernelEditorBase, "_julia_kernel_name", return_value=kernel_name
        ), patch.object(KernelEditorBase, "_julia_executable", return_value=julia_exec), patch.object(
            KernelEditorBase, "_julia_project", return_value="@."
        ):
            mock_message_box.exec.return_value = QMessageBox.StandardButton.Ok
            editor = KernelEditorBase(self._settings_widget, "julia")
            julia_project_dir = editor._julia_project()
            ijulia_installation_status = editor.is_ijulia_installed(julia_exec, julia_project_dir)
            if ijulia_installation_status == 0:
                self.skipTest("Failed to check IJulia status.")
            elif ijulia_installation_status == 2:
                self.skipTest(f"[{julia_exec}] IJulia not installed for project {editor._julia_project()}")
            self.assertTrue(editor.make_julia_kernel())
            while not editor._ready_to_install_kernel:
                QApplication.processEvents()
            while editor._install_julia_kernel_process is not None:
                QApplication.processEvents()
            editor.close()
        completion = subprocess.run(
            [sys.executable, "-m", "jupyter", "kernelspec", "list", "--json", kernel_name], capture_output=True
        )
        real_kernel_name = None
        kernel_info = json.loads(completion.stdout)
        for kernelspec_name in kernel_info["kernelspecs"]:
            if kernelspec_name.startswith(kernel_name):
                real_kernel_name = kernelspec_name
                break
        self.assertIsNotNone(real_kernel_name)
        if sys.platform == "win32":
            # For some reason the icon files in Julia kernel directory are marked as read only
            # on Windows platforms preventing removal.
            # This removes the read only flag.
            kernelspec_dir = kernel_info["kernelspecs"][real_kernel_name]["resource_dir"]
            subprocess.run(["attrib", "-r", str(pathlib.Path(kernelspec_dir, "*.*"))])
        completion = subprocess.run(
            [sys.executable, "-m", "jupyter", "kernelspec", "remove", "-f", real_kernel_name], capture_output=True
        )
        self.assertEqual(completion.returncode, 0)
