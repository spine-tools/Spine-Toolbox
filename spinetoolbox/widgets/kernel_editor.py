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

"""Widget for showing the progress of making a Julia or Python kernel."""
import subprocess
from PySide6.QtWidgets import QDialog, QMessageBox, QDialogButtonBox, QWidget
from PySide6.QtCore import Slot, Qt, QTimer
from PySide6.QtGui import QGuiApplication, QIcon
from jupyter_client.kernelspec import find_kernel_specs
from spine_engine.utils.helpers import resolve_current_python_interpreter, resolve_default_julia_executable
from spinetoolbox.execution_managers import QProcessExecutionManager
from spinetoolbox.helpers import (
    busy_effect,
    file_is_valid,
    dir_is_valid,
    ensure_window_is_on_screen,
    get_datetime,
)
from spinetoolbox.logger_interface import LoggerInterface


class KernelEditorBase(QDialog):
    """Base class for kernel editors."""

    def __init__(self, parent, python_or_julia):
        """
        Args:
            parent (SettingsWidget): Parent widget
            python_or_julia (str): kernel type; valid values: "julia", "python"
        """
        super().__init__(parent=parent)
        from ..ui import mini_kernel_editor_dialog  # pylint: disable=import-outside-toplevel

        self.ui = mini_kernel_editor_dialog.Ui_Dialog()
        self.ui.setupUi(self)
        self.setWindowFlags(Qt.WindowType.Window)
        self.setWindowIcon(QIcon(":/symbols/app.ico"))
        # Class attributes
        self._parent = parent
        self.python_or_julia = python_or_julia
        self._app_settings = self._parent.qsettings
        self._logger = LoggerInterface(self)
        self._install_kernel_process = None
        self._install_package_process = None
        self._ipykernel_install_failed = False
        self._install_ijulia_process = None
        self._rebuild_ijulia_process = None
        self._install_julia_kernel_process = None
        self._ready_to_install_kernel = False
        self.kernel_names_before = find_kernel_specs().keys()
        self._new_kernel_name = ""
        self.setAttribute(Qt.WA_DeleteOnClose)
        self._cursors = {w: w.cursor() for w in self.findChildren(QWidget)}
        for widget in self._cursors:
            widget.setCursor(Qt.BusyCursor)
        self.ui.buttonBox.button(QDialogButtonBox.StandardButton.Close).setVisible(False)

    def connect_signals(self):
        """Connects signals to slots."""
        self._logger.msg.connect(self.add_message)
        self._logger.msg_success.connect(self.add_success_message)
        self._logger.msg_warning.connect(self.add_warning_message)
        self._logger.msg_proc.connect(self.add_process_message)
        self._logger.msg_error.connect(self.add_process_error_message)

    def _show_close_button(self, failed=False):
        self.ui.buttonBox.button(QDialogButtonBox.StandardButton.Close).setVisible(True)
        self.ui.buttonBox.button(QDialogButtonBox.StandardButton.Cancel).setVisible(False)
        for widget, cursor in self._cursors.items():
            widget.setCursor(cursor)
        msg = "Done" if not failed else "Failed"
        self.ui.label_message.setText(self.ui.label_message.text() + msg)

    def make_kernel(self):
        QTimer.singleShot(0, self._do_make_kernel)
        self.exec()

    def _do_make_kernel(self):
        raise NotImplementedError()

    def new_kernel_name(self):
        """Returns the new kernel name after it's been created."""
        return self._new_kernel_name

    def _solve_new_kernel_name(self):
        """Finds out the new kernel name after a new kernel has been created."""
        kernel_names_after = find_kernel_specs().keys()
        try:
            self._new_kernel_name = list(set(kernel_names_after) - set(self.kernel_names_before))[0]
        except IndexError:
            pass

    def check_options(self, prgm, kernel_name, display_name, python_or_julia):
        """Checks that user options are valid before advancing with kernel making.

        Args:
            prgm (str): Full path to Python or Julia program
            kernel_name (str): Kernel name
            display_name (str): Kernel display name
            python_or_julia (str): Either 'python' or 'julia'

        Returns:
            bool: True if all user input is valid for making a new kernel, False otherwise
        """
        if prgm.strip() == "":
            if python_or_julia == "python":
                self._logger.msg_error.emit("Python interpreter missing")
            else:
                self._logger.msg_error.emit("Julia executable missing")
            return False
        if not file_is_valid(
            self,
            prgm,
            f"Invalid {'Python Interpreter' if python_or_julia == 'python' else 'Julia Executable'}",
            extra_check=python_or_julia,
        ):
            return False
        return True

    def _python_kernel_name(self):
        raise NotImplementedError()

    def _python_kernel_display_name(self):
        raise NotImplementedError()

    def _python_interpreter_name(self):
        return self.ui.lineEdit_python_interpreter.text()

    @Slot(bool)
    def make_python_kernel(self, checked=False):
        """Makes a new Python kernel. Offers to install ipykernel package if it is
        missing from the selected Python environment. Overwrites existing kernel
        with the same name if this is ok by user."""
        prgm = self._python_interpreter_name()
        if self._ipykernel_install_failed:
            # Makes sure that there's no never-ending loop if ipykernel installation fails for some reason
            self._logger.msg_error.emit(f"Installing package iPyKernel for {prgm} failed. Please install it manually.")
            self._ipykernel_install_failed = False
            return False
        kernel_name = self._python_kernel_name()
        kernel_display_name = self._python_kernel_display_name()
        if kernel_display_name == "":
            kernel_display_name = kernel_name + "_spinetoolbox"  # Default display name if not given
        if not self.check_options(prgm, kernel_name, kernel_display_name, "python"):
            return False
        # Check if ipykernel is installed
        if not self.is_package_installed(prgm, "ipykernel"):
            message = (
                f"Python environment<br><br><b>{prgm}</b><br><br>is missing the <b>ipykernel</b> package, "
                f"which is required for creating a kernel.<br><br>Do you want to install the package now?"
            )
            message_box = QMessageBox(
                QMessageBox.Icon.Question,
                "ipykernel Missing",
                message,
                QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel,
                parent=self,
            )
            message_box.button(QMessageBox.StandardButton.Ok).setText("Install ipykernel")
            answer = message_box.exec()
            if answer == QMessageBox.StandardButton.Cancel:
                return False
            # Install ipykernel
            self.start_package_install_process(prgm, "ipykernel")
            return True
        self.start_kernelspec_install_process(prgm, kernel_name, kernel_display_name)
        return True

    @staticmethod
    def is_package_installed(python_path, package_name):
        """Checks if given package is installed to given Python environment.

        Args:
            python_path (str): Full path to selected Python interpreter
            package_name (str): Package name

        Returns:
            (bool): True if installed, False if not
        """
        response = subprocess.check_output([python_path, "-m", "pip", "freeze", "-q"])
        installed_packages = [r.decode().split("==")[0] for r in response.split()]
        return package_name in installed_packages

    @busy_effect
    def start_package_install_process(self, python_path, package_name):
        """Starts installing the given package using pip.

        Args:
            python_path (str): Full path to selected Python interpreter
            package_name (str): Package name to install using pip
        """
        self._logger.msg.emit(f"Installing {package_name} into {python_path}")
        args = ["-m", "pip", "install", package_name]
        self._install_package_process = QProcessExecutionManager(self._logger, python_path, args)
        self._install_package_process.execution_finished.connect(self.handle_package_install_process_finished)
        self._install_package_process.start_execution()

    @busy_effect
    @Slot(int)
    def handle_package_install_process_finished(self, retval):
        """Handles installing package finished.

        Args:
            retval (int): Process return value. 0: success, !0: failure
        """
        self._install_package_process.execution_finished.disconnect()
        self._install_package_process.deleteLater()
        self._install_package_process = None
        if retval != 0:
            self._ipykernel_install_failed = True
            self._logger.msg_error.emit("Failed")
        else:
            self._ipykernel_install_failed = False
            self._logger.msg_success.emit("Package installation succeeded.")
        self.make_python_kernel()  # Try installing kernel specs now

    @busy_effect
    def start_kernelspec_install_process(self, prgm, k_name, d_name):
        r"""Installs kernel specifications for the given Python environment.
        Runs e.g. this command in QProcess

        python -m ipykernel install --user --name python-X.Y --display-name PythonX.Y

        Creates new kernel specs into %APPDATA%\jupyter\kernels. Existing directory will be overwritten.

        Note: We cannot use --sys.prefix here because if we have selected to create a kernel for some other
        python that was used in launching the app, the kernel will be created into a location that is not discoverable
        by jupyter and hence not by Spine Toolbox. E.g. when sys.executable is C:\Python36\python.exe, and we have
        selected that as the python for Spine Toolbox (Settings->Tools->Python interpreter is empty), creating a
        kernel with --sys-prefix creates kernel specs into C:\Python36\share\jupyter\kernels\python-3.6. This is ok and
        the kernel spec is discoverable by jupyter and Spine Toolbox.

        BUT when sys.executable is C:\Python36\python.exe, and we have selected another python for Spine
        Toolbox (Settings->Tools->Python interpreter is C:\Python38\python.exe), creating a
        kernel with --sys-prefix creates a kernel into C:\Python38\share\jupyter\kernels\python-3.8-sys-prefix. This
        is not discoverable by jupyter nor Spine Toolbox. You would need to start the app using C:\Python38\python.exe
        to see and use that kernel spec.

        Using --user option instead, creates kernel specs that are discoverable by any python that was used in starting
        Spine Toolbox.

        Args:
            prgm (str): Full path to Python interpreter for which the kernel is created
            k_name (str): Kernel name
            d_name (str): Kernel display name
        """
        self._logger.msg.emit("Starting Python kernel spec install process")
        args = ["-m", "ipykernel", "install", "--user", "--name", k_name, "--display-name", d_name]
        self._install_kernel_process = QProcessExecutionManager(self._logger, prgm, args)  # , semisilent=True)
        self._install_kernel_process.execution_finished.connect(self.handle_kernelspec_install_process_finished)
        self._install_kernel_process.start_execution()

    @busy_effect
    @Slot(int)
    def handle_kernelspec_install_process_finished(self, retval):
        """Handles case when the process for installing the kernel has finished.

        Args:
            retval (int): Process return value. 0: success, !0: failure
        """
        self._install_kernel_process.execution_finished.disconnect()
        self._install_kernel_process.deleteLater()
        self._install_kernel_process = None
        if retval != 0:
            self._logger.msg_error.emit("Installing kernel specs failed. Please install them manually.")
            self._logger.msg_error.emit("Failed")
            return
        self._logger.msg_success.emit("New kernel installed")

    def _julia_kernel_name(self):
        raise NotImplementedError()

    def _julia_executable(self):
        return self.ui.lineEdit_julia_executable.text()

    def _julia_project(self):
        return self.ui.lineEdit_julia_project.text()

    @Slot(bool)
    def make_julia_kernel(self, checked=False):
        """Makes a new Julia kernel. Offers to install IJulia package if it is
        missing from the selected Julia project. Overwrites existing kernel
        with the same name if this is ok by user."""
        julia = self._julia_executable()
        project = self._julia_project()
        if project != "@." and not dir_is_valid(self, project, "Invalid Julia Project directory"):
            return False
        kernel_name = self._julia_kernel_name()
        if not self.check_options(julia, kernel_name, kernel_name, "julia"):  # Julia display name cannot be chosen
            return False
        if self._ready_to_install_kernel:
            self.start_ijulia_installkernel_process(julia, project, kernel_name)
            return True
        # Check if IJulia is installed to selected Julia project
        retval = self.is_ijulia_installed(julia, project)
        if retval == 0:  # Julia is not configured correctly
            return False
        if retval == 1:  # IJulia is installed
            if self._is_rebuild_ijulia_needed():
                self.start_ijulia_rebuild_process(julia, project)
            else:
                self.start_ijulia_installkernel_process(julia, project, kernel_name)
            return True
        if retval == 2:  # IJulia is not installed
            project_ = project if project else "default"
            message = (
                f"Julia project <br><br><b>{project_}</b><br><br>is missing the <b>IJulia</b> package, "
                f"which is required for creating a kernel.<br><br>Do you want to install the package now?"
            )
            message_box = QMessageBox(
                QMessageBox.Icon.Question,
                "IJulia missing",
                message,
                QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel,
                parent=self,
            )
            message_box.button(QMessageBox.StandardButton.Ok).setText("Install IJulia")
            answer = message_box.exec()
            if answer == QMessageBox.StandardButton.Cancel:
                return False
            self.start_ijulia_install_process(julia, project)
        return True

    # pylint: disable=no-self-use
    def _is_rebuild_ijulia_needed(self):
        return True

    @busy_effect
    def is_ijulia_installed(self, program, project):
        """Checks if IJulia is installed for the given project.
        Note: Trying command 'using IJulia' does not work since
        it automatically tries loading it from the LOAD_PATH if
        not it's not found in the active project.

        Returns:
            int: 0 when process failed to start, 1 when IJulia is installed, 2 when IJulia is not installed.
        """
        self._logger.msg.emit(f"Checking if IJulia is installed for project {project}")
        args = [
            f"--project={project}",
            "-e",
            "using Pkg; if in(ARGS[1], keys(Pkg.installed())); println(ARGS[2]); else; println(ARGS[3]); end;",
            "IJulia",
            "True",  # This could be anything, as long as we just match this down below
            "False",
        ]
        exec_mngr = QProcessExecutionManager(self._logger, program, args, silent=True)
        exec_mngr.start_execution()
        if not exec_mngr.wait_for_process_finished(msecs=8000):
            self._logger.msg_error.emit(
                "Couldn't start Julia to check IJulia status. "
                "Please make sure that Julia {0} is correctly installed and try again.".format(program)
            )
            self._logger.msg_error.emit("Failed")
            return 0
        if exec_mngr.process_output == "True":
            self._logger.msg.emit("IJulia is installed")
            return 1
        self._logger.msg_warning.emit("IJulia is not installed")
        return 2

    @busy_effect
    def start_ijulia_install_process(self, julia, project):
        """Starts installing IJulia package to given Julia project.

        Args:
            julia (str): Full path to selected Julia executable
            project (str): Julia project (e.g. dir path or '@.', or '.')
        """
        self._logger.msg.emit(f"Installing IJulia for project {project}")
        self._logger.msg.emit("Depending on your system, this process can take a few minutes...")
        args = [f"--project={project}", "-e", "try using Pkg catch; end; Pkg.add(ARGS[1])", "IJulia"]
        self._install_ijulia_process = QProcessExecutionManager(self._logger, julia, args)
        self._install_ijulia_process.execution_finished.connect(self.handle_ijulia_install_finished)
        self._install_ijulia_process.start_execution()

    @busy_effect
    @Slot(int)
    def handle_ijulia_install_finished(self, ret):
        """Runs when IJulia install process finishes.

        Args:
            ret (int): Process return value. 0: success, !0: failure
        """
        self._install_ijulia_process.execution_finished.disconnect()
        self._install_ijulia_process.deleteLater()
        self._install_ijulia_process = None
        if ret != 0:
            self._logger.msg_error.emit("Installing IJulia failed. Please try again later.")
            self._ready_to_install_kernel = False
            return
        self._logger.msg_success.emit("IJulia installed")
        self._ready_to_install_kernel = True
        self.make_julia_kernel()

    @busy_effect
    def start_ijulia_rebuild_process(self, program, project):
        """Starts rebuilding IJulia."""
        self._logger.msg.emit("Rebuilding IJulia")
        self._logger.msg.emit("Depending on your system, this process can take a few minutes...")
        args = [f"--project={project}", "-e", "try using Pkg catch; end; Pkg.build(ARGS[1])", "IJulia"]
        self._rebuild_ijulia_process = QProcessExecutionManager(self._logger, program, args, semisilent=True)
        self._rebuild_ijulia_process.execution_finished.connect(self.handle_ijulia_rebuild_finished)
        self._rebuild_ijulia_process.start_execution()

    @busy_effect
    @Slot(int)
    def handle_ijulia_rebuild_finished(self, ret):
        """Runs when IJulia rebuild process finishes.

        Args:
            ret (int): Process return value. 0: success, !0: failure
        """
        self._rebuild_ijulia_process.execution_finished.disconnect()
        self._rebuild_ijulia_process.deleteLater()
        self._rebuild_ijulia_process = None
        if ret != 0:
            self._logger.msg_error.emit("Rebuilding IJulia failed. Please try again later.")
            self._ready_to_install_kernel = False
            return
        self._logger.msg_success.emit("IJulia rebuilt")
        self._ready_to_install_kernel = True
        self.make_julia_kernel()

    @busy_effect
    def start_ijulia_installkernel_process(self, program, project, kernel_name):
        """Installs the kernel using IJulia.installkernel function. Given kernel_name
        is the new kernel DISPLAY name prefix. IJulia strips the whitespace and
        uncapitalizes this to make the kernel name automatically. Julia version is
        concatenated to both kernel and display names automatically (This cannot be changed).
        """
        self._logger.msg.emit("Installing Julia kernel")
        args = [
            f"--project={project}",
            "-e",
            "using IJulia; installkernel(ARGS[1], ARGS[2])",
            f"{kernel_name}",
            f"--project={project}",
        ]
        self._install_julia_kernel_process = QProcessExecutionManager(self._logger, program, args, semisilent=True)
        self._install_julia_kernel_process.execution_finished.connect(self.handle_installkernel_process_finished)
        self._install_julia_kernel_process.start_execution()

    @busy_effect
    @Slot(int)
    def handle_installkernel_process_finished(self, retval):
        """Checks whether the IJulia.installkernel process finished successfully.

        Args:
            retval (int): Process return value. 0: success, !0: failure
        """
        self._install_julia_kernel_process.execution_finished.disconnect()
        self._install_julia_kernel_process.deleteLater()
        self._install_julia_kernel_process = None
        self._ready_to_install_kernel = False
        if retval != 0:
            self._logger.msg_error.emit("Installing kernel failed")
        else:
            self._logger.msg_success.emit("New kernel installed")

    def restore_dialog_dimensions(self):
        """Restore widget location, dimensions, and state from previous session."""
        dialog_size = self._app_settings.value("kernelEditor/windowSize", defaultValue="false")
        dialog_pos = self._app_settings.value("kernelEditor/windowPosition", defaultValue="false")
        dialog_maximized = self._app_settings.value("kernelEditor/windowMaximized", defaultValue="false")
        splitter_state = self._app_settings.value("kernelEditor/splitterState", defaultValue="false")
        n_screens = self._app_settings.value("mainWindow/n_screens", defaultValue=1)  # Yes, mainWindow
        # noinspection PyArgumentList
        n_screens_now = len(QGuiApplication.screens())  # Number of screens now
        original_size = self.size()
        # Note: cannot use booleans since Windows saves them as strings to registry
        if dialog_size != "false":
            self.resize(dialog_size)  # Expects QSize
        if dialog_pos != "false":
            self.move(dialog_pos)  # Expects QPoint
        if splitter_state != "false":
            self.ui.splitter.restoreState(splitter_state)  # Expects QByteArray
        if n_screens_now < int(n_screens):
            # There are less screens available now than on previous application startup
            # Move dialog to position 0,0 to make sure that it is not lost on another screen that does not exist
            self.move(0, 0)
        ensure_window_is_on_screen(self, original_size)
        if dialog_maximized == "true":
            self.setWindowState(Qt.WindowMaximized)

    @Slot(str)
    def add_message(self, msg):
        """Append regular message to kernel editor text browser.

        Args:
            msg (str): String written to QTextBrowser
        """
        message = format_event_message("msg", msg)
        self.ui.textBrowser_process.append(message)

    @Slot(str)
    def add_success_message(self, msg):
        """Append message with green text color to kernel editor text browser.

        Args:
            msg (str): String written to QTextBrowser
        """
        message = format_event_message("msg_success", msg)
        self.ui.textBrowser_process.append(message)

    @Slot(str)
    def add_error_message(self, msg):
        """Append message with red color to kernel editor text browser.

        Args:
            msg (str): String written to QTextBrowser
        """
        message = format_event_message("msg_error", msg)
        self.ui.textBrowser_process.append(message)

    @Slot(str)
    def add_warning_message(self, msg):
        """Append message with yellow (golden) color to kernel editor text browser.

        Args:
            msg (str): String written to QTextBrowser
        """
        message = format_event_message("msg_warning", msg)
        self.ui.textBrowser_process.append(message)

    @Slot(str)
    def add_process_message(self, msg):
        """Writes message from stdout to kernel editor text browser.

        Args:
            msg (str): String written to QTextBrowser
        """
        message = format_process_message("msg", msg)
        self.ui.textBrowser_process.append(message)

    @Slot(str)
    def add_process_error_message(self, msg):
        """Writes message from stderr to kernel editor text browser.

        Args:
            msg (str): String written to QTextBrowser
        """
        message = format_process_message("msg_error", msg)
        self.ui.textBrowser_process.append(message)

    def _save_ui(self):
        self._app_settings.setValue("kernelEditor/windowSize", self.size())
        self._app_settings.setValue("kernelEditor/windowPosition", self.pos())
        self._app_settings.setValue("kernelEditor/windowMaximized", self.windowState() == Qt.WindowMaximized)
        self._app_settings.setValue("kernelEditor/splitterState", self.ui.splitter.saveState())


