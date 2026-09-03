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
