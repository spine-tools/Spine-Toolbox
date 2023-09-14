######################################################################################################################
# Copyright (C) 2017-2022 Spine project consortium
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""
Classes for custom QGraphicsViews for the Entity graph view.
"""

import os
import sys
from PySide6.QtCore import Qt, QTimeLine, Signal, Slot, QRectF
from PySide6.QtWidgets import QMenu, QGraphicsView, QInputDialog, QColorDialog
from PySide6.QtGui import QCursor, QPainter, QIcon, QAction, QPageSize
from PySide6.QtPrintSupport import QPrinter
from PySide6.QtSvg import QSvgGenerator
from ...helpers import CharIconEngine
from ...widgets.custom_qgraphicsviews import CustomQGraphicsView
from ...widgets.custom_qwidgets import ToolBarWidgetAction, HorizontalSpinBox
from ..graphics_items import EntityItem, CrossHairsArcItem, BgItem
from .select_graph_parameters_dialog import SelectGraphParametersDialog


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
        self._bg_item = None
        self.selected_items = []
        self.removed_items = set()
        self.hidden_items = {}
        self.pruned_db_map_entity_ids = {}
        self._hovered_ent_item = None
        self.entity_class = None
        self.cross_hairs_items = []
        self.auto_expand_entities = None
        self.merge_dbs = None
        self.max_entity_dimension = None
        self.disable_max_relationship_dimension = None
        self._auto_expand_entities_action = None
        self._merge_dbs_action = None
        self._max_ent_dim_action = None
        self._disable_max_ent_dim_action = None
        self._max_ent_dim_spin_box = None
        self._add_entities_action = None
        self._select_graph_params_action = None
        self._save_pos_action = None
        self._clear_pos_action = None
        self._hide_selected_action = None
        self._show_all_hidden_action = None
        self._prune_selected_action = None
        self._restore_all_pruned_action = None
        self._rebuild_action = None
        self._export_as_image_action = None
        self._zoom_action = None
        self._rotate_action = None
        self._arc_length_action = None
        self._find_action = None
        self._add_bg_image_action = None
        self._previous_mouse_pos = None
        self._context_menu_pos = None
        self._hide_classes_menu = None
        self._show_hidden_menu = None
        self._prune_classes_menu = None
        self._restore_pruned_menu = None
        self._items_per_class = {}

    @property
    def _qsettings(self):
        return self._spine_db_editor.qsettings

    @property
    def db_mngr(self):
        return self._spine_db_editor.db_mngr

    @property
    def entity_items(self):
        return [x for x in self.scene().items() if isinstance(x, EntityItem) and x not in self.removed_items]

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
        self.populate_context_menu()

    def populate_context_menu(self):
        self.auto_expand_entities = (
            self._qsettings.value("appSettings/autoExpandObjects", defaultValue="true") == "true"
        )
        self.merge_dbs = self._qsettings.value("appSettings/mergeDBs", defaultValue="true") == "true"
        self.max_entity_dimension = int(self._qsettings.value("appSettings/maxRelationshipDimension", defaultValue="2"))
        self.disable_max_relationship_dimension = (
            self._qsettings.value("appSettings/disableMaxRelationshipDimension", defaultValue="true") == "true"
        )
        self._auto_expand_entities_action = self._menu.addAction("Auto-expand entities")
        self._auto_expand_entities_action.setCheckable(True)
        self._auto_expand_entities_action.setChecked(self.auto_expand_entities)
        self._auto_expand_entities_action.triggered.connect(self._set_auto_expand_entities)
        self._merge_dbs_action = self._menu.addAction("Merge databases")
        self._merge_dbs_action.setCheckable(True)
        self._merge_dbs_action.setChecked(self.merge_dbs)
        self._merge_dbs_action.triggered.connect(self._set_merge_dbs)
        self._max_ent_dim_action = ToolBarWidgetAction("Max entity dimension", self._menu, compact=True)
        self._max_ent_dim_spin_box = HorizontalSpinBox(self)
        self._max_ent_dim_spin_box.setMinimum(2)
        self._max_ent_dim_spin_box.setValue(self.max_entity_dimension)
        self._max_ent_dim_spin_box.valueChanged.connect(self._set_max_relationship_dimension)
        self._max_ent_dim_action.tool_bar.addWidget(self._max_ent_dim_spin_box)
        self._max_ent_dim_action.tool_bar.addSeparator()
        self._disable_max_ent_dim_action = self._max_ent_dim_action.tool_bar.addAction("\u221E")
        self._disable_max_ent_dim_action.setCheckable(True)
        self._disable_max_ent_dim_action.toggled.connect(self._set_disable_max_relationship_dimension)
        self._disable_max_ent_dim_action.toggled.connect(self._max_ent_dim_spin_box.setDisabled)
        self._disable_max_ent_dim_action.setToolTip("No limit")
        self._disable_max_ent_dim_action.setChecked(self.disable_max_relationship_dimension)
        self._menu.addAction(self._max_ent_dim_action)
        self._menu.addSeparator()
        self._add_entities_action = self._menu.addAction("Add entities...", self.add_entities_at_position)
        self._menu.addSeparator()
        self._find_action = self._menu.addAction("Find...", self._find)
        self._menu.addAction(self._find_action)
        self._menu.addSeparator()
        self._select_graph_params_action = self._menu.addAction(
            "Select graph parameters...", self.select_graph_parameters
        )
        self._save_pos_action = self._menu.addAction("Save positions", self.save_positions)
        self._clear_pos_action = self._menu.addAction("Clear saved positions", self.clear_saved_positions)
        self._menu.addSeparator()
        self._hide_selected_action = self._menu.addAction("Hide selected", self.hide_selected_items)
        self._hide_classes_menu = self._menu.addMenu("Hide classes")
        self._hide_classes_menu.triggered.connect(self._hide_class)
        self._show_hidden_menu = self._menu.addMenu("Show")
        self._show_hidden_menu.triggered.connect(self.show_hidden_items)
        self._show_all_hidden_action = self._menu.addAction("Show all", self.show_all_hidden_items)
        self._menu.addSeparator()
        self._prune_selected_action = self._menu.addAction("Prune selected", self.prune_selected_items)
        self._prune_classes_menu = self._menu.addMenu("Prune classes")
        self._prune_classes_menu.triggered.connect(self._prune_class)
        self._restore_pruned_menu = self._menu.addMenu("Restore")
        self._restore_pruned_menu.triggered.connect(self.restore_pruned_items)
        self._restore_all_pruned_action = self._menu.addAction("Restore all", self.restore_all_pruned_items)
        self._menu.addSeparator()
        self._add_bg_image_action = self._menu.addAction("Select background image...", self._add_bg_image)
        self._menu.addSeparator()
        self._rebuild_action = self._menu.addAction("Rebuild", self._spine_db_editor.rebuild_graph)
        self._export_as_image_action = self._menu.addAction("Export as vector image...", self.export_as_image)
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
        self._menu.aboutToShow.connect(self._update_actions_visibility)

    def _find(self):
        expr, ok = QInputDialog.getText(self, "Find in graph...", "Enter entity names to find separated by comma.")
        if not ok:
            return
        names = [x.strip() for x in expr.split(",")]
        items = [item for item in self.entity_items if any(n == item.entity_name for n in names)]
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

    @Slot()
    def _update_actions_visibility(self):
        """Enables or disables actions according to current selection in the graph."""
        has_graph = bool(self.items())
        self._save_pos_action.setEnabled(bool(self.selected_items))
        self._clear_pos_action.setEnabled(bool(self.selected_items))
        self._hide_selected_action.setEnabled(bool(self.selected_items))
        self._show_hidden_menu.setEnabled(any(self.hidden_items.values()))
        self._show_all_hidden_action.setEnabled(bool(self.hidden_items))
        self._prune_selected_action.setEnabled(bool(self.selected_items))
        self._restore_pruned_menu.setEnabled(any(self.pruned_db_map_entity_ids.values()))
        self._restore_all_pruned_action.setEnabled(any(self.pruned_db_map_entity_ids.values()))
        self._prune_selected_action.setText(f"Prune {self._get_selected_entity_names()}")
        self._rebuild_action.setEnabled(has_graph)
        self._zoom_action.setEnabled(has_graph)
        self._rotate_action.setEnabled(has_graph)
        self._find_action.setEnabled(has_graph)
        self._export_as_image_action.setEnabled(has_graph)
        self._items_per_class = {}
        for item in self.entity_items:
            key = f"{item.entity_class_name}"
            self._items_per_class.setdefault(key, list()).append(item)
        self._hide_classes_menu.clear()
        self._hide_classes_menu.setEnabled(bool(self._items_per_class))
        self._prune_classes_menu.clear()
        self._prune_classes_menu.setEnabled(bool(self._items_per_class))
        for key in sorted(self._items_per_class.keys() - self.hidden_items.keys()):
            self._hide_classes_menu.addAction(key)
        for key in sorted(self._items_per_class.keys() - self.pruned_db_map_entity_ids.keys()):
            self._prune_classes_menu.addAction(key)

    def make_items_menu(self):
        menu = QMenu(self)
        menu.addAction(self._save_pos_action)
        menu.addAction(self._clear_pos_action)
        menu.addSeparator()
        menu.addAction(self._hide_selected_action)
        menu.addAction(self._prune_selected_action)
        menu.addSeparator()
        menu.addAction("Edit", self.edit_selected)
        menu.addAction("Remove", self.remove_selected)
        menu.aboutToShow.connect(self._update_actions_visibility)
        return menu

    @Slot(bool)
    def _set_auto_expand_entities(self, _checked=False, save_setting=True):
        checked = self._auto_expand_entities_action.isChecked()
        if checked == self.auto_expand_entities:
            return
        if save_setting:
            self._qsettings.setValue("appSettings/autoExpandObjects", "true" if checked else "false")
        self.auto_expand_entities = checked
        self._spine_db_editor.build_graph()

    def set_auto_expand_entities(self, checked):
        self._auto_expand_entities_action.setChecked(checked)
        self._set_auto_expand_entities(save_setting=False)

    @Slot(bool)
    def _set_merge_dbs(self, _checked=False, save_setting=True):
        checked = self._merge_dbs_action.isChecked()
        if checked == self.merge_dbs:
            return
        if save_setting:
            self._qsettings.setValue("appSettings/mergeDBs", "true" if checked else "false")
        self.merge_dbs = checked
        self._spine_db_editor.build_graph()

    def set_merge_dbs(self, checked):
        self._merge_dbs_action.setChecked(checked)
        self._set_merge_dbs(save_setting=False)

    @Slot(bool)
    def _set_disable_max_relationship_dimension(self, _checked=False, save_setting=True):
        checked = self._disable_max_ent_dim_action.isChecked()
        if checked == self.disable_max_relationship_dimension:
            return
        if save_setting:
            self._qsettings.setValue("appSettings/disableMaxRelationshipDimension", "true" if checked else "false")
        self.disable_max_relationship_dimension = checked
        self._spine_db_editor.build_graph()

    def set_disable_max_relationship_dimension(self, checked):
        self._disable_max_ent_dim_action.setChecked(checked)
        self._set_disable_max_relationship_dimension(save_setting=False)

    @Slot(int)
    def _set_max_relationship_dimension(self, _value=None, save_setting=True):
        value = self._max_ent_dim_spin_box.value()
        if value == self.max_entity_dimension:
            return
        if save_setting:
            self._qsettings.setValue("appSettings/maxRelationshipDimension", str(value))
        self.max_entity_dimension = value
        self._spine_db_editor.build_graph()

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
        names = "'" + self.selected_items[0].entity_name + "'"
        if len(self.selected_items) > 1:
            names += f" and {len(self.selected_items) - 1} other entities"
        return names

    @Slot(bool)
    def hide_selected_items(self, checked=False):
        """Hides selected items."""
        key = self._get_selected_entity_names()
        self.hidden_items[key] = self.selected_items
        self._show_hidden_menu.addAction(key)
        for item in self.selected_items:
            item.setVisible(False)

    @Slot(QAction)
    def _hide_class(self, action):
        """Hides some class."""
        key = action.text()
        items = self._items_per_class[key]
        self.hidden_items[key] = items
        self._show_hidden_menu.addAction(key)
        for item in items:
            item.setVisible(False)

    @Slot(bool)
    def show_all_hidden_items(self, checked=False):
        """Shows all hidden items."""
        if not self.scene():
            return
        self._show_hidden_menu.clear()
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
            action = next(iter(a for a in self._show_hidden_menu.actions() if a.text() == key))
            self._show_hidden_menu.removeAction(action)
            for item in items:
                item.setVisible(True)

    @Slot(bool)
    def prune_selected_items(self, checked=False):
        """Prunes selected items."""
        entity_ids = {db_map_id for x in self.selected_items for db_map_id in x.db_map_ids}
        key = self._get_selected_entity_names()
        self.pruned_db_map_entity_ids[key] = entity_ids
        self._restore_pruned_menu.addAction(key)
        self._spine_db_editor.build_graph()

    @Slot(QAction)
    def _prune_class(self, action):
        """Prunnes some class."""
        key = action.text()
        self.pruned_db_map_entity_ids[key] = {
            (db_map, x["id"])
            for item in self._items_per_class[key]
            for db_map in item.db_maps
            for x in self.db_mngr.get_items_by_field(
                db_map, "entity", "class_id", item.entity_class_id(db_map), only_visible=False
            )
        }
        self._restore_pruned_menu.addAction(key)
        self._spine_db_editor.build_graph()

    @Slot(bool)
    def restore_all_pruned_items(self, checked=False):
        """Reinstates all pruned items."""
        self.pruned_db_map_entity_ids.clear()
        self._restore_pruned_menu.clear()
        self._spine_db_editor.build_graph()

    @Slot(QAction)
    def restore_pruned_items(self, action):
        """Reinstates some pruned items."""
        key = action.text()
        if self.pruned_db_map_entity_ids.pop(key, None) is not None:
            action = next(iter(a for a in self._restore_pruned_menu.actions() if a.text() == key))
            self._restore_pruned_menu.removeAction(action)
            self._spine_db_editor.build_graph()

    @Slot(bool)
    def select_graph_parameters(self, checked=False):
        dialog = SelectGraphParametersDialog(
            self._spine_db_editor,
            self.name_parameter,
            self.pos_x_parameter,
            self.pos_y_parameter,
            self.color_parameter,
            self.arc_width_parameter,
        )
        dialog.show()
        dialog.selection_made.connect(self._set_graph_parameters)

    @Slot(str, str, str, str, str)
    def _set_graph_parameters(
        self, name_parameter, pos_x_parameter, pos_y_parameter, color_parameter, arc_width_parameter
    ):
        self.name_parameter = name_parameter
        self.pos_x_parameter = pos_x_parameter
        self.pos_y_parameter = pos_y_parameter
        self.color_parameter = color_parameter
        self.arc_width_parameter = arc_width_parameter
        self._spine_db_editor.polish_items()

    @Slot(bool)
    def save_positions(self, checked=False):
        if not self.pos_x_parameter or not self.pos_y_parameter:
            msg = "You haven't selected the position parameters. Please go to Graph -> Select position parameters"
            self._spine_db_editor.msg.emit(msg)
            return
        ent_items = [item for item in self.selected_items if isinstance(item, EntityItem)]
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
                        (class_name, item.element_name_list or item.entity_name, pname, val)
                        for item in ent_items
                        for pname, val in zip(
                            (self.pos_x_parameter, self.pos_y_parameter),
                            self._spine_db_editor.convert_position(item.pos().x(), item.pos().y()),
                        )
                    ]
                )
        self.db_mngr.import_data(db_map_data)

    @Slot(bool)
    def clear_saved_positions(self, checked=False):
        if not self.selected_items:
            return
        db_map_ids = {}
        for item in self.selected_items:
            db_map_ids.setdefault(item.db_map, set()).add(item.entity_id)
        db_map_typed_data = {}
        for db_map, ids in db_map_ids.items():
            db_map_typed_data[db_map] = {
                "parameter_value": set(
                    pv["id"]
                    for parameter_name in (self.pos_x_parameter, self.pos_y_parameter)
                    for pv in self.db_mngr.get_items_by_field(
                        db_map, "parameter_value", "parameter_name", parameter_name, only_visible=False
                    )
                    if pv["entity_id"] in ids
                )
            }
        self.db_mngr.remove_items(db_map_typed_data)
        self._spine_db_editor.build_graph()

    @Slot(bool)
    def _add_bg_image(self, _checked=False):
        file_path = self._spine_db_editor.get_open_file_path(
            "addBgImage", "Select background image...", "SVG files (*.svg)"
        )
        if not file_path:
            return
        if self._bg_item is not None:
            self.scene().removeItem(self._bg_item)
        self._bg_item = BgItem(file_path)
        self.scene().addItem(self._bg_item)
        rect = self._get_viewport_scene_rect()
        self._bg_item.fit_rect(rect)
        self._bg_item.apply_zoom(self.zoom_factor)

    def clear_scene(self):
        for item in self.scene().items():
            if item.topLevelItem() is not item:
                continue
            if item is not self._bg_item:
                self.scene().removeItem(item)

    @Slot(bool)
    def export_as_image(self, _=False):
        file_path = self._spine_db_editor.get_save_file_path(
            "exportGraphAsImage", "Export as vector image...", "SVG files (*.svg);;PDF files (*.pdf)"
        )
        if not file_path:
            return
        # source = self._get_viewport_scene_rect()
        source = self.scene().itemsBoundingRect()
        margin = 0.05
        dx, dy = margin * source.width(), margin * source.height()
        source.adjust(-dx, -dy, dx, dy)
        current_zoom_factor = self.zoom_factor
        self._zoom(1.0 / current_zoom_factor)
        self.scene().clearSelection()
        file_ext = os.path.splitext(file_path)[-1]
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
        painter = QPainter(printer)
        self.scene().render(painter, QRectF(), source)
        if self._spine_db_editor.ui.legend_widget.isVisible():
            legend_width, legend_height = 0.5 * size.width(), 0.5 * margin * size.height()
            legend_rect = QRectF(
                0.5 * (size.width() - legend_width),
                size.height() - 0.5 * margin * size.height() - 0.5 * legend_height,
                legend_width,
                legend_height,
            )
            self._spine_db_editor.ui.legend_widget.paint(painter, legend_rect)
        painter.end()
        self._zoom(current_zoom_factor)
        self._spine_db_editor.file_exported.emit(file_path)

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
        return self._hovered_ent_item.entity_class_id(db_map) in self.entity_class["dimension_ids_to_go"]

    def mousePressEvent(self, event):
        """Handles relationship creation if one it's in process."""
        self._previous_mouse_pos = event.position().toPoint()
        if not self.cross_hairs_items:
            super().mousePressEvent(event)
            return
        if event.buttons() & Qt.RightButton or not self._hovered_ent_item:
            self.clear_cross_hairs_items()
            return
        if self._cross_hairs_has_valid_target():
            db_map = self.entity_class["db_map"]
            self.entity_class["dimension_ids_to_go"].remove(self._hovered_ent_item.entity_class_id(db_map))
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
        if (
            not self.itemAt(event.position().toPoint())
            and (event.buttons() & Qt.LeftButton)
            and self.dragMode() != QGraphicsView.DragMode.RubberBandDrag
        ):
            if self._previous_mouse_pos is not None:
                delta = event.position().toPoint() - self._previous_mouse_pos
                self._scroll_scene_by(delta.x(), delta.y())
            self._previous_mouse_pos = event.position().toPoint()

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
        ent_items = [
            item for item in self.items(pos) if isinstance(item, EntityItem) and item is not self.cross_hairs_items[0]
        ]
        self._hovered_ent_item = next(iter(ent_items), None)
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
        self._previous_mouse_pos = None
        if not self.cross_hairs_items:
            super().mouseReleaseEvent(event)

    def _scroll_scene_by(self, dx, dy):
        if dx == dy == 0:
            return
        scene_rect = self.sceneRect()
        view_scene_rect = self.mapFromScene(scene_rect).boundingRect()
        view_rect = self.viewport().rect()
        scene_dx = abs((self.mapToScene(0, 0) - self.mapToScene(dx, 0)).x())
        scene_dy = abs((self.mapToScene(0, 0) - self.mapToScene(0, dy)).y())
        if dx < 0 and view_rect.right() - dx >= view_scene_rect.right():
            scene_rect.adjust(0, 0, scene_dx, 0)
        elif dx > 0 and view_rect.left() - dx <= view_scene_rect.left():
            scene_rect.adjust(-scene_dx, 0, 0, 0)
        if dy < 0 and view_rect.bottom() - dy >= view_scene_rect.bottom():
            scene_rect.adjust(0, 0, 0, scene_dy)
        elif dy > 0 and view_rect.top() - dy <= view_scene_rect.top():
            scene_rect.adjust(0, -scene_dy, 0, 0)
        self.scene().setSceneRect(scene_rect)

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
