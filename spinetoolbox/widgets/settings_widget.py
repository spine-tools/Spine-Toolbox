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

"""Widget for controlling user settings."""
import os
import subprocess
from PySide6.QtCore import QPoint, QSettings, QSize, Qt, Slot
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import QColorDialog, QMenu, QMessageBox, QWidget
from spine_engine.utils.helpers import (
    get_julia_env,
    resolve_conda_executable,
    resolve_current_python_interpreter,
    resolve_default_julia_executable,
    resolve_gams_executable,
)
from ..config import DEFAULT_WORK_DIR, SETTINGS_SS
from ..helpers import (
    dir_is_valid,
    file_is_valid,
    is_valid_conda_executable,
    open_url,
    select_certificate_directory,
    select_conda_executable,
    select_gams_executable,
    select_work_directory,
    select_file_path,
    select_dir,
    load_list_of_paths_from_qsettings,
    save_path_to_qsettings,
    get_current_item,
    get_current_item_data,
    path_in_list,
)
from ..link import JumpLink, Link
from ..project_item_icon import ProjectItemIcon
from ..spine_db_editor.editors import db_editor_registry
from ..widgets.kernel_editor import MiniJuliaKernelEditor, MiniPythonKernelEditor
from .add_up_spine_opt_wizard import AddUpSpineOptWizard
from .install_julia_wizard import InstallJuliaWizard
from .notification import Notification


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
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.CustomizeWindowHint)
        self.setStyleSheet(SETTINGS_SS)
        self._mouse_press_pos = None
        self._mouse_release_pos = None
        self._mouse_move_pos = None

    @property
    def qsettings(self):
        return self._qsettings

    def connect_signals(self):
        """Connect signals."""
        self.ui.buttonBox.accepted.connect(self.save_and_close)
        self.ui.buttonBox.rejected.connect(self.update_ui_and_close)

    def keyPressEvent(self, e):
        """Close settings form when escape key is pressed.

        Args:
            e (QKeyEvent): Received key press event.
        """
        if e.key() == Qt.Key.Key_Escape:
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

    @Slot()
    def update_ui_and_close(self):
        """Updates UI to reflect current settings and close."""
        self.update_ui()
        self.close()

    @Slot()
    def save_and_close(self):
        """Saves settings and close."""
        if self.save_settings():
            self.close()


class SpineDBEditorSettingsMixin:
    def connect_signals(self):
        """Connect signals."""
        super().connect_signals()
        self.ui.checkBox_hide_empty_classes.clicked.connect(self.set_hide_empty_classes)
        self.ui.checkBox_auto_expand_entities.clicked.connect(self.set_auto_expand_entities)
        self.ui.checkBox_merge_dbs.clicked.connect(self.set_merge_dbs)
        self.ui.checkBox_snap_entities.clicked.connect(self.set_snap_entities)
        self.ui.spinBox_max_ent_dim_count.valueChanged.connect(self.set_max_entity_dimension_count)
        self.ui.spinBox_layout_algo_max_iterations.valueChanged.connect(self.set_build_iters)
        self.ui.spinBox_layout_algo_spread_factor.valueChanged.connect(self.set_spread_factor)
        self.ui.spinBox_layout_algo_neg_weight_exp.valueChanged.connect(self.set_neg_weight_exp)

    def read_settings(self):
        """Read saved settings from app QSettings instance and update UI to display them."""
        commit_at_exit = int(self._qsettings.value("appSettings/commitAtExit", defaultValue="1"))  # tri-state
        sticky_selection = self._qsettings.value("appSettings/stickySelection", defaultValue="false")
        hide_empty_classes = self._qsettings.value("appSettings/hideEmptyClasses", defaultValue="false")
        smooth_zoom = self._qsettings.value("appSettings/smoothEntityGraphZoom", defaultValue="false")
        smooth_rotation = self._qsettings.value("appSettings/smoothEntityGraphRotation", defaultValue="false")
        auto_expand_entities = self._qsettings.value("appSettings/autoExpandEntities", defaultValue="true")
        snap_entities = self._qsettings.value("appSettings/snapEntities", defaultValue="false")
        merge_dbs = self._qsettings.value("appSettings/mergeDBs", defaultValue="true")
        db_editor_show_undo = int(self._qsettings.value("appSettings/dbEditorShowUndo", defaultValue="2"))
        max_ent_dim_count = int(self._qsettings.value("appSettings/maxEntityDimensionCount", defaultValue="5"))
        build_iters = int(self._qsettings.value("appSettings/layoutAlgoBuildIterations", defaultValue="12"))
        spread_factor = int(self._qsettings.value("appSettings/layoutAlgoSpreadFactor", defaultValue="100"))
        neg_weight_exp = int(self._qsettings.value("appSettings/layoutAlgoNegWeightExp", defaultValue="2"))
        if commit_at_exit == 0:  # Not needed but makes the code more readable.
            self.ui.checkBox_commit_at_exit.setCheckState(Qt.CheckState.Unchecked)
        elif commit_at_exit == 1:
            self.ui.checkBox_commit_at_exit.setCheckState(Qt.CheckState.PartiallyChecked)
        else:  # commit_at_exit == "2":
            self.ui.checkBox_commit_at_exit.setCheckState(Qt.CheckState.Checked)
        self.ui.checkBox_entity_tree_sticky_selection.setChecked(sticky_selection == "true")
        self.ui.checkBox_hide_empty_classes.setChecked(hide_empty_classes == "true")
        self.ui.checkBox_smooth_entity_graph_zoom.setChecked(smooth_zoom == "true")
        self.ui.checkBox_smooth_entity_graph_rotation.setChecked(smooth_rotation == "true")
        self.ui.checkBox_auto_expand_entities.setChecked(auto_expand_entities == "true")
        self.ui.checkBox_snap_entities.setChecked(snap_entities == "true")
        self.ui.checkBox_merge_dbs.setChecked(merge_dbs == "true")
        if db_editor_show_undo == 2:
            self.ui.checkBox_db_editor_show_undo.setChecked(True)
        self.ui.spinBox_max_ent_dim_count.setValue(max_ent_dim_count)
        self.ui.spinBox_layout_algo_max_iterations.setValue(build_iters)
        self.ui.spinBox_layout_algo_spread_factor.setValue(spread_factor)
        self.ui.spinBox_layout_algo_neg_weight_exp.setValue(neg_weight_exp)

    def save_settings(self):
        """Get selections and save them to persistent memory."""
        if not super().save_settings():
            return False
        commit_at_exit = str(self.ui.checkBox_commit_at_exit.checkState().value)
        self._qsettings.setValue("appSettings/commitAtExit", commit_at_exit)
        sticky_selection = "true" if self.ui.checkBox_entity_tree_sticky_selection.checkState().value else "false"
        self._qsettings.setValue("appSettings/stickySelection", sticky_selection)
        hide_empty_classes = "true" if self.ui.checkBox_hide_empty_classes.checkState().value else "false"
        self._qsettings.setValue("appSettings/hideEmptyClasses", hide_empty_classes)
        smooth_zoom = "true" if self.ui.checkBox_smooth_entity_graph_zoom.checkState().value else "false"
        self._qsettings.setValue("appSettings/smoothEntityGraphZoom", smooth_zoom)
        smooth_rotation = "true" if self.ui.checkBox_smooth_entity_graph_rotation.checkState().value else "false"
        self._qsettings.setValue("appSettings/smoothEntityGraphRotation", smooth_rotation)
        auto_expand_entities = "true" if self.ui.checkBox_auto_expand_entities.checkState().value else "false"
        self._qsettings.setValue("appSettings/autoExpandEntities", auto_expand_entities)
        snap_entities = "true" if self.ui.checkBox_snap_entities.checkState().value else "false"
        self._qsettings.setValue("appSettings/snapEntities", snap_entities)
        merge_dbs = "true" if self.ui.checkBox_merge_dbs.checkState().value else "false"
        self._qsettings.setValue("appSettings/mergeDBs", merge_dbs)
        db_editor_show_undo = str(self.ui.checkBox_db_editor_show_undo.checkState().value)
        self._qsettings.setValue("appSettings/dbEditorShowUndo", db_editor_show_undo)
        max_ent_dim_count = str(self.ui.spinBox_layout_algo_max_iterations.value())
        self._qsettings.setValue("appSettings/maxEntityDimensionCount", max_ent_dim_count)
        build_iters = str(self.ui.spinBox_layout_algo_max_iterations.value())
        self._qsettings.setValue("appSettings/layoutAlgoBuildIterations", build_iters)
        spread_factor = str(self.ui.spinBox_layout_algo_spread_factor.value())
        self._qsettings.setValue("appSettings/layoutAlgoSpreadFactor", spread_factor)
        neg_weight_exp = str(self.ui.spinBox_layout_algo_neg_weight_exp.value())
        self._qsettings.setValue("appSettings/layoutAlgoNegWeightExp", neg_weight_exp)
        return True

    def update_ui(self):
        super().update_ui()
        hide_empty_classes = self._qsettings.value("appSettings/hideEmptyClasses", defaultValue="false") == "true"
        auto_expand_entities = self._qsettings.value("appSettings/autoExpandEntities", defaultValue="true") == "true"
        merge_dbs = self._qsettings.value("appSettings/mergeDBs", defaultValue="true") == "true"
        self.set_hide_empty_classes(hide_empty_classes)
        self.set_auto_expand_entities(auto_expand_entities)
        self.set_merge_dbs(merge_dbs)

    @Slot(bool)
    def set_hide_empty_classes(self, checked=False):
        for db_editor in db_editor_registry.tabs():
            db_editor.entity_tree_model.hide_empty_classes = checked

    @Slot(bool)
    def set_auto_expand_entities(self, checked=False):
        self._set_graph_property("auto_expand_entities", checked)

    @Slot(bool)
    def set_merge_dbs(self, checked=False):
        self._set_graph_property("merge_dbs", checked)

    @Slot(bool)
    def set_snap_entities(self, checked=False):
        self._set_graph_property("snap_entities", checked)

    @Slot(int)
    def set_max_entity_dimension_count(self, value=None):
        self._set_graph_property("max_entity_dimension_count", value)

    @Slot(int)
    def set_build_iters(self, value=None):
        self._set_graph_property("build_iters", value)

    @Slot(int)
    def set_spread_factor(self, value=None):
        self._set_graph_property("spread_factor", value)

    @Slot(int)
    def set_neg_weight_exp(self, value=None):
        self._set_graph_property("neg_weight_exp", value)

    def _set_graph_property(self, name, value):
        for db_editor in db_editor_registry.tabs():
            db_editor.ui.graphicsView.set_property(name, value)


