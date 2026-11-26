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

"""Classes for custom QDialogs for julia setup."""

import os
from enum import IntEnum, auto
from typing import Literal, TypeAlias
from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QCursor, QTextCursor, QIcon
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QHBoxLayout,
    QLabel,
    QLayout,
    QComboBox,
    QPushButton,
    QToolButton,
    QRadioButton,
    QVBoxLayout,
    QWidget,
    QWizard,
    QWizardPage,
    QMessageBox,
)
from spine_engine.logger_interface import LoggerInterface
from spine_engine.utils.helpers import resolve_default_julia_executable
from ..execution_managers import QProcessExecutionManager
from ..execution_models import ExecutionModels
from ..helpers import select_and_add_julia_executable, select_and_add_julia_project
from .custom_qtextbrowser import MonoSpaceFontTextBrowser
from .custom_qwidgets import HyperTextLabel, QWizardProcessPage, WrapLabel


class _PageId(IntEnum):
    INTRO = auto()
    SELECT_JULIA = auto()
    CHECK_PREVIOUS_INSTALL = auto()
    ADD_UP_SPINE_OPT = auto()
    SUCCESS = auto()
    FAILURE = auto()
    TROUBLESHOOT_PROBLEMS = auto()
    TROUBLESHOOT_SOLUTION = auto()
    ADD_UP_SPINE_OPT_AGAIN = auto()
    TOTAL_FAILURE = auto()


RequiredActions: TypeAlias = Literal["add", "update"]


class AddUpSpineOptWizard(QWizard):
    """A wizard to install & upgrade SpineOpt."""

    def __init__(self, parent: QWidget | None, execution_models: ExecutionModels):
        """
        Args:
            parent: the parent widget (SettingsWidget)
        """
        super().__init__(parent)
        self.setOption(QWizard.WizardOption.NoBackButtonOnStartPage, True)
        self.setWizardStyle(QWizard.WizardStyle.ModernStyle)
        self.process_log: str | None = None
        self.required_action: RequiredActions | None = None
        self.spine_opt_version_before_update: list[int] | None = None
        self.spine_opt_version_after_update: list[int] | None = None
        self.setWindowTitle("SpineOpt Installer")
        self._execution_models = execution_models
        self._execution_models.refresh_julia_executables_model(show_select_item=True)
        self._execution_models.refresh_julia_projects_model(show_select_item=True)
        self.setPage(_PageId.INTRO, IntroPage(self))
        self.setPage(_PageId.SELECT_JULIA, SelectJuliaPage(self, self._execution_models))
        self.setPage(_PageId.CHECK_PREVIOUS_INSTALL, CheckPreviousInstallPage(self))
        self.setPage(_PageId.ADD_UP_SPINE_OPT, AddUpSpineOptPage(self))
        self.setPage(_PageId.SUCCESS, SuccessPage(self))
        self.setPage(_PageId.FAILURE, FailurePage(self))
        self.setPage(_PageId.TROUBLESHOOT_PROBLEMS, TroubleshootProblemsPage(self))
        self.setPage(_PageId.TROUBLESHOOT_SOLUTION, TroubleshootSolutionPage(self))
        self.setPage(_PageId.ADD_UP_SPINE_OPT_AGAIN, AddUpSpineOptAgainPage(self))
        self.setPage(_PageId.TOTAL_FAILURE, TotalFailurePage(self))
        self.setStartId(_PageId.INTRO)
        self.setOption(QWizard.WizardOption.NoCancelButtonOnLastPage)

    def julia_executable(self):
        return self.property("julia_exe")

    def julia_project(self):
        return self.property("julia_project")


class IntroPage(QWizardPage):
    def __init__(self, parent: QWidget | None):
        super().__init__(parent)
        self.setTitle("Welcome")
        label = HyperTextLabel(
            "This wizard will help you install or upgrade "
            "<a title='spine opt' href='https://github.com/spine-tools/SpineOpt.jl#spineoptjl'>SpineOpt</a> "
            "in a Julia project of your choice."
        )
        layout = QVBoxLayout(self)
        layout.addWidget(label)

    def nextId(self):
        return _PageId.SELECT_JULIA


