######################################################################################################################
# Copyright (C) 2017-2021 Spine project consortium
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""
Dialog for selecting a kernel or creating a new Julia or Python kernel.

:author: P. Savolainen (VTT)
:date:   7.10.2020
"""
import os
import shutil
import json
import subprocess
from PySide2.QtWidgets import QDialog, QMenu, QMessageBox, QAbstractItemView, QApplication, QDialogButtonBox
from PySide2.QtCore import Slot, Qt, QModelIndex
from PySide2.QtGui import QStandardItemModel, QStandardItem, QGuiApplication, QIcon
from jupyter_client.kernelspec import find_kernel_specs
from spine_engine.utils.helpers import resolve_python_interpreter, resolve_julia_executable_from_path
from spinetoolbox.execution_managers import QProcessExecutionManager
from spinetoolbox.helpers import (
    open_url,
    busy_effect,
    select_python_interpreter,
    select_julia_executable,
    select_julia_project,
    file_is_valid,
    dir_is_valid,
    ensure_window_is_on_screen,
    get_datetime,
)
from spinetoolbox.config import MAINWINDOW_SS
from spinetoolbox.logger_interface import LoggerInterface


class KernelEditor(QDialog):
    """Class for a Python and Julia kernel editor."""

    def __init__(self, parent, python, julia, python_or_julia, current_kernel):
        """

        Args:
            parent (QWidget): Parent widget (Settings widget)
            python (str): Python interpreter, may be empty string
            julia (str): Julia executable, may be empty string
            python_or_julia (str): Setup KernelEditor according to selected mode
            current_kernel (str): Current selected Python or Julia kernel name
        """
        from ..ui import kernel_editor_dialog  # pylint: disable=import-outside-toplevel

        super().__init__(parent=parent)  # Inherits stylesheet from SettingsWindow
        self.setWindowFlags(Qt.Window)
        self.setup_dialog_style()
        # Class attributes
        self._parent = parent  # QSettingsWidget
        self._app_settings = self._parent._qsettings
        self._logger = LoggerInterface()
        self.ui = kernel_editor_dialog.Ui_Dialog()
        self.ui.setupUi(self)
        self.kernel_list_model = QStandardItemModel()
        self._kernel_list_context_menu = QMenu(self)
        self.selected_kernel = None
        self._install_kernel_process = None
        self._install_package_process = None
        self._ipykernel_install_failed = False
        self._install_ijulia_process = None
        self._rebuild_ijulia_process = None
        self._install_julia_kernel_process = None
        self._ready_to_install_kernel = False
        self.old_kernel_names = list()
        self.python_or_julia = python_or_julia
        # Set up
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.populate_kernel_model()
        if python_or_julia == "python":
            self.ui.stackedWidget.setCurrentIndex(0)
            self.setWindowTitle("Python Kernel Specification Editor")
            self.ui.label.setText("Available Python kernel specs")
            if python == "":
                python = resolve_python_interpreter(python)
            self.ui.lineEdit_python_interpreter.setText(python)
            self.update_python_cmd_tooltip()
        else:
            self.ui.stackedWidget.setCurrentIndex(1)
            self.setWindowTitle("Julia Kernel Specification Editor")
            self.ui.label.setText("Available Julia kernel specs")
            if julia == "":
                julia = resolve_julia_executable_from_path()
            self.ui.lineEdit_julia_executable.setText(julia)
            self.update_julia_cmd_tooltip()
        self.ui.tableView_kernel_list.setModel(self.kernel_list_model)
        self.ui.tableView_kernel_list.resizeColumnsToContents()
        self.set_kernel_selected(current_kernel)
        self.connect_signals()
        self._mouse_press_pos = None
        self._mouse_release_pos = None
        self._mouse_move_pos = None
        self.restore_dialog_dimensions()
        self._update_ok_button_enabled()

    def setup_dialog_style(self):
        """Sets windows icon and stylesheet.
        This can be removed when SettingsWidget
        inherits stylesheet from ToolboxUI."""
        self.setWindowIcon(QIcon(":/symbols/app.ico"))
        self.setStyleSheet(MAINWINDOW_SS)

    def connect_signals(self):
        """Connects signals to slots."""
        # pylint: disable=unnecessary-lambda
        self.ui.tableView_kernel_list.selectionModel().selectionChanged.connect(self._handle_kernel_selection_changed)
        self.ui.pushButton_make_python_kernel.clicked.connect(self.make_python_kernel)
        self.ui.pushButton_make_julia_kernel.clicked.connect(self.make_julia_kernel)
        self.ui.tableView_kernel_list.selectionModel().currentChanged.connect(self._check_kernel_is_ok)
        self.ui.tableView_kernel_list.customContextMenuRequested.connect(self.show_kernel_list_context_menu)
        self._kernel_list_context_menu.addAction("Open kernel.json", self._open_kernel_json)
        self._kernel_list_context_menu.addAction("Open containing folder", self._open_kernel_dir)
        self._kernel_list_context_menu.addSeparator()
        self._kernel_list_context_menu.addAction("Remove kernel", self._remove_kernel)
        self.ui.toolButton_select_python.clicked.connect(self.select_python_clicked)
        self.ui.toolButton_select_julia.clicked.connect(self.select_julia_clicked)
        self.ui.toolButton_select_julia_project.clicked.connect(self.select_julia_project_clicked)
        self.ui.lineEdit_python_kernel_name.textEdited.connect(self.python_kernel_name_edited)
        self.ui.lineEdit_python_kernel_display_name.textEdited.connect(lambda: self.update_python_cmd_tooltip())
        self.ui.lineEdit_julia_kernel_name.textEdited.connect(lambda: self.update_julia_cmd_tooltip())
        self.ui.lineEdit_julia_project.textEdited.connect(lambda: self.update_julia_cmd_tooltip())
        self._logger.msg.connect(self.add_message)
        self._logger.msg_success.connect(self.add_success_message)
        self._logger.msg_warning.connect(self.add_warning_message)
        self._logger.msg_proc.connect(self.add_process_message)
        self._logger.msg_error.connect(self.add_process_error_message)

    @Slot("QItemSelection", "QItemSelection")
    def _handle_kernel_selection_changed(self, _selected, _deselected):
        self._update_ok_button_enabled()

    def _update_ok_button_enabled(self):
        self.ui.buttonBox.button(QDialogButtonBox.Ok).setEnabled(
            self.ui.tableView_kernel_list.selectionModel().hasSelection()
        )

    @Slot(str)
    def python_kernel_name_edited(self, txt):
        """Updates the display name place holder text and the command QCustomLabel tool tip."""
        self.ui.lineEdit_python_kernel_display_name.setPlaceholderText(txt + "_spinetoolbox")
        self.update_python_cmd_tooltip()

    @Slot(bool)
    def select_julia_clicked(self, checked=False):
        """Opens file browser where user can select a Julia executable for the new kernel."""
        select_julia_executable(self, self.ui.lineEdit_julia_executable)
        self.update_julia_cmd_tooltip()

    @Slot(bool)
    def select_julia_project_clicked(self, checked=False):
        """Opens file browser where user can select a Julia project path for the new kernel."""
        select_julia_project(self, self.ui.lineEdit_julia_project)
        self.update_julia_cmd_tooltip()

    @Slot(bool)
    def select_python_clicked(self, checked=False):
        """Opens file browser where user can select the python interpreter for the new kernel."""
        select_python_interpreter(self, self.ui.lineEdit_python_interpreter)
        self.update_python_cmd_tooltip()

    def update_python_cmd_tooltip(self):
        """Updates Python command (CustomQLabel) tooltip according to selections."""
        interpreter = self.ui.lineEdit_python_interpreter.text()
        kernel_name = self.ui.lineEdit_python_kernel_name.text()
        if kernel_name == "":
            kernel_name = "NA"
            kernel_display_name = "NA"
        else:
            if self.ui.lineEdit_python_kernel_display_name.text() == "":
                kernel_display_name = self.ui.lineEdit_python_kernel_display_name.placeholderText()
            else:
                kernel_display_name = self.ui.lineEdit_python_kernel_display_name.text()
        tip = (
            interpreter
            + " -m ipykernel install --user --name "
            + kernel_name
            + " --display-name "
            + kernel_display_name
        )
        self.ui.label_python_cmd.setToolTip(tip)

    def update_julia_cmd_tooltip(self):
        """Updates Julia command (CustomQLabel) tooltip according to selections."""
        kernel_name = self.ui.lineEdit_julia_kernel_name.text().strip()
        project = self.ui.lineEdit_julia_project.text().strip()
        if kernel_name == "":
            kernel_name = "NA"
        tip = f"IJulia.installkernel({kernel_name}, --project={project})"
        self.ui.label_julia_cmd.setToolTip(tip)

    def set_kernel_selected(self, k_name):
        """Finds row index of given kernel name from the model,
        sets it selected and scrolls the view so that it's visible.

        Args:
            k_name (str): Kernel name to find and select
        """
        index = QModelIndex()  # Just in case it's not found
        if not k_name:
            self.ui.tableView_kernel_list.setCurrentIndex(index)
            return
        name_column = self.find_column("Name")
        for row in range(self.kernel_list_model.rowCount(self.ui.tableView_kernel_list.rootIndex())):
            row_index = self.kernel_list_model.index(row, name_column, self.ui.tableView_kernel_list.rootIndex())
            if k_name == row_index.data(Qt.DisplayRole):
                index = row_index
                break
        self.ui.tableView_kernel_list.setCurrentIndex(index)
        self.ui.tableView_kernel_list.scrollTo(index, QAbstractItemView.ScrollHint.PositionAtTop)

    @Slot("QModelIndex", "QModelIndex")
    def _check_kernel_is_ok(self, current, previous):
        """Shows a notification if there are any known problems with selected kernel.

        Args:
            current (QModelIndex): Currently selected index
            previous (QModelIndex): Previously selected index
        """
        if not current.isValid():
            return
        d = current.siblingAtColumn(self.find_column("Location")).data(Qt.DisplayRole)  # Location column
        kernel_json = os.path.join(d, "kernel.json")
        if not os.path.exists(kernel_json):
            self._logger.msg_error.emit(f"Path {kernel_json} does not exist")
            return
        if os.stat(kernel_json).st_size == 0:
            self._logger.msg_error.emit(f"{kernel_json} is empty")
            return
        with open(kernel_json, "r") as fh:
            try:
                json.load(fh)
            except json.decoder.JSONDecodeError:
                self._logger.msg_error.emit("Error in kernel.json file. Invalid JSON.")
                return

    def find_column(self, label):
        """Returns the column number from the kernel model with the given label.

        Args:
            label (str): Header column label

        Returns:
            int: Column number or -1 if label not found
        """
        for column in range(self.kernel_list_model.columnCount()):
            if self.kernel_list_model.headerData(column, Qt.Horizontal) == label:
                return column
        return -1

    @Slot(bool)
    def make_python_kernel(self, checked=False):
        """Makes a new Python kernel. Offers to install ipykernel package if it is
        missing from the selected Python environment. Overwrites existing kernel
        with the same name if this is ok by user."""
        prgm = self.ui.lineEdit_python_interpreter.text()
        if self._ipykernel_install_failed:
            # Makes sure that there's no never-ending loop if ipykernel installation fails for some reason
            self._logger.msg_error.emit(f"Installing package iPyKernel for {prgm} failed. Please install it manually.")
            self._ipykernel_install_failed = False
            return
        kernel_name = self.ui.lineEdit_python_kernel_name.text()
        kernel_display_name = self.ui.lineEdit_python_kernel_display_name.text()
        if kernel_display_name == "":
            kernel_display_name = kernel_name + "_spinetoolbox"  # Default display name if not given
        if not self.check_options(prgm, kernel_name, kernel_display_name, "python"):
            return
        # Check if ipykernel is installed
        if not self.is_package_installed(prgm, "ipykernel"):
            message = (
                f"Python environment<br><br><b>{prgm}</b><br><br>is missing the <b>ipykernel</b> package, "
                f"which is required for creating a kernel.<br><br>Do you want to install the package now?"
            )
            message_box = QMessageBox(
                QMessageBox.Question, "ipykernel Missing", message, QMessageBox.Ok | QMessageBox.Cancel, parent=self
            )
            message_box.button(QMessageBox.Ok).setText("Install ipykernel")
            answer = message_box.exec_()
            if answer == QMessageBox.Cancel:
                return
            # Install ipykernel
            self.start_package_install_process(prgm, "ipykernel")
            return
        self.start_kernelspec_install_process(prgm, kernel_name, kernel_display_name)

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
        self.old_kernel_names = find_python_kernels().keys()
        self._logger.msg.emit("Starting Python kernel spec install process")
        args = list()
        args.append("-m")
        args.append("ipykernel")
        args.append("install")
        args.append("--user")
        args.append("--name")
        args.append(k_name)
        args.append("--display-name")
        args.append(d_name)
        self._install_kernel_process = QProcessExecutionManager(self._logger, prgm, args, semisilent=True)
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
        self.populate_kernel_model()
        self.ui.tableView_kernel_list.resizeColumnsToContents()

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
        if not file_is_valid(self, prgm, "Invalid Python Interpreter", extra_check=python_or_julia):
            return False
        if not kernel_name:
            self._logger.msg_error.emit("Kernel name missing")
            return False
        name_taken = False
        display_name_taken = False
        # Ask permission to overwrite if kernel name is taken
        for row in range(self.kernel_list_model.rowCount(self.ui.tableView_kernel_list.rootIndex())):
            row_index = self.kernel_list_model.index(row, 0, self.ui.tableView_kernel_list.rootIndex())
            if kernel_name == row_index.siblingAtColumn(self.find_column("Name")).data(Qt.DisplayRole):  # Name column
                name_taken = True
            elif display_name == row_index.siblingAtColumn(self.find_column("Display Name")).data(
                Qt.DisplayRole
            ):  # Display name column
                display_name_taken = True
        if display_name_taken:
            # This now terminates the whole kernel making if display name is taken. We could just overwrite the kernel.
            self._logger.msg_error.emit(
                f"Display name {display_name} already exists." f"Please provide a new name or remove the other kernel."
            )
            return False
        if name_taken:
            msg = f"Kernel <b>{kernel_name}</b> already exists.<br><br>Would you like to overwrite it?"
            # noinspection PyCallByClass, PyTypeChecker
            message_box = QMessageBox(
                QMessageBox.Question, "Overwrite kernel?", msg, buttons=QMessageBox.Ok | QMessageBox.Cancel, parent=self
            )
            message_box.button(QMessageBox.Ok).setText("Overwrite kernel")
            answer = message_box.exec_()
            if answer != QMessageBox.Ok:
                return False
        return True

    def populate_kernel_model(self):
        """Populates the kernel model with kernels found in user's system
        either with Python or Julia kernels. Unknows, invalid, and
        unsupported kernels are appended to the end."""
        self.ui.tableView_kernel_list.setCurrentIndex(QModelIndex())  # To prevent unneeded currentChanged signals
        if self.python_or_julia == "python":  # Add Python kernels
            kernels = find_python_kernels()
            self.kernel_list_model.clear()
            self.kernel_list_model.setHorizontalHeaderItem(0, QStandardItem("Language"))
            self.kernel_list_model.setHorizontalHeaderItem(1, QStandardItem("Name"))
            self.kernel_list_model.setHorizontalHeaderItem(2, QStandardItem("Display Name"))
            self.kernel_list_model.setHorizontalHeaderItem(3, QStandardItem("Interpreter"))
            self.kernel_list_model.setHorizontalHeaderItem(4, QStandardItem("Location"))
            for name, location in kernels.items():
                d = self.get_kernel_deats(location)
                language = d["language"]
                display_name = d["display_name"]
                interpreter = d["exe"]
                row = [
                    QStandardItem(language),
                    QStandardItem(name),
                    QStandardItem(display_name),
                    QStandardItem(interpreter),
                    QStandardItem(location),
                ]
                for item in row:  # Set items non-editable
                    item.setFlags(~Qt.ItemIsEditable)
                self.kernel_list_model.appendRow(row)
            # Add unknown/invalid kernels
            unknowns = find_unknown_kernels()
            for n, l in unknowns.items():
                unknown_row = [QStandardItem(), QStandardItem(n), QStandardItem(), QStandardItem(), QStandardItem(l)]
                for item in unknown_row:  # Set items non-editable and paint bg red
                    item.setFlags(~Qt.ItemIsEditable)
                    item.setBackground(Qt.red)
                self.kernel_list_model.appendRow(unknown_row)
        else:  # Add Julia kernels
            kernels = find_julia_kernels()
            self.kernel_list_model.clear()
            self.kernel_list_model.setHorizontalHeaderItem(0, QStandardItem("Language"))
            self.kernel_list_model.setHorizontalHeaderItem(1, QStandardItem("Name"))
            self.kernel_list_model.setHorizontalHeaderItem(2, QStandardItem("Display Name"))
            self.kernel_list_model.setHorizontalHeaderItem(3, QStandardItem("Executable"))
            self.kernel_list_model.setHorizontalHeaderItem(4, QStandardItem("Project"))
            self.kernel_list_model.setHorizontalHeaderItem(5, QStandardItem("Location"))
            for name, location in kernels.items():
                d = self.get_kernel_deats(location)
                language = d["language"]
                display_name = d["display_name"]
                executable = d["exe"]
                project = d["project"]
                row = [
                    QStandardItem(language),
                    QStandardItem(name),
                    QStandardItem(display_name),
                    QStandardItem(executable),
                    QStandardItem(project),
                    QStandardItem(location),
                ]
                for item in row:  # Set items non-editable
                    item.setFlags(~Qt.ItemIsEditable)
                self.kernel_list_model.appendRow(row)
            # Add unknown/invalid kernels
            unknowns = find_unknown_kernels()
            for n, l in unknowns.items():
                unknown_row = [
                    QStandardItem(),
                    QStandardItem(n),
                    QStandardItem(),
                    QStandardItem(),
                    QStandardItem(),
                    QStandardItem(l),
                ]
                for item in unknown_row:  # Set items non-editable and paint bg red
                    item.setFlags(~Qt.ItemIsEditable)
                    item.setBackground(Qt.red)
                self.kernel_list_model.appendRow(unknown_row)
        # If a new kernel was added, set it selected
        if not self.old_kernel_names:
            return
        new_kernel = set(kernels.keys()) ^ set(self.old_kernel_names)
        if not new_kernel or len(new_kernel) > 1:
            return
        [n] = new_kernel  # Unpack the set
        self.set_kernel_selected(n)

    @staticmethod
    def get_kernel_deats(kernel_path):
        """Reads kernel.json from given kernel path and returns the details in a dictionary.

        Args:
            kernel_path (str): Full path to kernel directory

        Returns:
            dict: language (str), path to interpreter (str), display name (str), project (str) (NA for Python kernels)
        """
        deats = {"language": "", "exe": "", "display_name": "", "project": ""}
        kernel_json = os.path.join(kernel_path, "kernel.json")
        if not os.path.exists(kernel_json):
            return deats
        if os.stat(kernel_json).st_size == 0:  # File is empty
            return deats
        with open(kernel_json, "r") as fh:
            try:
                kernel_dict = json.load(fh)
            except json.decoder.JSONDecodeError:
                return deats
            try:
                language = kernel_dict["language"]
            except KeyError:
                language = ""
            try:
                interp = kernel_dict["argv"][0]
            except KeyError:
                interp = ""
            except IndexError:
                interp = ""
            try:
                display_name = kernel_dict["display_name"]
            except KeyError:
                display_name = ""
            try:
                # loop argv and find a string that starts with --project=
                project = ""
                for arg in kernel_dict["argv"]:
                    if arg.startswith("--project="):
                        project = arg[10:]
            except KeyError:
                project = ""
            except IndexError:
                project = ""
            deats["language"] = language
            deats["exe"] = interp
            deats["display_name"] = display_name
            deats["project"] = project
            return deats

    @Slot("QPoint")
    def show_kernel_list_context_menu(self, pos):
        """Shows the context-menu in the kernel list table view."""
        index = self.ui.tableView_kernel_list.indexAt(pos)
        if not index.isValid():
            return
        global_pos = self.ui.tableView_kernel_list.viewport().mapToGlobal(pos)
        self._kernel_list_context_menu.popup(global_pos)

    @Slot(bool)
    def _open_kernel_json(self, checked=False):
        """Opens kernel.json file using the default application for .json files."""
        index = self.ui.tableView_kernel_list.currentIndex()
        if not index.isValid():
            return
        d = index.siblingAtColumn(self.find_column("Location")).data(Qt.DisplayRole)  # Location column
        kernel_json = os.path.join(d, "kernel.json")
        if not os.path.exists(kernel_json):
            msg = f"Path <br><br>{kernel_json}<br><br>does not exist.<br>Consider removing the kernel manually."
            QMessageBox.warning(self, "Opening kernel.json failed", msg)
            return
        url = "file:///" + kernel_json
        res = open_url(url)
        if not res:
            msg = f"Opening file {kernel_json} failed."
            QMessageBox.warning(self, "Opening kernel.json failed", msg)
            return
        return

    @Slot(bool)
    def _open_kernel_dir(self, checked=False):
        """Opens kernel directory in OS file browser."""
        index = self.ui.tableView_kernel_list.currentIndex()
        if not index.isValid():
            return
        d = index.siblingAtColumn(self.find_column("Location")).data(Qt.DisplayRole)  # Location column
        if not os.path.exists(d):
            msg = "Path does not exist. Consider removing the kernel manually."
            # noinspection PyCallByClass, PyArgumentList
            QMessageBox.warning(self, "Opening directory failed", msg)
            return
        url = "file:///" + d
        res = open_url(url)
        if not res:
            msg = f"Opening directory {d} failed."
            # noinspection PyCallByClass, PyArgumentList
            QMessageBox.warning(self, "Opening file browser failed", msg)
            return
        return

    @Slot(bool)
    def _remove_kernel(self, checked=False):
        """Removes selected kernel by deleting the kernel directory."""
        index = self.ui.tableView_kernel_list.currentIndex()
        if not index.isValid():
            return
        name = index.siblingAtColumn(self.find_column("Name")).data(Qt.DisplayRole)  # Name column
        d = index.siblingAtColumn(self.find_column("Location")).data(Qt.DisplayRole)  # Location column
        if not os.path.exists(d):
            msg = "Path does not exist. Please remove it manually."
            # noinspection PyCallByClass, PyArgumentList
            QMessageBox.warning(self, "Removing kernel failed", msg)
            return
        msg = f"Are you sure you want to remove kernel <b>{name}</b>"
        msg += f"<br><br>Directory<br><br><b>{d}</b><br><br>will be deleted."
        # noinspection PyCallByClass, PyTypeChecker
        message_box = QMessageBox(
            QMessageBox.Question, "Remove kernel?", msg, buttons=QMessageBox.Ok | QMessageBox.Cancel, parent=self
        )
        message_box.button(QMessageBox.Ok).setText("Remove kernel")
        answer = message_box.exec_()
        if answer != QMessageBox.Ok:
            return
        try:
            shutil.rmtree(d)
        except OSError as os_err:
            msg = f"<b>{os_err}</b><br><br>Please edit permissions and try again or remove the directory manually."
            # noinspection PyCallByClass, PyArgumentList
            QMessageBox.warning(self, "Removing kernel failed", msg)
            return
        self._logger.msg.emit(f"kernel {name} removed")
        self.populate_kernel_model()
        self.ui.tableView_kernel_list.resizeColumnsToContents()

    def mousePressEvent(self, e):
        """Saves mouse position at the start of dragging.

        Args:
            e (QMouseEvent): Mouse event
        """
        self._mouse_press_pos = e.globalPos()
        self._mouse_move_pos = e.globalPos()
        super().mousePressEvent(e)

    def mouseReleaseEvent(self, e):
        """Saves mouse position at the end of dragging.

        Args:
            e (QMouseEvent): Mouse event
        """
        if self._mouse_press_pos is not None:
            self._mouse_release_pos = e.globalPos()
            moved = self._mouse_release_pos - self._mouse_press_pos
            if moved.manhattanLength() > 3:
                e.ignore()
                return

    def mouseMoveEvent(self, e):
        """Moves the window when mouse button is pressed and mouse cursor is moved.

        Args:
            e (QMouseEvent): Mouse event
        """
        currentpos = self.pos()
        globalpos = e.globalPos()
        if not self._mouse_move_pos:
            e.ignore()
            return
        diff = globalpos - self._mouse_move_pos
        newpos = currentpos + diff
        self.move(newpos)
        self._mouse_move_pos = globalpos

    @busy_effect
    @staticmethod
    def is_package_installed(python_path, package_name):
        """Checks if given package is installed to given Python environment.

        Args:
            python_path (str): Full path to selected Python interpreter
            package_name (str): Package name

        Returns:
            (bool): True if installed, False if not
        """
        response = subprocess.check_output([python_path, '-m', 'pip', 'freeze', '-q'])
        installed_packages = [r.decode().split('==')[0] for r in response.split()]
        return package_name in installed_packages

    @busy_effect
    def start_package_install_process(self, python_path, package_name):
        """Starts installing the given package using pip.

        Args:
            python_path (str): Full path to selected Python interpreter
            package_name (str): Package name to install using pip
        """
        self._logger.msg.emit(f"Installing ipykernel into {python_path}")
        args = list()
        args.append("-m")
        args.append("pip")
        args.append("install")
        args.append(package_name)
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
            self._logger.msg_success.emit("ipykernel installation succeeded")
        self.make_python_kernel()  # Try installing kernel specs now

    @Slot(bool)
    def make_julia_kernel(self, checked=False):
        """Makes a new Julia kernel. Offers to install IJulia package if it is
        missing from the selected Julia project. Overwrites existing kernel
        with the same name if this is ok by user."""
        julia = self.ui.lineEdit_julia_executable.text()
        project = self.ui.lineEdit_julia_project.text()
        if not dir_is_valid(self, project, "Invalid Julia Project directory"):
            return
        kernel_name = self.ui.lineEdit_julia_kernel_name.text()
        if not self.check_options(julia, kernel_name, kernel_name, "julia"):  # Julia display name cannot be chosen
            return
        if self._ready_to_install_kernel:
            self.start_ijulia_installkernel_process(julia, project, kernel_name)
            return
        # Check if IJulia is installed to selected Julia project
        retval = self.is_ijulia_installed(julia, project)
        if retval == 0:  # Julia is not configured correctly
            return
        if retval == 1:  # IJulia is installed
            if self.ui.checkBox_rebuild_ijulia.isChecked():
                self.start_ijulia_rebuild_process(julia, project)
            else:
                self.start_ijulia_installkernel_process(julia, project, kernel_name)
            return
        if retval == 2:  # IJulia is not installed
            message = (
                f"Julia project <br><br><b>{project}</b><br><br>is missing the <b>IJulia</b> package, "
                f"which is required for creating a kernel.<br><br>Do you want to install the package now?"
            )
            message_box = QMessageBox(
                QMessageBox.Question, "IJulia missing", message, QMessageBox.Ok | QMessageBox.Cancel, parent=self
            )
            message_box.button(QMessageBox.Ok).setText("Install IJulia")
            answer = message_box.exec_()
            if answer == QMessageBox.Cancel:
                return
            self.start_ijulia_install_process(julia, project)

    @busy_effect
    def is_ijulia_installed(self, program, project):
        """Checks if IJulia is installed for the given project.
        Note: Trying command 'using IJulia' does not work since
        it automatically tries loading it from the LOAD_PATH if
        not it's not found in the active project.

        Returns:
            (int): 0 when process failed to start, 1 when IJulia is installed, 2 when IJulia is not installed.
        """
        self._logger.msg.emit(f"Checking if IJulia is installed for project {project}")
        args = list()
        args.append(f"--project={project}")
        args.append("-e")
        args.append("using Pkg; if in(ARGS[1], keys(Pkg.installed())); println(ARGS[2]); else; println(ARGS[3]); end;")
        args.append("IJulia")
        args.append("True")  # This could be anything, as long as we just match this down below
        args.append("False")
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
        args = list()
        args.append(f"--project={project}")
        args.append("-e")
        args.append("try using Pkg catch; end; Pkg.add(ARGS[1])")
        args.append("IJulia")
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
        args = list()
        args.append(f"--project={project}")
        args.append("-e")
        args.append("try using Pkg catch; end; Pkg.build(ARGS[1])")
        args.append("IJulia")
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
        is actually the new kernel DISPLAY name. IJulia strips the whitespace and
        uncapitalizes this to make the kernel name automatically. Julia version is
        concatenated to both names automatically (This cannot be changed).
        """
        self._logger.msg.emit("Installing Julia kernel")
        self.old_kernel_names = find_julia_kernels().keys()
        args = list()
        args.append(f"--project={project}")
        args.append("-e")
        args.append("using IJulia; installkernel(ARGS[1], ARGS[2])")
        args.append(f"{kernel_name}")
        args.append(f"--project={project}")
        self._install_julia_kernel_process = QProcessExecutionManager(self._logger, program, args, semisilent=True)
        self._install_julia_kernel_process.execution_finished.connect(self.handle_installkernel_process_finished)
        self._install_julia_kernel_process.start_execution()

    @busy_effect
    @Slot(int)
    def handle_installkernel_process_finished(self, retval):
        """Checks whether or not the IJulia.installkernel process finished successfully.

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
        self.populate_kernel_model()
        self.ui.tableView_kernel_list.resizeColumnsToContents()

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

    def done(self, r):
        """Overridden QDialog method. Sets the selected kernel instance attribute so
        that it can be read by the SettingsForm after this dialog has been closed.

        Args:
            r (int) QDialog Accepted or Rejected
        """
        self._save_ui()
        self.selected_kernel = None
        if r == QDialog.Accepted:
            ind = self.ui.tableView_kernel_list.selectedIndexes()
            if len(ind) > 0:
                self.selected_kernel = ind[0].siblingAtColumn(self.find_column("Name")).data(Qt.DisplayRole)
        super().done(r)

    def closeEvent(self, event=None):
        """Handles dialog closing.

        Args:
            event (QCloseEvent): Close event
        """
        self._save_ui()
        if event:
            event.accept()


def find_kernels():
    """Returns a dictionary mapping kernel names to kernel paths."""
    kernels = find_kernel_specs()
    if not kernels:
        return dict()
    return kernels


def find_python_kernels():
    """Returns a dictionary of Python kernels. Keys are kernel_names, values are kernel paths."""
    python_kernels = dict()
    for kernel_name, location in find_kernels().items():
        d = KernelEditor.get_kernel_deats(location)
        if d["language"].lower().strip() == "python":
            python_kernels[kernel_name] = location
    return python_kernels


def find_julia_kernels():
    """Returns a dictionary of Julia kernels. Keys are kernel_names, values are kernel paths."""
    julia_kernels = dict()
    for kernel_name, location in find_kernels().items():
        d = KernelEditor.get_kernel_deats(location)
        if d["language"].lower().strip() == "julia":
            julia_kernels[kernel_name] = location
    return julia_kernels


def find_unknown_kernels():
    """Returns a dictionary of kernels that are neither Python nor Julia kernels."""
    all_kernels = find_kernels()
    p = find_python_kernels()
    j = find_julia_kernels()
    remains1 = dict(set(all_kernels.items()) ^ set(p.items()))  # remains after removing python kernels
    remains2 = dict(set(remains1.items()) ^ set(j.items()))  # Remains after removing python and julia kernels
    return remains2


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
