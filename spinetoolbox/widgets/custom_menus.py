######################################################################################################################
# Copyright (C) 2017 - 2019 Spine project consortium
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
import os
from operator import itemgetter
from PySide2.QtWidgets import QMenu, QWidgetAction, QAction, QMessageBox, QWidget
from PySide2.QtGui import QIcon
from PySide2.QtCore import Qt, Signal, Slot, QPoint
from helpers import fix_name_ambiguity, tuple_itemgetter
from plotting import plot_pivot_column, plot_selection, PlottingError, PivotTablePlottingHints
from widgets.custom_qwidgets import FilterWidget
from widgets.parameter_value_editor import ParameterValueEditor
from widgets.report_plotting_failure import report_plotting_failure


def handle_plotting_failure(error):
    """Reports a PlottingError exception to the user."""
    errorBox = QMessageBox()
    errorBox.setWindowTitle("Plotting failed")
    errorBox.setText(error.message)
    errorBox.exec()


class CustomContextMenu(QMenu):
    """Context menu master class for several context menus.

    Attributes:
        parent (QWidget): Parent for menu widget (ToolboxUI)
        position (QPoint): Position on screen
    """

    def __init__(self, parent, position):
        """Constructor."""
        super().__init__(parent=parent)
        self._parent = parent
        self.position = position
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
        self.exec_(self.position)
        return self.option


class CategoryProjectItemContextMenu(CustomContextMenu):
    """Context menu for category project items in the QTreeView.

    Attributes:
        parent (QWidget): Parent for menu widget (ToolboxUI)
        position (QPoint): Position on screen
    """

    def __init__(self, parent, position):
        """Class constructor."""
        super().__init__(parent, position)
        self.add_action("Open project directory...")


class ProjectItemModelContextMenu(CustomContextMenu):
    """Context menu for project item model in the QTreeView.

    Attributes:
        parent (QWidget): Parent for menu widget (ToolboxUI)
        position (QPoint): Position on screen
    """

    def __init__(self, parent, position):
        """Class constructor."""
        super().__init__(parent, position)
        self.add_action("Open project directory...")
        self.addSeparator()
        self.add_action("Export project to GraphML")


class ProjectItemContextMenu(CustomContextMenu):
    """Context menu for project items in the QTreeView and in the QGraphicsView.

    Attributes:
        parent (QWidget): Parent for menu widget (ToolboxUI)
        position (QPoint): Position on screen
    """

    def __init__(self, parent, position):
        """Class constructor."""
        super().__init__(parent, position)
        self.add_action("Open directory...")
        self.addSeparator()
        self.add_action("Rename")
        self.add_action("Remove item")


class LinkContextMenu(CustomContextMenu):
    """Context menu class for connection links.

    Attributes:
        parent (QWidget): Parent for menu widget (ToolboxUI)
        position (QPoint): Position on screen
        parallel_link (Link(QGraphicsPathItem)): Link that is parallel to the one that requested the menu
    """

    def __init__(self, parent, position, parallel_link=None):
        """Class constructor."""
        super().__init__(parent, position)
        self.add_action("Remove connection")
        self.add_action("Take connection")
        if parallel_link:
            self.add_action("Send to bottom")


class ToolTemplateContextMenu(CustomContextMenu):
    """Context menu class for Tool templates.

    Attributes:
        parent (QWidget): Parent for menu widget (ToolboxUI)
        position (QPoint): Position on screen
        index (QModelIndex): Index of item that requested the context-menu
    """

    def __init__(self, parent, position, index):
        """Class constructor."""
        super().__init__(parent, position)
        if not index.isValid():
            # If no item at index
            return
        self.add_action("Edit Tool template")
        self.add_action("Edit main program file...")
        self.add_action("Open main program directory...")
        self.add_action("Open Tool template definition file...")
        self.addSeparator()
        self.add_action("Remove Tool template")