class MiniPythonKernelEditor(KernelEditorBase):
    """A Simple Python kernel maker. The Python executable path is passed in
    the constructor, then calling ``make_kernel`` starts the process.
    """

    def __init__(self, parent, python_exe):
        super().__init__(parent, "python")
        self.ui.label_message.setText("Finalizing Python configuration... ")
        self.ui.stackedWidget.setCurrentIndex(0)
        self.setWindowTitle("Python Kernel Specification Creator")
        if not python_exe:
            python_exe = resolve_current_python_interpreter()
        self.ui.lineEdit_python_interpreter.setText(python_exe)
        self.python_exe = python_exe
        self._kernel_name = "python_kernel"  # Fallback name
        self.connect_signals()

    def _julia_kernel_name(self):
        raise NotImplementedError()

    def _python_kernel_name(self):
        return self._kernel_name

    def _python_kernel_display_name(self):
        return ""

    def _do_make_kernel(self):
        if not self.make_python_kernel():
            self._show_close_button(failed=True)

    @busy_effect
    @Slot(int)
    def handle_kernelspec_install_process_finished(self, retval):
        super().handle_kernelspec_install_process_finished(retval)
        self._solve_new_kernel_name()
        self._show_close_button(failed=retval != 0)

    def set_kernel_name(self):
        """Retrieves Python version in a subprocess and makes a kernel name based on it."""
        manager = QProcessExecutionManager(self, self.python_exe, args=["--version"], silent=True)
        manager.start_execution()
        manager.wait_for_process_finished()
        out = manager.process_output  # e.g. 'Python 3.10.8'
        if not out:
            return
        try:
            ver = out.split()[1].split(".")
            ver = ver[0] + ver[1]
        except IndexError:
            return
        self._kernel_name = "python" + ver


