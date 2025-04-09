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
from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QCursor, QTextCursor
from PySide6.QtWidgets import (
    QCheckBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QRadioButton,
    QVBoxLayout,
    QWidget,
    QWizard,
    QWizardPage,
    QApplication,
)
from ..config import REQUIRED_SPINE_OPT_VERSION
from ..execution_managers import QProcessExecutionManager
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
        self.setPage(_PageId.ADD_UP_SPINE_OPT_AGAIN, AddUpSpineOptAgainPage(self))
        self.setPage(_PageId.TOTAL_FAILURE, TotalFailurePage(self))
        self.setStartId(_PageId.INTRO)
        self.setOption(QWizard.WizardOption.NoCancelButtonOnLastPage)


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
        self.setTitle("Select Julia")
        self._julia_exe = julia_exe
        self._julia_project = julia_project
        self._julia_exe_line_edit = QLineEdit()
        self._julia_project_line_edit = QLineEdit()
        self._julia_project_line_edit.setPlaceholderText("Use Julia's default project")
        self.registerField("julia_exe*", self._julia_exe_line_edit)
        self.registerField("julia_project", self._julia_project_line_edit)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Julia executable"))
        julia_exe_widget = QWidget()
        julia_exe_layout = QHBoxLayout(julia_exe_widget)
        julia_exe_layout.addWidget(self._julia_exe_line_edit)
        julia_exe_button = QPushButton("Browse")
        julia_exe_layout.addWidget(julia_exe_button)
        layout.addWidget(julia_exe_widget)
        layout.addWidget(QLabel("Julia project/environment (directory)"))
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
            self, "Select Julia project/environment (directory)", self.field("julia_project")
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
        QApplication.setOverrideCursor(QCursor(Qt.CursorShape.BusyCursor))  # pylint: disable=undefined-variable
        self._exec_mngr.start_execution()

    def _handle_check_install_finished(self, ret):
        QApplication.restoreOverrideCursor()  # pylint: disable=undefined-variable
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
                f"but version {REQUIRED_SPINE_OPT_VERSION} or higher is required."
            )
            self.layout().addWidget(WrapLabel(msg))
            self.wizard().required_action = "update"
            self.setFinalPage(False)
            self.setCommitPage(True)
            self.setButtonText(QWizard.WizardButton.CommitButton, "Update SpineOpt")
            self.completeChanged.emit()
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
        processing, code, process = {
            "add": (
                "Installing",
                'using Pkg; Pkg.Registry.add("General"); Pkg.add("SpineOpt")',
                "installation",
            ),
            "update": ("Updating", 'using Pkg; Pkg.update("SpineInterface"); Pkg.update("SpineOpt")', "update"),
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
        QApplication.setOverrideCursor(QCursor(Qt.CursorShape.BusyCursor))  # pylint: disable=undefined-variable
        self._exec_mngr.start_execution()

    def _handle_spine_opt_add_up_finished(self, ret):
        QApplication.restoreOverrideCursor()  # pylint: disable=undefined-variable
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
        process = {"add": "installation", "update": "update"}[self.wizard().required_action]
        self.msg_error.emit(f"SpineOpt {process} failed")
        self.wizard().process_log = self._log.toHtml()
        self.wizard().process_log_plain = self._log.toPlainText()

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
    def _handle_check_box_clicked(self, checked=False):
        self.setFinalPage(not checked)

    def nextId(self):
        if self.field("troubleshoot"):
            return _PageId.TROUBLESHOOT_PROBLEMS
        return -1


class TroubleshootProblemsPage(QWizardPage):
    def __init__(self, parent):
        super().__init__(parent)
        self.setTitle("Troubleshooting")
        msg = "Select your problem from the list."
        self._button1 = QRadioButton("None of the below")
        self._button2 = QRadioButton("Installing SpineOpt fails with the following message (or similar):")
        msg2 = MonoSpaceFontTextBrowser(self)
        msg2.append(
            """
            \u22ee<br>
            error: GitError(Code:ERROR, Class:SSL, Your Julia is built with a SSL/TLS engine that libgit2 
            doesn't know how to configure to use a file or directory of certificate authority roots, 
            but your environment specifies one via the SSL_CERT_FILE variable. If you believe your 
            system's root certificates are safe to use, you can `export JULIA_SSL_CA_ROOTS_PATH=""` 
            in your environment to use those instead.<br>
            \u22ee
            """
        )
        self._button3 = QRadioButton("Installing SpineOpt fails with one of the following messages (or similar):")
        msg3a = MonoSpaceFontTextBrowser(self)
        msg3b = MonoSpaceFontTextBrowser(self)
        msg3a.append(
            """
            \u22ee<br>
            Updating git-repo `https://github.com/spine-tools/SpineJuliaRegistry`<br>
            Resolving package versions...<br>
            ERROR: expected package `UUIDs [cf7118a7]` to be registered<br>
            \u22ee
            """
        )
        msg3b.append(
            """
            \u22ee<br>
            Updating git-repo `https://github.com/spine-tools/SpineJuliaRegistry`<br>
            Resolving package versions...<br>
            ERROR: cannot find name corresponding to UUID f269a46b-ccf7-5d73-abea-4c690281aa53 in a registry<br>
            \u22ee
            """
        )
        self._button4 = QRadioButton("On Windows 7, installing SpineOpt fails with the following message (or similar):")
        msg4 = MonoSpaceFontTextBrowser(self)
        msg4.append(
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
    def _show_log(self, _=False):
        log_widget = QWidget(self, f=Qt.WindowType.Window)
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

    def _initialize_page_solution1(self):
        self.setFinalPage(False)
        action = {"add": "Install SpineOpt", "update": "Update SpineOpt"}[self.wizard().required_action]
        julia = self.field("julia_exe")
        env = self.field("julia_project")
        if not env:
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
        if not env:
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

    def _initialize_page_solution2(self):
        self.setFinalPage(True)
        julia = self.field("julia_exe")
        env = self.field("julia_project")
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
        if not env:
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

    def _initialize_page_solution3(self):
        self.setFinalPage(True)
        julia = self.field("julia_exe")
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

    def _initialize_page_solution4(self):
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
    def __init__(self, parent):
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
    def _handle_copy_clicked(self, _=False):
        self._copy_label.show()
        QApplication.clipboard().setText(self.wizard().process_log_plain)  # pylint: disable=undefined-variable

    def nextId(self):
        return -1


def _clear_layout(layout):
    while True:
        child = layout.takeAt(0)
        if child is None:
            break
        child.widget().deleteLater()
