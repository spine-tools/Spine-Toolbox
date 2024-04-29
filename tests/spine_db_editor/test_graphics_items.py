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

"""Unit tests for Database editor's ``graphics_items`` module."""
import unittest
from unittest import mock
from PySide6.QtCore import QPointF
from PySide6.QtWidgets import QApplication
from spinetoolbox.spine_db_editor.graphics_items import EntityItem
from spinetoolbox.spine_db_editor.widgets.spine_db_editor import SpineDBEditor
from tests.mock_helpers import TestSpineDBManager


class TestEntityItem(unittest.TestCase):
    _db_mngr = None

    @classmethod
    def setUpClass(cls):
        # SpineDBEditor takes long to construct hence we make only one of them for the entire suite.
        if not QApplication.instance():
            QApplication()

    def setUp(self):
        with mock.patch("spinetoolbox.spine_db_editor.widgets.spine_db_editor.SpineDBEditor.restore_ui"), mock.patch(
            "spinetoolbox.spine_db_editor.widgets.spine_db_editor.SpineDBEditor.show"
        ):
            mock_settings = mock.Mock()
            mock_settings.value.side_effect = lambda *args, **kwargs: 0
            self._db_mngr = TestSpineDBManager(mock_settings, None)
            logger = mock.MagicMock()
            self._db_map = self._db_mngr.get_db_map("sqlite://", logger, codename="database", create=True)
            self._spine_db_editor = SpineDBEditor(self._db_mngr, {"sqlite://": "database"})
            self._spine_db_editor.pivot_table_model = mock.MagicMock()
        self._db_mngr.add_entity_classes({self._db_map: [{"name": "oc", "id": 1}]})
        self._db_mngr.add_entities({self._db_map: [{"name": "o", "class_id": 1, "id": 1}]})
        self._db_mngr.add_entity_classes({self._db_map: [{"name": "rc", "id": 2, "dimension_id_list": [1]}]})
        self._db_mngr.add_entities(
            {
                self._db_map: [
                    {
                        "name": "r",
                        "id": 2,
                        "class_id": 2,
                        "entity_class_name": "rc",
                        "element_id_list": [1],
                    }
                ]
            }
        )
        with mock.patch.object(EntityItem, "refresh_icon"):
            self._item = EntityItem(self._spine_db_editor, 0.0, 0.0, 0, ((self._db_map, 2),))

    @classmethod
    def tearDownClass(cls):
        QApplication.removePostedEvents(None)  # Clean up unfinished fetcher signals

    def tearDown(self):
        with mock.patch(
            "spinetoolbox.spine_db_editor.widgets.spine_db_editor.SpineDBEditor.save_window_state"
        ) as mock_save_w_s, mock.patch("spinetoolbox.spine_db_manager.QMessageBox"):
            self._spine_db_editor.close()
            mock_save_w_s.assert_called_once()
        self._db_mngr.close_all_sessions()
        self._db_mngr.clean_up()
        self._spine_db_editor.deleteLater()
        self._spine_db_editor = None

    def test_name(self):
        self.assertEqual(self._item.name, "r")

    def test_entity_class_id(self):
        self.assertEqual(self._item.entity_class_id(self._db_map), self._db_map.get_entity_class_item(id=2)["id"])

    def test_entity_class_name(self):
        self.assertEqual(self._item.entity_class_name, "rc")

    def test_db_map(self):
        self.assertIs(self._item.first_db_map, self._db_map)

    def test_entity_id(self):
        self.assertEqual(self._item.entity_id(self._db_map), 2)

    def test_first_db_map(self):
        self.assertIs(self._item.first_db_map, self._db_map)

    def test_display_data(self):
        self.assertEqual(self._item.display_data, "r")

    def test_display_database(self):
        self.assertEqual(self._item.display_database, "database")

    def test_db_maps(self):
        self.assertEqual(self._item.db_maps, [self._db_map])

    def test_db_map_data(self):
        self.assertEqual(
            self._item.db_map_data(self._db_map).resolve(),
            {
                "name": "r",
                "id": 2,
                "class_id": 2,
                "entity_class_name": "rc",
                "element_id_list": (1,),
                "description": None,
            },
        )

    def test_db_map_id_equals_entity_id(self):
        self.assertEqual(self._item.db_map_id(self._db_map), self._item.entity_id(self._db_map))

    def test_pos(self):
        position = self._item.pos()
        self.assertEqual(position.x(), 0.0)
        self.assertEqual(position.y(), 0.0)

    def test_add_arc_item(self):
        arc = mock.MagicMock()
        self._item.add_arc_item(arc)
        self.assertEqual(self._item.arc_items, [arc])
        arc.update_line.assert_called()

    def test_apply_zoom(self):
        self._item.apply_zoom(0.5)
        self.assertEqual(self._item.scale(), 0.5)
        self._item.apply_zoom(1.5)
        self.assertEqual(self._item.scale(), 1.0)

    def test_apply_rotation(self):
        arc = mock.MagicMock()
        self._item.add_arc_item(arc)
        position = self._item.pos()
        self.assertEqual(position.x(), 1.0)
        self.assertEqual(position.y(), 1.0)
        rotation_center = QPointF(101.0, 1.0)
        self._item.apply_rotation(-90.0, rotation_center)
        self.assertEqual(self._item.pos(), QPointF(101.0, -99.0))
        arc.update_line.assert_has_calls([])


if __name__ == "__main__":
    unittest.main()
