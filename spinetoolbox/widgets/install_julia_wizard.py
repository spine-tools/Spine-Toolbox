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

try:
    import jill.install as jill_install
except ModuleNotFoundError:
    jill_install = None
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
)
from PySide6.QtCore import Signal, Slot, Qt
from PySide6.QtGui import QCursor
from spine_engine.utils.helpers import resolve_current_python_interpreter
from ..execution_managers import QProcessExecutionManager
from ..config import APPLICATION_PATH
from .custom_qwidgets import HyperTextLabel, QWizardProcessPage, LabelWithCopyButton


class _PageId(IntEnum):
    INTRO = auto()
    SELECT_DIRS = auto()
    INSTALL = auto()
    SUCCESS = auto()
    FAILURE = auto()


class InstallJuliaWizard(QWizard):
    """A wizard to install julia"""

    julia_exe_selected = Signal(str)

    def __init__(self, parent):
        """Initialize class.

        Args:
            parent (QWidget): the parent widget (SettingsWidget)
        """
        super().__init__(parent)
        if jill_install is None:
            self.addPage(JillNotFoundPage(self))
            return
        self.julia_exe = None
        self.setWindowTitle("Julia Installer")
        self.setPage(_PageId.INTRO, IntroPage(self))
        self.setPage(_PageId.SELECT_DIRS, SelectDirsPage(self))
        self.setPage(_PageId.INSTALL, InstallJuliaPage(self))
        self.setPage(_PageId.SUCCESS, SuccessPage(self))
        self.setPage(_PageId.FAILURE, FailurePage(self))
        self.setStartId(_PageId.INTRO)

    def set_julia_exe(self):
        basename = next(
            (file for file in os.listdir(self.field("symlink_dir")) if file.lower().startswith("julia")), None
        )
        if basename is None:
            self.julia_exe = None
            return
        self.julia_exe = os.path.join(self.field("symlink_dir"), basename)

    def accept(self):
        super().accept()
        if jill_install is not None and self.field("use_julia"):
            self.julia_exe_selected.emit(self.julia_exe)


class JillNotFoundPage(QWizardPage):
    def __init__(self, parent):
        super().__init__(parent)
        self.setTitle("Unable to find jill")
        conda_env = os.environ.get("CONDA_DEFAULT_ENV", "base")
        toolbox_dir = os.path.dirname(APPLICATION_PATH)
        header = (
            "<p>Spine Toolbox needs the <a href='https://pypi.org/project/jill/'>jill</a> package "
            "to install Julia. "
            "To get the right version of jill for Spine Toolbox, "
            "please upgrade requirements as follows:</p>"
        )
        indent = 4 * "&nbsp;"
        point1 = f"{indent}1. Open Anaconda prompt."
        point2 = f"{indent}2. Activate the {conda_env} environment:"
        point3 = f"{indent}3. Navigate to your Spine Toolbox directory:"
        point4 = f"{indent}4. Upgrade requirements using <b>pip</b>:"
        point5 = f"{indent}5. Restart Spine Toolbox."
        layout = QVBoxLayout(self)
        layout.addWidget(HyperTextLabel(header))
        layout.addWidget(HyperTextLabel(point1))
        layout.addWidget(HyperTextLabel(point2))
        layout.addWidget(LabelWithCopyButton(f"conda activate {conda_env}"))
        layout.addWidget(HyperTextLabel(point3))
        layout.addWidget(LabelWithCopyButton(f"cd {toolbox_dir}"))
        layout.addWidget(HyperTextLabel(point4))
        layout.addWidget(LabelWithCopyButton("python -m pip install --upgrade -r requirements.txt"))
        layout.addWidget(HyperTextLabel(point5))


class IntroPage(QWizardPage):
    def __init__(self, parent):
        super().__init__(parent)
        self.setTitle("Welcome")
        label = HyperTextLabel(
            "This wizard will help you install "
            "<a title='julia language' href='https://julialang.org/'>Julia</a> in your computer."
        )
        layout = QVBoxLayout(self)
        layout.addWidget(label)

    def nextId(self):
        return _PageId.SELECT_DIRS


