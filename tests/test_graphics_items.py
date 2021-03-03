######################################################################################################################
# Copyright (C) 2017-2021 Spine project consortium
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""
Unit tests for ``graphics_items`` module.

:authors: A. Soininen (VTT)
:date:    17.12.2020
"""
import os.path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch, PropertyMock
from PySide2.QtCore import QEvent, QPoint, Qt
from PySide2.QtGui import QColor
from PySide2.QtWidgets import QApplication, QGraphicsSceneMouseEvent
from spinedb_api import DiffDatabaseMapping, import_scenarios, import_tools
from spine_engine.project_item.connection import Connection
from spine_engine.project_item.project_item_resource import database_resource
from spinetoolbox.graphics_items import ExclamationIcon, Link, ProjectItemIcon, RankIcon
from spinetoolbox.project_commands import MoveIconCommand
from .mock_helpers import clean_up_toolbox, create_toolboxui_with_project


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
        icon = ProjectItemIcon(self._toolbox, "", QColor(Qt.gray), QColor(Qt.green))
        self.assertEqual(icon.name(), "")
        self.assertEqual(icon.x(), 0)
        self.assertEqual(icon.y(), 0)
        self.assertIn(icon, self._toolbox.ui.graphicsView.scene().items())
        self.assertEqual(icon.incoming_links(), [])
        self.assertEqual(icon.outgoing_links(), [])

    def test_finalize(self):
        icon = ProjectItemIcon(self._toolbox, "", QColor(Qt.gray), QColor(Qt.green))
        icon.finalize("new name", -43, 314)
        self.assertEqual(icon.name(), "new name")
        self.assertEqual(icon.x(), -43)
        self.assertEqual(icon.y(), 314)

    def test_conn_button(self):
        icon = ProjectItemIcon(self._toolbox, "", QColor(Qt.gray), QColor(Qt.green))
        button = icon.conn_button("left")
        self.assertEqual(button.position, "left")
        button = icon.conn_button("right")
        self.assertEqual(button.position, "right")
        button = icon.conn_button("bottom")
        self.assertEqual(button.position, "bottom")

    def test_outgoing_and_incoming_links(self):
        source_icon = ProjectItemIcon(self._toolbox, "", QColor(Qt.gray), QColor(Qt.green))
        target_icon = ProjectItemIcon(self._toolbox, "", QColor(Qt.gray), QColor(Qt.green))
        connection = Connection("source item", "bottom", "destination item", "bottom")
        link = Link(self._toolbox, source_icon.conn_button("bottom"), target_icon.conn_button("bottom"), connection)
        link.src_connector.links.append(link)
        link.dst_connector.links.append(link)
        self.assertEqual(source_icon.outgoing_links(), [link])
        self.assertEqual(target_icon.incoming_links(), [link])

    def test_drag_icon(self):
        icon = ProjectItemIcon(self._toolbox, "", QColor(Qt.gray), QColor(Qt.green))
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


class TestExclamationIcon(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not QApplication.instance():
            QApplication()

    def test_no_notifications(self):
        with patch("PySide2.QtWidgets.QToolTip.showText") as show_text:
            icon = ExclamationIcon(None)
            icon.hoverEnterEvent(QGraphicsSceneMouseEvent())
            show_text.assert_not_called()

    def test_add_notification(self):
        with patch("PySide2.QtWidgets.QToolTip.showText") as show_text:
            icon = ExclamationIcon(None)
            icon.add_notification("Please note!")
            icon.hoverEnterEvent(QGraphicsSceneMouseEvent())
            show_text.assert_called_once_with(QPoint(0, 0), "<p>Please note!")

    def test_clear_notifications(self):
        with patch("PySide2.QtWidgets.QToolTip.showText") as show_text:
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
        item_icon = ProjectItemIcon(self._toolbox, "", QColor(Qt.gray), QColor(Qt.green))
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
        with patch("spinetoolbox.ui_main.SpineDBManager.thread", new_callable=PropertyMock) as mock_thread:
            mock_thread.return_value = QApplication.instance().thread()
            self._toolbox = create_toolboxui_with_project(self._temp_dir.name)
        type(self._toolbox.db_mngr).thread = PropertyMock(return_value=QApplication.instance().thread())
        source_item_icon = ProjectItemIcon(self._toolbox, "", QColor(Qt.gray), QColor(Qt.green))
        source_item_icon.update_name_item("source icon")
        destination_item_icon = ProjectItemIcon(self._toolbox, "", QColor(Qt.gray), QColor(Qt.green))
        destination_item_icon.update_name_item("destination icon")
        connection = Connection("source icon", "right", "destination icon", "left")
        self._link = Link(
            self._toolbox, source_item_icon.conn_button(), destination_item_icon.conn_button(), connection
        )

    def tearDown(self):
        clean_up_toolbox(self._toolbox)
        self._temp_dir.cleanup()

    def test_scenario_filter_gets_added_to_filter_model(self):
        url = "sqlite:///" + os.path.join(self._temp_dir.name, "db.sqlite")
        db_map = DiffDatabaseMapping(url, create=True)
        import_scenarios(db_map, (("scenario", True),))
        db_map.commit_session("Add test data.")
        db_map.connection.close()
        self._link.handle_dag_changed([database_resource("provider", url)])
        self._link.refresh_resource_filter_model()
        self.assertTrue(self._link.connection.has_filters())
        filter_model = self._link.resource_filter_model
        self.assertEqual(filter_model.rowCount(), 1)
        self.assertEqual(filter_model.columnCount(), 1)
        index = filter_model.index(0, 0)
        self.assertEqual(index.data(), url)
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

    def test_tool_filter_gets_added_to_filter_model(self):
        url = "sqlite:///" + os.path.join(self._temp_dir.name, "db.sqlite")
        db_map = DiffDatabaseMapping(url, create=True)
        import_tools(db_map, ("tool",))
        db_map.commit_session("Add test data.")
        db_map.connection.close()
        self._link.handle_dag_changed([database_resource("provider", url)])
        self._link.refresh_resource_filter_model()
        self.assertTrue(self._link.connection.has_filters())
        filter_model = self._link.resource_filter_model
        self.assertEqual(filter_model.rowCount(), 1)
        self.assertEqual(filter_model.columnCount(), 1)
        index = filter_model.index(0, 0)
        self.assertEqual(index.data(), url)
        root_item = filter_model.itemFromIndex(index)
        self.assertEqual(root_item.rowCount(), 2)
        self.assertEqual(root_item.columnCount(), 1)
        tool_title_item = root_item.child(1, 0)
        self.assertEqual(tool_title_item.index().data(), "Tool filter")
        self.assertEqual(tool_title_item.rowCount(), 2)
        self.assertEqual(tool_title_item.columnCount(), 1)
        tool_item = tool_title_item.child(0, 0)
        self.assertEqual(tool_item.index().data(), "Select all")
        tool_item = tool_title_item.child(1, 0)
        self.assertEqual(tool_item.index().data(), "tool")

    def test_toggle_scenario_filter(self):
        url = "sqlite:///" + os.path.join(self._temp_dir.name, "db.sqlite")
        db_map = DiffDatabaseMapping(url, create=True)
        import_scenarios(db_map, (("scenario", True),))
        db_map.commit_session("Add test data.")
        db_map.connection.close()
        self._link.handle_dag_changed([database_resource("provider", url)])
        self._link.refresh_resource_filter_model()
        filter_model = self._link.resource_filter_model
        filter_model.set_online(url, "scenario_filter", {1: True})
        self.assertEqual(self._link.connection.resource_filters, {url: {"scenario_filter": {1: True}}})

    def test_toggle_tool_filter(self):
        url = "sqlite:///" + os.path.join(self._temp_dir.name, "db.sqlite")
        db_map = DiffDatabaseMapping(url, create=True)
        import_tools(db_map, ("tool",))
        db_map.commit_session("Add test data.")
        db_map.connection.close()
        self._link.handle_dag_changed([database_resource("provider", url)])
        self._link.refresh_resource_filter_model()
        filter_model = self._link.resource_filter_model
        filter_model.set_online(url, "tool_filter", {1: True})
        self.assertEqual(self._link.connection.resource_filters, {url: {"tool_filter": {1: True}}})


if __name__ == "__main__":
    unittest.main()