class SelectJuliaPage(QWizardPage):
    def __init__(self, parent: QWidget | None, execution_models: ExecutionModels):
        super().__init__(parent)
        self.setTitle("Select Julia")
        self._execution_models = execution_models
        self._julia_exe_combobox = QComboBox()
        self._julia_project_combobox = QComboBox()
        self._julia_exe_combobox.setModel(self._execution_models.julia_executables_model)
        self._julia_project_combobox.setModel(self._execution_models.julia_projects_model)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Julia executable"))
        julia_exe_widget = QWidget()
        julia_exe_layout = QHBoxLayout(julia_exe_widget)
        julia_exe_layout.setContentsMargins(0, 0, 0, 0)
        julia_exe_layout.addWidget(self._julia_exe_combobox)
        add_julia_exe_button = QToolButton(self)
        add_julia_exe_button.setIcon(QIcon(":/symbols/julia-logo.svg"))
        add_julia_exe_button.setToolTip("Add existing Julia")
        julia_exe_layout.addWidget(add_julia_exe_button)
        layout.addWidget(julia_exe_widget)
        layout.addWidget(QLabel("Julia project"))
        julia_project_widget = QWidget()
        julia_project_layout = QHBoxLayout(julia_project_widget)
        julia_project_layout.setContentsMargins(0, 0, 0, 0)
        julia_project_layout.addWidget(self._julia_project_combobox)
        add_julia_project_button = QToolButton(self)
        add_julia_project_button.setIcon(QIcon(":/icons/menu_icons/folder-open-solid.svg"))
        add_julia_project_button.setToolTip(
            "Add path to Julia project\nTip: You can add a path to an empty folder here."
        )
        julia_project_layout.addWidget(add_julia_project_button)
        layout.addWidget(julia_project_widget)
        self._julia_exe_combobox.currentIndexChanged.connect(lambda _: self.completeChanged.emit())
        self._julia_project_combobox.currentIndexChanged.connect(lambda _: self.completeChanged.emit())
        add_julia_exe_button.clicked.connect(self._on_add_julia_executable_clicked)
        add_julia_project_button.clicked.connect(self._on_add_julia_project_clicked)

    @Slot(bool)
    def _on_add_julia_executable_clicked(self, _=False):
        select_and_add_julia_executable(self._julia_exe_combobox, self._execution_models, self)

    @Slot(bool)
    def _on_add_julia_project_clicked(self, _=False):
        select_and_add_julia_project(self._julia_project_combobox, self._execution_models, self)

    def initializePage(self):
        self._julia_exe_combobox.setCurrentIndex(0)
        self._julia_project_combobox.setCurrentIndex(0)

    def isComplete(self):
        """Enables the Next button when True."""
        exe_item = self._execution_models.julia_executables_model.item(self._julia_exe_combobox.currentIndex())
        if not exe_item or not exe_item.data():
            return False
        project_item = self._execution_models.julia_projects_model.item(self._julia_project_combobox.currentIndex())
        if not project_item or not project_item.data():
            return False
        return True

    def validatePage(self):
        """Validates page after Next button is clicked. Note that there's no need
        to check for the existence of the Julia project path. Julia should create
        the path if it doesn't exist."""
        exe_item = self._execution_models.julia_executables_model.item(self._julia_exe_combobox.currentIndex())
        project_item = self._execution_models.julia_projects_model.item(self._julia_project_combobox.currentIndex())
        if exe_item.data()["exe"] == "":
            exe = resolve_default_julia_executable()
        else:
            exe = exe_item.data()["exe"]
        if not os.path.exists(exe):
            QMessageBox.warning(
                self, "Julia executable not found", f"The Julia executable '{exe}' does not exist."
            )
            return False
        self.wizard().setProperty("julia_exe", exe)
        self.wizard().setProperty("julia_project", project_item.data()["path"])
        return True


