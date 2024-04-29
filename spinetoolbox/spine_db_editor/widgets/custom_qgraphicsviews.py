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

"""Classes for custom QGraphicsViews for the Entity graph view."""
import os
import sys
import tempfile
from contextlib import contextmanager
import numpy as np
from PySide6.QtCore import Qt, QTimeLine, Signal, Slot, QRectF, QRunnable, QThreadPool
from PySide6.QtWidgets import QMenu, QInputDialog, QColorDialog, QMessageBox, QLineEdit, QGraphicsScene
from PySide6.QtGui import QCursor, QPainter, QIcon, QAction, QPageSize, QPixmap
from PySide6.QtPrintSupport import QPrinter
from PySide6.QtSvg import QSvgGenerator
from ...helpers import CharIconEngine, remove_first
from ...widgets.custom_qgraphicsviews import CustomQGraphicsView
from ...widgets.custom_qwidgets import ToolBarWidgetAction, HorizontalSpinBox
from ..graphics_items import EntityItem, CrossHairsArcItem, BgItem, ArcItem
from .custom_qwidgets import ExportAsVideoDialog
from .select_graph_parameters_dialog import SelectGraphParametersDialog


class _GraphProperty:
    def __init__(self, name, settings_name):
        self._name = name
        self._settings_name = "appSettings/" + settings_name
        self._spine_db_editor = None
        self._value = None

    @property
    def value(self):
        return self._value

    def connect_spine_db_editor(self, spine_db_editor):
        self._spine_db_editor = spine_db_editor


class _GraphBoolProperty(_GraphProperty):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._action = None

    @Slot(bool)
    def _set_value(self, _checked=False, save_setting=True):
        checked = self._action.isChecked()
        if checked == self._value:
            return
        self._value = checked
        if save_setting:
            self._spine_db_editor.qsettings.setValue(self._settings_name, "true" if checked else "false")
            self._spine_db_editor.build_graph()

    def set_value(self, checked):
        self._action.setChecked(checked)
        self._set_value(save_setting=False)

    def update(self, menu):
        self._value = self._spine_db_editor.qsettings.value(self._settings_name, defaultValue="true") == "true"
        self._action = menu.addAction(self._name)
        self._action.setCheckable(True)
        self._action.setChecked(self._value)
        self._action.triggered.connect(self._set_value)


