######################################################################################################################
# Copyright (C) 2017-2020 Spine project consortium
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
from unittest.mock import patch
from PySide2.QtCore import QEvent, QPoint, Qt
from PySide2.QtGui import QColor
from PySide2.QtWidgets import QApplication, QGraphicsSceneMouseEvent
from spinedb_api import DiffDatabaseMapping, import_scenarios, import_tools
from spinedb_api.filters.tools import filter_config
from spine_engine.project_item.project_item_resource import ProjectItemResource
from spinetoolbox.graphics_items import ExclamationIcon, Link, ProjectItemIcon, RankIcon
from spinetoolbox.metaobject import MetaObject
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
        link = Link(self._toolbox, source_icon.conn_button("bottom"), target_icon.conn_button("bottom"))
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
        self._toolbox = create_toolboxui_with_project(self._temp_dir.name)
        source_item_icon = ProjectItemIcon(self._toolbox, "", QColor(Qt.gray), QColor(Qt.green))
        source_item_icon.update_name_item("source icon")
        destination_item_icon = ProjectItemIcon(self._toolbox, "", QColor(Qt.gray), QColor(Qt.green))
        destination_item_icon.update_name_item("destination icon")
        self._link = Link(self._toolbox, source_item_icon.conn_button(), destination_item_icon.conn_button())

    def tearDown(self):
        clean_up_toolbox(self._toolbox)
        self._temp_dir.cleanup()

    def test_empty_filter_stacks(self):
        self.assertEqual(self._link.filter_stacks(), {})

    def test_scenario_filter_gets_added_to_filter_model(self):
        with TemporaryDirectory() as temp_dir:
            url = "sqlite:///" + os.path.join(temp_dir, "db.sqlite")
            db_map = DiffDatabaseMapping(url, create=True)
            import_scenarios(db_map, (("scenario", True),))
            db_map.commit_session("Add test data.")
            db_map.connection.close()
            self._link.handle_dag_changed([ProjectItemResource(MetaObject("provider", ""), "database", url)])
            self.assertEqual(self._link.filter_stacks(), {})
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
            self._toolbox.db_mngr.close_all_sessions()

    def test_tool_filter_gets_added_to_filter_model(self):
        with TemporaryDirectory() as temp_dir:
            url = "sqlite:///" + os.path.join(temp_dir, "db.sqlite")
            db_map = DiffDatabaseMapping(url, create=True)
            import_tools(db_map, ("tool",))
            db_map.commit_session("Add test data.")
            db_map.connection.close()
            self._link.handle_dag_changed([ProjectItemResource(MetaObject("provider", ""), "database", url)])
            self.assertEqual(self._link.filter_stacks(), {})
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
            self._toolbox.db_mngr.close_all_sessions()

    def test_toggle_scenario_filter(self):
        with TemporaryDirectory() as temp_dir:
            url = "sqlite:///" + os.path.join(temp_dir, "db.sqlite")
            db_map = DiffDatabaseMapping(url, create=True)
            import_scenarios(db_map, (("scenario", True),))
            db_map.commit_session("Add test data.")
            db_map.connection.close()
            self._link.handle_dag_changed([ProjectItemResource(MetaObject("provider", ""), "database", url)])
            self._link.refresh_resource_filter_model()
            filter_model = self._link.resource_filter_model
            scenario_item = filter_model.itemFromIndex(filter_model.index(0, 0)).child(0, 0).child(0, 0)
            filter_model.toggle_checked_state(scenario_item.index())
            self.assertEqual(
                self._link.filter_stacks(),
                {(url, "destination icon"): [(filter_config("scenario_filter", "scenario"),)]},
            )
            self._toolbox.db_mngr.close_all_sessions()

    def test_toggle_tool_filter(self):
        with TemporaryDirectory() as temp_dir:
            url = "sqlite:///" + os.path.join(temp_dir, "db.sqlite")
            db_map = DiffDatabaseMapping(url, create=True)
            import_tools(db_map, ("tool",))
            db_map.commit_session("Add test data.")
            db_map.connection.close()
            self._link.handle_dag_changed([ProjectItemResource(MetaObject("provider", ""), "database", url)])
            self._link.refresh_resource_filter_model()
            filter_model = self._link.resource_filter_model
            scenario_item = filter_model.itemFromIndex(filter_model.index(0, 0)).child(1, 0).child(0, 0)
            filter_model.toggle_checked_state(scenario_item.index())
            self.assertEqual(
                self._link.filter_stacks(), {(url, "destination icon"): [(filter_config("tool_filter", "tool"),)]}
            )
            self._toolbox.db_mngr.close_all_sessions()


if __name__ == "__main__":
    unittest.main()
