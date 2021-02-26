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
Widget for controlling user settings.

:author: P. Savolainen (VTT)
:date:   17.1.2018
"""

import os
from PySide2.QtWidgets import QWidget, QFileDialog, QMessageBox, QColorDialog
from PySide2.QtCore import Slot, Qt, QSize
from PySide2.QtGui import QPixmap
from spine_engine.utils.helpers import resolve_julia_executable_from_path, resolve_python_executable_from_path
from .notification import Notification
from .julia_wizards import InstallJuliaWizard
from ..config import DEFAULT_WORK_DIR, SETTINGS_SS
from ..graphics_items import Link
from ..widgets.kernel_editor import KernelEditor, find_python_kernels, find_julia_kernels
from ..helpers import (
    select_python_interpreter,
    select_julia_executable,
    select_julia_project,
    file_is_valid,
    dir_is_valid,
)


class SettingsWidgetBase(QWidget):
    def __init__(self, qsettings):
        """
        Args:
            qsettings (QSettings): Toolbox settings
        """
        # FIXME: setting the parent to toolbox causes the checkboxes in the
        # groupBox_general to not layout correctly, this might be caused elsewhere?
        from ..ui.settings import Ui_SettingsForm  # pylint: disable=import-outside-toplevel

        super().__init__(parent=None)  # Do not set parent. Uses own stylesheet.
        # Set up the ui from Qt Designer files
        self._qsettings = qsettings
        self.ui = Ui_SettingsForm()
        self.ui.setupUi(self)
        self.setWindowFlags(Qt.Window | Qt.CustomizeWindowHint)
        self.setStyleSheet(SETTINGS_SS)
        self._mouse_press_pos = None
        self._mouse_release_pos = None
        self._mouse_move_pos = None

    def connect_signals(self):
        """Connect signals."""
        self.ui.buttonBox.accepted.connect(self.save_and_close)
        self.ui.buttonBox.rejected.connect(self.update_ui_and_close)

    def keyPressEvent(self, e):
        """Close settings form when escape key is pressed.

        Args:
            e (QKeyEvent): Received key press event.
        """
        if e.key() == Qt.Key_Escape:
            self.update_ui_and_close()

    def mousePressEvent(self, e):
        """Save mouse position at the start of dragging.

        Args:
            e (QMouseEvent): Mouse event
        """
        self._mouse_press_pos = e.globalPos()
        self._mouse_move_pos = e.globalPos()
        super().mousePressEvent(e)

    def mouseReleaseEvent(self, e):
        """Save mouse position at the end of dragging.

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

    def update_ui(self):
        """Updates UI to reflect current settings. Called when the user choses to cancel their changes.
        Undoes all temporary UI changes that resulted from the user playing with certain settings."""

    def save_settings(self):
        """Gets selections and saves them to persistent memory."""
        return True

    @Slot(bool)
    def update_ui_and_close(self, checked=False):
        """Updates UI to reflect current settings and close."""
        self.update_ui()
        self.close()

    @Slot(bool)
    def save_and_close(self, checked=False):
        """Saves settings and close."""
        if self.save_settings():
            self.close()