class _GraphIntProperty(_GraphProperty):
    def __init__(self, min_value, max_value, default_value, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._min_value, self._max_value, self._default_value = min_value, max_value, default_value
        self._spin_box = None

    @Slot(int)
    def _set_value(self, _value=None, save_setting=True):
        value = self._spin_box.value()
        if value == self._value:
            return
        self._value = value
        if save_setting:
            self._spine_db_editor.qsettings.setValue(self._settings_name, str(value))
            self._spine_db_editor.build_graph()

    def set_value(self, value):
        self._spin_box.setValue(value)
        self._set_value(save_setting=False)

    def update(self, menu):
        self._value = int(
            self._spine_db_editor.qsettings.value(self._settings_name, defaultValue=str(self._default_value))
        )
        action = ToolBarWidgetAction(self._name, menu, compact=True)
        self._spin_box = HorizontalSpinBox(menu)
        self._spin_box.setMinimum(self._min_value)
        if self._max_value is not None:
            self._spin_box.setMaximum(self._max_value)
        self._spin_box.setValue(self._value)
        self._spin_box.valueChanged.connect(self._set_value)
        action.tool_bar.addWidget(self._spin_box)
        menu.addAction(action)


class EntityQGraphicsView(CustomQGraphicsView):
    """QGraphicsView for the Entity Graph View."""

    graph_selection_changed = Signal(list)

    def __init__(self, parent):
        """

        Args:
            parent (QWidget): Graph View Form's (QMainWindow) central widget (self.centralwidget)
        """
        super().__init__(parent=parent)  # Parent is passed to QWidget's constructor
        self._spine_db_editor = None
        self._menu = QMenu(self)
        self.pos_x_parameter = "x"
        self.pos_y_parameter = "y"
        self.name_parameter = ""
        self.color_parameter = ""
        self.arc_width_parameter = ""
        self.vertex_radius_parameter = ""
        self._current_state_name = ""
        self._margin = 0.025
        self._bg_item = None
        self.selected_items = []
        self.hidden_items = {}
        self._hovered_ent_item = None
        self.entity_class = None
        self.cross_hairs_items = []
        self._properties = {
            "auto_expand_entities": _GraphBoolProperty("Auto-expand entities", "autoExpandEntities"),
            "merge_dbs": _GraphBoolProperty("Merge databases", "mergeDBs"),
            "snap_entities": _GraphBoolProperty("Snap entities to grid", "snapEntities"),
            "max_entity_dimension_count": _GraphIntProperty(
                2, None, 5, "Max. entity dimension count", "maxEntityDimensionCount"
            ),
            "build_iters": _GraphIntProperty(3, None, 12, "Number of build iterations", "layoutAlgoBuildIterations"),
            "spread_factor": _GraphIntProperty(
                1, 100, 100, "Minimum distance between nodes (%)", "layoutAlgoSpreadFactor"
            ),
            "neg_weight_exp": _GraphIntProperty(
                1, 100, 2, "Decay rate of attraction with distance", "layoutAlgoNegWeightExp"
            ),
        }
        self._add_entities_action = None
        self._select_graph_params_action = None
        self._save_pos_action = None
        self._clear_pos_action = None
        self._show_all_hidden_action = None
        self._restore_all_pruned_action = None
        self._rebuild_action = None
        self._export_as_image_action = None
        self._export_as_video_action = None
        self._zoom_action = None
        self._rotate_action = None
        self._arc_length_action = None
        self._find_action = None
        self._select_bg_image_action = None
        self._save_state_action = None
        self._context_menu_pos = None
        self._hide_classes_menu = None
        self._show_hidden_menu = None
        self._prune_classes_menu = None
        self._restore_pruned_menu = None
        self._load_state_menu = None
        self._remove_state_menu = None
        self._items_per_class = {}
        self._db_map_graph_data_by_name = {}
        self._thread_pool = QThreadPool()

    @property
    def _qsettings(self):
        return self._spine_db_editor.qsettings

    @property
    def db_mngr(self):
        return self._spine_db_editor.db_mngr

    @property
    def entity_items(self):
        return [x for x in self.scene().items() if isinstance(x, EntityItem) and x.isVisible()]

    def get_property(self, name):
        return self._properties[name].value

    def set_property(self, name, value):
        return self._properties[name].set_value(value)

    def get_all_properties(self):
        return {name: prop.value for name, prop in self._properties.items()}

    def set_many_properties(self, props):
        for name, value in props.items():
            self.set_property(name, value)

    @Slot()
    def handle_scene_selection_changed(self):
        """Filters parameters by selected objects in the graph."""
        if self.scene() is None:
            return
        self.selected_items = [x for x in self.scene().selectedItems() if isinstance(x, EntityItem)]
        self.graph_selection_changed.emit(self.selected_items)
        default_data = self.selected_items[0].default_parameter_data() if len(self.selected_items) == 1 else {}
        default_db_map = self.selected_items[0].first_db_map if len(self.selected_items) == 1 else None
        self._spine_db_editor.set_default_parameter_data(default_data, default_db_map)

    def connect_spine_db_editor(self, spine_db_editor):
        self._spine_db_editor = spine_db_editor
        for prop in self._properties.values():
            prop.connect_spine_db_editor(spine_db_editor)
        self.populate_context_menu()

    def populate_context_menu(self):
        self._add_entities_action = self._menu.addAction("Add entities...", self.add_entities_at_position)
        self._menu.addSeparator()
        self._find_action = self._menu.addAction("Search...", self._find)
        self._menu.addSeparator()
        self._hide_classes_menu = self._menu.addMenu("Hide classes")
        self._hide_classes_menu.triggered.connect(self._hide_class)
        self._show_hidden_menu = self._menu.addMenu("Show")
        self._show_hidden_menu.triggered.connect(self.show_hidden_items)
        self._show_all_hidden_action = self._menu.addAction("Show all", self.show_all_hidden_items)
        self._menu.addSeparator()
        self._prune_classes_menu = self._menu.addMenu("Prune classes")
        self._prune_classes_menu.triggered.connect(self._prune_class)
        self._restore_pruned_menu = self._menu.addMenu("Restore")
        self._restore_pruned_menu.triggered.connect(self.restore_pruned_items)
        self._restore_all_pruned_action = self._menu.addAction("Restore all", self.restore_all_pruned_items)
        self._menu.addSeparator()
        self._zoom_action = ToolBarWidgetAction("Zoom", self._menu, compact=True)
        self._zoom_action.tool_bar.addAction("-", self.zoom_out).setToolTip("Zoom out")
        self._zoom_action.tool_bar.addAction("Reset", self.reset_zoom).setToolTip("Reset zoom")
        self._zoom_action.tool_bar.addAction("+", self.zoom_in).setToolTip("Zoom in")
        self._rotate_action = ToolBarWidgetAction("Rotate", self._menu, compact=True)
        self._rotate_action.tool_bar.addAction("\u2b6f", self.rotate_anticlockwise).setToolTip(
            "Rotate counter-clockwise"
        )
        self._rotate_action.tool_bar.addAction("\u2b6e", self.rotate_clockwise).setToolTip("Rotate clockwise")
        self._arc_length_action = ToolBarWidgetAction("Arc length", self._menu, compact=True)
        self._arc_length_action.tool_bar.addAction(
            QIcon(CharIconEngine("\uf422")), "", self.decrease_arc_length
        ).setToolTip("Decrease arc length")
        self._arc_length_action.tool_bar.addAction(
            QIcon(CharIconEngine("\uf424")), "", self.increase_arc_length
        ).setToolTip("Increase arc length")
        self._menu.addSeparator()
        self._menu.addAction(self._zoom_action)
        self._menu.addAction(self._arc_length_action)
        self._menu.addAction(self._rotate_action)
        self._menu.addSeparator()
        for prop in self._properties.values():
            prop.update(self._menu)
        self._menu.addSeparator()
        self._select_graph_params_action = self._menu.addAction(
            "Select graph parameters...", self.select_graph_parameters
        )
        self._select_bg_image_action = self._menu.addAction("Select background image...", self._select_bg_image)
        self._menu.addSeparator()
        self._save_pos_action = self._menu.addAction("Save positions", self._save_all_positions)
        self._clear_pos_action = self._menu.addAction("Clear saved positions", self._clear_all_positions)
        self._menu.addSeparator()
        self._save_state_action = self._menu.addAction("Save state...", self._save_state)
        self._load_state_menu = self._menu.addMenu("Load state")
        self._load_state_menu.triggered.connect(self._load_state)
        self._remove_state_menu = self._menu.addMenu("Remove state")
        self._remove_state_menu.triggered.connect(self._remove_state)
        self._menu.addSeparator()
        self._export_as_image_action = self._menu.addAction("Export as image...", self.export_as_image)
        self._export_as_video_action = self._menu.addAction("Export as video...", self.export_as_video)
        self._menu.addSeparator()
        self._rebuild_action = self._menu.addAction("Rebuild", self._spine_db_editor.rebuild_graph)
        self._menu.aboutToShow.connect(self._update_actions_visibility)

    @Slot()
    def _update_actions_visibility(self):
        """Enables or disables actions according to current selection in the graph."""
        has_graph = bool(self.items())
        self._items_per_class = {}
        for item in self.entity_items:
            key = f"{item.entity_class_name}"
            self._items_per_class.setdefault(key, []).append(item)
        self._db_map_graph_data_by_name = self._spine_db_editor.get_db_map_graph_data_by_name()
        self._show_all_hidden_action.setEnabled(bool(self.hidden_items))
        self._restore_all_pruned_action.setEnabled(any(self._spine_db_editor.pruned_db_map_entity_ids.values()))
        self._rebuild_action.setEnabled(has_graph)
        self._zoom_action.setEnabled(has_graph)
        self._rotate_action.setEnabled(has_graph)
        self._find_action.setEnabled(has_graph)
        self._export_as_image_action.setEnabled(has_graph)
        self._export_as_video_action.setEnabled(has_graph and self._spine_db_editor.ui.time_line_widget.isVisible())
        self._show_hidden_menu.clear()
        self._show_hidden_menu.setEnabled(any(self.hidden_items.values()))
        for key in sorted(self.hidden_items):
            self._show_hidden_menu.addAction(key)
        self._restore_pruned_menu.clear()
        self._restore_pruned_menu.setEnabled(any(self._spine_db_editor.pruned_db_map_entity_ids.values()))
        for key in sorted(self._spine_db_editor.pruned_db_map_entity_ids):
            self._restore_pruned_menu.addAction(key)
        self._hide_classes_menu.clear()
        self._hide_classes_menu.setEnabled(bool(self._items_per_class))
        for key in sorted(self._items_per_class.keys() - self.hidden_items.keys()):
            self._hide_classes_menu.addAction(key)
        self._prune_classes_menu.clear()
        self._prune_classes_menu.setEnabled(bool(self._items_per_class))
        for key in sorted(self._items_per_class.keys() - self._spine_db_editor.pruned_db_map_entity_ids.keys()):
            self._prune_classes_menu.addAction(key)
        self._save_state_action.setEnabled(has_graph)
        self._load_state_menu.clear()
        self._load_state_menu.setEnabled(bool(self._db_map_graph_data_by_name))
        self._remove_state_menu.clear()
        self._remove_state_menu.setEnabled(bool(self._db_map_graph_data_by_name))
        for key in sorted(self._db_map_graph_data_by_name.keys()):
            self._load_state_menu.addAction(key)
            self._remove_state_menu.addAction(key)

    def make_items_menu(self):
        menu = QMenu(self)
        menu.addAction("Save positions", self._save_selected_positions).setEnabled(bool(self.selected_items))
        menu.addAction("Clear saved positions", self._clear_selected_positions).setEnabled(bool(self.selected_items))
        menu.addSeparator()
        menu.addAction("Hide", self.hide_selected_items).setEnabled(bool(self.selected_items))
        menu.addAction("Prune", self.prune_selected_items).setEnabled(bool(self.selected_items))
        menu.addSeparator()
        menu.addAction("Edit", self.edit_selected).setEnabled(bool(self.selected_items))
        menu.addAction("Remove", self.remove_selected).setEnabled(bool(self.selected_items))
        return menu

    def _save_state(self):
        name, ok = QInputDialog.getText(
            self, "Save state...", "Enter a name for the state.", QLineEdit.Normal, self._current_state_name
        )
        if not ok:
            return
        db_map_graph_data = self._db_map_graph_data_by_name.get(name)
        if db_map_graph_data is not None:
            button = QMessageBox.question(
                self._spine_db_editor,
                self._spine_db_editor.windowTitle(),
                f"State {name} already exists. Do you want to overwrite it?",
            )
            if button == QMessageBox.StandardButton.Yes:
                self._spine_db_editor.overwrite_graph_data(db_map_graph_data)
            return
        self._spine_db_editor.save_graph_data(name)

    @Slot(QAction)
    def _load_state(self, action):
        self._current_state_name = name = action.text()
        db_map_graph_data = self._db_map_graph_data_by_name.get(name)
        self._spine_db_editor.load_graph_data(db_map_graph_data)

    @Slot(QAction)
    def _remove_state(self, action):
        name = action.text()
        self._spine_db_editor.remove_graph_data(name)

    def _find(self):
        expr, ok = QInputDialog.getText(self, "Find in graph...", "Enter entity names to find separated by comma.")
        if not ok:
            return
        names = [x.strip() for x in expr.split(",")]
        items = [item for item in self.entity_items if any(n == item.name for n in names)]
        if not items:
            return
        color = QColorDialog.getColor(Qt.yellow, self, "Choose highlight color")
        for item in items:
            item.set_highlight_color(color)

    def increase_arc_length(self):
        for item in self.entity_items:
            new_pos = 1.1 * item.pos()
            item.set_pos(new_pos.x(), new_pos.y())

    def decrease_arc_length(self):
        for item in self.entity_items:
            new_pos = item.pos() / 1.1
            item.set_pos(new_pos.x(), new_pos.y())

    @Slot(bool)
    def add_entities_at_position(self, checked=False):
        self._spine_db_editor.add_entities_at_position(self._context_menu_pos)

    @Slot(bool)
    def edit_selected(self, _=False):
        """Edits selected items."""
        ent_items = [item for item in self.selected_items if isinstance(item, EntityItem)]
        self._spine_db_editor.show_edit_entities_form(ent_items)

    @Slot(bool)
    def remove_selected(self, _=False):
        """Removes selected items."""
        if not self.selected_items:
            return
        selected = {"entity": [item for item in self.selected_items if isinstance(item, EntityItem)]}
        self._spine_db_editor.show_remove_entity_tree_items_form(selected)

    def _get_selected_entity_names(self):
        if not self.selected_items:
            return ""
        names = "'" + self.selected_items[0].name + "'"
        if len(self.selected_items) > 1:
            names += f" and {len(self.selected_items) - 1} other entities"
        return names

    @Slot(bool)
    def hide_selected_items(self, checked=False):
        """Hides selected items."""
        key = self._get_selected_entity_names()
        self.hidden_items[key] = self.selected_items
        for item in self.selected_items:
            item.setVisible(False)

    @Slot(QAction)
    def _hide_class(self, action):
        """Hides some class."""
        key = action.text()
        items = self._items_per_class[key]
        self.hidden_items[key] = items
        for item in items:
            item.setVisible(False)

    @Slot(bool)
    def show_all_hidden_items(self, checked=False):
        """Shows all hidden items."""
        if not self.scene():
            return
        while self.hidden_items:
            _, items = self.hidden_items.popitem()
            for item in items:
                item.setVisible(True)

    @Slot(QAction)
    def show_hidden_items(self, action):
        """Shows some hidden items."""
        key = action.text()
        items = self.hidden_items.pop(key, None)
        if items is not None:
            for item in items:
                item.setVisible(True)

    @Slot(bool)
    def prune_selected_items(self, checked=False):
        """Prunes selected items."""
        key = self._get_selected_entity_names()
        self._spine_db_editor.prune_graph(key, {db_map_id for x in self.selected_items for db_map_id in x.db_map_ids})

    @Slot(QAction)
    def _prune_class(self, action):
        """Prunnes some class."""
        key = action.text()
        self._spine_db_editor.prune_graph(
            key,
            {
                (db_map, x["id"])
                for item in self._items_per_class[key]
                for db_map in item.db_maps
                for x in self.db_mngr.get_items_by_field(db_map, "entity", "class_id", item.entity_class_id(db_map))
            },
        )

    @Slot(bool)
    def restore_all_pruned_items(self, checked=False):
        """Reinstates all pruned items."""
        self._spine_db_editor.restore_graph()

    @Slot(QAction)
    def restore_pruned_items(self, action):
        """Reinstates some pruned items."""
        key = action.text()
        self._spine_db_editor.restore_graph(key)

    @Slot(bool)
    def select_graph_parameters(self, checked=False):
        parameters = {
            "Name": self.name_parameter,
            "Position x": self.pos_x_parameter,
            "Position y": self.pos_y_parameter,
            "Color": self.color_parameter,
            "Arc width": self.arc_width_parameter,
            "Vertex radius": self.vertex_radius_parameter,
        }
        dialog = SelectGraphParametersDialog(self._spine_db_editor, parameters)
        dialog.show()
        dialog.selection_made.connect(self._set_graph_parameters)

    @Slot(list)
    def _set_graph_parameters(self, parameters):
        parameters = iter(parameters)
        self.name_parameter = next(parameters)
        self.pos_x_parameter = next(parameters)
        self.pos_y_parameter = next(parameters)
        self.color_parameter = next(parameters)
        self.arc_width_parameter = next(parameters)
        self.vertex_radius_parameter = next(parameters)
        self._spine_db_editor.polish_items()

    @Slot(bool)
    def _save_selected_positions(self, checked=False):
        self._save_positions(self.selected_items)

    @Slot(bool)
    def _save_all_positions(self, checked=False):
        self._save_positions(self.entity_items)

    def _save_positions(self, items):
        if not self.pos_x_parameter or not self.pos_y_parameter:
            msg = "You haven't selected the position parameters"
            self._spine_db_editor.msg.emit(msg)
            return
        ent_items = [item for item in items if isinstance(item, EntityItem)]
        db_map_class_ent_items = {}
        for item in ent_items:
            for db_map in item.db_maps:
                db_map_class_ent_items.setdefault(db_map, {}).setdefault(item.entity_class_name, []).append(item)
        db_map_data = {}
        for db_map, class_ent_items in db_map_class_ent_items.items():
            data = db_map_data.setdefault(db_map, {})
            for class_name, ent_items in class_ent_items.items():
                data.setdefault("parameter_definitions", []).extend(
                    [(class_name, self.pos_x_parameter), (class_name, self.pos_y_parameter)]
                )
                data.setdefault("parameter_values", []).extend(
                    [
                        (class_name, item.element_name_list or item.name, pname, val)
                        for item in ent_items
                        for pname, val in zip(
                            (self.pos_x_parameter, self.pos_y_parameter),
                            self._spine_db_editor.convert_position(item.pos().x(), item.pos().y()),
                        )
                    ]
                )
        self.db_mngr.import_data(db_map_data)

    @Slot(bool)
    def _clear_selected_positions(self, checked=False):
        self._clear_positions(self.selected_items)

    @Slot(bool)
    def _clear_all_positions(self, checked=False):
        self._clear_positions(self.entity_items)

    def _clear_positions(self, items):
        if not items:
            return
        db_map_ids = {}
        for item in items:
            for db_map, entity_id in item.db_map_ids:
                db_map_ids.setdefault(db_map, set()).add(entity_id)
        db_map_typed_data = {}
        for db_map, ids in db_map_ids.items():
            db_map_typed_data[db_map] = {
                "parameter_value": set(
                    pv["id"]
                    for parameter_name in (self.pos_x_parameter, self.pos_y_parameter)
                    for pv in self.db_mngr.get_items_by_field(
                        db_map, "parameter_value", "parameter_name", parameter_name
                    )
                    if pv["entity_id"] in ids
                )
            }
        self.db_mngr.remove_items(db_map_typed_data)
        self._spine_db_editor.build_graph()

    @Slot(bool)
    def _select_bg_image(self, _checked=False):
        file_path = self._spine_db_editor.get_open_file_path(
            "addBgImage", "Select background image...", "SVG files (*.svg)"
        )
        if not file_path:
            return
        with open(file_path, "r") as fh:
            svg = fh.read().rstrip()
        self.set_bg_svg(svg)
        rect = self._get_viewport_scene_rect()
        self._bg_item.fit_rect(rect)
        self._bg_item.apply_zoom(self.zoom_factor)

    def set_bg_svg(self, svg):
        if self._bg_item is not None:
            self.scene().removeItem(self._bg_item)
        self._bg_item = BgItem(svg)
        self.scene().addItem(self._bg_item)

    def get_bg_svg(self):
        return self._bg_item.svg if self._bg_item else ""

    def set_bg_rect(self, rect):
        if self._bg_item is not None and rect:
            self._bg_item.fit_rect(rect)

    def get_bg_rect(self):
        if self._bg_item is not None:
            rect = self._bg_item.scene_rect()
            return rect.x(), rect.y(), rect.width(), rect.height()

    def clear_scene(self):
        for item in self.scene().items():
            if item.topLevelItem() is not item:
                continue
            if item is not self._bg_item:
                self.scene().removeItem(item)

    @contextmanager
    def _no_zoom(self):
        current_zoom_factor = self.zoom_factor
        self._zoom(1.0 / current_zoom_factor)
        try:
            yield
        finally:
            self._zoom(current_zoom_factor)

    @Slot(bool)
    def export_as_image(self, _=False):
        file_path = self._spine_db_editor.get_save_file_path(
            "exportGraphAsImage", "Export as image...", "SVG files (*.svg);;PDF files (*.pdf)"
        )
        if not file_path:
            return
        with self._no_zoom():
            self._do_export_as_image(file_path)
        self._spine_db_editor.file_exported.emit(file_path, 1.0, False)

    def _do_export_as_image(self, file_path):
        source = self._get_print_source()
        file_ext = os.path.splitext(file_path)[-1].lower()
        if not file_ext:
            file_ext = ".svg"
            file_path += file_ext
        if file_ext == ".svg":
            printer = QSvgGenerator()
            size = source.size().toSize()
            printer.setSize(size)
            printer.setViewBox(source.translated(-source.topLeft()))
            printer.setFileName(file_path)
        elif file_ext == ".pdf":
            printer = QPrinter()
            page_size = QPageSize(source.size(), QPageSize.Unit.Point)
            size = page_size.sizePixels(printer.resolution())
            printer.setPageSize(page_size)
            printer.setOutputFileName(file_path)
        else:
            size = source.size().toSize()
            printer = QPixmap(size)
            printer.fill(Qt.white)
        self._print_scene(printer, source, size)
        if isinstance(printer, QPixmap):
            printer.save(file_path)

    def _get_print_source(self, scene=None):
        if scene is None:
            scene = self.scene()
        source = scene.itemsBoundingRect().intersected(self._get_viewport_scene_rect())
        margin = self._margin * max(source.width(), source.height())
        bottom_margin_row_count = (
            self._spine_db_editor.ui.legend_widget.row_count()
            if self._spine_db_editor.ui.legend_widget.isVisible()
            else 1
        )
        source.adjust(-margin, -margin, margin, bottom_margin_row_count * margin)
        return source

    def _print_scene(self, printer, source, size, index=None, scene=None):
        if scene is None:
            scene = self.scene()
        painter = QPainter(printer)
        scene.render(painter, QRectF(), source)
        margin = self._margin * max(size.width(), size.height())
        if self._spine_db_editor.ui.legend_widget.isVisible():
            self._spine_db_editor.ui.legend_widget.row_count()
            legend_width = 0.5 * size.width()
            legend_height = self._spine_db_editor.ui.legend_widget.row_count() * margin
            legend_rect = QRectF(
                0.5 * (size.width() - legend_width), size.height() - legend_height, legend_width, legend_height
            )
            painter.fillRect(legend_rect, Qt.white)
            self._spine_db_editor.ui.legend_widget.paint(painter, legend_rect)
        if index is not None:
            height = 0.375 * margin
            font = painter.font()
            font.setPointSizeF(height)
            painter.setFont(font)
            text = str(index)
            rect = painter.boundingRect(source, text)
            left = 0.5 * (size.width() - rect.width())
            painter.fillRect(left, 0, rect.width(), rect.height(), Qt.white)
            painter.drawText(left, rect.height(), str(index))
        painter.end()

    def _clone_scene(self):
        scene = QGraphicsScene()
        entity_items = {item.db_map_ids: item.clone() for item in self.entity_items}
        arc_items = [item.clone(entity_items) for item in self.items() if isinstance(item, ArcItem)]
        for item in entity_items.values():
            scene.addItem(item)
        for item in arc_items:
            scene.addItem(item)
        if self._bg_item:
            scene.addItem(self._bg_item.clone())
        return scene, list(entity_items.values())

    def _frames(self, start, stop, step_len, buffer_path, cv2):
        if start == stop:
            return ()
        scene, entity_items = self._clone_scene()
        source = self._get_print_source(scene=scene)
        size = source.size().toSize()
        index = start
        mpeg4_max_extent = 2048
        pixmap = QPixmap(size)
        while True:
            pixmap.fill(Qt.white)
            for item in entity_items:
                item.update_props(index)
            self._print_scene(pixmap, source, size, index=index, scene=scene)
            ok = pixmap.scaled(mpeg4_max_extent, mpeg4_max_extent, Qt.KeepAspectRatio, Qt.SmoothTransformation).save(
                buffer_path
            )
            assert ok
            yield cv2.imread(buffer_path, -1)
            index += step_len
            if index > stop:
                break

    @Slot(bool)
    def export_as_video(self):
        try:
            import cv2
        except ModuleNotFoundError:
            self._spine_db_editor.msg_error.emit(
                "Export as video requires <a href='https://pypi.org/project/opencv-python/'>opencv-python</a>"
            )
            return
        file_path = self._spine_db_editor.get_save_file_path(
            "exportGraphAsVideo", "Export as video...", "All files (*);;MP4 files (*.mp4);;AVI files (*.avi)"
        )
        if not file_path:
            return
        start, stop = self._spine_db_editor.ui.time_line_widget.get_index_range()
        dialog = ExportAsVideoDialog(str(start), str(stop), parent=self)
        if dialog.exec_() == ExportAsVideoDialog.Rejected:
            return
        file_ext = os.path.splitext(file_path)[-1].lower()
        if not file_ext:
            file_ext = ".mp4"
            file_path += file_ext
        start, stop, step_len, fps = dialog.selections()
        start = np.datetime64(start)
        stop = np.datetime64(stop)
        step_len = np.timedelta64(step_len, "h")
        runnable = QRunnable.create(lambda: self._do_export_as_video(file_path, start, stop, step_len, fps, cv2))
        self._thread_pool.start(runnable)

    def _do_export_as_video(self, file_path, start, stop, step_len, fps, cv2):
        frame_count = (stop - start) // step_len
        with tempfile.NamedTemporaryFile() as f:
            buffer_path = f.name + ".png"
            frame_iter = enumerate(self._frames(start, stop, step_len, buffer_path, cv2))
            try:
                k, frame = next(frame_iter)
            except StopIteration:
                return
            height, width, _layers = frame.shape
            video = cv2.VideoWriter(file_path, cv2.VideoWriter_fourcc(*"XVID"), fps, (width, height))
            video.write(frame)
            self._spine_db_editor.file_exported.emit(file_path, k / frame_count, False)
            for k, frame in frame_iter:
                video.write(frame)
                self._spine_db_editor.file_exported.emit(file_path, k / frame_count, False)
        cv2.destroyAllWindows()
        video.release()
        self._spine_db_editor.file_exported.emit(file_path, 1.0, False)

    def set_cross_hairs_items(self, entity_class, cross_hairs_items):
        """Sets 'cross_hairs' items for connecting entities.

        Args:
            entity_class (dict)
            cross_hairs_items (list(QGraphicsItems))
        """
        self.entity_class = entity_class
        self.cross_hairs_items = cross_hairs_items
        for item in cross_hairs_items:
            self.scene().addItem(item)
            item.apply_zoom(self.zoom_factor)
        cursor_pos = self.mapFromGlobal(QCursor.pos())
        self._update_cross_hairs_pos(cursor_pos)
        self.viewport().setCursor(Qt.BlankCursor)

    def clear_cross_hairs_items(self):
        self.entity_class = None
        for item in self.cross_hairs_items:
            item.hide()
            item.scene().removeItem(item)
        self.cross_hairs_items.clear()
        self.viewport().unsetCursor()

    def _cross_hairs_has_valid_target(self):
        db_map = self.entity_class["db_map"]
        return any(
            id_ in self.entity_class["dimension_ids_to_go"] for id_ in self._hovered_ent_item.entity_class_ids(db_map)
        )

    def mousePressEvent(self, event):
        """Handles relationship creation if one it's in process."""
        if not self.cross_hairs_items:
            super().mousePressEvent(event)
            return
        if event.buttons() & Qt.RightButton or not self._hovered_ent_item:
            self.clear_cross_hairs_items()
            return
        if self._cross_hairs_has_valid_target():
            db_map = self.entity_class["db_map"]
            remove_first(self.entity_class["dimension_ids_to_go"], self._hovered_ent_item.entity_class_ids(db_map))
            if self.entity_class["dimension_ids_to_go"]:
                # Add hovered as member and keep going, we're not done yet
                ch_ent_item = self.cross_hairs_items[1]
                ch_arc_item = CrossHairsArcItem(ch_ent_item, self._hovered_ent_item, self._spine_db_editor._ARC_WIDTH)
                ch_ent_item.refresh_icon()
                self.scene().addItem(ch_arc_item)
                ch_arc_item.apply_zoom(self.zoom_factor)
                self.cross_hairs_items.append(ch_arc_item)
                return
            # Here we're done, add the relationships between the hovered and the members
            ch_item, _, *ch_arc_items = self.cross_hairs_items
            ent_items = [arc_item.el_item for arc_item in ch_arc_items]
            ent_items.remove(ch_item)
            self._spine_db_editor.finalize_connecting_entities(self.entity_class, self._hovered_ent_item, *ent_items)
            self.clear_cross_hairs_items()

    def mouseMoveEvent(self, event):
        """Updates the hovered object item if we're in entity creation mode."""
        if self.cross_hairs_items:
            self._update_cross_hairs_pos(event.position().toPoint())
            return
        super().mouseMoveEvent(event)

    def _update_cross_hairs_pos(self, pos):
        """Updates the hovered object item and sets the 'cross_hairs' icon accordingly.

        Args:
            pos (QPoint): the desired position in view coordinates
        """
        cross_hairs_item = self.cross_hairs_items[0]
        scene_pos = self.mapToScene(pos)
        delta = scene_pos - cross_hairs_item.scenePos()
        cross_hairs_item.move_by(delta.x(), delta.y())
        self._hovered_ent_item = None
        ent_items = (
            item for item in self.items(pos) if isinstance(item, EntityItem) and item not in self.cross_hairs_items
        )
        self._hovered_ent_item = next(ent_items, None)
        if self._hovered_ent_item is not None:
            if self._cross_hairs_has_valid_target():
                if len(self.entity_class["dimension_ids_to_go"]) == 1:
                    self.cross_hairs_items[0].set_check_icon()
                else:
                    self.cross_hairs_items[0].set_plus_icon()
                return
            self.cross_hairs_items[0].set_ban_icon()
            return
        self.cross_hairs_items[0].set_normal_icon()

    def mouseReleaseEvent(self, event):
        if not self.cross_hairs_items:
            super().mouseReleaseEvent(event)

    def keyPressEvent(self, event):
        """Aborts relationship creation if user presses ESC."""
        super().keyPressEvent(event)
        if event.key() == Qt.Key_Escape and self.cross_hairs_items:
            self._spine_db_editor.msg.emit("Relationship creation aborted.")
            self.clear_cross_hairs_items()

    def contextMenuEvent(self, e):
        """Shows context menu.

        Args:
            e (QContextMenuEvent): Context menu event
        """
        super().contextMenuEvent(e)
        if e.isAccepted():
            return
        e.accept()
        self._context_menu_pos = self.mapToScene(e.pos())
        self._menu.exec(e.globalPos())

    def _compute_max_zoom(self):
        return sys.maxsize

    def _use_smooth_zoom(self):
        return self._qsettings.value("appSettings/smoothEntityGraphZoom", defaultValue="false") == "true"

    def _zoom(self, factor):
        self.scale(factor, factor)
        self.apply_zoom()

    def apply_zoom(self):
        for item in self.items():
            if hasattr(item, "apply_zoom"):
                item.apply_zoom(self.zoom_factor)

    def wheelEvent(self, event):
        """Zooms in/out. If user has pressed the shift key, rotates instead.

        Args:
            event (QWheelEvent): Mouse wheel event
        """
        if event.modifiers() != Qt.ShiftModifier:
            super().wheelEvent(event)
            return
        event.accept()
        smooth_rotation = self._qsettings.value("appSettings/smoothEntityGraphRotation", defaultValue="false")
        if smooth_rotation == "true":
            num_degrees = event.delta() / 8
            num_steps = num_degrees / 15
            self._scheduled_transformations += num_steps
            if self._scheduled_transformations * num_steps < 0:
                self._scheduled_transformations = num_steps
            if self.time_line:
                self.time_line.deleteLater()
            self.time_line = QTimeLine(200, self)
            self.time_line.setUpdateInterval(20)
            self.time_line.valueChanged.connect(self._handle_rotation_time_line_advanced)
            self.time_line.finished.connect(self._handle_transformation_time_line_finished)
            self.time_line.start()
        else:
            angle = event.angleDelta().y() / 8
            self._rotate(angle)
            self._set_preferred_scene_rect()

    def _handle_rotation_time_line_advanced(self, pos):
        """Performs rotation whenever the smooth rotation time line advances."""
        angle = self._scheduled_transformations / 2.0
        self._rotate(angle)

    def _rotate(self, angle):
        center = self._get_viewport_scene_rect().center()
        for item in self.items():
            if hasattr(item, "apply_rotation"):
                item.apply_rotation(angle, center)

    def rotate_clockwise(self):
        """Performs a rotate clockwise with fixed angle."""
        self._rotate(-self._angle / 8)
        self._set_preferred_scene_rect()

    def rotate_anticlockwise(self):
        """Performs a rotate anticlockwise with fixed angle."""
        self._rotate(self._angle / 8)
        self._set_preferred_scene_rect()
