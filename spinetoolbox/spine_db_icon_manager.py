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

"""Provides SpineDBIconManager."""
from collections.abc import Iterable
from PySide6.QtCore import QBuffer, QPointF, QRectF, Qt
from PySide6.QtGui import QFont, QIcon, QPainter, QTextOption
from PySide6.QtSvg import QSvgGenerator, QSvgRenderer
from PySide6.QtWidgets import QGraphicsScene
from spinedb_api.db_mapping_base import PublicItem
from .font import TOOLBOX_FONT
from .helpers import TransparentIconEngine, default_icon_id, interpret_icon_id


def _align_text_in_item(item):
    document = item.document()
    document.setDocumentMargin(0)
    option = QTextOption(Qt.AlignCenter)
    document.setDefaultTextOption(option)
    item.adjustSize()
    rect = item.boundingRect()
    size = 0.875 * round(min(rect.width(), rect.height()))
    font = item.font()
    font.setPixelSize(max(1, size))
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


class _SceneSvgRenderer(QSvgRenderer):
    def __init__(self, scene):
        buffer = QBuffer()
        generator = QSvgGenerator()
        generator.setOutputDevice(buffer)
        scene_rect = scene.sceneRect()
        generator.setViewBox(scene_rect)
        painter = QPainter(generator)
        scene.render(painter, scene_rect, scene_rect)
        painter.end()
        buffer.open(QBuffer.ReadOnly)
        super().__init__(buffer.readAll())
        buffer.close()
        self.scene = scene