class ObjectTreeContextMenu(CustomContextMenu):
    """Context menu class for object tree items in tree view form.

    Attributes:
        parent (QWidget): Parent for menu widget (TreeViewForm)
        position (QPoint): Position on screen
        index (QModelIndex): Index of item that requested the context-menu
    """

    def __init__(self, parent, position, index):
        """Class constructor."""
        super().__init__(parent, position)
        if not index.isValid():
            return
        copy_icon = self._parent.ui.actionCopy.icon()
        plus_object_icon = self._parent.ui.actionAdd_objects.icon()
        plus_relationship_icon = self._parent.ui.actionAdd_relationships.icon()
        edit_object_icon = self._parent.ui.actionEdit_objects.icon()
        edit_relationship_icon = self._parent.ui.actionEdit_relationships.icon()
        remove_icon = QIcon(":/icons/menu_icons/cube_minus.svg")
        fully_expand_icon = self._parent.fully_expand_icon
        fully_collapse_icon = self._parent.fully_collapse_icon
        find_next_icon = self._parent.find_next_icon
        item_type = index.data(Qt.UserRole)
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
            self.addSeparator()
            self.add_action("Edit object classes", edit_object_icon)
        elif item_type == 'object':
            self.addSeparator()
            self.add_action("Edit objects", edit_object_icon)
        elif item_type == 'relationship_class':
            self.add_action("Add relationships", plus_relationship_icon)
            self.addSeparator()
            self.add_action("Edit relationship classes", edit_relationship_icon)
        elif item_type == 'relationship':
            self.addSeparator()
            self.add_action("Edit relationships", edit_relationship_icon)
        if item_type != 'root':
            self.addSeparator()
            self.add_action("Remove selection", remove_icon)


class RelationshipTreeContextMenu(CustomContextMenu):
    """Context menu class for relationship tree items in tree view form.

    Attributes:
        parent (QWidget): Parent for menu widget (TreeViewForm)
        position (QPoint): Position on screen
        index (QModelIndex): Index of item that requested the context-menu
    """

    def __init__(self, parent, position, index):
        """Class constructor."""
        super().__init__(parent, position)
        if not index.isValid():
            return
        copy_icon = self._parent.ui.actionCopy.icon()
        plus_relationship_icon = self._parent.ui.actionAdd_relationships.icon()
        edit_relationship_icon = self._parent.ui.actionEdit_relationships.icon()
        remove_icon = QIcon(":/icons/menu_icons/cubes_minus.svg")
        item_type = index.data(Qt.UserRole)
        self.add_action("Copy text", copy_icon)
        self.addSeparator()
        if item_type == 'root':
            self.add_action("Add relationship classes", plus_relationship_icon)
        elif item_type == 'relationship_class':
            self.add_action("Add relationships", plus_relationship_icon)
            self.addSeparator()
            self.add_action("Edit relationship classes", edit_relationship_icon)
        elif item_type == 'relationship':
            self.add_action("Edit relationships", edit_relationship_icon)
        if item_type != 'root':
            self.addSeparator()
            self.add_action("Remove selection", remove_icon)


class ParameterContextMenu(CustomContextMenu):
    """Context menu class for object (relationship) parameter items in tree views.

    Attributes:
        parent (QWidget): Parent for menu widget (TreeViewForm)
        position (QPoint): Position on screen
        index (QModelIndex): Index of item that requested the context-menu
    """

    def __init__(self, parent, position, index):
        """Class constructor."""
        super().__init__(parent, position)
        if not index.isValid():
            return
        copy_icon = self._parent.ui.actionCopy.icon()
        paste_icon = self._parent.ui.actionPaste.icon()
        remove_icon = QIcon(":/icons/menu_icons/cog_minus.svg")
        self.add_action("Copy", copy_icon)
        self.add_action("Paste", paste_icon)
        self.addSeparator()
        self.add_action("Remove selection", remove_icon)


