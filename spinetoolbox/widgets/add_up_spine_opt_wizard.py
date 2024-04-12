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
from enum import IntEnum, auto
from PySide6.QtWidgets import (
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
    QRadioButton,
)
from PySide6.QtCore import Slot, Qt
from PySide6.QtGui import QCursor
from ..execution_managers import QProcessExecutionManager
from ..config import REQUIRED_SPINE_OPT_VERSION
from .custom_qtextbrowser import MonoSpaceFontTextBrowser
from .custom_qwidgets import WrapLabel, HyperTextLabel, QWizardProcessPage


class _PageId(IntEnum):
    INTRO = auto()
    SELECT_JULIA = auto()
    CHECK_PREVIOUS_INSTALL = auto()
    ADD_UP_SPINE_OPT = auto()
    SUCCESS = auto()
    FAILURE = auto()
    TROUBLESHOOT_PROBLEMS = auto()
    TROUBLESHOOT_SOLUTION = auto()
    RESET_REGISTRY = auto()
    ADD_UP_SPINE_OPT_AGAIN = auto()
    TOTAL_FAILURE = auto()


class AddUpSpineOptWizard(QWizard):
    """A wizard to install & upgrade SpineOpt."""

    def __init__(self, parent, julia_exe, julia_project):
        """
        Args:
            parent (QWidget): the parent widget (SettingsWidget)
            julia_exe (str): path to Julia executable
            julia_project (str): path to Julia project
        """
        super().__init__(parent)
        self.process_log = None
        self.required_action = None
        self.setWindowTitle("SpineOpt Installer")
        self.setPage(_PageId.INTRO, IntroPage(self))
        self.setPage(_PageId.SELECT_JULIA, SelectJuliaPage(self, julia_exe, julia_project))
        self.setPage(_PageId.CHECK_PREVIOUS_INSTALL, CheckPreviousInstallPage(self))
        self.setPage(_PageId.ADD_UP_SPINE_OPT, AddUpSpineOptPage(self))
        self.setPage(_PageId.SUCCESS, SuccessPage(self))
        self.setPage(_PageId.FAILURE, FailurePage(self))
        self.setPage(_PageId.TROUBLESHOOT_PROBLEMS, TroubleshootProblemsPage(self))
        self.setPage(_PageId.TROUBLESHOOT_SOLUTION, TroubleshootSolutionPage(self))
        self.setPage(_PageId.RESET_REGISTRY, ResetRegistryPage(self))
        self.setPage(_PageId.ADD_UP_SPINE_OPT_AGAIN, AddUpSpineOptAgainPage(self))
        self.setPage(_PageId.TOTAL_FAILURE, TotalFailurePage(self))
        self.setStartId(_PageId.INTRO)


class IntroPage(QWizardPage):
    def __init__(self, parent):
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

    @Slot(bool)
    def _select_julia_exe(self, _):
        julia_exe, _ = QFileDialog.getOpenFileName(self, "Select Julia executable", self.field("julia_exe"))
        if not julia_exe:
            return
        self.setField("julia_exe", julia_exe)

    @Slot(bool)
    def _select_julia_project(self, _):
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
        _clear_layout(self.layout())
        julia_exe = self.field("julia_exe")
        julia_project = self.field("julia_project")
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
        self._exec_mngr = QProcessExecutionManager(self, julia_exe, args, silent=True)
        self.completeChanged.emit()
        self._exec_mngr.execution_finished.connect(self._handle_check_install_finished)
        qApp.setOverrideCursor(QCursor(Qt.BusyCursor))  # pylint: disable=undefined-variable
        self._exec_mngr.start_execution()

    def _handle_check_install_finished(self, ret):
        qApp.restoreOverrideCursor()  # pylint: disable=undefined-variable
        self._exec_mngr.execution_finished.disconnect(self._handle_check_install_finished)
        if self.wizard().currentPage() is not self:
            return
        output_log = self._exec_mngr.process_output
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
            self.setFinalPage(False)
            self.setCommitPage(True)
            self.setButtonText(QWizard.CommitButton, "Update SpineOpt")
            self.completeChanged.emit()
            return
        self.layout().addWidget(QLabel("SpineOpt is not installed."))
        self.wizard().required_action = "add"
        self.setFinalPage(False)
        self.setCommitPage(True)
        self.setButtonText(QWizard.CommitButton, "Install SpineOpt")
        self.completeChanged.emit()

    def nextId(self):
        if self.wizard().required_action is None:
            return -1
        return _PageId.ADD_UP_SPINE_OPT


