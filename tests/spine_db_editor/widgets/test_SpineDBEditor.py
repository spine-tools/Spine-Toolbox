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

"""Unit tests for SpineDBEditor classes."""
import pathlib
import unittest
from unittest import mock
from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import QModelIndex, QItemSelectionModel

from spinedb_api import Duration
from spinedb_api.helpers import name_from_elements
from spinetoolbox.spine_db_editor.widgets.spine_db_editor import SpineDBEditor
from .spine_db_editor_test_base import DBEditorTestBase
from tests.mock_helpers import TestSpineDBManager


class TestSpineDBEditor(DBEditorTestBase):
    def test_set_object_parameter_definition_defaults(self):
        """Test that defaults are set in object parameter_definition models according the object tree selection."""
        self.spine_db_editor.init_models()
        self.put_mock_object_classes_in_db_mngr()
        self.fetch_entity_tree_model()
        # Select fish item in object tree
        root_item = self.spine_db_editor.entity_tree_model.root_item
        fish_item = root_item.child(1)
        fish_index = self.spine_db_editor.entity_tree_model.index_from_item(fish_item)
        self.spine_db_editor.ui.treeView_entity.setCurrentIndex(fish_index)
        self.spine_db_editor.ui.treeView_entity.selectionModel().select(fish_index, QItemSelectionModel.Select)
        # Check default in object parameter_definition
        model = self.spine_db_editor.parameter_definition_model
        model.empty_model.fetchMore(QModelIndex())
        h = model.header.index
        row_data = []
        for row in range(model.rowCount()):
            row_data.append(tuple(model.index(row, h(field)).data() for field in ("entity_class_name", "database")))
        self.assertIn(("fish", "database"), row_data)

    def test_save_window_state(self):
        self.spine_db_editor.db_maps = [self.mock_db_map]
        self.spine_db_editor.db_urls = [""]
        self.spine_db_editor.save_window_state()
        self.spine_db_editor.qsettings.beginGroup.assert_has_calls([mock.call("spineDBEditor"), mock.call("")])
        self.spine_db_editor.qsettings.endGroup.assert_has_calls([mock.call(), mock.call()])
        qsettings_save_calls = self.spine_db_editor.qsettings.setValue.call_args_list
        self.assertEqual(len(qsettings_save_calls), 2)
        saved_dict = {saved[0][0]: saved[0][1] for saved in qsettings_save_calls}
        self.assertIn("windowState", saved_dict)
        self.assertIn("last_open", saved_dict)

    def test_open_element_name_list_editor(self):
        self.spine_db_editor.init_models()
        self.put_mock_dataset_in_db_mngr()
        self.fetch_entity_tree_model()
        entity_model = self.spine_db_editor.entity_tree_model
        entity_tree_root = entity_model.index(0, 0)
        class_index = entity_model.index(3, 0, entity_tree_root)
        self.assertEqual(class_index.data(), "fish__dog")
        self.spine_db_editor.ui.treeView_entity.setCurrentIndex(class_index)
        while self.spine_db_editor.parameter_value_model.rowCount() != 3:
            QApplication.processEvents()
        model = self.spine_db_editor.parameter_value_model
        index = model.index(0, 1)
        with mock.patch(
            "spinetoolbox.spine_db_editor.widgets.stacked_view_mixin.ElementNameListEditor"
        ) as editor_constructor:
            editor = mock.MagicMock()
            editor_constructor.return_value = editor
            self.spine_db_editor.show_element_name_list_editor(index, self.fish_dog_class["id"], self.mock_db_map)
            editor_constructor.assert_called_with(
                self.spine_db_editor,
                index,
                ["fish", "dog"],
                [[("nemo",)], [("pluto",), ("scooby",)]],
                (("nemo",), ("pluto",)),
            )
            editor.show.assert_called_once()

    def test_import_spineopt_basic_model_template(self):
        self.spine_db_editor.init_models()
        resource_path = pathlib.Path(__file__).parent.parent.parent / "test_resources"
        template_path = resource_path / "spineopt_template.json"
        self.spine_db_editor.import_from_json(str(template_path))
        model_path = resource_path / "basic_model_template.json"
        self.spine_db_editor.import_from_json(str(model_path))
        expected_entities = {
            "model": {"simple"},
            "report": {"report1"},
            "stochastic_scenario": {"realization"},
            "stochastic_structure": {"deterministic"},
            "temporal_block": {"flat"},
            "model__default_stochastic_structure": {name_from_elements(("simple", "deterministic"))},
            "model__default_temporal_block": {name_from_elements(("simple", "flat"))},
            "model__report": {name_from_elements(("simple", "report1"))},
            "stochastic_structure__stochastic_scenario": {name_from_elements(("deterministic", "realization"))},
        }
        for class_name, expected_names in expected_entities.items():
            with self.subTest(entity_class=class_name):
                entities = self.mock_db_map.get_entity_items(entity_class_name=class_name)
                self.assertEqual(len(entities), len(expected_names))
                names = {entity["name"] for entity in entities}
                self.assertEqual(names, expected_names)
        expected_parameter_values = {("temporal_block", "flat", "resolution", "Base"): Duration("1D")}
        for unique_id, expected_value in expected_parameter_values.items():
            class_name, entity_name, definition_name, alternative_name = unique_id
            with self.subTest(
                entity_class=class_name, entity=entity_name, parameter=definition_name, alternative=alternative_name
            ):
                value = self.mock_db_map.get_parameter_value_item(
                    entity_class_name=class_name,
                    entity_byname=(entity_name,),
                    parameter_definition_name=definition_name,
                    alternative_name=alternative_name,
                )
                self.assertEqual(value["parsed_value"], expected_value)


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
        while not self._db_map.closed:
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
        self._db_mngr.add_entity_classes({self._db_map: [{"name": "my_object_class"}]})
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
        self._db_mngr.add_entity_classes({self._db_map: [{"name": "my_object_class"}]})
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


if __name__ == "__main__":
    unittest.main()