class SimpleEditableParameterValueContextMenu(CustomContextMenu):
    """
    Context menu class for object (relationship) parameter value items in graph views.

    Attributes:
        parent (QWidget): Parent for menu widget (TreeViewForm)
        position (QPoint): Position on screen
        index (QModelIndex): Index of item that requested the context-menu
    """

    def __init__(self, parent, position, index):
        """Class constructor."""
        super().__init__(parent, position)
        if not index.isValid():
            return
        self.add_action("Open in editor...")
        self.addSeparator()
        self.add_action("Plot")


class EditableParameterValueContextMenu(CustomContextMenu):
    """
    Context menu class for object (relationship) parameter value items in tree views.

    Attributes:
        parent (QWidget): Parent for menu widget (TreeViewForm)
        position (QPoint): Position on screen
        index (QModelIndex): Index of item that requested the context-menu
    """

    def __init__(self, parent, position, index):
        super().__init__(parent, position)
        if not index.isValid():
            return
        copy_icon = self._parent.ui.actionCopy.icon()
        paste_icon = self._parent.ui.actionPaste.icon()
        remove_icon = QIcon(":/icons/menu_icons/cog_minus.svg")
        self.add_action("Open in editor...")
        self.addSeparator()
        self.add_action("Plot")
        self.addSeparator()
        self.add_action("Copy", copy_icon)
        self.add_action("Paste", paste_icon)
        self.addSeparator()
        self.add_action("Remove selection", remove_icon)


class ParameterValueListContextMenu(CustomContextMenu):
    """Context menu class for parameter enum view in tree view form.

    Attributes:
        parent (QWidget): Parent for menu widget (TreeViewForm)
        position (QPoint): Position on screen
        index (QModelIndex): Index of item that requested the context-menu
    """

    def __init__(self, parent, position, index):
        """Class constructor."""
        super().__init__(parent, position)
        if not index.isValid():
            return
        copy_icon = self._parent.ui.actionCopy.icon()
        remove_icon = QIcon(":/icons/minus.png")
        self.add_action("Copy", copy_icon)
        self.addSeparator()
        self.add_action("Remove selection", remove_icon)


class GraphViewContextMenu(CustomContextMenu):
    """Context menu class for qgraphics view in graph view.

    Attributes:
        parent (QWidget): Parent for menu widget (GraphViewForm)
        position (QPoint): Position on screen
    """

    def __init__(self, parent, position):
        """Class constructor."""
        super().__init__(parent, position)
        self.add_action("Hide selected items", enabled=len(parent.object_item_selection) > 0)
        self.add_action("Show hidden items", enabled=len(parent.hidden_items) > 0)
        self.addSeparator()
        self.add_action("Prune selected items", enabled=len(parent.object_item_selection) > 0)
        self.add_action("Reinstate pruned items", enabled=len(parent.rejected_items) > 0)


class ObjectItemContextMenu(CustomContextMenu):
    """Context menu class for object graphic items in graph view.

    Attributes:
        parent (QWidget): Parent for menu widget (GraphViewForm)
        position (QPoint): Position on screen
        graphics_item (ObjectItem (QGraphicsItem)): item that requested the menu
    """

    def __init__(self, parent, position, graphics_item):
        """Class constructor."""
        super().__init__(parent, position)
        self.relationship_class_dict = dict()
        object_item_selection_length = len(parent.object_item_selection)
        self.add_action('Hide')
        self.add_action('Prune')
        if parent.read_only:
            return
        self.addSeparator()
        if graphics_item.is_template:
            self.add_action("Set name", enabled=object_item_selection_length == 1)
        else:
            self.add_action("Rename", enabled=object_item_selection_length == 1)
        self.add_action("Remove")
        self.addSeparator()
        if graphics_item.is_template or object_item_selection_length > 1:
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
                    'dimension': i,
                }


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
    """Popup menu class for add Tool template button.

    Attributes:
        parent (QWidget): parent widget (ToolboxUI)
    """

    def __init__(self, parent):
        """Class constructor."""
        super().__init__(parent)
        # Open empty Tool template Form
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
        enabled = bool(tool.tool_template())
        self.add_action("Edit Tool template", tool.edit_tool_template, enabled=enabled)
        self.add_action("Edit main program file...", tool.open_tool_main_program_file, enabled=enabled)
        self.add_action("Open main program directory...", tool.open_tool_main_directory, enabled=enabled)
        self.add_action("Open definition file", tool.open_tool_template_file, enabled=enabled)
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