class CheckPreviousInstallPage(QWizardPage):
    def __init__(self, parent: QWidget | None):
        super().__init__(parent)
        self.setTitle("Checking previous installation")
        self._exec_mngr: QProcessExecutionManager | None = None
        self._errored = False
        QVBoxLayout(self)

    def isComplete(self):
        return self._exec_mngr is None and not self._errored

    def cleanupPage(self):
        super().cleanupPage()
        if self._exec_mngr is not None:
            self._exec_mngr.stop_execution()

    def initializePage(self):
        _clear_layout(self.layout())
        self._exec_mngr = _create_exec_manager_to_resolve_spine_opt_version(
            self.wizard().property("julia_exe"), self.wizard().property("julia_project"), self
        )
        self.completeChanged.emit()
        self._exec_mngr.execution_finished.connect(self._handle_check_install_finished)
        QApplication.setOverrideCursor(QCursor(Qt.CursorShape.BusyCursor))  # pylint: disable=undefined-variable
        self._exec_mngr.start_execution()

    def _handle_check_install_finished(self, ret: int) -> None:
        QApplication.restoreOverrideCursor()  # pylint: disable=undefined-variable
        self._exec_mngr.execution_finished.disconnect(self._handle_check_install_finished)
        if self.wizard().currentPage() is not self:
            return
        spine_opt_version = self._exec_mngr.process_output
        error_log = self._exec_mngr.process_error
        self._exec_mngr = None
        if ret != 0:
            msg = "<p>Julia failed to run.</p><p>Please go back and check your selections.</p>"
            self.layout().addWidget(WrapLabel(msg))
            if error_log:
                self.layout().addWidget(WrapLabel("Below is the error log."))
                log = MonoSpaceFontTextBrowser(self)
                log.append(error_log)
                self.layout().addWidget(log)
            self._errored = True
            self.completeChanged.emit()
            return
        if spine_opt_version:
            msg = f"SpineOpt version {spine_opt_version} is installed."
            self.layout().addWidget(WrapLabel(msg))
            self.wizard().required_action = "update"
            self.setFinalPage(False)
            self.setCommitPage(True)
            self.setButtonText(QWizard.WizardButton.CommitButton, "Update SpineOpt")
            self.completeChanged.emit()
            self.wizard().spine_opt_version_before_update = [int(v) for v in spine_opt_version.split(".")]
            return
        self.layout().addWidget(QLabel("SpineOpt is not installed."))
        self.wizard().required_action = "add"
        self.setFinalPage(False)
        self.setCommitPage(True)
        self.setButtonText(QWizard.WizardButton.CommitButton, "Install SpineOpt")
        self.completeChanged.emit()

    def nextId(self):
        if self.wizard().required_action is None:
            return -1
        return _PageId.ADD_UP_SPINE_OPT


