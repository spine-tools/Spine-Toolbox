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
SpineDBFetcher class.

:authors: M. Marin (KTH)
:date:   13.3.2020
"""

from PySide2.QtCore import Signal, Slot, QObject, QThread, Qt
from PySide2.QtGui import QCursor


class SpineDBFetcher(QObject):
    """Handles signals from DB manager and channels them to listeners."""

    scenarios_fetched = Signal(object)
    alternatives_fetched = Signal(object)
    scenario_alternatives_fetched = Signal(object)
    object_classes_fetched = Signal(object)
    objects_fetched = Signal(object)
    relationship_classes_fetched = Signal(object)
    relationships_fetched = Signal(object)
    entity_groups_fetched = Signal(object)
    parameter_definitions_fetched = Signal(object)
    parameter_values_fetched = Signal(object)
    parameter_value_lists_fetched = Signal(object)
    parameter_tags_fetched = Signal(object)

    def __init__(self, db_mngr, listener, *db_maps):
        """Initializes the fetcher object.

        Args:
            db_mngr (SpineDBManager)
            listener (DataStoreForm)
            db_maps (DiffDatabaseMapping)
        """
        super().__init__()
        self.db_mngr = db_mngr
        self.listener = listener
        self.db_maps = db_maps
        self._thread = QThread()
        self.moveToThread(self._thread)
        self._thread.start()
        self.connect_signals()

    def connect_signals(self):
        """Connects signals."""
        self.alternatives_fetched.connect(self.receive_alternatives_fetched)
        self.scenarios_fetched.connect(self.receive_scenarios_fetched)
        self.scenario_alternatives_fetched.connect(self.receive_scenario_alternatives_fetched)
        self.object_classes_fetched.connect(self.receive_object_classes_fetched)
        self.objects_fetched.connect(self.receive_objects_fetched)
        self.relationship_classes_fetched.connect(self.receive_relationship_classes_fetched)
        self.relationships_fetched.connect(self.receive_relationships_fetched)
        self.entity_groups_fetched.connect(self.receive_entity_groups_fetched)
        self.parameter_definitions_fetched.connect(self.receive_parameter_definitions_fetched)
        self.parameter_values_fetched.connect(self.receive_parameter_values_fetched)
        self.parameter_value_lists_fetched.connect(self.receive_parameter_value_lists_fetched)
        self.parameter_tags_fetched.connect(self.receive_parameter_tags_fetched)
        self.destroyed.connect(lambda: self.clean_up())  # pylint: disable=unnecessary-lambda
        qApp.aboutToQuit.connect(self._thread.quit)  # pylint: disable=undefined-variable

    def run(self):
        self.listener.setCursor(QCursor(Qt.BusyCursor))
        self.listener.silenced = True
        object_classes = {x: self.db_mngr.get_object_classes(x) for x in self.db_maps}
        relationship_classes = {x: self.db_mngr.get_relationship_classes(x) for x in self.db_maps}
        parameter_definitions = {x: self.db_mngr.get_parameter_definitions(x) for x in self.db_maps}
        objects = {x: self.db_mngr.get_objects(x) for x in self.db_maps}
        relationships = {x: self.db_mngr.get_relationships(x) for x in self.db_maps}
        entity_groups = {x: self.db_mngr.get_entity_groups(x) for x in self.db_maps}
        parameter_values = {x: self.db_mngr.get_parameter_values(x) for x in self.db_maps}
        parameter_value_lists = {x: self.db_mngr.get_parameter_value_lists(x) for x in self.db_maps}
        parameter_tags = {x: self.db_mngr.get_parameter_tags(x) for x in self.db_maps}
        alternatives = {x: self.db_mngr.get_alternatives(x) for x in self.db_maps}
        scenarios = {x: self.db_mngr.get_scenarios(x) for x in self.db_maps}
        scenario_alternatives = {x: self.db_mngr.get_scenario_alternatives(x) for x in self.db_maps}
        self.object_classes_fetched.emit(object_classes)
        self.relationship_classes_fetched.emit(relationship_classes)
        self.parameter_definitions_fetched.emit(parameter_definitions)
        self.objects_fetched.emit(objects)
        self.relationships_fetched.emit(relationships)
        self.entity_groups_fetched.emit(entity_groups)
        self.parameter_values_fetched.emit(parameter_values)
        self.parameter_value_lists_fetched.emit(parameter_value_lists)
        self.parameter_tags_fetched.emit(parameter_tags)
        self.alternatives_fetched.emit(alternatives)
        self.scenarios_fetched.emit(scenarios)
        self.scenario_alternatives_fetched.emit(scenario_alternatives)
        self.deleteLater()

    def clean_up(self):
        self._thread.quit()
        self.listener.silenced = False
        self.listener.unsetCursor()

    @Slot(object)
    def receive_alternatives_fetched(self, db_map_data):
        self.db_mngr.cache_items("alternative", db_map_data)
        self.listener.receive_alternatives_added(db_map_data)

    @Slot(object)
    def receive_scenarios_fetched(self, db_map_data):
        self.db_mngr.cache_items("scenario", db_map_data)
        self.listener.receive_scenarios_added(db_map_data)

    @Slot(object)
    def receive_scenario_alternatives_fetched(self, db_map_data):
        self.db_mngr.cache_items("scenario_alternative", db_map_data)
        self.listener.receive_scenario_alternatives_added(db_map_data)

    @Slot(object)
    def receive_object_classes_fetched(self, db_map_data):
        self.db_mngr.cache_items("object class", db_map_data)
        self.db_mngr.update_icons(db_map_data)
        self.listener.receive_object_classes_fetched(db_map_data)

    @Slot(object)
    def receive_objects_fetched(self, db_map_data):
        self.db_mngr.cache_items("object", db_map_data)
        self.listener.receive_objects_fetched(db_map_data)

    @Slot(object)
    def receive_relationship_classes_fetched(self, db_map_data):
        self.db_mngr.cache_items("relationship class", db_map_data)
        self.listener.receive_relationship_classes_fetched(db_map_data)

    @Slot(object)
    def receive_relationships_fetched(self, db_map_data):
        self.db_mngr.cache_items("relationship", db_map_data)
        self.listener.receive_relationships_fetched(db_map_data)

    @Slot(object)
    def receive_entity_groups_fetched(self, db_map_data):
        self.db_mngr.cache_items("entity group", db_map_data)
        self.listener.receive_entity_groups_fetched(db_map_data)

    @Slot(object)
    def receive_parameter_definitions_fetched(self, db_map_data):
        self.db_mngr.cache_items("parameter definition", db_map_data)
        self.listener.receive_parameter_definitions_fetched(db_map_data)

    @Slot(object)
    def receive_parameter_values_fetched(self, db_map_data):
        self.db_mngr.cache_items("parameter value", db_map_data)
        self.listener.receive_parameter_values_fetched(db_map_data)

    @Slot(object)
    def receive_parameter_value_lists_fetched(self, db_map_data):
        self.db_mngr.cache_items("parameter value list", db_map_data)
        self.listener.receive_parameter_value_lists_fetched(db_map_data)

    @Slot(object)
    def receive_parameter_tags_fetched(self, db_map_data):
        self.db_mngr.cache_items("parameter tag", db_map_data)
        self.listener.receive_parameter_tags_fetched(db_map_data)
