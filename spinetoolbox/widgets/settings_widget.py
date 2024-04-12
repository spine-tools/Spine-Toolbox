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
from PySide6.QtWidgets import QWidget, QFileDialog, QColorDialog, QMenu, QMessageBox
from PySide6.QtCore import Slot, Qt, QSize, QSettings, QPoint, QEvent
from PySide6.QtGui import QPixmap, QIcon, QStandardItemModel, QStandardItem
from spine_engine.utils.helpers import (
    resolve_current_python_interpreter,
    resolve_default_julia_executable,
    resolve_gams_executable,
    resolve_conda_executable,
    get_julia_env,
)
from .notification import Notification
from .install_julia_wizard import InstallJuliaWizard
from .add_up_spine_opt_wizard import AddUpSpineOptWizard
from ..config import DEFAULT_WORK_DIR, SETTINGS_SS
from ..link import Link, JumpLink
from ..project_item_icon import ProjectItemIcon
from ..kernel_fetcher import KernelFetcher
from ..widgets.kernel_editor import (
    MiniPythonKernelEditor,
    MiniJuliaKernelEditor,
)
from ..helpers import (
    select_gams_executable,
    select_python_interpreter,
    select_julia_executable,
    select_julia_project,
    select_conda_executable,
    select_certificate_directory,
    file_is_valid,
    dir_is_valid,
    home_dir,
    open_url,
    is_valid_conda_executable,
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

    # pylint: disable=no-self-use
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
        auto_expand_entities = self._qsettings.value("appSettings/autoExpandObjects", defaultValue="true")
        snap_entities = self._qsettings.value("appSettings/snapEntities", defaultValue="false")
        merge_dbs = self._qsettings.value("appSettings/mergeDBs", defaultValue="true")
        db_editor_show_undo = int(self._qsettings.value("appSettings/dbEditorShowUndo", defaultValue="2"))
        max_ent_dim_count = int(self.qsettings.value("appSettings/maxEntityDimensionCount", defaultValue="5"))
        build_iters = int(self.qsettings.value("appSettings/layoutAlgoBuildIterations", defaultValue="12"))
        spread_factor = int(self.qsettings.value("appSettings/layoutAlgoSpreadFactor", defaultValue="100"))
        neg_weight_exp = int(self.qsettings.value("appSettings/layoutAlgoNegWeightExp", defaultValue="2"))
        if commit_at_exit == 0:  # Not needed but makes the code more readable.
            self.ui.checkBox_commit_at_exit.setCheckState(Qt.CheckState.Unchecked)
        elif commit_at_exit == 1:
            self.ui.checkBox_commit_at_exit.setCheckState(Qt.PartiallyChecked)
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
        self._qsettings.setValue("appSettings/autoExpandObjects", auto_expand_entities)
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
        auto_expand_entities = self._qsettings.value("appSettings/autoExpandObjects", defaultValue="true") == "true"
        merge_dbs = self._qsettings.value("appSettings/mergeDBs", defaultValue="true") == "true"
        self.set_hide_empty_classes(hide_empty_classes)
        self.set_auto_expand_entities(auto_expand_entities)
        self.set_merge_dbs(merge_dbs)

    @Slot(bool)
    def set_hide_empty_classes(self, checked=False):
        for db_editor in self.db_mngr.get_all_spine_db_editors():
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
        for db_editor in self.db_mngr.get_all_spine_db_editors():
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
        self.orig_work_dir = ""  # Work dir when this widget was opened
        self.julia_kernel_fetcher = None
        self.python_kernel_fetcher = None
        self._julia_kernel_model = QStandardItemModel(self)
        self._python_kernel_model = QStandardItemModel(self)
        self._python_kernel_combobox_context_menu = self._make_python_kernel_context_menu()
        self._julia_kernel_combobox_context_menu = self._make_julia_kernel_context_menu()
        self.ui.comboBox_julia_kernel.setModel(self._julia_kernel_model)
        self.ui.comboBox_python_kernel.setModel(self._python_kernel_model)
        # Set up comboBox menus for showing a context menu
        self.ui.comboBox_python_kernel.view().viewport().installEventFilter(self)
        self.ui.comboBox_julia_kernel.view().viewport().installEventFilter(self)
        self.ui.comboBox_python_kernel.view().setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.ui.comboBox_julia_kernel.view().setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.newly_created_kernel = None
        self._remote_host = ""
        # Initial scene bg color. Is overridden immediately in read_settings() if it exists in qSettings
        self.bg_color = self._toolbox.ui.graphicsView.scene().bg_color
        for item in self.ui.listWidget.findItems("*", Qt.MatchWildcard):
            item.setSizeHint(QSize(128, 44))
        # Ensure this window gets garbage-collected when closed
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.connect_signals()
        self.read_settings()
        self._update_python_widgets_enabled(self.ui.radioButton_use_python_jupyter_console.isChecked())
        self._update_julia_widgets_enabled(self.ui.radioButton_use_julia_jupyter_console.isChecked())
        self._update_remote_execution_page_widget_status(self.ui.checkBox_enable_remote_exec.isChecked())

    def connect_signals(self):
        """Connect signals."""
        super().connect_signals()
        self.ui.toolButton_browse_gams.clicked.connect(self.browse_gams_button_clicked)
        self.ui.toolButton_browse_julia.clicked.connect(self.browse_julia_button_clicked)
        self.ui.toolButton_browse_julia_project.clicked.connect(self.browse_julia_project_button_clicked)
        self.ui.toolButton_browse_python.clicked.connect(self.browse_python_button_clicked)
        self.ui.toolButton_browse_conda.clicked.connect(self.browse_conda_button_clicked)
        self.ui.toolButton_pick_secfolder.clicked.connect(self.browse_certificate_directory_clicked)
        self.ui.pushButton_make_python_kernel.clicked.connect(self.make_python_kernel)
        self.ui.pushButton_make_julia_kernel.clicked.connect(self.make_julia_kernel)
        self.ui.comboBox_python_kernel.customContextMenuRequested.connect(
            self.show_python_kernel_context_menu_on_combobox
        )
        self.ui.comboBox_julia_kernel.customContextMenuRequested.connect(
            self.show_julia_kernel_context_menu_on_combobox
        )
        self.ui.comboBox_python_kernel.view().customContextMenuRequested.connect(
            self.show_python_kernel_context_menu_on_combobox_list
        )
        self.ui.comboBox_julia_kernel.view().customContextMenuRequested.connect(
            self.show_julia_kernel_context_menu_on_combobox_list
        )
        self.ui.lineEdit_conda_path.textChanged.connect(self._refresh_python_kernels)
        self.ui.toolButton_browse_work.clicked.connect(self.browse_work_path)
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

    def _make_python_kernel_context_menu(self):
        """Returns a context-menu for Python kernel comboBox."""
        m = QMenu(self.ui.comboBox_python_kernel.view())
        m.addAction("Open resource dir", self._open_python_kernel_resource_dir)
        return m

    def _make_julia_kernel_context_menu(self):
        """Returns a context-menu for Julia kernel comboBox."""
        m = QMenu(self.ui.comboBox_julia_kernel.view())
        m.addAction("Open resource dir", self._open_julia_kernel_resource_dir)
        return m

    def eventFilter(self, o, event):
        """Event filter that catches mouse right button release events. This event
        typically closes the context-menu, but we want to prevent this and show a
        context-menu instead.

        Args:
            o (QObject): Watcher
            event (QEvent): Event

        Returns:
            bool: True when event is caught, False otherwise
        """
        if event.type() == QEvent.Type.MouseButtonRelease:
            if event.button() == Qt.MouseButton.RightButton:
                return True
        return False

    @Slot(bool)
    def _update_python_widgets_enabled(self, state):
        """Enables or disables some widgets based on given boolean state."""
        self.ui.comboBox_python_kernel.setEnabled(state)
        self.ui.pushButton_make_python_kernel.setEnabled(state)
        self.ui.lineEdit_python_path.setEnabled(not state)
        self.ui.toolButton_browse_python.setEnabled(not state)

    @Slot(bool)
    def _update_julia_widgets_enabled(self, state):
        """Enables or disables some widgets based on given boolean state."""
        self.ui.comboBox_julia_kernel.setEnabled(state)
        self.ui.pushButton_make_julia_kernel.setEnabled(state)
        self.ui.lineEdit_julia_path.setEnabled(not state)
        self.ui.lineEdit_julia_project_path.setEnabled(not state)
        self.ui.toolButton_browse_julia.setEnabled(not state)
        self.ui.toolButton_browse_julia_project.setEnabled(not state)

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
    def _show_install_julia_wizard(self, _=False):
        """Opens Install Julia Wizard."""
        wizard = InstallJuliaWizard(self)
        wizard.julia_exe_selected.connect(self.ui.lineEdit_julia_path.setText)
        wizard.show()

    @Slot(bool)
    def _show_add_up_spine_opt_wizard(self, _=False):
        """Opens the add/update SpineOpt wizard."""
        use_julia_jupyter_console, julia_path, julia_project_path, julia_kernel = self._get_julia_settings()
        settings = QSettings("SpineProject", "AddUpSpineOptWizard")
        settings.setValue("appSettings/useJuliaKernel", use_julia_jupyter_console)
        settings.setValue("appSettings/juliaPath", julia_path)
        settings.setValue("appSettings/juliaProjectPath", julia_project_path)
        settings.setValue("appSettings/juliaKernel", julia_kernel)
        julia_env = get_julia_env(settings)
        settings.deleteLater()
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
    def browse_gams_button_clicked(self, _=False):
        """Calls static method that shows a file browser for selecting a Gams executable."""
        select_gams_executable(self, self.ui.lineEdit_gams_path)

    @Slot(bool)
    def browse_julia_button_clicked(self, _=False):
        """Calls static method that shows a file browser for selecting a Julia path."""
        select_julia_executable(self, self.ui.lineEdit_julia_path)

    @Slot(bool)
    def browse_julia_project_button_clicked(self, _=False):
        """Calls static method that shows a folder browser for selecting a Julia project."""
        select_julia_project(self, self.ui.lineEdit_julia_project_path)

    @Slot(bool)
    def browse_python_button_clicked(self, _=False):
        """Calls static method that shows a file browser for selecting a Python interpreter."""
        select_python_interpreter(self, self.ui.lineEdit_python_path)

    @Slot(bool)
    def browse_conda_button_clicked(self, _=False):
        """Calls static method that shows a file browser for selecting a Conda executable."""
        select_conda_executable(self, self.ui.lineEdit_conda_path)

    @Slot(bool)
    def browse_certificate_directory_clicked(self, _=False):
        """Calls static method that shows a file browser for selecting the security folder for Engine Server."""
        select_certificate_directory(self, self.ui.lineEdit_secfolder)

    @Slot(bool)
    def make_python_kernel(self, _=False):
        """Makes a Python kernel for Jupyter Console based on selected Python interpreter.
        If a kernel using this Python interpreter already exists, sets that kernel selected in the comboBox."""
        python_exe = self.ui.lineEdit_python_path.text().strip()
        if not python_exe:
            python_exe = resolve_current_python_interpreter()
        python_kernel = _get_kernel_name_by_exe(python_exe, self._python_kernel_model)
        if not python_kernel:
            mpke = MiniPythonKernelEditor(self, python_exe)
            mpke.set_kernel_name()
            mpke.make_kernel()
            self.newly_created_kernel = mpke.new_kernel_name()
            self.start_fetching_python_kernels()
            return
        self.newly_created_kernel = python_kernel
        self.restore_saved_python_kernel()

    @Slot(bool)
    def make_julia_kernel(self, _=False):
        """Makes a Julia kernel for Jupyter Console based on selected Julia executable and Julia project.
        If a kernel using the selected Julia executable and project already exists, sets that kernel
        selected in the comboBox."""
        use_julia_jupyter_console, julia_exe, julia_project, julia_kernel = self._get_julia_settings()
        if not julia_exe:
            julia_exe = resolve_default_julia_executable()
        julia_kernel = _get_kernel_name_by_exe(julia_exe, self._julia_kernel_model)
        if julia_kernel:  # Kernel with matching executable found
            match = _selected_project_matches_kernel_project(julia_kernel, julia_project, self._julia_kernel_model)
            if not match:  # Julia project does not match, ask what to do
                msg = (
                    f"Julia kernel <b>{julia_kernel}</b> pointing to executable <b>{julia_exe}</b> "
                    f"already exists, but the Julia project is different. If you click <b>Make kernel</b>, "
                    f"this kernel <b>may be overwritten</b>. Continue?"
                )
                box = QMessageBox(
                    QMessageBox.Icon.Question,
                    "Make a new Julia kernel?",
                    msg,
                    buttons=QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel,
                    parent=self,
                )
                box.button(QMessageBox.StandardButton.Ok).setText("Make kernel")
                box.setWindowIcon(QIcon(":/symbols/app.ico"))
                answer = box.exec()
                if answer != QMessageBox.StandardButton.Ok:
                    return
            else:  # Matching kernel found -> set as current item
                self.newly_created_kernel = julia_kernel
                self.restore_saved_julia_kernel()
                return
        # Make new kernel or (possibly) overwrite existing one
        mjke = MiniJuliaKernelEditor(self, julia_exe, julia_project)
        mjke.make_kernel()
        self.newly_created_kernel = mjke.new_kernel_name()
        if not self.newly_created_kernel:  # This is an empty string if the kernel was overwritten
            self.newly_created_kernel = julia_kernel
        self.start_fetching_julia_kernels()

    @Slot(QPoint)
    def show_python_kernel_context_menu_on_combobox(self, pos):
        """Shows the context-menu on Python kernels combobox."""
        row = self.ui.comboBox_python_kernel.currentIndex()
        if row == 0:
            return
        global_pos = self.ui.comboBox_python_kernel.mapToGlobal(pos)
        self._python_kernel_combobox_context_menu.popup(global_pos)

    @Slot(QPoint)
    def show_julia_kernel_context_menu_on_combobox(self, pos):
        """Shows the context-menu on Julia kernels combobox."""
        row = self.ui.comboBox_julia_kernel.currentIndex()
        if row == 0:
            return
        global_pos = self.ui.comboBox_julia_kernel.mapToGlobal(pos)
        self._julia_kernel_combobox_context_menu.popup(global_pos)

    @Slot(QPoint)
    def show_python_kernel_context_menu_on_combobox_list(self, pos):
        """Shows the context-menu on Python kernels combobox popup list."""
        index = self.ui.comboBox_python_kernel.view().indexAt(pos)
        if not index.isValid() or index.row() == 0:
            return
        global_pos = self.ui.comboBox_python_kernel.view().viewport().mapToGlobal(pos)
        self._python_kernel_combobox_context_menu.popup(global_pos)

    @Slot(QPoint)
    def show_julia_kernel_context_menu_on_combobox_list(self, pos):
        """Shows the context-menu on Julia kernels combobox popup list."""
        index = self.ui.comboBox_julia_kernel.view().indexAt(pos)
        if not index.isValid() or index.row() == 0:
            return
        global_pos = self.ui.comboBox_julia_kernel.view().viewport().mapToGlobal(pos)
        self._julia_kernel_combobox_context_menu.popup(global_pos)

    @Slot(bool)
    def _open_python_kernel_resource_dir(self, _=False):
        """Opens Python kernels resource dir."""
        try:
            index = self.ui.comboBox_python_kernel.view().selectedIndexes()[0]
            item = self._python_kernel_model.item(index.row())
        except IndexError:
            row = self.ui.comboBox_python_kernel.currentIndex()
            item = self._python_kernel_model.item(row)
        self.open_rsc_dir(item)

    @Slot(bool)
    def _open_julia_kernel_resource_dir(self, _=False):
        """Opens Julia kernels resource dir."""
        try:
            index = self.ui.comboBox_julia_kernel.view().selectedIndexes()[0]
            item = self._julia_kernel_model.item(index.row())
        except IndexError:
            row = self.ui.comboBox_julia_kernel.currentIndex()
            item = self._julia_kernel_model.item(row)
        self.open_rsc_dir(item)

    def open_rsc_dir(self, item):
        """Open path hidden in given item's tooltip in file browser."""
        resource_dir = item.toolTip()
        if not os.path.exists(resource_dir):
            Notification(self, f"Path '{resource_dir}' does not exist").show()
            return
        url = "file:///" + resource_dir
        res = open_url(url)
        if not res:
            Notification(self, f"Opening resource directory '{resource_dir}' failed").show()
            return

    @Slot(bool)
    def browse_work_path(self, _=False):
        """Open file browser where user can select the path to wanted work directory."""
        # noinspection PyCallByClass, PyTypeChecker, PyArgumentList
        answer = QFileDialog.getExistingDirectory(self, "Select Work Directory", home_dir())
        if answer == "":  # Cancel button clicked
            return
        selected_path = os.path.abspath(answer)
        self.ui.lineEdit_work_dir.setText(selected_path)

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
        """Read saved settings from app QSettings instance and update UI to display them."""
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
        use_julia_jupyter_console = int(self._qsettings.value("appSettings/useJuliaKernel", defaultValue="0"))
        julia_path = self._qsettings.value("appSettings/juliaPath", defaultValue="")
        julia_project_path = self._qsettings.value("appSettings/juliaProjectPath", defaultValue="")
        use_python_jupyter_console = int(self._qsettings.value("appSettings/usePythonKernel", defaultValue="0"))
        python_path = self._qsettings.value("appSettings/pythonPath", defaultValue="")
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
        # Add Python and Julia kernels to comboBoxes
        self.start_fetching_julia_kernels()
        self.start_fetching_python_kernels()
        if use_julia_jupyter_console == 2:
            self.ui.radioButton_use_julia_jupyter_console.setChecked(True)
        else:
            self.ui.radioButton_use_julia_basic_console.setChecked(True)
        self.ui.lineEdit_julia_path.setPlaceholderText(resolve_default_julia_executable())
        self.ui.lineEdit_julia_path.setText(julia_path)
        self.ui.lineEdit_julia_project_path.setText(julia_project_path)
        if use_python_jupyter_console == 2:
            self.ui.radioButton_use_python_jupyter_console.setChecked(True)
        else:
            self.ui.radioButton_use_python_basic_console.setChecked(True)
        self.ui.lineEdit_python_path.setPlaceholderText(resolve_current_python_interpreter())
        self.ui.lineEdit_python_path.setText(python_path)
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
            self.ui.checkBox_save_spec_before_closing.setCheckState(Qt.PartiallyChecked)
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
        if use_julia_jupyter_console == "2" and not julia_kernel:
            msg = (
                f"You have selected <b>Jupyter Console</b> for Julia Tools "
                f"but you did not select a kernel, please"
                f"<br><br>1. Select one from the dropdown menu"
                f"<br>2. Click <b>Make Julia Kernel</b> button to create one, or"
                f"<br>3. Select <b>Basic Console</b>"
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
        use_python_jupyter_console = "2" if self.ui.radioButton_use_python_jupyter_console.isChecked() else "0"
        python_exe = self.ui.lineEdit_python_path.text().strip()
        if self.ui.comboBox_python_kernel.currentIndex() == 0:
            python_kernel = ""
        else:
            python_kernel = self.ui.comboBox_python_kernel.currentText()
        if use_python_jupyter_console == "2" and not python_kernel:
            msg = (
                f"You have selected <b>Jupyter Console</b> for Python Tools "
                f"but you did not select a kernel, please"
                f"<br><br>1. Select one from the dropdown menu"
                f"<br>2. Click <b>Make Python Kernel</b> button to create one, or"
                f"<br>3. Select <b>Basic Console</b>"
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
        """Returns current Julia execution settings in Settings->Tools widget."""
        use_julia_jupyter_console = "2" if self.ui.radioButton_use_julia_jupyter_console.isChecked() else "0"
        julia_exe = self.ui.lineEdit_julia_path.text().strip()
        julia_project = self.ui.lineEdit_julia_project_path.text().strip()
        julia_kernel = ""
        if self.ui.comboBox_julia_kernel.currentIndex() != 0:
            julia_kernel = self.ui.comboBox_julia_kernel.currentText()
        return use_julia_jupyter_console, julia_exe, julia_project, julia_kernel

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

    def start_fetching_julia_kernels(self):
        """Starts a thread for fetching Julia kernels."""
        if self.julia_kernel_fetcher is not None and self.julia_kernel_fetcher.isRunning():
            # Trying to start a new thread when the old one is still running
            return
        self._julia_kernel_model.clear()
        self.ui.comboBox_julia_kernel.addItem("Select Julia kernel...")
        conda_path = self._toolbox.qsettings().value("appSettings/condaPath", defaultValue="")
        self.julia_kernel_fetcher = KernelFetcher(conda_path, fetch_mode=4)
        self.julia_kernel_fetcher.kernel_found.connect(self.add_julia_kernel)
        self.julia_kernel_fetcher.finished.connect(self.restore_saved_julia_kernel)
        self.julia_kernel_fetcher.finished.connect(self.julia_kernel_fetcher.deleteLater)
        self.julia_kernel_fetcher.start()

    @Slot()
    def stop_fetching_julia_kernels(self):
        """Terminates the kernel fetcher thread."""
        if self.julia_kernel_fetcher is not None:
            self.julia_kernel_fetcher.stop_fetcher.emit()

    @Slot(str, str, bool, QIcon, dict)
    def add_julia_kernel(self, kernel_name, resource_dir, conda, icon, deats):
        """Adds a kernel entry as an item to Julia kernels comboBox."""
        if self.julia_kernel_fetcher is not None and not self.julia_kernel_fetcher.keep_going:
            # Settings widget closed while thread still running
            return
        item = QStandardItem(kernel_name)
        item.setIcon(icon)
        item.setToolTip(resource_dir)
        item.setData(deats)
        self._julia_kernel_model.appendRow(item)

    @Slot()
    def restore_saved_julia_kernel(self):
        """Sets saved or given julia kernel selected after kernels have been loaded."""
        if self.julia_kernel_fetcher is not None and not self.julia_kernel_fetcher.keep_going:
            # Settings widget closed while thread still running
            return
        if not self.newly_created_kernel:
            julia_kernel = self._qsettings.value("appSettings/juliaKernel", defaultValue="")
        else:
            julia_kernel = self.newly_created_kernel
            self.newly_created_kernel = None
        ind = self.ui.comboBox_julia_kernel.findText(julia_kernel)
        if ind == -1:
            self.ui.comboBox_julia_kernel.setCurrentIndex(0)
        else:
            self.ui.comboBox_julia_kernel.setCurrentIndex(ind)
        self.julia_kernel_fetcher = None

    def start_fetching_python_kernels(self, conda_path_updated=False):
        """Starts a thread for fetching Python kernels."""
        if self.python_kernel_fetcher is not None and self.python_kernel_fetcher.isRunning():
            # Trying to start a new thread when the old one is still running
            return
        self._python_kernel_model.clear()
        self.ui.comboBox_python_kernel.addItem("Select Python kernel...")
        if not conda_path_updated:
            conda_path = self._toolbox.qsettings().value("appSettings/condaPath", defaultValue="")
        else:
            conda_path = self.ui.lineEdit_conda_path.text().strip()
        self.python_kernel_fetcher = KernelFetcher(conda_path, fetch_mode=2)
        self.python_kernel_fetcher.kernel_found.connect(self.add_python_kernel)
        self.python_kernel_fetcher.finished.connect(self.restore_saved_python_kernel)
        self.python_kernel_fetcher.finished.connect(self.python_kernel_fetcher.deleteLater)
        self.python_kernel_fetcher.start()

    @Slot()
    def stop_fetching_python_kernels(self):
        """Terminates the kernel fetcher thread."""
        if self.python_kernel_fetcher is not None:
            self.python_kernel_fetcher.stop_fetcher.emit()

    @Slot(str, str, bool, QIcon, dict)
    def add_python_kernel(self, kernel_name, resource_dir, conda, icon, deats):
        """Adds a kernel entry as an item to Python kernels comboBox."""
        if self.python_kernel_fetcher is not None and not self.python_kernel_fetcher.keep_going:
            # Settings widget closed while thread still running
            return
        item = QStandardItem(kernel_name)
        item.setIcon(icon)
        item.setToolTip(resource_dir)
        deats["is_conda"] = conda
        item.setData(deats)
        self._python_kernel_model.appendRow(item)

    @Slot()
    def restore_saved_python_kernel(self):
        """Sets saved or given python kernel selected after kernels have been loaded."""
        if self.python_kernel_fetcher is not None and not self.python_kernel_fetcher.keep_going:
            # Settings widget closed while thread still running
            return
        if not self.newly_created_kernel:
            python_kernel = self._qsettings.value("appSettings/pythonKernel", defaultValue="")
        else:
            python_kernel = self.newly_created_kernel
            self.newly_created_kernel = None
        ind = self.ui.comboBox_python_kernel.findText(python_kernel)
        if ind == -1:
            self.ui.comboBox_python_kernel.setCurrentIndex(0)
        else:
            self.ui.comboBox_python_kernel.setCurrentIndex(ind)
        self.python_kernel_fetcher = None

    @Slot(str)
    def _refresh_python_kernels(self, conda_path):
        """Refreshes Python kernels when the conda line edit points to a valid conda
        executable or when the line edit is cleared.

        Args:
            conda_path (str): Text in line edit after it's been changed.
        """
        if conda_path and not is_valid_conda_executable(conda_path):
            return
        self.newly_created_kernel = self.ui.comboBox_python_kernel.currentText()
        self.start_fetching_python_kernels(conda_path_updated=True)

    def closeEvent(self, ev):
        self.stop_fetching_julia_kernels()
        self.stop_fetching_python_kernels()
        super().closeEvent(ev)
        self._toolbox.update_properties_ui()


def _get_kernel_name_by_exe(p, kernel_model):
    """Returns the kernel name corresponding to given executable or an empty string if not found.

    Args:
        p (str): Absolute path to an executable
        kernel_model (QStandardItemModel): Model containing items, which contain kernel spec details as item data

    Returns:
        str: Kernel name or an empty string
    """
    for i in range(1, kernel_model.rowCount()):  # Start from row 1
        name = kernel_model.item(i).data(Qt.ItemDataRole.DisplayRole)
        deats = kernel_model.item(i).data()
        if not deats:
            continue  # Conda kernels don't have deats
        if _samefile(deats["exe"], p):
            return name
    return ""


def _selected_project_matches_kernel_project(julia_kernel_name, julia_project, kernel_model):
    """Checks if given Julia kernel's project matches the given Julia project.

    Args:
        julia_kernel_name (str): Kernel name
        julia_project (str): Path or some other string (e.g. '@.') to denote the Julia project
        kernel_model (QStandardItemModel): Model containing kernels

    Returns:
        bool: True if projects match, False otherwise
    """
    for row in range(1, kernel_model.rowCount()):  # Start from row 1
        if kernel_model.item(row).data(Qt.ItemDataRole.DisplayRole) == julia_kernel_name:
            deats = kernel_model.item(row).data()
            if _samefile(deats["project"], julia_project) or deats["project"] == julia_project:
                return True
    return False


def _samefile(a, b):
    try:
        return os.path.samefile(os.path.realpath(a), os.path.realpath(b))
    except FileNotFoundError:
        return False