class SelectDirsPage(QWizardPage):
    def __init__(self, parent):
        super().__init__(parent)
        self.setTitle("Select directories")
        self._install_dir_line_edit = QLineEdit()
        self._symlink_dir_line_edit = QLineEdit()
        self.registerField("install_dir*", self._install_dir_line_edit)
        self.registerField("symlink_dir*", self._symlink_dir_line_edit)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Directory for Julia packages:"))
        install_dir_widget = QWidget()
        install_dir_layout = QHBoxLayout(install_dir_widget)
        install_dir_layout.addWidget(self._install_dir_line_edit)
        install_dir_button = QPushButton("Browse")
        install_dir_layout.addWidget(install_dir_button)
        layout.addWidget(install_dir_widget)
        layout.addWidget(QLabel("Directory for Julia executable:"))
        symlink_dir_widget = QWidget()
        symlink_dir_layout = QHBoxLayout(symlink_dir_widget)
        symlink_dir_layout.addWidget(self._symlink_dir_line_edit)
        symlink_dir_button = QPushButton("Browse")
        symlink_dir_layout.addWidget(symlink_dir_button)
        layout.addWidget(symlink_dir_widget)
        install_dir_button.clicked.connect(self._select_install_dir)
        symlink_dir_button.clicked.connect(self._select_symlink_dir)
        self.setCommitPage(True)
        self.setButtonText(QWizard.CommitButton, "Install Julia")

    def initializePage(self):
        self._install_dir_line_edit.setText(jill_install.default_install_dir())
        self._symlink_dir_line_edit.setText(jill_install.default_symlink_dir())

    def _select_install_dir(self):
        install_dir = QFileDialog.getExistingDirectory(
            self, "Select directory for Julia packages", self.field("install_dir")
        )
        if not install_dir:
            return
        self.setField("install_dir", install_dir)

    def _select_symlink_dir(self):
        symlink_dir = QFileDialog.getExistingDirectory(
            self, "Select directory for Julia executable", self.field("symlink_dir")
        )
        if not symlink_dir:
            return
        self.setField("symlink_dir", symlink_dir)

    def nextId(self):
        return _PageId.INSTALL


class InstallJuliaPage(QWizardProcessPage):
    def __init__(self, parent):
        super().__init__(parent)
        self.setTitle("Installing Julia")

    def cleanupPage(self):
        super().cleanupPage()
        if self._exec_mngr is not None:
            self._exec_mngr.stop_execution()
        self.msg_error.emit("Aborted by the user")

    def initializePage(self):
        args = [
            "-m",
            "jill",
            "install",
            "--confirm",
            "--install_dir",
            self.field("install_dir"),
            "--symlink_dir",
            self.field("symlink_dir"),
        ]
        # Resolve Python in this order
        # 1. sys.executable when not frozen
        # 2. PATH python if frozen (This fails if no jill installed)
        # 3. If no PATH python, uses embedded python <install_dir>/tools/python.exe
        python = resolve_current_python_interpreter()
        self._exec_mngr = QProcessExecutionManager(self, python, args, semisilent=True)
        self.completeChanged.emit()
        self._exec_mngr.execution_finished.connect(self._handle_julia_install_finished)
        self.msg_success.emit("Julia installation started")
        cmd = python + " " + " ".join(args)
        self.msg.emit(f"$ <b>{cmd}<b/>")
        qApp.setOverrideCursor(QCursor(Qt.BusyCursor))  # pylint: disable=undefined-variable
        self._exec_mngr.start_execution()

    @Slot(int)
    def _handle_julia_install_finished(self, ret):
        qApp.restoreOverrideCursor()  # pylint: disable=undefined-variable
        self._exec_mngr.execution_finished.disconnect(self._handle_julia_install_finished)
        if self.wizard().currentPage() != self:
            return
        self._exec_mngr = None
        self.completeChanged.emit()
        if ret == 0:
            self.wizard().set_julia_exe()
        if self.wizard().julia_exe is not None:
            self.msg_success.emit("Julia successfully installed")
            return
        self.msg_error.emit("Julia installation failed")

    def nextId(self):
        if self.wizard().julia_exe is not None:
            return _PageId.SUCCESS
        return _PageId.FAILURE


class SuccessPage(QWizardPage):
    def __init__(self, parent):
        super().__init__(parent)
        self.setTitle("Installation successful")
        self._label = HyperTextLabel()
        layout = QVBoxLayout(self)
        use_julia_check_box = QCheckBox("Use this Julia with Spine Toolbox")
        self.registerField("use_julia", use_julia_check_box)
        layout.addWidget(self._label)
        layout.addStretch()
        layout.addWidget(use_julia_check_box)
        layout.addStretch()
        layout.addStretch()

    def initializePage(self):
        self._label.setText(f"Julia executable created at <b>{self.wizard().julia_exe}</b>")
        self.setField("use_julia", True)

    def nextId(self):
        return -1


class FailurePage(QWizardPage):
    def __init__(self, parent):
        super().__init__(parent)
        self.setTitle("Installation failed")
        self._label = HyperTextLabel()
        layout = QVBoxLayout(self)
        layout.addWidget(self._label)

    def initializePage(self):
        self._label.setText(
            "Apologies. Please install Julia manually "
            "from <a title='julia downloads' href='https://julialang.org/downloads/'>here</a>."
        )

    def nextId(self):
        return -1