class SpineDBIconManager:
    """A class to manage object_class icons for spine db editors."""

    def __init__(self):
        self.display_icons = {}  # A mapping from object_class name to display icon code
        self._class_renderers = {}  # A mapping from class name to associated renderer
        self._multi_class_renderers = (
            {}
        )  # A mapping from tuple(class name, dimension name list, id) to associated renderer
        self._group_renderers = {}  # A mapping from class name to associated group renderer
        self.icon_renderers = {}

    def update_icon_caches(self, classes: Iterable[PublicItem]):
        """Called after adding or updating entity classes.
        Stores display_icons and clears obsolete entries
        from the relationship class and entity group renderer caches.

        Args:
            classes: iterable of entity classes that were updated.
        """
        for class_ in classes:
            self.display_icons[class_["name"]] = class_["display_icon"]
        class_names = {x["name"] for x in classes}
        class_dimension_name_lists = {x["dimension_name_list"] for x in classes}
        # Three cases where deletions are made: class is deleted, renamed, or its element(s) renamed
        dirty_keys = {
            k for k in self._multi_class_renderers if k[0] in class_names or k[1] in class_dimension_name_lists
        }
        dirty_keys.update(k for k in self._multi_class_renderers if any(x in k[1] for x in class_names))
        for k in dirty_keys:
            del self._multi_class_renderers[k]
        for name in class_names:
            self._group_renderers.pop(name, None)
            self._class_renderers.pop(name, None)

    def _create_icon_renderer(self, icon_code, color_code):
        scene = QGraphicsScene()
        font = QFont(TOOLBOX_FONT.family)
        text_item = scene.addText(icon_code, font)
        text_item.setDefaultTextColor(color_code)
        _align_text_in_item(text_item)
        self.icon_renderers[icon_code, color_code] = _SceneSvgRenderer(scene)

    def icon_renderer(self, icon_code, color_code):
        if (icon_code, color_code) not in self.icon_renderers:
            self._create_icon_renderer(icon_code, color_code)
        return self.icon_renderers[icon_code, color_code]

    def color_class_renderer(self, entity_class, color_code):
        class_name = entity_class["name"]
        display_icon = self.display_icons.get(class_name, -1)
        icon_code, _ = interpret_icon_id(display_icon)
        return self.icon_renderer(chr(icon_code), color_code)

    def _create_class_renderer(self, class_name):
        display_icon = self.display_icons.get(class_name, -1)
        icon_code, color_code = interpret_icon_id(display_icon)
        self._class_renderers[class_name] = self.icon_renderer(chr(icon_code), color_code)

    def _create_multi_class_renderer(self, name, dimension_name_list, id_):
        if not any(dimension_name_list):
            self._multi_class_renderers[
                (
                    name,
                    dimension_name_list,
                    id_,
                )
            ] = self.icon_renderer("\uf1b3", 0)
            return
        font = QFont(TOOLBOX_FONT.family)
        scene = QGraphicsScene()
        display_icon = self.display_icons.get(name, None)
        if display_icon and display_icon != default_icon_id():  # If the entity class has an icon set, use that one.
            icon_code, color_code = interpret_icon_id(display_icon)
            self._multi_class_renderers[
                (
                    name,
                    dimension_name_list,
                    id_,
                )
            ] = self.icon_renderer(chr(icon_code), color_code)
            return
        # If no icon is set, create a composite from the icons of the class elements.
        x = 0
        for j, dimension_name in enumerate(dimension_name_list):
            display_icon = self.display_icons.get(dimension_name, -1)
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
        self._multi_class_renderers[
            (
                name,
                dimension_name_list,
                id_,
            )
        ] = _SceneSvgRenderer(scene)

    def update_multi_classes(self, name, dimension_name_list, id_):
        """Updates the multi class renderers when their members change"""
        if name not in {x[0] for x in self._multi_class_renderers}:
            if dimension_name_list in {x[1] for x in self._multi_class_renderers} and id_ in {
                x[2] for x in self._multi_class_renderers
            }:  # In this case the class has been renamed and the renderer will be updated accordingly.
                key, value, new_key = None, None, None
                for key, value in self._multi_class_renderers.items():
                    if key[1] == dimension_name_list:
                        new_key = (
                            name,
                            key[1],
                            id_,
                        )
                        break
                if new_key:
                    del self._multi_class_renderers[key]
                    self._multi_class_renderers[new_key] = value
            else:
                self.multi_class_renderer(name, dimension_name_list, id_)
        new_key = None
        for key, value in self._multi_class_renderers.items():
            if key[0] == name:  # Updates the names of the dependency classes if they have changed
                new_key = (
                    name,
                    dimension_name_list,
                    id_,
                )
                break
        if new_key:
            del self._multi_class_renderers[key]
            self._multi_class_renderers[new_key] = value

    def class_renderer(self, entity_class):
        name, dimension_name_list, id_ = entity_class["name"], entity_class["dimension_name_list"], entity_class["id"]
        if not dimension_name_list:
            if name not in self._class_renderers:
                self._create_class_renderer(name)
            return self._class_renderers[name]
        self.update_multi_classes(name, dimension_name_list, id_)
        return self._multi_class_renderers[
            (
                name,
                dimension_name_list,
                id_,
            )
        ]

    def multi_class_renderer(self, name, dimension_name_list, id_):
        """Creates a new multi-class renderer if one doesn't exist already"""
        if name not in self._multi_class_renderers:
            self._create_multi_class_renderer(name, dimension_name_list, id_)
        return self._multi_class_renderers[
            (
                name,
                dimension_name_list,
                id_,
            )
        ]

    def _create_group_renderer(self, class_name):
        display_icon = self.display_icons.get(class_name, -1)
        icon_code, color_code = interpret_icon_id(display_icon)
        font = QFont(TOOLBOX_FONT.family)
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
        self._group_renderers[class_name] = _SceneSvgRenderer(scene)

    def group_renderer(self, entity_class):
        class_name = entity_class["name"]
        if class_name not in self._group_renderers:
            self._create_group_renderer(class_name)
        return self._group_renderers[class_name]

    @staticmethod
    def icon_from_renderer(renderer):
        return QIcon(SceneIconEngine(renderer.scene))


class SceneIconEngine(TransparentIconEngine):
    """Specialization of QIconEngine used to draw scene-based icons."""

    def __init__(self, scene):
        super().__init__()
        self.scene = scene

    def paint(self, painter, rect, mode=None, state=None):
        painter.save()
        self.scene.render(painter, rect, self.scene.sceneRect())
        painter.restore()
