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

"""Contains wizard like dialogs for creating kernel specs for Python or Julia."""

import os
import subprocess
from PySide6.QtCore import Qt, Signal, Slot, QThread, QProcess
from PySide6.QtGui import QGuiApplication, QIcon
from PySide6.QtWidgets import QDialog, QMessageBox
from spine_engine.utils.helpers import (
    custom_find_kernel_specs,
    resolve_current_python_interpreter,
    resolve_default_julia_executable,
)
from spinetoolbox.execution_managers import QProcessExecutionManager
from spinetoolbox.helpers import (
    ensure_window_is_on_screen,
    get_datetime,
    get_current_item_data,
    set_combobox_item_invalid_property,
)
from spinetoolbox.widgets.notification import Notification


class KernelManagerBase(QDialog):
    """Base class for kernel managers."""

    msg = Signal(str)
    msg_success = Signal(str)
    msg_warning = Signal(str)
    msg_proc = Signal(str)
    msg_proc_error = Signal(str)
    msg_error = Signal(str)

    def __init__(self, parent, execution_models):
        """
        Args:
            parent (SettingsWidget): Parent widget
            execution_models (ExecutionModels): Python and Julia runtime manager
        """
        super().__init__(parent=parent)
        self._parent = parent
        self._exec_models = execution_models
        self._app_settings = self._parent.qsettings
        self._new_kernel_name = None

    def connect_signals(self):
        """Connects signals to slots."""
        self.msg.connect(self.add_message)
        self.msg_success.connect(self.add_success_message)
        self.msg_warning.connect(self.add_warning_message)
        self.msg_proc.connect(self.add_process_message)
        self.msg_error.connect(self.add_process_error_message)

    def _check_selections(self):
        raise NotImplementedError()

    def _complete_kernel_name(self):
        raise NotImplementedError()

    @property
    def new_kernel_name(self):
        """Returns the new kernel name after it's been created."""
        return self._new_kernel_name

    @staticmethod
    def _get_list_of_executables(model, executable_type):
        l = list()
        for row in range(model.rowCount()):
            data = model.item(row).data()
            if not data:
                continue
            path = data["exe"]
            if path == "":
                if executable_type == "julia":
                    path = resolve_default_julia_executable()
                elif executable_type == "python":
                    path = resolve_current_python_interpreter()
                else:
                    raise RuntimeError(f"Unknown executable type:{executable_type}")
            l.append(path)
        return l

    def ask_permission_to_overwrite(self, kname):
        """Opens a messagebox asking whether to overwrite an existing kernel."""
        message_box = QMessageBox(
            QMessageBox.Icon.Question,
            f"Overwrite kernel {kname}?",
            f"Kernel {kname} already exists. By clicking <b>Make kernel</b>, the "
            f"existing kernel will be overwritten. Continue?",
            parent=self,
        )
        yes_button = message_box.addButton("Make kernel", QMessageBox.ButtonRole.YesRole)
        cancel_button = message_box.addButton("Cancel", QMessageBox.ButtonRole.NoRole)
        message_box.setDefaultButton(cancel_button)
        message_box.exec_()
        if message_box.clickedButton() is yes_button:
            return True
        return False

    def set_failed_state(self, status_label_txt, progress_label_txt):
        """Stops progress bar animation and sets the progress to 0 for failure.
        Sets label texts and shows the Close button."""
        self.ui.label_status.setText(status_label_txt)
        self.ui.label_in_progress_msg.setText(progress_label_txt)
        self.ui.progressBar.reset()
        self.ui.progressBar.setRange(0, 100)
        self.ui.progressBar.setValue(0)
        self.ui.pushButton_close.show()

    def _save_ui(self):
        self._app_settings.setValue("kernelEditor/windowSize", self.size())
        self._app_settings.setValue("kernelEditor/windowPosition", self.pos())
        self._app_settings.setValue(
            "kernelEditor/windowMaximized", self.windowState() == Qt.WindowState.WindowMaximized
        )

    def restore_dialog_dimensions(self):
        """Restore widget location, dimensions, and state from previous session."""
        dialog_size = self._app_settings.value("kernelEditor/windowSize", defaultValue="false")
        dialog_pos = self._app_settings.value("kernelEditor/windowPosition", defaultValue="false")
        dialog_maximized = self._app_settings.value("kernelEditor/windowMaximized", defaultValue="false")
        n_screens = self._app_settings.value("mainWindow/n_screens", defaultValue=1)  # Yes, mainWindow
        # noinspection PyArgumentList
        n_screens_now = len(QGuiApplication.screens())  # Number of screens now
        original_size = self.size()
        # Note: cannot use booleans since Windows saves them as strings to registry
        if dialog_size != "false":
            self.resize(dialog_size)  # Expects QSize
        if dialog_pos != "false":
            self.move(dialog_pos)  # Expects QPoint
        if n_screens_now < int(n_screens):
            # There are less screens available now than on previous application startup
            # Move dialog to position 0,0 to make sure that it is not lost on another screen that does not exist
            self.move(0, 0)
        ensure_window_is_on_screen(self, original_size)
        if dialog_maximized == "true":
            self.setWindowState(Qt.WindowState.WindowMaximized)

    @Slot(str)
    def add_message(self, msg):
        """Append regular message to kernel editor text browser.

        Args:
            msg (str): String written to QTextBrowser
        """
        message = format_event_message("msg", msg)
        self.ui.textBrowser.append(message)

    @Slot(str)
    def add_success_message(self, msg):
        """Append message with green text color to kernel editor text browser.

        Args:
            msg (str): String written to QTextBrowser
        """
        message = format_event_message("msg_success", msg)
        self.ui.textBrowser.append(message)

    @Slot(str)
    def add_error_message(self, msg):
        """Append message with red color to kernel editor text browser.

        Args:
            msg (str): String written to QTextBrowser
        """
        message = format_event_message("msg_error", msg)
        self.ui.textBrowser.append(message)

    @Slot(str)
    def add_warning_message(self, msg):
        """Append message with yellow (golden) color to kernel editor text browser.

        Args:
            msg (str): String written to QTextBrowser
        """
        message = format_event_message("msg_warning", msg)
        self.ui.textBrowser.append(message)

    @Slot(str)
    def add_process_message(self, msg):
        """Writes message from stdout to kernel editor text browser.

        Args:
            msg (str): String written to QTextBrowser
        """
        message = format_process_message("msg", msg)
        self.ui.textBrowser.append(message)

    @Slot(str)
    def add_process_error_message(self, msg):
        """Writes message from stderr to kernel editor text browser.

        Args:
            msg (str): String written to QTextBrowser
        """
        message = format_process_message("msg_error", msg)
        self.ui.textBrowser.append(message)


