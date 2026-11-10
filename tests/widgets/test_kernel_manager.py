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

"""Unit tests for the ``kernel_manager`` module."""

import pathlib
import subprocess
import sys
import venv
from tempfile import TemporaryDirectory
from unittest.mock import MagicMock, patch
import pytest
from PySide6.QtWidgets import QApplication, QWidget
from spinetoolbox.execution_models import ExecutionModels
from spinetoolbox.widgets.kernel_manager import MiniPythonKernelManager, MiniJuliaKernelManager


@pytest.fixture
def settings_widget():
    widget = MockSettingsWidget()
    yield widget
    widget.deleteLater()


class MockSettingsWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.qsettings = MagicMock()


class TestKernelManagers:
    def test_is_ipykernel_installed(self, application, settings_widget):
        models = ExecutionModels(MagicMock())
        manager = MiniPythonKernelManager(settings_widget, models)
        manager._python_exe = sys.executable
        with patch(
            "spinetoolbox.widgets.kernel_manager.MiniPythonKernelManager.start_kernelspec_install_process"
        ) as mock_start:
            mock_start.return_value = None
            manager.is_ipykernel_installed()
            mock_start.assert_called_once()

    def test_make_python_kernel(self, application, settings_widget):
        with TemporaryDirectory() as environment_dir:
            venv.create(environment_dir, system_site_packages=True)
            env_path = pathlib.Path(environment_dir)
            python_path = (
                env_path / "Scripts" / "python.exe"
                if sys.platform == "win32"
                else env_path / "bin" / "python"
            )
            kernel_name = "spinetoolbox_test_python_kernel"
            models = ExecutionModels(MagicMock())
            models.load_python_system_interpreters([str(python_path)], show_select_item=True)
            with (
                patch.object(models, "refresh_python_interpreters_model") as refresh_mock,
                patch("spinetoolbox.widgets.kernel_manager.VersionCollector") as mock_version_collector
            ):
                editor = MiniPythonKernelManager(settings_widget, models)
                refresh_mock.assert_called_once()
                mock_version_collector.assert_called()
            editor._python_exe = str(python_path)
            editor._python_kernel_name = kernel_name
            editor.make_python_kernel()
            while editor._install_package_process is not None:
                QApplication.processEvents()
            while editor._install_kernel_process is not None:
                QApplication.processEvents()
            assert editor.new_kernel_name == kernel_name
            editor.close()
            completion = subprocess.run(
                [str(python_path), "-m", "jupyter", "kernelspec", "remove", "-f", kernel_name],
                capture_output=True,
                check=False,
            )
            assert completion.returncode == 0

    def test_make_julia_kernel(self, application, settings_widget):
        """Tries to create a Julia kernel with a non-existing Julia."""
        kernel_name = "spinetoolbox_test_julia_kernel"
        julia_exec = "some/julia.exe"
        models = ExecutionModels(MagicMock())
        models.load_julia_executables([julia_exec], show_select_item=True)
        with (
            patch.object(models, "refresh_julia_executables_model") as refresh_mock,
            patch("spinetoolbox.widgets.kernel_manager.VersionCollector") as mock_version_collector
        ):
            editor = MiniJuliaKernelManager(settings_widget, models)
            refresh_mock.assert_called_once()
            mock_version_collector.assert_called()
        editor._julia_exe = julia_exec
        editor._julia_project = ""
        editor._julia_kernel_name_prefix = kernel_name
        with (
            patch("os.path.isfile") as mock_isfile,
            patch("spinetoolbox.widgets.kernel_manager.MiniJuliaKernelManager._complete_kernel_name") as mock_kname
        ):
            mock_isfile.return_value = True
            mock_kname.return_value = kernel_name
            editor.make_julia_kernel()
        # Creating the kernel fails because 'some/julia.exe' doesn't exist
        assert editor.ui.stackedWidget.currentIndex() == 1
        assert editor.ui.label_status.text() == "Creating kernel failed"
        editor.close()
