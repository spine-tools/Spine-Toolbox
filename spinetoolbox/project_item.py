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
ProjectItem and ProjectItemResource classes.

:authors: P. Savolainen (VTT)
:date:   4.10.2018
"""

import os
import logging
from urllib.parse import urlparse
from urllib.request import url2pathname
from PySide2.QtCore import Signal, QUrl
from PySide2.QtGui import QDesktopServices
from .helpers import create_dir, rename_dir
from .metaobject import MetaObject, shorten
from spinetoolbox.project_commands import SetItemSpecificationCommand


class ProjectItem(MetaObject):
    """Class for project items that are not category nor root.
    These items can be executed, refreshed, and so on.

    Attributes:
        x (float): horizontal position in the screen
        y (float): vertical position in the screen
    """

    item_changed = Signal()

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
        self._item_factory = None
        self._project = project
        self.x = x
        self.y = y
        self._logger = logger
        self._properties_ui = None
        self._icon = None
        self._sigs = None
        self._active = False
        self.item_changed.connect(lambda: self._project.notify_changes_in_containing_dag(self.name))
        # Make project directory for this Item
        self.data_dir = os.path.join(self._project.items_dir, self.short_name)
        self._specification = None
        self.undo_specification = None

    def create_data_dir(self):
        try:
            create_dir(self.data_dir)
        except OSError:
            self._logger.msg_error.emit(f"[OSError] Creating directory {self.data_dir} failed. Check permissions.")

    @staticmethod
    def item_type():
        """Item's type identifier string."""
        raise NotImplementedError()

    def item_factory(self):
        """Item's factory identifier string."""
        return self._item_factory

    def set_item_factory(self, item_factory):
        self._item_factory = item_factory

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
        """Sets Tool specification for this Tool. Removes Tool specification if None given as argument.

        Args:
            specification (ToolSpecification): Tool specification of this Tool. None removes the specification.
        """
        self.undo_specification = self._specification
        self._specification = specification

    def undo_set_specification(self):
        self.do_set_specification(self.undo_specification)

    def set_icon(self, icon):
        """
        Sets the icon for the item.

        Args:
            icon (ProjectItemIcon): item's icon
        """
        self._icon = icon

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

    def execution_item(self):
        """Creates project item's execution counterpart."""
        raise NotImplementedError()

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

    def handle_dag_changed(self, rank, resources):
        """
        Handles changes in the DAG.

        Subclasses should reimplement the _do_handle_dag_changed() method.

        Args:
            rank (int): item's execution order
            resources (list): resources available from input items
        """
        self.clear_notifications()
        self.set_rank(rank)
        self._do_handle_dag_changed(resources)

    def _do_handle_dag_changed(self, resources):
        """
        Handles changes in the DAG.

        Usually this entails validating the input resources and populating file references etc.
        The default implementation does nothing.

        Args:
            resources (list): resources available from input items
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
            "short name": self.short_name,
            "description": self.description,
            "x": self.get_icon().sceneBoundingRect().center().x(),
            "y": self.get_icon().sceneBoundingRect().center().y(),
        }

    @staticmethod
    def default_name_prefix():
        """prefix for default item name"""
        raise NotImplementedError()

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
        new_short_name = shorten(new_name)
        # Rename project item data directory
        new_data_dir = os.path.join(self._project.items_dir, new_short_name)  # Make path for new data dir
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
        # Rename node and edges in the graph (dag) that contains this project item
        return True

    def open_directory(self):
        """Open this item's data directory in file explorer."""
        url = "file:///" + self.data_dir
        # noinspection PyTypeChecker, PyCallByClass, PyArgumentList
        res = QDesktopServices.openUrl(QUrl(url, QUrl.TolerantMode))
        if not res:
            self._logger.msg_error.emit(f"Failed to open directory: {self.data_dir}")

    def tear_down(self):
        """Tears down this item. Called both before closing the app and when removing the item from the project.
        Implement in subclasses to eg close all QMainWindows opened by this item.
        """

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

    @staticmethod
    def upgrade_from_no_version_to_version_1(item_name, old_item_dict, old_project_dir):
        """
        Upgrades item's dictionary from no version to version 1.

        Subclasses should reimplement this method if their JSON format changed between no version
        and version 1 .proj files.

        Args:
            item_name (str): item's name
            old_item_dict (str): no version item dictionary
            old_project_dir (str): path to the previous project dir. We use old project directory
                here since the new project directory may be empty at this point and the directories
                for the new project items have not been created yet.

        Returns:
            version 1 item dictionary
        """
        return old_item_dict


