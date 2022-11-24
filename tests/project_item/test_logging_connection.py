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
"""Unit tests for the ``logging_connection`` module."""
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import MagicMock

from PySide6.QtGui import QColor
from PySide6.QtWidgets import QApplication

from spine_engine.project_item.project_item_resource import database_resource
from spinedb_api.filters.scenario_filter import SCENARIO_FILTER_TYPE
from spinetoolbox.project_item.logging_connection import LoggingConnection
from spinetoolbox.project_item.project_item import ProjectItem
from spinetoolbox.project_item.project_item_factory import ProjectItemFactory
from spinetoolbox.project_item_icon import ProjectItemIcon
from spinetoolbox.widgets.properties_widget import PropertiesWidgetBase
from tests.mock_helpers import create_toolboxui_with_project, clean_up_toolbox


class TestLoggingConnection(unittest.TestCase):
    def test_replace_resource_from_source(self):
        toolbox = MagicMock()
        disabled_filters = {"database": {"scenario_filter": {"Base"}}}
        connection = LoggingConnection(
            "source", "bottom", "destination", "top", toolbox=toolbox, disabled_filter_names=disabled_filters
        )
        connection.link = MagicMock()
        original = database_resource("source", "sqlite:///db.sqlite", label="database", filterable=True)
        connection.receive_resources_from_source([original])
        self.assertEqual(connection.database_resources, {original})
        modified = database_resource("source", "sqlite:///db2.sqlite", label="new database", filterable=True)
        connection.replace_resources_from_source([original], [modified])
        self.assertEqual(connection.database_resources, {modified})
        self.assertEqual(connection._disabled_filter_names, {"new database": {"scenario_filter": {"Base"}}})
        connection.tear_down()

    def test_set_online(self):
        toolbox = MagicMock()
        disabled_filters = {"label": {"scenario_filter": {"Base"}}}
        connection = LoggingConnection(
            "source", "bottom", "destination", "top", toolbox=toolbox, disabled_filter_names=disabled_filters
        )
        connection.set_online("label", "scenario_filter", {"Base": True})
        self.assertEqual(connection.disabled_filter_names("label", "scenario_filter"), set())
        connection.tear_down()


class TestLoggingConnectionWithToolbox(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not QApplication.instance():
            QApplication()

    def setUp(self):
        self._temp_dir = TemporaryDirectory()
        self._toolbox = create_toolboxui_with_project(self._temp_dir.name)

    def tearDown(self):
        clean_up_toolbox(self._toolbox)
        self._temp_dir.cleanup()

    def test_removing_connection_that_has_None_db_map_does_not_raise(self):
        project = self._toolbox.project()
        self._toolbox.item_factories[_DataStore.item_type()] = _DataStoreFactory
        self._toolbox._item_properties_uis[_DataStore.item_type()] = _DataStoreFactory.make_properties_widget(self)
        store_1 = _DataStore("Store 1", project)
        project.add_item(store_1)
        store_2 = _DataStore("Store 2", project)
        project.add_item(store_2)
        connection = LoggingConnection("Store 1", "right", "Store 2", "left", toolbox=self._toolbox)
        connection.set_online(store_1.resource_label(), SCENARIO_FILTER_TYPE, {"scenario name": False})
        self.assertTrue(project.add_connection(connection))
        try:
            project.remove_connection(connection)
        except KeyError:
            self.fail("remove_connection raised")


class _DataStoreFactory(ProjectItemFactory):
    @staticmethod
    def item_class():
        return _DataStore

    @staticmethod
    def icon():
        return ":/icons/menu_icons/trash-alt.svg"

    @staticmethod
    def icon_color():
        return QColor("black")

    @staticmethod
    def make_icon(toolbox):
        return ProjectItemIcon(toolbox, _DataStoreFactory.icon(), _DataStoreFactory.icon_color())

    @staticmethod
    def make_properties_widget(toolbox):
        return _DataStorePropertiesWidget(toolbox)


class _DataStore(ProjectItem):
    def __init__(self, name, project):
        super().__init__(name, "", 0.0, 0.0, project)

    @staticmethod
    def item_type():
        return "Mock Data Store"

    @staticmethod
    def item_category():
        return "Data Stores"

    # pylint: disable=no-self-use
    def resources_for_direct_successors(self):
        return [
            database_resource(
                self.name, "sqlite:///non/existent/database.sqlite", label=self.resource_label(), filterable=True
            )
        ]

    def resource_label(self):
        return f"database@{self.name}"


class _DataStorePropertiesWidget(PropertiesWidgetBase):
    def __init__(self, toolbox):
        super().__init__(toolbox)
        self.ui = object()


if __name__ == '__main__':
    unittest.main()