class MiniPythonKernelManager(KernelManagerBase):
    """A Simple Python kernel manager."""

    def __init__(self, parent, models):
        super().__init__(parent, models)
        from ..ui import python_kernel_manager  # pylint: disable=import-outside-toplevel

        self.ui = python_kernel_manager.Ui_Dialog()
        self.ui.setupUi(self)
        self.setWindowFlags(Qt.WindowType.Window)
        self.setWindowIcon(QIcon(":/symbols/app.ico"))
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self.setWindowTitle("Python Kernel Manager")
        Notification(self, "Setting things up...").show()
        # Disable combobox and button until versions have been received
        self.ui.comboBox_python_interpreter.setEnabled(False)
        self.ui.pushButton_make_kernel.setEnabled(False)
        self._python_exe = None
        self._python_kernel_name = None
        self._install_kernel_process = None
        self._install_package_process = None
        self._ipykernel_install_failed = False
        self._python_versions = None
        self.ui.stackedWidget.setCurrentIndex(0)
        self.ui.comboBox_python_interpreter.setModel(self._exec_models.python_interpreters_model)
        self._exec_models.refresh_python_interpreters_model(show_select_item=True)
        self.ui.comboBox_python_interpreter.setCurrentIndex(0)
        python_interpreters = self._get_list_of_executables(self._exec_models.python_interpreters_model, "python")
        self.kernel_name_creator = VersionCollector(python_interpreters)
        self.kernel_name_creator.versions_collected.connect(self.on_versions_collected)
        self.kernel_name_creator.start()
        self.connect_signals()

    def connect_signals(self):
        super().connect_signals()
        self.ui.pushButton_make_kernel.clicked.connect(self.make_python_kernel)
        self.ui.pushButton_close.clicked.connect(self.close)
        self.ui.comboBox_python_interpreter.currentIndexChanged.connect(self._set_python_exe)

    @Slot(dict)
    def on_versions_collected(self, python_versions):
        self.ui.comboBox_python_interpreter.setEnabled(True)
        self.ui.pushButton_make_kernel.setEnabled(True)
        self._python_versions = python_versions  # eg. {"exe1": "314", "exe2": "315", ...}

    def _check_selections(self):
        if not self._python_exe:
            Notification(self, "Please select a Python interpreter").show()
            return False
        if not os.path.isfile(self._python_exe):
            Notification(
                self, f"Path {self._python_exe} doesn't exist. Please select another Python interpreter"
            ).show()
            return False
        return True

    def _complete_kernel_name(self):
        """Creates the Python kernel name based on Python version."""
        try:
            version = self._python_versions[self._python_exe]
        except IndexError:
            raise RuntimeError(f"Python version check failed for {self._python_exe}")
        return f"python{version}"

    @Slot(int)
    def _set_python_exe(self, _ind):
        """Updates the selected python interpreter and kernel name for that python.
        Sets the combobox current item red if the python interpreter path doesn't exist."""
        combo = self.ui.comboBox_python_interpreter
        model = combo.model()
        item = model.itemFromIndex(model.index(_ind, 0))
        set_combobox_item_invalid_property(combo, item)
        data = get_current_item_data(self.ui.comboBox_python_interpreter, self._exec_models.python_interpreters_model)
        if not data:
            self._python_exe = None
            self.ui.pushButton_make_kernel.setText("Make kernel")
            return
        self._python_exe = data["exe"]
        if not self._python_exe:
            self._python_exe = resolve_current_python_interpreter()
        self._python_kernel_name = self._complete_kernel_name()
        if not self._python_kernel_name:
            self.ui.pushButton_make_kernel.setText("Make kernel")
            return
        self.ui.pushButton_make_kernel.setText(f"Make kernel {self._python_kernel_name}")
        return

    @Slot(bool)
    def make_python_kernel(self, _=False):
        """Checks that a valid Python interpreter is selected and asks for confirmation
        to overwrite an existing kernel if necessary. Then starts the process by
        checking if ipykernel is installed."""
        if not self._check_selections():
            return
        kname = self._complete_kernel_name()
        index = self._exec_models.find_python_kernel_index(kname)
        if index.isValid():
            if not self.ask_permission_to_overwrite(kname):
                return
        self.ui.pushButton_make_kernel.setEnabled(False)
        self.ui.stackedWidget.setCurrentIndex(1)
        self.ui.progressBar.setRange(0, 0)
        self.ui.pushButton_close.hide()
        self.is_ipykernel_installed()

    def is_ipykernel_installed(self):
        """Checks if ipykernel is installed. If not, asks permission to install it.
         If ipykernel is installed, starts creating the kernel specs."""
        try:
            subprocess.run(
                [self._python_exe, "-c", "import ipykernel"],
                capture_output=True,
                text=True,
                check=True,
            )
        except subprocess.CalledProcessError:
            # ipykernel missing. Ask permission to install it.
            message = (
                f"Python environment<br><br><b>{self._python_exe}</b><br><br>"
                f"does not have the <b>ipykernel</b> package installed.<br><br>"
                f"Ipykernel is required for Jupyter integration and must be "
                f"available in this environment to use it in a Jupyter "
                f"Console within Spine Toolbox.<br><br>"
                f"Do you want to install the package now?"
            )
            message_box = QMessageBox(
                QMessageBox.Icon.Question,
                "ipykernel missing",
                message,
                QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel,
                parent=self,
            )
            message_box.button(QMessageBox.StandardButton.Ok).setText("Install ipykernel")
            if message_box.exec() == QMessageBox.StandardButton.Cancel:
                self.msg.emit(
                    "\nInstallation of ipykernel was cancelled. This Python environment will "
                    "not be available for use in a Jupyter Console within Spine Toolbox. "
                    "You may close the dialog."
                )
                self.set_failed_state("Kernel creating cancelled", "")
                return
            self.start_installing_ipykernel()
            return
        self.start_kernelspec_install_process()

    def start_installing_ipykernel(self):
        """Starts installing ipykernel package using pip."""
        self.ui.label_status.setText("Installing ipykernel")
        self.msg.emit(f"Installing <b>ipykernel</b> into environment {self._python_exe}")
        args = ["-m", "pip", "install", "ipykernel"]
        self._install_package_process = QProcessExecutionManager(self, self._python_exe, args, semisilent=True)
        self._install_package_process.execution_finished.connect(self._handle_ipykernel_installation_finished)
        self._install_package_process.start_execution()

    @Slot(int)
    def _handle_ipykernel_installation_finished(self, retval):
        """Handles installing package finished.

        Args:
            retval (int): Process return value. 0: success, !0: failure
        """
        self._install_package_process.execution_finished.disconnect()
        self._install_package_process.deleteLater()
        self._install_package_process = None
        if retval != 0:
            self.set_failed_state("Kernel creation failed", "ipykernel installation failed. See details below")
            return
        self.start_kernelspec_install_process()

    def start_kernelspec_install_process(self):
        r"""Installs a Jupyter kernel specification for the selected Python interpreter.

        Starts a QProcess that runs a command similar to:

            python -m ipykernel install --user --name python-X.Y --display-name python-X.Y_spinetoolbox

        The ``--user`` option is used instead of ``--sys-prefix`` to ensure
        that the kernel specification is installed into the user's Jupyter
        kernels directory (for example, ``%APPDATA%\jupyter\kernels`` on
        Windows). This makes the kernel discoverable regardless of which
        Python interpreter was used to launch Spine Toolbox.

        Using ``--sys-prefix`` could install the kernel specification into
        the selected interpreter's environment-specific Jupyter directory,
        making it visible only when Jupyter is started from that same
        interpreter environment.
        """
        self.ui.label_status.setText(f"Creating kernel {self._python_kernel_name}")
        k_name = self._python_kernel_name
        kd_name = k_name + "_spinetoolbox"
        self.msg.emit("Starting Python kernel spec install process")
        args = ["-m", "ipykernel", "install", "--user", "--name", k_name, "--display-name", kd_name]
        self._install_kernel_process = QProcessExecutionManager(self, self._python_exe, args, semisilent=True)
        self._install_kernel_process.execution_finished.connect(self._handle_kernelspec_installation_finished)
        self._install_kernel_process.start_execution()

    @Slot(int)
    def _handle_kernelspec_installation_finished(self, retval):
        """Handles cleaning up after the kernel creation process has finished.

        Args:
            retval (int): Process return value. 0: success, !0: failure
        """
        self._install_kernel_process.execution_finished.disconnect()
        self._install_kernel_process.deleteLater()
        self._install_kernel_process = None
        if retval != 0:
            self.set_failed_state(f"Creating Kernel {self._python_kernel_name} failed!", "Please see details below. You may try again or install the kernel manually")
            return
        self.ui.progressBar.setRange(0, 100)
        self.ui.progressBar.setValue(100)
        self.ui.stackedWidget.setCurrentIndex(2)
        self.ui.pushButton_close.show()
        self.ui.label_success_status.setText(f"Kernel {self._python_kernel_name} created successfully!")
        self._new_kernel_name = self._python_kernel_name
        self.ui.label_interpreter.setText(f"{self._python_exe}")


