######################################################################################################################
# Copyright (C) 2017-2020 Spine project consortium
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

from PySide2.QtCore import Qt, QTimeLine
from PySide2.QtWidgets import QMenu
from PySide2.QtGui import QCursor
from ...widgets.custom_qgraphicsviews import CustomQGraphicsView
from ..graphics_items import ObjectItem, CrossHairsArcItem


class EntityQGraphicsView(CustomQGraphicsView):
    """QGraphicsView for the Entity Graph View."""

    def __init__(self, parent):
        """

        Args:
            parent (QWidget): Graph View Form's (QMainWindow) central widget (self.centralwidget)
        """
        super().__init__(parent=parent)  # Parent is passed to QWidget's constructor
        self._data_store_form = None
        self._menu = QMenu(self)
        self._hovered_obj_item = None
        self.relationship_class = None
        self.cross_hairs_items = []

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
        obj_item = cross_hairs_items[0]
        obj_item.grabMouse()
        cursor_pos = self.mapFromGlobal(QCursor.pos())
        pos = self.mapToScene(cursor_pos)
        delta = pos - obj_item.scenePos()
        obj_item.block_move_by(delta.x(), delta.y())
        self._update_hovered_obj_item(cursor_pos)

    def clear_cross_hairs_items(self):
        self.relationship_class = None
        for item in self.cross_hairs_items:
            item.hide()
            item.scene().removeItem(item)
        self.cross_hairs_items.clear()
        self.viewport().setCursor(Qt.ArrowCursor)

    def connect_data_store_form(self, data_store_form):
        self._data_store_form = data_store_form
        self.create_context_menu()

    def create_context_menu(self):
        self._menu.addAction(self._data_store_form.ui.actionExport_graph_as_pdf)
        self._menu.addSeparator()
        for action in self._data_store_form.ui.menuGraph.actions():
            self._menu.addAction(action)

    def edit_selected(self):
        """Edits selected items using the connected data store form."""
        self._data_store_form.edit_entity_graph_items()

    def remove_selected(self):
        """Removes selected items using the connected data store form."""
        self._data_store_form.remove_entity_graph_items()

    def mousePressEvent(self, event):
        """Handles relationship creation if one it's in process."""
        if not self.cross_hairs_items:
            super().mousePressEvent(event)
            return
        if event.buttons() & Qt.RightButton:
            self.clear_cross_hairs_items()
            self._data_store_form.msg.emit("Relationship creation aborted.")
            return
        if not self._hovered_obj_item:
            self.clear_cross_hairs_items()
            self._data_store_form.msg.emit("Unable to create relationship. You didn't click on an object.")
            return
        if self._hovered_obj_item.entity_class_id in self.relationship_class["object_class_ids_to_go"]:
            self.relationship_class["object_class_ids_to_go"].remove(self._hovered_obj_item.entity_class_id)
            if self.relationship_class["object_class_ids_to_go"]:
                # Add hovered as member and keep going, we're not done yet
                ch_rel_item = self.cross_hairs_items[1]
                ch_arc_item = CrossHairsArcItem(ch_rel_item, self._hovered_obj_item, self._data_store_form._ARC_WIDTH)
                ch_rel_item.refresh_icon()
                self.scene().addItem(ch_arc_item)
                ch_arc_item.apply_zoom(self.zoom_factor)
                self.cross_hairs_items.append(ch_arc_item)
                self._data_store_form.msg.emit(
                    "Successfuly added new member object '{0}'".format(self._hovered_obj_item.entity_name)
                )
                return
            # Here we're done, add the relationships between the hovered and the members
            ch_item, _, *ch_arc_items = self.cross_hairs_items
            obj_items = [arc_item.obj_item for arc_item in ch_arc_items]
            obj_items.remove(ch_item)
            self._data_store_form.finalize_relationship(self.relationship_class, self._hovered_obj_item, *obj_items)
            self.clear_cross_hairs_items()
            return
        self._data_store_form.msg.emit("Not a valid member object for this relationship.")

    def mouseMoveEvent(self, event):
        """Updates the hovered object item if we're in relationship creation mode."""
        super().mouseMoveEvent(event)
        if not self.cross_hairs_items:
            return
        self._update_hovered_obj_item(event.pos())

    def _update_hovered_obj_item(self, pos):
        """Updates the hovered object item and sets the 'cross_hairs' icon accordingly.

        Args:
            pos (QPoint)
        """
        self.viewport().setCursor(Qt.BlankCursor)
        self._hovered_obj_item = None
        items_at_pos = [item for item in self.items(pos) if item not in self.cross_hairs_items]
        self._hovered_obj_item = next(iter([x for x in items_at_pos if isinstance(x, ObjectItem)]), None)
        if self._hovered_obj_item is not None:
            if self._hovered_obj_item.entity_class_id in self.relationship_class["object_class_ids_to_go"]:
                if len(self.relationship_class["object_class_ids_to_go"]) == 1:
                    self.cross_hairs_items[0].set_check_icon()
                else:
                    self.cross_hairs_items[0].set_plus_icon()
                return
            self.cross_hairs_items[0].set_ban_icon()
            return
        self.cross_hairs_items[0].set_foo_icon()

    def mouseReleaseEvent(self, event):
        if not self.cross_hairs_items:
            super().mouseReleaseEvent(event)

    def keyPressEvent(self, event):
        """Aborts relationship creation if user presses ESC."""
        super().keyPressEvent(event)
        if event.key() == Qt.Key_Escape and self.cross_hairs_items:
            self._data_store_form.msg.emit("Relationship creation aborted.")
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
        self._data_store_form._handle_menu_graph_about_to_show()
        self._menu.exec_(e.globalPos())

    def _use_smooth_zoom(self):
        return self._qsettings.value("appSettings/smoothEntityGraphZoom", defaultValue="false") == "true"

    def _zoom(self, factor):
        self.scale(factor, factor)
        self.apply_zoom()

    def apply_zoom(self):
        for item in self.items():
            if hasattr(item, "apply_zoom"):
                item.apply_zoom(self.zoom_factor)
        self._set_preferred_scene_rect()

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
