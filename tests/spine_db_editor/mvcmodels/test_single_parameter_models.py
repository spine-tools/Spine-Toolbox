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
"""Unit tests for the ``single_parameter_model`` module."""
import unittest
from unittest.mock import MagicMock
from PySide6.QtWidgets import QApplication

from spinedb_api import to_database
from spinetoolbox.mvcmodels.shared import DB_MAP_ROLE
from spinetoolbox.spine_db_editor.mvcmodels.single_parameter_models import (
    SingleParameterModel,
    SingleObjectParameterValueModel,
)
from tests.mock_helpers import q_object, TestSpineDBManager

OBJECT_PARAMETER_VALUE_HEADER = [
    "object_class_name",
    "object_name",
    "parameter_name",
    "alternative_name",
    "value",
    "database",
]


class TestEmptySingleParameterModel(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not QApplication.instance():
            QApplication()

    def test_rowCount_is_zero(self):
        with q_object(SingleParameterModel(OBJECT_PARAMETER_VALUE_HEADER, None, None, None, False, False)) as model:
            self.assertEqual(model.rowCount(), 0)

    def test_columnCount_is_header_length(self):
        with q_object(SingleParameterModel(OBJECT_PARAMETER_VALUE_HEADER, None, None, None, False, False)) as model:
            self.assertEqual(model.columnCount(), len(OBJECT_PARAMETER_VALUE_HEADER))


class TestSingleObjectParameterValueModel(unittest.TestCase):
    OBJECT_PARAMETER_VALUE_HEADER = [
        "object_class_name",
        "object_name",
        "parameter_name",
        "alternative_name",
        "value",
        "database",
    ]

    @classmethod
    def setUpClass(cls):
        if not QApplication.instance():
            QApplication()

    def setUp(self):
        self._db_mngr = TestSpineDBManager(None, None)
        self._logger = MagicMock()
        self._db_map = self._db_mngr.get_db_map("sqlite:///", self._logger, codename="Test database", create=True)

    def tearDown(self):
        self._db_mngr.close_all_sessions()
        self._db_mngr.clean_up()
        self._db_mngr.deleteLater()

    def test_data_db_map_role(self):
        self._db_mngr.add_object_classes({self._db_map: [{"name": "my_class"}]})
        self._db_mngr.add_parameter_definitions({self._db_map: [{"entity_class_id": 1, "name": "my_parameter"}]})
        self._db_mngr.add_objects({self._db_map: [{"class_id": 1, "name": "my_object"}]})
        value, type_ = to_database(2.3)
        self._db_mngr.add_parameter_values(
            {
                self._db_map: [
                    {
                        "entity_class_id": 1,
                        "entity_id": 1,
                        "parameter_definition_id": 1,
                        "value": value,
                        "type": type_,
                        "alternative_id": 1,
                    }
                ]
            }
        )
        with q_object(
            SingleObjectParameterValueModel(OBJECT_PARAMETER_VALUE_HEADER, self._db_mngr, self._db_map, 1, True, False)
        ) as model:
            if model.canFetchMore(None):
                model.fetchMore(None)
            model.add_rows([1])
            self.assertEqual(model.index(0, 0).data(DB_MAP_ROLE), self._db_map)


if __name__ == '__main__':
    unittest.main()