class MiniJuliaKernelEditor(KernelEditorBase):
    """A Simple Julia Kernel maker. The julia exe and project are passed in
    the constructor, then calling ``make_kernel`` starts the process.
    """

    def __init__(self, parent, julia_exe, julia_project):
        super().__init__(parent, "julia")
        self.ui.label_message.setText("Finalizing Julia configuration... ")
        self.ui.stackedWidget.setCurrentIndex(1)
        self.setWindowTitle("Julia Kernel Specification Creator")
        if not julia_exe:
            julia_exe = resolve_default_julia_executable()
        self.ui.lineEdit_julia_executable.setText(julia_exe)
        self.ui.lineEdit_julia_project.setText(julia_project)
        self._kernel_name = "julia"  # This is a prefix, IJulia decides the final kernel name
        self.connect_signals()

    def _julia_kernel_name(self):
        return self._kernel_name

    def _python_kernel_name(self):
        raise NotImplementedError()

    def _python_kernel_display_name(self):
        raise NotImplementedError()

    def _do_make_kernel(self):
        if not self.make_julia_kernel():
            self._show_close_button(failed=True)

    @busy_effect
    @Slot(int)
    def handle_installkernel_process_finished(self, retval):
        super().handle_installkernel_process_finished(retval)
        self._solve_new_kernel_name()
        self._show_close_button(failed=retval != 0)


def format_event_message(msg_type, message, show_datetime=True):
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
