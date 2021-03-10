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
    """Fetches content from a Spine database."""

    finished = Signal()
    _started = Signal()

    def __init__(self, db_mngr, mini):
        """Initializes the fetcher object.

        Args:
            db_mngr (SpineDBManager): used for fetching.
            mini (MiniSpineDBManager): used for signalling about the fetching.
                It has the same cache and icon_mngr as db_mngr but not the same signaller.
                This means we can signal only to a specific listener.
        """
        super().__init__()
        self._db_mngr = db_mngr
        self._mini = mini
        self.moveToThread(db_mngr.thread)
        self._started.connect(self._do_fetch)
        self._db_maps = None
        self._tablenames = None
        self.prepared = False
        self.started = False

    def clean_up(self):
        self.deleteLater()
        self._mini.deleteLater()

    def fetch(self, listener, db_maps, tablenames=None):
        """Fetches items from the database and emit added signals.

        Args:
            db_maps (Iterable of DatabaseMappingBase): database maps to fetch
            tablenames (list, optional): If given, only fetches tables in this list, otherwise fetches them all
        """
        for db_map in db_maps:
            self._mini.signaller.add_db_map_listener(db_map, listener)
        self._db_maps = db_maps
        self._tablenames = tablenames
        self.prepared = True
        self._db_mngr.fetch_next()

    def start(self):
        self.started = True
        self._started.emit()

    @Slot()
    def _do_fetch(self):
        getter_signal_lookup = {
            "object_class": (self._db_mngr.get_object_classes, self._mini.object_classes_added),
            "relationship_class": (self._db_mngr.get_relationship_classes, self._mini.relationship_classes_added),
            "parameter_definition": (self._db_mngr.get_parameter_definitions, self._mini.parameter_definitions_added),
            "parameter_definition_tag": (
                self._db_mngr.get_parameter_definition_tags,
                self._mini.parameter_definition_tags_added,
            ),
            "object": (self._db_mngr.get_objects, self._mini.objects_added),
            "relationship": (self._db_mngr.get_relationships, self._mini.relationships_added),
            "entity_group": (self._db_mngr.get_entity_groups, self._mini.entity_groups_added),
            "parameter_value": (self._db_mngr.get_parameter_values, self._mini.parameter_values_added),
            "parameter_value_list": (self._db_mngr.get_parameter_value_lists, self._mini.parameter_value_lists_added),
            "parameter_tag": (self._db_mngr.get_parameter_tags, self._mini.parameter_tags_added),
            "alternative": (self._db_mngr.get_alternatives, self._mini.alternatives_added),
            "scenario": (self._db_mngr.get_scenarios, self._mini.scenarios_added),
            "scenario_alternative": (self._db_mngr.get_scenario_alternatives, self._mini.scenario_alternatives_added),
            "feature": (self._db_mngr.get_features, self._mini.features_added),
            "tool": (self._db_mngr.get_tools, self._mini.tools_added),
            "tool_feature": (self._db_mngr.get_tool_features, self._mini.tool_features_added),
            "tool_feature_method": (self._db_mngr.get_tool_feature_methods, self._mini.tool_feature_methods_added),
        }
        if self._tablenames is None:
            self._tablenames = getter_signal_lookup.keys()
        for tablename in self._tablenames:
            getter_signal = getter_signal_lookup.get(tablename)
            if getter_signal is None:
                continue
            getter, signal = getter_signal
            for db_map in self._db_maps:
                for chunk in getter(db_map):
                    signal.emit({db_map: chunk})
        self.finished.emit()