class MiniJuliaKernelManager(KernelManagerBase):
    """A Simple Julia kernel manager."""

    def __init__(self, parent, models):
        super().__init__(parent, models)
        from ..ui import julia_kernel_manager  # pylint: disable=import-outside-toplevel

        self.ui = julia_kernel_manager.Ui_Dialog()
        self.ui.setupUi(self)
        self.setWindowFlags(Qt.WindowType.Window)
        self.setWindowIcon(QIcon(":/symbols/app.ico"))
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self.setWindowTitle("Julia Kernel Manager")
        self.ui.stackedWidget.setCurrentIndex(0)
        Notification(self, "Setting things up...").show()
        self._kernel_names_before = custom_find_kernel_specs().keys()
        # Disable comboboxes and button until versions have been received
        self.ui.comboBox_julia_executable.setEnabled(False)
        self.ui.comboBox_julia_environment.setEnabled(False)
        self.ui.pushButton_make_kernel.setEnabled(False)
        self._exec_models.refresh_julia_executables_model(show_select_item=True)
        self._exec_models.refresh_julia_projects_model(show_select_item=True)
        self.ui.comboBox_julia_executable.setModel(self._exec_models.julia_executables_model)
        self.ui.comboBox_julia_environment.setModel(self._exec_models.julia_projects_model)
        self.ui.comboBox_julia_executable.setCurrentIndex(0)
        self.ui.comboBox_julia_environment.setCurrentIndex(0)
        self._julia_kernel_name_prefix = None
        self._julia_exe = None
        self._julia_project = None
        self._julia_versions = None
        self._check_ijulia_status_process = None
        self._install_ijulia_process = None
        self._install_julia_kernel_process = None
        julia_executables = self._get_list_of_executables(self._exec_models.julia_executables_model, "julia")
        self.kernel_name_creator = VersionCollector(julia_executables)
        self.kernel_name_creator.versions_collected.connect(self.on_versions_collected)
        self.kernel_name_creator.start()
        self.connect_signals()

    def connect_signals(self):
        super().connect_signals()
        self.ui.pushButton_make_kernel.clicked.connect(self.make_julia_kernel)
        self.ui.comboBox_julia_executable.currentIndexChanged.connect(self._set_julia_exe)
        self.ui.comboBox_julia_environment.currentIndexChanged.connect(self._set_julia_project)
        self.ui.pushButton_close.clicked.connect(self.close)

    @Slot(dict)
    def on_versions_collected(self, julia_versions):
        self.ui.comboBox_julia_executable.setEnabled(True)
        self.ui.comboBox_julia_environment.setEnabled(True)
        self.ui.pushButton_make_kernel.setEnabled(True)
        self._julia_versions = julia_versions  # eg. {"exe1": "1.10", "exe2": "1.11", ...}

    def _check_selections(self):
        if not self._julia_exe:
            Notification(self, "Please select a Julia executable").show()
            return False
        if not os.path.isfile(self._julia_exe):
            Notification(
                self, f"Path {self._julia_exe} doesn't exist. Please select another Julia executable"
            ).show()
            return False
        if self._julia_project is None:
            Notification(self, "Please select a Julia environment").show()
            return False
        if self._julia_project != "" and self._julia_project != "@." and not os.path.exists(self._julia_project):
            Notification(
                self, f"Path {self._julia_project} doesn't exist. Please select another Julia environment"
            ).show()
            return False
        return True

    def _complete_kernel_name(self):
        """Creates the final julia kernel name based on julia version and environment."""
        try:
            version = self._julia_versions[self._julia_exe]
        except IndexError:
            raise RuntimeError(f"Julia version check failed for {self._julia_exe}")
        return f"{self._julia_kernel_name_prefix}-{version}"

    @Slot(int)
    def _set_julia_exe(self, _ind):
        combo = self.ui.comboBox_julia_executable
        model = combo.model()
        item = model.itemFromIndex(model.index(_ind, 0))
        set_combobox_item_invalid_property(combo, item)
        data = get_current_item_data(self.ui.comboBox_julia_executable, self._exec_models.julia_executables_model)
        if not data:
            self._julia_exe = None
            self._julia_kernel_name_prefix = None
            self.ui.pushButton_make_kernel.setText("Make kernel")
            return
        self._julia_exe = data["exe"]
        if not self._julia_exe:
            self._julia_exe = resolve_default_julia_executable()
        if self._julia_project is not None:
            kernel_name = self._complete_kernel_name()
            self.ui.pushButton_make_kernel.setText(f"Make kernel {kernel_name}")
        else:
            self.ui.pushButton_make_kernel.setText(f"Make kernel")
        return

    @Slot(int)
    def _set_julia_project(self, _ind):
        combo = self.ui.comboBox_julia_environment
        model = combo.model()
        item = model.itemFromIndex(model.index(_ind, 0))
        set_combobox_item_invalid_property(combo, item)
        data = get_current_item_data(self.ui.comboBox_julia_environment, self._exec_models.julia_projects_model)
        if not data:
            self._julia_project = None
            self._julia_kernel_name_prefix = None
            self.ui.pushButton_make_kernel.setText("Make kernel")
            return
        self._julia_project = data["path"]
        if self._julia_project == "":
            self._julia_kernel_name_prefix = "julia-global"
        elif self._julia_project == "@.":
            self._julia_kernel_name_prefix = "julia-project"
        else:
            _, env_prefix = os.path.split(self._julia_project)
            env_prefix = env_prefix.lower()
            self._julia_kernel_name_prefix = "julia-" + env_prefix
        if self._julia_exe is not None:
            kernel_name = self._complete_kernel_name()
            self.ui.pushButton_make_kernel.setText(f"Make kernel {kernel_name}")
        else:
            self.ui.pushButton_make_kernel.setText(f"Make kernel")

    @Slot(bool)
    def make_julia_kernel(self, _=False):
        """Checks that selections are valid and asks for confirmation
        to overwrite an existing kernel if necessary. Then starts the
        process by first checking if IJulia is installed."""
        if not self._check_selections():
            return
        kname = self._complete_kernel_name()
        index = self._exec_models.find_julia_kernel_index(kname)
        if index.isValid():
            if not self.ask_permission_to_overwrite(kname):
                return
        self.ui.stackedWidget.setCurrentIndex(1)
        self.ui.progressBar.setRange(0, 0)
        self.ui.pushButton_close.hide()
        self.is_ijulia_installed()

    def is_ijulia_installed(self):
        """Checks if IJulia is installed for the selected project.

        Note: Using command 'using IJulia' does not work because
        it automatically tries loading IJulia from the LOAD_PATH if
        it's not found in the active project.

        using Pkg

        deps = Pkg.dependencies()
        installed = any(pkg.name == ARGS[1] for pkg in values(deps))
        println(installed ? ARGS[2]: ARGS[3])
        """

        self.msg.emit("Checking IJulia status")
        args = [
            f"--project={self._julia_project}",
            "-e",
            "using Pkg; deps = Pkg.dependencies(); installed = any(pkg.name == ARGS[1] for pkg in values(deps)); println(installed ? ARGS[2] : ARGS[3])",
            "IJulia",
            "True",  # This could be anything, as long as we just match this afterward
            "False",
        ]
        self._check_ijulia_status_process = QProcessExecutionManager(self, self._julia_exe, args)
        self._check_ijulia_status_process._process.finished.connect(self._handle_ijulia_check_finished)
        prog = self._check_ijulia_status_process.program()
        args = self._check_ijulia_status_process.args()
        self._check_ijulia_status_process._process.start(prog, args)
        if (
            self._check_ijulia_status_process._process is not None
            and not self._check_ijulia_status_process._process.waitForStarted(msecs=10000)
        ):
            self.msg.emit(
                f"Julia {prog} failed to start. Please make sure that Julia is correctly installed and try again."
            )
            self._check_ijulia_status_process._process.deleteLater()
            self._check_ijulia_status_process._process = None
            self._check_ijulia_status_process.deleteLater()
            self._check_ijulia_status_process = None
            self.set_failed_state("Creating kernel failed", "Starting Julia failed. See details below.")

    @Slot(int, QProcess.ExitStatus)
    def _handle_ijulia_check_finished(self, exit_code, exit_status):
        """Runs when IJulia status check process has finished.

        Args:
            exit_code (int): Return code from external program
            exit_status (int): QProcess.ExitStatus.NormalExit or QProcess.ExitStatus.CrashExit
        """
        out = str(self._check_ijulia_status_process._process.readAllStandardOutput().data(), "utf-8", errors="replace")
        errout = str(
            self._check_ijulia_status_process._process.readAllStandardError().data(), "utf-8", errors="replace"
        )
        julia = self._check_ijulia_status_process.program()
        self._check_ijulia_status_process._process.deleteLater()
        self._check_ijulia_status_process._process = None
        self._check_ijulia_status_process.deleteLater()
        self._check_ijulia_status_process = None
        if exit_status == QProcess.ExitStatus.CrashExit:
            self.msg_error.emit(errout)
            self.msg.emit(f"Julia process {julia} crashed. Please check that Julia is installed correctly.")
            self.set_failed_state("Creating kernel failed","Julia process crashed. See details below.")
            return
        if exit_code != 0:
            self.msg_error.emit(errout)
            self.msg.emit(f"Julia process {self._julia_exe} failed. See details above.")
            self.set_failed_state("Creating kernel failed","Julia process failed. See details below.")
            return
        if out.strip() == "True":  # IJulia already installed
            self.msg.emit("IJulia is installed")
            self.start_ijulia_installkernel_process()
            return
        # IJulia missing. Ask permission to install it.
        project_ = self._julia_project if self._julia_project else "global"
        message = (
            f"Julia environment<br><br><b>{project_}</b><br><br>"
            f"does not have the <b>IJulia</b> package installed.<br><br>"
            f"IJulia is required for Jupyter integration and must be "
            f"available in this environment to use it in a Jupyter "
            f"Console within Spine Toolbox.<br><br>"
            f"Do you want to install the package now?"
        )
        message_box = QMessageBox(
            QMessageBox.Icon.Question,
            "IJulia missing",
            message,
            QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel,
            parent=self,
        )
        message_box.button(QMessageBox.StandardButton.Ok).setText("Install IJulia")
        if message_box.exec() == QMessageBox.StandardButton.Cancel:
            self.msg_warning.emit(
                "\nInstallation of IJulia was cancelled. This Julia environment will "
                "not be available for use in a Jupyter Console within Spine Toolbox. "
                "You may close the dialog."
            )
            self.set_failed_state("Kernel creating cancelled", "")
            return
        self.start_ijulia_install_process()

    def start_ijulia_install_process(self):
        """Starts installing IJulia package to given Julia project."""
        if not self._julia_project:
            self.msg.emit(f"Installing IJulia for the global project")
        else:
            self.msg.emit(f"Installing IJulia for project {self._julia_project}")
        self.msg.emit("Depending on your system, this process can take a few minutes...")
        args = [f"--project={self._julia_project}", "-e", "try using Pkg catch; end; Pkg.add(ARGS[1])", "IJulia"]
        self._install_ijulia_process = QProcessExecutionManager(self, self._julia_exe, args)
        self._install_ijulia_process._logger.msg_proc_error.connect(self.add_process_error_message)
        self._install_ijulia_process.execution_finished.connect(self._handle_ijulia_install_finished)
        self._install_ijulia_process.start_execution()

    @Slot(int)
    def _handle_ijulia_install_finished(self, ret):
        """Runs when IJulia install process finishes.

        Args:
            ret (int): Process return value. 0: success, !0: failure
        """
        self._install_ijulia_process.execution_finished.disconnect()
        self._install_ijulia_process.deleteLater()
        self._install_ijulia_process = None
        if ret != 0:
            self.msg.emit("Failed to install IJulia- See the process output above for details.")
            self.ui.label_status.setText("Creating kernel failed")
            self.ui.label_in_progress_msg.setText("Installing IJulia failed. See details below.")
            self.set_failed_state("Kernel creating failed", "Installing IJulia failed. See details below.")
            return
        self.msg_success.emit("IJulia successfully installed")
        self.start_ijulia_installkernel_process()

    def start_ijulia_installkernel_process(self):
        """Installs the kernel using IJulia.installkernel function. Given kernel_name
        is the new kernel DISPLAY name prefix. IJulia strips the whitespace and
        uncapitalizes this to make the kernel name automatically. Julia version is
        concatenated to both kernel and display names automatically (This cannot be changed).
        """
        self.msg.emit("Installing Julia kernel")
        args = [
            f"--project={self._julia_project}",
            "-e",
            "using IJulia; installkernel(ARGS[1], ARGS[2])",
            f"{self._julia_kernel_name_prefix}",
            f"--project={self._julia_project}",
        ]
        self._install_julia_kernel_process = QProcessExecutionManager(self, self._julia_exe, args, semisilent=True)
        self._install_julia_kernel_process.execution_finished.connect(self._handle_installkernel_process_finished)
        self._install_julia_kernel_process.start_execution()

    @Slot(int)
    def _handle_installkernel_process_finished(self, retval):
        """Checks whether the IJulia.installkernel process finished successfully.

        Args:
            retval (int): Process return value. 0: success, !0: failure
        """
        self._install_julia_kernel_process.execution_finished.disconnect()
        self._install_julia_kernel_process.deleteLater()
        self._install_julia_kernel_process = None
        if retval != 0:
            self.set_failed_state(f"Creating kernel {self._complete_kernel_name()} failed!", "Please see details below. You may try again or install the kernel manually.")
            return
        self.ui.progressBar.setRange(0, 100)
        self.ui.progressBar.setValue(100)
        self.ui.stackedWidget.setCurrentIndex(2)
        self.ui.pushButton_close.show()
        self._solve_new_kernel_name()
        if not self._new_kernel_name:
            # An existing kernel was overwritten
            self._new_kernel_name = self._complete_kernel_name()
        self.ui.label_success_status.setText(f"Kernel {self._new_kernel_name} created successfully!")
        self.ui.label_executable.setText(f"{self._julia_exe}")
        _project = "global" if not self._julia_project else self._julia_project
        self.ui.label_environment.setText(f"{_project}")

    def _solve_new_kernel_name(self):
        """Finds out the new kernel name after a new kernel has been created."""
        kernel_names_after = custom_find_kernel_specs().keys()
        try:
            self._new_kernel_name = list(set(kernel_names_after) - set(self._kernel_names_before))[0]
        except IndexError:
            pass


