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

import os
from operator import itemgetter
from PySide2.QtWidgets import QMenu, QWidgetAction, QAction
from PySide2.QtGui import QIcon
from PySide2.QtCore import Signal, Slot, QPoint, QEvent
from ..helpers import fix_name_ambiguity, tuple_itemgetter
from ..plotting import plot_pivot_column, plot_selection, PlottingError, PivotTablePlottingHints
from .custom_qwidgets import FilterWidget
from .parameter_value_editor import ParameterValueEditor
from .report_plotting_failure import report_plotting_failure


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
    """Context menu for project items in the Project tree widget and in the Design View."""

    def __init__(self, parent, position):
        """
        Args:
            parent (QWidget): Parent for menu widget (ToolboxUI)
            position (QPoint): Position on screen
        """
        super().__init__(parent, position)
        self.add_action("Copy")
        self.add_action("Paste")
        self.add_action("Duplicate")
        self.addSeparator()
        self.add_action("Open directory...")
        self.addSeparator()
        self.add_action("Rename")
        self.add_action("Remove item")


class LinkContextMenu(CustomContextMenu):
    """Context menu class for connection links.

    Attributes:
        parent (QWidget): Parent for menu widget (ToolboxUI)
        position (QPoint): Position on screen
        link (Link(QGraphicsPathItem)): Link that requested the menu
    """

    def __init__(self, parent, position, link):
        """Class constructor."""
        super().__init__(parent, position)
        self.add_action("Remove connection")
        self.add_action("Take connection")
        if link.has_parallel_link():
            self.add_action("Send to bottom")


