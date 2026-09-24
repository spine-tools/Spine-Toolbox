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
from unittest import mock
from PySide6.QtGui import QAction
import pytest
from spinetoolbox.spine_db_editor.mvcmodels.alternative_model import AlternativeModel
from spinetoolbox.spine_db_editor.mvcmodels.entity_tree_models import EntityTreeModel
from spinetoolbox.spine_db_editor.widgets.custom_qtreeview import AlternativeTreeView, EntityTreeView


@pytest.fixture()
def empty_entity_tree_view(parent_widget, app_settings, db_mngr):
    view = EntityTreeView(parent_widget)
    model = EntityTreeModel(parent_widget, app_settings, db_mngr)
    view.setModel(model)
    view.set_app_settings(app_settings)
    copy_action = QAction(parent_widget)
    view.finish_init(copy_action)
    yield view


@pytest.fixture()
def entity_tree_view(empty_entity_tree_view, db_map):
    model = empty_entity_tree_view.model()
    model.db_maps = [db_map]
    model.build_tree()
    yield empty_entity_tree_view


@pytest.fixture()
def empty_alternative_tree_view(parent_widget, app_settings, db_mngr):
    view = AlternativeTreeView(parent_widget)
    model = AlternativeModel(parent_widget, db_mngr)
    view.setModel(model)
    view.set_app_settings(app_settings)
    copy_action = QAction(parent_widget)
    paste_action = QAction(parent_widget)
    view.finish_init(copy_action, paste_action)
    yield view


@pytest.fixture()
def alternative_tree_view(empty_alternative_tree_view, db_map):
    model = empty_alternative_tree_view.model()
    model.db_maps = [db_map]
    model.build_tree()
    yield empty_alternative_tree_view


@pytest.fixture
def dog_fish_db_map(db_map):
    with db_map:
        db_map.add_entity_class(name="fish")
        db_map.add_parameter_definition(entity_class_name="fish", name="water")
        db_map.add_entity(entity_class_name="fish", name="nemo")
        db_map.add_parameter_value(
            entity_class_name="fish",
            entity_byname=("nemo",),
            parameter_definition_name="water",
            alternative_name="Base",
            parsed_value="salt",
        )
        db_map.add_entity_class(name="dog")
        db_map.add_parameter_definition(entity_class_name="dog", name="breed")
        db_map.add_entity(entity_class_name="dog", name="pluto")
        db_map.add_parameter_value(
            entity_class_name="dog",
            entity_byname=("pluto",),
            parameter_definition_name="breed",
            alternative_name="Base",
            parsed_value="bloodhound",
        )
        db_map.add_entity(entity_class_name="dog", name="scooby")
        db_map.add_parameter_value(
            entity_class_name="dog",
            entity_byname=("scooby",),
            parameter_definition_name="breed",
            alternative_name="Base",
            parsed_value="great dane",
        )
        db_map.add_entity_class(dimension_name_list=["fish", "dog"])
        db_map.add_parameter_definition(entity_class_name="fish__dog", name="relative_speed")
        db_map.add_entity(entity_class_name="fish__dog", entity_byname=("nemo", "pluto"))
        db_map.add_parameter_value(
            entity_class_name="fish__dog",
            entity_byname=("nemo", "pluto"),
            parameter_definition_name="relative_speed",
            alternative_name="Base",
            parsed_value=-1,
        )
        db_map.add_entity(entity_class_name="fish__dog", entity_byname=("nemo", "scooby"))
        db_map.add_parameter_value(
            entity_class_name="fish__dog",
            entity_byname=("nemo", "scooby"),
            parameter_definition_name="relative_speed",
            alternative_name="Base",
            parsed_value=5,
        )
        db_map.add_entity_class(dimension_name_list=["dog", "fish"])
        db_map.add_parameter_definition(entity_class_name="dog__fish", name="combined_mojo")
        db_map.add_entity(entity_class_name="dog__fish", entity_byname=("pluto", "nemo"))
        db_map.add_parameter_value(
            entity_class_name="dog__fish",
            entity_byname=("pluto", "nemo"),
            parameter_definition_name="combined_mojo",
            alternative_name="Base",
            parsed_value=100,
        )
    yield db_map