class AddUpSpineOptPage(QWizardProcessPage):
    def initializePage(self):
        required_action = self.wizard().required_action
        processing, code, process = {
            "add": (
                "Installing",
                'using Pkg; Pkg.Registry.add("General"); Pkg.add("SpineOpt")',
                "installation",
            ),
            "update": ("Updating", 'using Pkg; Pkg.update("SpineInterface"); Pkg.update("SpineOpt")', "update"),
        }[required_action]
        self.setTitle(f"{processing} SpineOpt")
        julia_exe = self.wizard().property("julia_exe")
        julia_project = self.wizard().property("julia_project")
        args = [f"--project={julia_project}", "-e", code]
        self._exec_mngr = QProcessExecutionManager(self, julia_exe, args, semisilent=True)
        self.completeChanged.emit()
        if required_action == "add":
            self._exec_mngr.execution_finished.connect(self._handle_spine_opt_add_up_finished)
        else:
            self._exec_mngr.execution_finished.connect(self._handle_spine_opt_update_finished)
        self.msg_success.emit(f"SpineOpt {process} started")
        cmd = julia_exe + " " + " ".join(args)
        self.msg.emit(f"$ <b>{cmd}<b/>")
        QApplication.setOverrideCursor(QCursor(Qt.CursorShape.BusyCursor))  # pylint: disable=undefined-variable
        self._exec_mngr.start_execution()

    def _handle_spine_opt_update_finished(self, ret: int) -> None:
        self._exec_mngr.execution_finished.disconnect(self._handle_spine_opt_update_finished)
        if ret == 0:
            self._exec_mngr = _create_exec_manager_to_resolve_spine_opt_version(
                self.wizard().property("julia_exe"), self.wizard().property("julia_project"), self
            )
            self._exec_mngr.execution_finished.connect(self._handle_check_spine_opt_version_finished)
            self._exec_mngr.start_execution()
            return
        self._handle_spine_opt_add_up_finished(ret)

    def _handle_check_spine_opt_version_finished(self, ret: int) -> None:
        self._exec_mngr.execution_finished.disconnect(self._handle_check_spine_opt_version_finished)
        if ret == 0:
            self.wizard().spine_opt_version_after_update = [int(v) for v in self._exec_mngr.process_output.split(".")]
        self._handle_spine_opt_add_up_finished(ret)

    def _handle_spine_opt_add_up_finished(self, ret: int) -> None:
        QApplication.restoreOverrideCursor()  # pylint: disable=undefined-variable
        required_action = self.wizard().required_action
        if required_action == "add":
            self._exec_mngr.execution_finished.disconnect(self._handle_spine_opt_add_up_finished)
        if self.wizard().currentPage() is not self:
            return
        self._exec_mngr = None
        self._successful = ret == 0
        self.completeChanged.emit()
        if self._successful:
            if required_action == "add":
                message = "SpineOpt successfully installed."
            elif self.wizard().spine_opt_version_before_update < self.wizard().spine_opt_version_after_update:
                message = "SpineOpt successfully updated."
            else:
                message = "No update found."
            self.msg_success.emit(message)
            return
        process = {"add": "installation", "update": "update"}[required_action]
        self.msg_error.emit(f"SpineOpt {process} failed")
        self.wizard().process_log = self._log.toHtml()
        self.wizard().process_log_plain = self._log.toPlainText()

    def nextId(self):
        if self._successful:
            return _PageId.SUCCESS
        return _PageId.FAILURE


class SuccessPage(QWizardPage):
    def __init__(self, parent: QWidget | None):
        super().__init__(parent)
        self._label = WrapLabel()
        layout = QVBoxLayout(self)
        layout.addWidget(self._label)

    def initializePage(self):
        required_action = self.wizard().required_action
        if required_action == "add":
            self.setTitle("Installation successful")
        else:
            if self.wizard().spine_opt_version_after_update > self.wizard().spine_opt_version_before_update:
                self.setTitle("Update successful")
            else:
                self.setTitle("No update available")

    def nextId(self):
        return -1


class FailurePage(QWizardPage):
    def initializePage(self):
        process = {"add": "Installation", "update": "Update"}[self.wizard().required_action]
        self.setTitle(f"{process} failed")
        check_box = QCheckBox("Troubleshoot problems")
        check_box.setChecked(True)
        self.registerField("troubleshoot", check_box)
        layout = QVBoxLayout(self)
        msg = (
            "Apologies. Please see the Troubleshoot problems section "
            "by clicking <b>Next</b> or click <b>Cancel</b> to close "
            "the wizard."
        )
        layout.addWidget(WrapLabel(msg))
        layout.addStretch()
        layout.addWidget(check_box)
        layout.addStretch()
        layout.addStretch()
        check_box.clicked.connect(self._handle_check_box_clicked)

    @Slot(bool)
    def _handle_check_box_clicked(self, checked: bool = False) -> None:
        self.setFinalPage(not checked)

    def nextId(self):
        if self.field("troubleshoot"):
            return _PageId.TROUBLESHOOT_PROBLEMS
        return -1


