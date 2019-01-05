######################################################################################################################
# Copyright (C) 2017 - 2018 Spine project consortium
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""
Widget for controlling user settings.

:author: P. Savolainen (VTT)
:date:   17.1.2018
"""

import os
from PySide2.QtWidgets import QWidget, QStatusBar, QFileDialog, QStyle
from PySide2.QtCore import Slot, Qt
import ui.settings
from config import DEFAULT_PROJECT_DIR, DEFAULT_WORK_DIR, STATUSBAR_SS, \
    SETTINGS_SS, GAMS_EXECUTABLE, GAMSIDE_EXECUTABLE, JULIA_EXECUTABLE


class SettingsWidget(QWidget):
    """ A widget to change user's preferred settings.

    Attributes:
        toolbox (ToolboxUI): Parent widget.
        configs (ConfigurationParser): Configuration object
    """
    def __init__(self, toolbox, configs):
        """ Initialize class. """
        super().__init__(parent=toolbox, f=Qt.Window)  # Do not set parent. Uses own stylesheet.
        self._toolbox = toolbox  # QWidget parent
        self._configs = configs
        self._project = self._toolbox.project()
        self.orig_work_dir = ""  # Work dir when this widget was opened
        # Set up the ui from Qt Designer files
        self.ui = ui.settings.Ui_SettingsForm()
        self.ui.setupUi(self)
        self.ui.toolButton_browse_gams.setIcon(self.style().standardIcon(QStyle.SP_DialogOpenButton))
        self.ui.toolButton_browse_julia.setIcon(self.style().standardIcon(QStyle.SP_DialogOpenButton))
        self.ui.toolButton_browse_work.setIcon(self.style().standardIcon(QStyle.SP_DialogOpenButton))
        self.setWindowFlags(Qt.Window | Qt.CustomizeWindowHint)
        # Ensure this window gets garbage-collected when closed
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.statusbar = QStatusBar(self)
        self.statusbar.setFixedHeight(20)
        self.statusbar.setSizeGripEnabled(False)
        self.statusbar.setStyleSheet(STATUSBAR_SS)
        self.ui.horizontalLayout_statusbar_placeholder.addWidget(self.statusbar)
        self.setStyleSheet(SETTINGS_SS)
        self.ui.pushButton_ok.setDefault(True)
        self._mousePressPos = None
        self._mouseReleasePos = None
        self._mouseMovePos = None
        self.connect_signals()
        self.read_settings()
        self.read_project_settings()

    def connect_signals(self):
        """ Connect PyQt signals. """
        self.ui.pushButton_ok.clicked.connect(self.ok_clicked)
        self.ui.pushButton_cancel.clicked.connect(self.close)
        self.ui.toolButton_browse_gams.clicked.connect(self.browse_gams_path)
        self.ui.toolButton_browse_julia.clicked.connect(self.browse_julia_path)
        self.ui.toolButton_browse_work.clicked.connect(self.browse_work_path)

    @Slot(bool, name="browse_gams_path")
    def browse_gams_path(self, checked=False):
        """Open file browser where user can select the directory of
        GAMS that the user wants to use."""
        # noinspection PyCallByClass, PyTypeChecker, PyArgumentList
        answer = QFileDialog.getExistingDirectory(self, 'Select GAMS Directory', os.path.abspath('C:\\'))
        if answer == '':  # Cancel button clicked
            return
        selected_path = os.path.abspath(answer)
        gams_path = os.path.join(selected_path, GAMS_EXECUTABLE)
        gamside_path = os.path.join(selected_path, GAMSIDE_EXECUTABLE)
        if not os.path.isfile(gams_path) and not os.path.isfile(gamside_path):
            self.statusbar.showMessage("gams.exe and gamside.exe not found in selected directory", 10000)
            self.ui.lineEdit_gams_path.setText("")
            return
        else:
            self.statusbar.showMessage("Selected directory is valid GAMS directory", 10000)
            self.ui.lineEdit_gams_path.setText(selected_path)
        return

    @Slot(bool, name="browse_julia_path")
    def browse_julia_path(self, checked=False):
        """Open file browser where user can select the path to wanted Julia version."""
        # noinspection PyCallByClass, PyTypeChecker, PyArgumentList
        answer = QFileDialog.getExistingDirectory(self, 'Select Julia Directory', os.path.abspath('C:\\'))
        if answer == '':  # Cancel button clicked
            return
        selected_path = os.path.abspath(answer)
        julia_path = os.path.join(selected_path, JULIA_EXECUTABLE)
        if not os.path.isfile(julia_path):
            self.statusbar.showMessage("julia.exe not found in selected directory", 10000)
            self.ui.lineEdit_julia_path.setText("")
            return
        else:
            self.statusbar.showMessage("Selected directory is valid Julia directory", 10000)
            self.ui.lineEdit_julia_path.setText(selected_path)
        return

    @Slot(bool, name="browse_work_path")
    def browse_work_path(self, checked=False):
        """Open file browser where user can select the path to wanted work directory."""
        # noinspection PyCallByClass, PyTypeChecker, PyArgumentList
        answer = QFileDialog.getExistingDirectory(self, 'Select work directory', os.path.abspath('C:\\'))
        if answer == '':  # Cancel button clicked
            return
        selected_path = os.path.abspath(answer)
        self.ui.lineEdit_work_dir.setText(selected_path)

    def read_settings(self):
        """Read current settings from config object and update UI to show them."""
        open_previous_project = self._configs.getboolean("settings", "open_previous_project")
        show_exit_prompt = self._configs.getboolean("settings", "show_exit_prompt")
        save_at_exit = self._configs.get("settings", "save_at_exit")  # Tri-state checkBox
        commit_at_exit = self._configs.get("settings", "commit_at_exit")  # Tri-state checkBox
        use_smooth_zoom = self._configs.getboolean("settings", "use_smooth_zoom")
        proj_dir = self._configs.get("settings", "project_directory")
        datetime = self._configs.getboolean("settings", "datetime")
        gams_path = self._configs.get("settings", "gams_path")
        use_repl = self._configs.getboolean("settings", "use_repl")
        julia_path = self._configs.get("settings", "julia_path")
        delete_data = self._configs.getboolean("settings", "delete_data")
        if open_previous_project:
            self.ui.checkBox_open_previous_project.setCheckState(Qt.Checked)
        if show_exit_prompt:
            self.ui.checkBox_exit_prompt.setCheckState(Qt.Checked)
        if save_at_exit == "0":  # Not needed but makes the code more readable.
            self.ui.checkBox_save_at_exit.setCheckState(Qt.Unchecked)
        elif save_at_exit == "1":
            self.ui.checkBox_save_at_exit.setCheckState(Qt.PartiallyChecked)
        elif save_at_exit == "2":
            self.ui.checkBox_save_at_exit.setCheckState(Qt.Checked)
        else:  # default
            self.ui.checkBox_save_at_exit.setCheckState(Qt.PartiallyChecked)
        if commit_at_exit == "0":  # Not needed but makes the code more readable.
            self.ui.checkBox_commit_at_exit.setCheckState(Qt.Unchecked)
        elif commit_at_exit == "1":
            self.ui.checkBox_commit_at_exit.setCheckState(Qt.PartiallyChecked)
        elif commit_at_exit == "2":
            self.ui.checkBox_commit_at_exit.setCheckState(Qt.Checked)
        else:  # default
            self.ui.checkBox_commit_at_exit.setCheckState(Qt.PartiallyChecked)
        if use_smooth_zoom:
            self.ui.checkBox_use_smooth_zoom.setCheckState(Qt.Checked)
        if datetime:
            self.ui.checkBox_datetime.setCheckState(Qt.Checked)
        if delete_data:
            self.ui.checkBox_delete_data.setCheckState(Qt.Checked)
        if not proj_dir:
            proj_dir = DEFAULT_PROJECT_DIR
        self.ui.lineEdit_project_dir.setText(proj_dir)
        self.ui.lineEdit_gams_path.setText(gams_path)
        if use_repl:
            self.ui.checkBox_use_repl.setCheckState(Qt.Checked)
        self.ui.lineEdit_julia_path.setText(julia_path)

    def read_project_settings(self):
        """Read project settings from config object and update settings widgets accordingly."""
        work_dir = DEFAULT_WORK_DIR
        if self._project:
            self.ui.lineEdit_project_name.setText(self._project.name)
            self.ui.textEdit_project_description.setText(self._project.description)
            work_dir = self._project.work_dir
        self.ui.lineEdit_work_dir.setText(work_dir)
        self.orig_work_dir = work_dir

    @Slot(name='ok_clicked')
    def ok_clicked(self):
        """Get selections and save them to conf file."""
        a = int(self.ui.checkBox_open_previous_project.checkState())
        b = int(self.ui.checkBox_exit_prompt.checkState())
        f = str(int(self.ui.checkBox_save_at_exit.checkState()))
        g = str(int(self.ui.checkBox_commit_at_exit.checkState()))
        h = int(self.ui.checkBox_use_smooth_zoom.checkState())
        d = int(self.ui.checkBox_datetime.checkState())
        delete_data = int(self.ui.checkBox_delete_data.checkState())
        # Check that GAMS directory is valid. Set it empty if not.
        gams_path = self.ui.lineEdit_gams_path.text()
        if not gams_path == "":  # Skip this if using GAMS in system path
            gams_exe_path = os.path.join(gams_path, GAMS_EXECUTABLE)
            gamside_exe_path = os.path.join(gams_path, GAMSIDE_EXECUTABLE)
            if not os.path.isfile(gams_exe_path) and not os.path.isfile(gamside_exe_path):
                self.statusbar.showMessage("GAMS executables not found in selected directory", 10000)
                return
        e = int(self.ui.checkBox_use_repl.checkState())
        # Check that Julia directory is valid. Set it empty if not.
        julia_path = self.ui.lineEdit_julia_path.text()
        if not julia_path == "":  # Skip this if using Julia in system path
            julia_exe_path = os.path.join(julia_path, JULIA_EXECUTABLE)
            if not os.path.isfile(julia_exe_path):
                self.statusbar.showMessage("Julia executable not found in selected directory", 10000)
                return
        # Write to config object
        self._configs.setboolean("settings", "open_previous_project", a)
        self._configs.setboolean("settings", "show_exit_prompt", b)
        self._configs.set("settings", "save_at_exit", f)
        self._configs.set("settings", "commit_at_exit", g)
        self._configs.setboolean("settings", "use_smooth_zoom", h)
        self._configs.setboolean("settings", "datetime", d)
        self._configs.setboolean("settings", "delete_data", delete_data)
        self._configs.set("settings", "gams_path", gams_path)
        self._configs.setboolean("settings", "use_repl", e)
        self._configs.set("settings", "julia_path", julia_path)
        # Update project settings
        self.update_project_settings()
        self._configs.save()
        self.close()

    def update_project_settings(self):
        """Update project settings when Ok has been clicked."""
        if not self._project:
            return
        save = False
        if not self.ui.lineEdit_work_dir.text():
            work_dir = DEFAULT_WORK_DIR
        else:
            work_dir = self.ui.lineEdit_work_dir.text()
        # Check if work directory was changed
        if not self.orig_work_dir == work_dir:
            if not self._project.change_work_dir(work_dir):
                self._toolbox.msg_error.emit("Could not change project work directory. Creating new dir:{0} failed "
                                             .format(work_dir))
            else:
                save = True
        if not self._project.description == self.ui.textEdit_project_description.toPlainText():
            # Set new project description
            self._project.set_description(self.ui.textEdit_project_description.toPlainText())
            save = True
        if save:
            self._toolbox.msg.emit("Project settings changed. Saving project...")
            self._toolbox.save_project()

    def keyPressEvent(self, e):
        """Close settings form when escape key is pressed.

        Args:
            e (QKeyEvent): Received key press event.
        """
        if e.key() == Qt.Key_Escape:
            self.close()

    def closeEvent(self, event=None):
        """Handle close window.

        Args:
            event (QEvent): Closing event if 'X' is clicked.
        """
        if event:
            event.accept()

    def mousePressEvent(self, e):
        """Save mouse position at the start of dragging.

        Args:
            e (QMouseEvent): Mouse event
        """
        self._mousePressPos = e.globalPos()
        self._mouseMovePos = e.globalPos()
        super().mousePressEvent(e)

    def mouseReleaseEvent(self, e):
        """Save mouse position at the end of dragging.

        Args:
            e (QMouseEvent): Mouse event
        """
        if self._mousePressPos is not None:
            self._mouseReleasePos = e.globalPos()
            moved = self._mouseReleasePos - self._mousePressPos
            if moved.manhattanLength() > 3:
                e.ignore()
                return

    def mouseMoveEvent(self, e):
        """Moves the window when mouse button is pressed and mouse cursor is moved.

        Args:
            e (QMouseEvent): Mouse event
        """
        # logging.debug("MouseMoveEvent at pos:%s" % e.pos())
        # logging.debug("MouseMoveEvent globalpos:%s" % e.globalPos())
        currentpos = self.pos()
        globalpos = e.globalPos()
        if not self._mouseMovePos:
            e.ignore()
            return
        diff = globalpos - self._mouseMovePos
        newpos = currentpos + diff
        self.move(newpos)
        self._mouseMovePos = globalpos
