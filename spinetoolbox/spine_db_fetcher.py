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
    """Fetches content from a Spine database and 'sends' them to another thread (via a signal-slot mechanism of course),
    so contents can be processed in that thread without affecting the UI."""

    finished = Signal(object)
    _ready_to_finish = Signal()
    _scenarios_fetched = Signal(object)
    _alternatives_fetched = Signal(object)
    _scenario_alternatives_fetched = Signal(object)
    _object_classes_fetched = Signal(object)
    _objects_fetched = Signal(object)
    _relationship_classes_fetched = Signal(object)
    _relationships_fetched = Signal(object)
    _entity_groups_fetched = Signal(object)
    _parameter_definitions_fetched = Signal(object)
    _parameter_values_fetched = Signal(object)
    _parameter_value_lists_fetched = Signal(object)
    _parameter_tags_fetched = Signal(object)

    def __init__(self, db_mngr, listener):
        """Initializes the fetcher object.

        Args:
            db_mngr (SpineDBManager)
            listener (DataStoreForm)
        """
        super().__init__()
        self._db_mngr = db_mngr
        self._listener = listener
        self._thread = QThread()
        # NOTE: by moving this to another thread, all the slots defined below are called on that thread too
        self.moveToThread(self._thread)
        self._thread.start()
        self.connect_signals()

    def connect_signals(self):
        """Connects signals."""
        self._ready_to_finish.connect(self._emit_finished_signal)
        self._alternatives_fetched.connect(self._receive_alternatives_fetched)
        self._scenarios_fetched.connect(self._receive_scenarios_fetched)
        self._scenario_alternatives_fetched.connect(self._receive_scenario_alternatives_fetched)
        self._object_classes_fetched.connect(self._receive_object_classes_fetched)
        self._objects_fetched.connect(self._receive_objects_fetched)
        self._relationship_classes_fetched.connect(self._receive_relationship_classes_fetched)
        self._relationships_fetched.connect(self._receive_relationships_fetched)
        self._entity_groups_fetched.connect(self._receive_entity_groups_fetched)
        self._parameter_definitions_fetched.connect(self._receive_parameter_definitions_fetched)
        self._parameter_values_fetched.connect(self._receive_parameter_values_fetched)
        self._parameter_value_lists_fetched.connect(self._receive_parameter_value_lists_fetched)
        self._parameter_tags_fetched.connect(self._receive_parameter_tags_fetched)

    def fetch(self, db_maps):
        """Fetches items from the database and emit fetched signals.
        """
        self._listener.setCursor(QCursor(Qt.BusyCursor))
        self._listener.silenced = True
        object_classes = {x: self._db_mngr.get_object_classes(x) for x in db_maps}
        self._object_classes_fetched.emit(object_classes)
        relationship_classes = {x: self._db_mngr.get_relationship_classes(x) for x in db_maps}
        self._relationship_classes_fetched.emit(relationship_classes)
        parameter_definitions = {x: self._db_mngr.get_parameter_definitions(x) for x in db_maps}
        self._parameter_definitions_fetched.emit(parameter_definitions)
        objects = {x: self._db_mngr.get_objects(x) for x in db_maps}
        self._objects_fetched.emit(objects)
        relationships = {x: self._db_mngr.get_relationships(x) for x in db_maps}
        self._relationships_fetched.emit(relationships)
        entity_groups = {x: self._db_mngr.get_entity_groups(x) for x in db_maps}
        self._entity_groups_fetched.emit(entity_groups)
        parameter_values = {x: self._db_mngr.get_parameter_values(x) for x in db_maps}
        self._parameter_values_fetched.emit(parameter_values)
        parameter_value_lists = {x: self._db_mngr.get_parameter_value_lists(x) for x in db_maps}
        self._parameter_value_lists_fetched.emit(parameter_value_lists)
        parameter_tags = {x: self._db_mngr.get_parameter_tags(x) for x in db_maps}
        self._parameter_tags_fetched.emit(parameter_tags)
        alternatives = {x: self._db_mngr.get_alternatives(x) for x in db_maps}
        self._alternatives_fetched.emit(alternatives)
        scenarios = {x: self._db_mngr.get_scenarios(x) for x in db_maps}
        self._scenarios_fetched.emit(scenarios)
        scenario_alternatives = {x: self._db_mngr.get_scenario_alternatives(x) for x in db_maps}
        self._scenario_alternatives_fetched.emit(scenario_alternatives)
        self._ready_to_finish.emit()

    def clean_up(self):
        self._listener.silenced = False
        self._listener.unsetCursor()
        self.quit()

    def quit(self):
        self._thread.quit()
        self._thread.wait()

    @Slot(object)
    def _receive_alternatives_fetched(self, db_map_data):
        self._db_mngr.cache_items("alternative", db_map_data)
        self._listener.receive_alternatives_added(db_map_data)

    @Slot(object)
    def _receive_scenarios_fetched(self, db_map_data):
        self._db_mngr.cache_items("scenario", db_map_data)
        self._listener.receive_scenarios_added(db_map_data)

    @Slot(object)
    def _receive_scenario_alternatives_fetched(self, db_map_data):
        self._db_mngr.cache_items("scenario_alternative", db_map_data)
        self._listener.receive_scenario_alternatives_added(db_map_data)

    @Slot(object)
    def _receive_object_classes_fetched(self, db_map_data):
        self._db_mngr.cache_items("object class", db_map_data)
        self._db_mngr.update_icons(db_map_data)
        self._listener.receive_object_classes_fetched(db_map_data)

    @Slot(object)
    def _receive_objects_fetched(self, db_map_data):
        self._db_mngr.cache_items("object", db_map_data)
        self._listener.receive_objects_fetched(db_map_data)

    @Slot(object)
    def _receive_relationship_classes_fetched(self, db_map_data):
        self._db_mngr.cache_items("relationship class", db_map_data)
        self._listener.receive_relationship_classes_fetched(db_map_data)

    @Slot(object)
    def _receive_relationships_fetched(self, db_map_data):
        self._db_mngr.cache_items("relationship", db_map_data)
        self._listener.receive_relationships_fetched(db_map_data)

    @Slot(object)
    def _receive_entity_groups_fetched(self, db_map_data):
        self._db_mngr.cache_items("entity group", db_map_data)
        self._listener.receive_entity_groups_fetched(db_map_data)

    @Slot(object)
    def _receive_parameter_definitions_fetched(self, db_map_data):
        self._db_mngr.cache_items("parameter definition", db_map_data)
        self._listener.receive_parameter_definitions_fetched(db_map_data)

    @Slot(object)
    def _receive_parameter_values_fetched(self, db_map_data):
        self._db_mngr.cache_items("parameter value", db_map_data)
        self._listener.receive_parameter_values_fetched(db_map_data)

    @Slot(object)
    def _receive_parameter_value_lists_fetched(self, db_map_data):
        self._db_mngr.cache_items("parameter value list", db_map_data)
        self._listener.receive_parameter_value_lists_fetched(db_map_data)

    @Slot(object)
    def _receive_parameter_tags_fetched(self, db_map_data):
        self._db_mngr.cache_items("parameter tag", db_map_data)
        self._listener.receive_parameter_tags_fetched(db_map_data)

    @Slot()
    def _emit_finished_signal(self):
        self.finished.emit(self)
