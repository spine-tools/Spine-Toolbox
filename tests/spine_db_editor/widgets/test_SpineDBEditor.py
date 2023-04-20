######################################################################################################################
# Copyright (C) 2017-2022 Spine project consortium
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""
Unit tests for SpineDBEditor classes.
"""

import unittest
from unittest import mock
from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import QModelIndex, QItemSelectionModel
import spinetoolbox.resources_icons_rc  # pylint: disable=unused-import
from spinetoolbox.spine_db_editor.widgets.spine_db_editor import SpineDBEditor
from spinetoolbox.spine_db_editor.mvcmodels.compound_parameter_models import CompoundParameterModel
from .test_SpineDBEditorAdd import TestSpineDBEditorAddMixin
from .test_SpineDBEditorUpdate import TestSpineDBEditorUpdateMixin
from .test_SpineDBEditorRemove import TestSpineDBEditorRemoveMixin
from .test_SpineDBEditorFilter import TestSpineDBEditorFilterMixin
from ...mock_helpers import TestSpineDBManager


class TestSpineDBEditor(
    TestSpineDBEditorAddMixin,
    TestSpineDBEditorUpdateMixin,
    TestSpineDBEditorRemoveMixin,
    TestSpineDBEditorFilterMixin,
    unittest.TestCase,
):
    @staticmethod
    def _object_class(*args):
        return dict(zip(["id", "name", "description", "display_order", "display_icon"], args))

    @staticmethod
    def _object(*args):
        return dict(zip(["id", "class_id", "class_name", "name", "description"], args))

    @staticmethod
    def _relationship_class(*args):
        return dict(zip(["id", "name", "object_class_id_list", "object_class_name_list", "display_icon"], args))

    @staticmethod
    def _relationship(*args):
        return dict(
            zip(
                [
                    "id",
                    "class_id",
                    "name",
                    "class_name",
                    "object_class_id_list",
                    "object_class_name_list",
                    "object_id_list",
                    "object_name_list",
                ],
                args,
            )
        )

    @staticmethod
    def _object_parameter_definition(*args):
        d = dict(zip(["id", "object_class_id", "object_class_name", "name"], args))
        d.update({"default_value": None, "default_type": None})
        return d

    @staticmethod
    def _relationship_parameter_definition(*args):
        d = dict(
            zip(
                [
                    "id",
                    "relationship_class_id",
                    "relationship_class_name",
                    "object_class_id_list",
                    "object_class_name_list",
                    "name",
                ],
                args,
            )
        )
        d.update({"default_value": None, "default_type": None})
        return d

    @staticmethod
    def _object_parameter_value(*args):
        d = dict(
            zip(
                [
                    "id",
                    "object_class_id",
                    "object_class_name",
                    "object_id",
                    "object_name",
                    "parameter_definition_id",
                    "parameter_name",
                    "alternative_id",
                    "value",
                    "type",
                ],
                args,
            )
        )
        d["entity_id"] = d["object_id"]
        return d

    @staticmethod
    def _relationship_parameter_value(*args):
        d = dict(
            zip(
                [
                    "id",
                    "relationship_class_id",
                    "relationship_class_name",
                    "object_class_id_list",
                    "object_class_name_list",
                    "relationship_id",
                    "object_id_list",
                    "object_name_list",
                    "parameter_definition_id",
                    "parameter_name",
                    "alternative_id",
                    "value",
                    "type",
                ],
                args,
            )
        )
        d["entity_id"] = d["relationship_id"]
        return d

    @classmethod
    def setUpClass(cls):
        """Overridden method. Runs once before all tests in this class."""
        if not QApplication.instance():
            QApplication()
        cls.create_mock_dataset()

    @classmethod
    def create_mock_dataset(cls):
        cls.fish_class = cls._object_class(1, "fish", "A fish.", 1, None)
        cls.dog_class = cls._object_class(2, "dog", "A dog.", 3, None)
        cls.fish_dog_class = cls._relationship_class(
            3,
            "fish__dog",
            [cls.fish_class["id"], cls.dog_class["id"]],
            [cls.fish_class["name"], cls.dog_class["name"]],
            None,
        )
        cls.dog_fish_class = cls._relationship_class(
            4,
            "dog__fish",
            [cls.dog_class["id"], cls.fish_class["id"]],
            [cls.dog_class["name"], cls.fish_class["name"]],
            None,
        )
        cls.nemo_object = cls._object(1, cls.fish_class["id"], cls.fish_class["name"], 'nemo', 'The lost one.')
        cls.pluto_object = cls._object(2, cls.dog_class["id"], cls.dog_class["name"], 'pluto', "Mickey's.")
        cls.scooby_object = cls._object(3, cls.dog_class["id"], cls.dog_class["name"], 'scooby', 'Scooby-Dooby-Doo.')
        cls.pluto_nemo_rel = cls._relationship(
            4,
            cls.dog_fish_class["id"],
            "dog__fish_pluto__nemo",
            cls.dog_fish_class["name"],
            [cls.dog_class["id"], cls.fish_class["id"]],
            [cls.dog_class["name"], cls.fish_class["name"]],
            [cls.pluto_object["id"], cls.nemo_object["id"]],
            [cls.pluto_object["name"], cls.nemo_object["name"]],
        )
        cls.nemo_pluto_rel = cls._relationship(
            5,
            cls.fish_dog_class["id"],
            "fish__dog_nemo__pluto",
            cls.fish_dog_class["name"],
            [cls.fish_class["id"], cls.dog_class["id"]],
            [cls.fish_class["name"], cls.dog_class["name"]],
            [cls.nemo_object["id"], cls.pluto_object["id"]],
            [cls.nemo_object["name"], cls.pluto_object["name"]],
        )
        cls.nemo_scooby_rel = cls._relationship(
            6,
            cls.fish_dog_class["id"],
            "fish__dog_nemo__scooby",
            cls.fish_dog_class["name"],
            [cls.fish_class["id"], cls.dog_class["id"]],
            [cls.fish_class["name"], cls.dog_class["name"]],
            [cls.nemo_object["id"], cls.scooby_object["id"]],
            [cls.nemo_object["name"], cls.scooby_object["name"]],
        )
        cls.water_parameter = cls._object_parameter_definition(1, cls.fish_class["id"], cls.fish_class["name"], "water")
        cls.breed_parameter = cls._object_parameter_definition(2, cls.dog_class["id"], cls.dog_class["name"], "breed")
        cls.relative_speed_parameter = cls._relationship_parameter_definition(
            3,
            cls.fish_dog_class["id"],
            cls.fish_dog_class["name"],
            cls.fish_dog_class["object_class_id_list"],
            cls.fish_dog_class["object_class_name_list"],
            "relative_speed",
        )
        cls.combined_mojo_parameter = cls._relationship_parameter_definition(
            4,
            cls.dog_fish_class["id"],
            cls.dog_fish_class["name"],
            cls.dog_fish_class["object_class_id_list"],
            cls.dog_fish_class["object_class_name_list"],
            "combined_mojo",
        )
        cls.nemo_water = cls._object_parameter_value(
            1,
            cls.water_parameter["object_class_id"],
            cls.water_parameter["object_class_name"],
            cls.nemo_object["id"],
            cls.nemo_object["name"],
            cls.water_parameter["id"],
            cls.water_parameter["name"],
            1,
            b'"salt"',
            None,
        )
        cls.pluto_breed = cls._object_parameter_value(
            2,
            cls.breed_parameter["object_class_id"],
            cls.breed_parameter["object_class_name"],
            cls.pluto_object["id"],
            cls.pluto_object["name"],
            cls.breed_parameter["id"],
            cls.breed_parameter["name"],
            1,
            b'"bloodhound"',
            None,
        )
        cls.scooby_breed = cls._object_parameter_value(
            3,
            cls.breed_parameter["object_class_id"],
            cls.breed_parameter["object_class_name"],
            cls.scooby_object["id"],
            cls.scooby_object["name"],
            cls.breed_parameter["id"],
            cls.breed_parameter["name"],
            1,
            b'"great dane"',
            None,
        )
        cls.nemo_pluto_relative_speed = cls._relationship_parameter_value(
            4,
            cls.relative_speed_parameter["relationship_class_id"],
            cls.relative_speed_parameter["relationship_class_name"],
            cls.relative_speed_parameter["object_class_id_list"],
            cls.relative_speed_parameter["object_class_name_list"],
            cls.nemo_pluto_rel["id"],
            cls.nemo_pluto_rel["object_id_list"],
            cls.nemo_pluto_rel["object_name_list"],
            cls.relative_speed_parameter["id"],
            cls.relative_speed_parameter["name"],
            1,
            b"-1",
            None,
        )
        cls.nemo_scooby_relative_speed = cls._relationship_parameter_value(
            5,
            cls.relative_speed_parameter["relationship_class_id"],
            cls.relative_speed_parameter["relationship_class_name"],
            cls.relative_speed_parameter["object_class_id_list"],
            cls.relative_speed_parameter["object_class_name_list"],
            cls.nemo_scooby_rel["id"],
            cls.nemo_scooby_rel["object_id_list"],
            cls.nemo_scooby_rel["object_name_list"],
            cls.relative_speed_parameter["id"],
            cls.relative_speed_parameter["name"],
            1,
            b"5",
            None,
        )
        cls.pluto_nemo_combined_mojo = cls._relationship_parameter_value(
            6,
            cls.combined_mojo_parameter["relationship_class_id"],
            cls.combined_mojo_parameter["relationship_class_name"],
            cls.combined_mojo_parameter["object_class_id_list"],
            cls.combined_mojo_parameter["object_class_name_list"],
            cls.pluto_nemo_rel["id"],
            cls.pluto_nemo_rel["object_id_list"],
            cls.pluto_nemo_rel["object_name_list"],
            cls.combined_mojo_parameter["id"],
            cls.combined_mojo_parameter["name"],
            1,
            b"100",
            None,
        )

    def setUp(self):
        """Overridden method. Runs before each test. Makes instances of SpineDBEditor classes."""
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

    def tearDown(self):
        """Overridden method. Runs after each test.
        Use this to free resources after a test if needed.
        """
        with mock.patch(
            "spinetoolbox.spine_db_editor.widgets.spine_db_editor.SpineDBEditor.save_window_state"
        ) as mock_save_w_s, mock.patch("spinetoolbox.spine_db_manager.QMessageBox"):
            self.spine_db_editor.close()
            mock_save_w_s.assert_called_once()
        self.db_mngr.close_all_sessions()
        while not self.mock_db_map.connection.closed:
            QApplication.processEvents()
        self.db_mngr.clean_up()
        self.spine_db_editor.deleteLater()
        self.spine_db_editor = None

    def put_mock_object_classes_in_db_mngr(self):
        """Put fish and dog object classes in the db mngr."""
        object_classes = [self.fish_class, self.dog_class]
        self.db_mngr.add_object_classes({self.mock_db_map: object_classes})
        self.fetch_object_tree_model()

    def put_mock_objects_in_db_mngr(self):
        """Put nemo, pluto and scooby objects in the db mngr."""
        objects = [self.nemo_object, self.pluto_object, self.scooby_object]
        self.db_mngr.add_objects({self.mock_db_map: objects})
        self.fetch_object_tree_model()

    def put_mock_relationship_classes_in_db_mngr(self):
        """Put dog__fish and fish__dog relationship classes in the db mngr."""
        relationship_classes = [self.fish_dog_class, self.dog_fish_class]
        self.db_mngr.add_relationship_classes({self.mock_db_map: relationship_classes})
        self.fetch_object_tree_model()

    def put_mock_relationships_in_db_mngr(self):
        """Put pluto_nemo, nemo_pluto and nemo_scooby relationships in the db mngr."""
        relationships = [self.pluto_nemo_rel, self.nemo_pluto_rel, self.nemo_scooby_rel]
        self.db_mngr.add_relationships({self.mock_db_map: relationships})
        self.fetch_object_tree_model()

    def put_mock_object_parameter_definitions_in_db_mngr(self):
        """Put water and breed object parameter definitions in the db mngr."""
        parameter_definitions = [self.water_parameter, self.breed_parameter]
        self.db_mngr.add_parameter_definitions({self.mock_db_map: parameter_definitions})

    def put_mock_relationship_parameter_definitions_in_db_mngr(self):
        """Put relative speed and combined mojo relationship parameter definitions in the db mngr."""
        parameter_definitions = [self.relative_speed_parameter, self.combined_mojo_parameter]
        self.db_mngr.add_parameter_definitions({self.mock_db_map: parameter_definitions})

    def put_mock_object_parameter_values_in_db_mngr(self):
        """Put some object parameter values in the db mngr."""
        parameter_values = [self.nemo_water, self.pluto_breed, self.scooby_breed]
        self.db_mngr.add_parameter_values({self.mock_db_map: parameter_values})

    def put_mock_relationship_parameter_values_in_db_mngr(self):
        """Put some relationship parameter values in the db mngr."""
        parameter_values = [
            self.nemo_pluto_relative_speed,
            self.nemo_scooby_relative_speed,
            self.pluto_nemo_combined_mojo,
        ]
        self.db_mngr.add_parameter_values({self.mock_db_map: parameter_values})

    def put_mock_dataset_in_db_mngr(self):
        """Put mock dataset in the db mngr."""
        self.put_mock_object_classes_in_db_mngr()
        self.put_mock_objects_in_db_mngr()
        self.put_mock_relationship_classes_in_db_mngr()
        self.put_mock_relationships_in_db_mngr()
        self.put_mock_object_parameter_definitions_in_db_mngr()
        self.put_mock_relationship_parameter_definitions_in_db_mngr()
        self.put_mock_object_parameter_values_in_db_mngr()
        self.put_mock_relationship_parameter_values_in_db_mngr()

    def fetch_object_tree_model(self):
        for item in self.spine_db_editor.object_tree_model.visit_all():
            if item.can_fetch_more():
                item.fetch_more()

    def test_set_object_parameter_definition_defaults(self):
        """Test that defaults are set in object parameter_definition models according the object tree selection."""
        self.spine_db_editor.init_models()
        self.put_mock_object_classes_in_db_mngr()
        self.fetch_object_tree_model()
        # Select fish item in object tree
        root_item = self.spine_db_editor.object_tree_model.root_item
        fish_item = root_item.child(1)
        fish_index = self.spine_db_editor.object_tree_model.index_from_item(fish_item)
        self.spine_db_editor.ui.treeView_object.setCurrentIndex(fish_index)
        self.spine_db_editor.ui.treeView_object.selectionModel().select(fish_index, QItemSelectionModel.Select)
        # Check default in object parameter_definition
        model = self.spine_db_editor.object_parameter_definition_model
        model.empty_model.fetchMore(QModelIndex())
        h = model.header.index
        row_data = []
        for row in range(model.rowCount()):
            row_data.append(tuple(model.index(row, h(field)).data() for field in ("object_class_name", "database")))
        self.assertIn(("fish", "database"), row_data)


class TestClosingDBEditors(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not QApplication.instance():
            QApplication()

    def setUp(self):
        self._editors = []
        with mock.patch("spinetoolbox.spine_db_editor.widgets.spine_db_editor.SpineDBEditor.restore_ui"), mock.patch(
            "spinetoolbox.spine_db_editor.widgets.spine_db_editor.SpineDBEditor.show"
        ):
            mock_settings = mock.Mock()
            mock_settings.value.side_effect = lambda *args, **kwargs: 0
            self._db_mngr = TestSpineDBManager(mock_settings, None)
            logger = mock.MagicMock()
            self._db_map = self._db_mngr.get_db_map("sqlite://", logger, codename="database", create=True)

    def tearDown(self):
        self._db_mngr.close_all_sessions()
        while not self._db_map.connection.closed:
            QApplication.processEvents()
        self._db_mngr.clean_up()
        for editor in self._editors:
            editor.deleteLater()

    def _make_db_editor(self):
        editor = SpineDBEditor(self._db_mngr, {"sqlite://": "database"})
        self._editors.append(editor)
        return editor

    def test_first_editor_to_close_does_not_ask_for_confirmation_on_dirty_database(self):
        editor_1 = self._make_db_editor()
        editor_2 = self._make_db_editor()
        self._db_mngr.add_object_classes({self._db_map: [{"name": "my_object_class"}]})
        self.assertTrue(self._db_mngr.dirty(self._db_map))
        with mock.patch(
            "spinetoolbox.spine_db_editor.widgets.spine_db_editor.SpineDBEditor.save_window_state"
        ), mock.patch("spinetoolbox.spine_db_manager.QMessageBox"), mock.patch(
            "spinetoolbox.spine_db_editor.widgets.spine_db_editor.SpineDBEditor._prompt_to_commit_changes"
        ) as commit_changes:
            commit_changes.return_value = QMessageBox.StandardButton.Discard
            editor_1.close()
            commit_changes.assert_not_called()
            editor_2.close()
            commit_changes.assert_called_once()

    def test_editor_asks_for_confirmation_even_when_non_editor_listeners_are_connected(self):
        editor = self._make_db_editor()
        self._db_mngr.add_object_classes({self._db_map: [{"name": "my_object_class"}]})
        self.assertTrue(self._db_mngr.dirty(self._db_map))
        non_editor_listener = object()
        self._db_mngr.register_listener(non_editor_listener, self._db_map)
        with mock.patch(
            "spinetoolbox.spine_db_editor.widgets.spine_db_editor.SpineDBEditor.save_window_state"
        ), mock.patch("spinetoolbox.spine_db_manager.QMessageBox"), mock.patch(
            "spinetoolbox.spine_db_editor.widgets.spine_db_editor.SpineDBEditor._prompt_to_commit_changes"
        ) as commit_changes:
            commit_changes.return_value = QMessageBox.StandardButton.Discard
            editor.close()
            commit_changes.assert_called_once()


if __name__ == '__main__':
    unittest.main()
