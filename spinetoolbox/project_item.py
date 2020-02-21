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
from PySide2.QtCore import Signal, QUrl, QParallelAnimationGroup, QEventLoop
from PySide2.QtGui import QDesktopServices
from .helpers import create_dir, rename_dir
from .metaobject import MetaObject, shorten


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
    def category():
        """Item's category identifier string."""
        raise NotImplementedError()

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
        self._properties_ui = properties_ui
        if self._sigs is None:
            self._sigs = self.make_signal_handler_dict()

    def set_icon(self, icon):
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

    def stop_execution(self):
        """Stops executing this View."""
        self._logger.msg.emit(f"Stopping {self.name}")

    def execute(self, resources, direction):
        """
        Executes this item in the given direction using the given resources and returns a boolean
        indicating the outcome.

        Subclasses need to implement execute_forward and execute_backward to do the appropriate work
        in each direction.

        Args:
            resources (list): a list of ProjectItemResources available for execution
            direction (str): either "forward" or "backward"

        Returns:
            bool: True if execution succeeded, False otherwise
        """
        if direction == "forward":
            self._logger.msg.emit("")
            self._logger.msg.emit(f"Executing {self.item_type()} <b>{self.name}</b>")
            self._logger.msg.emit("***")
            if self.execute_forward(resources):
                self.run_leave_animation()
                return True
            return False
        return self.execute_backward(resources)

    def run_leave_animation(self):
        """
        Runs the animation that represents execution leaving this item.
        Blocks until the animation is finished.
        """
        loop = QEventLoop()
        animation = self.make_execution_leave_animation()
        animation.finished.connect(loop.quit)
        animation.start()
        if animation.state() == QParallelAnimationGroup.Running:
            loop.exec_()

    def execute_forward(self, resources):
        """
        Executes this item in the forward direction.

        The default implementation just returns True.

        Args:
            resources (list): a list of ProjectItemResources available for execution

        Returns:
            bool: True if execution succeeded, False otherwise
        """
        return True

    def execute_backward(self, resources):
        """
        Executes this item in the backward direction.

        The default implementation just returns True.

        Args:
            resources (list): a list of ProjectItemResources available for execution

        Returns:
            bool: True if execution succeeded, False otherwise
        """
        return True

    def output_resources(self, direction):
        """
        Returns output resources for execution in the given direction.

        Subclasses need to implement output_resources_backward and/or output_resources_forward
        if they want to provide resources in any direction.

        Args:
            direction (str): Direction where output resources are passed

        Returns:
            a list of ProjectItemResources
        """
        return {"backward": self.output_resources_backward, "forward": self.output_resources_forward}[direction]()

    # pylint: disable=no-self-use
    def output_resources_forward(self):
        """
        Returns output resources for forward execution.

        The default implementation returns an empty list.

        Returns:
            a list of ProjectItemResources
        """
        return list()

    # pylint: disable=no-self-use
    def output_resources_backward(self):
        """
        Returns output resources for backward execution.

        The default implementation returns an empty list.

        Returns:
            a list of ProjectItemResources
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

    def make_execution_leave_animation(self):
        """
        Returns animation to play when execution leaves this item.

        Returns:
            QParallelAnimationGroup
        """
        icon = self.get_icon()
        links = set(link for conn in icon.connectors.values() for link in conn.links if link.src_connector == conn)
        anim_group = QParallelAnimationGroup(self)
        for link in links:
            anim_group.addAnimation(link.make_execution_animation())
        return anim_group

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

    # pylint: disable=no-self-use
    def available_resources_downstream(self, upstream_resources):
        """
        Returns resources available to downstream items.

        Should be reimplemented by subclasses if they want to offer resources
        to downstream items. The default implementation returns an empty list.

        Args:
            upstream_resources (list): a list of resources available from upstream items

        Returns:
            a list of ProjectItemResources
        """
        return list()

    # pylint: disable=no-self-use
    def available_resources_upstream(self):
        """
        Returns resources available to upstream items.

        Should be reimplemented by subclasses if they want to offer resources
        to upstream items. The default implementation returns an empty list.

        Returns:
            a list of ProjectItemResources
        """
        return list()

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


class ProjectItemResource:
    """Class to hold a resource made available by a project item
    and that may be consumed by another project item."""

    def __init__(self, provider, type_, url="", metadata=None):
        """Init class.

        Args:
            provider (ProjectItem): The item that provides the resource
            type_ (str): The resource type, either "file" or "database" (for now)
            url (str): The url of the resource
            metadata (dict): Some metadata providing extra information about the resource. For now it has one key:
                - future (bool): whether the resource is from the future, e.g. Tool output files advertised beforehand
        """
        self.provider = provider
        self.type_ = type_
        self.url = url
        self.parsed_url = urlparse(url)
        if not metadata:
            metadata = dict()
        self.metadata = metadata

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
