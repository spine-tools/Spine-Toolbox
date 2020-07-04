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
Classes for handling models in PySide2's model/view framework.

:author: P. Vennström (VTT)
:date:   11.5.2020
"""
from collections import namedtuple
from collections.abc import Iterable
from PySide2.QtCore import Qt, Slot
from PySide2.QtGui import QCursor, QFont, QIcon
from PySide2.QtWidgets import QHeaderView, QMenu, QTableView, QToolButton
from ..spine_io.io_api import TYPE_STRING_TO_CLASS
from ..spine_io.type_conversion import value_to_convert_spec, NewIntegerSequenceDateTimeConvertSpecDialog
from spinetoolbox.helpers import CharIconEngine

_ALLOWED_TYPES = list(sorted(TYPE_STRING_TO_CLASS.keys()))
_ALLOWED_TYPES.append("integer sequence datetime")

_TYPE_TO_FONT_AWESOME_ICON = {
    "integer sequence datetime": chr(int('f073', 16)),
    "boolean": chr(int('f6ad', 16)),
    "string": chr(int('f031', 16)),
    "datetime": chr(int('f073', 16)),
    "duration": chr(int('f017', 16)),
    "float": chr(int('f534', 16)),
}

Margin = namedtuple("Margin", ("left", "right", "top", "bottom"))


class TableViewWithButtonHeader(QTableView):
    """Customized table with data type buttons on horizontal and vertical headers"""

    def __init__(self, parent=None):
        """
        Args:
            parent (QWidget): a parent widget
        """
        super().__init__(parent)
        self._horizontal_header = _HeaderWithButton(Qt.Horizontal, self)
        self._vertical_header = _HeaderWithButton(Qt.Vertical, self)
        self.setHorizontalHeader(self._horizontal_header)
        self._horizontal_header.setContextMenuPolicy(Qt.CustomContextMenu)
        self._horizontal_header.customContextMenuRequested.connect(self._show_horizontal_header_menu)
        self._horizontal_menu = self._create_horizontal_header_menu()
        self.setVerticalHeader(self._vertical_header)
        self._vertical_header.setContextMenuPolicy(Qt.CustomContextMenu)
        self._vertical_header.customContextMenuRequested.connect(self._show_vertical_header_menu)
        self._vertical_menu = self._create_vertical_header_menu()

    def scrollContentsBy(self, dx, dy):
        """Scrolls the table's contents by given delta."""
        super().scrollContentsBy(dx, dy)
        if dx != 0:
            self._horizontal_header.fix_widget_positions()
        if dy != 0:
            self._vertical_header.fix_widget_positions()

    def _create_horizontal_header_menu(self):
        """Returns a new menu for the horizontal header"""
        parent = self._horizontal_header
        menu = QMenu(parent)
        type_menu = _create_allowed_types_menu(parent, self._set_all_column_data_types)
        type_menu.setTitle("Set all data types to...")
        menu.addMenu(type_menu)
        return menu

    def _create_vertical_header_menu(self):
        """Returns a new menu for the vertical header."""
        parent = self._horizontal_header
        menu = QMenu(parent)
        type_menu = _create_allowed_types_menu(parent, self._set_all_row_data_types)
        type_menu.setTitle("Set all data types to...")
        menu.addMenu(type_menu)
        return menu

    @Slot("QPoint")
    def _show_horizontal_header_menu(self, pos):
        """Opens the context menu of the horizontal header."""
        screen_pos = self._horizontal_header.mapToGlobal(pos)
        self._horizontal_menu.exec_(screen_pos)

    @Slot("QPoint")
    def _show_vertical_header_menu(self, pos):
        """Opens the context menu of the vertical header."""
        screen_pos = self._vertical_header.mapToGlobal(pos)
        self._vertical_menu.exec_(screen_pos)

    @Slot("QAction")
    def _set_all_column_data_types(self, action):
        """Sets all columns data types to the type given by action's text."""
        type_str = action.text()
        columns = range(self._horizontal_header.count())
        self._horizontal_header.set_data_types(columns, type_str)

    @Slot("QAction")
    def _set_all_row_data_types(self, action):
        """Sets all rows data types to the type given by action's text."""
        type_str = action.text()
        rows = range(self._vertical_header.count())
        self._vertical_header.set_data_types(rows, type_str)


