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

"""Contains base classes for project items and item factories."""
from __future__ import annotations
from collections.abc import Callable
import logging
import os
from typing import TYPE_CHECKING, Optional
from PySide6.QtCore import Signal, Slot
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QWidget
from spine_engine.project_item.project_item_resource import ProjectItemResource
from spine_engine.project_item.project_item_specification import ProjectItemSpecification
from spine_engine.utils.helpers import ExecutionDirection, shorten
from ..helpers import create_dir, open_url, rename_dir
from ..log_mixin import LogMixin
from ..logger_interface import LoggerInterface
from ..metaobject import MetaObject
from ..project_commands import SetItemSpecificationCommand
from ..project_item_icon import ProjectItemIcon
from ..project_upgrader import ProjectUpgrader

if TYPE_CHECKING:
    from ..project import SpineToolboxProject
    from ..ui_main import ToolboxUI


class ProjectItem(LogMixin, MetaObject):
    """Class for project items that are not category nor root.
    These items can be executed, refreshed, and so on.

    Attributes:
        x: horizontal position in the screen
        y: vertical position in the screen
    """

    def __init__(self, name: str, description: str, x: float, y: float, project: SpineToolboxProject):
        """
        Args:
            name: item name
            description: item description
            x: horizontal position on the scene
            y: vertical position on the scene
            project: project item's project
        """
        super().__init__(name, description)
        self._project = project
        self.x: float = x
        self.y: float = y
        self._logger = project.toolbox()
        self._properties_ui = None
        self._icon = None
        self._sigs = {}
        self._active = False
        self._actions = []
        # Make project directory for this Item
        self.data_dir: str = str(os.path.join(self._project.items_dir, self.short_name))
        self._specification = None

    def create_data_dir(self) -> None:
        try:
            create_dir(self.data_dir)
        except OSError:
            self._logger.msg_error.emit(f"[OSError] Creating directory {self.data_dir} failed. Check permissions.")

    def data_files(self) -> list[str]:
        """Returns a list of files that are in the data directory."""
        if not os.path.isdir(self.data_dir):
            return []
        with os.scandir(self.data_dir) as scan_iterator:
            return [entry.path for entry in scan_iterator if entry.is_file()]

    @staticmethod
    def item_type() -> str:
        """Item's type identifier string."""
        raise NotImplementedError()

    @property
    def project(self) -> SpineToolboxProject:
        return self._project

    @property
    def logger(self) -> LoggerInterface:
        return self._logger

    def make_signal_handler_dict(self) -> dict[Signal, Callable]:
        """Returns a dictionary of all shared signals and their handlers.
        This is to enable simpler connecting and disconnecting.
        Must be implemented in subclasses.
        """
        return {}

    def activate(self) -> None:
        """Restore selections and connect signals."""
        self._active = True
        self.update_name_label()
        self.restore_selections()  # Do this before connecting signals or funny things happen
        self._connect_signals()

    def deactivate(self) -> bool:
        """Save selections and disconnect signals."""
        self.save_selections()
        if not self._disconnect_signals():
            logging.error("Item %s deactivation failed", self.name)
            return False
        self._active = False
        return True

    def restore_selections(self) -> None:
        """Restore selections into shared widgets when this project item is selected."""

    def save_selections(self) -> None:
        """Save selections in shared widgets for this project item into instance variables."""

    def _connect_signals(self) -> None:
        """Connect signals to handlers."""
        self._sigs = self.make_signal_handler_dict()
        for signal, handler in self._sigs.items():
            signal.connect(handler)

    def _disconnect_signals(self) -> bool:
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

    def set_properties_ui(self, properties_ui: QWidget) -> None:
        """
        Sets the properties tab widget for the item.

        Note that this method expects the widget that is generated from the .ui files
        and initialized with the setupUi() method rather than the entire properties tab widget.

        Args:
            properties_ui: item's properties UI
        """
        self._properties_ui = properties_ui

    def specification(self) -> Optional[ProjectItemSpecification]:
        """Returns the specification for this item."""
        return self._specification

    def undo_specification(self) -> Optional[ProjectItemSpecification]:
        return self._specification

    def set_specification(self, specification: Optional[ProjectItemSpecification]) -> None:
        """Pushes a new SetItemSpecificationCommand to the undo stack."""
        if specification == self._specification:
            return
        self._toolbox.undo_stack.push(
            SetItemSpecificationCommand(self.name, specification, self.undo_specification(), self._project)
        )

    def do_set_specification(self, specification: Optional[ProjectItemSpecification]) -> bool:
        """Sets specification for this item. Removes specification if None given as argument.

        Args:
            specification: specification of this item. None removes the specification.
        """
        if specification and specification.item_type != self.item_type():
            return False
        self._specification = specification
        return True

    def set_icon(self, icon: ProjectItemIcon) -> None:
        """Sets the icon for the item."""
        self._icon = icon
        self._icon.finalize(self.name, self.x, self.y)

    def get_icon(self) -> ProjectItemIcon:
        """Returns the graphics item representing this item in the scene."""
        return self._icon

    def _check_notifications(self) -> None:
        """Checks if exclamation icon notifications need to be set or cleared."""

    def clear_notifications(self) -> None:
        """Clear all notifications from the exclamation icon."""
        self.get_icon().exclamation_icon.clear_notifications()

    def add_notification(self, text: str) -> None:
        """Add a notification to the exclamation icon."""
        self.get_icon().exclamation_icon.add_notification(text)

    def remove_notification(self, text: str) -> None:
        """Remove the first notification that includes given subtext."""
        self.get_icon().exclamation_icon.remove_notification(text)

    def clear_other_notifications(self, text: str) -> None:
        """Remove notifications that don't include the given subtext."""
        self.get_icon().exclamation_icon.clear_other_notifications(text)

    def set_rank(self, rank: int) -> None:
        """Set rank of this item for displaying in the design view."""
        if rank is not None:
            self.get_icon().rank_icon.set_rank(rank + 1)
        else:
            self.get_icon().rank_icon.set_rank("X")

    def handle_execution_successful(self, execution_direction: ExecutionDirection) -> None:
        """Performs item dependent actions after the execution item has finished successfully.

        Args:
            execution_direction: current execution direction
        """

    def resources_for_direct_successors(self) -> list[ProjectItemResource]:
        """
        Returns resources for direct successors.

        These resources can include transient files that don't exist yet, or filename patterns.
        The default implementation returns an empty list.

        Returns:
            a list of ProjectItemResources
        """
        return []

    def resources_for_direct_predecessors(self) -> list[ProjectItemResource]:
        """
        Returns resources for direct predecessors.

        These resources can include transient files that don't exist yet, or filename patterns.
        The default implementation returns an empty list.

        Returns:
            a list of ProjectItemResources
        """
        return []

    def _resources_to_predecessors_changed(self) -> None:
        """Notifies direct predecessors that item's resources have changed."""
        self._project.notify_resource_changes_to_predecessors(self)

    def _resources_to_predecessors_replaced(
        self, old: list[ProjectItemResource], new: list[ProjectItemResource]
    ) -> None:
        """Notifies direct predecessors that item's resources have been replaced.

        Args:
            old: old resources
            new: new resources
        """
        self._project.notify_resource_replacement_to_predecessors(self, old, new)

    def upstream_resources_updated(self, resources: list[ProjectItemResource]) -> None:
        """Notifies item that resources from direct predecessors have changed.

        Args:
            resources: new resources from upstream
        """

    def replace_resources_from_upstream(self, old: list[ProjectItemResource], new: list[ProjectItemResource]) -> None:
        """Replaces existing resources from direct predecessor by a new ones.

        Args:
            old: old resources
            new: new resources
        """

    def _resources_to_successors_changed(self) -> None:
        """Notifies direct successors that item's resources have changed."""
        self._project.notify_resource_changes_to_successors(self)

    def _resources_to_successors_replaced(self, old: list[ProjectItemResource], new: list[ProjectItemResource]) -> None:
        """Notifies direct successors that one of item's resources has been replaced.

        Args:
            old: old resources
            new: new resources
        """
        self._project.notify_resource_replacement_to_successors(self, old, new)

    def downstream_resources_updated(self, resources: list[ProjectItemResource]) -> None:
        """Notifies item that resources from direct successors have changed.

        Args:
            resources: new resources from downstream
        """

    def replace_resources_from_downstream(self, old: list[ProjectItemResource], new: list[ProjectItemResource]) -> None:
        """Replaces existing resources from direct successor by a new ones.

        Args:
            old: old resources
            new: new resources
        """

    def item_dict(self) -> dict:
        """Returns a dictionary corresponding to this item.

        Returns:
            dict: serialized project item
        """
        return {
            "type": self.item_type(),
            "description": self.description,
            "x": self.get_icon().x(),
            "y": self.get_icon().y(),
        }

    @staticmethod
    def item_dict_local_entries() -> list[tuple[str, ...]]:
        """Returns entries or 'paths' in item dict that should be stored in project's local data directory.

        Returns:
            list of tuple of str: local data item dict entries
        """
        return []

    @staticmethod
    def parse_item_dict(item_dict: dict) -> tuple[str, float, float]:
        """
        Reads the information needed to construct the base ProjectItem class from an item dict.

        Args:
            item_dict: an item dict
        Returns:
            tuple: item's name, description as well as x and y coordinates
        """
        description = item_dict["description"]
        x = item_dict["x"]
        y = item_dict["y"]
        return description, x, y

    def copy_local_data(self, item_dict: dict) -> None:
        """
        Copies local data linked to a duplicated project item.

        Args:
            item_dict: serialized item
        """

    @staticmethod
    def from_dict(name: str, item_dict: dict, toolbox: ToolboxUI, project: SpineToolboxProject) -> ProjectItem:
        """
        Deserialized an item from item dict.

        Args:
            name: item's name
            item_dict: serialized item
            toolbox: the main window
            project: a project

        Returns:
            deserialized item
        """
        raise NotImplementedError()

    def actions(self) -> list[QAction]:
        """
        Item specific actions.

        Returns:
            item's actions
        """
        return self._actions

    def rename(self, new_name: str, rename_data_dir_message: str) -> bool:
        """
        Renames this item.

        If the project item needs any additional steps in renaming, override this
        method in subclass. See e.g. rename() method in DataStore class.

        Args:
            new_name: New name
            rename_data_dir_message: Message to show when renaming item's data directory

        Returns:
            True if item was renamed successfully, False otherwise
        """
        if shorten(new_name) != self.short_name:
            new_data_dir = str(os.path.join(self._project.items_dir, shorten(new_name)))
            if not rename_dir(self.data_dir, new_data_dir, self._toolbox, rename_data_dir_message):
                return False
            self.data_dir = new_data_dir
        self.set_name(new_name)
        self.get_icon().update_name_item(new_name)
        if self._active:
            self.update_name_label()
            self._project.toolbox().override_console_and_execution_list()
        return True

    @Slot(bool)
    def open_directory(self, checked=False):
        """Open this item's data directory in file explorer."""
        url = "file:///" + self.data_dir
        # noinspection PyTypeChecker, PyCallByClass, PyArgumentList
        res = open_url(url)
        if not res:
            self._logger.msg_error.emit(f"Failed to open directory: {self.data_dir}")

    def tear_down(self) -> None:
        """Tears down this item. Called both before closing the app and when removing the item from the project.
        Implement in subclasses to e.g. close all QMainWindows opened by this item.
        """
        for action in self._actions:
            action.deleteLater()
        self.deleteLater()

    def set_up(self) -> None:
        """Sets up this item. Called when adding the item to the project.
        Implement in subclasses to e.g. recreate attributes destroyed by tear_down.
        """
        self.set_rank(0)
        self._check_notifications()
        self.create_data_dir()
        self.do_set_specification(self._specification)

    def update_name_label(self) -> None:
        """
        Updates the name label on the properties widget, used when selecting an item and renaming the selected one.
        """
        self._project.toolbox().label_item_name.setText(f"<b>{self.name}</b>")

    def notify_destination(self, source_item: ProjectItem) -> None:
        """
        Informs an item that it has become the destination of a connection between two items.

        The default implementation logs a warning message. Subclasses should reimplement this if they need
        more specific behavior.

        Args:
            source_item: connection source item
        """
        self._logger.msg_warning.emit(
            "Link established. Interaction between a "
            f"<b>{source_item.item_type()}</b> and a <b>{self.item_type()}</b> has not been "
            "implemented yet."
        )

    @staticmethod
    def upgrade_v1_to_v2(item_name: str, item_dict: dict) -> dict:
        """
        Upgrades item's dictionary from v1 to v2.

        Subclasses should reimplement this method if there are changes between version 1 and version 2.

        Args:
            item_name: item's name
            item_dict: Version 1 item dictionary

        Returns:
            Version 2 item dictionary
        """
        return item_dict

    @staticmethod
    def upgrade_v2_to_v3(item_name: str, item_dict: dict, project_upgrader: ProjectUpgrader) -> dict:
        """
        Upgrades item's dictionary from v2 to v3.

        Subclasses should reimplement this method if there are changes between version 2 and version 3.

        Args:
            item_name: item's name
            item_dict: Version 2 item dictionary
            project_upgrader: Project upgrader class instance

        Returns:
            Version 3 item dictionary
        """
        return item_dict
