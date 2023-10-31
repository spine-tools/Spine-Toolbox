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
"""Unit tests for Pivot and Frozen tables."""
import unittest
from unittest.mock import MagicMock, patch
from PySide6.QtWidgets import QApplication
from spinetoolbox.spine_db_editor.widgets.spine_db_editor import SpineDBEditor
from tests.mock_helpers import TestSpineDBManager, fetch_model


class TestPivotHeaderDraggingAndDropping(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not QApplication.instance():
            QApplication()

    def setUp(self):
        app_settings = MagicMock()
        logger = MagicMock()
        self._db_mngr = TestSpineDBManager(app_settings, None)
        self._db_map = self._db_mngr.get_db_map("sqlite://", logger, codename="test_db", create=True)
        with patch.object(SpineDBEditor, "restore_ui"):
            self._editor = SpineDBEditor(self._db_mngr, {"sqlite://": self._db_map.codename})

    def tearDown(self):
        self._db_mngr.close_all_sessions()
        self._db_mngr.clean_up()

    def _add_entity_class_data(self):
        data = {
            "entity_classes": (("class1",),),
            "parameter_definitions": (("class1", "parameter1"), ("class1", "parameter2")),
            "entities": (("class1", "object1"), ("class1", "object2")),
            "parameter_values": (
                ("class1", "object1", "parameter1", 1.0),
                ("class1", "object2", "parameter1", 3.0),
                ("class1", "object1", "parameter2", 5.0),
                ("class1", "object2", "parameter2", 7.0),
            ),
        }
        self._db_mngr.import_data({self._db_map: data})

    def _start(self):
        get_item_exceptions = []

        def guarded_get_item(db_map, item_type, id_):
            try:
                return db_map.get_item(item_type, id=id_)
            except Exception as error:
                get_item_exceptions.append(error)
                return None

        with patch.object(self._db_mngr, "get_item") as get_item:
            get_item.side_effect = guarded_get_item
            object_class_index = self._editor.entity_tree_model.index(0, 0)
            fetch_model(self._editor.entity_tree_model)
            index = self._editor.entity_tree_model.index(0, 0, object_class_index)
            self._editor._update_class_attributes(index)
            with patch.object(self._editor.ui.dockWidget_pivot_table, "isVisible") as mock_is_visible:
                mock_is_visible.return_value = True
                self._editor.do_reload_pivot_table()
            self._model = self._editor.pivot_table_model
            self._model.beginResetModel()
            self._model.endResetModel()
            QApplication.processEvents()
            self.assertEqual(get_item_exceptions, [])

    def test_drag_and_drop_database_from_frozen_table(self):
        self._add_entity_class_data()
        self._start()
        for frozen_column in range(self._editor.frozen_table_model.columnCount()):
            frozen_index = self._editor.frozen_table_model.index(0, frozen_column)
            if frozen_index.data() == "database":
                break
        else:
            raise RuntimeError("No 'database' column found in frozen table")
        original_frozen_columns = tuple(self._editor.pivot_table_model.model.pivot_frozen)
        frozen_table_header_widget = self._editor.ui.frozen_table.indexWidget(frozen_index)
        self._editor.handle_header_dropped(frozen_table_header_widget, frozen_table_header_widget)
        QApplication.processEvents()
        self.assertEqual(self._editor.pivot_table_model.model.pivot_frozen, original_frozen_columns)


if __name__ == '__main__':
    unittest.main()
