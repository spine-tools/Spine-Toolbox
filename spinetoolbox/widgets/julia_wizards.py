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

import sys
import os
from enum import IntEnum, auto
from jill.install import default_symlink_dir, default_install_dir
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
from .custom_qtextbrowser import CustomQTextBrowser


class _PageId(IntEnum):
    INTRO = auto()
    SELECT_DIRS = auto()
    INSTALL = auto()
    SUCCESS = auto()
    FAILURE = auto()


class IntroPage(QWizardPage):
    def __init__(self, parent):
        super().__init__(parent)
        self.setTitle("Welcome")
        label = QLabel("This wizard will help you install Julia in your computer.")
        label.setWordWrap(True)
        layout = QVBoxLayout(self)
        layout.addWidget(label)

    def nextId(self):
        return _PageId.SELECT_DIRS


class SelectDirsPage(QWizardPage):
    def __init__(self, parent):
        super().__init__(parent)
        self.setTitle("Select directories")
        install_dir_line_edit = QLineEdit()
        symlink_dir_line_edit = QLineEdit()
        self.registerField("install_dir", install_dir_line_edit)
        self.registerField("symlink_dir", symlink_dir_line_edit)
        install_dir_line_edit.setText(default_install_dir())
        symlink_dir_line_edit.setText(default_symlink_dir())
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Where do you want Julia packages installed:"))
        install_dir_widget = QWidget()
        install_dir_layout = QHBoxLayout(install_dir_widget)
        install_dir_layout.addWidget(install_dir_line_edit)
        install_dir_button = QPushButton("Browse")
        install_dir_layout.addWidget(install_dir_button)
        layout.addWidget(install_dir_widget)
        layout.addWidget(QLabel("Where you want Julia executables (e.g., `julia`, `julia-1`) placed:"))
        symlink_dir_widget = QWidget()
        symlink_dir_layout = QHBoxLayout(symlink_dir_widget)
        symlink_dir_layout.addWidget(symlink_dir_line_edit)
        symlink_dir_button = QPushButton("Browse")
        symlink_dir_layout.addWidget(symlink_dir_button)
        layout.addWidget(symlink_dir_widget)
        install_dir_button.clicked.connect(self._select_install_dir)
        symlink_dir_button.clicked.connect(self._select_symlink_dir)
        self.setCommitPage(True)
        self.setButtonText(QWizard.CommitButton, "Install Julia")

    def _select_install_dir(self):
        install_dir = QFileDialog.getExistingDirectory(
            self, "Select Julia install directory", self.field("install_dir")
        )
        if not install_dir:
            return
        self.setField("install_dir", install_dir)

    def _select_symlink_dir(self):
        symlink_dir = QFileDialog.getExistingDirectory(
            self, "Select Julia executables directory", self.field("symlink_dir")
        )
        if not symlink_dir:
            return
        self.setField("symlink_dir", symlink_dir)

    def nextId(self):
        return _PageId.INSTALL


class InstallJuliaPage(QWizardPage):

    msg = Signal(str)
    msg_warning = Signal(str)
    msg_error = Signal(str)
    msg_success = Signal(str)
    msg_proc = Signal(str)
    msg_proc_error = Signal(str)

    def __init__(self, parent):
        super().__init__(parent)
        self.setTitle("Installing Julia")
        self._log = CustomQTextBrowser(self)
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
        msg = self._log.append(format_log_message("msg", msg, show_datetime=False))
        self._log.append(msg)

    def _add_msg_warning(self, msg):
        msg = self._log.append(format_log_message("msg_warning", msg, show_datetime=False))
        self._log.append(msg)

    def _add_msg_error(self, msg):
        msg = self._log.append(format_log_message("msg_error", msg, show_datetime=False))
        self._log.append(msg)

    def _add_msg_succes(self, msg):
        msg = self._log.append(format_log_message("msg_success", msg, show_datetime=False))
        self._log.append(msg)

    def isComplete(self):
        return self._exec_mngr is None

    def initializePage(self):
        self._exec_mngr = QProcessExecutionManager(
            self,
            sys.executable,
            [
                "-m",
                "jill",
                "install",
                "--confirm",
                "--install_dir",
                self.field("install_dir"),
                "--symlink_dir",
                self.field("symlink_dir"),
            ],
        )
        qApp.setOverrideCursor(QCursor(Qt.BusyCursor))  # pylint: disable=undefined-variable
        self.completeChanged.emit()
        self._exec_mngr.execution_finished.connect(self._handle_julia_install_finished)
        self._exec_mngr.start_execution()

    @Slot(int)
    def _handle_julia_install_finished(self, ret):
        self._exec_mngr.execution_finished.disconnect(self._handle_julia_install_finished)
        if self.wizard().currentPage() != self:
            return
        self._exec_mngr = None
        qApp.restoreOverrideCursor()  # pylint: disable=undefined-variable
        self.completeChanged.emit()
        self._successful = ret == 0
        if ret == 0:
            self.wizard().set_julia_exe()
        if self.wizard().julia_exe is not None:
            self.msg_success.emit("Julia successfully installed")
            return
        self.msg_success.emit("Julia installation failed")

    def cleanupPage(self):
        super().cleanupPage()
        if self._exec_mngr is not None:
            self._exec_mngr.stop_execution()
        self.msg_error.emit("Aborted by the user")
        qApp.restoreOverrideCursor()  # pylint: disable=undefined-variable

    def nextId(self):
        if self.wizard().julia_exe is not None:
            return _PageId.SUCCESS
        return _PageId.FAILURE


class SuccessPage(QWizardPage):
    def __init__(self, parent):
        super().__init__(parent)
        self.setTitle("Installation successful")
        self._label = QLabel()
        layout = QVBoxLayout(self)
        check_box = QCheckBox("Use this Julia with Spine Toolbox")
        check_box.setChecked(True)
        self.registerField("use_julia", check_box)
        layout.addWidget(self._label)
        layout.addStretch()
        layout.addWidget(check_box)
        layout.addStretch()
        layout.addStretch()

    def initializePage(self):
        self._label.setText(f"Julia executable created at '{self.wizard().julia_exe}'")

    def nextId(self):
        return -1


class FailurePage(QWizardPage):
    def __init__(self, parent):
        super().__init__(parent)
        self.setTitle("Installation failed")
        label = QLabel(
            "Apologies. You may install Julia manually "
            "from <a title='julia downloads' href='https://julialang.org/downloads/'>here</a>."
        )
        label.setWordWrap(True)
        label.setTextFormat(Qt.RichText)
        label.setTextInteractionFlags(Qt.TextBrowserInteraction)
        label.setOpenExternalLinks(True)
        layout = QVBoxLayout(self)
        layout.addWidget(label)

    def nextId(self):
        return -1


class InstallJuliaWizard(QWizard):
    """A wizard to install julia
    """

    julia_exe_selected = Signal(str)

    def __init__(self, parent):
        """Initialize class.

        Args:
            parent (QWidget): the parent widget
            db_names (str): database names
        """
        super().__init__(parent)
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
            (file for file in os.listdir(self.field('symlink_dir')) if file.lower().startswith("julia")), None
        )
        if basename is None:
            self.julia_exe = None
            return
        self.julia_exe = os.path.join(self.field('symlink_dir'), basename)

    def accept(self):
        super().accept()
        if self.field("use_julia"):
            self.julia_exe_selected.emit(self.julia_exe)