class SpineDBEditorSettingsWidget(SpineDBEditorSettingsMixin, SettingsWidgetBase):
    """A widget to change user's preferred settings, but only for the Spine db editor."""

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

    @property
    def db_mngr(self):
        return self._multi_db_editor.db_mngr


class SettingsWidget(SpineDBEditorSettingsMixin, SettingsWidgetBase):
    """A widget to change user's preferred settings."""

    def __init__(self, toolbox):
        """
        Args:
            toolbox (ToolboxUI): Parent widget.
        """
        super().__init__(toolbox.qsettings())
        self.ui.stackedWidget.setCurrentIndex(0)
        self.ui.listWidget.setFocus()
        self.ui.listWidget.setCurrentRow(0)
        self._toolbox = toolbox
        self._models = self._toolbox.exec_compound_models
        self.orig_work_dir = ""  # Work dir when this widget was opened
        self.ui.comboBox_julia_path.setModel(self._models.julia_executables_model)
        self.ui.comboBox_julia_project_path.setModel(self._models.julia_projects_model)
        self.ui.comboBox_julia_kernel.setModel(self._models.julia_kernel_model)
        self.ui.comboBox_python_interpreters.setModel(self._models.python_interpreters_model)
        self.ui.comboBox_python_kernels.setModel(self._models.python_kernel_model)
        self._saved_python_kernel = None
        self._saved_julia_kernel = None
        self._remote_host = ""
        # Initial scene bg color. Is overridden immediately in read_settings() if it exists in QSettings
        self.bg_color = self._toolbox.ui.graphicsView.scene().bg_color
        for item in self.ui.listWidget.findItems("*", Qt.MatchFlag.MatchWildcard):
            item.setSizeHint(QSize(128, 44))
        # Ensure this window gets garbage-collected when closed
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self.connect_signals()
        self.read_settings()
        self._update_python_widgets_enabled(self.ui.radioButton_use_python_jupyter_console.isChecked())
        self._update_julia_widgets_enabled(self.ui.radioButton_use_julia_jupyter_console.isChecked())
        self._update_remote_execution_page_widget_status(self.ui.checkBox_enable_remote_exec.isChecked())

    def connect_signals(self):
        """Connect signals."""
        super().connect_signals()
        self.ui.toolButton_reset_all_settings.clicked.connect(self._remove_all_settings)
        self.ui.toolButton_browse_gams.clicked.connect(self.browse_gams_button_clicked)
        self.ui.toolButton_browse_julia.clicked.connect(self._add_julia_executable)
        self.ui.toolButton_browse_julia_project.clicked.connect(self._add_julia_project)
        self.ui.toolButton_browse_python.clicked.connect(self._add_python_interpreter)
        self.ui.toolButton_browse_conda.clicked.connect(self.browse_conda_button_clicked)
        self.ui.toolButton_pick_secfolder.clicked.connect(self.browse_certificate_directory_clicked)
        self.ui.toolButton_make_python_kernel.clicked.connect(self.add_python_kernel)
        self.ui.toolButton_make_julia_kernel.clicked.connect(self.make_julia_kernel)
        self.ui.comboBox_julia_path.customContextMenuRequested.connect(self._show_julia_path_context_menu)
        self.ui.comboBox_julia_path.currentIndexChanged.connect(self._set_combobox_tooltip)
        self.ui.comboBox_julia_project_path.customContextMenuRequested.connect(self._show_julia_projects_context_menu)
        self.ui.comboBox_julia_project_path.currentIndexChanged.connect(self._set_combobox_tooltip)
        self.ui.comboBox_julia_kernel.customContextMenuRequested.connect(self._show_julia_kernel_context_menu)
        self.ui.comboBox_julia_kernel.currentIndexChanged.connect(self._set_combobox_tooltip)
        self.ui.comboBox_python_interpreters.customContextMenuRequested.connect(
            self._show_python_interpreters_context_menu
        )
        self.ui.comboBox_python_interpreters.currentIndexChanged.connect(self._set_combobox_tooltip)
        self.ui.comboBox_python_kernels.customContextMenuRequested.connect(self._show_python_kernel_context_menu)
        self.ui.comboBox_python_kernels.currentIndexChanged.connect(self._set_combobox_tooltip)
        self.ui.lineEdit_conda_path.textEdited.connect(self._refresh_python_kernels)
        self.ui.toolButton_browse_work.clicked.connect(self.browse_work_directory_button_clicked)
        self.ui.toolButton_bg_color.clicked.connect(self.show_color_dialog)
        self.ui.radioButton_bg_grid.clicked.connect(self.update_scene_bg)
        self.ui.radioButton_bg_tree.clicked.connect(self.update_scene_bg)
        self.ui.radioButton_bg_solid.clicked.connect(self.update_scene_bg)
        self.ui.checkBox_color_toolbar_icons.clicked.connect(self.set_toolbar_colored_icons)
        self.ui.checkBox_use_curved_links.clicked.connect(self.update_links_geometry)
        self.ui.checkBox_use_rounded_items.clicked.connect(self.update_items_path)
        self.ui.pushButton_install_julia.clicked.connect(self._show_install_julia_wizard)
        self.ui.pushButton_add_up_spine_opt.clicked.connect(self._show_add_up_spine_opt_wizard)
        self.ui.radioButton_use_python_jupyter_console.toggled.connect(self._update_python_widgets_enabled)
        self.ui.radioButton_use_julia_jupyter_console.toggled.connect(self._update_julia_widgets_enabled)
        self.ui.checkBox_enable_remote_exec.clicked.connect(self._update_remote_execution_page_widget_status)
        self.ui.lineEdit_host.textEdited.connect(self._edit_remote_host)
        self.ui.user_defined_engine_process_limit_radio_button.toggled.connect(
            self.ui.engine_process_limit_spin_box.setEnabled
        )
        self.ui.user_defined_persistent_process_limit_radio_button.toggled.connect(
            self.ui.persistent_process_limit_spin_box.setEnabled
        )

    @Slot(bool)
    def _update_python_widgets_enabled(self, state):
        """Enables or disables some widgets based on given boolean state."""
        self.ui.comboBox_python_kernels.setEnabled(state)
        self.ui.comboBox_python_interpreters.setEnabled(not state)

    @Slot(bool)
    def _update_julia_widgets_enabled(self, state):
        """Enables or disables some widgets based on given boolean state."""
        self.ui.comboBox_julia_kernel.setEnabled(state)
        self.ui.comboBox_julia_path.setEnabled(not state)
        self.ui.comboBox_julia_project_path.setEnabled(not state)

    @Slot(bool)
    def _update_remote_execution_page_widget_status(self, state):
        """Enables or disables widgets on Remote Execution page,
        based on the state of remote execution enabled check box."""
        self.ui.lineEdit_host.setEnabled(state)
        self.ui.spinBox_port.setEnabled(state)
        self.ui.comboBox_security.setEnabled(state)
        self.ui.lineEdit_secfolder.setEnabled(state)
        self.ui.toolButton_pick_secfolder.setEnabled(state)

    @Slot(bool)
    def _remove_all_settings(self, _=False):
        msg = (
            "Do you want to reset all settings to factory defaults? <b>Spine Toolbox will be shutdown</b> "
            "for the changes to take effect.<br/>Continue?"
        )
        box_title = "Close app and return to factory defaults?"
        box = QMessageBox(
            QMessageBox.Icon.Question,
            box_title,
            msg,
            buttons=QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel,
            parent=self,
        )
        box.button(QMessageBox.StandardButton.Ok).setText("Reset and Shutdown")
        answer = box.exec()
        if answer != QMessageBox.StandardButton.Ok:
            return
        self._toolbox.shutdown_and_clear_settings = True
        self.close()
        self._toolbox.close()

    @Slot(bool)
    def _show_install_julia_wizard(self, _=False):
        """Opens Install Julia Wizard."""
        wizard = InstallJuliaWizard(self)
        wizard.julia_exe_selected.connect(self.ui.comboBox_julia_path.setText)
        wizard.show()

    @Slot(bool)
    def _show_add_up_spine_opt_wizard(self, _=False):
        """Opens the add/update SpineOpt wizard."""
        use_julia_jupyter_console, julia_path, julia_project_path, julia_kernel = self._get_julia_settings()
        if julia_project_path != "@." and not dir_is_valid(
            self,
            julia_project_path,
            "Invalid Julia Project",
            "Julia project must be an existing directory, @., or empty",
        ):
            return
        use_jupyter_console = True if use_julia_jupyter_console == "2" else False
        julia_env = get_julia_env(use_jupyter_console, julia_kernel, julia_path, julia_project_path)
        if julia_env is None:
            julia_exe = julia_project = ""
        else:
            julia_exe, julia_project = julia_env
        wizard = AddUpSpineOptWizard(self, julia_exe, julia_project)
        wizard.show()

    @property
    def db_mngr(self):
        return self._toolbox.db_mngr

    @Slot(bool)
    def browse_work_directory_button_clicked(self, _=False):
        """Calls static method that shows a directory browser for selecting a Work directory."""
        select_work_directory(self, self.ui.lineEdit_work_dir)

    @Slot(bool)
    def browse_gams_button_clicked(self, _=False):
        """Calls static method that shows a file browser for selecting a Gams executable."""
        select_gams_executable(self, self.ui.lineEdit_gams_path)

    @Slot(bool)
    def browse_conda_button_clicked(self, _=False):
        """Calls static method that shows a file browser for selecting a Conda executable."""
        select_conda_executable(self, self.ui.lineEdit_conda_path)

    @Slot(bool)
    def browse_certificate_directory_clicked(self, _=False):
        """Calls static method that shows a file browser for selecting the security folder for Engine Server."""
        select_certificate_directory(self, self.ui.lineEdit_secfolder)

    @Slot(bool)
    def add_python_kernel(self, _=False):
        """Makes a Python kernel for Jupyter Console based on selected Python interpreter.
        If a kernel using this Python interpreter already exists, sets that kernel selected in the comboBox."""
        use_python_jupyter_console, python_exe, python_kernel = self._get_python_settings()
        # python_kernel_found = _get_python_kernel_name_by_exe(python_exe, self._models.python_kernel_model)
        # if not python_kernel_found:
        mpke = MiniPythonKernelEditor(self, self._models)
        mpke.exec()
        self._saved_python_kernel = python_kernel if not mpke.new_kernel_name() else mpke.new_kernel_name()
        activate_jupyter_kernel = True if mpke.new_kernel_name() else False
        self.ui.radioButton_use_python_jupyter_console.setChecked(activate_jupyter_kernel)
        self._models.refresh_python_interpreters_model()
        ind = self._models.find_python_interpreter_index(python_exe)
        self.ui.comboBox_python_interpreters.setCurrentIndex(ind.row())
        self._models.start_fetching_python_kernels(self._set_saved_python_kernel_selected)

    @Slot(bool)
    def make_julia_kernel(self, _=False):
        """Makes a Julia kernel for Jupyter Console based on selected Julia executable and Julia project.
        If a kernel using the selected Julia executable and project already exists, sets that kernel
        selected in the comboBox."""
        _, julia_exe, julia_project, julia_kernel = self._get_julia_settings()
        # Make new kernel or (possibly) overwrite existing one
        mjke = MiniJuliaKernelEditor(self, self._models)
        mjke.exec()
        self._saved_julia_kernel = julia_kernel if not mjke.new_kernel_name() else mjke.new_kernel_name()
        activate_jupyter_kernel = True if mjke.new_kernel_name() else False
        self.ui.radioButton_use_julia_jupyter_console.setChecked(activate_jupyter_kernel)
        self._models.refresh_julia_executables_model()
        self._models.refresh_julia_projects_model()
        ind = self._models.find_julia_executable_index(julia_exe)
        self.ui.comboBox_julia_path.setCurrentIndex(ind.row())
        index = self._models.find_julia_project_index(julia_project)
        self.ui.comboBox_julia_project_path.setCurrentIndex(index.row())
        self._models.start_fetching_julia_kernels(self._set_saved_julia_kernel_selected)

    @Slot(QPoint)
    def _show_julia_path_context_menu(self, pos):
        """Shows the context-menu on Julia executables combobox."""
        data = get_current_item_data(self.ui.comboBox_julia_path, self._models.julia_executables_model)
        global_pos = self.ui.comboBox_julia_path.mapToGlobal(pos)
        self._show_julia_context_menu(self.ui.comboBox_julia_path, global_pos, data)

    @Slot(QPoint)
    def _show_julia_projects_context_menu(self, pos):
        """Shows the context-menu on Julia projects combobox."""
        data = get_current_item_data(self.ui.comboBox_julia_project_path, self._models.julia_projects_model)
        global_pos = self.ui.comboBox_julia_project_path.mapToGlobal(pos)
        self._show_julia_context_menu(self.ui.comboBox_julia_project_path, global_pos, data)

    @Slot(QPoint)
    def _show_julia_kernel_context_menu(self, pos):
        """Shows the context-menu on Julia kernels combobox."""
        data = get_current_item_data(self.ui.comboBox_julia_kernel, self._models.julia_kernel_model)
        global_pos = self.ui.comboBox_julia_kernel.mapToGlobal(pos)
        self._show_julia_context_menu(self.ui.comboBox_julia_kernel, global_pos, data)

    def _show_julia_context_menu(self, menu_parent, global_pos, data):
        """Creates and shows the context menu for Julia comboBoxes."""
        if not data:
            return
        m = QMenu(menu_parent)
        if not data.get("is_jupyter", False):
            if not data.get("is_project", False):
                m.addAction(QIcon(":icons/menu_icons/trash-alt.svg"), "Remove from list", self._remove_julia_executable)
                m.addAction(QIcon(":icons/menu_icons/folder-open-solid.svg"), "Open containing folder...", self._open_julia_executable_dir)
            else:
                m.addAction(QIcon(":icons/menu_icons/trash-alt.svg"), "Remove from list", self._remove_julia_project)
                m.addAction(QIcon(":icons/menu_icons/folder-open-solid.svg"), "Open folder...", self._open_julia_project_dir)
        else:
            m.addAction(QIcon(":icons/menu_icons/folder-open-solid.svg"), "Open resource folder...", self._open_julia_kernel_resource_dir)
        m.popup(global_pos)

    @Slot(QPoint)
    def _show_python_interpreters_context_menu(self, pos):
        data = get_current_item_data(self.ui.comboBox_python_interpreters, self._models.python_interpreters_model)
        global_pos = self.ui.comboBox_python_interpreters.mapToGlobal(pos)
        self._show_python_context_menu(self.ui.comboBox_python_interpreters, global_pos, data)

    @Slot(QPoint)
    def _show_python_kernel_context_menu(self, pos):
        data = get_current_item_data(self.ui.comboBox_python_kernels, self._models.python_kernel_model)
        global_pos = self.ui.comboBox_python_kernels.mapToGlobal(pos)
        self._show_python_context_menu(self.ui.comboBox_python_kernels, global_pos, data)

    def _show_python_context_menu(self, menu_parent, global_pos, data):
        """Creates and shows the context menu for both python interpreters and kernels comboBoxes."""
        if not data:
            return
        m = QMenu(menu_parent)
        if not data["is_jupyter"]:
            m.addAction(QIcon(":icons/menu_icons/trash-alt.svg"), "Remove from list", self._remove_python_system_interpreter)
            m.addAction(QIcon(":icons/menu_icons/folder-open-solid.svg"), "Open containing folder...", self._open_python_interpreter_dir)
        else:
            m.addAction(QIcon(":icons/menu_icons/folder-open-solid.svg"), "Open resource folder...", self._open_python_kernel_resource_dir)
        m.popup(global_pos)

    @Slot(int)
    def _set_combobox_tooltip(self, row):
        """Sets the current items tooltip as the combobox tooltip."""
        if row == -1:
            return
        model = self.sender().model()
        tp = model.itemFromIndex(model.index(row, 0)).toolTip()
        self.sender().setToolTip(tp)

    @Slot(bool)
    def show_color_dialog(self, _=False):
        """Lets user pick the background color from a color dialog."""
        # noinspection PyArgumentList
        color = QColorDialog.getColor(initial=self.bg_color)
        if not color.isValid():
            return  # Canceled
        self.bg_color = color
        self.update_bg_color()

    def update_bg_color(self):
        """Set tool button icon as the selected color and update Design View scene background color."""
        pixmap = QPixmap(16, 16)
        pixmap.fill(self.bg_color)
        self.ui.toolButton_bg_color.setIcon(pixmap)
        self._toolbox.ui.graphicsView.scene().set_bg_color(self.bg_color)
        self._toolbox.ui.graphicsView.scene().update()

    @Slot(bool)
    def update_scene_bg(self, _=False):
        """Draw background on scene depending on radiobutton states."""
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
            if isinstance(item, (Link, JumpLink)):
                item.update_geometry(curved_links=checked)

    @Slot(bool)
    def update_items_path(self, checked=False):
        for item in self._toolbox.ui.graphicsView.items():
            if isinstance(item, ProjectItemIcon):
                item.update_path(checked)

    @Slot(bool)
    def set_toolbar_colored_icons(self, checked=False):
        self._toolbox.set_toolbar_colored_icons(checked)

    @Slot(bool)
    def _update_properties_widget(self, _checked=False):
        self._toolbox.ui.tabWidget_item_properties.update()

    def read_settings(self):
        """Reads saved settings from app QSettings instance and updates UI to display them."""
        # checkBox check state 0: unchecked, 1: partially checked, 2: checked
        # QSettings value() method returns a str even if a boolean was stored
        super().read_settings()
        open_previous_project = int(self._qsettings.value("appSettings/openPreviousProject", defaultValue="0"))
        show_exit_prompt = int(self._qsettings.value("appSettings/showExitPrompt", defaultValue="2"))
        save_at_exit = self._qsettings.value("appSettings/saveAtExit", defaultValue="prompt")
        datetime = int(self._qsettings.value("appSettings/dateTime", defaultValue="2"))
        delete_data = int(self._qsettings.value("appSettings/deleteData", defaultValue="0"))
        custom_open_project_dialog = self._qsettings.value("appSettings/customOpenProjectDialog", defaultValue="true")
        smooth_zoom = self._qsettings.value("appSettings/smoothZoom", defaultValue="false")
        color_toolbar_icons = self._qsettings.value("appSettings/colorToolbarIcons", defaultValue="false")
        color_properties_widgets = self._qsettings.value("appSettings/colorPropertiesWidgets", defaultValue="false")
        curved_links = self._qsettings.value("appSettings/curvedLinks", defaultValue="false")
        drag_to_draw_links = self._qsettings.value("appSettings/dragToDrawLinks", defaultValue="false")
        rounded_items = self._qsettings.value("appSettings/roundedItems", defaultValue="false")
        prevent_overlapping = self._qsettings.value("appSettings/preventOverlapping", defaultValue="false")
        data_flow_anim_dur = int(self._qsettings.value("appSettings/dataFlowAnimationDuration", defaultValue="100"))
        bg_choice = self._qsettings.value("appSettings/bgChoice", defaultValue="solid")
        bg_color = self._qsettings.value("appSettings/bgColor", defaultValue="false")
        gams_path = self._qsettings.value("appSettings/gamsPath", defaultValue="")
        use_julia_jupyter_console = self._qsettings.value("appSettings/useJuliaKernel", defaultValue="0")
        julia_path = self._qsettings.value("appSettings/juliaPath", defaultValue="")
        julia_project_path = self._qsettings.value("appSettings/juliaProjectPath", defaultValue="")
        julia_kernel = self._qsettings.value("appSettings/juliaKernel", defaultValue="")
        julia_executables = load_list_of_paths_from_qsettings(self._qsettings, "appSettings/juliaExecutables")
        julia_projects = load_list_of_paths_from_qsettings(self._qsettings, "appSettings/juliaProjects")
        use_python_jupyter_console = self._qsettings.value("appSettings/usePythonKernel", defaultValue="0")
        python_path = self._qsettings.value("appSettings/pythonPath", defaultValue="")
        python_kernel = self._qsettings.value("appSettings/pythonKernel", defaultValue="")
        python_interpreters = load_list_of_paths_from_qsettings(self._qsettings, "appSettings/pythonInterpreters")
        conda_path = self._qsettings.value("appSettings/condaPath", defaultValue="")
        work_dir = self._qsettings.value("appSettings/workDir", defaultValue="")
        save_spec = int(self._qsettings.value("appSettings/saveSpecBeforeClosing", defaultValue="1"))  # tri-state
        spec_show_undo = int(self._qsettings.value("appSettings/specShowUndo", defaultValue="2"))
        if open_previous_project == 2:
            self.ui.checkBox_open_previous_project.setCheckState(Qt.CheckState.Checked)
        if show_exit_prompt == 2:
            self.ui.checkBox_exit_prompt.setCheckState(Qt.CheckState.Checked)
        self.ui.project_save_options_combo_box.setCurrentIndex({"prompt": 0, "automatic": 1}[save_at_exit])
        if datetime == 2:
            self.ui.checkBox_datetime.setCheckState(Qt.CheckState.Checked)
        if delete_data == 2:
            self.ui.checkBox_delete_data.setCheckState(Qt.CheckState.Checked)
        if custom_open_project_dialog == "true":
            self.ui.checkBox_custom_open_project_dialog.setCheckState(Qt.CheckState.Checked)
        if smooth_zoom == "true":
            self.ui.checkBox_use_smooth_zoom.setCheckState(Qt.CheckState.Checked)
        if color_toolbar_icons == "true":
            self.ui.checkBox_color_toolbar_icons.setCheckState(Qt.CheckState.Checked)
        if color_properties_widgets == "true":
            self.ui.checkBox_color_properties_widgets.setCheckState(Qt.CheckState.Checked)
        if curved_links == "true":
            self.ui.checkBox_use_curved_links.setCheckState(Qt.CheckState.Checked)
        if drag_to_draw_links == "true":
            self.ui.checkBox_drag_to_draw_links.setCheckState(Qt.CheckState.Checked)
        if rounded_items == "true":
            self.ui.checkBox_use_rounded_items.setCheckState(Qt.CheckState.Checked)
        self.ui.horizontalSlider_data_flow_animation_duration.setValue(data_flow_anim_dur)
        if prevent_overlapping == "true":
            self.ui.checkBox_prevent_overlapping.setCheckState(Qt.CheckState.Checked)
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
        self.ui.lineEdit_gams_path.setPlaceholderText(resolve_gams_executable(""))
        self.ui.lineEdit_gams_path.setText(gams_path)
        # Below lines ensure that the pythonPath interpreter is inserted into the pythonInterpreters list
        # I.e. it is for upgrading users settings to use the new keys.
        if not path_in_list(python_path, python_interpreters):
            python_interpreters = save_path_to_qsettings(self._qsettings, "appSettings/pythonInterpreters", str(python_path))
        if not path_in_list(julia_path, julia_executables):
            julia_executables = save_path_to_qsettings(self._qsettings, "appSettings/juliaExecutables", str(julia_path))
        if not path_in_list(julia_project_path, julia_projects) and not julia_project_path == "@.":
            julia_projects = save_path_to_qsettings(self._qsettings, "appSettings/juliaProjects", str(julia_project_path))
        if use_python_jupyter_console == "0":
            self.ui.radioButton_use_python_basic_console.setChecked(True)
        else:
            self.ui.radioButton_use_python_jupyter_console.setChecked(True)
        self._models.refresh_python_interpreters_model(python_interpreters)
        python_ind = self._models.find_python_interpreter_index(python_path)
        self.ui.comboBox_python_interpreters.setCurrentIndex(python_ind.row())
        # _saved_python_kernel is used to select the correct Python after all kernels have been loaded
        self._saved_python_kernel = python_kernel
        # Fetch Python jupyter and conda kernels
        self._models.start_fetching_python_kernels(self._set_saved_python_kernel_selected)
        if use_julia_jupyter_console == "0":
            self.ui.radioButton_use_julia_basic_console.setChecked(True)
        else:
            self.ui.radioButton_use_julia_jupyter_console.setChecked(True)
        self._models.refresh_julia_executables_model(julia_executables)
        julia_ind = self._models.find_julia_executable_index(julia_path)
        self.ui.comboBox_julia_path.setCurrentIndex(julia_ind.row())
        self._models.refresh_julia_projects_model(julia_projects)
        project_ind = self._models.find_julia_project_index(julia_project_path)
        self.ui.comboBox_julia_project_path.setCurrentIndex(project_ind.row())
        # _saved_julia_kernel is used to select the correct Julia after all kernels have been loaded
        self._saved_julia_kernel = julia_kernel
        # Fetch Julia jupyter and conda kernels
        self._models.start_fetching_julia_kernels(self._set_saved_julia_kernel_selected)
        conda_placeholder_txt = resolve_conda_executable("")
        if conda_placeholder_txt:
            self.ui.lineEdit_conda_path.setPlaceholderText(conda_placeholder_txt)
        self.ui.lineEdit_conda_path.setText(conda_path)
        if os.path.normpath(work_dir) != os.path.normpath(DEFAULT_WORK_DIR):
            self.ui.lineEdit_work_dir.setText(work_dir)
        self.ui.lineEdit_work_dir.setPlaceholderText(DEFAULT_WORK_DIR)
        self.orig_work_dir = work_dir
        if save_spec == 0:
            self.ui.checkBox_save_spec_before_closing.setCheckState(Qt.CheckState.Unchecked)
        elif save_spec == 1:
            self.ui.checkBox_save_spec_before_closing.setCheckState(Qt.CheckState.PartiallyChecked)
        else:  # save_spec == 2:
            self.ui.checkBox_save_spec_before_closing.setCheckState(Qt.CheckState.Checked)
        if spec_show_undo == 2:
            self.ui.checkBox_spec_show_undo.setChecked(True)
        self._read_engine_settings()

    def _read_engine_settings(self):
        """Reads Engine settings and sets the corresponding UI elements."""
        # Remote execution settings
        enable_remote_exec = self._qsettings.value("engineSettings/remoteExecutionEnabled", defaultValue="false")
        if enable_remote_exec == "true":
            self.ui.checkBox_enable_remote_exec.setCheckState(Qt.CheckState.Checked)
        remote_host = self._qsettings.value("engineSettings/remoteHost", defaultValue="")
        self._edit_remote_host(remote_host)
        remote_port = int(self._qsettings.value("engineSettings/remotePort", defaultValue="49152"))
        self.ui.spinBox_port.setValue(remote_port)
        security = self._qsettings.value("engineSettings/remoteSecurityModel", defaultValue="")
        if not security:
            self.ui.comboBox_security.setCurrentIndex(0)
        else:
            self.ui.comboBox_security.setCurrentIndex(1)
        sec_folder = self._qsettings.value("engineSettings/remoteSecurityFolder", defaultValue="")
        self.ui.lineEdit_secfolder.setText(sec_folder)
        # Parallel process limits
        process_limiter = self._qsettings.value("engineSettings/processLimiter", defaultValue="unlimited")
        if process_limiter == "unlimited":
            self.ui.unlimited_engine_process_radio_button.setChecked(True)
        elif process_limiter == "auto":
            self.ui.automatic_engine_process_limit_radio_button.setChecked(True)
        else:
            self.ui.user_defined_engine_process_limit_radio_button.setChecked(True)
        process_limit = int(self._qsettings.value("engineSettings/maxProcesses", defaultValue=os.cpu_count()))
        self.ui.engine_process_limit_spin_box.setValue(process_limit)
        persistent_limiter = self._qsettings.value("engineSettings/persistentLimiter", defaultValue="unlimited")
        if persistent_limiter == "unlimited":
            self.ui.unlimited_persistent_process_radio_button.setChecked(True)
        elif persistent_limiter == "auto":
            self.ui.automatic_persistent_process_limit_radio_button.setChecked(True)
        else:
            self.ui.user_defined_persistent_process_limit_radio_button.setChecked(True)
        persistent_process_limit = int(
            self._qsettings.value("engineSettings/maxPersistentProcesses", defaultValue=os.cpu_count())
        )
        self.ui.persistent_process_limit_spin_box.setValue(persistent_process_limit)

    @Slot()
    def save_settings(self):
        """Get selections and save them to persistent memory.
        Note: On Linux, True and False are saved as boolean values into QSettings.
        On Windows, booleans and integers are saved as strings. To make it consistent,
        we should use strings.
        """
        # checkBox check state 0: unchecked, 1: partially checked, 2: checked
        # checkBox check states are cast from integers to string for consistency
        if not super().save_settings():
            return False
        open_prev_proj = str(self.ui.checkBox_open_previous_project.checkState().value)
        self._qsettings.setValue("appSettings/openPreviousProject", open_prev_proj)
        exit_prompt = str(self.ui.checkBox_exit_prompt.checkState().value)
        self._qsettings.setValue("appSettings/showExitPrompt", exit_prompt)
        save_at_exit = {0: "prompt", 1: "automatic"}[self.ui.project_save_options_combo_box.currentIndex()]
        self._qsettings.setValue("appSettings/saveAtExit", save_at_exit)
        datetime = str(self.ui.checkBox_datetime.checkState().value)
        self._qsettings.setValue("appSettings/dateTime", datetime)
        delete_data = str(self.ui.checkBox_delete_data.checkState().value)
        self._qsettings.setValue("appSettings/deleteData", delete_data)
        custom_open_project_dial = "true" if self.ui.checkBox_custom_open_project_dialog.checkState().value else "false"
        self._qsettings.setValue("appSettings/customOpenProjectDialog", custom_open_project_dial)
        smooth_zoom = "true" if self.ui.checkBox_use_smooth_zoom.checkState().value else "false"
        self._qsettings.setValue("appSettings/smoothZoom", smooth_zoom)
        color_toolbar_icons = "true" if self.ui.checkBox_color_toolbar_icons.checkState().value else "false"
        self._qsettings.setValue("appSettings/colorToolbarIcons", color_toolbar_icons)
        color_properties_widgets = "true" if self.ui.checkBox_color_properties_widgets.checkState().value else "false"
        self._qsettings.setValue("appSettings/colorPropertiesWidgets", color_properties_widgets)
        curved_links = "true" if self.ui.checkBox_use_curved_links.checkState().value else "false"
        self._qsettings.setValue("appSettings/curvedLinks", curved_links)
        drag_to_draw_links = "true" if self.ui.checkBox_drag_to_draw_links.checkState().value else "false"
        self._qsettings.setValue("appSettings/dragToDrawLinks", drag_to_draw_links)
        rounded_items = "true" if self.ui.checkBox_use_rounded_items.checkState().value else "false"
        self._qsettings.setValue("appSettings/roundedItems", rounded_items)
        prevent_overlapping = "true" if self.ui.checkBox_prevent_overlapping.checkState().value else "false"
        self._qsettings.setValue("appSettings/preventOverlapping", prevent_overlapping)
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
        save_spec = str(self.ui.checkBox_save_spec_before_closing.checkState().value)
        self._qsettings.setValue("appSettings/saveSpecBeforeClosing", save_spec)
        spec_show_undo = str(self.ui.checkBox_spec_show_undo.checkState().value)
        self._qsettings.setValue("appSettings/specShowUndo", spec_show_undo)
        # GAMS
        gams_path = self.ui.lineEdit_gams_path.text().strip()
        # Check gams_path is a file, it exists, and file name starts with 'gams'
        if not file_is_valid(self, gams_path, "Invalid GAMS Program", extra_check="gams"):
            return False
        self._qsettings.setValue("appSettings/gamsPath", gams_path)
        # Julia
        use_julia_jupyter_console, julia_exe, julia_project, julia_kernel = self._get_julia_settings()
        print(f"[{use_julia_jupyter_console}] julia exe:{julia_exe}, julia project:{julia_project}, kernel:{julia_kernel}")
        if use_julia_jupyter_console == "2" and not julia_kernel:
            msg = (
                "You have selected <b>Use Jupyter kernel</b> for Julia Tools "
                "but you did not select a kernel, please select a <b>Jupyter "
                "kernel</b> from the dropdown menu or select <b>Use Julia "
                "executable / Julia project</b>"
            )
            box = QMessageBox(QMessageBox.Icon.Warning, "No Julia kernel selected", msg, parent=self)
            box.setWindowIcon(QIcon(":/symbols/app.ico"))
            box.exec()
            return False
        self._qsettings.setValue("appSettings/useJuliaKernel", use_julia_jupyter_console)
        # Check julia_path is a file, it exists, and file name starts with 'julia'
        if not file_is_valid(self, julia_exe, "Invalid Julia Executable", extra_check="julia"):
            return False
        self._qsettings.setValue("appSettings/juliaPath", julia_exe)
        # Check julia project is a directory and it exists
        if julia_project != "@." and not dir_is_valid(self, julia_project, "Invalid Julia Project"):
            return False
        self._qsettings.setValue("appSettings/juliaProjectPath", julia_project)
        self._qsettings.setValue("appSettings/juliaKernel", julia_kernel)
        # Python
        use_python_jupyter_console, python_exe, python_kernel = self._get_python_settings()
        print(f"[{use_python_jupyter_console}] python exe:{python_exe}, kernel:{python_kernel}")
        if use_python_jupyter_console == "2" and not python_kernel:
            msg = (
                "You have selected <b>Use Jupyter kernel</b> for Python Tools "
                "but you did not select a kernel, please select a <b>Jupyter "
                "kernel</b> from the dropdown menu or select <b>Use system or "
                "virtualenv Python interpreter</b>"
            )
            box = QMessageBox(QMessageBox.Icon.Warning, "No Python kernel selected", msg, parent=self)
            box.setWindowIcon(QIcon(":/symbols/app.ico"))
            box.exec()
            return False
        self._qsettings.setValue("appSettings/usePythonKernel", use_python_jupyter_console)
        # Check python_path is a file, it exists, and file name starts with 'python'
        if not file_is_valid(self, python_exe, "Invalid Python Interpreter", extra_check="python"):
            return False
        self._qsettings.setValue("appSettings/pythonPath", python_exe)
        self._qsettings.setValue("appSettings/pythonKernel", python_kernel)
        # Conda
        conda_exe = self.ui.lineEdit_conda_path.text().strip()
        if not is_valid_conda_executable(conda_exe):
            conda_exe = ""
        self._qsettings.setValue("appSettings/condaPath", conda_exe)
        # Work directory
        work_dir = self.ui.lineEdit_work_dir.text().strip()
        self.set_work_directory(work_dir)
        # Check if something in the app needs to be updated
        self._toolbox.show_datetime = self._toolbox.update_datetime()
        if not self._save_engine_settings():
            return False
        return True

    def _save_engine_settings(self):
        """Stores Engine settings to application settings.

        Returns:
            bool: True if settings were stored successfully, False otherwise
        """
        # Remote execution settings
        remote_exec = "true" if self.ui.checkBox_enable_remote_exec.checkState().value else "false"
        self._qsettings.setValue("engineSettings/remoteExecutionEnabled", remote_exec)
        self._qsettings.setValue("engineSettings/remoteHost", self._remote_host)
        self._qsettings.setValue("engineSettings/remotePort", self.ui.spinBox_port.value())
        if self.ui.comboBox_security.currentIndex() == 0:
            sec_str = ""
        else:
            sec_str = self.ui.comboBox_security.currentText()
        self._qsettings.setValue("engineSettings/remoteSecurityModel", sec_str)
        self._qsettings.setValue("engineSettings/remoteSecurityFolder", self.ui.lineEdit_secfolder.text())
        # Parallel process limits
        if self.ui.unlimited_engine_process_radio_button.isChecked():
            limiter = "unlimited"
        elif self.ui.automatic_engine_process_limit_radio_button.isChecked():
            limiter = "auto"
        else:
            limiter = "user"
        self._qsettings.setValue("engineSettings/processLimiter", limiter)
        self._qsettings.setValue("engineSettings/maxProcesses", str(self.ui.engine_process_limit_spin_box.value()))
        if self.ui.unlimited_persistent_process_radio_button.isChecked():
            limiter = "unlimited"
        elif self.ui.automatic_persistent_process_limit_radio_button.isChecked():
            limiter = "auto"
        else:
            limiter = "user"
        self._qsettings.setValue("engineSettings/persistentLimiter", limiter)
        self._qsettings.setValue(
            "engineSettings/maxPersistentProcesses", str(self.ui.persistent_process_limit_spin_box.value())
        )
        return True

    def _get_julia_settings(self):
        """Returns current Julia settings on Settings->Tools page."""
        use_julia_jupyter_console = "2" if self.ui.radioButton_use_julia_jupyter_console.isChecked() else "0"
        data = get_current_item_data(self.ui.comboBox_julia_path, self._models.julia_executables_model)
        if not data:
            julia_exe = ""
        else:
            julia_exe = data["exe"]
        project_data = get_current_item_data(self.ui.comboBox_julia_project_path, self._models.julia_projects_model)
        julia_project = project_data["path"]
        julia_kernel = ""
        if self.ui.comboBox_julia_kernel.currentIndex() != 0:
            kernel_data = get_current_item_data(self.ui.comboBox_julia_kernel, self._models.julia_kernel_model)
            julia_kernel = kernel_data["kernel_name"]
        return use_julia_jupyter_console, julia_exe, julia_project, julia_kernel

    def _get_python_settings(self):
        """Returns current Python settings on Settings->Tools page."""
        use_python_jupyter_console = "2" if self.ui.radioButton_use_python_jupyter_console.isChecked() else "0"
        data = get_current_item_data(self.ui.comboBox_python_interpreters, self._models.python_interpreters_model)
        python_exe = data["exe"]
        python_kernel = ""
        if self.ui.comboBox_python_kernels.currentIndex() != 0:
            kernel_data = get_current_item_data(self.ui.comboBox_python_kernels, self._models.python_kernel_model)
            try:
                python_kernel = kernel_data["kernel_name"]
            except KeyError:  # Happens when conda kernel is selected and user clears the conda line edit path
                python_kernel = ""
        return use_python_jupyter_console, python_exe, python_kernel

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
        rounded_items = self._qsettings.value("appSettings/roundedItems", defaultValue="false")
        bg_choice = self._qsettings.value("appSettings/bgChoice", defaultValue="solid")
        bg_color = self._qsettings.value("appSettings/bgColor", defaultValue="false")
        color_toolbar_icons = self._qsettings.value("appSettings/colorToolbarIcons", defaultValue="false")
        self.set_toolbar_colored_icons(color_toolbar_icons == "true")
        self.update_links_geometry(curved_links == "true")
        self.update_items_path(rounded_items == "true")
        if bg_choice == "grid":
            self.ui.radioButton_bg_grid.setChecked(True)
        elif bg_choice == "tree":
            self.ui.radioButton_bg_tree.setChecked(True)
        else:
            self.ui.radioButton_bg_solid.setChecked(True)
        self.update_scene_bg()
        if not bg_color == "false":
            self.bg_color = bg_color
        self.update_bg_color()

    @Slot(str)
    def _edit_remote_host(self, new_text):
        """Prepends host line edit with the protocol for user convenience.

        Args:
            new_text (str): Text in the line edit after user has entered a character
        """
        prep_str = "tcp://"
        if new_text.startswith(prep_str):  # prep str already present
            new = new_text[len(prep_str) :]
        else:  # First letter has been entered
            new = new_text
        # Clear when only prep str present or when clear (x) button is clicked
        if new_text == prep_str or not new_text:
            self.ui.lineEdit_host.clear()
        else:
            self.ui.lineEdit_host.setText(prep_str + new)  # Add prep str + user input
        self._remote_host = new

    @Slot(bool)
    def _add_julia_executable(self, _=False):
        """Calls static method that shows a file browser for selecting a Julia path."""
        current_path = self.ui.comboBox_julia_path.currentText()
        if not current_path:
            current_path = resolve_default_julia_executable()
        init_dir, _ = os.path.split(current_path)
        fpath = select_file_path(self, "Select Julia Executable", init_dir, "julia")
        if not fpath:
            return
        ind = self._models.add_julia_executable(fpath, self)
        self.ui.comboBox_julia_path.setCurrentIndex(ind.row())

    @Slot(bool)
    def _add_julia_project(self, _=False):
        """Calls static method that shows a folder browser for selecting a Julia project."""
        dpath = select_dir(self, "Select Julia project directory")
        if not dpath:
            return
        ind = self._models.add_julia_project(dpath, self)
        self.ui.comboBox_julia_project_path.setCurrentIndex(ind.row())

    @Slot(bool)
    def _remove_julia_executable(self, _=False):
        """Removes the selected system interpreter from the list of known Pythons."""
        data = get_current_item_data(self.ui.comboBox_julia_path, self._models.julia_executables_model)
        if not data["exe"]:
            Notification(self, "This is the Julia in PATH and cannot be removed").show()
            return
        else:
            self._models.remove_julia_executable(data["exe"])
            self.ui.comboBox_julia_path.setCurrentIndex(0)

    @Slot(bool)
    def _remove_julia_project(self, _=False):
        """Removes the selected system interpreter from the list of known Pythons."""
        data = get_current_item_data(self.ui.comboBox_julia_project_path, self._models.julia_projects_model)
        if data["path"] == "@." or data["path"] == "":
            Notification(self, "This is the Julia base project and cannot be removed").show()
            return
        else:
            self._models.remove_julia_project(data["path"])
            self.ui.comboBox_julia_project_path.setCurrentIndex(0)

    @Slot(bool)
    def _open_julia_executable_dir(self, _=False):
        data = get_current_item_data(self.ui.comboBox_julia_path, self._models.julia_executables_model)
        if data["exe"] == "":
            path, _ = os.path.split(resolve_default_julia_executable())
        else:
            path, _ = os.path.split(data["exe"])
        self.open_rsc_dir(path)

    @Slot(bool)
    def _open_julia_project_dir(self, _=False):
        data = get_current_item_data(self.ui.comboBox_julia_project_path, self._models.julia_projects_model)
        if data["path"] == "@." or data["path"] == "":
            # Open the dir that contains the current Julia executable
            current_julia_data = get_current_item_data(self.ui.comboBox_julia_path, self._models.julia_executables_model)
            current_julia = current_julia_data["exe"]
            if not current_julia:
                path, _ = os.path.split(resolve_default_julia_executable())
            else:
                path, _ = os.path.split(current_julia)
        else:
            path = data["path"]
        self.open_rsc_dir(path)

    @Slot()
    def _set_saved_julia_kernel_selected(self):
        """Selects saved Julia after Julia models have been reloaded."""
        # if self.julia_kernel_fetcher is not None and not self.julia_kernel_fetcher.keep_going:
            # Settings widget closed while thread still running
        #     return
        ind = self._models.find_julia_kernel_index(self._saved_julia_kernel, self)
        self.ui.comboBox_julia_kernel.setCurrentIndex(ind.row())
        self._saved_julia_kernel = None

    @Slot(bool)
    def _add_python_interpreter(self, _=False):
        current_path = self.ui.comboBox_python_interpreters.currentText()
        if not current_path:
            current_path = resolve_current_python_interpreter()
        init_dir, _ = os.path.split(current_path)
        new_python = select_file_path(self, "Select Python Interpreter", init_dir, "python")
        if not new_python:
            return
        ind = self._models.add_python_interpreter(new_python, self)
        self.ui.comboBox_python_interpreters.setCurrentIndex(ind.row())

    @Slot()
    def _set_saved_python_kernel_selected(self):
        """Sets saved python as selected after Pythons have been (re)loaded."""
        # if self.python_kernel_fetcher is not None and not self.python_kernel_fetcher.keep_going:
        #     # Settings widget closed while thread still running
        #     return
        ind = self._models.find_python_kernel_index(self._saved_python_kernel, self)
        self.ui.comboBox_python_kernels.setCurrentIndex(ind.row())
        self._saved_python_kernel = None

    @Slot(bool)
    def _remove_python_system_interpreter(self, _=False):
        """Removes the selected system interpreter from the list of known Pythons."""
        data = get_current_item_data(self.ui.comboBox_python_interpreters, self._models.python_interpreters_model)
        path = data["exe"]
        if not path:
            Notification(self, "This is the current Spine Toolbox interpreter and cannot be removed").show()
        else:
            self._models.remove_python_interpreter(path)
            self.ui.comboBox_python_interpreters.setCurrentIndex(0)

    @Slot(bool)
    def _open_python_interpreter_dir(self, _=False):
        """Opens selected Python interpreter folder in File Explorer."""
        data = get_current_item_data(self.ui.comboBox_python_interpreters, self._models.python_interpreters_model)
        if data["exe"] == "":
            path, _ = os.path.split(resolve_current_python_interpreter())
        else:
            path, _ = os.path.split(data["exe"])
        self.open_rsc_dir(path)

    @Slot(bool)
    def _open_python_kernel_resource_dir(self, _=False):
        """Opens selected Python kernel's resource folder in File Explorer."""
        item = get_current_item(self.ui.comboBox_python_kernels, self._models.python_kernel_model)
        self.open_rsc_dir(item.toolTip())

    @Slot(bool)
    def _open_julia_kernel_resource_dir(self, _=False):
        """Opens Julia kernels resource dir."""
        item = get_current_item(self.ui.comboBox_julia_kernel, self._models.julia_kernel_model)
        self.open_rsc_dir(item.toolTip())

    def open_rsc_dir(self, path):
        """Opens given path in file browser."""
        if not os.path.exists(path):
            Notification(self, f"Path '{path}' does not exist").show()
            return
        url = "file:///" + path
        res = open_url(url)
        if not res:
            Notification(self, f"Opening directory '{path}' failed").show()
            return

    @Slot(str)
    def _refresh_python_kernels(self, conda_path):
        """Refreshes Python kernels when the conda line edit points to a valid conda
        executable or when the line edit is cleared.

        Args:
            conda_path (str): Text in line edit after it's been changed.
        """
        if conda_path and not is_valid_conda_executable(conda_path):
            return
        use_jupyter_console, python_exe, python_kernel = self._get_python_settings()
        self._saved_python_kernel = python_kernel
        self._models.start_fetching_python_kernels(self._set_saved_python_kernel_selected, conda_path)

    def closeEvent(self, ev):
        self._models.stop_fetching_julia_kernels()
        self._models.stop_fetching_python_kernels()
        super().closeEvent(ev)
        self._toolbox.update_properties_ui()