class ProjectItemFactory(MetaObject):
    """Class for project item factories."""

    def __init__(self, toolbox, name, description):
        """
        Args:
            toolbox (ToolboxUI)
            name (str): Category name
            description (str): Category description
        """
        super().__init__(name, description)
        self.properties_ui = self.properties_widget_maker(toolbox).ui

    @staticmethod
    def icon():
        """
        Returns the icon resource path.

        Returns:
            str
        """
        raise NotImplementedError()

    @staticmethod
    def item_category():
        """
        Returns the item category string, e.g., "Tools".

        Returns:
            str
        """
        raise NotImplementedError()

    @staticmethod
    def item_type():
        """
        Returns the category item type string, e.g., "Gimlet".

        Returns:
            str
        """
        raise NotImplementedError()

    @property
    def properties_widget_maker(self):
        """
        Returns a QWidget subclass to create the properties ui.

        Returns:
            class
        """
        raise NotImplementedError()

    @property
    def item_maker(self):
        """
        Returns a ProjectItem subclass.

        Returns:
            class
        """
        raise NotImplementedError()

    @property
    def icon_maker(self):
        """
        Returns a ProjectItemIcon subclass.

        Returns:
            class
        """
        raise NotImplementedError()

    @property
    def add_form_maker(self):
        """
        Returns an AddProjectItem subclass.

        Returns:
            class
        """
        raise NotImplementedError()

    @staticmethod
    def supports_specifications():
        """
        Returns whether or not this factory supports specs.
        If the subclass implementation returns True, then it must also implement
        ``specification_form_maker``, ``specification_menu_maker``, and  ``specification_loader``.

        Returns:
            bool
        """
        return False

    @property
    def specification_form_maker(self):
        """
        Returns a QWidget subclass to create and edit specifications.

        Returns:
            class
        """
        raise NotImplementedError()

    def specification_menu_maker(self):
        """
        Returns an ItemSpecificationMenu subclass.

        Returns:
            class
        """
        raise NotImplementedError()

    @property
    def specification_loader(self):
        """
        Returns a function to load specifications.

        Returns:
            class
        """
        raise NotImplementedError()

    def make_icon(self, toolbox, x, y, w, h, project_item):
        """
        Returns a ProjectItemIcon to use with given toolbox, for given project item.

        Args:
            toolbox (ToolboxUI)
            x, y, w, h (int): Icon coordinates and dimensions
            project_item (ProjectItem)

        Returns:
            ProjectItemIcon
        """
        return self.icon_maker(toolbox, x, y, w, h, project_item, self.icon())

    def make_item(self, *args, **kwargs):
        """
        Returns a project item while setting its factory attribute.

        Returns:
            ProjectItem
        """
        item = self.item_maker(*args, **kwargs)
        item.set_item_factory(self.name)
        return item

    def activate_project_item(self, toolbox, project_item):
        """
        Activates the given project item so it works with the given toolbox.
        This is mainly intended to facilitate adding items back with redo.

        Args:
            toolbox (ToolboxUI)
            project_item (ProjectItem)
        """
        icon = project_item.get_icon()
        if icon is not None:
            icon.activate()
        else:
            icon = self.make_icon(toolbox, project_item.x - 35, project_item.y - 35, 70, 70, project_item)
            project_item.set_icon(icon)
        project_item.set_properties_ui(self.properties_ui)
        project_item.create_data_dir()
        project_item.set_up()


class ProjectItemSpecification(MetaObject):
    """Class to hold a project item specification."""

    def __init__(self, name, description=None, factory_name=""):
        """
        Args:
            name (str): specification name
            description (str): description
            factory_name (str): Project item factory name, e.g., "Tools"
        """
        super().__init__(name, description)
        self.factory_name = factory_name
        self.def_file_path = ""  # specification's JSON file path

    def set_def_path(self, path):
        """Sets the file path for this tool specification.

        Args:
            path (str): Absolute path to the specification file.
        """
        self.def_file_path = path

    def get_def_path(self):
        """Returns tool specification file path."""
        return self.def_file_path


class ProjectItemResource:
    """Class to hold a resource made available by a project item
    and that may be consumed by another project item."""

    def __init__(self, provider, type_, url="", metadata=None):
        """
        Args:
            provider (ProjectItem or ExecutionItem): The item that provides the resource
            type_ (str): The resource type, currently available types:

                - "file": url points to the file's path
                - "database": url is the databases url
                - "transient_file": a file that may not yet be available or may change its location;
                  url points to latest version or is empty, metadata contains the "label" key
                  and an optional "pattern" key
                - "file_pattern": a file patter with wildcards that acts as a placeholder;
                  url is empty, metadata contains the "label" key
            url (str): The url of the resource
            metadata (dict): Some metadata providing extra information about the resource.
                Currently available keys:

                - label (str): a textual label
                - pattern (str): a file pattern if the file is part of that pattern
        """
        self.provider = provider
        self.type_ = type_
        self.url = url
        self.parsed_url = urlparse(url)
        self.metadata = metadata if metadata is not None else dict()

    def __eq__(self, other):
        if not isinstance(other, ProjectItemResource):
            # don't attempt to compare against unrelated types
            return NotImplemented
        return (
            self.provider == other.provider
            and self.type_ == other.type_
            and self.url == other.url
            and self.metadata == other.metadata
        )

    def __repr__(self):
        result = "ProjectItemResource("
        result += f"provider={self.provider}, "
        result += f"type_={self.type_}, "
        result += f"url={self.url}, "
        result += f"metadata={self.metadata})"
        return result

    @property
    def path(self):
        """Returns the resource path in the local syntax, as obtained from parsing the url."""
        return url2pathname(self.parsed_url.path)

    @property
    def scheme(self):
        """Returns the resource scheme, as obtained from parsing the url."""
        return self.parsed_url.scheme