class CreateMainProgramPopupMenu(CustomPopupMenu):
    """Popup menu class for add main program QToolButton in Tool Template editor.

    Attributes:
        parent (QWidget): Parent widget (ToolTemplateWidget)
    """

    def __init__(self, parent):
        """Class constructor."""
        super().__init__(parent)
        self._parent = parent
        # Open a tool template file
        self.add_action("Make new main program", self._parent.new_main_program_file)
        self.add_action("Select existing main program", self._parent.browse_main_program)


class RecentProjectsPopupMenu(CustomPopupMenu):
    """Recent projects menu embedded to 'File-Open recent' QAction."""

    def __init__(self, parent):
        """

        Args:
            parent (QWidget): Parent widget of this menu (ToolboxUI)
        """
        super().__init__(parent=parent)
        self._parent = parent
        self.add_recent_projects()

    def add_recent_projects(self):
        """Reads the previous project names and paths from QSettings. Ads them to the QMenu as QActions."""
        recents = self._parent.qsettings().value("appSettings/recentProjects", defaultValue=None)
        if recents:
            recents = str(recents)
            recents_list = recents.split("\n")
            for entry in recents_list:
                name, filepath = entry.split("<>")
                self.add_action(name, lambda checked=False, filepath=filepath: self.call_open_project(
                        checked, filepath))

    @Slot(bool, str, name="call_open_project")
    def call_open_project(self, checked, p):
        """Slot for catching the user selected action from the recent projects menu.

        Args:
            checked (bool): Argument sent by triggered signal
            p (str): Full path to a project file
        """
        if not os.path.exists(p):
            # Project has been removed, remove it from recent projects list
            self._parent.remove_path_from_recent_projects(p)
            return
        # Check if the same project is already open
        if self._parent.project():
            if p == self._parent.project().path:
                self._parent.msg.emit("Project already open")
                return
        if not self._parent.open_project(p):
            return


