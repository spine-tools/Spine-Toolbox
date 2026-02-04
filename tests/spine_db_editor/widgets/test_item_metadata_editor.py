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
from PySide6.QtWidgets import QApplication
from tests.mock_helpers import assert_table_model_data_pytest


class TestItemMetadataEditor:
    def test_selecting_entity_from_entity_tree_shows_its_metadata(self, db_editor, db_map, db_name):
        db_map.add_entity_class(name="Gadget")
        db_map.add_entity(entity_class_name="Gadget", name="watch")
        db_map.add_metadata(name="Author", value="A. Uthor")
        db_map.add_entity_metadata(
            entity_class_name="Gadget", entity_byname=("watch",), metadata_name="Author", metadata_value="A. Uthor"
        )
        entity_tree = db_editor.ui.treeView_entity
        entity_model = entity_tree.model()
        root_index = entity_model.index(0, 0)
        entity_model.fetchMore(root_index)
        while entity_model.rowCount(root_index) != 1:
            QApplication.processEvents()
        gadget_index = entity_model.index(0, 0, root_index)
        assert gadget_index.data() == "Gadget"
        entity_model.fetchMore(gadget_index)
        while entity_model.rowCount(gadget_index) != 1:
            QApplication.processEvents()
        watch_index = entity_model.index(0, 0, gadget_index)
        assert watch_index.data() == "watch"
        entity_tree.setCurrentIndex(watch_index)
        metadata_view = db_editor.ui.item_metadata_table_view
        metadata_model = metadata_view.model()
        expected = [["Author", "A. Uthor", db_name], ["", "", db_name]]
        assert_table_model_data_pytest(metadata_model, expected)

    def test_selecting_entity_from_entity_table_shows_its_metadata(self, db_editor, db_map, db_name):
        db_map.add_entity_class(name="Gadget")
        db_map.add_entity(entity_class_name="Gadget", name="watch")
        db_map.add_metadata(name="Author", value="A. Uthor")
        db_map.add_entity_metadata(
            entity_class_name="Gadget", entity_byname=("watch",), metadata_name="Author", metadata_value="A. Uthor"
        )
        entity_table = db_editor.ui.entity_table_view
        entity_model = entity_table.model()
        while entity_model.rowCount() != 1:
            QApplication.processEvents()
        class_index = entity_model.index(0, 0)
        assert class_index.data() == "Gadget"
        entity_table.setCurrentIndex(class_index)
        metadata_view = db_editor.ui.item_metadata_table_view
        metadata_model = metadata_view.model()
        expected = [["Author", "A. Uthor", db_name], ["", "", db_name]]
        assert_table_model_data_pytest(metadata_model, expected)

    def test_selecting_value_from_value_table_shows_its_metadata(self, db_editor, db_map, db_name):
        db_map.add_entity_class(name="Gadget")
        db_map.add_entity(entity_class_name="Gadget", name="watch")
        db_map.add_parameter_definition(entity_class_name="Gadget", name="X")
        db_map.add_parameter_value(
            entity_class_name="Gadget",
            entity_byname=("watch",),
            parameter_definition_name="X",
            alternative_name="Base",
            parsed_value=2.3,
        )
        db_map.add_metadata(name="Author", value="A. Uthor")
        db_map.add_parameter_value_metadata(
            entity_class_name="Gadget",
            entity_byname=("watch",),
            parameter_definition_name="X",
            alternative_name="Base",
            metadata_name="Author",
            metadata_value="A. Uthor",
        )
        value_table = db_editor.ui.tableView_parameter_value
        value_model = value_table.model()
        while value_model.rowCount() != 1:
            QApplication.processEvents()
        class_index = value_model.index(0, 1)
        assert class_index.data() == "Gadget"
        value_table.setCurrentIndex(class_index)
        metadata_view = db_editor.ui.item_metadata_table_view
        metadata_model = metadata_view.model()
        expected = [["Author", "A. Uthor", db_name], ["", "", db_name]]
        assert_table_model_data_pytest(metadata_model, expected)