class TroubleshootProblemsPage(QWizardPage):
    def __init__(self, parent: QWidget | None):
        super().__init__(parent)
        self.setTitle("Troubleshooting")
        msg = "Select your problem from the list."
        self._button1 = QRadioButton("None of the below")
        self._button2 = QRadioButton("Installing SpineOpt fails with the following message (or similar):")
        msg2 = MonoSpaceFontTextBrowser(self)
        msg2.append("""
            \u22ee<br>
            error: GitError(Code:ERROR, Class:SSL, Your Julia is built with a SSL/TLS engine that libgit2 
            doesn't know how to configure to use a file or directory of certificate authority roots, 
            but your environment specifies one via the SSL_CERT_FILE variable. If you believe your 
            system's root certificates are safe to use, you can `export JULIA_SSL_CA_ROOTS_PATH=""` 
            in your environment to use those instead.<br>
            \u22ee
            """)
        self._button3 = QRadioButton("Installing SpineOpt fails with one of the following messages (or similar):")
        msg3a = MonoSpaceFontTextBrowser(self)
        msg3b = MonoSpaceFontTextBrowser(self)
        msg3a.append("""
            \u22ee<br>
            Updating git-repo `https://github.com/spine-tools/SpineJuliaRegistry`<br>
            Resolving package versions...<br>
            ERROR: expected package `UUIDs [cf7118a7]` to be registered<br>
            \u22ee
            """)
        msg3b.append("""
            \u22ee<br>
            Updating git-repo `https://github.com/spine-tools/SpineJuliaRegistry`<br>
            Resolving package versions...<br>
            ERROR: cannot find name corresponding to UUID f269a46b-ccf7-5d73-abea-4c690281aa53 in a registry<br>
            \u22ee
            """)
        self._button4 = QRadioButton("On Windows 7, installing SpineOpt fails with the following message (or similar):")
        msg4 = MonoSpaceFontTextBrowser(self)
        msg4.append("""
            \u22ee<br>
            Downloading artifact: OpenBLAS32<br>
            Exception setting "SecurityProtocol": "Cannot convert null to type "System.Net.<br>
            SecurityProtocolType" due to invalid enumeration values. Specify one of the fol<br>
            lowing enumeration values and try again. The possible enumeration values are "S<br>
            sl3, Tls"."<br>
            At line:1 char:35<br>
            + [System.Net.ServicePointManager]:: <<<< SecurityProtocol =<br>
            + CategoryInfo          : InvalidOperation: (:) [], RuntimeException<br>
            + FullyQualifiedErrorId : PropertyAssignmentException<br>
            \u22ee
            """)
        layout = QVBoxLayout(self)
        layout.addWidget(WrapLabel(msg))
        layout.addStretch()
        layout.addWidget(self._button1)
        layout.addStretch()
        layout.addWidget(self._button2)
        layout.addWidget(msg2)
        layout.addStretch()
        layout.addWidget(self._button3)
        layout.addWidget(msg3a)
        layout.addWidget(msg3b)
        layout.addStretch()
        layout.addWidget(self._button4)
        layout.addWidget(msg4)
        layout.addStretch()
        button_view_log = QPushButton("View log")
        widget_view_log = QWidget()
        layout_view_log = QHBoxLayout(widget_view_log)
        layout_view_log.addStretch()
        layout_view_log.addWidget(button_view_log)
        layout.addWidget(widget_view_log)
        layout.addStretch()
        cursor = QTextCursor()
        cursor.movePosition(QTextCursor.MoveOperation.Start, QTextCursor.MoveMode.MoveAnchor)
        msg2.setTextCursor(cursor)  # Scroll to the beginning of the document
        msg3a.setTextCursor(cursor)
        msg3b.setTextCursor(cursor)
        msg4.setTextCursor(cursor)
        self.registerField("problem1", self._button1)
        self.registerField("problem2", self._button2)
        self.registerField("problem3", self._button3)
        self.registerField("problem4", self._button4)
        self._button1.toggled.connect(lambda _: self.completeChanged.emit())
        self._button2.toggled.connect(lambda _: self.completeChanged.emit())
        self._button3.toggled.connect(lambda _: self.completeChanged.emit())
        self._button4.toggled.connect(lambda _: self.completeChanged.emit())
        button_view_log.clicked.connect(self._show_log)

    def isComplete(self):
        return self.field("problem1") or self.field("problem2") or self.field("problem3") or self.field("problem4")

    @Slot(bool)
    def _show_log(self, _: bool = False) -> None:
        log_widget = QWidget(self, f=Qt.WindowType.Window)
        layout = QVBoxLayout(log_widget)
        log = MonoSpaceFontTextBrowser(log_widget)
        log.append(self.wizard().process_log)
        layout.addWidget(log)
        log_widget.show()

    def nextId(self):
        return _PageId.TROUBLESHOOT_SOLUTION


