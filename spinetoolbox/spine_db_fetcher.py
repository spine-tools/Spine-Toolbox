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

"""
SpineDBFetcher class.

:authors: M. Marin (KTH)
:date:   13.3.2020
"""

from PySide2.QtCore import Signal, Slot, QObject


class SpineDBFetcher(QObject):
    """Fetches content from a Spine database and 'sends' them to another thread (via a signal-slot mechanism of course),
    so contents can be processed in that thread without affecting the UI."""

    finished = Signal()
    _fetch_requested = Signal(object, object)

    def __init__(self, db_mngr, listener):
        """Initializes the fetcher object.

        Args:
            db_mngr (SpineDBManager)
            listener (SpineDBEditor)
        """
        super().__init__()
        self._db_mngr = db_mngr
        self._listener = listener
        self.is_finished = False
        self.moveToThread(db_mngr.thread)
        self._fetch_requested.connect(self._do_fetch)

    def fetch(self, db_maps, tablenames=None):
        """Fetches items from the database and emit added signals.

        Args:
            db_maps (Iterable of DatabaseMappingBase): database maps to fetch
            tablenames (list, optional): If given, only fetches tables in this list, otherwise fetches them all
        """
        self._fetch_requested.emit(db_maps, tablenames)

    def close(self):
        self.deleteLater()

    @Slot(object, object)
    def _do_fetch(self, db_maps, tablenames):
        getter_receiver_lookup = {
            "object_class": (self._db_mngr.get_object_classes, self._receive_object_classes_added),
            "relationship_class": (self._db_mngr.get_relationship_classes, self._receive_relationship_classes_added),
            "parameter_definition": (
                self._db_mngr.get_parameter_definitions,
                self._receive_parameter_definitions_added,
            ),
            "parameter_definition_tag": (
                self._db_mngr.get_parameter_definition_tags,
                self._receive_parameter_definition_tags_added,
            ),
            "object": (self._db_mngr.get_objects, self._receive_objects_added),
            "relationship": (self._db_mngr.get_relationships, self._receive_relationships_added),
            "entity_group": (self._db_mngr.get_entity_groups, self._receive_entity_groups_added),
            "parameter_value": (self._db_mngr.get_parameter_values, self._receive_parameter_values_added),
            "parameter_value_list": (
                self._db_mngr.get_parameter_value_lists,
                self._receive_parameter_value_lists_added,
            ),
            "parameter_tag": (self._db_mngr.get_parameter_tags, self._receive_parameter_tags_added),
            "alternative": (self._db_mngr.get_alternatives, self._receive_alternatives_added),
            "scenario": (self._db_mngr.get_scenarios, self._receive_scenarios_added),
            "scenario_alternative": (
                self._db_mngr.get_scenario_alternatives,
                self._receive_scenario_alternatives_added,
            ),
            "feature": (self._db_mngr.get_features, self._receive_features_added),
            "tool": (self._db_mngr.get_tools, self._receive_tools_added),
            "tool_feature": (self._db_mngr.get_tool_features, self._receive_tool_features_added),
            "tool_feature_method": (self._db_mngr.get_tool_feature_methods, self._receive_tool_feature_methods_added),
        }
        if tablenames is None:
            tablenames = getter_receiver_lookup.keys()
        for tablename in tablenames:
            getter_receiver = getter_receiver_lookup.get(tablename)
            if getter_receiver is None:
                continue
            getter, receiver = getter_receiver
            for db_map in db_maps:
                for chunk in getter(db_map):
                    receiver({db_map: chunk})
        self.finished.emit()
        self.is_finished = True

    def _receive_alternatives_added(self, db_map_data):
        self._db_mngr.cache_items("alternative", db_map_data)
        self._listener.receive_alternatives_added(db_map_data)

    def _receive_scenarios_added(self, db_map_data):
        self._db_mngr.cache_items("scenario", db_map_data)
        self._listener.receive_scenarios_added(db_map_data)

    def _receive_scenario_alternatives_added(self, db_map_data):
        self._db_mngr.cache_items("scenario_alternative", db_map_data)

    def _receive_object_classes_added(self, db_map_data):
        self._db_mngr.cache_items("object_class", db_map_data)
        self._db_mngr.update_icons(db_map_data)
        self._listener.receive_object_classes_added(db_map_data)

    def _receive_objects_added(self, db_map_data):
        self._db_mngr.cache_items("object", db_map_data)
        self._listener.receive_objects_added(db_map_data)

    def _receive_relationship_classes_added(self, db_map_data):
        self._db_mngr.cache_items("relationship_class", db_map_data)
        self._listener.receive_relationship_classes_added(db_map_data)

    def _receive_relationships_added(self, db_map_data):
        self._db_mngr.cache_items("relationship", db_map_data)
        self._listener.receive_relationships_added(db_map_data)

    def _receive_entity_groups_added(self, db_map_data):
        self._db_mngr.cache_items("entity_group", db_map_data)
        self._listener.receive_entity_groups_added(db_map_data)

    def _receive_parameter_definitions_added(self, db_map_data):
        self._db_mngr.cache_items("parameter_definition", db_map_data)
        self._listener.receive_parameter_definitions_added(db_map_data)

    def _receive_parameter_definition_tags_added(self, db_map_data):
        self._db_mngr.cache_items("parameter_definition_tag", db_map_data)

    def _receive_parameter_values_added(self, db_map_data):
        self._db_mngr.cache_items("parameter_value", db_map_data)
        self._listener.receive_parameter_values_added(db_map_data)

    def _receive_parameter_value_lists_added(self, db_map_data):
        self._db_mngr.cache_items("parameter_value_list", db_map_data)
        self._listener.receive_parameter_value_lists_added(db_map_data)

    def _receive_parameter_tags_added(self, db_map_data):
        self._db_mngr.cache_items("parameter_tag", db_map_data)
        self._listener.receive_parameter_tags_added(db_map_data)

    def _receive_features_added(self, db_map_data):
        self._db_mngr.cache_items("feature", db_map_data)
        self._listener.receive_features_added(db_map_data)

    def _receive_tools_added(self, db_map_data):
        self._db_mngr.cache_items("tool", db_map_data)
        self._listener.receive_tools_added(db_map_data)

    def _receive_tool_features_added(self, db_map_data):
        self._db_mngr.cache_items("tool_feature", db_map_data)
        self._listener.receive_tool_features_added(db_map_data)

    def _receive_tool_feature_methods_added(self, db_map_data):
        self._db_mngr.cache_items("tool_feature_method", db_map_data)
        self._listener.receive_tool_feature_methods_added(db_map_data)
