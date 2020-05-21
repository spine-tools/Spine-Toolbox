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
Classes for custom context menus and pop-up menus.

:author: M. Marin (KTH)
:date:   13.5.2020
"""

from PySide2.QtWidgets import QMenu, QWidgetAction
from PySide2.QtCore import QEvent, QPoint, Signal
from ...helpers import fix_name_ambiguity
from .custom_qwidgets import LazyFilterWidget, DataToValueFilterWidget
from ...widgets.custom_menus import CustomContextMenu, FilterMenuBase


class GraphViewContextMenu(QMenu):
    """Context menu class for qgraphics view in graph view."""

    def __init__(self, parent):
        """
        Args:
            parent (QWidget): Parent for menu widget (GraphViewForm)
        """
        super().__init__(parent)
        parent._handle_menu_graph_about_to_show()
        self.addAction(parent.ui.actionSave_positions)
        self.addAction(parent.ui.actionClear_positions)
        self.addSeparator()
        self.addAction(parent.ui.actionHide_selected)
        self.addAction(parent.ui.actionShow_hidden)
        self.addSeparator()
        self.addAction(parent.ui.actionPrune_selected_entities)
        self.addAction(parent.ui.actionPrune_selected_classes)
        self.addMenu(parent.ui.menuRestore_pruned)
        self.addAction(parent.ui.actionRestore_all_pruned)


class EntityItemContextMenu(CustomContextMenu):
    """Context menu class for entity graphic items in graph view."""

    def __init__(self, parent, position):
        """
        Args:
            parent (QWidget): Parent for menu widget (GraphViewForm)
            position (QPoint): Position on screen
        """
        super().__init__(parent, position)
        self.selection_count = len(parent.entity_item_selection)
        parent._handle_menu_graph_about_to_show()
        self.addAction(parent.ui.actionHide_selected)
        self.addAction(parent.ui.actionPrune_selected_entities)
        self.addAction(parent.ui.actionPrune_selected_classes)


class ObjectItemContextMenu(EntityItemContextMenu):
    def __init__(self, parent, position, graphics_item):
        """
        Args:
            parent (QWidget): Parent for menu widget (GraphViewForm)
            position (QPoint): Position on screen
            graphics_item (spinetoolbox.widgets.graph_view_graphics_items.ObjectItem): item that requested the menu
        """
        super().__init__(parent, position)
        self.relationship_class_dict = dict()
        self.addSeparator()
        if graphics_item.is_wip:
            self.add_action("Set name", enabled=self.selection_count == 1)
        else:
            self.add_action("Rename", enabled=self.selection_count == 1)
        self.add_action("Remove")
        if graphics_item.is_wip or self.selection_count > 1:
            return
        self.addSeparator()
        for relationship_class in parent.db_mngr.get_items(parent.db_map, "relationship class"):
            object_class_names = relationship_class["object_class_name_list"].split(",")
            fixed_object_class_names = fix_name_ambiguity(object_class_names)
            for i, object_class_name in enumerate(object_class_names):
                if object_class_name != graphics_item.entity_class_name:
                    continue
                option = "Add '{}' relationship".format(relationship_class['name'])
                if object_class_name != fixed_object_class_names[i]:
                    option += f" as dimension {i}"
                self.add_action(option)
                self.relationship_class_dict[option] = {'id': relationship_class["id"], 'dimension': i}


class RelationshipItemContextMenu(EntityItemContextMenu):
    def __init__(self, parent, position):
        """
        Args:
            parent (QWidget): Parent for menu widget (GraphViewForm)
            position (QPoint): Position on screen
        """
        super().__init__(parent, position)
        self.addSeparator()
        self.add_action("Remove")


class ParameterViewFilterMenu(FilterMenuBase):

    filterChanged = Signal(set, bool)

    def __init__(self, parent, source_model, show_empty=True):
        """
        Args:
            parent (DataStoreForm)
            source_model (CompoundParameterModel): a model to lazily get data from
        """
        super().__init__(parent)
        self._filter = LazyFilterWidget(self, source_model, show_empty=show_empty)
        self._filter_action = QWidgetAction(parent)
        self._filter_action.setDefaultWidget(self._filter)
        self.addAction(self._filter_action)
        self.connect_signals()
        self.aboutToShow.connect(self._filter.set_model)

    def emit_filter_changed(self, valid_values):
        self.filterChanged.emit(valid_values, self._filter.has_filter())


class TabularViewFilterMenu(FilterMenuBase):
    """Filter menu to use together with FilterWidget in TabularViewMixin."""

    filterChanged = Signal(int, set, bool)

    def __init__(self, parent, identifier, data_to_value, show_empty=True):
        """
        Args:
            parent (DataStoreForm)
            identifier (int): index identifier
            data_to_value (method): a method to translate item data to a value for display role
        """
        super().__init__(parent)
        self.identifier = identifier
        self._filter = DataToValueFilterWidget(self, data_to_value, show_empty=show_empty)
        self._filter_action = QWidgetAction(parent)
        self._filter_action.setDefaultWidget(self._filter)
        self.addAction(self._filter_action)
        self.anchor = parent
        self.connect_signals()

    def emit_filter_changed(self, valid_values):
        self.filterChanged.emit(self.identifier, valid_values, self._filter.has_filter())

    def event(self, event):
        if event.type() == QEvent.Show and self.anchor is not None:
            if self.anchor.area == "rows":
                pos = self.anchor.mapToGlobal(QPoint(0, 0)) + QPoint(0, self.anchor.height())
            elif self.anchor.area == "columns":
                pos = self.anchor.mapToGlobal(QPoint(0, 0)) + QPoint(self.anchor.width(), 0)
            self.move(pos)
        return super().event(event)