class AddUpSpineOptPage(QWizardProcessPage):
    def initializePage(self):
        processing, code, process = {
            "add": (
                "Installing",
                'using Pkg; pkg"registry add General https://github.com/spine-tools/SpineJuliaRegistry.git"; '
                'pkg"add SpineOpt"',
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
        self.msg.emit(f"$ <b>{cmd}<b/>")
        qApp.setOverrideCursor(QCursor(Qt.BusyCursor))  # pylint: disable=undefined-variable
        self._exec_mngr.start_execution()

    def _handle_spine_opt_add_up_finished(self, ret):
        qApp.restoreOverrideCursor()  # pylint: disable=undefined-variable
        self._exec_mngr.execution_finished.disconnect(self._handle_spine_opt_add_up_finished)
        if self.wizard().currentPage() is not self:
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
        check_box = QCheckBox("Troubleshoot problems")
        check_box.setChecked(True)
        self.registerField("troubleshoot", check_box)
        layout = QVBoxLayout(self)
        msg = "Apologies."
        layout.addWidget(WrapLabel(msg))
        layout.addStretch()
        layout.addWidget(check_box)
        layout.addStretch()
        layout.addStretch()
        check_box.clicked.connect(self._handle_check_box_clicked)

    @Slot(bool)
    def _handle_check_box_clicked(self, checked=False):
        self.setFinalPage(not checked)

    def initializePage(self):
        process = {"add": "Installation", "update": "Update"}[self.wizard().required_action]
        self.setTitle(f"{process} failed")

    def nextId(self):
        if self.field("troubleshoot"):
            return _PageId.TROUBLESHOOT_PROBLEMS
        return -1


class TroubleshootProblemsPage(QWizardPage):
    def __init__(self, parent):
        super().__init__(parent)
        self.setTitle("Troubleshooting")
        msg = "Select your problem from the list."
        self._button1 = QRadioButton("Installing SpineOpt fails with one of the following messages (or similar):")
        msg1a = MonoSpaceFontTextBrowser(self)
        msg1b = MonoSpaceFontTextBrowser(self)
        msg1a.append(
            """
            \u22ee<br>
            Updating git-repo `https://github.com/spine-tools/SpineJuliaRegistry`<br>
            Resolving package versions...<br>
            ERROR: expected package `UUIDs [cf7118a7]` to be registered<br>
            \u22ee
            """
        )
        msg1b.append(
            """
            \u22ee<br>
            Updating git-repo `https://github.com/spine-tools/SpineJuliaRegistry`<br>
            Resolving package versions...<br>
            ERROR: cannot find name corresponding to UUID f269a46b-ccf7-5d73-abea-4c690281aa53 in a registry<br>
            \u22ee
            """
        )
        self._button2 = QRadioButton("On Windows 7, installing SpineOpt fails with the following message (or similar):")
        msg2 = MonoSpaceFontTextBrowser(self)
        msg2.append(
            """
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
            """
        )
        layout = QVBoxLayout(self)
        layout.addWidget(WrapLabel(msg))
        layout.addStretch()
        layout.addWidget(self._button1)
        layout.addWidget(msg1a)
        layout.addWidget(msg1b)
        layout.addStretch()
        layout.addWidget(self._button2)
        layout.addWidget(msg2)
        layout.addStretch()
        button_view_log = QPushButton("View process log")
        widget_view_log = QWidget()
        layout_view_log = QHBoxLayout(widget_view_log)
        layout_view_log.addStretch()
        layout_view_log.addWidget(button_view_log)
        layout.addWidget(widget_view_log)
        layout.addStretch()
        self.registerField("problem1", self._button1)
        self.registerField("problem2", self._button2)
        self._button1.toggled.connect(lambda _: self.completeChanged.emit())
        self._button2.toggled.connect(lambda _: self.completeChanged.emit())
        button_view_log.clicked.connect(self._show_log)

    def isComplete(self):
        return self.field("problem1") or self.field("problem2")

    @Slot(bool)
    def _show_log(self, _=False):
        log_widget = QWidget(self, f=Qt.Window)
        layout = QVBoxLayout(log_widget)
        log = MonoSpaceFontTextBrowser(log_widget)
        log.append(self.wizard().process_log)
        layout.addWidget(log)
        log_widget.show()

    def nextId(self):
        return _PageId.TROUBLESHOOT_SOLUTION


class TroubleshootSolutionPage(QWizardPage):
    def __init__(self, parent):
        super().__init__(parent)
        self.setCommitPage(True)
        QVBoxLayout(self)

    def cleanupPage(self):
        super().cleanupPage()
        self.wizard().reset_registry = False

    def initializePage(self):
        _clear_layout(self.layout())
        if self.field("problem1"):
            self._initialize_page_solution1()
        elif self.field("problem2"):
            self._initialize_page_solution2()

    def _initialize_page_solution1(self):
        self.wizard().reset_registry = True
        self.setTitle("Reset Julia General Registry")
        description = (
            "<p>The issue you're facing can be due to an error in the installation of the Julia General registry "
            "from the Julia Package Server.</p>"
            "<p>The simplest solution is to delete any trace of the registry and install it again, from GitHub.</p>"
            "<p>However, <b>this will also remove all your installed packages</b>.</p>"
        )
        self.layout().addWidget(HyperTextLabel(description))
        self.setButtonText(QWizard.CommitButton, "Reset registry")

    def _initialize_page_solution2(self):
        action = {"add": "Install SpineOpt", "update": "Update SpineOpt"}[self.wizard().required_action]
        self.setTitle("Update Windows Managemet Framework")
        description = (
            "<p>The issue you're facing can be solved by installing Windows Managemet Framework 3 or greater, "
            "as follows:<ul>"
            "<li>Install .NET 4.5 "
            "from <a href=https://dotnet.microsoft.com/download/dotnet-framework/thank-you/"
            "net45-web-installer>here</a>.</li>"
            "<li>Install Windows management framework 3 or later "
            "from <a href=https://docs.microsoft.com/en-us/powershell/scripting/windows-powershell/wmf/"
            "overview?view=powershell-7.1>here</a>.</li>"
            f"<li>{action} again.</li>"
            "</ul></p>"
        )
        self.layout().addWidget(HyperTextLabel(description))
        self.setButtonText(QWizard.CommitButton, action)

    def nextId(self):
        if self.field("problem1"):
            return _PageId.RESET_REGISTRY
        return _PageId.ADD_UP_SPINE_OPT_AGAIN


class ResetRegistryPage(QWizardProcessPage):
    def initializePage(self):
        code = (
            "using Pkg; "
            'rm(joinp ath(DEPOT_PATH[1], "registries", "General"); force=true, recursive=true); '
            'withenv("JULIA_PKG_SERVER"=>"") do pkg"registry add" end'
        )
        self.setTitle("Resetting Julia General Registry")
        julia_exe = self.field("julia_exe")
        julia_project = self.field("julia_project")
        args = [f"--project={julia_project}", "-e", code]
        self._exec_mngr = QProcessExecutionManager(self, julia_exe, args, semisilent=True)
        self.completeChanged.emit()
        self._exec_mngr.execution_finished.connect(self._handle_registry_reset_finished)
        self.msg_success.emit("Registry reset started")
        cmd = julia_exe + " " + " ".join(args)
        self.msg.emit(f"$ <b>{cmd}<b/>")
        qApp.setOverrideCursor(QCursor(Qt.BusyCursor))  # pylint: disable=undefined-variable
        self._exec_mngr.start_execution()

    def _handle_registry_reset_finished(self, ret):
        qApp.restoreOverrideCursor()  # pylint: disable=undefined-variable
        self._exec_mngr.execution_finished.disconnect(self._handle_registry_reset_finished)
        if self.wizard().currentPage() is not self:
            return
        self._exec_mngr = None
        self._successful = ret == 0
        if self._successful:
            self.msg_success.emit("Registry successfully reset")
            self.setCommitPage(True)
            action = {"add": "Install SpineOpt", "update": "Update SpineOpt"}[self.wizard().required_action]
            self.setButtonText(QWizard.CommitButton, action)
        else:
            # FIXME: Rather, add a button to copy log to clipboard?
            # self.wizard().process_log = self._log.toHtml()
            self.msg_error.emit("Registry reset failed")
        self.completeChanged.emit()

    def nextId(self):
        if self._successful:
            return _PageId.ADD_UP_SPINE_OPT_AGAIN
        return _PageId.TOTAL_FAILURE


class AddUpSpineOptAgainPage(AddUpSpineOptPage):
    def nextId(self):
        if self._successful:
            return _PageId.SUCCESS
        return _PageId.TOTAL_FAILURE


class TotalFailurePage(QWizardPage):
    def __init__(self, parent):
        super().__init__(parent)
        self.setTitle("Troubleshooting failed")
        msg = "<p>Please <a href=https://github.com/spine-tools/SpineOpt.jl/issues>open an issue with SpineOpt</a>."
        layout = QVBoxLayout(self)
        layout.addWidget(HyperTextLabel(msg))

    def nextId(self):
        return -1


def _clear_layout(layout):
    while True:
        child = layout.takeAt(0)
        if child is None:
            break
        child.widget().deleteLater()