class _HeaderWithButton(QHeaderView):
    """Class that reimplements the QHeaderView section paint event to draw a button
    that is used to display and change the type of that column or row.
    """

    def __init__(self, orientation, parent=None):
        super().__init__(orientation, parent)
        self.setHighlightSections(True)
        self.setSectionsClickable(True)
        self.setDefaultAlignment(Qt.AlignLeft)
        self.sectionResized.connect(self._section_resize)
        self.sectionMoved.connect(self._section_move)
        self._font = QFont('Font Awesome 5 Free Solid')

        self._display_all = True
        self._display_sections = []

        self._margin = Margin(left=0, right=0, top=0, bottom=0)

        self._menu = _create_allowed_types_menu(self, self._menu_pressed)

        self._button = QToolButton(parent=self)
        self._button.setMenu(self._menu)
        self._button.setPopupMode(QToolButton.InstantPopup)
        self._button.setFont(self._font)
        self._button.setCursor(Qt.ArrowCursor)
        self._button.hide()

        self._render_button = QToolButton(parent=self)
        self._render_button.setFont(self._font)
        self._render_button.hide()

        self.setMinimumSectionSize(self.minimumSectionSize() + self.widget_width())

    @property
    def display_all(self):
        return self._display_all

    @display_all.setter
    def display_all(self, display_all):
        self._display_all = display_all
        self.viewport().update()

    @property
    def sections_with_buttons(self):
        return self._display_sections

    @sections_with_buttons.setter
    def sections_with_buttons(self, sections):
        self._display_sections = set(sections)
        self.viewport().update()

    @Slot("QAction")
    def _menu_pressed(self, action):
        """Sets the data type of a row or column according to menu action."""
        logical_index = self.logicalIndexAt(self._button.pos())
        type_str = action.text()
        self.set_data_types(logical_index, type_str, update_viewport=True)

    def set_data_types(self, sections, type_str, update_viewport=True):
        """
        Sets the data types of given sections (rows, columns).

        Args:
            sections (Iterable or int or NoneType): row/column index
            type_str (str): data type name
            update_viewport (bool): True if the buttons need repaint
        """
        if type_str == "integer sequence datetime":
            dialog = NewIntegerSequenceDateTimeConvertSpecDialog()
            if not dialog.exec_():
                return
            convert_spec = dialog.get_spec()
        else:
            convert_spec = value_to_convert_spec(type_str)
        if not isinstance(sections, Iterable):
            sections = [sections]
        orientation = self.orientation()
        for section in sections:
            self.model().set_type(section, convert_spec, orientation)
        if update_viewport:
            self.viewport().update()

    def widget_width(self):
        """Width of widget

        Returns:
            int: Width of widget
        """
        if self.orientation() == Qt.Horizontal:
            return self.height()
        return self.sectionSize(0)

    def widget_height(self):
        """Height of widget

        Returns:
            int: Height of widget
        """
        if self.orientation() == Qt.Horizontal:
            return self.height()
        return self.sectionSize(0)

    def _hide_or_show_button(self, logical_index):
        """Hides or shows the button depending on the logical index.

        Args:
            logical_index (int)
        """
        if logical_index in self._display_sections or self._display_all:
            self._set_button_geometry(self._button, logical_index)
            self._button.show()
        else:
            self._button.hide()

    def mouseMoveEvent(self, mouse_event):
        """Moves the button to the correct section so that interacting with the button works.
        """
        logical_index = self.logicalIndexAt(mouse_event.x(), mouse_event.y())
        self._hide_or_show_button(logical_index)
        super().mouseMoveEvent(mouse_event)

    def enterEvent(self, event):
        """Shows the button."""
        mouse_position = self.mapFromGlobal(QCursor.pos())
        logical_index = self.logicalIndexAt(mouse_position)
        self._hide_or_show_button(logical_index)
        super().enterEvent(event)

    def leaveEvent(self, event):
        """Hides button."""
        self._button.hide()
        super().leaveEvent(event)

    def _set_button_geometry(self, button, index):
        """Sets a buttons geometry depending on the index.

        Arguments:
            button (QWidget): QWidget that geometry should be set
            index (int): logical_index to set position and geometry to.
        """
        margin = self._margin
        if self.orientation() == Qt.Horizontal:
            button.setGeometry(
                self.sectionViewportPosition(index) + margin.left,
                margin.top,
                self.widget_width() - margin.left - margin.right,
                self.widget_height() - margin.top - margin.bottom,
            )
        else:
            button.setGeometry(
                margin.left,
                self.sectionViewportPosition(index) + margin.top,
                self.widget_width() - margin.left - margin.right,
                self.widget_height() - margin.top - margin.bottom,
            )

    def _section_resize(self, i):
        """When a section is resized.

        Arguments:
            i (int): logical index to section being resized
        """
        self._button.hide()
        mouse_position = self.mapFromGlobal(QCursor.pos())
        logical_index = self.logicalIndexAt(mouse_position)
        if i == logical_index:
            self._set_button_geometry(self._button, logical_index)

    def paintSection(self, painter, rect, logical_index):
        """Paints a section of the QHeader view.

        Works by drawing a pixmap of the button to the left of the original paint rectangle.
        Then shifts the original rect to the right so these two doesn't paint over each other.
        """
        if not self._display_all and logical_index not in self._display_sections:
            super().paintSection(painter, rect, logical_index)
            return

        # get the type of the section.
        type_spec = self.model().get_type(logical_index, self.orientation())
        if type_spec is None:
            type_spec = "string"
        else:
            type_spec = type_spec.DISPLAY_NAME
        font_str = _TYPE_TO_FONT_AWESOME_ICON[type_spec]

        # set data for both interaction button and render button.
        self._button.setText(font_str)
        self._render_button.setText(font_str)
        self._set_button_geometry(self._render_button, logical_index)

        # get pixmap from render button and draw into header section.
        rw = self._render_button.grab()
        if self.orientation() == Qt.Horizontal:
            painter.drawPixmap(self.sectionViewportPosition(logical_index), 0, rw)
        else:
            painter.drawPixmap(0, self.sectionViewportPosition(logical_index), rw)

        # shift rect that super class should paint in to the right so it doesn't
        # paint over the button
        rect.adjust(self.widget_width(), 0, 0, 0)
        super().paintSection(painter, rect, logical_index)

    def sectionSizeFromContents(self, logical_index):
        """Add the button width to the section so it displays right.

        Arguments:
            logical_index (int): logical index of section

        Returns:
            QSize: Size of section
        """
        org_size = super().sectionSizeFromContents(logical_index)
        org_size.setWidth(org_size.width() + self.widget_width())
        return org_size

    def _section_move(self, logical, old_visual_index, new_visual_index):
        """Section being moved.

        Arguments:
            logical (int): logical index of section beeing moved.
            old_visual_index (int): old visual index of section
            new_visual_index (int): new visual index of section
        """
        self._button.hide()
        mouse_position = self.mapFromGlobal(QCursor.pos())
        logical_index = self.logicalIndexAt(mouse_position)
        self._set_button_geometry(self._button, logical_index)

    def fix_widget_positions(self):
        """Update position of interaction button
        """
        mouse_position = self.mapFromGlobal(QCursor.pos())
        logical_index = self.logicalIndexAt(mouse_position)
        self._set_button_geometry(self._button, logical_index)

    def set_margins(self, margins):
        """Sets the header margins."""
        self._margin = margins


def _create_allowed_types_menu(parent, trigger_slot):
    """
    Returns a menu which contains actions for each allowed data type.

    Args:
        parent (QWidget): a parent widget
        trigger_slot (Slot): a slot which is connected to QMenu's 'triggered' signal
    Returns:
        QMenu: a menu
    """
    menu = QMenu(parent)
    for at in _ALLOWED_TYPES:
        icon_char = _TYPE_TO_FONT_AWESOME_ICON[at]
        engine = CharIconEngine(icon_char, 0)
        icon = QIcon(engine.pixmap())
        menu.addAction(icon, at)
    menu.triggered.connect(trigger_slot)
    return menu
