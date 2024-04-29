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

"""Unit tests for the item metadata table model."""
from tempfile import TemporaryDirectory
import unittest
from unittest import mock
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication
from spinedb_api import (
    DatabaseMapping,
    import_object_classes,
    import_object_metadata,
    import_object_parameter_value_metadata,
    import_object_parameter_values,
    import_object_parameters,
    import_objects,
    import_metadata,
    import_relationship_classes,
    import_relationship_metadata,
    import_relationship_parameter_value_metadata,
    import_relationship_parameter_values,
    import_relationship_parameters,
    import_relationships,
)
from spinetoolbox.spine_db_editor.mvcmodels.item_metadata_table_model import ItemMetadataTableModel
from spinetoolbox.spine_db_editor.mvcmodels.metadata_table_model_base import Column
from tests.mock_helpers import TestSpineDBManager, fetch_model


class TestItemMetadataTableModelWithExistingData(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not QApplication.instance():
            QApplication()

    def setUp(self):
        self._temp_dir = TemporaryDirectory()
        self._url = "sqlite:///" + self._temp_dir.name + "/db.sqlite"
        db_map = DatabaseMapping(self._url, create=True)
        import_object_classes(db_map, ("my_class",))
        import_objects(db_map, (("my_class", "my_object"),))
        import_object_parameters(db_map, (("my_class", "object_parameter"),))
        import_object_parameter_values(db_map, (("my_class", "my_object", "object_parameter", 2.3),))
        import_relationship_classes(db_map, (("entity_class", ("my_class",)),))
        import_relationships(db_map, (("entity_class", ("my_object",)),))
        import_relationship_parameters(db_map, (("entity_class", "relationship_parameter"),))
        import_relationship_parameter_values(db_map, (("entity_class", ("my_object",), "relationship_parameter", 5.0),))
        import_metadata(db_map, ('{"source": "Fountain of objects"}',))
        import_object_metadata(db_map, (("my_class", "my_object", '{"source": "Fountain of objects"}'),))
        import_metadata(db_map, ('{"source": "Fountain of relationships"}',))
        import_relationship_metadata(
            db_map, (("entity_class", ("my_object",), '{"source": "Fountain of relationships"}'),)
        )
        import_metadata(db_map, ('{"source": "Fountain of object values"}',))
        import_object_parameter_value_metadata(
            db_map, (("my_class", "my_object", "object_parameter", '{"source": "Fountain of object values"}'),)
        )
        import_metadata(db_map, ('{"source": "Fountain of relationship values"}',))
        import_relationship_parameter_value_metadata(
            db_map,
            (
                (
                    "entity_class",
                    ("my_object",),
                    "relationship_parameter",
                    '{"source": "Fountain of relationship values"}',
                ),
            ),
        )
        db_map.commit_session("Add test data.")
        db_map.close()
        mock_settings = mock.Mock()
        mock_settings.value.side_effect = lambda *args, **kwargs: 0
        self._db_mngr = TestSpineDBManager(mock_settings, None)
        logger = mock.MagicMock()
        self._db_map = self._db_mngr.get_db_map(self._url, logger, codename="database")
        QApplication.processEvents()
        self._db_map.fetch_all()
        self._model = ItemMetadataTableModel(self._db_mngr, [self._db_map], None)
        fetch_model(self._model)

    def tearDown(self):
        self._db_mngr.close_all_sessions()
        while not self._db_map.closed:
            QApplication.processEvents()
        self._db_mngr.clean_up()
        self._model.deleteLater()
        self._temp_dir.cleanup()

    def test_model_is_initially_empty(self):
        self.assertEqual(self._model.rowCount(), 1)
        self.assertEqual(self._model.columnCount(), 3)
        self.assertEqual(self._model.headerData(Column.NAME, Qt.Orientation.Horizontal), "name")
        self.assertEqual(self._model.headerData(Column.VALUE, Qt.Orientation.Horizontal), "value")
        self.assertEqual(self._model.headerData(Column.DB_MAP, Qt.Orientation.Horizontal), "database")
        self._assert_empty_last_row()

    def test_get_metadata_for_object(self):
        self._model.set_entity_ids({self._db_map: self._db_map.get_entity_item(id=1)["id"]})
        self.assertEqual(self._model.rowCount(), 2)
        self.assertEqual(self._model.index(0, Column.NAME).data(), "source")
        self.assertEqual(self._model.index(0, Column.VALUE).data(), "Fountain of objects")
        self.assertEqual(self._model.index(0, Column.DB_MAP).data(), "database")
        self._assert_empty_last_row()

    def test_get_metadata_for_relationship(self):
        self._model.set_entity_ids({self._db_map: self._db_map.get_entity_item(id=2)["id"]})
        self.assertEqual(self._model.rowCount(), 2)
        self.assertEqual(self._model.index(0, Column.NAME).data(), "source")
        self.assertEqual(self._model.index(0, Column.VALUE).data(), "Fountain of relationships")
        self.assertEqual(self._model.index(0, Column.DB_MAP).data(), "database")
        self._assert_empty_last_row()

    def test_get_metadata_for_object_parameter_value(self):
        self._model.set_parameter_value_ids({self._db_map: self._db_map.get_parameter_value_item(id=1)["id"]})
        self.assertEqual(self._model.rowCount(), 2)
        self.assertEqual(self._model.index(0, Column.NAME).data(), "source")
        self.assertEqual(self._model.index(0, Column.VALUE).data(), "Fountain of object values")
        self.assertEqual(self._model.index(0, Column.DB_MAP).data(), "database")
        self._assert_empty_last_row()

    def test_get_metadata_for_relationship_parameter_value(self):
        self._model.set_parameter_value_ids({self._db_map: self._db_map.get_parameter_value_item(id=2)["id"]})
        self.assertEqual(self._model.rowCount(), 2)
        self.assertEqual(self._model.index(0, Column.NAME).data(), "source")
        self.assertEqual(self._model.index(0, Column.VALUE).data(), "Fountain of relationship values")
        self.assertEqual(self._model.index(0, Column.DB_MAP).data(), "database")
        self._assert_empty_last_row()

    def _assert_empty_last_row(self):
        row = self._model.rowCount() - 1
        self.assertEqual(self._model.index(row, Column.NAME).data(), "")
        self.assertEqual(self._model.index(row, Column.VALUE).data(), "")
        self.assertEqual(self._model.index(row, Column.DB_MAP).data(), "database")

    def test_roll_back_after_item_metadata_update(self):
        self._model.set_entity_ids({self._db_map: self._db_map.get_entity_item(id=1)["id"]})
        index = self._model.index(0, Column.VALUE)
        self.assertTrue(self._model.setData(index, "Magician's hat"))
        self.assertEqual(self._model.rowCount(), 2)
        self.assertEqual(self._model.index(0, Column.NAME).data(), "source")
        self.assertEqual(self._model.index(0, Column.VALUE).data(), "Magician's hat")
        self._assert_empty_last_row()
        self._db_mngr.rollback_session(self._db_map)
        self.assertEqual(self._model.rowCount(), 2)
        self.assertEqual(self._model.index(0, Column.NAME).data(), "source")
        self.assertEqual(self._model.index(0, Column.VALUE).data(), "Fountain of objects")
        self._assert_empty_last_row()

    def test_update_relationship_parameter_value_metadata(self):
        self._model.set_parameter_value_ids({self._db_map: self._db_map.get_parameter_value_item(id=2)["id"]})
        index = self._model.index(0, Column.VALUE)
        self.assertTrue(self._model.setData(index, "Magician's hat"))
        self.assertEqual(self._model.rowCount(), 2)
        self.assertEqual(self._model.index(0, Column.NAME).data(), "source")
        self.assertEqual(self._model.index(0, Column.VALUE).data(), "Magician's hat")
        self._assert_empty_last_row()

    def test_update_relationship_metadata(self):
        self._model.set_entity_ids({self._db_map: self._db_map.get_entity_item(id=2)["id"]})
        index = self._model.index(0, Column.VALUE)
        self.assertTrue(self._model.setData(index, "Magician's hat"))
        self.assertEqual(self._model.rowCount(), 2)
        self.assertEqual(self._model.index(0, Column.NAME).data(), "source")
        self.assertEqual(self._model.index(0, Column.VALUE).data(), "Magician's hat")
        self._assert_empty_last_row()

    def test_add_relationship_parameter_value_metadata(self):
        self._model.set_parameter_value_ids({self._db_map: self._db_map.get_parameter_value_item(id=2)["id"]})
        index = self._model.index(1, Column.NAME)
        self.assertTrue(self._model.setData(index, "author"))
        index = self._model.index(1, Column.VALUE)
        self.assertTrue(self._model.setData(index, "Anonymous"))
        db_map_item_metadata = {
            self._db_map: [
                {"metadata_name": "author", "metadata_value": "Anonymous", "parameter_value_id": 2, "commit_id": None}
            ]
        }
        self._db_mngr.add_parameter_value_metadata(db_map_item_metadata)
        self.assertEqual(self._model.rowCount(), 3)
        self.assertEqual(self._model.index(0, Column.NAME).data(), "source")
        self.assertEqual(self._model.index(0, Column.VALUE).data(), "Fountain of relationship values")
        self.assertEqual(self._model.index(1, Column.NAME).data(), "author")
        self.assertEqual(self._model.index(1, Column.VALUE).data(), "Anonymous")
        self._assert_empty_last_row()

    def test_add_relationship_metadata(self):
        self._model.set_entity_ids({self._db_map: self._db_map.get_entity_item(id=2)["id"]})
        index = self._model.index(1, Column.NAME)
        self.assertTrue(self._model.setData(index, "author"))
        index = self._model.index(1, Column.VALUE)
        self.assertTrue(self._model.setData(index, "Anonymous"))
        db_map_item_metadata = {
            self._db_map: [
                {
                    "metadata_name": "author",
                    "metadata_value": "Anonymous",
                    "entity_id": 2,
                    "commit_id": None,
                }
            ]
        }
        self._db_mngr.add_entity_metadata(db_map_item_metadata)
        self.assertEqual(self._model.rowCount(), 3)
        self.assertEqual(self._model.index(0, Column.NAME).data(), "source")
        self.assertEqual(self._model.index(0, Column.VALUE).data(), "Fountain of relationships")
        self.assertEqual(self._model.index(1, Column.NAME).data(), "author")
        self.assertEqual(self._model.index(1, Column.VALUE).data(), "Anonymous")
        self._assert_empty_last_row()

    def test_remove_object_metadata_row(self):
        self._model.set_entity_ids({self._db_map: self._db_map.get_entity_item(id=1)["id"]})
        self._model.removeRows(0, 1)
        self.assertEqual(self._model.rowCount(), 1)

    def test_remove_object_parameter_value_metadata_row(self):
        self._model.set_parameter_value_ids({self._db_map: self._db_map.get_parameter_value_item(id=1)["id"]})
        self._model.removeRows(0, 1)
        self.assertEqual(self._model.rowCount(), 1)


if __name__ == "__main__":
    unittest.main()
