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
from unittest import mock
from PySide6.QtCore import QItemSelectionModel
from PySide6.QtWidgets import QApplication
from tests.mock_helpers import assert_table_model_data_pytest


def fetch_entity_tree_model(db_editor):
    for item in db_editor.entity_tree_model.visit_all():
        while item.can_fetch_more():
            item.fetch_more()
            QApplication.processEvents()


class TestSpineDBEditorWithDBMapping:

    def test_duplicate_zero_dimensional_entity_in_entity_tree_model(self, db_map, db_name, db_mngr, db_editor):
        data = {
            "entity_classes": [("fish",), ("dog",), ("fish__dog", ("fish", "dog"))],
            "entities": [("fish", "nemo"), ("dog", "pluto"), ("fish__dog", ("nemo", "pluto"))],
            "parameter_definitions": [("fish", "color")],
            "parameter_values": [("fish", "nemo", "color", "orange")],
        }
        db_mngr.import_data({db_map: data}, "Import test data.")
        QApplication.processEvents()
        fetch_entity_tree_model(db_editor)
        root_item = db_editor.entity_tree_model.root_item
        fish_item = next(iter(item for item in root_item.children if item.display_data == "fish"))
        nemo_item = fish_item.child(0)
        with mock.patch.object(db_mngr, "error_msg") as error_msg_signal:
            db_editor.duplicate_entity(nemo_item)
            error_msg_signal.emit.assert_not_called()
        assert fish_item.row_count() == 2
        nemo_dupe = fish_item.child(1)
        assert nemo_dupe.display_data == "nemo (1)"
        fish_dog_item = next(iter(item for item in root_item.children if item.display_data == "fish__dog"))
        fish_dog_item.fetch_more()
        assert fish_dog_item.row_count() == 2
        nemo_pluto_dupe = fish_dog_item.child(1)
        assert nemo_pluto_dupe.display_data == "nemo (1) ǀ pluto"
        root_index = db_editor.entity_tree_model.index_from_item(root_item)
        db_editor.ui.treeView_entity.selectionModel().setCurrentIndex(
            root_index, QItemSelectionModel.SelectionFlags.ClearAndSelect
        )
        while db_editor.parameter_value_model.rowCount() != 2:
            QApplication.processEvents()
        expected = [
            [None, "fish", "nemo", "color", "Base", "orange", db_name],
            [None, "fish", "nemo (1)", "color", "Base", "orange", db_name],
        ]
        assert_table_model_data_pytest(db_editor.parameter_value_model, expected)