class SpineDBEditorSettingsMixin:
    def connect_signals(self):
        """Connect signals."""
        super().connect_signals()
        self.ui.checkBox_auto_expand_objects.clicked.connect(self.set_auto_expand_objects)

    def read_settings(self):
        """Read saved settings from app QSettings instance and update UI to display them."""
        commit_at_exit = int(self._qsettings.value("appSettings/commitAtExit", defaultValue="1"))  # tri-state
        sticky_selection = self._qsettings.value("appSettings/stickySelection", defaultValue="false")
        smooth_zoom = self._qsettings.value("appSettings/smoothEntityGraphZoom", defaultValue="false")
        smooth_rotation = self._qsettings.value("appSettings/smoothEntityGraphRotation", defaultValue="false")
        relationship_items_follow = self._qsettings.value("appSettings/relationshipItemsFollow", defaultValue="true")
        auto_expand_objects = self._qsettings.value("appSettings/autoExpandObjects", defaultValue="true")
        if commit_at_exit == 0:  # Not needed but makes the code more readable.
            self.ui.checkBox_commit_at_exit.setCheckState(Qt.Unchecked)
        elif commit_at_exit == 1:
            self.ui.checkBox_commit_at_exit.setCheckState(Qt.PartiallyChecked)
        else:  # commit_at_exit == "2":
            self.ui.checkBox_commit_at_exit.setCheckState(Qt.Checked)
        self.ui.checkBox_object_tree_sticky_selection.setChecked(sticky_selection == "true")
        self.ui.checkBox_smooth_entity_graph_zoom.setChecked(smooth_zoom == "true")
        self.ui.checkBox_smooth_entity_graph_rotation.setChecked(smooth_rotation == "true")
        self.ui.checkBox_relationship_items_follow.setChecked(relationship_items_follow == "true")
        self.ui.checkBox_auto_expand_objects.setChecked(auto_expand_objects == "true")

    def save_settings(self):
        """Get selections and save them to persistent memory."""
        if not super().save_settings():
            return False
        commit_at_exit = str(int(self.ui.checkBox_commit_at_exit.checkState()))
        self._qsettings.setValue("appSettings/commitAtExit", commit_at_exit)
        sticky_selection = "true" if int(self.ui.checkBox_object_tree_sticky_selection.checkState()) else "false"
        self._qsettings.setValue("appSettings/stickySelection", sticky_selection)
        smooth_zoom = "true" if int(self.ui.checkBox_smooth_entity_graph_zoom.checkState()) else "false"
        self._qsettings.setValue("appSettings/smoothEntityGraphZoom", smooth_zoom)
        smooth_rotation = "true" if int(self.ui.checkBox_smooth_entity_graph_rotation.checkState()) else "false"
        self._qsettings.setValue("appSettings/smoothEntityGraphRotation", smooth_rotation)
        relationship_items_follow = "true" if int(self.ui.checkBox_relationship_items_follow.checkState()) else "false"
        self._qsettings.setValue("appSettings/relationshipItemsFollow", relationship_items_follow)
        auto_expand_objects = "true" if int(self.ui.checkBox_auto_expand_objects.checkState()) else "false"
        self._qsettings.setValue("appSettings/autoExpandObjects", auto_expand_objects)
        return True

    def update_ui(self):
        super().update_ui()
        auto_expand_objects = self._qsettings.value("appSettings/autoExpandObjects", defaultValue="true") == "true"
        self.set_auto_expand_objects(auto_expand_objects)


class SpineDBEditorSettingsWidget(SpineDBEditorSettingsMixin, SettingsWidgetBase):
    """A widget to change user's preferred settings, but only for the Spine db editor.
    """

    def __init__(self, multi_db_editor):
        """Initialize class."""
        super().__init__(multi_db_editor.qsettings)
        self._multi_db_editor = multi_db_editor
        self.ui.stackedWidget.setCurrentWidget(self.ui.SpineDBEditor)
        self.ui.listWidget.hide()
        self.connect_signals()

    def show(self):
        super().show()
        self.read_settings()

    @Slot(bool)
    def set_auto_expand_objects(self, checked=False):
        for db_editor in self._multi_db_editor.db_mngr.get_all_spine_db_editors():
            db_editor.ui.graphicsView.set_auto_expand_objects(checked)


