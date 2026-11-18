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
from unittest.mock import MagicMock, patch, Mock
import pytest
from PySide6.QtWidgets import QApplication, QWidget
from spinetoolbox.execution_models import ExecutionModels
from spinetoolbox.widgets.kernel_manager import MiniPythonKernelManager, MiniJuliaKernelManager, VersionCollector


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
                env_path / "Scripts" / "python.exe" if sys.platform == "win32" else env_path / "bin" / "python"
            )
            kernel_name = "spinetoolbox_test_python_kernel"
            models = ExecutionModels(MagicMock())
            models.load_python_system_interpreters([str(python_path)], show_select_item=True)
            with (
                patch.object(models, "refresh_python_interpreters_model") as refresh_mock,
                patch("spinetoolbox.widgets.kernel_manager.VersionCollector") as mock_version_collector,
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

    def test_python_kernel_manager_functionality(self, application, settings_widget):
        models = ExecutionModels(MagicMock())
        models.load_python_system_interpreters(["/some/pythonista"], show_select_item=True)
        with (
            patch.object(models, "refresh_python_interpreters_model") as refresh_mock,
            patch("spinetoolbox.widgets.kernel_manager.VersionCollector") as mock_version_collector,
        ):
            editor = MiniPythonKernelManager(settings_widget, models)
            refresh_mock.assert_called_once()
            mock_version_collector.assert_called()
        editor._python_versions = {"/some/pythonista": "320"}
        index = models.find_python_interpreter_index("/some/pythonista")
        editor.ui.comboBox_python_interpreter.setCurrentIndex(index.row())
        assert editor._python_kernel_name == "python320"
        assert editor._python_exe == "/some/pythonista"
        with (patch("os.path.isfile") as mock_isfile, patch("spinetoolbox.widgets.kernel_manager.Notification") as mock_notification):
            mock_isfile.return_value = False
            editor._check_selections()  # Stops at os.path.isfile because _python_exe is just a dummy
            mock_isfile.assert_called_once()
            mock_notification.assert_called_once()
        editor.ui.comboBox_python_interpreter.setCurrentIndex(0)
        assert editor._python_exe is None
        with pytest.raises(RuntimeError):
            editor._complete_kernel_name()
        with patch("spinetoolbox.widgets.kernel_manager.Notification") as mock_notification:
            editor._check_selections()
            mock_notification.assert_called_once()
        editor.msg_success.emit("hi")
        editor.msg_warning.emit("hi")
        editor.msg_proc.emit("hi")
        editor.msg_error.emit("hi")
        editor.add_error_message("hi")

    def test_ask_permission_to_overwrite(self, application, settings_widget):
        models = ExecutionModels(MagicMock())
        with patch("spinetoolbox.widgets.kernel_manager.VersionCollector") as mock_version_collector:
            editor = MiniPythonKernelManager(settings_widget, models)
            mock_version_collector.assert_called()
        with patch("spinetoolbox.widgets.kernel_manager.QMessageBox") as MockMessageBox:
            mb = MockMessageBox.return_value
            yes_button = object()
            cancel_button = object()
            mb.addButton.side_effect = [yes_button, cancel_button, yes_button, cancel_button]
            mb.clickedButton.side_effect = [yes_button, cancel_button]
            assert editor.ask_permission_to_overwrite("kname") is True
            assert editor.ask_permission_to_overwrite("kname") is False
            assert mb.exec_.call_count == 2

    def test_make_julia_kernel(self, application, settings_widget):
        """Tries to create a Julia kernel with a non-existing Julia."""
        kernel_name = "spinetoolbox_test_julia_kernel"
        julia_exec = "some/julia.exe"
        models = ExecutionModels(MagicMock())
        models.load_julia_executables([julia_exec], show_select_item=True)
        with (
            patch.object(models, "refresh_julia_executables_model") as refresh_mock,
            patch("spinetoolbox.widgets.kernel_manager.VersionCollector") as mock_version_collector,
        ):
            editor = MiniJuliaKernelManager(settings_widget, models)
            refresh_mock.assert_called_once()
            mock_version_collector.assert_called()
        editor._julia_exe = julia_exec
        editor._julia_project = ""
        editor._julia_kernel_name_prefix = kernel_name
        with (
            patch("os.path.isfile") as mock_isfile,
            patch("spinetoolbox.widgets.kernel_manager.MiniJuliaKernelManager._complete_kernel_name") as mock_kname,
        ):
            mock_isfile.return_value = True
            mock_kname.return_value = kernel_name
            editor.make_julia_kernel()
        # Creating the kernel fails because 'some/julia.exe' doesn't exist
        assert editor.ui.stackedWidget.currentIndex() == 1
        assert editor.ui.label_status.text() == "Creating kernel failed"
        editor.close()

    def test_julia_kernel_manager_functionality(self, application, settings_widget):
        models = ExecutionModels(MagicMock())
        models.load_julia_executables(["/some/julian"], show_select_item=True)
        models.load_julia_projects(["/some/julia/env"], show_select_item=True)
        with (
            patch.object(models, "refresh_julia_executables_model") as refresh_execs_mock,
            patch.object(models, "refresh_julia_projects_model") as refresh_projects_mock,
            patch("spinetoolbox.widgets.kernel_manager.VersionCollector") as mock_version_collector,
        ):
            editor = MiniJuliaKernelManager(settings_widget, models)
            refresh_execs_mock.assert_called_once()
            refresh_projects_mock.assert_called_once()
            mock_version_collector.assert_called()
        editor._julia_versions = {"/some/julian": "2.20"}
        # model = editor.ui.comboBox_julia_executable.model()
        # for row in range(model.rowCount()):
        #     index = model.index(row, 0)
        #     print(model.itemFromIndex(index).data(Qt.ItemDataRole.DisplayRole))
        #     print(f"data:{model.itemFromIndex(index).data()}")
        exe_index = models.find_julia_executable_index("/some/julian")
        editor.ui.comboBox_julia_executable.setCurrentIndex(exe_index.row())
        # print(f"prefix:{editor._julia_kernel_name_prefix}")
        # print(f"_julia_exe:{editor._julia_exe}")
        assert editor._julia_kernel_name_prefix == None
        assert editor._julia_exe == "/some/julian"
        # model = editor.ui.comboBox_julia_environment.model()
        # for row in range(model.rowCount()):
        #     index = model.index(row, 0)
        #     print(model.itemFromIndex(index).data(Qt.ItemDataRole.DisplayRole))
        #     print(f"data:{model.itemFromIndex(index).data()}")
        env_index = models.find_julia_project_index("/some/julia/env")
        editor.ui.comboBox_julia_environment.setCurrentIndex(env_index.row())
        # print(f"prefix:{editor._julia_kernel_name_prefix}")
        # print(f"_julia_project:{editor._julia_project}")
        assert editor._julia_project == "/some/julia/env"
        assert editor._julia_kernel_name_prefix == "julia-env"
        assert editor._complete_kernel_name() == "julia-env-2.20"
        with (patch("os.path.isfile") as mock_isfile, patch("spinetoolbox.widgets.kernel_manager.Notification") as mock_notification):
            mock_isfile.return_value = False
            editor._check_selections()  # Stops at os.path.isfile because _julia_exe is just a dummy
            mock_isfile.assert_called_once()
            mock_notification.assert_called_once()
        editor.ui.comboBox_julia_executable.setCurrentIndex(0)
        assert editor._julia_exe is None
        with pytest.raises(RuntimeError):
            editor._complete_kernel_name()
        with patch("spinetoolbox.widgets.kernel_manager.Notification") as mock_notification:
            editor._check_selections()
            mock_notification.assert_called_once()


class TestVersionCollector:
    def test_run_emits_versions(self):
        collector = VersionCollector(["a", "b"])
        slot = Mock()
        collector.versions_collected.connect(slot)
        with patch.object(VersionCollector,"_get_version", side_effect=["310", None]):
            collector.run()
        slot.assert_called_once_with({"a": "310", "b": "x.x"})

    def test_get_python_version(self):
        manager = MagicMock()
        manager.process_output = "Python 3.10.8"
        with (
            patch("os.path.exists") as mock_exists,
            patch("spinetoolbox.widgets.kernel_manager.QProcessExecutionManager") as manager_cls
        ):
            manager_cls.return_value = manager
            mock_exists.return_value = True
            version = VersionCollector._get_version("/path/python")
            assert version == "310"
            mock_exists.assert_called_once()
        manager.start_execution.assert_called_once()
        manager.wait_for_process_finished.assert_called_once()

    def test_get_julia_version(self):
        manager = MagicMock()
        manager.process_output = "julia version 1.13.3"
        with (
            patch("os.path.exists") as mock_exists,
            patch("spinetoolbox.widgets.kernel_manager.QProcessExecutionManager") as manager_cls
        ):
            manager_cls.return_value = manager
            mock_exists.return_value = True
            version = VersionCollector._get_version("/path/julia")
            assert version == "1.13"
            mock_exists.assert_called_once()
        manager.start_execution.assert_called_once()
        manager.wait_for_process_finished.assert_called_once()

    def test_get_version_missing_executable(self):
        with patch("os.path.exists") as mock_exists:
            mock_exists.return_value = False
            assert VersionCollector._get_version("/missing") is None
            mock_exists.assert_called_once()

    def test_get_version_empty_output(self):
        manager = MagicMock()
        manager.process_output = ""
        with (
            patch("os.path.exists") as mock_exists,
            patch("spinetoolbox.widgets.kernel_manager.QProcessExecutionManager") as manager_cls
        ):
            manager_cls.return_value = manager
            mock_exists.return_value = True
            assert VersionCollector._get_version("/path/exe") is None
            mock_exists.assert_called_once()

    def test_get_version_malformed_output(self):
        manager = MagicMock()
        manager.process_output = "Python"
        with (
            patch("os.path.exists") as mock_exists,
            patch("spinetoolbox.widgets.kernel_manager.QProcessExecutionManager") as manager_cls
        ):
            manager_cls.return_value = manager
            mock_exists.return_value = True
            assert VersionCollector._get_version("/path/exe") is None
            mock_exists.assert_called_once()
