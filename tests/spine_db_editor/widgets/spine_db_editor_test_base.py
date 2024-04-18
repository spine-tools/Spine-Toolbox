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

"""Base classes and helpers for database editor tests."""
import unittest
from unittest import mock
from PySide6.QtWidgets import QApplication
from spinetoolbox.spine_db_editor.widgets.spine_db_editor import SpineDBEditor
from tests.mock_helpers import TestSpineDBManager


class DBEditorTestBase(unittest.TestCase):
    @staticmethod
    def _entity_class(*args):
        return dict(zip(["id", "name", "dimension_id_list"], args))

    @staticmethod
    def _entity(*args):
        return dict(zip(["id", "class_id", "name", "element_id_list"], args))

    @staticmethod
    def _parameter_definition(*args):
        d = dict(zip(["id", "entity_class_id", "name"], args))
        d.update({"default_value": None, "default_type": None})
        return d

    @staticmethod
    def _parameter_value(*args):
        return dict(
            zip(
                ["id", "entity_class_id", "entity_id", "parameter_definition_id", "alternative_id", "value", "type"],
                args,
            )
        )

    @classmethod
    def setUpClass(cls):
        if not QApplication.instance():
            QApplication()
        cls.create_mock_dataset()

    @classmethod
    def create_mock_dataset(cls):
        cls.fish_class = cls._entity_class(1, "fish")
        cls.dog_class = cls._entity_class(2, "dog")
        cls.fish_dog_class = cls._entity_class(3, "fish__dog", [cls.fish_class["id"], cls.dog_class["id"]])
        cls.dog_fish_class = cls._entity_class(4, "dog__fish", [cls.dog_class["id"], cls.fish_class["id"]])
        cls.nemo_object = cls._entity(1, cls.fish_class["id"], "nemo")
        cls.pluto_object = cls._entity(2, cls.dog_class["id"], "pluto")
        cls.scooby_object = cls._entity(3, cls.dog_class["id"], "scooby")
        cls.pluto_nemo_rel = cls._entity(
            4, cls.dog_fish_class["id"], "dog__fish_pluto__nemo", [cls.pluto_object["id"], cls.nemo_object["id"]]
        )
        cls.nemo_pluto_rel = cls._entity(
            5, cls.fish_dog_class["id"], "fish__dog_nemo__pluto", [cls.nemo_object["id"], cls.pluto_object["id"]]
        )
        cls.nemo_scooby_rel = cls._entity(
            6, cls.fish_dog_class["id"], "fish__dog_nemo__scooby", [cls.nemo_object["id"], cls.scooby_object["id"]]
        )
        cls.water_parameter = cls._parameter_definition(1, cls.fish_class["id"], "water")
        cls.breed_parameter = cls._parameter_definition(2, cls.dog_class["id"], "breed")
        cls.relative_speed_parameter = cls._parameter_definition(3, cls.fish_dog_class["id"], "relative_speed")
        cls.combined_mojo_parameter = cls._parameter_definition(4, cls.dog_fish_class["id"], "combined_mojo")
        cls.nemo_water = cls._parameter_value(
            1,
            cls.water_parameter["entity_class_id"],
            cls.nemo_object["id"],
            cls.water_parameter["id"],
            1,
            b'"salt"',
            None,
        )
        cls.pluto_breed = cls._parameter_value(
            2,
            cls.breed_parameter["entity_class_id"],
            cls.pluto_object["id"],
            cls.breed_parameter["id"],
            1,
            b'"bloodhound"',
            None,
        )
        cls.scooby_breed = cls._parameter_value(
            3,
            cls.breed_parameter["entity_class_id"],
            cls.scooby_object["id"],
            cls.breed_parameter["id"],
            1,
            b'"great dane"',
            None,
        )
        cls.nemo_pluto_relative_speed = cls._parameter_value(
            4,
            cls.relative_speed_parameter["entity_class_id"],
            cls.nemo_pluto_rel["id"],
            cls.relative_speed_parameter["id"],
            1,
            b"-1",
            None,
        )
        cls.nemo_scooby_relative_speed = cls._parameter_value(
            5,
            cls.relative_speed_parameter["entity_class_id"],
            cls.nemo_scooby_rel["id"],
            cls.relative_speed_parameter["id"],
            1,
            b"5",
            None,
        )
        cls.pluto_nemo_combined_mojo = cls._parameter_value(
            6,
            cls.combined_mojo_parameter["entity_class_id"],
            cls.pluto_nemo_rel["id"],
            cls.combined_mojo_parameter["id"],
            1,
            b"100",
            None,
        )

    def setUp(self):
        """Makes instances of SpineDBEditor classes."""
        with mock.patch("spinetoolbox.spine_db_editor.widgets.spine_db_editor.SpineDBEditor.restore_ui"), mock.patch(
            "spinetoolbox.spine_db_editor.widgets.spine_db_editor.SpineDBEditor.show"
        ):
            mock_settings = mock.Mock()
            mock_settings.value.side_effect = lambda *args, **kwargs: 0
            self.db_mngr = TestSpineDBManager(mock_settings, None)
            logger = mock.MagicMock()
            self.mock_db_map = self.db_mngr.get_db_map("sqlite://", logger, codename="database", create=True)
            self.spine_db_editor = SpineDBEditor(self.db_mngr, {"sqlite://": "database"})
            self.spine_db_editor.pivot_table_model = mock.MagicMock()
            self.spine_db_editor.entity_tree_model.hide_empty_classes = False

    def tearDown(self):
        with mock.patch(
            "spinetoolbox.spine_db_editor.widgets.spine_db_editor.SpineDBEditor.save_window_state"
        ) as mock_save_w_s, mock.patch("spinetoolbox.spine_db_manager.QMessageBox"):
            self.spine_db_editor.close()
            mock_save_w_s.assert_called_once()
        self.db_mngr.close_all_sessions()
        while not self.mock_db_map.closed:
            QApplication.processEvents()
        self.db_mngr.clean_up()
        self.spine_db_editor.deleteLater()
        self.spine_db_editor = None

    def put_mock_object_classes_in_db_mngr(self):
        """Puts fish and dog object classes in the db mngr."""
        object_classes = [self.fish_class, self.dog_class]
        self.db_mngr.add_entity_classes({self.mock_db_map: object_classes})
        self.fetch_object_tree_model()

    def put_mock_objects_in_db_mngr(self):
        """Puts nemo, pluto and scooby objects in the db mngr."""
        objects = [self.nemo_object, self.pluto_object, self.scooby_object]
        self.db_mngr.add_entities({self.mock_db_map: objects})
        self.fetch_object_tree_model()

    def put_mock_relationship_classes_in_db_mngr(self):
        """Puts dog__fish and fish__dog relationship classes in the db mngr."""
        relationship_classes = [self.fish_dog_class, self.dog_fish_class]
        self.db_mngr.add_entity_classes({self.mock_db_map: relationship_classes})
        self.fetch_object_tree_model()

    def put_mock_relationships_in_db_mngr(self):
        """Puts pluto_nemo, nemo_pluto and nemo_scooby relationships in the db mngr."""
        relationships = [self.pluto_nemo_rel, self.nemo_pluto_rel, self.nemo_scooby_rel]
        self.db_mngr.add_entities({self.mock_db_map: relationships})
        self.fetch_object_tree_model()

    def put_mock_object_parameter_definitions_in_db_mngr(self):
        """Puts water and breed object parameter definitions in the db mngr."""
        parameter_definitions = [self.water_parameter, self.breed_parameter]
        self.db_mngr.add_parameter_definitions({self.mock_db_map: parameter_definitions})

    def put_mock_relationship_parameter_definitions_in_db_mngr(self):
        """Puts relative speed and combined mojo relationship parameter definitions in the db mngr."""
        parameter_definitions = [self.relative_speed_parameter, self.combined_mojo_parameter]
        self.db_mngr.add_parameter_definitions({self.mock_db_map: parameter_definitions})

    def put_mock_object_parameter_values_in_db_mngr(self):
        """Puts some object parameter values in the db mngr."""
        parameter_values = [self.nemo_water, self.pluto_breed, self.scooby_breed]
        self.db_mngr.add_parameter_values({self.mock_db_map: parameter_values})

    def put_mock_relationship_parameter_values_in_db_mngr(self):
        """Puts some relationship parameter values in the db mngr."""
        parameter_values = [
            self.nemo_pluto_relative_speed,
            self.nemo_scooby_relative_speed,
            self.pluto_nemo_combined_mojo,
        ]
        self.db_mngr.add_parameter_values({self.mock_db_map: parameter_values})

    def put_mock_dataset_in_db_mngr(self):
        """Puts mock dataset in the db mngr."""
        self.put_mock_object_classes_in_db_mngr()
        self.put_mock_objects_in_db_mngr()
        self.put_mock_relationship_classes_in_db_mngr()
        self.put_mock_relationships_in_db_mngr()
        self.put_mock_object_parameter_definitions_in_db_mngr()
        self.put_mock_relationship_parameter_definitions_in_db_mngr()
        self.put_mock_object_parameter_values_in_db_mngr()
        self.put_mock_relationship_parameter_values_in_db_mngr()

    def fetch_object_tree_model(self):
        for item in self.spine_db_editor.entity_tree_model.visit_all():
            while item.can_fetch_more():
                item.fetch_more()
                qApp.processEvents()