class SettingsWidget(SpineDBEditorSettingsMixin, SettingsWidgetBase):
    """A widget to change user's preferred settings."""

    def __init__(self, toolbox):
        """
        Args:
            toolbox (ToolboxUI): Parent widget.
        """
        super().__init__(toolbox.qsettings())
        self._toolbox = toolbox  # QWidget parent
        self._project = self._toolbox.project()
        self.orig_work_dir = ""  # Work dir when this widget was opened
        self._kernel_editor = None
        # Initial scene bg color. Is overridden immediately in read_settings() if it exists in qSettings
        self.bg_color = self._toolbox.ui.graphicsView.scene().bg_color
        for item in self.ui.listWidget.findItems("*", Qt.MatchWildcard):
            item.setSizeHint(QSize(128, 44))
        # Ensure this window gets garbage-collected when closed
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.connect_signals()
        self.read_settings()
        self.read_project_settings()

    def connect_signals(self):
        """Connect signals."""
        super().connect_signals()
        self.ui.toolButton_browse_gams.clicked.connect(self.browse_gams_path)
        self.ui.toolButton_browse_julia.clicked.connect(self.browse_julia_button_clicked)
        self.ui.toolButton_browse_julia_project.clicked.connect(self.browse_julia_project_button_clicked)
        self.ui.toolButton_browse_python.clicked.connect(self.browse_python_button_clicked)
        self.ui.pushButton_open_kernel_editor_python.clicked.connect(self.show_python_kernel_editor)
        self.ui.pushButton_open_kernel_editor_julia.clicked.connect(self.show_julia_kernel_editor)
        self.ui.toolButton_browse_work.clicked.connect(self.browse_work_path)
        self.ui.toolButton_bg_color.clicked.connect(self.show_color_dialog)
        self.ui.radioButton_bg_grid.clicked.connect(self.update_scene_bg)
        self.ui.radioButton_bg_tree.clicked.connect(self.update_scene_bg)
        self.ui.radioButton_bg_solid.clicked.connect(self.update_scene_bg)
        self.ui.checkBox_use_curved_links.clicked.connect(self.update_links_geometry)
        self.ui.radioButton_use_julia_executable.clicked.connect(self.toggle_julia_execution_mode)
        self.ui.radioButton_use_julia_console.clicked.connect(self.toggle_julia_execution_mode)
        self.ui.radioButton_use_python_interpreter.clicked.connect(self.toggle_python_execution_mode)
        self.ui.radioButton_use_python_console.clicked.connect(self.toggle_python_execution_mode)
        self.ui.pushButton_install_julia.clicked.connect(self._show_install_julia_wizard)

    def _show_install_julia_wizard(self):
        wizard = InstallJuliaWizard(self)
        wizard.julia_exe_selected.connect(self.ui.lineEdit_julia_path.setText)
        wizard.show()

    @Slot(bool)
    def set_auto_expand_objects(self, checked=False):
        for db_editor in self._toolbox.db_mngr.get_all_spine_db_editors():
            db_editor.ui.graphicsView.set_auto_expand_objects(checked)

    @Slot(bool)
    def browse_gams_path(self, checked=False):
        """Open file browser where user can select a GAMS program."""
        # noinspection PyCallByClass, PyArgumentList
        answer = QFileDialog.getOpenFileName(
            self, "Select GAMS Program (e.g. gams.exe on Windows)", os.path.abspath("C:\\")
        )
        if answer[0] == "":  # Canceled (american-english), cancelled (british-english)
            return
        # Check that it's not a directory
        if os.path.isdir(answer[0]):
            msg = "Please select a valid GAMS program (file) and not a directory"
            # noinspection PyCallByClass, PyArgumentList
            QMessageBox.warning(self, "Invalid GAMS Program", msg)
            return
        # Check that it's a file that actually exists
        if not os.path.exists(answer[0]):
            msg = "File {0} does not exist".format(answer[0])
            # noinspection PyCallByClass, PyArgumentList
            QMessageBox.warning(self, "Invalid GAMS Program", msg)
            return
        # Check that selected file at least starts with string 'gams'
        _, selected_file = os.path.split(answer[0])
        if not selected_file.lower().startswith("gams"):
            msg = "Selected file <b>{0}</b> may not be a valid GAMS program".format(selected_file)
            # noinspection PyCallByClass, PyArgumentList
            QMessageBox.warning(self, "Invalid GAMS Program", msg)
            return
        self.ui.lineEdit_gams_path.setText(answer[0])
        return

    @Slot(bool)
    def browse_julia_button_clicked(self, checked=False):
        """Calls static method that shows a file browser for selecting the Julia path."""
        select_julia_executable(self, self.ui.lineEdit_julia_path)

    @Slot(bool)
    def browse_julia_project_button_clicked(self, checked=False):
        """Calls static method that shows a file browser for selecting a Julia project."""
        select_julia_project(self, self.ui.lineEdit_julia_project_path)

    @Slot(bool)
    def browse_python_button_clicked(self, checked=False):
        """Calls static method that shows a file browser for selecting Python interpreter."""
        select_python_interpreter(self, self.ui.lineEdit_python_path)

    @Slot(bool)
    def show_python_kernel_editor(self, checked=False):
        """Opens kernel editor, where user can make a kernel for the Python Console."""
        p = self.ui.lineEdit_python_path.text()  # This may be an empty string
        j = self.ui.lineEdit_julia_path.text()
        current_kernel = self.ui.comboBox_python_kernel.currentText()
        self._kernel_editor = KernelEditor(self, p, j, "python", current_kernel)
        self._kernel_editor.finished.connect(self.python_kernel_editor_closed)
        self._kernel_editor.open()

    @Slot(int)
    def python_kernel_editor_closed(self, ret_code):
        """Catches the selected Python kernel name when the editor is closed."""
        previous_python_kernel = self.ui.comboBox_python_kernel.currentText()
        self.ui.comboBox_python_kernel.clear()
        python_kernel_cb_items = ["Select Python kernel spec..."] + [*find_python_kernels().keys()]
        self.ui.comboBox_python_kernel.addItems(python_kernel_cb_items)
        if ret_code != 1:  # Editor closed with something else than clicking Ok.
            # Set previous kernel selected in Python kernel combobox if it still exists
            python_kernel_index = self.ui.comboBox_python_kernel.findText(previous_python_kernel)
            if python_kernel_index == -1:
                self.ui.comboBox_python_kernel.setCurrentIndex(0)  # Previous not found
            else:
                self.ui.comboBox_python_kernel.setCurrentIndex(python_kernel_index)
            return
        new_kernel = self._kernel_editor.selected_kernel
        index = self.ui.comboBox_python_kernel.findText(new_kernel)
        if index == -1:  # New kernel not found, should be quite exceptional
            notification = Notification(self, f"Python kernel spec {new_kernel} not found")
            notification.show()
            self.ui.comboBox_python_kernel.setCurrentIndex(0)
        else:
            self.ui.comboBox_python_kernel.setCurrentIndex(index)

    @Slot(bool)
    def show_julia_kernel_editor(self, checked=False):
        """Opens kernel editor, where user can make a kernel the Julia Console."""
        p = self.ui.lineEdit_python_path.text()  # This may be an empty string
        j = self.ui.lineEdit_julia_path.text()
        current_kernel = self.ui.comboBox_julia_kernel.currentText()
        self._kernel_editor = KernelEditor(self, p, j, "julia", current_kernel)
        self._kernel_editor.finished.connect(self.julia_kernel_editor_closed)
        self._kernel_editor.open()

    @Slot(int)
    def julia_kernel_editor_closed(self, ret_code):
        """Catches the selected Julia kernel name when the editor is closed."""
        previous_julia_kernel = self.ui.comboBox_julia_kernel.currentText()
        self.ui.comboBox_julia_kernel.clear()
        julia_kernel_cb_items = ["Select Julia kernel spec..."] + [*find_julia_kernels().keys()]
        self.ui.comboBox_julia_kernel.addItems(julia_kernel_cb_items)
        if ret_code != 1:  # Editor closed with something else than clicking Ok.
            # Set previous kernel selected in combobox if it still exists
            previous_kernel_index = self.ui.comboBox_julia_kernel.findText(previous_julia_kernel)
            if previous_kernel_index == -1:
                self.ui.comboBox_julia_kernel.setCurrentIndex(0)
            else:
                self.ui.comboBox_julia_kernel.setCurrentIndex(previous_kernel_index)
            return
        new_kernel = self._kernel_editor.selected_kernel
        index = self.ui.comboBox_julia_kernel.findText(new_kernel)
        if index == -1:
            notification = Notification(self, f"Julia kernel spec {new_kernel} not found")
            notification.show()
            self.ui.comboBox_julia_kernel.setCurrentIndex(0)
        else:
            self.ui.comboBox_julia_kernel.setCurrentIndex(index)

    @Slot(bool)
    def browse_work_path(self, checked=False):
        """Open file browser where user can select the path to wanted work directory."""
        # noinspection PyCallByClass, PyTypeChecker, PyArgumentList
        answer = QFileDialog.getExistingDirectory(self, "Select Work Directory", os.path.abspath("C:\\"))
        if answer == '':  # Cancel button clicked
            return
        selected_path = os.path.abspath(answer)
        self.ui.lineEdit_work_dir.setText(selected_path)

    @Slot(bool)
    def show_color_dialog(self, checked=False):
        """Let user pick the bg color.

        Args:
            checked (boolean): Value emitted with clicked signal
        """
        # noinspection PyArgumentList
        color = QColorDialog.getColor(initial=self.bg_color)
        if not color.isValid():
            return  # Canceled
        self.bg_color = color
        self.update_bg_color()

    def update_bg_color(self):
        """Set tool button icon as the selected color and update
        Design View scene background color."""
        pixmap = QPixmap(16, 16)
        pixmap.fill(self.bg_color)
        self.ui.toolButton_bg_color.setIcon(pixmap)
        self._toolbox.ui.graphicsView.scene().set_bg_color(self.bg_color)
        self._toolbox.ui.graphicsView.scene().update()

    @Slot(bool)
    def update_scene_bg(self, checked=False):
        """Draw background on scene depending on radiobutton states.

        Args:
            checked (boolean): Toggle state
        """
        if self.ui.radioButton_bg_grid.isChecked():
            self._toolbox.ui.graphicsView.scene().set_bg_choice("grid")
        elif self.ui.radioButton_bg_tree.isChecked():
            self._toolbox.ui.graphicsView.scene().set_bg_choice("tree")
        elif self.ui.radioButton_bg_solid.isChecked():
            self._toolbox.ui.graphicsView.scene().set_bg_choice("solid")
        self._toolbox.ui.graphicsView.scene().update()

    @Slot(bool)
    def update_links_geometry(self, checked=False):
        for item in self._toolbox.ui.graphicsView.items():
            if isinstance(item, Link):
                item.update_geometry(curved_links=checked)

    @Slot(bool)
    def toggle_julia_execution_mode(self, checked=False):
        """Toggles between console and non-console Julia execution
        modes depending on radiobutton states.

        Args:
            checked (boolean): Toggle state
        """
        console_enabled = True
        if self.ui.radioButton_use_julia_executable.isChecked():
            console_enabled = False
        elif self.ui.radioButton_use_julia_console.isChecked():
            console_enabled = True
        self.ui.comboBox_julia_kernel.setEnabled(console_enabled)
        self.ui.lineEdit_julia_path.setEnabled(not console_enabled)
        self.ui.lineEdit_julia_project_path.setEnabled(not console_enabled)
        self.ui.toolButton_browse_julia.setEnabled(not console_enabled)
        self.ui.toolButton_browse_julia_project.setEnabled(not console_enabled)

    @Slot(bool)
    def toggle_python_execution_mode(self, checked=False):
        """Toggles between console and non-console Python execution
        modes depending on radiobutton states.

        Args:
            checked (boolean): Toggle state
        """
        console_enabled = True
        if self.ui.radioButton_use_python_interpreter.isChecked():
            console_enabled = False
        elif self.ui.radioButton_use_python_console.isChecked():
            console_enabled = True
        self.ui.comboBox_python_kernel.setEnabled(console_enabled)
        self.ui.lineEdit_python_path.setEnabled(not console_enabled)
        self.ui.toolButton_browse_python.setEnabled(not console_enabled)

    def read_settings(self):
        """Read saved settings from app QSettings instance and update UI to display them."""
        # checkBox check state 0: unchecked, 1: partially checked, 2: checked
        # QSettings value() method returns a str even if a boolean was stored
        super().read_settings()
        open_previous_project = int(self._qsettings.value("appSettings/openPreviousProject", defaultValue="0"))
        show_exit_prompt = int(self._qsettings.value("appSettings/showExitPrompt", defaultValue="2"))
        save_at_exit = int(self._qsettings.value("appSettings/saveAtExit", defaultValue="1"))  # tri-state
        datetime = int(self._qsettings.value("appSettings/dateTime", defaultValue="2"))
        delete_data = int(self._qsettings.value("appSettings/deleteData", defaultValue="0"))
        custom_open_project_dialog = self._qsettings.value("appSettings/customOpenProjectDialog", defaultValue="true")
        smooth_zoom = self._qsettings.value("appSettings/smoothZoom", defaultValue="false")
        curved_links = self._qsettings.value("appSettings/curvedLinks", defaultValue="false")
        data_flow_anim_dur = int(self._qsettings.value("appSettings/dataFlowAnimationDuration", defaultValue="100"))
        bg_choice = self._qsettings.value("appSettings/bgChoice", defaultValue="solid")
        bg_color = self._qsettings.value("appSettings/bgColor", defaultValue="false")
        gams_path = self._qsettings.value("appSettings/gamsPath", defaultValue="")
        use_embedded_julia = int(self._qsettings.value("appSettings/useEmbeddedJulia", defaultValue="2"))
        julia_path = self._qsettings.value("appSettings/juliaPath", defaultValue="")
        julia_project_path = self._qsettings.value("appSettings/juliaProjectPath", defaultValue="")
        julia_kernel = self._qsettings.value("appSettings/juliaKernel", defaultValue="")
        use_embedded_python = int(self._qsettings.value("appSettings/useEmbeddedPython", defaultValue="2"))
        python_path = self._qsettings.value("appSettings/pythonPath", defaultValue="")
        python_kernel = self._qsettings.value("appSettings/pythonKernel", defaultValue="")
        work_dir = self._qsettings.value("appSettings/workDir", defaultValue="")
        if open_previous_project == 2:
            self.ui.checkBox_open_previous_project.setCheckState(Qt.Checked)
        if show_exit_prompt == 2:
            self.ui.checkBox_exit_prompt.setCheckState(Qt.Checked)
        if save_at_exit == 0:  # Not needed but makes the code more readable.
            self.ui.checkBox_save_at_exit.setCheckState(Qt.Unchecked)
        elif save_at_exit == 1:
            self.ui.checkBox_save_at_exit.setCheckState(Qt.PartiallyChecked)
        else:  # save_at_exit == 2:
            self.ui.checkBox_save_at_exit.setCheckState(Qt.Checked)
        if datetime == 2:
            self.ui.checkBox_datetime.setCheckState(Qt.Checked)
        if delete_data == 2:
            self.ui.checkBox_delete_data.setCheckState(Qt.Checked)
        if custom_open_project_dialog == "true":
            self.ui.checkBox_custom_open_project_dialog.setCheckState(Qt.Checked)
        if smooth_zoom == "true":
            self.ui.checkBox_use_smooth_zoom.setCheckState(Qt.Checked)
        if curved_links == "true":
            self.ui.checkBox_use_curved_links.setCheckState(Qt.Checked)
        self.ui.horizontalSlider_data_flow_animation_duration.setValue(data_flow_anim_dur)
        if bg_choice == "grid":
            self.ui.radioButton_bg_grid.setChecked(True)
        elif bg_choice == "tree":
            self.ui.radioButton_bg_tree.setChecked(True)
        else:
            self.ui.radioButton_bg_solid.setChecked(True)
        if bg_color == "false":
            pass
        else:
            self.bg_color = bg_color
        self.update_bg_color()
        self.ui.lineEdit_gams_path.setText(gams_path)
        # Add Python and Julia kernels to comboBoxes
        julia_k_cb_items = ["Select Julia kernel spec..."] + [*find_julia_kernels().keys()]  # Unpack to list literal
        self.ui.comboBox_julia_kernel.addItems(julia_k_cb_items)
        python_k_cb_items = ["Select Python kernel spec..."] + [*find_python_kernels().keys()]
        self.ui.comboBox_python_kernel.addItems(python_k_cb_items)
        if use_embedded_julia == 2:
            self.ui.radioButton_use_julia_console.setChecked(True)
        else:
            self.ui.radioButton_use_python_interpreter.setChecked(True)
        self.toggle_julia_execution_mode()
        self.ui.lineEdit_julia_path.setPlaceholderText(resolve_julia_executable_from_path())
        self.ui.lineEdit_julia_path.setText(julia_path)
        self.ui.lineEdit_julia_project_path.setText(julia_project_path)
        ind = self.ui.comboBox_julia_kernel.findText(julia_kernel)
        if ind == -1:
            self.ui.comboBox_julia_kernel.setCurrentIndex(0)
        else:
            self.ui.comboBox_julia_kernel.setCurrentIndex(ind)
        if use_embedded_python == 2:
            self.ui.radioButton_use_python_console.setChecked(True)
        else:
            self.ui.radioButton_use_python_interpreter.setChecked(True)
        self.toggle_python_execution_mode()
        self.ui.lineEdit_python_path.setPlaceholderText(resolve_python_executable_from_path())
        self.ui.lineEdit_python_path.setText(python_path)
        ind = self.ui.comboBox_python_kernel.findText(python_kernel)
        if ind == -1:
            self.ui.comboBox_python_kernel.setCurrentIndex(0)
        else:
            self.ui.comboBox_python_kernel.setCurrentIndex(ind)
        self.ui.lineEdit_work_dir.setText(work_dir)
        self.orig_work_dir = work_dir

    def read_project_settings(self):
        """Get project name and description and update widgets accordingly."""
        if self._project:
            self.ui.lineEdit_project_name.setText(self._project.name)
            self.ui.textEdit_project_description.setText(self._project.description)
        else:
            # Disable project name and description line edits if no project open
            self.ui.lineEdit_project_name.setDisabled(True)
            self.ui.textEdit_project_description.setDisabled(True)

    @Slot()
    def save_settings(self):
        """Get selections and save them to persistent memory.
        Note: On Linux, True and False are saved as boolean values into QSettings.
        On Windows, booleans and integers are saved as strings. To make it consistent,
        we should use strings.
        """
        # checkBox check state 0: unchecked, 1: partially checked, 2: checked
        # checkBox check states are casted from integers to string because of Linux
        if not super().save_settings():
            return False
        open_prev_proj = str(int(self.ui.checkBox_open_previous_project.checkState()))
        self._qsettings.setValue("appSettings/openPreviousProject", open_prev_proj)
        exit_prompt = str(int(self.ui.checkBox_exit_prompt.checkState()))
        self._qsettings.setValue("appSettings/showExitPrompt", exit_prompt)
        save_at_exit = str(int(self.ui.checkBox_save_at_exit.checkState()))
        self._qsettings.setValue("appSettings/saveAtExit", save_at_exit)
        datetime = str(int(self.ui.checkBox_datetime.checkState()))
        self._qsettings.setValue("appSettings/dateTime", datetime)
        delete_data = str(int(self.ui.checkBox_delete_data.checkState()))
        self._qsettings.setValue("appSettings/deleteData", delete_data)
        custom_open_project_dial = "true" if int(self.ui.checkBox_custom_open_project_dialog.checkState()) else "false"
        self._qsettings.setValue("appSettings/customOpenProjectDialog", custom_open_project_dial)
        smooth_zoom = "true" if int(self.ui.checkBox_use_smooth_zoom.checkState()) else "false"
        self._qsettings.setValue("appSettings/smoothZoom", smooth_zoom)
        curved_links = "true" if int(self.ui.checkBox_use_curved_links.checkState()) else "false"
        self._qsettings.setValue("appSettings/curvedLinks", curved_links)
        data_flow_anim_dur = str(self.ui.horizontalSlider_data_flow_animation_duration.value())
        self._qsettings.setValue("appSettings/dataFlowAnimationDuration", data_flow_anim_dur)
        if self.ui.radioButton_bg_grid.isChecked():
            bg_choice = "grid"
        elif self.ui.radioButton_bg_tree.isChecked():
            bg_choice = "tree"
        else:
            bg_choice = "solid"
        self._qsettings.setValue("appSettings/bgChoice", bg_choice)
        self._qsettings.setValue("appSettings/bgColor", self.bg_color)
        # GAMS
        gams_path = self.ui.lineEdit_gams_path.text().strip()
        # Check gams_path is a file, it exists, and file name starts with 'gams'
        if not file_is_valid(self, gams_path, "Invalid GAMS Program", extra_check="gams"):
            return False
        self._qsettings.setValue("appSettings/gamsPath", gams_path)
        # Julia (str because Linux)
        use_emb_julia = "2" if self.ui.radioButton_use_julia_console.isChecked() else "0"
        self._qsettings.setValue("appSettings/useEmbeddedJulia", use_emb_julia)
        julia_path = self.ui.lineEdit_julia_path.text().strip()
        # Check julia_path is a file, it exists, and file name starts with 'julia'
        if not file_is_valid(self, julia_path, "Invalid Julia Executable", extra_check="julia"):
            return False
        self._qsettings.setValue("appSettings/juliaPath", julia_path)
        julia_project_path = self.ui.lineEdit_julia_project_path.text().strip()
        if not dir_is_valid(self, julia_project_path, "Invalid Julia Project"):  # Check it's a directory and it exists
            return False
        self._qsettings.setValue("appSettings/juliaProjectPath", julia_project_path)
        if self.ui.comboBox_julia_kernel.currentIndex() == 0:
            julia_kernel = ""
        else:
            julia_kernel = self.ui.comboBox_julia_kernel.currentText()
        self._qsettings.setValue("appSettings/juliaKernel", julia_kernel)
        # Python
        use_emb_python = "2" if self.ui.radioButton_use_python_console.isChecked() else "0"
        self._qsettings.setValue("appSettings/useEmbeddedPython", use_emb_python)
        python_path = self.ui.lineEdit_python_path.text().strip()
        # Check python_path is a file, it exists, and file name starts with 'python'
        if not file_is_valid(self, python_path, "Invalid Python Interpreter", extra_check="python"):
            return False
        self._qsettings.setValue("appSettings/pythonPath", python_path)
        if self.ui.comboBox_python_kernel.currentIndex() == 0:
            python_kernel = ""
        else:
            python_kernel = self.ui.comboBox_python_kernel.currentText()
        self._qsettings.setValue("appSettings/pythonKernel", python_kernel)
        # Work directory
        work_dir = self.ui.lineEdit_work_dir.text().strip()
        self.set_work_directory(work_dir)
        # Check if something in the app needs to be updated
        self._toolbox.show_datetime = self._toolbox.update_datetime()
        # Project
        self.update_project_settings()
        return True

    def update_project_settings(self):
        """Update project name and description if these have been changed."""
        if not self._project:
            return
        new_name = self.ui.lineEdit_project_name.text().strip()
        if self._project.name != new_name:
            # Change project name
            if new_name != "":
                self._project.call_set_name(new_name)
        if not self._project.description == self.ui.textEdit_project_description.toPlainText():
            # Set new project description
            self._project.call_set_description(self.ui.textEdit_project_description.toPlainText())

    def set_work_directory(self, new_work_dir):
        """Sets new work directory.

        Args:
            new_work_dir (str): Possibly a new work directory
        """
        if not new_work_dir:  # Happens when clearing the work dir line edit
            new_work_dir = DEFAULT_WORK_DIR
        if self.orig_work_dir != new_work_dir:
            self._toolbox.set_work_directory(new_work_dir)

    def update_ui(self):
        super().update_ui()
        curved_links = self._qsettings.value("appSettings/curvedLinks", defaultValue="false")
        bg_choice = self._qsettings.value("appSettings/bgChoice", defaultValue="solid")
        bg_color = self._qsettings.value("appSettings/bgColor", defaultValue="false")
        self.update_links_geometry(curved_links == "true")
        if bg_choice == "grid":
            self.ui.radioButton_bg_grid.setChecked(True)
        elif bg_choice == "tree":
            self.ui.radioButton_bg_tree.setChecked(True)
        else:
            self.ui.radioButton_bg_solid.setChecked(True)
        self.update_scene_bg()
        if bg_color == "false":
            pass
        else:
            self.bg_color = bg_color
        self.update_bg_color()
