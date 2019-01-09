######################################################################################################################
# Copyright (C) 2017 - 2018 Spine project consortium
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

:author: P. Savolainen (VTT)
:date:   9.1.2018
"""

import logging
from PySide2.QtWidgets import QMenu, QSpinBox, QWidgetAction, QAction
from PySide2.QtGui import QIcon
from PySide2.QtCore import Qt, Signal, Slot, QPoint
from helpers import fix_name_ambiguity, tuple_itemgetter
from widgets.custom_qwidget import FilterWidget
from operator import itemgetter


class CustomContextMenu(QMenu):
    """Context menu master class for several context menus.

    Attributes:
        parent (QWidget): Parent for menu widget (ToolboxUI)
    """
    def __init__(self, parent):
        """Constructor."""
        super().__init__(parent=parent)
        self._parent = parent
        self.option = "None"

    def add_action(self, text, icon=QIcon(), enabled=True):
        """Adds an action to the context menu.

        Args:
            text (str): Text description of the action
            icon (QIcon): Icon for menu item
            enabled (bool): Is action enabled?
        """
        action = self.addAction(icon, text)
        action.setEnabled(enabled)
        action.triggered.connect(lambda: self.set_action(text))

    def set_action(self, option):
        """Sets the action which was clicked.

        Args:
            option (str): string with the text description of the action
        """
        self.option = option

    def get_action(self):
        """Returns the clicked action, a string with a description."""
        return self.option


class ProjectItemContextMenu(CustomContextMenu):
    """Context menu for project items both in the QTreeView and in the QGraphicsView.

    Attributes:
        parent (QWidget): Parent for menu widget (ToolboxUI)
        position (QPoint): Position on screen
        index (QModelIndex): Index of item that requested the context-menu
    """
    def __init__(self, parent, position, index):
        """Class constructor."""
        super().__init__(parent)
        if not index.isValid():
            # If no item at index
            if not self._parent.project():
                return
            self.add_action("Open project directory...")
            self.exec_(position)
            return
        if not index.parent().isValid():
            if not self._parent.project():
                return
            # If index is at a category item
            self.add_action("Open project directory...")
            self.exec_(position)
            return
        d = self._parent.project_item_model.project_item(index)
        if d.item_type == "Data Connection":
            self.add_action("Open directory...")
        elif d.item_type == "Data Store":
            self.add_action("Open tree view...")
            self.add_action("Open graph view...")
            self.add_action("Open directory...")
        elif d.item_type == "Tool":
            self.add_action("Execute")
            self.add_action("Results...")
            if d.get_icon().wheel.isVisible():
                self.add_action("Stop")
            else:
                self.add_action("Stop", enabled=False)
            self.addSeparator()
            if not d.tool_template():
                enabled = False
            else:
                enabled = True
            self.add_action("Edit Tool template", enabled=enabled)
            self.add_action("Open main program file", enabled=enabled)
        elif d.item_type == "View":
            pass
        else:
            logging.error("Unknown item type:{0}".format(d.item_type))
            return
        self.addSeparator()
        self.add_action("Rename")
        self.add_action("Remove item")
        self.exec_(position)


class LinkContextMenu(CustomContextMenu):
    """Context menu class for connection links.

    Attributes:
        parent (QWidget): Parent for menu widget (ToolboxUI)
        position (QPoint): Position on screen
        index (QModelIndex): Index of item that requested the context-menu
        parallel_link (Link(QGraphicsPathItem)): Link that is parallel to the one that requested the menu
    """
    def __init__(self, parent, position, index, parallel_link=None):
        """Class constructor."""
        super().__init__(parent)
        if not index.isValid():
            return
        self.add_action("Remove connection")
        if parallel_link:
            self.add_action("Send to bottom")
        self.exec_(position)


class ToolTemplateContextMenu(CustomContextMenu):
    """Context menu class for Tool templates.

    Attributes:
        parent (QWidget): Parent for menu widget (ToolboxUI)
        position (QPoint): Position on screen
        index (QModelIndex): Index of item that requested the context-menu
    """

    def __init__(self, parent, position, index):
        """Class constructor."""
        super().__init__(parent)
        if not index.isValid():
            # If no item at index
            return
        if index.row() == 0:
            # Don't show menu when clicking on No tool
            return
        self.add_action("Edit Tool template")
        self.add_action("Remove Tool template")
        self.addSeparator()
        self.add_action("Open main program file")
        self.add_action("Open definition file")
        self.exec_(position)


class DcRefContextMenu(CustomContextMenu):
    """Context menu class for references view in Data Connection properties.

    Attributes:
        parent (QWidget): Parent for menu widget (ToolboxUI)
        position (QPoint): Position on screen
        index (QModelIndex): Index of item that requested the context-menu
    """
    def __init__(self, parent, position, index):
        """Class constructor."""
        super().__init__(parent)
        if not index.isValid():
            # If no item at index
            self.add_action("Add reference(s)")
            self.add_action("Remove reference(s)")
            self.add_action("Copy reference(s) to project")
        else:
            self.add_action("Edit...")
            self.add_action("Open containing directory...")
            self.addSeparator()
            self.add_action("Add reference(s)")
            self.add_action("Remove reference(s)")
            self.add_action("Copy reference(s) to project")
        self.exec_(position)


class DcDataContextMenu(CustomContextMenu):
    """Context menu class for data view in Data Connection properties.

    Attributes:
        parent (QWidget): Parent for menu widget (ToolboxUI)
        position (QPoint): Position on screen
        index (QModelIndex): Index of item that requested the context-menu
    """
    def __init__(self, parent, position, index):
        """Class constructor."""
        super().__init__(parent)
        if not index.isValid():
            # If no item at index
            self.add_action("New file...")
            self.addSeparator()
            self.add_action("Open Spine Datapackage Editor")
            self.add_action("Open directory...")
        else:
            self.add_action("Edit...")
            self.add_action("New file...")
            self.add_action("Remove file(s)")
            self.addSeparator()
            self.add_action("Open Spine Datapackage Editor")
            self.add_action("Open directory...")
        self.exec_(position)


class ToolPropertiesContextMenu(CustomContextMenu):
    """Common context menu class for all Tool QTreeViews in Tool properties.

    Attributes:
        parent (QWidget): Parent for menu widget (ToolboxUI)
        position (QPoint): Position on screen
        index (QModelIndex): Index of item that requested the context-menu
    """
    def __init__(self, parent, position, index):
        """Class constructor."""
        super().__init__(parent)
        self.add_action("Edit Tool template...")
        self.exec_(position)


class ObjectTreeContextMenu(CustomContextMenu):
    """Context menu class for object tree items in tree view form.

    Attributes:
        parent (QWidget): Parent for menu widget (TreeViewForm)
        position (QPoint): Position on screen
        index (QModelIndex): Index of item that requested the context-menu
    """
    def __init__(self, parent, position, index):
        """Class constructor."""
        super().__init__(parent)
        if not index.isValid():
            return
        copy_icon = self._parent.ui.actionCopy.icon()
        plus_object_icon = self._parent.ui.actionAdd_objects.icon()
        plus_relationship_icon = self._parent.ui.actionAdd_relationships.icon()
        plus_object_parameter_icon = self._parent.ui.actionAdd_object_parameter_values.icon()
        plus_relationship_parameter_icon = self._parent.ui.actionAdd_relationship_parameter_values.icon()
        edit_object_icon = self._parent.ui.actionEdit_objects.icon()
        edit_relationship_icon = self._parent.ui.actionEdit_relationships.icon()
        minus_object_icon = self._parent.ui.actionRemove_object_tree_items.icon()
        fully_expand_icon = self._parent.fully_expand_icon
        fully_collapse_icon = self._parent.fully_collapse_icon
        find_next_icon = self._parent.find_next_icon
        item = index.model().itemFromIndex(index)
        item_type = item.data(Qt.UserRole)
        self.add_action("Copy text", copy_icon)
        self.addSeparator()
        if index.model().hasChildren(index):
            self.add_action("Fully expand", fully_expand_icon)
            self.add_action("Fully collapse", fully_collapse_icon)
        if item_type == 'relationship':
            self.add_action("Find next", find_next_icon)
        self.addSeparator()
        if item_type == 'root':
            self.add_action("Add object classes", plus_object_icon)
        elif item_type == 'object_class':
            self.add_action("Add relationship classes", plus_relationship_icon)
            self.add_action("Add objects", plus_object_icon)
            self.add_action("Add parameter definitions", plus_object_parameter_icon)
            self.addSeparator()
            self.add_action("Edit object classes", edit_object_icon)
        elif item_type == 'object':
            self.add_action("Add parameter values", plus_object_parameter_icon)
            self.addSeparator()
            self.add_action("Edit objects", edit_object_icon)
        elif item_type == 'relationship_class':
            self.add_action("Add relationships", plus_relationship_icon)
            self.add_action("Add parameter definitions", plus_relationship_parameter_icon)
            self.addSeparator()
            self.add_action("Edit relationship classes", edit_relationship_icon)
        elif item_type == 'relationship':
            self.add_action("Add parameter values", plus_relationship_parameter_icon)
            self.addSeparator()
            self.add_action("Edit relationships", edit_relationship_icon)
        if item_type != 'root':
            self.addSeparator()
            self.add_action("Remove selected", minus_object_icon)
        self.exec_(position)


class ParameterContextMenu(CustomContextMenu):
    """Context menu class for object (relationship) parameter (value) items in tree views.

    Attributes:
        parent (QWidget): Parent for menu widget (TreeViewForm)
        position (QPoint): Position on screen
        index (QModelIndex): Index of item that requested the context-menu
    """
    def __init__(self, parent, position, index, remove_icon):
        """Class constructor."""
        super().__init__(parent)
        if not index.isValid():
            return
        copy_icon = self._parent.ui.actionCopy.icon()
        paste_icon = self._parent.ui.actionPaste.icon()
        self.add_action("Copy", copy_icon)
        self.add_action("Paste", paste_icon)
        self.addSeparator()
        self.add_action("Remove selected", remove_icon)
        self.exec_(position)


class GraphViewContextMenu(CustomContextMenu):
    """Context menu class for qgraphics view in graph view.

    Attributes:
        parent (QWidget): Parent for menu widget (GraphViewForm)
        position (QPoint): Position on screen
    """
    def __init__(self, parent, position):
        """Class constructor."""
        super().__init__(parent)
        self.add_action("Hide selected items", enabled=len(parent.object_item_selection) > 0)
        self.add_action("Show hidden items", enabled=len(parent.hidden_items) > 0)
        self.addSeparator()
        self.add_action("Prune selected items", enabled=len(parent.object_item_selection) > 0)
        self.add_action("Reinstate pruned items", enabled=len(parent.rejected_items) > 0)
        self.exec_(position)


class ObjectItemContextMenu(CustomContextMenu):
    """Context menu class for object graphic items in graph view.

    Attributes:
        parent (QWidget): Parent for menu widget (GraphViewForm)
        position (QPoint): Position on screen
        graphics_item (ObjectItem (QGraphicsItem)): item that requested the menu
    """
    def __init__(self, parent, position, graphics_item):
        """Class constructor."""
        super().__init__(parent)
        self.relationship_class_dict = dict()
        object_item_selection_length = len(parent.object_item_selection)
        self.add_action('Hide')
        self.add_action('Prune')
        if parent.read_only:
            self.exec_(position)
            return
        self.addSeparator()
        if graphics_item.is_template:
            self.add_action("Set name", enabled=object_item_selection_length == 1)
        else:
            self.add_action("Rename", enabled=object_item_selection_length == 1)
        self.add_action("Remove")
        self.addSeparator()
        if graphics_item.is_template or object_item_selection_length > 1:
            self.exec_(position)
            return
        for item in parent.relationship_class_list_model.findItems('*', Qt.MatchWildcard):
            relationship_class = item.data(Qt.UserRole + 1)
            if not relationship_class:
                continue
            relationship_class_id = relationship_class['id']
            relationship_class_name = relationship_class['name']
            object_class_id_list = [int(x) for x in relationship_class["object_class_id_list"].split(",")]
            object_class_name_list = relationship_class["object_class_name_list"].split(",")
            fixed_object_class_name_list = object_class_name_list.copy()
            fix_name_ambiguity(fixed_object_class_name_list)
            for i, object_class_name in enumerate(object_class_name_list):
                if object_class_name != graphics_item.object_class_name:
                    continue
                option = "Add '{}' relationship".format(relationship_class['name'])
                fixed_object_class_name = fixed_object_class_name_list[i]
                if object_class_name != fixed_object_class_name:
                    option += " as '{}'".format(fixed_object_class_name)
                self.add_action(option)
                self.relationship_class_dict[option] = {
                    'id': relationship_class_id,
                    'name': relationship_class_name,
                    'object_class_id_list': object_class_id_list,
                    'object_class_name_list': object_class_name_list,
                    'object_name_list': fixed_object_class_name_list,
                    'dimension': i
                }
        self.exec_(position)


class CustomPopupMenu(QMenu):
    """Popup menu master class for several popup menus.

    Attributes:
        parent (QWidget): Parent widget of this pop-up menu
    """
    def __init__(self, parent):
        """Class constructor."""
        super().__init__(parent=parent)
        self._parent = parent

    def add_action(self, text, slot, enabled=True):
        """Adds an action to the popup menu.

        Args:
            text (str): Text description of the action
            slot (method): Method to connect to action's triggered signal
            enabled (bool): Is action enabled?
        """
        action = self.addAction(text)
        action.setEnabled(enabled)
        action.triggered.connect(slot)


class AddToolTemplatePopupMenu(CustomPopupMenu):
    """Popup menu class for add tool template button.

    Attributes:
        parent (QWidget): parent widget (ToolboxUI)
    """
    def __init__(self, parent):
        """Class constructor."""
        super().__init__(parent)
        # Open empty Tool Template Form
        self.add_action("New", self._parent.show_tool_template_form)
        # Add an existing Tool template from file to project
        self.add_action("Add existing...", self._parent.open_tool_template)


class ToolTemplateOptionsPopupMenu(CustomPopupMenu):
    """Popup menu class for tool template options button in Tool item.

    Attributes:
        parent (QWidget): Parent widget of this menu (ToolboxUI)
        tool (Tool): Tool item that is associated with the pressed button
    """
    def __init__(self, parent, tool):
        super().__init__(parent)
        enabled = True if tool.tool_template() else False
        self.add_action("Edit Tool template", tool.edit_tool_template, enabled=enabled)
        self.add_action("Open definition file", tool.open_tool_template_file, enabled=enabled)
        self.add_action("Open main program file", tool.open_tool_main_program_file, enabled=enabled)
        self.addSeparator()
        self.add_action("New Tool template", self._parent.show_tool_template_form)
        self.add_action("Add Tool template...", self._parent.open_tool_template)


class AddIncludesPopupMenu(CustomPopupMenu):
    """Popup menu class for add includes button in Tool Template widget.

    Attributes:
        parent (QWidget): Parent widget (ToolTemplateWidget)
    """
    def __init__(self, parent):
        """Class constructor."""
        super().__init__(parent)
        self._parent = parent
        # Open a tool template file
        self.add_action("New file", self._parent.new_source_file)
        self.addSeparator()
        self.add_action("Open files...", self._parent.show_add_source_files_dialog)


class FilterMenu(QMenu):
    """Filter menu to use together with FilterWidget in TabularViewForm."""
    filterChanged = Signal(object, set, bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._remove_filter = QAction('Remove filters', None)
        self._filter = FilterWidget()
        self._filter_action = QWidgetAction(parent)
        self._filter_action.setDefaultWidget(self._filter)
        self.addAction(self._remove_filter)
        self.addAction(self._filter_action)

        # add connections
        self.aboutToHide.connect(self._cancel_filter)
        self.aboutToShow.connect(self._check_filter)
        self._remove_filter.triggered.connect(self._clear_filter)
        self._filter.okPressed.connect(self._change_filter)
        self._filter.cancelPressed.connect(self.hide)

    def add_items_to_filter_list(self, items):
        self._filter._filter_model.add_item(items)
        self._filter.save_state()

    def remove_items_from_filter_list(self, items):
        self._filter._filter_model.remove_items(items)
        self._filter.save_state()

    def set_filter_list(self, data):
        self._filter.set_filter_list(data)

    def _clear_filter(self):
        self._filter.clear_filter()
        self._change_filter()

    def _check_filter(self):
        self._remove_filter.setEnabled(self._filter.has_filter())

    def _cancel_filter(self):
        self._filter._cancel_filter()

    def _change_filter(self):
        valid_values = set(self._filter._filter_state)
        if self._filter._filter_empty_state:
            valid_values.add(None)
        self.filterChanged.emit(self, valid_values, self._filter.has_filter())
        self.hide()


class PivotTableModelMenu(QMenu):
    def __init__(self, model, proxy_model, parent=None):
        super().__init__(parent)
        self._model = model
        self._proxy = proxy_model
        self.relationship_tuple_key = ()
        self.class_type = ""

        # strings
        self._DELETE_INDEX = "Delete selected indexes"
        self._DELETE_RELATIONSHIP = "Delete selected relationships"
        self._RELATIONSHIP_CLASS = "relationship"

        # actions
        self.restore_values_action = self.addAction('Restore selected values')
        self.delete_values_action = self.addAction('Delete selected values')
        self.delete_index_action = self.addAction(self._DELETE_INDEX)
        self.delete_relationship_action = self.addAction(self._DELETE_RELATIONSHIP)
        self.delete_invalid_row_action = self.addAction('Delete selected invalid rows')
        self.delete_invalid_col_action = self.addAction('Delete selected invalid columns')
        self.insert_row_action = self.addAction('Insert rows')
        self.insert_col_action = self.addAction('Insert columns')

        # connect signals
        self.restore_values_action.triggered.connect(self.restore_values)
        self.delete_values_action.triggered.connect(self.delete_values)
        self.delete_index_action.triggered.connect(self.delete_index_values)
        self.delete_relationship_action.triggered.connect(self.delete_relationship_values)
        self.delete_invalid_row_action.triggered.connect(self.delete_invalid_row)
        self.delete_invalid_col_action.triggered.connect(self.delete_invalid_col)
        self.insert_row_action.triggered.connect(self.insert_row)
        self.insert_col_action.triggered.connect(self.insert_col)

    def _find_selected_indexes(self, indexes):
        """Find any selected index values"""
        selected = {}
        for i in indexes:
            index_name = None
            if self._model.index_in_column_headers(i):
                value = self.pivot_table_model.data(i)
                if value:
                    index_name = self._model.model.pivot_columns[i.row()]
            elif self._model.index_in_row_headers(i):
                value = self._model.data(i)
                if value:
                    index_name = self._model.model.pivot_rows[i.column()]
            if index_name and index_name in self._model.model._unique_name_2_name:
                index_name = self._model.model._unique_name_2_name[index_name]
                if index_name in selected:
                    selected[index_name].add(value)
                else:
                    selected[index_name] = set([value])
        return selected

    def _find_selected_relationships(self, indexes):
        """Find any selected tuple combinations in self.relationship_tuple_key"""
        pos = [self._model.model.index_names.index(n) for n in self.relationship_tuple_key]
        getter = tuple_itemgetter(itemgetter(*pos), len(pos))
        selected = set()
        for i in indexes:
            if self._model.index_in_column_headers(i) or self._model.index_in_row_headers(i):
                if (i.row() - self._model._num_headers_row in self._model.model._invalid_row
                    or i.column() - self._model._num_headers_column in self._model.model._invalid_column):
                    continue
                key = self._model.get_key(i)
                key = getter(key)
                if all(key):
                    selected.add(key)
        return selected

    def _get_selected_indexes(self):
        """Find selected indexes of parent, map to source if proxy is given"""
        indexes = self.parent().selectedIndexes()
        if self._proxy:
            indexes = [self._proxy.mapToSource(i) for i in indexes]
        return indexes

    def delete_invalid_row(self):
        return

    def delete_invalid_col(self):
        return

    def insert_row(self):
        return

    def insert_col(self):
        return

    def delete_values(self):
        """deletes selected indexes in pivot_table"""
        indexes = self._get_selected_indexes()
        self._model.delete_values(indexes)

    def restore_values(self):
        """restores edited selected indexes in pivot_table"""
        indexes = self._get_selected_indexes()
        self._model.restore_values(indexes)

    def delete_index_values(self):
        """finds selected index items and deletes"""
        indexes = self._get_selected_indexes()
        delete_dict = self._find_selected_indexes(indexes)
        if delete_dict:
            self._model.delete_index_values(delete_dict)

    def delete_relationship_values(self):
        """finds selected relationships deletes"""
        indexes = self._get_selected_indexes()
        delete_tuples = self._find_selected_relationships(indexes)
        if delete_tuples:
            self._model.delete_tuple_index_values({self.relationship_tuple_key: delete_tuples})

    def request_menu(self, QPos=None):
        indexes = self._get_selected_indexes()
        self.delete_relationship_action.setText(self._DELETE_RELATIONSHIP)
        self.delete_relationship_action.setEnabled(False)

        if len(indexes) > 1:
            # more than one index selected
            if (any(self._model.index_in_column_headers(i) for i in indexes) or
                any(self._model.index_in_row_headers(i) for i in indexes)):
                self.delete_index_action.setText(self._DELETE_INDEX)
                self.delete_index_action.setEnabled(True)
                if self.class_type == self._RELATIONSHIP_CLASS:
                    self.delete_relationship_action.setText(self._DELETE_RELATIONSHIP)
                    self.delete_relationship_action.setEnabled(True)

        elif len(indexes) == 1:
            # one selected, show names
            selected_index = self._find_selected_indexes(indexes)
            if selected_index:
                index_name = list(selected_index.keys())[0]
                index_value = list(selected_index[index_name])[0]
                self.delete_index_action.setText("Delete {}: {}".format(index_name, index_value))
                self.delete_index_action.setEnabled(True)
            else:
                self.delete_index_action.setText(self._DELETE_INDEX)
                self.delete_index_action.setEnabled(False)

            if self.class_type == self._RELATIONSHIP_CLASS:
                relationship = self._find_selected_relationships(indexes)
                if relationship:
                    relationship = list(relationship)[0]
                    self.delete_relationship_action.setText("Delete relationship: {}".format(", ".join(relationship)))
                    self.delete_relationship_action.setEnabled(True)

        pPos=self.parent().mapToGlobal(QPoint(5, 20))
        mPos=pPos+QPos
        self.move(mPos)
        self.show()
