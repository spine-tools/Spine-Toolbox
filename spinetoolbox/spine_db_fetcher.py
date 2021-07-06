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
from spinetoolbox.helpers import busy_effect


class SpineDBFetcher(QObject):
    """Fetches content from a Spine database."""

    _fetch_more_requested = Signal(str)

    def __init__(self, db_mngr, db_map):
        """Initializes the fetcher object.

        Args:
            db_mngr (SpineDBManager): used for fetching
            db_map (DiffDatabaseMapping): The db to fetch
        """
        super().__init__()
        self._db_mngr = db_mngr
        self._db_map = db_map
        self._getters = {
            "object_class": self._db_mngr.get_object_classes,
            "relationship_class": self._db_mngr.get_relationship_classes,
            "parameter_definition": self._db_mngr.get_parameter_definitions,
            "parameter_definition_tag": self._db_mngr.get_parameter_definition_tags,
            "object": self._db_mngr.get_objects,
            "relationship": self._db_mngr.get_relationships,
            "entity_group": self._db_mngr.get_entity_groups,
            "parameter_value": self._db_mngr.get_parameter_values,
            "parameter_value_list": self._db_mngr.get_parameter_value_lists,
            "parameter_tag": self._db_mngr.get_parameter_tags,
            "alternative": self._db_mngr.get_alternatives,
            "scenario": self._db_mngr.get_scenarios,
            "scenario_alternative": self._db_mngr.get_scenario_alternatives,
            "feature": self._db_mngr.get_features,
            "tool": self._db_mngr.get_tools,
            "tool_feature": self._db_mngr.get_tool_features,
            "tool_feature_method": self._db_mngr.get_tool_feature_methods,
        }
        self._signals = {
            "object_class": self._db_mngr.object_classes_added,
            "relationship_class": self._db_mngr.relationship_classes_added,
            "parameter_definition": self._db_mngr.parameter_definitions_added,
            "parameter_definition_tag": self._db_mngr.parameter_definition_tags_added,
            "object": self._db_mngr.objects_added,
            "relationship": self._db_mngr.relationships_added,
            "entity_group": self._db_mngr.entity_groups_added,
            "parameter_value": self._db_mngr.parameter_values_added,
            "parameter_value_list": self._db_mngr.parameter_value_lists_added,
            "parameter_tag": self._db_mngr.parameter_tags_added,
            "alternative": self._db_mngr.alternatives_added,
            "scenario": self._db_mngr.scenarios_added,
            "scenario_alternative": self._db_mngr.scenario_alternatives_added,
            "feature": self._db_mngr.features_added,
            "tool": self._db_mngr.tools_added,
            "tool_feature": self._db_mngr.tool_features_added,
            "tool_feature_method": self._db_mngr.tool_feature_methods_added,
        }
        self._iterators = {item_type: getter(self._db_map) for item_type, getter in self._getters.items()}
        self._fetched = {item_type: False for item_type in self._getters}
        self.moveToThread(db_mngr.worker_thread)
        self._fetch_more_requested.connect(self._fetch_more)

    def fetch_more(self, item_type):
        """Fetches items from the database.

        Args:
            item_type (str): the type of items to fetch, e.g. "object_class"
        """
        if self._fetched[item_type]:
            return
        self._fetch_more_requested.emit(item_type)

    @Slot(str)
    def _fetch_more(self, item_type):
        self._do_fetch_more(item_type)

    @busy_effect
    def _do_fetch_more(self, item_type):
        iterator = self._iterators.get(item_type)
        if iterator is None:
            return
        with self._db_map.original_tables():
            chunk = next(iterator, [])
        if not chunk:
            self._fetched[item_type] = True
            return
        signal = self._signals.get(item_type)
        signal.emit({self._db_map: chunk})