def format_event_message(msg_type, message, show_datetime=False):
    """Formats message for the kernel editor text browser.
    This is a copy of helpers.format_event_message() but the colors
    have been edited for a text browser with a white background.
    """
    color = {"msg": "black", "msg_success": "#00b300", "msg_error": "#ff3300", "msg_warning": "#ccad00"}[msg_type]
    open_tag = f"<span style='color:{color};white-space: pre-wrap;'>"
    date_str = get_datetime(show=show_datetime)
    return open_tag + date_str + message + "</span>"


def format_process_message(msg_type, message):
    """Formats process message for the kernel editor text browser."""
    return format_event_message(msg_type, message, show_datetime=False)


class VersionCollector(QThread):
    """Worker thread for collecting Python or Julia versions."""

    versions_collected = Signal(dict)

    def __init__(self, executables: list[str]):
        super().__init__()
        self._executables = executables

    def run(self):
        """Returns a dictionary mapping Julia or Python executable to a version string."""
        versions = dict()
        for p in self._executables:
            ver = self._get_version(p)
            if not ver:
                ver = "x.x"
            versions[p] = ver
        self.versions_collected.emit(versions)

    def _get_version(self, exe):
        """Retrieves given Python or Julia version in a subprocess."""
        if not os.path.exists(exe):
            return None
        manager = QProcessExecutionManager(self, exe, args=["--version"], silent=True)
        manager.start_execution()
        manager.wait_for_process_finished()
        out = manager.process_output  # e.g. 'Python 3.10.8' or 'julia version 1.11.3'
        if not out:
            return None
        try:
            name = out.split()[0].lower()
            ver_list = out.split()[-1].split(".")
            if name == "python":
                ver = f"{ver_list[0]}{ver_list[1]}"
            else:
                ver = f"{ver_list[0]}.{ver_list[1]}"
        except IndexError:
            return None
        return ver
