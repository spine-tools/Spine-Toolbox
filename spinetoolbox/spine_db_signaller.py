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
Spine DB Signaller class.

:authors: M. Marin (KTH)
:date:   31.10.2019
"""

from PySide2.QtCore import Slot


class SpineDBSignaller:
    """Handles signals from DB manager and channels them to listeners."""

    def __init__(self, db_mngr):
        """Initializes the signaler object.

        Args:
            db_mngr (SpineDBManager)
        """
        self.db_mngr = db_mngr
        self.listeners = dict()

    def add_db_map_listener(self, db_map, listener):
        """Adds listener for given db_map."""
        self.listeners.setdefault(listener, set()).add(db_map)

    def remove_db_map_listener(self, db_map, listener):
        """Removes db_map from the the maps listener listens to."""
        db_maps = self.listeners.get(listener, set())
        if db_map in db_maps:
            db_maps.remove(db_map)
            if not db_maps:
                self.listeners.pop(listener)

    def db_map_listeners(self, db_map):
        return set(listener for listener, db_maps in self.listeners.items() if db_map in db_maps)

    def connect_signals(self):
        """Connects signals."""
        # Added
        self.db_mngr.object_classes_added.connect(self.receive_object_classes_added)
        self.db_mngr.objects_added.connect(self.receive_objects_added)
        self.db_mngr.relationship_classes_added.connect(self.receive_relationship_classes_added)
        self.db_mngr.relationships_added.connect(self.receive_relationships_added)
        self.db_mngr.parameter_definitions_added.connect(self.receive_parameter_definitions_added)
        self.db_mngr.parameter_values_added.connect(self.receive_parameter_values_added)
        self.db_mngr.parameter_value_lists_added.connect(self.receive_parameter_value_lists_added)
        self.db_mngr.parameter_tags_added.connect(self.receive_parameter_tags_added)
        # Updated
        self.db_mngr.object_classes_updated.connect(self.receive_object_classes_updated)
        self.db_mngr.objects_updated.connect(self.receive_objects_updated)
        self.db_mngr.relationship_classes_updated.connect(self.receive_relationship_classes_updated)
        self.db_mngr.relationships_updated.connect(self.receive_relationships_updated)
        self.db_mngr.parameter_definitions_updated.connect(self.receive_parameter_definitions_updated)
        self.db_mngr.parameter_values_updated.connect(self.receive_parameter_values_updated)
        self.db_mngr.parameter_value_lists_updated.connect(self.receive_parameter_value_lists_updated)
        self.db_mngr.parameter_tags_updated.connect(self.receive_parameter_tags_updated)
        self.db_mngr.parameter_definition_tags_set.connect(self.receive_parameter_definition_tags_set)
        # Removed
        self.db_mngr.object_classes_removed.connect(self.receive_object_classes_removed)
        self.db_mngr.objects_removed.connect(self.receive_objects_removed)
        self.db_mngr.relationship_classes_removed.connect(self.receive_relationship_classes_removed)
        self.db_mngr.relationships_removed.connect(self.receive_relationships_removed)
        self.db_mngr.parameter_definitions_removed.connect(self.receive_parameter_definitions_removed)
        self.db_mngr.parameter_values_removed.connect(self.receive_parameter_values_removed)
        self.db_mngr.parameter_value_lists_removed.connect(self.receive_parameter_value_lists_removed)
        self.db_mngr.parameter_tags_removed.connect(self.receive_parameter_tags_removed)
        # Commit, rollback, refresh
        self.db_mngr.session_refreshed.connect(self.receive_session_refreshed)
        self.db_mngr.session_committed.connect(self.receive_session_committed)
        self.db_mngr.session_rolled_back.connect(self.receive_session_rolled_back)

    @staticmethod
    def _shared_db_map_data(db_map_data, db_maps):
        return {db_map: data for db_map, data in db_map_data.items() if db_map in db_maps}

    @Slot(object)
    def receive_object_classes_added(self, db_map_data):
        for listener, db_maps in self.listeners.items():
            shared_db_map_data = self._shared_db_map_data(db_map_data, db_maps)
            if shared_db_map_data:
                listener.receive_object_classes_added(shared_db_map_data)

    @Slot(object)
    def receive_objects_added(self, db_map_data):
        for listener, db_maps in self.listeners.items():
            shared_db_map_data = self._shared_db_map_data(db_map_data, db_maps)
            if shared_db_map_data:
                listener.receive_objects_added(shared_db_map_data)

    @Slot(object)
    def receive_relationship_classes_added(self, db_map_data):
        for listener, db_maps in self.listeners.items():
            shared_db_map_data = self._shared_db_map_data(db_map_data, db_maps)
            if shared_db_map_data:
                listener.receive_relationship_classes_added(shared_db_map_data)

    @Slot(object)
    def receive_relationships_added(self, db_map_data):
        for listener, db_maps in self.listeners.items():
            shared_db_map_data = self._shared_db_map_data(db_map_data, db_maps)
            if shared_db_map_data:
                listener.receive_relationships_added(shared_db_map_data)

    @Slot(object)
    def receive_parameter_definitions_added(self, db_map_data):
        for listener, db_maps in self.listeners.items():
            shared_db_map_data = self._shared_db_map_data(db_map_data, db_maps)
            if shared_db_map_data:
                listener.receive_parameter_definitions_added(shared_db_map_data)

    @Slot(object)
    def receive_parameter_values_added(self, db_map_data):
        for listener, db_maps in self.listeners.items():
            shared_db_map_data = self._shared_db_map_data(db_map_data, db_maps)
            if shared_db_map_data:
                listener.receive_parameter_values_added(shared_db_map_data)

    @Slot(object)
    def receive_parameter_value_lists_added(self, db_map_data):
        for listener, db_maps in self.listeners.items():
            shared_db_map_data = self._shared_db_map_data(db_map_data, db_maps)
            if shared_db_map_data:
                listener.receive_parameter_value_lists_added(shared_db_map_data)

    @Slot(object)
    def receive_parameter_tags_added(self, db_map_data):
        for listener, db_maps in self.listeners.items():
            shared_db_map_data = self._shared_db_map_data(db_map_data, db_maps)
            if shared_db_map_data:
                listener.receive_parameter_tags_added(shared_db_map_data)

    @Slot(object)
    def receive_object_classes_updated(self, db_map_data):
        for listener, db_maps in self.listeners.items():
            shared_db_map_data = self._shared_db_map_data(db_map_data, db_maps)
            if shared_db_map_data:
                listener.receive_object_classes_updated(shared_db_map_data)

    @Slot(object)
    def receive_objects_updated(self, db_map_data):
        for listener, db_maps in self.listeners.items():
            shared_db_map_data = self._shared_db_map_data(db_map_data, db_maps)
            if shared_db_map_data:
                listener.receive_objects_updated(shared_db_map_data)

    @Slot(object)
    def receive_relationship_classes_updated(self, db_map_data):
        for listener, db_maps in self.listeners.items():
            shared_db_map_data = self._shared_db_map_data(db_map_data, db_maps)
            if shared_db_map_data:
                listener.receive_relationship_classes_updated(shared_db_map_data)

    @Slot(object)
    def receive_relationships_updated(self, db_map_data):
        for listener, db_maps in self.listeners.items():
            shared_db_map_data = self._shared_db_map_data(db_map_data, db_maps)
            if shared_db_map_data:
                listener.receive_relationships_updated(shared_db_map_data)

    @Slot(object)
    def receive_parameter_definitions_updated(self, db_map_data):
        for listener, db_maps in self.listeners.items():
            shared_db_map_data = self._shared_db_map_data(db_map_data, db_maps)
            if shared_db_map_data:
                listener.receive_parameter_definitions_updated(shared_db_map_data)

    @Slot(object)
    def receive_parameter_values_updated(self, db_map_data):
        for listener, db_maps in self.listeners.items():
            shared_db_map_data = self._shared_db_map_data(db_map_data, db_maps)
            if shared_db_map_data:
                listener.receive_parameter_values_updated(shared_db_map_data)

    @Slot(object)
    def receive_parameter_value_lists_updated(self, db_map_data):
        for listener, db_maps in self.listeners.items():
            shared_db_map_data = self._shared_db_map_data(db_map_data, db_maps)
            if shared_db_map_data:
                listener.receive_parameter_value_lists_updated(shared_db_map_data)

    @Slot(object)
    def receive_parameter_tags_updated(self, db_map_data):
        for listener, db_maps in self.listeners.items():
            shared_db_map_data = self._shared_db_map_data(db_map_data, db_maps)
            if shared_db_map_data:
                listener.receive_parameter_tags_updated(shared_db_map_data)

    @Slot(object)
    def receive_parameter_definition_tags_set(self, db_map_data):
        for listener, db_maps in self.listeners.items():
            shared_db_map_data = self._shared_db_map_data(db_map_data, db_maps)
            if shared_db_map_data:
                listener.receive_parameter_definition_tags_set(shared_db_map_data)

    @Slot(object)
    def receive_object_classes_removed(self, db_map_data):
        for listener, db_maps in self.listeners.items():
            shared_db_map_data = self._shared_db_map_data(db_map_data, db_maps)
            if shared_db_map_data:
                listener.receive_object_classes_removed(shared_db_map_data)

    @Slot(object)
    def receive_objects_removed(self, db_map_data):
        for listener, db_maps in self.listeners.items():
            shared_db_map_data = self._shared_db_map_data(db_map_data, db_maps)
            if shared_db_map_data:
                listener.receive_objects_removed(shared_db_map_data)

    @Slot(object)
    def receive_relationship_classes_removed(self, db_map_data):
        for listener, db_maps in self.listeners.items():
            shared_db_map_data = self._shared_db_map_data(db_map_data, db_maps)
            if shared_db_map_data:
                listener.receive_relationship_classes_removed(shared_db_map_data)

    @Slot(object)
    def receive_relationships_removed(self, db_map_data):
        for listener, db_maps in self.listeners.items():
            shared_db_map_data = self._shared_db_map_data(db_map_data, db_maps)
            if shared_db_map_data:
                listener.receive_relationships_removed(shared_db_map_data)

    @Slot(object)
    def receive_parameter_definitions_removed(self, db_map_data):
        for listener, db_maps in self.listeners.items():
            shared_db_map_data = self._shared_db_map_data(db_map_data, db_maps)
            if shared_db_map_data:
                listener.receive_parameter_definitions_removed(shared_db_map_data)

    @Slot(object)
    def receive_parameter_values_removed(self, db_map_data):
        for listener, db_maps in self.listeners.items():
            shared_db_map_data = self._shared_db_map_data(db_map_data, db_maps)
            if shared_db_map_data:
                listener.receive_parameter_values_removed(shared_db_map_data)

    @Slot(object)
    def receive_parameter_value_lists_removed(self, db_map_data):
        for listener, db_maps in self.listeners.items():
            shared_db_map_data = self._shared_db_map_data(db_map_data, db_maps)
            if shared_db_map_data:
                listener.receive_parameter_value_lists_removed(shared_db_map_data)

    @Slot(object)
    def receive_parameter_tags_removed(self, db_map_data):
        for listener, db_maps in self.listeners.items():
            shared_db_map_data = self._shared_db_map_data(db_map_data, db_maps)
            if shared_db_map_data:
                listener.receive_parameter_tags_removed(shared_db_map_data)

    @Slot(set)
    def receive_session_refreshed(self, db_maps):
        for listener, listener_db_maps in self.listeners.items():
            shared_db_maps = listener_db_maps.intersection(db_maps)
            if shared_db_maps:
                listener.receive_session_refreshed(shared_db_maps)

    @Slot(set)
    def receive_session_committed(self, db_maps):
        for listener, listener_db_maps in self.listeners.items():
            shared_db_maps = listener_db_maps.intersection(db_maps)
            if shared_db_maps:
                listener.receive_session_committed(shared_db_maps)

    @Slot(set)
    def receive_session_rolled_back(self, db_maps):
        for listener, listener_db_maps in self.listeners.items():
            shared_db_maps = listener_db_maps.intersection(db_maps)
            if shared_db_maps:
                listener.receive_session_rolled_back(shared_db_maps)