class FilterMenu(QMenu):
    """Filter menu to use together with FilterWidget in TabularViewForm."""

    filterChanged = Signal(object, set, bool)

    def __init__(self, parent=None, show_empty=True):
        super().__init__(parent)
        self._remove_filter = QAction('Remove filters', None)
        self._filter = FilterWidget(show_empty=show_empty)
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
        self.open_value_editor_action = self.addAction('Open in editor...')
        self.addSeparator()
        self.plot_action = self.addAction('Plot')
        self.addSeparator()
        self.restore_values_action = self.addAction('Restore selected values')
        self.delete_values_action = self.addAction('Delete selected values')
        self.delete_index_action = self.addAction(self._DELETE_INDEX)
        self.delete_relationship_action = self.addAction(self._DELETE_RELATIONSHIP)
        self.delete_invalid_row_action = self.addAction('Delete selected invalid rows')
        self.delete_invalid_col_action = self.addAction('Delete selected invalid columns')
        self.insert_row_action = self.addAction('Insert rows')
        self.insert_col_action = self.addAction('Insert columns')

        # connect signals
        self.open_value_editor_action.triggered.connect(self.open_value_editor)
        self.plot_action.triggered.connect(self.plot)
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
                value = self._model.data(i)
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
                if (
                    i.row() - self._model._num_headers_row in self._model.model._invalid_row
                    or i.column() - self._model._num_headers_column in self._model.model._invalid_column
                ):
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

    def delete_invalid_row(self):  # pylint: disable=no-self-use
        return

    def delete_invalid_col(self):  # pylint: disable=no-self-use
        return

    def insert_row(self):  # pylint: disable=no-self-use
        return

    def insert_col(self):  # pylint: disable=no-self-use
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

    def open_value_editor(self):
        """Opens the parameter value editor for the first selected cell."""
        model_index = self._get_selected_indexes()[0]
        value_name = ", ".join(self._model.get_key(model_index))
        value_editor = ParameterValueEditor(model_index, value_name, parent_widget=self.parent())
        value_editor.show()

    def plot(self):
        """Plots the selected cells in the pivot table."""
        selected_indexes = self._get_selected_indexes()
        hints = PivotTablePlottingHints()
        try:
            plot_window = plot_selection(self._model, selected_indexes, hints)
        except PlottingError as error:
            report_plotting_failure(error)
            return
        plotted_column_names = set()
        for index in selected_indexes:
            label = hints.column_label(self._model, index.column())
            plotted_column_names.add(label)
        plot_window.setWindowTitle("Plot    -- {} --".format(", ".join(plotted_column_names)))
        plot_window.show()

    def request_menu(self, QPos=None):
        """Shows the context menu on the screen."""
        indexes = self._get_selected_indexes()
        self.delete_relationship_action.setText(self._DELETE_RELATIONSHIP)
        self.delete_relationship_action.setEnabled(False)

        if len(indexes) > 1:
            # more than one index selected
            self.open_value_editor_action.setEnabled(False)
            self.plot_action.setEnabled(any(self._model.index_in_data(index) for index in indexes))
            if any(self._model.index_in_column_headers(i) for i in indexes) or any(
                self._model.index_in_row_headers(i) for i in indexes
            ):
                self.delete_index_action.setText(self._DELETE_INDEX)
                self.delete_index_action.setEnabled(True)
                if self.class_type == self._RELATIONSHIP_CLASS:
                    self.delete_relationship_action.setText(self._DELETE_RELATIONSHIP)
                    self.delete_relationship_action.setEnabled(True)

        elif len(indexes) == 1:
            # one selected, show names
            selected_index = self._find_selected_indexes(indexes)
            index_in_data = self._model.index_in_data(indexes[0])
            self.open_value_editor_action.setEnabled(index_in_data)
            self.plot_action.setEnabled(index_in_data)
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

        pPos = self.parent().mapToGlobal(QPoint(5, 20))
        mPos = pPos + QPos
        self.move(mPos)
        self.show()


class PivotTableHorizontalHeaderMenu(QMenu):
    """
    A context menu for the horizontal header of a pivot table.

    Attributes:
         model (PivotTableModel): a model
         parent (QWidget): a parent widget
    """

    def __init__(self, model, parent=None):
        super().__init__(parent)
        self._model = model
        self._model_index = None
        self._plot_action = self.addAction("Plot single column")
        self._plot_action.triggered.connect(self._plot_column)
        self._set_as_X_action = self.addAction("Use as X")
        self._set_as_X_action.setCheckable(True)
        self._set_as_X_action.triggered.connect(self._set_x_flag)

    @Slot(name="_plot_column")
    def _plot_column(self):
        """Plots a single column not the selection."""
        try:
            support = PivotTablePlottingHints()
            plot_window = plot_pivot_column(self._model, self._model_index.column(), support)
        except PlottingError as error:
            report_plotting_failure(error)
            return
        plot_window.setWindowTitle(
            "Plot    -- {} --".format(support.column_label(self._model, self._model_index.column()))
        )
        plot_window.show()

    @Slot("QPoint", name="request_menu")
    def request_menu(self, pos):
        """Shows the context menu on the screen."""
        self.move(self.parent().mapToGlobal(pos))
        self._model_index = self.parent().indexAt(pos)
        if self._model.index_in_top_left(self._model_index):
            self._plot_action.setEnabled(False)
            self._set_as_X_action.setEnabled(False)
            self._set_as_X_action.setChecked(False)
        else:
            self._plot_action.setEnabled(True)
            self._set_as_X_action.setEnabled(True)
            self._set_as_X_action.setChecked(self._model_index.column() == self._model.plot_x_column)
        self.show()

    @Slot(name="_set_x_flag")
    def _set_x_flag(self):
        """Sets the X flag for a column."""
        self._model.set_plot_x_column(self._model_index.column(), self._set_as_X_action.isChecked())
