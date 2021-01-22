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
Classes for custom QGraphicsViews for the Entity graph view.

:authors: P. Savolainen (VTT), M. Marin (KTH)
:date:   6.2.2018
"""

from PySide2.QtCore import Qt, QTimeLine, Signal, Slot, QRectF
from PySide2.QtWidgets import QMenu
from PySide2.QtGui import QCursor, QPainter
from PySide2.QtPrintSupport import QPrinter
from ...widgets.custom_qgraphicsviews import CustomQGraphicsView
from ...widgets.custom_qwidgets import ToolbarWidgetAction
from ..graphics_items import EntityItem, ObjectItem, RelationshipItem, CrossHairsArcItem, make_figure_graphics_item
from .select_position_parameters_dialog import SelectPositionParametersDialog
from .graph_layout_generator import make_heat_map


class EntityQGraphicsView(CustomQGraphicsView):
    """QGraphicsView for the Entity Graph View."""

    graph_selection_changed = Signal(object)

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
        self.selected_items = list()
        self.removed_items = list()
        self.hidden_items = list()
        self.prunned_entity_ids = dict()
        self.heat_map_items = list()
        self._point_value_tuples_per_parameter_name = dict()  # Used in the heat map menu
        self._hovered_obj_item = None
        self.relationship_class = None
        self.cross_hairs_items = []
        self.show_cascading_relationships = None
        self._show_cascading_relationships_action = None
        self._save_pos_action = None
        self._clear_pos_action = None
        self._hide_action = None
        self._show_hidden_action = None
        self._prune_entities_action = None
        self._prune_classes_action = None
        self._restore_all_pruned_action = None
        self._rebuild_action = None
        self._export_as_pdf_action = None
        self._zoom_action = None
        self._rotate_action = None
        self._restore_pruned_menu = None
        self._parameter_heat_map_menu = None

    @property
    def entity_items(self):
        return [x for x in self.scene().items() if isinstance(x, EntityItem) and x not in self.removed_items]

    def setScene(self, scene):
        super().setScene(scene)
        scene.selectionChanged.connect(self._handle_scene_selection_changed)

    @Slot()
    def _handle_scene_selection_changed(self):
        """Filters parameters by selected objects in the graph."""
        if self.scene() is None:
            return
        selected_items = self.scene().selectedItems()
        selected_objs = [x for x in selected_items if isinstance(x, ObjectItem)]
        selected_rels = [x for x in selected_items if isinstance(x, RelationshipItem)]
        self.selected_items = selected_objs + selected_rels
        self.graph_selection_changed.emit({"object": selected_objs, "relationship": selected_rels})

    def connect_spine_db_editor(self, spine_db_editor):
        self._spine_db_editor = spine_db_editor
        self.populate_context_menu()

    def populate_context_menu(self):
        self._show_cascading_relationships_action = self._menu.addAction("Show cascading relationship")
        self._show_cascading_relationships_action.setCheckable(True)
        self.show_cascading_relationships = (
            self._spine_db_editor.qsettings.value("appSettings/showCascadingRelationships", defaultValue="false")
            == "true"
        )
        self._show_cascading_relationships_action.setChecked(self.show_cascading_relationships)
        self._show_cascading_relationships_action.toggled.connect(self.set_show_cascading_relationships)
        self._menu.addSeparator()
        self._save_pos_action = self._menu.addAction("Save positions", self.save_positions)
        self._clear_pos_action = self._menu.addAction("Clear saved positions", self.clear_saved_positions)
        self._menu.addSeparator()
        self._hide_action = self._menu.addAction("Hide", self.hide_selected_items)
        self._show_hidden_action = self._menu.addAction("Show hidden", self.show_hidden_items)
        self._menu.addSeparator()
        self._prune_entities_action = self._menu.addAction("Prune entities", self.prune_selected_entities)
        self._prune_classes_action = self._menu.addAction("Prune classes", self.prune_selected_classes)
        self._restore_pruned_menu = self._menu.addMenu("Restore")
        self._restore_pruned_menu.triggered.connect(self.restore_pruned_items)
        self._restore_all_pruned_action = self._menu.addAction("Restore all", self.restore_all_pruned_items)
        self._menu.addSeparator()
        # FIXME: The heap map doesn't seem to be working nicely
        # self._parameter_heat_map_menu = self._menu.addMenu("Add heat map")
        # self._parameter_heat_map_menu.triggered.connect(self.add_heat_map)
        self._menu.addSeparator()
        self._rebuild_action = self._menu.addAction("Rebuild", self._spine_db_editor.build_graph)
        self._export_as_pdf_action = self._menu.addAction("Export as PDF", self.export_as_pdf)
        self._menu.addSeparator()
        self._zoom_action = ToolbarWidgetAction("Zoom", self._menu, compact=True)
        self._zoom_action.tool_bar.addAction("-", self.zoom_out).setToolTip("Zoom out")
        self._zoom_action.tool_bar.addAction("Reset", self.reset_zoom).setToolTip("Reset zoom")
        self._zoom_action.tool_bar.addAction("+", self.zoom_in).setToolTip("Zoom in")
        self._rotate_action = ToolbarWidgetAction("Rotate", self._menu, compact=True)
        self._rotate_action.tool_bar.addAction("\u2b6f", self.rotate_anticlockwise).setToolTip(
            "Rotate counter-clockwise"
        )
        self._rotate_action.tool_bar.addAction("\u2b6e", self.rotate_clockwise).setToolTip("Rotate clockwise")
        self._menu.addSeparator()
        self._menu.addAction(self._zoom_action)
        self._menu.addSeparator()
        self._menu.addAction(self._rotate_action)
        self._menu.aboutToShow.connect(self._update_actions_visibility)

    @Slot()
    def _update_actions_visibility(self):
        """Enables or disables actions according to current selection in the graph."""
        self._save_pos_action.setEnabled(bool(self.selected_items))
        self._clear_pos_action.setEnabled(bool(self.selected_items))
        self._hide_action.setEnabled(bool(self.selected_items))
        self._show_hidden_action.setEnabled(bool(self.hidden_items))
        self._prune_entities_action.setEnabled(bool(self.selected_items))
        self._prune_classes_action.setEnabled(bool(self.selected_items))
        self._restore_pruned_menu.setEnabled(any(self.prunned_entity_ids.values()))
        self._restore_all_pruned_action.setEnabled(any(self.prunned_entity_ids.values()))
        self._prune_entities_action.setText(f"Prune {self._get_selected_entity_names()}")
        self._prune_classes_action.setText(f"Prune {self._get_selected_class_names()}")
        has_graph = bool(self.items())
        self._rebuild_action.setEnabled(has_graph)
        self._zoom_action.setEnabled(has_graph)
        self._rotate_action.setEnabled(has_graph)
        self._export_as_pdf_action.setEnabled(has_graph)
        # FIXME: The heap map doesn't seem to be working nicely
        # self._parameter_heat_map_menu.setEnabled(has_graph)
        # if has_graph:
        #    self._populate_add_heat_map_menu()

    def make_items_menu(self):
        menu = QMenu(self)
        menu.addAction(self._save_pos_action)
        menu.addAction(self._clear_pos_action)
        menu.addSeparator()
        menu.addAction(self._hide_action)
        menu.addAction(self._prune_entities_action)
        menu.addAction(self._prune_classes_action)
        menu.addSeparator()
        menu.addAction("Edit", self.edit_selected)
        menu.addAction("Remove", self.remove_selected)
        menu.aboutToShow.connect(self._update_actions_visibility)
        return menu

    @Slot(bool)
    def edit_selected(self, _=False):
        """Edits selected items."""
        obj_items = [item for item in self.selected_items if isinstance(item, ObjectItem)]
        rel_items = [item for item in self.selected_items if isinstance(item, RelationshipItem)]
        self._spine_db_editor.show_edit_objects_form(obj_items)
        self._spine_db_editor.show_edit_relationships_form(rel_items)

    @Slot(bool)
    def remove_selected(self, _=False):
        """Removes selected items."""
        if not self.selected_items:
            return
        db_map_typed_data = {}
        for item in self.selected_items:
            db_map, entity_id = item.db_map_entity_id
            db_map_typed_data.setdefault(db_map, {}).setdefault(item.entity_type, set()).add(entity_id)
        self._spine_db_editor.db_mngr.remove_items(db_map_typed_data)

    @Slot(bool)
    def set_show_cascading_relationships(self, checked=False):
        self.show_cascading_relationships = checked
        self._show_cascading_relationships_action.setChecked(checked)
        self._spine_db_editor.build_graph()

    @Slot(bool)
    def hide_selected_items(self, checked=False):
        """Hides selected items."""
        self.hidden_items.extend(self.selected_items)
        for item in self.selected_items:
            item.set_all_visible(False)

    @Slot(bool)
    def show_hidden_items(self, checked=False):
        """Shows hidden items."""
        if not self.scene():
            return
        for item in self.hidden_items:
            item.set_all_visible(True)
        self.hidden_items.clear()

    def _get_selected_entity_names(self):
        if len(self.selected_items) == 1:
            return "'" + self.selected_items[0].entity_name + "'"
        return "selected entities"

    def _get_selected_class_names(self):
        if len(self.selected_items) == 1:
            return "'" + self.selected_items[0].entity_class_name + "'"
        return "selected classes"

    @Slot(bool)
    def prune_selected_entities(self, checked=False):
        """Prunes selected items."""
        entity_ids = {x.db_map_entity_id for x in self.selected_items}
        key = self._get_selected_entity_names()
        self.prunned_entity_ids[key] = entity_ids
        self._restore_pruned_menu.addAction(key)
        self._spine_db_editor.build_graph()

    @Slot(bool)
    def prune_selected_classes(self, checked=False):
        """Prunes selected items."""
        db_map_class_ids = {}
        for x in self.selected_items:
            db_map_class_ids.setdefault(x.db_map, set()).add(x.entity_class_id)
        entity_ids = {
            (db_map, x["id"])
            for db_map, class_ids in db_map_class_ids.items()
            for x in self._spine_db_editor.db_mngr.get_items(db_map, "object")
            if x["class_id"] in class_ids
        }
        entity_ids |= {
            (db_map, x["id"])
            for db_map, class_ids in db_map_class_ids.items()
            for x in self._spine_db_editor.db_mngr.get_items(db_map, "relationship")
            if x["class_id"] in class_ids
        }
        key = self._get_selected_class_names()
        self.prunned_entity_ids[key] = entity_ids
        self._restore_pruned_menu.addAction(key)
        self._spine_db_editor.build_graph()

    @Slot(bool)
    def restore_all_pruned_items(self, checked=False):
        """Reinstates all pruned items."""
        self.prunned_entity_ids.clear()
        self._spine_db_editor.build_graph()

    @Slot("QAction")
    def restore_pruned_items(self, action):
        """Reinstates last pruned items."""
        key = action.text()
        if self.prunned_entity_ids.pop(key, None) is not None:
            action = next(iter(a for a in self._restore_pruned_menu.actions() if a.text() == key))
            self._restore_pruned_menu.removeAction(action)
            self._spine_db_editor.build_graph()

    @Slot(bool)
    def select_position_parameters(self, checked=False):
        dialog = SelectPositionParametersDialog(self._spine_db_editor)
        dialog.show()
        dialog.selection_made.connect(self._set_position_parameters)

    @Slot(str, str)
    def _set_position_parameters(self, parameter_pos_x, parameter_pos_y):
        self.pos_x_parameter = parameter_pos_x
        self.pos_y_parameter = parameter_pos_y

    @Slot(bool)
    def save_positions(self, checked=False):
        if not self.pos_x_parameter or not self.pos_y_parameter:
            msg = "You haven't selected the position parameters. Please go to Graph -> Select position parameters"
            self._spine_db_editor.msg.emit(msg)
            return
        obj_items = [item for item in self.selected_items if isinstance(item, ObjectItem)]
        rel_items = [item for item in self.selected_items if isinstance(item, RelationshipItem)]
        db_map_class_obj_items = {}
        db_map_class_rel_items = {}
        for item in obj_items:
            db_map_class_obj_items.setdefault(item.db_map, {}).setdefault(item.entity_class_name, []).append(item)
        for item in rel_items:
            db_map_class_rel_items.setdefault(item.db_map, {}).setdefault(item.entity_class_name, []).append(item)
        db_map_data = {}
        for db_map, class_obj_items in db_map_class_obj_items.items():
            data = db_map_data.setdefault(db_map, {})
            for class_name, obj_items in class_obj_items.items():
                data["object_parameters"] = [(class_name, self.pos_x_parameter), (class_name, self.pos_y_parameter)]
                data["object_parameter_values"] = [
                    (class_name, item.entity_name, self.pos_x_parameter, item.pos().x()) for item in obj_items
                ] + [(class_name, item.entity_name, self.pos_y_parameter, item.pos().y()) for item in obj_items]
        for db_map, class_rel_items in db_map_class_rel_items.items():
            data = db_map_data.setdefault(db_map, {})
            for class_name, rel_items in class_rel_items.items():
                data["relationship_parameters"] = [
                    (class_name, self.pos_x_parameter),
                    (class_name, self.pos_y_parameter),
                ]
                data["relationship_parameter_values"] = [
                    (class_name, item.object_name_list.split(","), self.pos_x_parameter, item.pos().x())
                    for item in rel_items
                ] + [
                    (class_name, item.object_name_list.split(","), self.pos_y_parameter, item.pos().y())
                    for item in rel_items
                ]
        self._spine_db_editor.db_mngr.import_data(db_map_data)

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
                    for pv in self._spine_db_editor.db_mngr.get_items_by_field(
                        db_map, "parameter_value", "parameter_name", parameter_name
                    )
                    if pv["entity_id"] in ids
                )
            }
        self._spine_db_editor.db_mngr.remove_items(db_map_typed_data)
        self._spine_db_editor.build_graph()

    @Slot(bool)
    def export_as_pdf(self, checked=False):
        file_path = self._spine_db_editor.get_pdf_file_path()
        if not file_path:
            return
        source = self._get_viewport_scene_rect()
        current_zoom_factor = self.zoom_factor
        self._zoom(1.0 / current_zoom_factor)
        self.scene().clearSelection()
        printer = QPrinter()
        printer.setPaperSize(source.size(), QPrinter.Point)
        printer.setOutputFileName(file_path)
        painter = QPainter(printer)
        self.scene().render(painter, QRectF(), source)
        painter.end()
        self._zoom(current_zoom_factor)
        self._spine_db_editor.file_exported.emit(file_path)

    def _populate_add_heat_map_menu(self):
        """Populates the menu 'Add heat map' with parameters for currently shown items in the graph."""
        db_map_class_ids = {}
        for item in self.entity_items:
            db_map_class_ids.setdefault(item.db_map, set()).add(item.entity_class_id)
        db_map_parameters = self._spine_db_editor.db_mngr.find_cascading_parameter_data(
            db_map_class_ids, "parameter_definition"
        )
        db_map_class_parameters = {}
        parameter_value_ids = {}
        for db_map, parameters in db_map_parameters.items():
            for p in parameters:
                db_map_class_parameters.setdefault((db_map, p["entity_class_id"]), []).append(p)
            parameter_value_ids = {
                (db_map, pv["parameter_id"], pv["entity_id"]): pv["id"]
                for pv in self._spine_db_editor.db_mngr.find_cascading_parameter_values_by_definition(
                    {db_map: {x["id"] for x in parameters}}
                )[db_map]
            }
        self._point_value_tuples_per_parameter_name.clear()
        for item in self.entity_items:
            for parameter in db_map_class_parameters.get((item.db_map, item.entity_class_id), ()):
                pv_id = parameter_value_ids.get((item.db_map, parameter["id"], item.entity_id))
                try:
                    value = float(self._spine_db_editor.db_mngr.get_value(item.db_map, "parameter_value", pv_id))
                    pos = item.pos()
                    self._point_value_tuples_per_parameter_name.setdefault(parameter["parameter_name"], []).append(
                        (pos.x(), -pos.y(), value)
                    )
                except (TypeError, ValueError):
                    pass
        self._parameter_heat_map_menu.clear()
        for name, point_value_tuples in self._point_value_tuples_per_parameter_name.items():
            if len(point_value_tuples) > 1:
                self._parameter_heat_map_menu.addAction(name)
        self._parameter_heat_map_menu.setDisabled(self._parameter_heat_map_menu.isEmpty())

    @Slot("QAction")
    def add_heat_map(self, action):
        """Adds heat map for the parameter in the action text.
        """
        self._clean_up_heat_map_items()
        point_value_tuples = self._point_value_tuples_per_parameter_name[action.text()]
        x, y, values = zip(*point_value_tuples)
        heat_map, xv, yv, min_x, min_y, max_x, max_y = make_heat_map(x, y, values)
        heat_map_item, hm_figure = make_figure_graphics_item(self.scene(), z=-3, static=True)
        colorbar_item, cb_figure = make_figure_graphics_item(self.scene(), z=3, static=False)
        colormesh = hm_figure.gca().pcolormesh(xv, yv, heat_map)
        cb_figure.colorbar(colormesh, fraction=1)
        cb_figure.gca().set_visible(False)
        width = max_x - min_x
        height = max_y - min_y
        heat_map_item.widget().setGeometry(min_x, min_y, width, height)
        extent = self._spine_db_editor.VERTEX_EXTENT
        colorbar_item.widget().setGeometry(max_x + extent, min_y, 2 * extent, height)
        self.heat_map_items += [heat_map_item, colorbar_item]

    def _clean_up_heat_map_items(self):
        for item in self.heat_map_items:
            item.hide()
            self.scene().removeItem(item)
        self.heat_map_items.clear()

    def set_cross_hairs_items(self, relationship_class, cross_hairs_items):
        """Sets 'cross_hairs' items for relationship creation.

        Args:
            relationship_class (dict)
            cross_hairs_items (list(QGraphicsItems))
        """
        self.relationship_class = relationship_class
        self.cross_hairs_items = cross_hairs_items
        for item in cross_hairs_items:
            self.scene().addItem(item)
            item.apply_zoom(self.zoom_factor)
        cursor_pos = self.mapFromGlobal(QCursor.pos())
        self._update_cross_hairs_pos(cursor_pos)
        self.viewport().setCursor(Qt.BlankCursor)

    def clear_cross_hairs_items(self):
        self.relationship_class = None
        for item in self.cross_hairs_items:
            item.hide()
            item.scene().removeItem(item)
        self.cross_hairs_items.clear()
        self.viewport().unsetCursor()

    def _cross_hairs_has_valid_taget(self):
        return (
            self._hovered_obj_item.db_map == self.cross_hairs_items[0].db_map
            and self._hovered_obj_item.entity_class_id in self.relationship_class["object_class_ids_to_go"]
        )

    def mousePressEvent(self, event):
        """Handles relationship creation if one it's in process."""
        if not self.cross_hairs_items:
            super().mousePressEvent(event)
            return
        if event.buttons() & Qt.RightButton or not self._hovered_obj_item:
            self.clear_cross_hairs_items()
            return
        if self._cross_hairs_has_valid_taget():
            self.relationship_class["object_class_ids_to_go"].remove(self._hovered_obj_item.entity_class_id)
            if self.relationship_class["object_class_ids_to_go"]:
                # Add hovered as member and keep going, we're not done yet
                ch_rel_item = self.cross_hairs_items[1]
                ch_arc_item = CrossHairsArcItem(ch_rel_item, self._hovered_obj_item, self._spine_db_editor._ARC_WIDTH)
                ch_rel_item.refresh_icon()
                self.scene().addItem(ch_arc_item)
                ch_arc_item.apply_zoom(self.zoom_factor)
                self.cross_hairs_items.append(ch_arc_item)
                return
            # Here we're done, add the relationships between the hovered and the members
            ch_item, _, *ch_arc_items = self.cross_hairs_items
            obj_items = [arc_item.obj_item for arc_item in ch_arc_items]
            obj_items.remove(ch_item)
            self._spine_db_editor.finalize_relationship(self.relationship_class, self._hovered_obj_item, *obj_items)
            self.clear_cross_hairs_items()

    def mouseMoveEvent(self, event):
        """Updates the hovered object item if we're in relationship creation mode."""
        if not self.cross_hairs_items:
            super().mouseMoveEvent(event)
            return
        self._update_cross_hairs_pos(event.pos())

    def _update_cross_hairs_pos(self, pos):
        """Updates the hovered object item and sets the 'cross_hairs' icon accordingly.

        Args:
            pos (QPoint): the desired position in view coordinates
        """
        cross_hairs_item = self.cross_hairs_items[0]
        scene_pos = self.mapToScene(pos)
        delta = scene_pos - cross_hairs_item.scenePos()
        cross_hairs_item.block_move_by(delta.x(), delta.y())
        self._hovered_obj_item = None
        obj_items = [item for item in self.items(pos) if isinstance(item, ObjectItem)]
        self._hovered_obj_item = next(iter(obj_items), None)
        if self._hovered_obj_item is not None:
            if self._cross_hairs_has_valid_taget():
                if len(self.relationship_class["object_class_ids_to_go"]) == 1:
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
        self._menu.exec_(e.globalPos())

    def _compute_min_zoom(self):
        return 0.5 * self.zoom_factor * self._items_fitting_zoom

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
        if event.orientation() != Qt.Vertical:
            event.ignore()
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
