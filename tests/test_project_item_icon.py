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

"""Unit tests for ``project_item_icon`` module."""
import os.path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch, MagicMock
from PySide6.QtCore import QEvent, QPoint, Qt
from PySide6.QtGui import QColor, QContextMenuEvent
from PySide6.QtWidgets import QApplication, QGraphicsSceneMouseEvent
from spinedb_api import DatabaseMapping, import_scenarios
from spine_engine.project_item.project_item_resource import database_resource
from spinetoolbox.project_item_icon import ExclamationIcon, ProjectItemIcon, RankIcon
from spinetoolbox.project_item.logging_connection import LoggingConnection
from spinetoolbox.link import Link
from spinetoolbox.project_commands import MoveIconCommand
from tests.mock_helpers import add_view, clean_up_toolbox, create_toolboxui_with_project, TestSpineDBManager


class TestProjectItemIcon(unittest.TestCase):
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

    def test_init(self):
        icon = ProjectItemIcon(self._toolbox, ":/icons/home.svg", QColor(Qt.GlobalColor.gray))
        self.assertEqual(icon.name(), "")
        self.assertEqual(icon.x(), 0)
        self.assertEqual(icon.y(), 0)
        self.assertEqual(icon.incoming_links(), [])
        self.assertEqual(icon.outgoing_connection_links(), [])

    def test_finalize(self):
        icon = ProjectItemIcon(self._toolbox, ":/icons/home.svg", QColor(Qt.GlobalColor.gray))
        icon.finalize("new name", -43, 314)
        self.assertEqual(icon.name(), "new name")
        self.assertEqual(icon.x(), -43)
        self.assertEqual(icon.y(), 314)

    def test_conn_button(self):
        icon = ProjectItemIcon(self._toolbox, ":/icons/home.svg", QColor(Qt.GlobalColor.gray))
        button = icon.conn_button("left")
        self.assertEqual(button.position, "left")
        button = icon.conn_button("right")
        self.assertEqual(button.position, "right")
        button = icon.conn_button("bottom")
        self.assertEqual(button.position, "bottom")

    def test_outgoing_and_incoming_links(self):
        source_icon = ProjectItemIcon(self._toolbox, ":/icons/home.svg", QColor(Qt.GlobalColor.gray))
        target_icon = ProjectItemIcon(self._toolbox, ":/icons/home.svg", QColor(Qt.GlobalColor.gray))
        self._toolbox.project().get_item = MagicMock()
        connection = LoggingConnection("source item", "bottom", "destination item", "bottom", toolbox=self._toolbox)
        link = Link(self._toolbox, source_icon.conn_button("bottom"), target_icon.conn_button("bottom"), connection)
        link.src_connector.links.append(link)
        link.dst_connector.links.append(link)
        self.assertEqual(source_icon.outgoing_connection_links(), [link])
        self.assertEqual(target_icon.incoming_links(), [link])

    def test_drag_icon(self):
        item = add_view(self._toolbox.project(), self._toolbox.item_factories, "View")
        icon = item.get_icon()
        self.assertEqual(icon.x(), 0.0)
        self.assertEqual(icon.y(), 0.0)
        icon.mousePressEvent(QGraphicsSceneMouseEvent(QEvent.GraphicsSceneMousePress))
        icon.mouseMoveEvent(QGraphicsSceneMouseEvent(QEvent.GraphicsSceneMouseMove))
        icon.moveBy(99.0, 88.0)
        icon.mouseReleaseEvent(QGraphicsSceneMouseEvent(QEvent.GraphicsSceneMouseRelease))
        self.assertEqual(icon.x(), 99.0)
        self.assertEqual(icon.y(), 88.0)
        self.assertEqual(self._toolbox.undo_stack.count(), 1)
        move_command = self._toolbox.undo_stack.command(0)
        self.assertIsInstance(move_command, MoveIconCommand)

    def test_context_menu_event(self):
        item = add_view(self._toolbox.project(), self._toolbox.item_factories, "View")
        icon = item.get_icon()
        with patch("spinetoolbox.ui_main.ToolboxUI.show_project_or_item_context_menu") as mock_show_menu:
            mock_show_menu.return_value = True
            icon.contextMenuEvent(QGraphicsSceneMouseEvent(QEvent.Type.ContextMenu))
            mock_show_menu.assert_called()


