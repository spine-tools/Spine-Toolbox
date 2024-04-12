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

"""Test for `mass_select_items_dialogs` module."""
import unittest
from unittest import mock
from PySide6.QtWidgets import QApplication, QDialogButtonBox

from spinedb_api.temp_id import TempId
from spinetoolbox.spine_db_editor.widgets.mass_select_items_dialogs import MassRemoveItemsDialog
from spinetoolbox.spine_db_manager import SpineDBManager


class TestMassRemoveItemsDialog(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not QApplication.instance():
            QApplication()

    def setUp(self):
        url = "sqlite:///"
        with mock.patch("spinetoolbox.spine_db_editor.widgets.spine_db_editor.SpineDBEditor.restore_ui"), mock.patch(
            "spinetoolbox.spine_db_editor.widgets.spine_db_editor.SpineDBEditor.show"
        ):
            mock_settings = mock.Mock()
            mock_settings.value.side_effect = lambda *args, **kwargs: 0
            self._db_mngr = SpineDBManager(mock_settings, None)
            logger = mock.MagicMock()
            self._db_map = self._db_mngr.get_db_map(url, logger, codename="database", create=True)
        QApplication.processEvents()

    def tearDown(self):
        self._db_mngr.close_all_sessions()
        while not self._db_map.closed:
            QApplication.processEvents()
        self._db_mngr.clean_up()

    def test_stored_state(self):
        state = {"databases": {self._db_map: True}, "items": {"entity": True, "entity_class": True}}
        dialog = MassRemoveItemsDialog(None, self._db_mngr, self._db_map, stored_state=state)
        self.assertEqual(
            dialog._item_check_boxes_widget.checked_states(),
            {
                "alternative": False,
                "entity_group": False,
                "entity_metadata": False,
                "list_value": False,
                "metadata": False,
                "entity": True,
                "entity_alternative": False,
                "entity_class": True,
                "parameter_definition": False,
                "parameter_value": False,
                "parameter_value_list": False,
                "parameter_value_metadata": False,
                "scenario": False,
                "scenario_alternative": False,
                "superclass_subclass": False,
            },
        )
        self.assertTrue(dialog._database_check_boxes_widget._check_boxes[self._db_map].isChecked())

    def test_purge_objects(self):
        self._db_mngr.add_entity_classes({self._db_map: [{"name": "my_class"}]})
        classes = self._db_mngr.get_items(self._db_map, "entity_class")
        class_id = classes[0]["id"]
        self._db_mngr.add_entities({self._db_map: [{"class_id": class_id, "name": "my_object"}]})
        entities = [item._asdict() for item in self._db_mngr.get_items(self._db_map, "entity")]
        self.assertEqual(len(entities), 1)
        entity_id = entities[0]["id"]
        self.assertEqual(
            entities,
            [
                {
                    "class_id": class_id,
                    "description": None,
                    "id": entity_id,
                    "name": "my_object",
                    "element_id_list": (),
                }
            ],
        )
        dialog = MassRemoveItemsDialog(None, self._db_mngr, self._db_map)
        dialog._database_check_boxes_widget._check_boxes[self._db_map].setChecked(True)
        dialog._item_check_boxes_widget._item_check_boxes["entity"].setChecked(True)
        dialog._ui.button_box.button(QDialogButtonBox.StandardButton.Ok).click()
        self.assertEqual(self._db_mngr.get_items(self._db_map, "entity"), [])


if __name__ == "__main__":
    unittest.main()
