######################################################################################################################
# Copyright (C) 2017-2021 Spine project consortium
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################
"""Contains logging connection and jump classes."""
from spinedb_api.filters.scenario_filter import SCENARIO_FILTER_TYPE
from spinedb_api.filters.tool_filter import TOOL_FILTER_TYPE
from spinedb_api import DatabaseMapping, SpineDBAPIError, SpineDBVersionError
from spine_engine.project_item.connection import ResourceConvertingConnection, Jump
from ..log_mixin import LogMixin
from ..mvcmodels.resource_filter_model import ResourceFilterModel
from ..helpers import busy_effect


class HeadlessConnection(ResourceConvertingConnection):
    """A project item connection that is compatible with headless mode."""

    def __init__(
        self,
        source_name,
        source_position,
        destination_name,
        destination_position,
        options=None,
        disabled_filter_names=None,
        legacy_resource_filter_ids=None,
    ):
        super().__init__(
            source_name, source_position, destination_name, destination_position, options, disabled_filter_names
        )
        self._legacy_resource_filter_ids = legacy_resource_filter_ids

    @property
    def database_resources(self):
        """Connection's database resources"""
        return self._resources

    def set_filter_enabled(self, resource_label, filter_type, filter_name, enabled):
        """Enables or disables a filter.

        Args:
            resource_label (str): database resource name
            filter_type (str): filter type
            filter_name (str): filter name
            enabled (bool): True to enable the filter, False to disable it
        """
        disabled_names = self._disabled_filter_names.setdefault(resource_label, {}).setdefault(filter_type, set())
        if enabled:
            disabled_names.discard(filter_name)
        else:
            disabled_names.add(filter_name)

    def _convert_legacy_resource_filter_ids_to_disabled_filter_names(self):
        """Converts legacy resource filter ids to disabled filter names.

        This method should be called once after constructing the connection from potentially legacy dict
        using ``from_dict()``.
        """
        for resource in self._resources:
            resource_filter_ids = self._legacy_resource_filter_ids.get(resource.label)
            if resource_filter_ids is None:
                continue
            url = resource.url
            if not url:
                continue
            try:
                db_map = DatabaseMapping(url)
            except (SpineDBAPIError, SpineDBVersionError):
                continue
            try:
                scenario_filter_ids = resource_filter_ids.get(SCENARIO_FILTER_TYPE)
                disabled_scenarios = set()
                if scenario_filter_ids is not None:
                    for row in db_map.query(db_map.scenario_sq):
                        if row.id not in scenario_filter_ids:
                            disabled_scenarios.add(row.name)
                self._disabled_filter_names.setdefault(resource.label, {})[SCENARIO_FILTER_TYPE] = sorted(
                    list(disabled_scenarios)
                )
                tool_filter_ids = resource_filter_ids.get(TOOL_FILTER_TYPE)
                disabled_tools = set()
                if tool_filter_ids is not None:
                    for row in db_map.query(db_map.tool_sq):
                        if row.id not in tool_filter_ids:
                            disabled_tools.add(row.name)
                self._disabled_filter_names.setdefault(resource.label, {})[TOOL_FILTER_TYPE] = sorted(
                    list(disabled_tools)
                )
            finally:
                db_map.connection.close()
        self._legacy_resource_filter_ids = None

    @staticmethod
    def _constructor_args_from_dict(connection_dict):
        """See base class."""
        kw_args = ResourceConvertingConnection._constructor_args_from_dict(connection_dict)
        resource_filters = connection_dict.get("resource_filters")
        if resource_filters is not None:
            # Legacy, for backwards compatibility. Resource filters have been superseded by disabled_filters.
            kw_args["legacy_resource_filter_ids"] = resource_filters
        return kw_args

    @classmethod
    def from_dict(cls, connection_dict, **kwargs):
        """Deserializes a connection from dict.

        Args:
            connection_dict (dict): serialized LoggingConnection
            **kwargs: additional keyword arguments to be forwarded to class constructor
        """
        kw_args_from_dict = cls._constructor_args_from_dict(connection_dict)
        return cls(**kw_args_from_dict, **kwargs)

    def receive_resources_from_source(self, resources):
        """See base class."""
        super().receive_resources_from_source(resources)
        if self._legacy_resource_filter_ids is not None:
            self._convert_legacy_resource_filter_ids_to_disabled_filter_names()

    def replace_resources_from_source(self, old, new):
        """Replaces existing resources by new ones.

        Args:
            old (list of ProjectItemResource): old resources
            new (list of ProjectItemResource): new resources
        """
        for old_resource, new_resource in zip(old, new):
            self._resources.discard(old_resource)
            old_filters = self._disabled_filter_names.pop(old_resource.label, None)
            if new_resource.type_ == "database":
                self._resources.add(new_resource)
                if old_filters is not None:
                    self._disabled_filter_names[new_resource.label] = old_filters


