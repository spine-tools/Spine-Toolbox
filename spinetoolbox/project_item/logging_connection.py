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

"""Contains logging connection and jump classes."""
from spinedb_api.filters.scenario_filter import SCENARIO_FILTER_TYPE
from spinedb_api.filters.alternative_filter import ALTERNATIVE_FILTER_TYPE
from spinedb_api import DatabaseMapping, SpineDBAPIError, SpineDBVersionError
from spine_engine.project_item.connection import ResourceConvertingConnection, Jump, ConnectionBase, FilterSettings
from ..log_mixin import LogMixin
from ..mvcmodels.resource_filter_model import ResourceFilterModel
from ..helpers import busy_effect
from ..fetch_parent import FlexibleFetchParent


_DATABASE_ITEM_TYPE = {ALTERNATIVE_FILTER_TYPE: "alternative", SCENARIO_FILTER_TYPE: "scenario"}


class HeadlessConnection(ResourceConvertingConnection):
    """A project item connection that is compatible with headless mode."""

    def __init__(
        self,
        source_name,
        source_position,
        destination_name,
        destination_position,
        options=None,
        filter_settings=None,
        legacy_resource_filter_ids=None,
    ):
        super().__init__(source_name, source_position, destination_name, destination_position, options, filter_settings)
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
        specific_filter_settings = self._filter_settings.known_filters.setdefault(resource_label, {}).setdefault(
            filter_type, {}
        )
        specific_filter_settings[filter_name] = enabled

    def set_filter_type_enabled(self, filter_type, enabled):
        """Enables or disables a filter type.

        Args:
            filter_type (str): filter type
            enabled (bool): True to enable the filter type, False to disable it
        """
        self._filter_settings.enabled_filter_types[filter_type] = enabled

    def _convert_legacy_resource_filter_ids_to_filter_settings(self):
        """Converts legacy resource filter ids to filter settings.

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
                if scenario_filter_ids is not None:
                    specific_filter_settings = self._filter_settings.known_filters.setdefault(
                        resource.label, {}
                    ).setdefault(SCENARIO_FILTER_TYPE, {})
                    for row in db_map.query(db_map.scenario_sq):
                        specific_filter_settings[row.name]: row.id = row.id in scenario_filter_ids
            finally:
                db_map.close()
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
            self._convert_legacy_resource_filter_ids_to_filter_settings()

    def replace_resources_from_source(self, old, new):
        """Replaces existing resources by new ones.

        Args:
            old (list of ProjectItemResource): old resources
            new (list of ProjectItemResource): new resources
        """
        for old_resource, new_resource in zip(old, new):
            self._resources.discard(old_resource)
            old_filters = self._filter_settings.known_filters.pop(old_resource.label, None)
            if new_resource.type_ == "database":
                self._resources.add(new_resource)
                if old_filters is not None:
                    self._filter_settings.known_filters[new_resource.label] = old_filters


class LoggingConnection(LogMixin, HeadlessConnection):
    def __init__(self, *args, toolbox, **kwargs):
        super().__init__(*args, **kwargs)
        self._toolbox = toolbox
        self.resource_filter_model = ResourceFilterModel(self, toolbox.project(), toolbox.undo_stack, toolbox)
        self.link = None
        self._source_item_type = self._toolbox.project().get_item(self.source).item_type()
        self._destination_item_type = self._toolbox.project().get_item(self.destination).item_type()
        self._db_maps = {}
        self._fetch_parents = {}

    def __hash__(self):
        return super(ConnectionBase, self).__hash__()

    @staticmethod
    def item_type():
        return "connection"

    @property
    def graphics_item(self):
        return self.link

    def has_filters(self):
        """Returns True if connection has any filters.

        Returns:
            bool: True if connection has filters, False otherwise
        """
        for resource in self._resources:
            url = resource.url
            if not url:
                continue
            db_map = self._get_db_map(url, ignore_version_error=True)
            if db_map is None:
                continue
            known_filters = self._filter_settings.known_filters.get(resource.label, {})
            for filter_type, item_type in _DATABASE_ITEM_TYPE.items():
                available = {x["name"] for x in self._toolbox.db_mngr.get_items(db_map, item_type)}
                filters = known_filters.get(filter_type, {})
                if any(enabled for s, enabled in filters.items() if s in available):
                    return True
                if self._filter_settings.auto_online and any(name not in filters for name in available):
                    return True
        return False

    def _get_db_map(self, url, ignore_version_error=False):
        if url not in self._db_maps:
            db_map = self._toolbox.db_mngr.get_db_map(url, self._toolbox, ignore_version_error=ignore_version_error)
            if db_map is None:
                return None
            self._db_maps[url] = db_map
            self._toolbox.db_mngr.register_listener(self, db_map)
            self._fetch_more_if_possible()
        return self._db_maps[url]

    def _pop_unused_db_maps(self):
        """Removes unused database maps and unregisters from listening the DB manager."""
        resource_urls = {resource.url for resource in self._resources}
        resource_urls.discard(None)
        obsolete_urls = set(self._db_maps) - resource_urls
        for url in obsolete_urls:
            db_map = self._db_maps.pop(url)
            self._fetch_parents.pop(db_map)
            self._toolbox.db_mngr.unregister_listener(self, db_map)

    def _make_fetch_parent(self, db_map, item_type):
        fetch_parents = self._fetch_parents.setdefault(db_map, {})
        if item_type not in fetch_parents:
            fetch_parents[item_type] = self._fetch_parents.setdefault(db_map, {}).setdefault(
                item_type,
                FlexibleFetchParent(
                    item_type,
                    handle_items_added=lambda _: self._receive_data_changed(),
                    handle_items_removed=lambda _: self._receive_data_changed(),
                    handle_items_updated=lambda _: self._receive_data_changed(),
                    owner=self.resource_filter_model,
                ),
            )
        return fetch_parents[item_type]

    def _fetch_more_if_possible(self):
        for db_map in self._db_maps.values():
            for item_type in ("scenario",):
                fetch_parent = self._make_fetch_parent(db_map, item_type)
                if self._toolbox.db_mngr.can_fetch_more(db_map, fetch_parent):
                    self._toolbox.db_mngr.fetch_more(db_map, fetch_parent)

    def _receive_data_changed(self):
        self.link.update_icons()
        self.refresh_resource_filter_model()
        self._fetch_more_if_possible()

    def receive_session_committed(self, db_maps, cookie):
        self._receive_data_changed()

    def receive_session_rolled_back(self, db_map):
        self._receive_data_changed()

    def receive_error_msg(self, _db_map_error_log):
        pass

    def get_filter_item_names(self, filter_type, url):
        db_map = self._get_db_map(url)
        if db_map is None:
            return []
        item_type = _DATABASE_ITEM_TYPE[filter_type]
        return sorted(x["name"] for x in self._toolbox.db_mngr.get_items(db_map, item_type))

    def _do_purge_before_writing(self, resources):
        purged_urls = super()._do_purge_before_writing(resources)
        committed_db_maps = set()
        for url in purged_urls:
            db_map = self._toolbox.db_mngr.db_map(url)
            if db_map:
                committed_db_maps.add(db_map)
        if committed_db_maps:
            self._toolbox.db_mngr.notify_session_committed(self, *committed_db_maps)
        return purged_urls

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

    def online_filters(self, resource_label, filter_type):
        """Returns filter online states for given resource and filter type.

        Args:
            resource_label (str): resource label
            filter_type (str): filter type

        Returns:
            dict: mapping from filter names to online states
        """
        found_resource = None
        for resource in self._resources:
            if resource.label == resource_label:
                found_resource = resource
                break
        if found_resource is None:
            return {}
        return self._resource_filters_online(found_resource, filter_type)

    def set_online(self, resource, filter_type, online):
        """Sets the given filters online or offline.

        Args:
            resource (str): Resource label
            filter_type (str): filter type
            online (dict): mapping from scenario name to online flag
        """
        self._filter_settings.known_filters.setdefault(resource, {}).setdefault(filter_type, {}).update(online)

    def set_filter_default_online_status(self, auto_online):
        """Sets the auto_online flag.

        Args:
            auto_online (bool): If True, unknown filters are online by default
        """
        self._filter_settings.auto_online = auto_online
        if self is self._toolbox.active_link_item:
            self._toolbox.link_properties_widgets[LoggingConnection].set_auto_check_filters_state(auto_online)

    def refresh_resource_filter_model(self):
        """Makes resource filter mode fetch filter data from database."""
        self.resource_filter_model.build_tree()

    def set_filter_type_enabled(self, filter_type, enabled):
        """See base class."""
        super().set_filter_type_enabled(filter_type, enabled)
        self.resource_filter_model.set_filter_type_enabled(filter_type, enabled)
        if self is self._toolbox.active_link_item:
            self._toolbox.link_properties_widgets[LoggingConnection].set_filter_type_enabled(filter_type, enabled)

    def receive_resources_from_source(self, resources):
        """See base class."""
        super().receive_resources_from_source(resources)
        self._pop_unused_db_maps()
        self.link.update_icons()

    def replace_resources_from_source(self, old, new):
        """See base class."""
        super().replace_resources_from_source(old, new)
        self._pop_unused_db_maps()
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
        project = self._toolbox.project()
        sibling_conns = project.incoming_connections(self.destination)
        for conn in sibling_conns:
            conn.link.update_icons()
        project.notify_resource_changes_to_successors(project.get_item(self.source))
        project.notify_resource_changes_to_predecessors(project.get_item(self.destination))
        if self is self._toolbox.active_link_item:
            self._toolbox.link_properties_widgets[LoggingConnection].load_connection_options()

    def _check_available_filters(self):
        """Cross-checks filter settings with source databases.

        Returns:
            FilterSettings: filter settings containing only filters that exist in source databases
        """
        filter_settings = FilterSettings(
            auto_online=self._filter_settings.auto_online,
            enabled_filter_types=self._filter_settings.enabled_filter_types,
        )
        for resource in self._resources:
            for filter_type in (SCENARIO_FILTER_TYPE, ALTERNATIVE_FILTER_TYPE):
                online_filters = self._resource_filters_online(resource, filter_type)
                if online_filters is not None:
                    filter_settings.known_filters.setdefault(resource.label, {})[filter_type] = online_filters
        return filter_settings

    def _resource_filters_online(self, resource, filter_type):
        url = resource.url
        if not url:
            return None
        db_map = self._get_db_map(url)
        if db_map is None:
            return None
        db_item_type = _DATABASE_ITEM_TYPE[filter_type]
        available_filters = (x["name"] for x in self._toolbox.db_mngr.get_items(db_map, db_item_type))
        specific_filter_settings = self._filter_settings.known_filters.get(resource.label, {}).get(filter_type, {})
        checked_specific_filter_settings = {}
        for name in sorted(available_filters):
            checked_specific_filter_settings[name] = specific_filter_settings.get(
                name, self._filter_settings.auto_online
            )
        return checked_specific_filter_settings

    def to_dict(self):
        """See base class."""
        original = None
        if self.has_filters():
            # Temporarily remove unavailable filters to keep project.json clean.
            original = self._filter_settings
            self._filter_settings = self._check_available_filters()
        d = super().to_dict()
        if original is not None:
            self._filter_settings = original
        return d

    def tear_down(self):
        """Releases system resources held by the connection."""
        for db_map in self._db_maps.values():
            self._toolbox.db_mngr.unregister_listener(self, db_map)
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