class TestExclamationIcon(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not QApplication.instance():
            QApplication()

    def test_no_notifications(self):
        with patch("PySide6.QtWidgets.QToolTip.showText") as show_text:
            icon = ExclamationIcon(None)
            icon.hoverEnterEvent(QGraphicsSceneMouseEvent())
            show_text.assert_not_called()

    def test_add_notification(self):
        with patch("PySide6.QtWidgets.QToolTip.showText") as show_text:
            icon = ExclamationIcon(None)
            icon.add_notification("Please note!")
            icon.hoverEnterEvent(QGraphicsSceneMouseEvent())
            show_text.assert_called_once_with(QPoint(0, 0), "<p>Please note!")

    def test_clear_notifications(self):
        with patch("PySide6.QtWidgets.QToolTip.showText") as show_text:
            icon = ExclamationIcon(None)
            icon.add_notification("Please note!")
            icon.clear_notifications()
            icon.hoverEnterEvent(QGraphicsSceneMouseEvent())
            show_text.assert_not_called()


class TestRankIcon(unittest.TestCase):
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

    def test_set_rank(self):
        item_icon = ProjectItemIcon(self._toolbox, ":/icons/home.svg", QColor(Qt.GlobalColor.gray))
        icon = RankIcon(item_icon)
        self.assertEqual(icon.toPlainText(), "")
        icon.set_rank(23)
        self.assertEqual(icon.toPlainText(), "23")


class TestLink(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not QApplication.instance():
            QApplication()

    def setUp(self):
        self._temp_dir = TemporaryDirectory()
        self._toolbox = create_toolboxui_with_project(self._temp_dir.name)
        self._toolbox.db_mngr = TestSpineDBManager(MagicMock(), None)
        source_item_icon = ProjectItemIcon(self._toolbox, ":/icons/home.svg", QColor(Qt.GlobalColor.gray))
        source_item_icon.update_name_item("source icon")
        destination_item_icon = ProjectItemIcon(self._toolbox, ":/icons/home.svg", QColor(Qt.GlobalColor.gray))
        destination_item_icon.update_name_item("destination icon")
        project = self._toolbox.project()
        project.get_item = MagicMock()
        connection = LoggingConnection("source icon", "right", "destination icon", "left", toolbox=self._toolbox)
        connection.link = self._link = Link(
            self._toolbox, source_item_icon.conn_button(), destination_item_icon.conn_button(), connection
        )
        project.find_connection = MagicMock()
        project.find_connection.return_value = connection
        self._link.update_icons = MagicMock()

    def tearDown(self):
        clean_up_toolbox(self._toolbox)
        self._temp_dir.cleanup()

    def test_scenario_filter_gets_added_to_filter_model(self):
        url = "sqlite:///" + os.path.join(self._temp_dir.name, "db.sqlite")
        db_map = DatabaseMapping(url, create=True)
        import_scenarios(db_map, (("scenario", True),))
        db_map.commit_session("Add test data.")
        db_map.close()
        self._link.connection.receive_resources_from_source(
            [database_resource("provider", url, "my_database", filterable=True)]
        )
        self._link.connection.refresh_resource_filter_model()
        filter_model = self._link.connection.resource_filter_model
        self.assertEqual(filter_model.rowCount(), 1)
        self.assertEqual(filter_model.columnCount(), 1)
        index = filter_model.index(0, 0)
        self.assertEqual(index.data(), "my_database")
        root_item = filter_model.itemFromIndex(index)
        self.assertEqual(root_item.rowCount(), 2)
        self.assertEqual(root_item.columnCount(), 1)
        scenario_title_item = root_item.child(0, 0)
        self.assertEqual(scenario_title_item.index().data(), "Scenario filter")
        self.assertEqual(scenario_title_item.rowCount(), 2)
        self.assertEqual(scenario_title_item.columnCount(), 1)
        scenario_item = scenario_title_item.child(0, 0)
        self.assertEqual(scenario_item.index().data(), "Select all")
        scenario_item = scenario_title_item.child(1, 0)
        self.assertEqual(scenario_item.index().data(), "scenario")
        alternative_title_item = root_item.child(1, 0)
        self.assertEqual(alternative_title_item.index().data(), "Alternative filter")
        self.assertEqual(alternative_title_item.rowCount(), 2)
        self.assertEqual(alternative_title_item.columnCount(), 1)
        alternative_item = alternative_title_item.child(0, 0)
        self.assertEqual(alternative_item.index().data(), "Select all")
        alternative_item = alternative_title_item.child(1, 0)
        self.assertEqual(alternative_item.index().data(), "Base")
        scenario_index = filter_model.indexFromItem(scenario_item)
        self.assertEqual(self._link.connection.online_filters("my_database", "scenario_filter"), {"scenario": True})
        filter_model.setData(scenario_index, Qt.CheckState.Unchecked.value, role=Qt.ItemDataRole.CheckStateRole)
        self.assertEqual(self._link.connection.online_filters("my_database", "scenario_filter"), {"scenario": False})
        self.assertEqual(self._link.connection.online_filters("my_database", "alternative_filter"), {"Base": True})

    def test_toggle_scenario_filter(self):
        url = "sqlite:///" + os.path.join(self._temp_dir.name, "db.sqlite")
        db_map = DatabaseMapping(url, create=True)
        import_scenarios(db_map, (("scenario", True),))
        db_map.commit_session("Add test data.")
        db_map.close()
        self._link.connection.receive_resources_from_source([database_resource("provider", url, filterable=True)])
        self._link.connection.refresh_resource_filter_model()
        self.assertEqual(self._link.connection.online_filters(url, "scenario_filter"), {"scenario": True})
        filter_model = self._link.connection.resource_filter_model
        filter_model.set_online(url, "scenario_filter", {"scenario": False})
        self.assertEqual(self._link.connection.online_filters(url, "scenario_filter"), {"scenario": False})


if __name__ == "__main__":
    unittest.main()
