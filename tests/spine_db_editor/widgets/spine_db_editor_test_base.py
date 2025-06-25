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
from unittest import mock
from PySide6.QtWidgets import QApplication
from spinedb_api import to_database
from spinetoolbox.spine_db_editor.widgets.spine_db_editor import SpineDBEditor
from tests.mock_helpers import TestCaseWithQApplication, MockSpineDBManager


class DBEditorTestBase(TestCaseWithQApplication):
    db_codename = "database"

    def setUp(self):
        """Makes instances of SpineDBEditor classes."""
        with (
            mock.patch("spinetoolbox.spine_db_editor.widgets.spine_db_editor.SpineDBEditor.restore_ui"),
            mock.patch("spinetoolbox.spine_db_editor.widgets.spine_db_editor.SpineDBEditor.show"),
        ):
            mock_settings = mock.Mock()
            mock_settings.value.side_effect = lambda *args, **kwargs: 0
            self.db_mngr = MockSpineDBManager(mock_settings, None)
            logger = mock.MagicMock()
            self.mock_db_map = self.db_mngr.get_db_map("sqlite://", logger, create=True)
            self.db_mngr.name_registry.register("sqlite://", self.db_codename)
            self.spine_db_editor = SpineDBEditor(self.db_mngr, {"sqlite://": self.db_codename})
            self.spine_db_editor.pivot_table_model = mock.MagicMock()
            self.spine_db_editor.entity_tree_model.hide_empty_classes = False

    def tearDown(self):
        with (
            mock.patch(
                "spinetoolbox.spine_db_editor.widgets.spine_db_editor.SpineDBEditor.save_window_state"
            ) as mock_save_w_s,
            mock.patch("spinetoolbox.spine_db_manager.QMessageBox"),
        ):
            self.spine_db_editor.close()
            mock_save_w_s.assert_called_once()
        self.db_mngr.close_all_sessions()
        while not self.mock_db_map.closed:
            QApplication.processEvents()
        self.db_mngr.clean_up()
        self.spine_db_editor.deleteLater()
        self.spine_db_editor = None

    def _assert_success(self, result):
        item, error = result
        self.assertIsNone(error)
        return item

    def put_mock_object_classes_in_db_mngr(self):
        """Puts fish and dog object classes in the db mngr."""
        self.fish_class = self._assert_success(self.mock_db_map.add_entity_class_item(name="fish"))
        self.dog_class = self._assert_success(self.mock_db_map.add_entity_class_item(name="dog"))

    def put_mock_objects_in_db_mngr(self):
        """Puts nemo, pluto and scooby objects in the db mngr."""
        self.nemo_object = self._assert_success(
            self.mock_db_map.add_entity_item(entity_class_name=self.fish_class["name"], name="nemo")
        )
        self.pluto_object = self._assert_success(
            self.mock_db_map.add_entity_item(entity_class_name=self.dog_class["name"], name="pluto")
        )
        self.scooby_object = self._assert_success(
            self.mock_db_map.add_entity_item(entity_class_name=self.dog_class["name"], name="scooby")
        )

    def put_mock_relationship_classes_in_db_mngr(self):
        """Puts dog__fish and fish__dog relationship classes in the db mngr."""
        self.fish_dog_class = self._assert_success(
            self.mock_db_map.add_entity_class_item(
                dimension_name_list=(self.fish_class["name"], self.dog_class["name"])
            )
        )
        self.dog_fish_class = self._assert_success(
            self.mock_db_map.add_entity_class_item(
                dimension_name_list=(self.dog_class["name"], self.fish_class["name"])
            )
        )

    def put_mock_relationships_in_db_mngr(self):
        """Puts pluto_nemo, nemo_pluto and nemo_scooby relationships in the db mngr."""
        self.pluto_nemo_rel = self._assert_success(
            self.mock_db_map.add_entity_item(
                entity_class_name=self.dog_fish_class["name"],
                entity_byname=(self.pluto_object["name"], self.nemo_object["name"]),
            )
        )
        self.nemo_pluto_rel = self._assert_success(
            self.mock_db_map.add_entity_item(
                entity_class_name=self.fish_dog_class["name"],
                entity_byname=(self.nemo_object["name"], self.pluto_object["name"]),
            )
        )
        self.nemo_scooby_rel = self._assert_success(
            self.mock_db_map.add_entity_item(
                entity_class_name=self.fish_dog_class["name"],
                entity_byname=(self.nemo_object["name"], self.scooby_object["name"]),
            )
        )

    def put_mock_object_parameter_definitions_in_db_mngr(self):
        """Puts water and breed object parameter definitions in the db mngr."""
        self.water_parameter = self._assert_success(
            self.mock_db_map.add_parameter_definition_item(entity_class_name=self.fish_class["name"], name="water")
        )
        self.breed_parameter = self._assert_success(
            self.mock_db_map.add_parameter_definition_item(entity_class_name=self.dog_class["name"], name="breed")
        )

    def put_mock_relationship_parameter_definitions_in_db_mngr(self):
        """Puts relative speed and combined mojo relationship parameter definitions in the db mngr."""
        self.relative_speed_parameter = self._assert_success(
            self.mock_db_map.add_parameter_definition_item(
                entity_class_name=self.fish_dog_class["name"], name="relative_speed"
            )
        )
        self.combined_mojo_parameter = self._assert_success(
            self.mock_db_map.add_parameter_definition_item(
                entity_class_name=self.dog_fish_class["name"], name="combined_mojo"
            )
        )

    def put_mock_object_parameter_values_in_db_mngr(self):
        """Puts some object parameter values in the db mngr."""
        value, type_ = to_database("salt")
        self.nemo_water = self._assert_success(
            self.mock_db_map.add_parameter_value_item(
                entity_class_name=self.fish_class["name"],
                entity_byname=(self.nemo_object["name"],),
                parameter_definition_name=self.water_parameter["name"],
                alternative_name="Base",
                value=value,
                type=type_,
            )
        )
        value, type_ = to_database("bloodhound")
        self.pluto_breed = self._assert_success(
            self.mock_db_map.add_parameter_value_item(
                entity_class_name=self.dog_class["name"],
                entity_byname=(self.pluto_object["name"],),
                parameter_definition_name=self.breed_parameter["name"],
                alternative_name="Base",
                value=value,
                type=type_,
            )
        )
        value, type_ = to_database("great dane")
        self.scooby_breed = self._assert_success(
            self.mock_db_map.add_parameter_value_item(
                entity_class_name=self.dog_class["name"],
                entity_byname=(self.scooby_object["name"],),
                parameter_definition_name=self.breed_parameter["name"],
                alternative_name="Base",
                value=value,
                type=type_,
            )
        )

    def put_mock_relationship_parameter_values_in_db_mngr(self):
        """Puts some relationship parameter values in the db mngr."""
        value, type_ = to_database(-1)
        self.nemo_pluto_relative_speed = self._assert_success(
            self.mock_db_map.add_parameter_value_item(
                entity_class_name=self.fish_dog_class["name"],
                entity_byname=(self.nemo_object["name"], self.pluto_object["name"]),
                parameter_definition_name=self.relative_speed_parameter["name"],
                alternative_name="Base",
                value=value,
                type=type_,
            )
        )
        value, type_ = to_database(5)
        self.nemo_scooby_relative_speed = self._assert_success(
            self.mock_db_map.add_parameter_value_item(
                entity_class_name=self.fish_dog_class["name"],
                entity_byname=(self.nemo_object["name"], self.scooby_object["name"]),
                parameter_definition_name=self.relative_speed_parameter["name"],
                alternative_name="Base",
                value=value,
                type=type_,
            )
        )
        value, type_ = to_database(100)
        self.pluto_nemo_combined_mojo = self._assert_success(
            self.mock_db_map.add_parameter_value_item(
                entity_class_name=self.dog_fish_class["name"],
                entity_byname=(self.pluto_object["name"], self.nemo_object["name"]),
                parameter_definition_name=self.combined_mojo_parameter["name"],
                alternative_name="Base",
                value=value,
                type=type_,
            )
        )

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

    def fetch_entity_tree_model(self):
        for item in self.spine_db_editor.entity_tree_model.visit_all():
            while item.can_fetch_more():
                item.fetch_more()
                qApp.processEvents()  # pylint: disable=undefined-variable