class TroubleshootSolutionPage(QWizardPage):
    def __init__(self, parent: QWidget | None):
        super().__init__(parent)
        self.setCommitPage(True)
        QVBoxLayout(self)

    def initializePage(self):
        _clear_layout(self.layout())
        if self.field("problem1"):
            self._initialize_page_solution1()
        elif self.field("problem2"):
            self._initialize_page_solution2()
        elif self.field("problem3"):
            self._initialize_page_solution3()
        elif self.field("problem4"):
            self._initialize_page_solution4()

    def _initialize_page_solution1(self) -> None:
        self.setFinalPage(False)
        action = {"add": "Install SpineOpt", "update": "Update SpineOpt"}[self.wizard().required_action]
        julia = self.wizard().property("julia_exe")
        env = self.wizard().property("julia_project")
        if not env or env == "@.":
            install_cmds = f"""
            <span style="color:green;">julia> </span><span>import Pkg</span><br>
            <span style="color:green;">julia> </span><span>Pkg.Registry.add("General")</span><br>
            <span style="color:green;">julia> </span><span>Pkg.add("SpineOpt")</span><br>"""
        else:
            install_cmds = f"""
            <span style="color:green;">julia> </span><span>import Pkg</span><br>
            <span style="color:green;">julia> </span><span>cd("{env}")</span><br>
            <span style="color:green;">julia> </span><span>Pkg.activate(".")</span><br>
            <span style="color:green;">julia> </span><span>Pkg.Registry.add("General")</span><br>
            <span style="color:green;">julia> </span><span>Pkg.add("SpineOpt")</span><br>"""
        if not env or env == "@.":
            update_cmds = """
            <span style="color:green;">julia> </span><span>import Pkg</span><br>
            <span style="color:green;">julia> </span><span>Pkg.update("SpineInterface")</span><br>
            <span style="color:green;">julia> </span><span>Pkg.update("SpineOpt")</span><br>"""
        else:
            update_cmds = f"""
            <span style="color:green;">julia> </span><span>import Pkg</span><br>
            <span style="color:green;">julia> </span><span>cd("{env}")</span><br>
            <span style="color:green;">julia> </span><span>Pkg.activate(".")</span><br>
            <span style="color:green;">julia> </span><span>Pkg.update("SpineInterface")</span><br>
            <span style="color:green;">julia> </span><span>Pkg.update("SpineOpt")</span><br>"""
        action_cmds = {"Install SpineOpt": install_cmds, "Update SpineOpt": update_cmds}
        self.setTitle("What now?")
        msg_browser = MonoSpaceFontTextBrowser(self)
        msg_browser.append(action_cmds[action])
        label1_txt = (
            "<p><ol type'1'>"
            f"<li>Click the <b>{action}</b> button to try again.</li>"
            f"<li><b>{action}</b> manually. Open your favorite terminal (ie. Command prompt) and start the "
            f"Julia REPL using command:<br><br><i>{julia}</i><br><br>"
            "In the Julia REPL, enter the following commands (gray text, not the green one):</li></ol></p>"
        )
        label2_txt = (
            "<p>See also up-to-date "
            "<a href=https://spine-tools.github.io/SpineOpt.jl/latest/getting_started/installation>installation "
            "instructions in SpineOpt documentation</a>.</p>"
        )
        self.layout().addWidget(HyperTextLabel(label1_txt))
        self.layout().addWidget(msg_browser)
        self.layout().addWidget(HyperTextLabel(label2_txt))
        self.setButtonText(QWizard.WizardButton.CommitButton, action)

    def _initialize_page_solution2(self) -> None:
        self.setFinalPage(True)
        julia = self.wizard().property("julia_exe")
        env = self.wizard().property("julia_project")
        self.setTitle("Environment variable JULIA_SSL_CA_ROOTS_PATH missing")
        description = (
            "<p>You are most likely running Toolbox in a Conda environment and the issue "
            "you're facing is due to a missing environment variable. The simplest solution "
            "is to open the Julia REPL from the Anaconda Prompt, add the environment variable, "
            "and then install SpineOpt.</p>"
            "<p>To do this, open your Anaconda prompt and start the Julia REPL using "
            f"command:<br><br><i>{julia}</i><br><br>In the Julia REPL, enter the commands below (gray text, "
            "not the green one). After entering the commands, SpineOpt should be installed. If you run into "
            "other problems, please <a href=https://github.com/spine-tools/SpineOpt.jl/issues>open an issue "
            "with SpineOpt</a>.</p>"
        )
        if not env or env == "@.":
            install_cmds = f"""
            <span style="color:green;">julia> </span><span>using Pkg</span><br>
            <span style="color:green;">julia> </span><span>ENV["JULIA_SSL_CA_ROOTS_PATH"] = ""</span><br>
            <span style="color:green;">julia> </span><span>Pkg.Registry.add("General")</span><br>
            <span style="color:green;">julia> </span><span>Pkg.add("SpineOpt")</span><br>"""
        else:
            install_cmds = f"""
            <span style="color:green;">julia> </span><span>using Pkg</span><br>
            <span style="color:green;">julia> </span><span>cd("{env}")</span><br>
            <span style="color:green;">julia> </span><span>Pkg.activate(".")</span><br>
            <span style="color:green;">julia> </span><span>ENV["JULIA_SSL_CA_ROOTS_PATH"] = ""</span><br>
            <span style="color:green;">julia> </span><span>Pkg.Registry.add("General")</span><br>
            <span style="color:green;">julia> </span><span>Pkg.add("SpineOpt")</span><br>"""
        cmd_browser = MonoSpaceFontTextBrowser(self)
        cmd_browser.append(install_cmds)
        self.layout().addWidget(HyperTextLabel(description))
        self.layout().addWidget(cmd_browser)

    def _initialize_page_solution3(self) -> None:
        self.setFinalPage(True)
        julia = self.wizard().property("julia_exe")
        self.setTitle("Reset Julia General Registry")
        description = (
            "<p>The issue you're facing can be due to an error in the installation of the Julia General registry "
            "from the Julia Package Server. The simplest solution is to delete any trace of the registry and install "
            "it again from GitHub.</p>"
            "<p>To do this, open your favorite terminal (ie. Command prompt) and start the Julia REPL using "
            f"command:<br><br><i>{julia}</i><br><br>In the Julia REPL, enter the commands below (gray text, "
            "not the green one). Afterwards, try Add/Update SpineOpt again.</p>"
            "<p><b>NOTE: this will also remove all your installed packages</b>.</p>"
        )
        cmds = f"""
        <span style="color:green;">julia> </span><span>import Pkg</span><br>
        <span style="color:green;">julia> </span><span>Pkg.Registry.rm("General")</span><br>
        <span style="color:green;">julia> </span><span>Pkg.Registry.add()</span><br>"""
        cmd_browser = MonoSpaceFontTextBrowser(self)
        cmd_browser.append(cmds)
        self.layout().addWidget(HyperTextLabel(description))
        self.layout().addWidget(cmd_browser)

    def _initialize_page_solution4(self) -> None:
        self.setFinalPage(True)
        action = {"add": "Install SpineOpt", "update": "Update SpineOpt"}[self.wizard().required_action]
        self.setTitle("Update Windows Management Framework")
        description = (
            "<p>The issue you're facing can be solved by updating Windows Management Framework to 5.1 or greater, "
            "as follows:<ul>"
            "<li>Install latest .NET Framework (minimum 4.5) "
            "from <a href='https://dotnet.microsoft.com/en-us/download/dotnet-framework'>here</a>.</li>"
            "<li>Install Windows management framework 5.1 or later "
            "from <a href='https://www.microsoft.com/en-us/download/details.aspx?id=54616'>here</a>.</li>"
            f"<li>{action} again.</li>"
            "</ul></p>"
        )
        self.layout().addWidget(HyperTextLabel(description))

    def nextId(self):
        if self.field("problem2") or self.field("problem3") or self.field("problem4"):
            return -1
        return _PageId.ADD_UP_SPINE_OPT_AGAIN