class ToolSpecificationContextMenu(CustomContextMenu):
    """Context menu class for Tool specifications.

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
        self.add_action("Edit Tool specification")
        self.add_action("Edit main program file...")
        self.add_action("Open main program directory...")
        self.add_action("Open Tool specification file...")
        self.addSeparator()
        self.add_action("Remove Tool specification")


class EntityTreeContextMenu(CustomContextMenu):
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
        item = index.model().item_from_index(index)
        self.add_action("Copy text", QIcon(":/icons/menu_icons/copy.svg"))
        self.addSeparator()
        for action_block in item.context_menu_actions:
            for text, icon in action_block.items():
                self.add_action(text, icon)
            self.addSeparator()


class ObjectTreeContextMenu(EntityTreeContextMenu):
    """Context menu class for object tree items in tree view form.

    Attributes:
        parent (QWidget): Parent for menu widget (TreeViewForm)
        position (QPoint): Position on screen
        index (QModelIndex): Index of item that requested the context-menu
    """

    def __init__(self, parent, position, index):
        """Class constructor."""
        super().__init__(parent, position, index)
        item = index.model().item_from_index(index)
        if item.has_children():
            self.addSeparator()
            self.add_action("Fully expand", QIcon(":/icons/menu_icons/angle-double-right.svg"))
            self.add_action("Fully collapse", QIcon(":/icons/menu_icons/angle-double-left.svg"))


class RelationshipTreeContextMenu(EntityTreeContextMenu):
    """Context menu class for relationship tree items in tree view form.

    Attributes:
        parent (QWidget): Parent for menu widget (TreeViewForm)
        position (QPoint): Position on screen
        index (QModelIndex): Index of item that requested the context-menu
    """


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
        self.add_action("Hide selected", enabled=len(parent.entity_item_selection) > 0)
        self.add_action("Show hidden", enabled=len(parent.hidden_items) > 0)
        self.addSeparator()
        self.add_action("Prune selected", enabled=len(parent.entity_item_selection) > 0)
        self.add_action("Restore pruned", enabled=len(parent.rejected_items) > 0)


class EntityItemContextMenu(CustomContextMenu):
    """Context menu class for entity graphic items in graph view."""

    def __init__(self, parent, position):
        """Class constructor.

        Args:
            parent (QWidget): Parent for menu widget (GraphViewForm)
            position (QPoint): Position on screen
        """
        super().__init__(parent, position)
        self.selection_count = len(parent.entity_item_selection)
        self.add_action('Hide')
        self.add_action('Prune')


class ObjectItemContextMenu(EntityItemContextMenu):
    def __init__(self, parent, position, graphics_item):
        """Class constructor.

        Args:
            parent (QWidget): Parent for menu widget (GraphViewForm)
            position (QPoint): Position on screen
            graphics_item (ObjectItem (QGraphicsItem)): item that requested the menu
        """
        super().__init__(parent, position)
        self.addSeparator()
        if graphics_item.is_wip:
            self.add_action("Set name", enabled=self.selection_count == 1)
        else:
            self.add_action("Rename", enabled=self.selection_count == 1)
        self.add_action("Remove")
        if graphics_item.is_wip or self.selection_count > 1:
            return
        self.addSeparator()
        self.relationship_class_dict = dict()
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
        """Class constructor.

        Args:
            parent (QWidget): Parent for menu widget (GraphViewForm)
            position (QPoint): Position on screen
        """
        super().__init__(parent, position)
        self.addSeparator()
        self.add_action("Remove")


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


class AddToolSpecificationPopupMenu(CustomPopupMenu):
    """Popup menu class for add Tool specification button.

    Attributes:
        parent (QWidget): parent widget (ToolboxUI)
    """

    def __init__(self, parent):
        """Class constructor."""
        super().__init__(parent)
        # Open empty Tool specification Form
        self.add_action("New", self._parent.show_tool_specification_form)
        # Add an existing Tool specification from file to project
        self.add_action("Add existing...", self._parent.open_tool_specification)


class ToolSpecificationOptionsPopupmenu(CustomPopupMenu):
    """Popup menu class for tool specification options button in Tool item.

    Attributes:
        parent (QWidget): Parent widget of this menu (ToolboxUI)
        tool (Tool): Tool item that is associated with the pressed button
    """

    def __init__(self, parent, tool):
        super().__init__(parent)
        enabled = bool(tool.tool_specification())
        self.add_action("Edit Tool specification", tool.edit_tool_specification, enabled=enabled)
        self.add_action("Edit main program file...", tool.open_tool_main_program_file, enabled=enabled)
        self.add_action("Open main program directory...", tool.open_tool_main_directory, enabled=enabled)
        self.add_action("Open definition file", tool.open_tool_specification_file, enabled=enabled)
        self.addSeparator()
        self.add_action("New Tool specification", self._parent.show_tool_specification_form)
        self.add_action("Add Tool specification...", self._parent.open_tool_specification)


class AddIncludesPopupMenu(CustomPopupMenu):
    """Popup menu class for add includes button in Tool specification editor widget.

    Attributes:
        parent (QWidget): Parent widget (ToolSpecificationWidget)
    """

    def __init__(self, parent):
        """Class constructor."""
        super().__init__(parent)
        self._parent = parent
        # Open a tool specification file
        self.add_action("New file", self._parent.new_source_file)
        self.addSeparator()
        self.add_action("Open files...", self._parent.show_add_source_files_dialog)


class CreateMainProgramPopupMenu(CustomPopupMenu):
    """Popup menu class for add main program QToolButton in Tool specification editor widget.

    Attributes:
        parent (QWidget): Parent widget (ToolSpecificationWidget)
    """

    def __init__(self, parent):
        """Class constructor."""
        super().__init__(parent)
        self._parent = parent
        # Open a tool specification file
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
                self.add_action(
                    name, lambda checked=False, filepath=filepath: self.call_open_project(checked, filepath)
                )

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
    """Filter menu to use together with FilterWidget in TabularViewMixin."""

    filterChanged = Signal(object, set, bool)

    def __init__(self, parent=None, show_empty=True):
        super().__init__(parent)
        self.object_class_name = None
        self.unique_name = None
        self._remove_filter = QAction('Remove filters', None)
        self._filter = FilterWidget(show_empty=show_empty)
        self._filter_action = QWidgetAction(parent)
        self._filter_action.setDefaultWidget(self._filter)
        self.addAction(self._remove_filter)
        self.addAction(self._filter_action)
        self.anchor = parent

        # add connections
        self.aboutToHide.connect(self._cancel_filter)
        self.aboutToShow.connect(self._check_filter)
        self._remove_filter.triggered.connect(self._clear_filter)
        self._filter.okPressed.connect(self._change_filter)
        self._filter.cancelPressed.connect(self.hide)

    def add_items_to_filter_list(self, items):
        self._filter._filter_model.add_items(items)
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

    def event(self, event):
        if event.type() == QEvent.Show and self.anchor is not None:
            if self.anchor.area == "rows":
                pos = self.anchor.mapToGlobal(QPoint(0, 0)) + QPoint(0, self.anchor.height())
            elif self.anchor.area == "columns":
                pos = self.anchor.mapToGlobal(QPoint(0, 0)) + QPoint(self.anchor.width(), 0)
            self.move(pos)
        return super().event(event)


class PivotTableModelMenu(QMenu):

    _DELETE_OBJECT = "Delete selected objects"
    _DELETE_RELATIONSHIP = "Delete selected relationships"

    def __init__(self, parent):
        """
        Args:
            parent (TabularViewMixin)
        """
        super().__init__(parent)
        self._table = parent.ui.pivot_table
        self._proxy = self._table.model()
        self._source = self._proxy.sourceModel()

        # actions
        self.open_value_editor_action = self.addAction('Open in editor...')
        self.addSeparator()
        self.plot_action = self.addAction('Plot')
        self.addSeparator()
        self.restore_values_action = self.addAction('Restore selected values')
        self.delete_values_action = self.addAction('Delete selected values')
        self.delete_object_action = self.addAction(self._DELETE_OBJECT)
        self.delete_relationship_action = self.addAction(self._DELETE_RELATIONSHIP)

        # connect signals
        self.open_value_editor_action.triggered.connect(self.open_value_editor)
        self.plot_action.triggered.connect(self.plot)
        self.restore_values_action.triggered.connect(self.restore_values)
        self.delete_values_action.triggered.connect(self.delete_values)
        self.delete_object_action.triggered.connect(self.delete_objects)
        self.delete_relationship_action.triggered.connect(self.delete_relationships)

        # TODO
        # self.delete_invalid_row_action = self.addAction('Delete selected invalid rows')
        # self.delete_invalid_col_action = self.addAction('Delete selected invalid columns')
        # self.insert_row_action = self.addAction('Insert rows')
        # self.insert_col_action = self.addAction('Insert columns')
        #
        # self.delete_invalid_row_action.triggered.connect(self.delete_invalid_row)
        # self.delete_invalid_col_action.triggered.connect(self.delete_invalid_col)
        # self.insert_row_action.triggered.connect(self.insert_row)
        # self.insert_col_action.triggered.connect(self.insert_col)

    def _find_selected_objects(self, indexes):
        """Returns objects from given indexes keyed by class.

        Returns:
            dict(str,set)
        """
        selected = {}
        for i in indexes:
            index_name = None
            value = self._source.data(i)
            if value:
                if self._source.index_in_column_headers(i):
                    index_name = self._source.model.pivot_columns[i.row()]
                elif self._source.index_in_row_headers(i):
                    index_name = self._source.model.pivot_rows[i.column()]
            index_name = self._source.model._unique_name_2_name.get(index_name)
            if index_name is not None:
                selected.setdefault(index_name, set()).add(value)
        return selected

    def _find_selected_relationships(self, indexes):
        """Returns relationships from given indexes.

        Returns:
            dict(tuple,set)
        """
        relationship_tuple_key = self.parent().relationship_tuple_key
        if not relationship_tuple_key:
            return {}
        pos = [self._source.model.index_names.index(n) for n in relationship_tuple_key]
        getter = tuple_itemgetter(itemgetter(*pos), len(pos))
        selected = set()
        for i in indexes:
            if self._source.index_in_column_headers(i) or self._source.index_in_row_headers(i):
                if (
                    i.row() - self._source._num_headers_row in self._source.model._invalid_row
                    or i.column() - self._source._num_headers_column in self._source.model._invalid_column
                ):
                    continue
                key = self._source.get_key(i)
                key = getter(key)
                if all(key):
                    selected.add(key)
        return {relationship_tuple_key: selected}

    def _get_selected_indexes(self):
        """Find selected indexes of parent, map to source if proxy is given"""
        indexes = self._table.selectedIndexes()
        if self._proxy:
            indexes = [self._proxy.mapToSource(i) for i in indexes]
        return indexes

    def delete_invalid_row(self):  # pylint: disable=no-self-use
        # TODO
        return

    def delete_invalid_col(self):  # pylint: disable=no-self-use
        # TODO
        return

    def insert_row(self):  # pylint: disable=no-self-use
        # TODO
        return

    def insert_col(self):  # pylint: disable=no-self-use
        # TODO
        return

    def delete_values(self):
        """deletes selected indexes in pivot_table"""
        indexes = self._get_selected_indexes()
        self._source.delete_values(indexes)

    def restore_values(self):
        """restores edited selected indexes in pivot_table"""
        indexes = self._get_selected_indexes()
        self._source.restore_values(indexes)

    def delete_objects(self):
        """finds selected objects and deletes"""
        indexes = self._get_selected_indexes()
        delete_dict = self._find_selected_objects(indexes)
        if delete_dict:
            self._source.delete_index_values(delete_dict)

    def delete_relationships(self):
        """finds selected relationships and deletes"""
        indexes = self._get_selected_indexes()
        delete_dict = self._find_selected_relationships(indexes)
        if delete_dict:
            self._source.delete_tuple_index_values(delete_dict)

    def open_value_editor(self):
        """Opens the parameter value editor for the first selected cell."""
        model_index = self._get_selected_indexes()[0]
        self.parent().show_parameter_value_editor(model_index, self._table)

    def plot(self):
        """Plots the selected cells in the pivot table."""
        selected_indexes = self._get_selected_indexes()
        hints = PivotTablePlottingHints()
        try:
            plot_window = plot_selection(self._source, selected_indexes, hints)
        except PlottingError as error:
            report_plotting_failure(error, self)
            return
        plotted_column_names = set()
        for index in selected_indexes:
            label = hints.column_label(self._source, index.column())
            plotted_column_names.add(label)
        plot_window.setWindowTitle("Plot    -- {} --".format(", ".join(plotted_column_names)))
        plot_window.show()

    def request_menu(self, QPos=None):
        """Shows the context menu on the screen."""
        indexes = self._get_selected_indexes()

        indexes_in_data = [ind for ind in indexes if self._source.index_in_data(ind)]

        self.open_value_editor_action.setEnabled(len(indexes_in_data) == 1)
        self.plot_action.setEnabled(len(indexes_in_data) > 1)
        self.restore_values_action.setEnabled(bool(indexes_in_data))  # TODO: check there's data to restore
        self.delete_values_action.setEnabled(bool(indexes_in_data))
        selected_objects = self._find_selected_objects(indexes)
        selected_relationships = self._find_selected_relationships(indexes)
        selected_obj_values = [v for values in selected_objects.values() for v in values]
        selected_rel_values = [v for values in selected_relationships.values() for v in values]
        self.delete_object_action.setEnabled(bool(selected_obj_values))
        self.delete_relationship_action.setEnabled(bool(selected_rel_values))
        if len(selected_obj_values) == 1:
            class_name = list(selected_objects.keys())[0]
            entity_name = list(selected_objects[class_name])[0]
            self.delete_object_action.setText("Delete {}: {}".format(class_name, entity_name))
        else:
            self.delete_object_action.setText(self._DELETE_OBJECT)
        if len(selected_rel_values) == 1:
            class_name = list(selected_relationships.keys())[0]
            entity_name = list(selected_relationships[class_name])[0]
            self.delete_relationship_action.setText("Delete relationsip: {}".format(entity_name))
        else:
            self.delete_relationship_action.setText(self._DELETE_RELATIONSHIP)
        pos = self._table.viewport().mapToGlobal(QPos)
        self.move(pos)
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

    @Slot()
    def _plot_column(self):
        """Plots a single column not the selection."""
        try:
            support = PivotTablePlottingHints()
            plot_window = plot_pivot_column(self._model, self._model_index.column(), support)
        except PlottingError as error:
            report_plotting_failure(error, self)
            return
        plot_window.setWindowTitle(
            "Plot    -- {} --".format(support.column_label(self._model, self._model_index.column()))
        )
        plot_window.show()

    @Slot("QPoint")
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

    @Slot()
    def _set_x_flag(self):
        """Sets the X flag for a column."""
        self._model.set_plot_x_column(self._model_index.column(), self._set_as_X_action.isChecked())
