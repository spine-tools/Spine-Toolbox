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
Contains base classes for project items and item factories.

:authors: P. Savolainen (VTT)
:date:   4.10.2018
"""

import os
import logging
from PySide2.QtCore import Signal, Slot
from PySide2.QtWidgets import QWidget
from spinetoolbox.helpers import create_dir, rename_dir, open_url
from spinetoolbox.metaobject import MetaObject
from spinetoolbox.project_commands import SetItemSpecificationCommand
from spinetoolbox.widgets.custom_qtextbrowser import SignedTextDocument
from spinetoolbox.helpers import format_log_message, format_process_message, add_message_to_document
from spine_engine.utils.helpers import shorten


class ProjectItem(MetaObject):
    """Class for project items that are not category nor root.
    These items can be executed, refreshed, and so on.

    Attributes:
        x (float): horizontal position in the screen
        y (float): vertical position in the screen
    """

    item_executed = Signal(object, object)
    """Emitted when the item has been successfully executed."""
    item_changed = Signal()
    """Request DAG update. Emitted when a change affects other items in the DAG."""

    def __init__(self, name, description, x, y, project, logger):
        """
        Args:
            name (str): item name
            description (str): item description
            x (float): horizontal position on the scene
            y (float): vertical position on the scene
            project (SpineToolboxProject): project item's project
            logger (LoggerInterface): a logger instance
        """
        super().__init__(name, description)
        self._project = project
        self.x = x
        self.y = y
        self._logger = logger
        self._properties_ui = None
        self._icon = None
        self._sigs = None
        self._active = False
        self._actions = list()
        self.item_changed.connect(lambda: self._project.notify_changes_in_containing_dag(self.name))
        self.item_executed.connect(self.handle_execution_successful)
        # Make project directory for this Item
        self.data_dir = os.path.join(self._project.items_dir, self.short_name)
        self._specification = None
        self.undo_specification = None
        self._event_document = SignedTextDocument(name)
        self._process_document = SignedTextDocument(name)
        self._filter_event_documents = {}
        self._filter_process_documents = {}
        self.julia_console = QWidget()
        self.python_console = QWidget()

    def create_data_dir(self):
        try:
            create_dir(self.data_dir)
        except OSError:
            self._logger.msg_error.emit(f"[OSError] Creating directory {self.data_dir} failed. Check permissions.")

    @staticmethod
    def item_type():
        """Item's type identifier string."""
        raise NotImplementedError()

    @staticmethod
    def item_category():
        """Item's category."""
        raise NotImplementedError()

    @property
    def event_document(self):
        return self._event_document

    @property
    def process_document(self):
        return self._process_document

    @property
    def filter_event_documents(self):
        return self._filter_event_documents

    @property
    def filter_process_documents(self):
        return self._filter_process_documents

    # pylint: disable=no-self-use
    def make_signal_handler_dict(self):
        """Returns a dictionary of all shared signals and their handlers.
        This is to enable simpler connecting and disconnecting.
        Must be implemented in subclasses.
        """
        return dict()

    def activate(self):
        """Restore selections and connect signals."""
        self._active = True
        self.restore_selections()  # Do this before connecting signals or funny things happen
        self._connect_signals()

    def deactivate(self):
        """Save selections and disconnect signals."""
        self.save_selections()
        if not self._disconnect_signals():
            logging.error("Item %s deactivation failed", self.name)
            return False
        self._active = False
        return True

    def restore_selections(self):
        """Restore selections into shared widgets when this project item is selected."""

    def save_selections(self):
        """Save selections in shared widgets for this project item into instance variables."""

    def _connect_signals(self):
        """Connect signals to handlers."""
        for signal, handler in self._sigs.items():
            signal.connect(handler)

    def _disconnect_signals(self):
        """Disconnect signals from handlers and check for errors."""
        for signal, handler in self._sigs.items():
            try:
                ret = signal.disconnect(handler)
            except RuntimeError:
                self._logger.msg_error.emit(f"RuntimeError in disconnecting <b>{self.name}</b> signals")
                logging.error("RuntimeError in disconnecting signal %s from handler %s", signal, handler)
                return False
            if not ret:
                self._logger.msg_error.emit(f"Disconnecting signal in <b>{self.name}</b> failed")
                logging.error("Disconnecting signal %s from handler %s failed", signal, handler)
                return False
        return True

    def set_properties_ui(self, properties_ui):
        """
        Sets the properties tab widget for the item.

        Note that this method expects the widget that is generated from the .ui files
        and initialized with the setupUi() method rather than the entire properties tab widget.

        Args:
            properties_ui (QWidget): item's properties UI
        """
        self._properties_ui = properties_ui
        if self._sigs is None:
            self._sigs = self.make_signal_handler_dict()

    def specification(self):
        """Returns the specification for this item."""
        return self._specification

    def set_specification(self, specification):
        """Pushes a new SetToolSpecificationCommand to the toolbox' undo stack.
        """
        if specification == self._specification:
            return
        self._toolbox.undo_stack.push(SetItemSpecificationCommand(self, specification))

    def do_set_specification(self, specification):
        """Sets specification for this item. Removes specification if None given as argument.

        Args:
            specification (ProjectItemSpecification): specification of this item. None removes the specification.
        """
        if specification and specification.item_type != self.item_type():
            return False
        self.undo_specification = self._specification
        self._specification = specification
        return True

    def undo_set_specification(self):
        self.do_set_specification(self.undo_specification)

    def set_icon(self, icon):
        """
        Sets the icon for the item.

        Args:
            icon (ProjectItemIcon): item's icon
        """
        self._icon = icon
        self._icon.update(self.name, self.x, self.y)

    def get_icon(self):
        """Returns the graphics item representing this item in the scene."""
        return self._icon

    def clear_notifications(self):
        """Clear all notifications from the exclamation icon."""
        self.get_icon().exclamation_icon.clear_notifications()

    def add_notification(self, text):
        """Add a notification to the exclamation icon."""
        self.get_icon().exclamation_icon.add_notification(text)

    def set_rank(self, rank):
        """Set rank of this item for displaying in the design view."""
        if rank is not None:
            self.get_icon().rank_icon.set_rank(rank + 1)
        else:
            self.get_icon().rank_icon.set_rank("X")

    @property
    def executable_class(self):
        raise NotImplementedError()

    def execution_item(self):
        """Creates project item's execution counterpart."""
        if self._specification is None:
            specifications = {}
        else:
            specifications = {self.item_type(): {self._specification.name: self._specification}}
        return self.executable_class.from_dict(
            self.item_dict(), self.name, self._project.project_dir, self._project.settings, specifications, self._logger
        )

    @Slot(object, object)
    def handle_execution_successful(self, execution_direction, engine_state):
        """Performs item dependent actions after the execution item has finished successfully."""

    # pylint: disable=no-self-use
    def resources_for_direct_successors(self):
        """
        Returns resources for direct successors.

        These resources can include transient files that don't exist yet, or filename patterns.
        The default implementation returns an empty list.

        Returns:
            list: a list of ProjectItemResources
        """
        return list()

    def resources_for_direct_predecessors(self):
        """
        Returns resources for direct predecessors.

        These resources can include transient files that don't exist yet, or filename patterns.
        The default implementation returns an empty list.

        Returns:
            list: a list of ProjectItemResources
        """
        return list()

    def handle_dag_changed(self, rank, upstream_resources, downstream_resources):
        """
        Handles changes in the DAG.

        Subclasses should reimplement the _do_handle_dag_changed() method.

        Args:
            rank (int): item's execution order
            upstream_resources (list): resources available from upstream
            downstream_resources (list, optional): resources available from downstream
        """
        self.clear_notifications()
        self.set_rank(rank)
        self._do_handle_dag_changed(upstream_resources, downstream_resources)
        for link in self._icon.incoming_links():
            link._do_handle_dag_changed(upstream_resources)

    def _do_handle_dag_changed(self, upstream_resources, downstream_resources):
        """
        Handles changes in the DAG.

        Usually this entails validating the input resources and populating file references etc.
        The default implementation does nothing.

        Args:
            upstream_resources (list): resources available from upstream
            downstream_resources (list, optional): resources available from downstream
        """

    def invalidate_workflow(self, edges):
        """Notifies that this item's workflow is not acyclic.

        Args:
            edges (list): A list of edges that make the graph acyclic after removing them.
        """
        edges = ["{0} -> {1}".format(*edge) for edge in edges]
        self.clear_notifications()
        self.set_rank(None)
        self.add_notification(
            "The workflow defined for this item has loops and thus cannot be executed. "
            "Possible fix: remove link(s) {0}.".format(", ".join(edges))
        )

    def item_dict(self):
        """Returns a dictionary corresponding to this item."""
        return {
            "type": self.item_type(),
            "description": self.description,
            "x": self.get_icon().sceneBoundingRect().center().x(),
            "y": self.get_icon().sceneBoundingRect().center().y(),
        }

    @staticmethod
    def parse_item_dict(item_dict):
        """
        Reads the information needed to construct the base ProjectItem class from an item dict.

        Args:
            item_dict (dict): an item dict
        Returns:
            tuple: item's name, description as well as x and y coordinates
        """
        description = item_dict["description"]
        x = item_dict["x"]
        y = item_dict["y"]
        return description, x, y

    @staticmethod
    def from_dict(name, item_dict, toolbox, project, logger):
        """
        Deserialized an item from item dict.

        Args:
            name (str): item's name
            item_dict (dict): serialized item
            toolbox (ToolboxUI): the main window
            project (SpineToolboxProject): a project
            logger (LoggerInterface): a logger
        Returns:
            ProjectItem: deserialized item
        """
        raise NotImplementedError()

    def actions(self):
        """
        Item specific actions.

        Returns:
            list of QAction: item's actions
        """
        return self._actions

    def rename(self, new_name):
        """
        Renames this item.

        If the project item needs any additional steps in renaming, override this
        method in subclass. See e.g. rename() method in DataStore class.

        Args:
            new_name(str): New name

        Returns:
            bool: True if renaming succeeded, False otherwise
        """
        old_name = self.name
        new_short_name = shorten(new_name)
        # Rename project item data directory
        new_data_dir = os.path.join(self._project.items_dir, new_short_name)
        if not rename_dir(self.data_dir, new_data_dir, self._logger):
            return False
        # Rename project item
        self.set_name(new_name)
        # Update project item directory variable
        self.data_dir = new_data_dir
        # Update name label in tab
        if self._active:
            self.update_name_label()
        # Update name item of the QGraphicsItem
        self.get_icon().update_name_item(new_name)
        self._project.dag_handler.rename_node(old_name, new_name)
        return True

    def open_directory(self):
        """Open this item's data directory in file explorer."""
        url = "file:///" + self.data_dir
        # noinspection PyTypeChecker, PyCallByClass, PyArgumentList
        res = open_url(url)
        if not res:
            self._logger.msg_error.emit(f"Failed to open directory: {self.data_dir}")

    def tear_down(self):
        """Tears down this item. Called both before closing the app and when removing the item from the project.
        Implement in subclasses to eg close all QMainWindows opened by this item.
        """
        for action in self._actions:
            action.deleteLater()

    def set_up(self):
        """Sets up this item. Called when adding the item to the project.
        Implement in subclasses to eg recreate attributes destroyed by tear_down.
        """

    def update_name_label(self):
        """
        Updates the name label on the properties widget when renaming an item.

        Must be reimplemented by subclasses.
        """
        raise NotImplementedError()

    def notify_destination(self, source_item):
        """
        Informs an item that it has become the destination of a connection between two items.

        The default implementation logs a warning message. Subclasses should reimplement this if they need
        more specific behavior.

        Args:
            source_item (ProjectItem): connection source item
        """
        self._logger.msg_warning.emit(
            "Link established. Interaction between a "
            f"<b>{source_item.item_type()}</b> and a <b>{self.item_type()}</b> has not been "
            "implemented yet."
        )

    def add_log_message(self, filter_id, msg_type, msg_text):
        if filter_id:
            if filter_id not in self._filter_event_documents:
                self._filter_event_documents[filter_id] = SignedTextDocument(self.name)
                if self._active:
                    self._project._toolbox.ui.treeView_eventlog.model().layoutChanged.emit()
            document = self._filter_event_documents[filter_id]
        else:
            document = self._log_document
        message = format_log_message(msg_type, msg_text)
        add_message_to_document(document, message)

    def add_process_message(self, filter_id, msg_type, msg_text):
        if filter_id:
            if filter_id not in self._filter_process_documents:
                self._filter_process_documents[filter_id] = SignedTextDocument(self.name)
                if self._active:
                    self._project._toolbox.ui.treeView_processlog.model().layoutChanged.emit()
            document = self._filter_process_documents[filter_id]
        else:
            document = self._process_document
        message = format_process_message(msg_type, msg_text)
        add_message_to_document(document, message)

    @staticmethod
    def upgrade_from_no_version_to_version_1(item_name, old_item_dict, old_project_dir):
        """
        Upgrades item's dictionary from no version to version 1.

        Subclasses should reimplement this method if their JSON format changed between no version
        and version 1 .proj files.

        Args:
            item_name (str): item's name
            old_item_dict (dict): no version item dictionary
            old_project_dir (str): path to the previous project dir. We use old project directory
                here since the new project directory may be empty at this point and the directories
                for the new project items have not been created yet.

        Returns:
            version 1 item dictionary
        """
        return old_item_dict

    @staticmethod
    def upgrade_v1_to_v2(item_name, item_dict):
        """
        Upgrades item's dictionary from v1 to v2.

        Subclasses should reimplement this method if there are changes between version 1 and version 2.

        Args:
            item_name (str): item's name
            item_dict (dict): Version 1 item dictionary
            project_upgrader (ProjectUpgrader)

        Returns:
            dict: Version 2 item dictionary
        """
        return item_dict

    @staticmethod
    def upgrade_v2_to_v3(item_name, item_dict, project_upgrader):
        """
        Upgrades item's dictionary from v2 to v3.

        Subclasses should reimplement this method if there are changes between version 2 and version 3.

        Args:
            item_name (str): item's name
            item_dict (dict): Version 1 item dictionary

        Returns:
            dict: Version 2 item dictionary
        """
        return item_dict
