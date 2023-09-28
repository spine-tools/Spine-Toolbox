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
Unit tests for the models in ``compound_parameter_models`` module.
"""
import unittest
from unittest.mock import MagicMock, patch
from PySide6.QtWidgets import QApplication
from spinetoolbox.spine_db_editor.mvcmodels.compound_models import (
    CompoundParameterDefinitionModel,
    CompoundParameterValueModel,
)
from spinetoolbox.spine_db_editor.widgets.spine_db_editor import SpineDBEditor
from tests.mock_helpers import TestSpineDBManager, fetch_model


class TestCompoundObjectParameterDefinitionModel(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not QApplication.instance():
            QApplication()

    def setUp(self):
        app_settings = MagicMock()
        logger = MagicMock()
        self._db_mngr = TestSpineDBManager(app_settings, None)
        self._db_map = self._db_mngr.get_db_map("sqlite://", logger, codename="test_db", create=True)
        with patch("spinetoolbox.spine_db_editor.widgets.spine_db_editor.SpineDBEditor.restore_ui"):
            self._db_editor = SpineDBEditor(self._db_mngr, {"sqlite://": "test_db"})

    def tearDown(self):
        with patch("spinetoolbox.spine_db_editor.widgets.spine_db_editor.SpineDBEditor.save_window_state"), patch(
            "spinetoolbox.spine_db_editor.widgets.spine_db_editor.QMessageBox"
        ):
            self._db_editor.close()
        self._db_mngr.close_all_sessions()
        while not self._db_map.closed:
            QApplication.processEvents()
        self._db_mngr.clean_up()
        self._db_editor.deleteLater()

    def test_horizontal_header(self):
        model = CompoundParameterDefinitionModel(self._db_editor, self._db_mngr, self._db_map)
        model.init_model()
        expected_header = [
            "entity_class_name",
            "parameter_name",
            "value_list_name",
            "default_value",
            "description",
            "database",
        ]
        header = [model.headerData(i) for i in range(model.columnCount())]
        self.assertEqual(header, expected_header)

    def test_data_for_single_parameter_definition(self):
        model = CompoundParameterDefinitionModel(self._db_editor, self._db_mngr, self._db_map)
        model.init_model()
        fetch_model(model)
        self._db_mngr.add_entity_classes({self._db_map: [{"name": "oc", "id": 1}]})
        self._db_mngr.add_parameter_definitions({self._db_map: [{"name": "p", "entity_class_id": 1, "id": 1}]})
        self.assertEqual(model.rowCount(), 2)
        self.assertEqual(model.columnCount(), 6)
        row = [model.index(0, column).data() for column in range(model.columnCount())]
        expected = ["oc", "p", None, "None", None, "test_db"]
        self.assertEqual(row, expected)


class TestCompoundRelationshipParameterDefinitionModel(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not QApplication.instance():
            QApplication()

    def setUp(self):
        app_settings = MagicMock()
        logger = MagicMock()
        self._db_mngr = TestSpineDBManager(app_settings, None)
        self._db_map = self._db_mngr.get_db_map("sqlite://", logger, codename="test_db", create=True)
        with patch("spinetoolbox.spine_db_editor.widgets.spine_db_editor.SpineDBEditor.restore_ui"):
            self._db_editor = SpineDBEditor(self._db_mngr, {"sqlite://": "test_db"})

    def tearDown(self):
        with patch("spinetoolbox.spine_db_editor.widgets.spine_db_editor.SpineDBEditor.save_window_state"), patch(
            "spinetoolbox.spine_db_editor.widgets.spine_db_editor.QMessageBox"
        ):
            self._db_editor.close()
        self._db_mngr.close_all_sessions()
        while not self._db_map.closed:
            QApplication.processEvents()
        self._db_mngr.clean_up()
        self._db_editor.deleteLater()

    def test_horizontal_header(self):
        model = CompoundParameterDefinitionModel(self._db_editor, self._db_mngr, self._db_map)
        model.init_model()
        expected_header = [
            "entity_class_name",
            "parameter_name",
            "value_list_name",
            "default_value",
            "description",
            "database",
        ]
        header = [model.headerData(i) for i in range(model.columnCount())]
        self.assertEqual(header, expected_header)

    def test_data_for_single_parameter_definition(self):
        model = CompoundParameterDefinitionModel(self._db_editor, self._db_mngr, self._db_map)
        model.init_model()
        fetch_model(model)
        self._db_mngr.add_entity_classes({self._db_map: [{"name": "oc", "id": 1}]})
        self._db_mngr.add_entity_classes({self._db_map: [{"name": "rc", "dimension_id_list": [1], "id": 2}]})
        self._db_mngr.add_parameter_definitions({self._db_map: [{"name": "p", "entity_class_id": 2, "id": 1}]})
        self._db_map.fetch_all()
        self.assertEqual(model.rowCount(), 2)
        self.assertEqual(model.columnCount(), 6)
        row = [model.index(0, column).data() for column in range(model.columnCount())]
        expected = ["rc", "p", None, "None", None, "test_db"]
        self.assertEqual(row, expected)


class TestCompoundObjectParameterValueModel(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not QApplication.instance():
            QApplication()

    def setUp(self):
        app_settings = MagicMock()
        logger = MagicMock()
        self._db_mngr = TestSpineDBManager(app_settings, None)
        self._db_map = self._db_mngr.get_db_map("sqlite://", logger, codename="test_db", create=True)
        self._db_map.fetch_all()
        with patch("spinetoolbox.spine_db_editor.widgets.spine_db_editor.SpineDBEditor.restore_ui"):
            self._db_editor = SpineDBEditor(self._db_mngr, {"sqlite://": "test_db"})

    def tearDown(self):
        with patch("spinetoolbox.spine_db_editor.widgets.spine_db_editor.SpineDBEditor.save_window_state"), patch(
            "spinetoolbox.spine_db_editor.widgets.spine_db_editor.QMessageBox"
        ):
            self._db_editor.close()
        self._db_mngr.close_all_sessions()
        while not self._db_map.closed:
            QApplication.processEvents()
        self._db_mngr.clean_up()
        self._db_editor.deleteLater()

    def test_horizontal_header(self):
        model = CompoundParameterValueModel(self._db_editor, self._db_mngr, self._db_map)
        model.init_model()
        expected_header = [
            "entity_class_name",
            "entity_byname",
            "parameter_name",
            "alternative_name",
            "value",
            "database",
        ]
        header = [model.headerData(i) for i in range(model.columnCount())]
        self.assertEqual(header, expected_header)

    def test_data_for_single_parameter(self):
        model = CompoundParameterValueModel(self._db_editor, self._db_mngr, self._db_map)
        model.init_model()
        fetch_model(model)
        self._db_mngr.add_entity_classes({self._db_map: [{"name": "oc", "id": 1}]})
        self._db_mngr.add_parameter_definitions({self._db_map: [{"name": "p", "entity_class_id": 1, "id": 1}]})
        self._db_mngr.add_entities({self._db_map: [{"name": "o", "class_id": 1, "id": 1}]})
        self._db_mngr.add_parameter_values(
            {
                self._db_map: [
                    {
                        "parameter_definition_id": 1,
                        "value": b"23.0",
                        "type": None,
                        "entity_id": 1,
                        "entity_class_id": 1,
                        "alternative_id": 1,
                        "id": 1,
                    }
                ]
            }
        )
        self.assertEqual(model.rowCount(), 2)
        self.assertEqual(model.columnCount(), 6)
        row = [model.index(0, column).data() for column in range(model.columnCount())]
        expected = ["oc", "o", "p", "Base", "23.0", "test_db"]
        self.assertEqual(row, expected)


class TestCompoundRelationshipParameterValueModel(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not QApplication.instance():
            QApplication()

    def setUp(self):
        app_settings = MagicMock()
        logger = MagicMock()
        self._db_mngr = TestSpineDBManager(app_settings, None)
        self._db_map = self._db_mngr.get_db_map("sqlite://", logger, codename="test_db", create=True)
        self._db_map.fetch_all()
        with patch("spinetoolbox.spine_db_editor.widgets.spine_db_editor.SpineDBEditor.restore_ui"):
            self._db_editor = SpineDBEditor(self._db_mngr, {"sqlite://": "test_db"})

    def tearDown(self):
        with patch("spinetoolbox.spine_db_editor.widgets.spine_db_editor.SpineDBEditor.save_window_state"), patch(
            "spinetoolbox.spine_db_editor.widgets.spine_db_editor.QMessageBox"
        ):
            self._db_editor.close()
        self._db_mngr.close_all_sessions()
        while not self._db_map.closed:
            QApplication.processEvents()
        self._db_mngr.clean_up()
        self._db_editor.deleteLater()

    def test_horizontal_header(self):
        model = CompoundParameterValueModel(self._db_editor, self._db_mngr, self._db_map)
        model.init_model()
        expected_header = [
            "entity_class_name",
            "entity_byname",
            "parameter_name",
            "alternative_name",
            "value",
            "database",
        ]
        header = [model.headerData(i) for i in range(model.columnCount())]
        self.assertEqual(header, expected_header)

    def test_data_for_single_parameter(self):
        model = CompoundParameterValueModel(self._db_editor, self._db_mngr, self._db_map)
        model.init_model()
        fetch_model(model)
        self._db_mngr.add_entity_classes({self._db_map: [{"name": "oc", "id": 1}]})
        self._db_mngr.add_entities({self._db_map: [{"name": "o", "class_id": 1, "id": 1}]})
        self._db_mngr.add_entity_classes({self._db_map: [{"name": "rc", "dimension_id_list": [1], "id": 2}]})
        self._db_mngr.add_parameter_definitions({self._db_map: [{"name": "p", "entity_class_id": 2, "id": 1}]})
        self._db_mngr.add_entities({self._db_map: [{"name": "r", "class_id": 2, "element_id_list": [1], "id": 2}]})
        self._db_mngr.add_parameter_values(
            {
                self._db_map: [
                    {
                        "parameter_definition_id": 1,
                        "value": b"23.0",
                        "type": None,
                        "entity_id": 2,
                        "entity_class_id": 2,
                        "alternative_id": 1,
                        "id": 1,
                    }
                ]
            }
        )
        self.assertEqual(model.rowCount(), 2)
        self.assertEqual(model.columnCount(), 6)
        row = [model.index(0, column).data() for column in range(model.columnCount())]
        expected = ["rc", "o", "p", "Base", "23.0", "test_db"]
        self.assertEqual(row, expected)


if __name__ == '__main__':
    unittest.main()
