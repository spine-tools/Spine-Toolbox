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
from ..helpers import busy_effect, ItemTypeFetchParent


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
                self._disabled_filter_names.setdefault(resource.label, {})[SCENARIO_FILTER_TYPE] = disabled_scenarios
                tool_filter_ids = resource_filter_ids.get(TOOL_FILTER_TYPE)
                disabled_tools = set()
                if tool_filter_ids is not None:
                    for row in db_map.query(db_map.tool_sq):
                        if row.id not in tool_filter_ids:
                            disabled_tools.add(row.name)
                self._disabled_filter_names.setdefault(resource.label, {})[TOOL_FILTER_TYPE] = disabled_tools
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
        self._source_item_type = self._toolbox.project().get_item(self.source).item_type()
        self._destination_item_type = self._toolbox.project().get_item(self.destination).item_type()
        self._db_maps = {}
        self._fetch_parents = {}

    def __hash__(self):
        # FIXME: Don't we have this in the Base class?
        return hash((self.source, self._source_position, self.destination, self._destination_position))

    @staticmethod
    def item_type():
        return "connection"

    @property
    def graphics_item(self):
        return self.link

    @property
    def has_filters(self):
        for resource in self._resources:
            url = resource.url
            if not url:
                continue
            disabled_scenarios = set(self._disabled_filter_names.get(resource.label, {}).get(SCENARIO_FILTER_TYPE, ()))
            disabled_tools = set(self._disabled_filter_names.get(resource.label, {}).get(TOOL_FILTER_TYPE, ()))
            if not disabled_scenarios and not disabled_tools:
                return True
            db_map = self._get_db_map(url)
            available_scenarios = {
                x["name"] for x in self._toolbox.db_mngr.get_items(db_map, "scenario", only_visible=True)
            }
            enabled_scenarios = available_scenarios - disabled_scenarios
            if enabled_scenarios:
                return True
            available_tools = {x["name"] for x in self._toolbox.db_mngr.get_items(db_map, "tool", only_visible=True)}
            enabled_tools = available_tools - disabled_tools
            if enabled_tools:
                return True
        return False

    def _get_db_map(self, url):
        if url not in self._db_maps:
            self._db_maps[url] = db_map = self._toolbox.db_mngr.get_db_map(url, self._toolbox)
            self._toolbox.db_mngr.register_listener(self, db_map)
            self._fetch_more_if_possible()
        return self._db_maps[url]

    def _pop_unused_db_maps(self):
        resource_urls = {resource.url for resource in self._resources}
        resource_urls.discard(None)
        obsolete_urls = set(self._db_maps) - resource_urls
        for url in obsolete_urls:
            db_map = self._db_maps.pop(url)
            self._toolbox.db_mngr.unregister_listener(self, db_map)
            self._fetch_parents.pop(db_map)

    def _fetch_more_if_possible(self):
        for db_map in self._db_maps.values():
            for item_type in ("scenario", "tool"):
                fetch_parent = self._fetch_parents.setdefault(db_map, {}).setdefault(
                    item_type, ItemTypeFetchParent(item_type)
                )
                if self._toolbox.db_mngr.can_fetch_more(db_map, fetch_parent):
                    self._toolbox.db_mngr.fetch_more(db_map, fetch_parent)

    def _receive_data_changed(self):
        self.link.update_icons()
        self.refresh_resource_filter_model()
        self._fetch_more_if_possible()

    def receive_scenarios_added(self, _db_map_data):
        self._receive_data_changed()

    def receive_scenarios_removed(self, _db_map_data):
        self._receive_data_changed()

    def receive_scenarios_updated(self, _db_map_data):
        self._receive_data_changed()

    def receive_tools_added(self, _db_map_data):
        self._receive_data_changed()

    def receive_tools_removed(self, _db_map_data):
        self._receive_data_changed()

    def receive_tools_updated(self, _db_map_data):
        self._receive_data_changed()

    def get_scenario_names(self, url):
        db_map = self._get_db_map(url)
        return sorted(x["name"] for x in self._toolbox.db_mngr.get_items(db_map, "scenario", only_visible=True))

    def get_tool_names(self, url):
        db_map = self._get_db_map(url)
        return sorted(x["name"] for x in self._toolbox.db_mngr.get_items(db_map, "tool", only_visible=True))

    def may_have_filters(self):
        """Returns whether this connection may have filters.

        Returns:
            bool: True if it is possible for the connection to have filters, False otherwise
        """
        return bool(self._resources)

    def may_have_write_index(self):
        """Returns whether this connection may have write index.

        Returns:
            bool: True if it is possible for the connection to have write index, False otherwise
        """
        return self._destination_item_type == "Data Store"

    def may_use_memory_db(self):
        """Returns whether this connection may use memory DB.

        Returns:
            bool: True if it is possible for the connection to use memory DB, False otherwise
        """
        return {"Tool", "Data Store"} == {self._source_item_type, self._destination_item_type}

    def may_use_datapackage(self):
        """Returns whether this connection may use datapackage.

        Returns:
            bool: True if it is possible for the connection to use datapackage, False otherwise
        """
        return self._source_item_type in {"Exporter", "Data Connection", "Tool"}

    def may_purge_before_writing(self):
        """Returns whether this connection may purge before writing.

        Returns:
            bool: True if it is possible for the connection to purge before writing, False otherwise
        """
        return self._destination_item_type == "Data Store"

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
        enabled = {filter_name for filter_name, is_on in online.items() if is_on}
        disabled = {filter_name for filter_name, is_on in online.items() if not is_on}
        current_disabled = self._disabled_filter_names.get(resource, {}).get(filter_type, set())
        self._disabled_filter_names.setdefault(resource, {})[filter_type] = disabled | (current_disabled - enabled)

    def refresh_resource_filter_model(self):
        """Makes resource filter mode fetch filter data from database."""
        self.resource_filter_model.build_tree()

    def receive_resources_from_source(self, resources):
        """See base class."""
        super().receive_resources_from_source(resources)
        self._pop_unused_db_maps()
        self.link.update_icons()

    def replace_resources_from_source(self, old, new):
        """See base class."""
        super().replace_resources_from_source(old, new)
        self._pop_unused_db_maps()

    @busy_effect
    def set_connection_options(self, options):
        """Overwrites connections options.

        Args:
            options (dict): new options
        """
        if options == self.options:
            return
        self.options = options
        project = self._toolbox.project()
        sibling_conns = project.incoming_connections(self.destination)
        for conn in sibling_conns:
            conn.link.update_icons()
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
    def item_type():
        return "jump"
