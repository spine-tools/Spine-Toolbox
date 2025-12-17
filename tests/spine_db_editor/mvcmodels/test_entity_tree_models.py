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
from spinetoolbox.spine_db_editor.mvcmodels.entity_tree_models import EntityTreeModel


class TestEntityTreeModel:
    def test_superclass_name_displayed_after_subclass_name(self, db_editor, db_mngr, db_map):
        with db_map:
            db_map.add_entity_class(name="Object")
            db_map.add_entity_class(name="Any")
            db_map.add_superclass_subclass(superclass_name="Any", subclass_name="Object")
        model = EntityTreeModel(db_editor, db_mngr, db_map)
        model.build_tree()
        model.root_item.fetch_more()
        while len(model.root_item.children) != 2:
            QApplication.processEvents()
        assert [child.display_data for child in model.root_item.children] == ["Any", "Object (Any)"]
