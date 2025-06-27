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
from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QGuiApplication, QIcon
from PySide6.QtWidgets import QDialog, QDialogButtonBox, QMessageBox, QWidget, QPushButton
from spine_engine.utils.helpers import (
    custom_find_kernel_specs,
    resolve_current_python_interpreter,
    resolve_default_julia_executable,
)
from spinetoolbox.execution_managers import QProcessExecutionManager
from spinetoolbox.helpers import (
    busy_effect,
    dir_is_valid,
    ensure_window_is_on_screen,
    file_is_valid,
    get_datetime,
    get_current_item_data,
    issamefile,
)
from spinetoolbox.logger_interface import LoggerInterface


class KernelEditorBase(QDialog):
    """Base class for kernel editors."""

    def __init__(self, parent, models):
        """
        Args:
            parent (SettingsWidget): Parent widget
            models (ExecutableCompoundModels): Python and Julia models
        """
        super().__init__(parent=parent)
        from ..ui import mini_kernel_editor_dialog  # pylint: disable=import-outside-toplevel

        self.ui = mini_kernel_editor_dialog.Ui_Dialog()
        self.ui.setupUi(self)
        self.make_kernel_button = QPushButton("Make kernel")
        self.ui.buttonBox.addButton(self.make_kernel_button, QDialogButtonBox.ButtonRole.ActionRole)
        self.setWindowFlags(Qt.WindowType.Window)
        self.setWindowIcon(QIcon(":/symbols/app.ico"))
        # Class attributes
        self._parent = parent
        self._models = models
        self._python_exe = None
        self._python_kernel_name = None
        self._julia_exe = None
        self._julia_project = ""
        self._julia_kernel_name_prefix = None  # This is a prefix, IJulia decides the final kernel name
        self._app_settings = self._parent.qsettings
        self._logger = LoggerInterface(self)
        self._install_kernel_process = None
        self._install_package_process = None
        self._ipykernel_install_failed = False
        self._install_ijulia_process = None
        self._rebuild_ijulia_process = None
        self._install_julia_kernel_process = None
        self._ready_to_install_kernel = False
        self.kernel_names_before = custom_find_kernel_specs().keys()
        self._new_kernel_name = ""
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self._cursors = {w: w.cursor() for w in self.findChildren(QWidget)}
        self.ui.buttonBox.button(QDialogButtonBox.StandardButton.Close).setVisible(False)

    def connect_signals(self):
        """Connects signals to slots."""
        self._logger.msg.connect(self.add_message)
        self._logger.msg_success.connect(self.add_success_message)
        self._logger.msg_warning.connect(self.add_warning_message)
        self._logger.msg_proc.connect(self.add_process_message)
        self._logger.msg_error.connect(self.add_process_error_message)
        self.make_kernel_button.clicked.connect(self.make_kernel)

    def _show_close_button(self, failed=False):
        self.ui.buttonBox.button(QDialogButtonBox.StandardButton.Close).setVisible(True)
        self.ui.buttonBox.button(QDialogButtonBox.StandardButton.Cancel).setVisible(False)
        self.make_kernel_button.setVisible(False)
        for widget, cursor in self._cursors.items():
            widget.setCursor(cursor)
        msg = "Done" if not failed else "Failed"
        self.ui.label_message.setText(self.ui.label_message.text() + msg)

    @Slot(bool)
    def make_kernel(self, _=False):
        if not self._activate_selections():
            return
        for widget in self._cursors:
            widget.setCursor(Qt.CursorShape.BusyCursor)
        self._do_make_kernel()

    def _do_make_kernel(self):
        raise NotImplementedError()

    def _activate_selections(self):
        raise NotImplementedError()

    def new_kernel_name(self):
        """Returns the new kernel name after it's been created."""
        return self._new_kernel_name

    def _solve_new_kernel_name(self):
        """Finds out the new kernel name after a new kernel has been created."""
        kernel_names_after = custom_find_kernel_specs().keys()
        try:
            self._new_kernel_name = list(set(kernel_names_after) - set(self.kernel_names_before))[0]
        except IndexError:
            pass

    @Slot(bool)
    def make_python_kernel(self, _=False):
        """Makes a new Python kernel. Offers to install ipykernel package if it is
        missing from the selected Python environment. Overwrites existing kernel
        with the same name if this is ok by user."""
        if not self._python_exe:
            self._logger.msg.emit("Please select a Python interpreter")
            return False
        if self._ipykernel_install_failed:
            # Makes sure that there's no never-ending loop if ipykernel installation fails for some reason
            self._logger.msg_error.emit(
                f"Installing iPyKernel for {self._python_exe} failed. Please install it manually."
            )
            self._ipykernel_install_failed = False
            return False
        # Check if ipykernel is installed
        try:
            if not self.is_package_installed("ipykernel"):
                message = (
                    f"Python environment<br><br><b>{self._python_exe}</b><br><br>is missing the <b>ipykernel</b> "
                    f"package, which is required for creating a kernel.<br><br>Do you want to install the package now?"
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
                self.start_package_install_process("ipykernel")
                return True
        except subprocess.CalledProcessError:
            return False
        self.start_kernelspec_install_process()
        return True

    def is_package_installed(self, package_name):
        """Checks if package with given name is installed.

        Args:
            package_name (str): Package name

        Returns:
            (bool): True if installed, False if not
        """
        try:
            response = subprocess.check_output(
                [self._python_exe, "-m", "pip", "freeze", "-q"], stderr=subprocess.STDOUT
            )
        except subprocess.CalledProcessError as exc:
            err_msg = exc.output.decode("utf-8")
            err_msgs = err_msg.split("\n")
            for i in range(len(err_msgs)):
                self._logger.msg_error.emit(err_msgs[i].strip("\r"))
            self._logger.msg_warning.emit(
                f"It seems that running the command <b>{self._python_exe} -m pip "
                f"freeze -q</b> failed for some reason. Please try "
                f"installing the Jupyter kernel manually."
            )
            raise
        installed_packages = [r.decode().split("==")[0] for r in response.split()]
        return package_name in installed_packages

    @busy_effect
    def start_package_install_process(self, package_name):
        """Starts installing the given package using pip.

        Args:
            package_name (str): Package name to install using pip
        """
        self._logger.msg.emit(f"Installing {package_name} into {self._python_exe}")
        args = ["-m", "pip", "install", package_name]
        self._install_package_process = QProcessExecutionManager(self._logger, self._python_exe, args)
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
    def start_kernelspec_install_process(self):
        r"""Installs kernel specifications for the given Python environment.
        Runs e.g. this command in QProcess

        python -m ipykernel install --user --name python-X.Y --display-name PythonX.Y

        Creates new kernel specs into %APPDATA%\jupyter\kernels. Existing directory will be overwritten.

        Note: We cannot use --sys.prefix here because if we are creating a kernel for a python that was
        NOT used in launching the app, the kernel will be created into a location that is not discoverable
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
        """
        k_name = self._python_kernel_name
        kd_name = k_name + "_spinetoolbox"
        self._logger.msg.emit("Starting Python kernel spec install process")
        args = ["-m", "ipykernel", "install", "--user", "--name", k_name, "--display-name", kd_name]
        self._install_kernel_process = QProcessExecutionManager(self._logger, self._python_exe, args)  # semisilent=True
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
        self._show_close_button(failed=retval != 0)
        if retval != 0:
            self._logger.msg_error.emit("Installing kernel specs failed. Please install them manually.")
            return
        self._logger.msg_success.emit("New kernel installed")
        self._solve_new_kernel_name()  # TODO: This is probably not necessary for Python kernels
        self.ui.label_python_kernel_name.setText(f"Click Close to activate kernel {self._new_kernel_name}")

    @Slot(bool)
    def make_julia_kernel(self, _=False):
        """Makes a new Julia kernel. Offers to install IJulia package if it is
        missing from the selected Julia project. Overwrites existing kernel
        with the same name if this is ok by user."""
        if not self._julia_exe:
            self._logger.msg.emit("Please select a Julia executable")
            return False
        if self._julia_project != "@." and not dir_is_valid(
            self, self._julia_project, "Invalid Julia Project directory"
        ):
            return False
        if self._ready_to_install_kernel:
            self.start_ijulia_installkernel_process()
            return True
        # Check if IJulia is installed to selected Julia project
        retval = self.is_ijulia_installed()
        if retval == 0:  # Julia is not configured correctly
            return False
        if retval == 1:  # IJulia is installed
            if self._is_rebuild_ijulia_needed():
                self.start_ijulia_rebuild_process()
            else:
                self.start_ijulia_installkernel_process()
            return True
        if retval == 2:  # IJulia is not installed
            project_ = self._julia_project if self._julia_project else "default"
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
            self.start_ijulia_install_process()
        return True

    @staticmethod
    def _is_rebuild_ijulia_needed():
        return True

    @busy_effect
    def is_ijulia_installed(self):
        """Checks if IJulia is installed for the selected project.
        Note: Trying command 'using IJulia' does not work since
        it automatically tries loading it from the LOAD_PATH if
        not it's not found in the active project.

        Returns:
            int: 0 when process failed to start, 1 when IJulia is installed, 2 when IJulia is not installed.
        """
        self._logger.msg.emit(f"Checking if IJulia is installed for project {self._julia_project}")
        args = [
            f"--project={self._julia_project}",
            "-e",
            "using Pkg; if in(ARGS[1], keys(Pkg.installed())); println(ARGS[2]); else; println(ARGS[3]); end;",
            "IJulia",
            "True",  # This could be anything, as long as we just match this down below
            "False",
        ]
        exec_mngr = QProcessExecutionManager(self._logger, self._julia_exe, args, silent=True)
        exec_mngr.start_execution()
        if not exec_mngr.wait_for_process_finished(msecs=8000):
            self._logger.msg_error.emit(
                f"Couldn't start Julia to check IJulia status. "
                f"Please make sure that Julia {self._julia_exe} is correctly installed and try again."
            )
            self._logger.msg_error.emit("Failed")
            return 0
        if exec_mngr.process_output == "True":
            self._logger.msg.emit("IJulia is installed")
            return 1
        self._logger.msg_warning.emit("IJulia is not installed")
        return 2

    @busy_effect
    def start_ijulia_install_process(self):
        """Starts installing IJulia package to given Julia project."""
        self._logger.msg.emit(f"Installing IJulia for project {self._julia_project}")
        self._logger.msg.emit("Depending on your system, this process can take a few minutes...")
        args = [f"--project={self._julia_project}", "-e", "try using Pkg catch; end; Pkg.add(ARGS[1])", "IJulia"]
        self._install_ijulia_process = QProcessExecutionManager(self._logger, self._julia_exe, args)
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
    def start_ijulia_rebuild_process(self):
        """Starts rebuilding IJulia."""
        self._logger.msg.emit("Rebuilding IJulia")
        self._logger.msg.emit("Depending on your system, this process can take a few minutes...")
        args = [f"--project={self._julia_project}", "-e", "try using Pkg catch; end; Pkg.build(ARGS[1])", "IJulia"]
        self._rebuild_ijulia_process = QProcessExecutionManager(self._logger, self._julia_exe, args, semisilent=True)
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
    def start_ijulia_installkernel_process(self):
        """Installs the kernel using IJulia.installkernel function. Given kernel_name
        is the new kernel DISPLAY name prefix. IJulia strips the whitespace and
        uncapitalizes this to make the kernel name automatically. Julia version is
        concatenated to both kernel and display names automatically (This cannot be changed).
        """
        self._logger.msg.emit("Installing Julia kernel")
        args = [
            f"--project={self._julia_project}",
            "-e",
            "using IJulia; installkernel(ARGS[1], ARGS[2])",
            f"{self._julia_kernel_name_prefix}",
            f"--project={self._julia_project}",
        ]
        # TODO: IJulia.installkernel() should return new kernel path. If we can get
        #  it, there's no need for _solve_new_kernel_name()
        self._install_julia_kernel_process = QProcessExecutionManager(
            self._logger, self._julia_exe, args, semisilent=True
        )
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
        self._show_close_button(failed=retval != 0)
        if retval != 0:
            self._logger.msg_error.emit("Installing kernel specs failed. Please install them manually.")
            return
        self._logger.msg_success.emit("New kernel installed")
        self._solve_new_kernel_name()
        self.ui.label_julia_kernel_name.setText(f"Click Close to activate kernel {self._new_kernel_name}")

    def make_kernel_name(self, exe, prefix):
        """Retrieves Python or Julia version in a subprocess and makes a kernel name based on it."""
        manager = QProcessExecutionManager(self, exe, args=["--version"], silent=True)
        manager.start_execution()
        manager.wait_for_process_finished()
        out = manager.process_output  # e.g. 'Python 3.10.8' or 'julia version 1.11.3'
        if not out:
            return None
        try:
            name = out.split()[0].lower()
            ver_list = out.split()[-1].split(".")
            prefix = prefix.lower().replace(" ", "-")
            if name == "python":
                ver = ver_list[0] + ver_list[1]
            else:
                ver = f"-{ver_list[0]}.{ver_list[1]}"
        except IndexError:
            return None
        return prefix + ver

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
            self.setWindowState(Qt.WindowState.WindowMaximized)

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
        self._app_settings.setValue(
            "kernelEditor/windowMaximized", self.windowState() == Qt.WindowState.WindowMaximized
        )
        self._app_settings.setValue("kernelEditor/splitterState", self.ui.splitter.saveState())


class MiniPythonKernelEditor(KernelEditorBase):
    """A Simple Python kernel maker."""

    def __init__(self, parent, models):
        super().__init__(parent, models)
        self.setWindowTitle("Python Jupyter Kernel Creator")
        self.ui.label_message.setText("Select a Python interpreter and click Make kernel...")
        self.ui.stackedWidget.setCurrentIndex(0)
        self.ui.comboBox_python_interpreter.setModel(self._models.python_interpreters_model)
        self._models.refresh_python_interpreters_model(show_select_item=True)
        self.ui.comboBox_python_interpreter.setCurrentIndex(0)
        self.ui.lineEdit_python_kernel_name_prefix.setText("python")
        self.ui.label_python_kernel_name.clear()
        self.connect_signals()

    def connect_signals(self):
        super().connect_signals()
        self.ui.comboBox_python_interpreter.currentIndexChanged.connect(self._set_python_exe)
        self.ui.lineEdit_python_kernel_name_prefix.textEdited.connect(self._set_kernel_name)

    def _activate_selections(self):
        if not self._set_python_exe(0):
            self._logger.msg_warning.emit("Please select a Python interpreter")
            return False
        self.ui.label_message.setText("Finalizing Python configuration... ")
        return True

    @Slot(int)
    def _set_python_exe(self, _ind):
        self.ui.buttonBox.button(QDialogButtonBox.StandardButton.Close).setVisible(False)
        self.ui.buttonBox.button(QDialogButtonBox.StandardButton.Cancel).setVisible(True)
        self.make_kernel_button.setVisible(True)
        data = get_current_item_data(self.ui.comboBox_python_interpreter, self._models.python_interpreters_model)
        if not data:
            self._python_exe = None
            self.ui.label_python_kernel_name.clear()
            return False
        self._python_exe = data["exe"]
        if not self._python_exe:
            self._python_exe = resolve_current_python_interpreter()
        python_kernel_found = _get_python_kernel_name_by_exe(self._python_exe, self._models.python_kernel_model)
        if python_kernel_found:
            self._logger.msg.emit(
                f"Python kernel <b>{python_kernel_found}</b> using Python "
                f"<b>{self._python_exe}</b> already exists. Click Close to activate it or edit "
                f"kernel name below to make a new one."
            )
            self._new_kernel_name = python_kernel_found
            self.ui.buttonBox.button(QDialogButtonBox.StandardButton.Close).setVisible(True)
            self.ui.buttonBox.button(QDialogButtonBox.StandardButton.Cancel).setVisible(False)
            self.make_kernel_button.setVisible(False)
            self.ui.label_python_kernel_name.setText(f"Click Close to activate kernel {python_kernel_found}")
            return False
        prefix = self.ui.lineEdit_python_kernel_name_prefix.text().strip()
        self._python_kernel_name = self.make_kernel_name(self._python_exe, prefix)
        if not self._python_kernel_name:
            self._logger.msg_error.emit(
                f"Something went wrong. Retrieving version of python {self._python_exe} failed. "
                f"Please select another Python or try reinstalling"
            )
            self.ui.label_python_kernel_name.setText("Kernel name unavailable")
            return False
        self.ui.label_python_kernel_name.setText(f"New kernel name will be {self._python_kernel_name}")
        return True

    @Slot(str)
    def _set_kernel_name(self, edited_text):
        kname = self.make_kernel_name(self._python_exe, edited_text)
        self._python_kernel_name = kname
        knames = _get_kernel_names(self._models.python_kernel_model)
        if kname in knames:
            self.ui.label_python_kernel_name.setText(f"Kernel {kname} already exists. Click Close to activate it.")
            self._new_kernel_name = kname
            self.ui.buttonBox.button(QDialogButtonBox.StandardButton.Close).setVisible(True)
            self.ui.buttonBox.button(QDialogButtonBox.StandardButton.Cancel).setVisible(False)
            self.make_kernel_button.setVisible(False)
        else:
            self.ui.label_python_kernel_name.setText(f"New kernel name will be: {kname}")
            self.ui.buttonBox.button(QDialogButtonBox.StandardButton.Close).setVisible(False)
            self.ui.buttonBox.button(QDialogButtonBox.StandardButton.Cancel).setVisible(True)
            self.make_kernel_button.setVisible(True)

    def _do_make_kernel(self):
        if not self.make_python_kernel():
            self._show_close_button(failed=True)


class MiniJuliaKernelEditor(KernelEditorBase):
    """A Simple Julia Kernel maker."""

    def __init__(self, parent, models):
        super().__init__(parent, models)
        self._julia_kernel_name_prefix = "julia"
        self.setWindowTitle("Julia Jupyter Kernel Creator")
        self.ui.label_message.setText("Select a Julia executable and a project and click Make kernel...")
        self.ui.stackedWidget.setCurrentIndex(1)
        self.ui.comboBox_julia_executable.setModel(self._models.julia_executables_model)
        self.ui.comboBox_julia_project.setModel(self._models.julia_projects_model)
        self._models.refresh_julia_executables_model(show_select_item=True)
        self._models.refresh_julia_projects_model(show_select_item=False)  # No 'Select Julia project...' item
        self.ui.comboBox_julia_executable.setCurrentIndex(0)
        self.ui.comboBox_julia_project.setCurrentIndex(0)
        self.ui.label_julia_kernel_name.clear()
        self.ui.lineEdit_julia_kernel_name_prefix.setText(self._julia_kernel_name_prefix)
        self.connect_signals()

    def connect_signals(self):
        super().connect_signals()
        self.ui.comboBox_julia_executable.currentIndexChanged.connect(self._set_julia_exe)
        self.ui.comboBox_julia_project.currentIndexChanged.connect(self._set_julia_project)
        self.ui.lineEdit_julia_kernel_name_prefix.textEdited.connect(self._set_kernel_name)

    def _activate_selections(self):
        self.ui.buttonBox.button(QDialogButtonBox.StandardButton.Close).setVisible(False)
        self.ui.buttonBox.button(QDialogButtonBox.StandardButton.Cancel).setVisible(True)
        self.make_kernel_button.setVisible(True)
        if not self._julia_exe:
            self._logger.msg_warning.emit("Please select a Julia executable")
            return False
        self.ui.label_message.setText("Finalizing Julia configuration... ")
        return True

    @Slot(int)
    def _set_julia_exe(self, _ind):
        data = get_current_item_data(self.ui.comboBox_julia_executable, self._models.julia_executables_model)
        if not data:
            self._julia_exe = None
            self.ui.label_julia_kernel_name.clear()
            return False
        self._julia_exe = data["exe"]
        if not self._julia_exe:
            self._julia_exe = resolve_default_julia_executable()
        prefix = self.ui.lineEdit_julia_kernel_name_prefix.text().strip()
        kernel_name = self.make_kernel_name(self._julia_exe, prefix)
        if not kernel_name:
            self._logger.msg_error.emit(
                f"Something went wrong. Retrieving version of Julia {self._julia_exe} failed. "
                f"Please select another Julia or try reinstalling"
            )
            self.ui.label_julia_kernel_name.setText("Kernel name unavailable")
            return False
        if self._check_existing_kernels():
            return False
        if self._kernel_exists(kernel_name):
            return False
        self.ui.label_julia_kernel_name.setText(f"New kernel name will be {kernel_name}")
        return True

    @Slot(int)
    def _set_julia_project(self, _ind):
        data = get_current_item_data(self.ui.comboBox_julia_project, self._models.julia_projects_model)
        self._julia_project = data["path"]
        prefix = self.ui.lineEdit_julia_kernel_name_prefix.text().strip()
        if not self._julia_exe:
            return False
        kernel_name = self.make_kernel_name(self._julia_exe, prefix)
        if not kernel_name:
            self._logger.msg_error.emit(
                f"Something went wrong. Retrieving version of Julia {self._julia_exe} failed. "
                f"Please select another Julia or try reinstalling"
            )
            self.ui.label_julia_kernel_name.setText("Kernel name unavailable")
            return False
        if self._check_existing_kernels():
            return False
        if self._kernel_exists(kernel_name):
            return False
        self.ui.label_julia_kernel_name.setText(f"New kernel name will be {kernel_name}")
        return True

    @Slot(str)
    def _set_kernel_name(self, edited_text):
        kname = self.make_kernel_name(self._julia_exe, edited_text)
        self._julia_kernel_name_prefix = edited_text
        # Check if the resolved kernel_name already exists
        if self._kernel_exists(kname):
            return False
        self._restore_defaults()
        if kname is not None:
            self.ui.label_julia_kernel_name.setText(f"New kernel name will be {kname}")
        return True

    def _kernel_exists(self, kname):
        """Checks if a kernel with the given name already exists in the Julia kernel model."""
        if kname in _get_kernel_names(self._models.julia_kernel_model):
            self._new_kernel_name = kname
            self.ui.label_message.setText(f"Kernel {kname} already exists. Click Close to activate.")
            self.ui.textBrowser_process.clear()
            kernel_exe = _get_kernel_exe(kname, self._models.julia_kernel_model)
            kernel_project = _get_julia_kernel_project(kname, self._models.julia_kernel_model)
            kernel_project = "HOME" if not kernel_project else kernel_project
            self._logger.msg.emit(
                f"Kernel <b>{kname}</b> using exe <b>{kernel_exe}</b> and project <b>{kernel_project}</b> "
                f"already exists. Edit the Julia kernel prefix to make a new one."
            )
            self.ui.label_julia_kernel_name.setText(f"Click Close to activate kernel {kname}")
            self.ui.buttonBox.button(QDialogButtonBox.StandardButton.Close).setVisible(True)
            self.ui.buttonBox.button(QDialogButtonBox.StandardButton.Cancel).setVisible(False)
            self.make_kernel_button.setVisible(False)
            return True
        return False

    def _check_existing_kernels(self):
        """Checks if a kernel with the selected exe/project already exists."""
        if not self._julia_exe:
            return False
        existing_kernel = _get_julia_kernel_name_by_exe(self._julia_exe, self._models.julia_kernel_model)
        if existing_kernel:
            self.ui.textBrowser_process.clear()
            match_found = _selected_project_matches_kernel_project(
                existing_kernel, self._julia_project, self._models.julia_kernel_model
            )
            kernel_project = "HOME" if not self._julia_project else self._julia_project
            if match_found:
                self.ui.label_message.setText(
                    f"Kernel {existing_kernel} using your selections already exists. " f"Click Close to activate it."
                )
                self._logger.msg.emit(
                    f"Kernel <b>{existing_kernel}</b> executable <b>{self._julia_exe}</b> and "
                    f"project <b>{kernel_project}</b> match your selections."
                )
            else:
                kernels_project = _get_julia_kernel_project(existing_kernel, self._models.julia_kernel_model)
                self.ui.label_message.setText(
                    f"Kernel {existing_kernel} is available but project does not match your "
                    f"selection. Click Close to activate it anyway."
                )
                self._logger.msg.emit(
                    f"Kernel <b>{existing_kernel}</b> using the selected Julia "
                    f"is available but the project does not match your selection. Kernel "
                    f"<b>{existing_kernel}</b> uses project <b>{kernels_project}</b>. Click "
                    f"Close to activate this kernel or edit the Julia kernel prefix and "
                    f"click Make kernel."
                )
            self._new_kernel_name = existing_kernel
            self.ui.buttonBox.button(QDialogButtonBox.StandardButton.Close).setVisible(True)
            self.ui.buttonBox.button(QDialogButtonBox.StandardButton.Cancel).setVisible(False)
            self.make_kernel_button.setVisible(False)
            self.ui.label_julia_kernel_name.setText(f"Click Close to activate kernel {existing_kernel}")
            return True
        self._restore_defaults()
        return False

    def _restore_defaults(self):
        """Clears text browser, resets label, and shows default buttons."""
        self.ui.textBrowser_process.clear()
        self.ui.label_message.setText("Select a Julia executable and a project and click Make kernel...")
        self.ui.buttonBox.button(QDialogButtonBox.StandardButton.Close).setVisible(False)
        self.ui.buttonBox.button(QDialogButtonBox.StandardButton.Cancel).setVisible(True)
        self.make_kernel_button.setVisible(True)

    def _do_make_kernel(self):
        if not self.make_julia_kernel():
            self._show_close_button(failed=True)


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


def _get_kernel_names(kernel_model):
    """Returns available kernel names from the given model in a list."""
    knames = list()
    for i in range(1, kernel_model.rowCount()):  # Start from row 1
        item_data = kernel_model.item(i).data()
        if not item_data["is_jupyter"]:
            continue
        name = kernel_model.item(i).data(Qt.ItemDataRole.DisplayRole)
        knames.append(name)
    return knames


def _get_julia_kernel_name_by_exe(p, kernel_model):
    if not p:
        p = resolve_default_julia_executable()
    return _get_kernel_name_by_exe(p, kernel_model)


def _get_python_kernel_name_by_exe(p, kernel_model):
    if not p:
        p = resolve_current_python_interpreter()
    return _get_kernel_name_by_exe(p, kernel_model)


def _get_kernel_name_by_exe(p, kernel_model):
    """Returns the kernel name corresponding to given executable or an empty string if not found.

    Args:
        p (str): Absolute path to an executable
        kernel_model (QStandardItemModel): Model with items containing kernel spec details

    Returns:
        str: Kernel name or an empty string
    """
    for i in range(1, kernel_model.rowCount()):  # Start from row 1
        item_data = kernel_model.item(i).data()
        if not item_data["is_jupyter"]:
            continue
        name = kernel_model.item(i).data(Qt.ItemDataRole.DisplayRole)
        deats = kernel_model.item(i).data()
        if not deats:
            continue
        try:
            if issamefile(deats["exe"], p):
                return name
        except KeyError:
            pass  # Conda kernel deats don't have the "exe" key
    return ""


def _selected_project_matches_kernel_project(julia_kernel_name, julia_project, kernel_model):
    """Checks if given Julia kernel's project matches the given Julia project.

    Args:
        julia_kernel_name (str): Kernel name
        julia_project (str): Path or some other string (e.g. '@.') to denote the Julia project
        kernel_model (QStandardItemModel): Model containing kernels

    Returns:
        bool: True if projects match, False otherwise
    """
    for row in range(1, kernel_model.rowCount()):  # Start from row 1
        if kernel_model.item(row).data(Qt.ItemDataRole.DisplayRole) == julia_kernel_name:
            deats = kernel_model.item(row).data()
            if not deats or "project" not in deats.keys():
                continue
            if issamefile(deats["project"], julia_project) or deats["project"] == julia_project:
                return True
    return False


def _get_kernel_exe(kname, kernel_model):
    """Returns the executable associated to given kernel name."""
    for row in range(1, kernel_model.rowCount()):  # Start from row 1
        if kernel_model.item(row).data(Qt.ItemDataRole.DisplayRole) == kname:
            deats = kernel_model.item(row).data()
            return deats["exe"]
    return None


def _get_julia_kernel_project(kname, kernel_model):
    """Returns the project associated with given Julia kernel."""
    for row in range(1, kernel_model.rowCount()):  # Start from row 1
        if kernel_model.item(row).data(Qt.ItemDataRole.DisplayRole) == kname:
            deats = kernel_model.item(row).data()
            if not deats or "project" not in deats.keys():
                continue
            return deats["project"]
    return None
