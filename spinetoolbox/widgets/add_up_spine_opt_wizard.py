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
Classes for custom QDialogs for julia setup.

:author: M. Marin (KTH)
:date:   13.5.2018
"""

from enum import IntEnum, auto
from PySide2.QtWidgets import (
    QWidget,
    QWizard,
    QWizardPage,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QFileDialog,
    QCheckBox,
)
from PySide2.QtCore import Signal, Slot, Qt
from PySide2.QtGui import QCursor
from ..execution_managers import QProcessExecutionManager
from ..helpers import format_log_message
from ..config import REQUIRED_SPINE_OPT_VERSION
from .custom_qtextbrowser import CustomQTextBrowser
from .custom_qwidgets import WrapLabel, HyperTextLabel


class _PageId(IntEnum):
    INTRO = auto()
    SELECT_JULIA = auto()
    CHECK_PREVIOUS_INSTALL = auto()
    ADD_UP_SPINE_OPT = auto()
    SUCCESS = auto()
    FAILURE = auto()


class AddUpSpineOptWizard(QWizard):
    """A wizard to add/updated spine opt
    """

    troubleshooting_requested = Signal()

    def __init__(self, parent, julia_exe, julia_project):
        """Initialize class.

        Args:
            parent (QWidget): the parent widget (SettingsWidget)
        """
        super().__init__(parent)
        self.process_log = None
        self.julia_exe = None
        self.required_action = None
        self.setWindowTitle("SpineOpt Installer")
        self.setPage(_PageId.INTRO, IntroPage(self))
        self.setPage(_PageId.SELECT_JULIA, SelectJuliaPage(self, julia_exe, julia_project))
        self.setPage(_PageId.CHECK_PREVIOUS_INSTALL, CheckPreviousInstallPage(self))
        self.setPage(_PageId.ADD_UP_SPINE_OPT, AddUpSpineOptPage(self))
        self.setPage(_PageId.SUCCESS, SuccessPage(self))
        self.setPage(_PageId.FAILURE, FailurePage(self))
        self.setStartId(_PageId.INTRO)

    def accept(self):
        super().accept()
        if self.field("troubleshooting"):
            self.troubleshooting_requested.emit()


class IntroPage(QWizardPage):
    def __init__(self, parent):
        super().__init__(parent)
        self.setTitle("Welcome")
        label = HyperTextLabel(
            "This wizard will help you install or upgrade "
            "<a title='spine opt' href='https://github.com/Spine-project/SpineOpt.jl#spineoptjl'>SpineOpt</a> "
            "in a Julia project of your choice."
        )
        layout = QVBoxLayout(self)
        layout.addWidget(label)

    def nextId(self):
        return _PageId.SELECT_JULIA


class SelectJuliaPage(QWizardPage):
    def __init__(self, parent, julia_exe, julia_project):
        super().__init__(parent)
        self.setTitle("Select Julia project")
        self._julia_exe = julia_exe
        self._julia_project = julia_project
        self._julia_exe_line_edit = QLineEdit()
        self._julia_project_line_edit = QLineEdit()
        self._julia_project_line_edit.setPlaceholderText("Use Julia's default project")
        self.registerField("julia_exe*", self._julia_exe_line_edit)
        self.registerField("julia_project", self._julia_project_line_edit)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Julia executable:"))
        julia_exe_widget = QWidget()
        julia_exe_layout = QHBoxLayout(julia_exe_widget)
        julia_exe_layout.addWidget(self._julia_exe_line_edit)
        julia_exe_button = QPushButton("Browse")
        julia_exe_layout.addWidget(julia_exe_button)
        layout.addWidget(julia_exe_widget)
        layout.addWidget(QLabel("Julia project (directory):"))
        julia_project_widget = QWidget()
        julia_project_layout = QHBoxLayout(julia_project_widget)
        julia_project_layout.addWidget(self._julia_project_line_edit)
        julia_project_button = QPushButton("Browse")
        julia_project_layout.addWidget(julia_project_button)
        layout.addWidget(julia_project_widget)
        julia_exe_button.clicked.connect(self._select_julia_exe)
        julia_project_button.clicked.connect(self._select_julia_project)

    def initializePage(self):
        self._julia_exe_line_edit.setText(self._julia_exe)
        self._julia_project_line_edit.setText(self._julia_project)

    def _select_julia_exe(self):
        julia_exe = QFileDialog.getOpenFileName(self, "Select Julia executable", self.field("julia_exe"))
        if not julia_exe:
            return
        self.setField("julia_exe", julia_exe)

    def _select_julia_project(self):
        julia_project = QFileDialog.getExistingDirectory(
            self, "Select Julia project (directory)", self.field("julia_project")
        )
        if not julia_project:
            return
        self.setField("julia_project", julia_project)

    def nextId(self):
        return _PageId.CHECK_PREVIOUS_INSTALL


class CheckPreviousInstallPage(QWizardPage):
    def __init__(self, parent):
        super().__init__(parent)
        self.setTitle("Checking previous installation")
        self._exec_mngr = None
        self._errored = False
        QVBoxLayout(self)

    def isComplete(self):
        return self._exec_mngr is None and not self._errored

    def cleanupPage(self):
        super().cleanupPage()
        if self._exec_mngr is not None:
            self._exec_mngr.stop_execution()

    def initializePage(self):
        while True:
            child = self.layout().takeAt(0)
            if child is None:
                break
            child.widget().deleteLater()
        julia_exe = self.field("julia_exe")
        julia_project = self.field("julia_project")
        args = [
            f"--project={julia_project}",
            "-e",
            'import Pkg; '
            'pkgs = Pkg.TOML.parsefile(joinpath(dirname(Base.active_project()), "Manifest.toml")); '
            'spine_opt = get(pkgs, "Spin eOpt", nothing); '
            'if spine_opt != nothing println(spine_opt[1]["version"]) end',
        ]
        self._exec_mngr = QProcessExecutionManager(self, julia_exe, args, silent=True)
        self.completeChanged.emit()
        self._exec_mngr.execution_finished.connect(self._handle_check_install_finished)
        qApp.setOverrideCursor(QCursor(Qt.BusyCursor))  # pylint: disable=undefined-variable
        self._exec_mngr.start_execution()

    @Slot(int)
    def _handle_check_install_finished(self, ret):
        qApp.restoreOverrideCursor()  # pylint: disable=undefined-variable
        self._exec_mngr.execution_finished.disconnect(self._handle_check_install_finished)
        if self.wizard().currentPage() != self:
            return
        output_log = self._exec_mngr.process_output
        error_log = self._exec_mngr.process_error
        self._exec_mngr = None
        if ret != 0:
            msg = "<p>Julia failed to run.</p><p>Please go back and check your selections.</p>"
            self.layout().addWidget(WrapLabel(msg))
            if error_log:
                self.layout().addWidget(WrapLabel("Below is the error log."))
                log = CustomQTextBrowser(self)
                log.append(error_log)
                self.layout().addWidget(log)
            self._errored = True
            self.completeChanged.emit()
            return
        spine_opt_version = output_log
        if spine_opt_version:
            if [int(x) for x in spine_opt_version.split(".")] >= [
                int(x) for x in REQUIRED_SPINE_OPT_VERSION.split(".")
            ]:
                msg = f"SpineOpt version {spine_opt_version} is installed and is already the required version."
                self.layout().addWidget(WrapLabel(msg))
                self.setFinalPage(True)
                return
            msg = (
                f"SpineOpt version {spine_opt_version} is installed, "
                f"but version {REQUIRED_SPINE_OPT_VERSION} is required."
            )
            self.layout().addWidget(WrapLabel(msg))
            self.wizard().required_action = "update"
            self.setCommitPage(True)
            self.setButtonText(QWizard.CommitButton, "Update SpineOpt")
            self.completeChanged.emit()
            return
        self.layout().addWidget(QLabel("SpineOpt is not installed."))
        self.wizard().required_action = "add"
        self.setCommitPage(True)
        self.setButtonText(QWizard.CommitButton, "Install SpineOpt")
        self.completeChanged.emit()

    def nextId(self):
        if self.wizard().required_action is None:
            return -1
        return _PageId.ADD_UP_SPINE_OPT


class AddUpSpineOptPage(QWizardPage):

    msg = Signal(str)
    msg_warning = Signal(str)
    msg_error = Signal(str)
    msg_success = Signal(str)
    msg_proc = Signal(str)
    msg_proc_error = Signal(str)

    def __init__(self, parent):
        super().__init__(parent)
        self._log = CustomQTextBrowser(self)
        self.registerField("process_log", self._log)
        self._exec_mngr = None
        self._successful = False
        layout = QVBoxLayout(self)
        layout.addWidget(self._log)
        self._connect_signals()

    def _connect_signals(self):
        self.msg.connect(self._add_msg)
        self.msg_warning.connect(self._add_msg_warning)
        self.msg_error.connect(self._add_msg_error)
        self.msg_success.connect(self._add_msg_succes)
        self.msg_proc.connect(self._add_msg)
        self.msg_proc_error.connect(self._add_msg_error)

    def _add_msg(self, msg):
        self._log.append(format_log_message("msg", msg, show_datetime=False))

    def _add_msg_warning(self, msg):
        self._log.append(format_log_message("msg_warning", msg, show_datetime=False))

    def _add_msg_error(self, msg):
        self._log.append(format_log_message("msg_error", msg, show_datetime=False))

    def _add_msg_succes(self, msg):
        self._log.append(format_log_message("msg_success", msg, show_datetime=False))

    def isComplete(self):
        return self._exec_mngr is None

    def initializePage(self):
        processing, code, process = {
            "add": (
                "Installing",
                'using Pkg; pkg"regi stry add https://github.com/Spine-project/SpineJuliaRegistry.git"; pkg"add SpineOpt"',
                "installation",
            ),
            "update": ("Updating", 'using Pkg; pkg"up SpineOpt"', "update"),
        }[self.wizard().required_action]
        self.setTitle(f"{processing} SpineOpt")
        julia_exe = self.field("julia_exe")
        julia_project = self.field("julia_project")
        args = [f"--project={julia_project}", "-e", code]
        self._exec_mngr = QProcessExecutionManager(self, julia_exe, args, semisilent=True)
        self.completeChanged.emit()
        self._exec_mngr.execution_finished.connect(self._handle_spine_opt_add_up_finished)
        self.msg_success.emit(f"SpineOpt {process} started")
        cmd = julia_exe + " " + " ".join(args)
        self.msg.emit(f"$ <b>{cmd}<b/>...")
        qApp.setOverrideCursor(QCursor(Qt.BusyCursor))  # pylint: disable=undefined-variable
        self._exec_mngr.start_execution()

    @Slot(int)
    def _handle_spine_opt_add_up_finished(self, ret):
        qApp.restoreOverrideCursor()  # pylint: disable=undefined-variable
        self._exec_mngr.execution_finished.disconnect(self._handle_spine_opt_add_up_finished)
        if self.wizard().currentPage() != self:
            return
        self._exec_mngr = None
        self._successful = ret == 0
        self.completeChanged.emit()
        if self._successful:
            configured = {"add": "installed", "update": "updated"}[self.wizard().required_action]
            self.msg_success.emit(f"SpineOpt successfully {configured}")
            return
        process = {"add": "installation", "update": "updatee"}[self.wizard().required_action]
        self.msg_error.emit(f"SpineOpt {process} failed")
        self.wizard().process_log = self._log.toHtml()

    def cleanupPage(self):
        super().cleanupPage()
        if self._exec_mngr is not None:
            self._exec_mngr.stop_execution()
        self.msg_error.emit("Aborted by the user")

    def nextId(self):
        if self._successful:
            return _PageId.SUCCESS
        return _PageId.FAILURE


class SuccessPage(QWizardPage):
    def __init__(self, parent):
        super().__init__(parent)
        self._label = WrapLabel()
        layout = QVBoxLayout(self)
        layout.addWidget(self._label)

    def initializePage(self):
        process = {"add": "Installation", "update": "Update"}[self.wizard().required_action]
        self.setTitle(f"{process} successful")

    def nextId(self):
        return -1


class FailurePage(QWizardPage):
    def __init__(self, parent):
        super().__init__(parent)
        self._log = CustomQTextBrowser(self)
        check_box = QCheckBox("Run troubleshooting wizard")
        check_box.setChecked(True)
        self.registerField("troubleshooting", check_box)
        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)
        self._button_copy = QPushButton("Copy")
        self._label_copy = QLabel()
        button_layout.addWidget(self._button_copy)
        button_layout.addWidget(self._label_copy)
        button_layout.addStretch()
        layout = QVBoxLayout(self)
        msg = (
            "<p>Apologies.</p><p>Below is the process log; "
            "we suggest you to copy/paste it somewhere safe, for troubleshooting.</p>"
        )
        layout.addWidget(WrapLabel(msg))
        layout.addWidget(self._log)
        layout.addWidget(button_container)
        layout.addWidget(check_box)
        self._button_copy.clicked.connect(self._copy_log_to_clipboard)

    @Slot(bool)
    def _copy_log_to_clipboard(self, _=False):
        qApp.clipboard().setText(self._log.toPlainText())  # pylint: disable=undefined-variable
        self._label_copy.setText("Process log copied to clipboard")

    def initializePage(self):
        process = {"add": "Installation", "update": "Update"}[self.wizard().required_action]
        self.setTitle(f"{process} failed")
        self._log.clear()
        self._log.append(self.wizard().process_log)

    def nextId(self):
        return -1