class LoggingConnection(LogMixin, HeadlessConnection):
    def __init__(self, *args, toolbox, **kwargs):
        super().__init__(*args, **kwargs)
        self._toolbox = toolbox
        self.resource_filter_model = ResourceFilterModel(self, toolbox.undo_stack, toolbox)
        self.link = None

    @property
    def graphics_item(self):
        return self.link

    @staticmethod
    def item_type(self):
        return "connection"

    def may_have_filters(self):
        """Returns True if connection may have filters.

        Returns:
            bool: True if it is possible for the connection to have filters, False otherwise
        """
        return bool(self._resources)

    def disabled_filter_names(self, resource_label, filter_type):
        """Returns disabled filter names for given resource and filter type.

        Args:
            resource_label (str): resource label
            filter_type (str): filter type

        Returns:
            set of str: names of disabled filters
        """
        return self._disabled_filter_names.get(resource_label, {}).get(filter_type, set())

    def set_online(self, resource, filter_type, online):
        """Sets the given filters online or offline.

        Args:
            resource (str): Resource label
            filter_type (str): Either SCENARIO_FILTER_TYPE or TOOL_FILTER_TYPE, for now.
            online (dict): mapping from scenario/tool id to online flag
        """
        enableds = {filter_name for filter_name, is_on in online.items() if is_on}
        disableds = {filter_name for filter_name, is_on in online.items() if not is_on}
        current_disableds = self._disabled_filter_names.get(resource, {}).get(filter_type, set())
        self._disabled_filter_names.setdefault(resource, {})[filter_type] = disableds | (current_disableds - enableds)

    def refresh_resource_filter_model(self):
        """Makes resource filter mode fetch filter data from database."""
        self.resource_filter_model.build_tree()

    def receive_resources_from_source(self, resources):
        """See base class."""
        super().receive_resources_from_source(resources)
        self.link.update_icons()

    @busy_effect
    def set_connection_options(self, options):
        """Overwrites connections options.

        Args:
            options (dict): new options
        """
        if options == self.options:
            return
        self.options = options
        self.link.update_icons()
        project = self._toolbox.project()
        item = project.get_item(self.source)
        project.notify_resource_changes_to_successors(item)
        if self is self._toolbox.active_link_item:
            self._toolbox.link_properties_widgets[LoggingConnection].load_connection_options()

    def _mask_unavailable_disabled_filters(self):
        """Cross-checks disabled filters with source databases.

        Returns:
            dict: disabled filter names containing only names that exist in source databases
        """
        available_disabled_filter_names = {}
        for resource in self._resources:
            url = resource.url
            if not url:
                continue
            try:
                db_map = DatabaseMapping(url)
            except (SpineDBAPIError, SpineDBVersionError):
                continue
            try:
                disabled_scenarios = set(
                    self._disabled_filter_names.get(resource.label, {}).get(SCENARIO_FILTER_TYPE, set())
                )
                available_scenarios = {row.name for row in db_map.query(db_map.scenario_sq)}
                available_disabled_scenarios = disabled_scenarios & available_scenarios
                if available_disabled_scenarios:
                    available_disabled_filter_names.setdefault(resource.label, {})[
                        SCENARIO_FILTER_TYPE
                    ] = available_disabled_scenarios
                disabled_tools = set(self._disabled_filter_names.get(resource.label, {}).get(TOOL_FILTER_TYPE, set()))
                available_tools = {row.name for row in db_map.query(db_map.tool_sq)}
                available_disabled_tools = disabled_tools & available_tools
                if available_disabled_tools:
                    available_disabled_filter_names.setdefault(resource.label, {})[
                        TOOL_FILTER_TYPE
                    ] = available_disabled_tools
            finally:
                db_map.connection.close()
        return available_disabled_filter_names

    def to_dict(self):
        """See base class."""
        has_disabled_filters = self._has_disabled_filters()
        original = None
        if has_disabled_filters:
            # Temporarily remove unavailable filters to keep project.json clean.
            original = self._disabled_filter_names
            self._disabled_filter_names = self._mask_unavailable_disabled_filters()
        d = super().to_dict()
        if has_disabled_filters:
            self._disabled_filter_names = original
        return d

    def tear_down(self):
        """Releases system resources held by the connection."""
        self.resource_filter_model.deleteLater()


class LoggingJump(LogMixin, Jump):
    def __init__(self, *args, toolbox=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._toolbox = toolbox
        self.jump_link = None

    @property
    def graphics_item(self):
        return self.jump_link

    @staticmethod
    def item_type(self):
        return "jump"