class AddUpSpineOptAgainPage(AddUpSpineOptPage):
    def nextId(self):
        if self._successful:
            return _PageId.SUCCESS
        return _PageId.TOTAL_FAILURE


class TotalFailurePage(QWizardPage):
    def __init__(self, parent: QWidget | None):
        super().__init__(parent)
        self._copy_label = QLabel()

    def initializePage(self):
        self.setTitle("Troubleshooting failed")
        msg = (
            "<p>Please <a href=https://github.com/spine-tools/SpineOpt.jl/issues>open an issue with SpineOpt</a>."
            "<br>Copy the log and paste it into the issue description.</p>"
        )
        layout = QVBoxLayout(self)
        layout.addWidget(HyperTextLabel(msg))
        copy_widget = QWidget()
        copy_button = QPushButton("Copy log")
        self._copy_label.setText("Log copied to clipboard")
        self._copy_label.hide()
        layout_copy = QHBoxLayout(copy_widget)
        layout_copy.addWidget(copy_button)
        layout_copy.addWidget(self._copy_label)
        layout_copy.addStretch()
        layout.addWidget(copy_widget)
        copy_button.clicked.connect(self._handle_copy_clicked)

    @Slot(bool)
    def _handle_copy_clicked(self, _: bool = False) -> None:
        self._copy_label.show()
        QApplication.clipboard().setText(self.wizard().process_log_plain)  # pylint: disable=undefined-variable

    def nextId(self):
        return -1


def _clear_layout(layout: QLayout) -> None:
    while True:
        child = layout.takeAt(0)
        if child is None:
            break
        child.widget().deleteLater()


def _create_exec_manager_to_resolve_spine_opt_version(
    julia_exe: str, julia_project: str, logger: LoggerInterface
) -> QProcessExecutionManager:
    args = [
        f"--project={julia_project}",
        "-e",
        "import Pkg; "
        'manifest = joinpath(dirname(Base.active_project()), "Manifest.toml"); '
        "pkgs = isfile(manifest) ? Pkg.TOML.parsefile(manifest) : Dict(); "
        'manifest_format = get(pkgs, "manifest_format", missing); '
        "if manifest_format === missing "
        'spine_opt = get(pkgs, "SpineOpt", nothing) '
        'else spine_opt = get(pkgs["deps"], "SpineOpt", nothing) end; '
        'if spine_opt != nothing println(spine_opt[1]["version"]) end; ',
    ]
    return QProcessExecutionManager(logger, julia_exe, args, silent=True)
