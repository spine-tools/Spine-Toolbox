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
Provides SpineDBIconManager.

:authors: M. Marin (KTH)
:date:   3.2.2021
"""

from PySide2.QtCore import QSize, Qt, QPointF, QRectF
from PySide2.QtWidgets import QGraphicsScene
from PySide2.QtGui import QIcon, QFont, QTextOption
from .helpers import TransparentIconEngine, CharIconEngine, interpret_icon_id, object_icon


def _align_text_in_item(item):
    document = item.document()
    document.setDocumentMargin(0)
    option = QTextOption(Qt.AlignCenter)
    document.setDefaultTextOption(option)
    item.adjustSize()
    rect = item.boundingRect()
    size = 0.875 * round(min(rect.width(), rect.height()))
    font = item.font()
    font.setPixelSize(size)
    item.setFont(font)


def _center_scene(scene):
    rect = scene.itemsBoundingRect()
    center = rect.center()
    extent = 0.5 * max(rect.width(), rect.height())
    top_left = center - QPointF(extent, extent)
    bottom_right = center + QPointF(extent, extent)
    square = QRectF(top_left, bottom_right)
    scene.setSceneRect(square)
    rect_item = scene.addRect(square)
    rect_item.setPen(Qt.NoPen)


class SpineDBIconManager:
    """A class to manage object_class icons for spine db editors."""

    ICON_SIZE = QSize(512, 512)

    def __init__(self):
        self.display_icons = {}  # A mapping from object_class name to display icon code
        self.rel_cls_scenes = {}  # A mapping from object_class name list to associated scene
        self.obj_group_scenes = {}  # A mapping from class name to associated group scene

    def update_icon_caches(self, object_classes):
        """Called after adding or updating object classes.
        Stores display_icons and clears obsolete entries
        from the relationship class and entity group scene caches."""
        for object_class in object_classes:
            self.display_icons[object_class["name"]] = object_class["display_icon"]
        object_class_names = [x["name"] for x in object_classes]
        dirty_keys = [k for k in self.rel_cls_scenes if any(x in object_class_names for x in k)]
        for k in dirty_keys:
            del self.rel_cls_scenes[k]
        for name in object_class_names:
            self.obj_group_scenes.pop(name, None)

    def object_icon(self, object_class_name):
        """An icon for the given object_class."""
        display_icon = self.display_icons.get(object_class_name, -1)
        return object_icon(display_icon)

    def _create_rel_cls_scene(self, object_class_names):
        font = QFont('Font Awesome 5 Free Solid')
        scene = QGraphicsScene()
        x = 0
        for j, obj_cls_name in enumerate(object_class_names):
            display_icon = self.display_icons.get(obj_cls_name, -1)
            icon_code, color_code = interpret_icon_id(display_icon)
            text_item = scene.addText(chr(icon_code), font)
            text_item.setDefaultTextColor(color_code)
            _align_text_in_item(text_item)
            if j % 2 == 0:
                y = 0
            else:
                y = -0.875 * 0.75 * text_item.boundingRect().height()
                text_item.setZValue(-1)
            text_item.setPos(x, y)
            x += 0.875 * 0.5 * text_item.boundingRect().width()
        _center_scene(scene)
        self.rel_cls_scenes[object_class_names] = scene

    def relationship_icon(self, str_object_class_name_list):
        if not str_object_class_name_list:
            return QIcon(CharIconEngine("\uf1b3", 0))
        object_class_names = tuple(str_object_class_name_list.split(","))
        if object_class_names not in self.rel_cls_scenes:
            self._create_rel_cls_scene(object_class_names)
        scene = self.rel_cls_scenes[object_class_names]
        return QIcon(SceneIconEngine(scene))

    def _create_obj_group_scene(self, object_class_name):
        display_icon = self.display_icons.get(object_class_name, -1)
        icon_code, color_code = interpret_icon_id(display_icon)
        font = QFont('Font Awesome 5 Free Solid')
        scene = QGraphicsScene()
        x = 0
        for _ in range(2):
            y = 0
            for _ in range(2):
                text_item = scene.addText(chr(icon_code), font)
                text_item.setDefaultTextColor(color_code)
                text_item.setPos(x, y)
                y += 0.875 * text_item.boundingRect().height()
            x += 0.875 * text_item.boundingRect().width()
        scene.addRect(scene.itemsBoundingRect())
        self.obj_group_scenes[object_class_name] = scene

    def object_group_icon(self, object_class_name):
        if object_class_name not in self.obj_group_scenes:
            self._create_obj_group_scene(object_class_name)
        scene = self.obj_group_scenes[object_class_name]
        return QIcon(SceneIconEngine(scene))


class SceneIconEngine(TransparentIconEngine):
    """Specialization of QIconEngine used to draw scene-based icons."""

    def __init__(self, scene):
        super().__init__()
        self.scene = scene

    def paint(self, painter, rect, mode=None, state=None):
        painter.save()
        self.scene.render(painter, rect, self.scene.itemsBoundingRect())
        painter.restore()
