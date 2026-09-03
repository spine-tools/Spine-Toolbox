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

from tempfile import TemporaryDirectory
from unittest.mock import MagicMock, patch
from PySide6.QtCore import QEvent, QPoint, Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QGraphicsSceneMouseEvent
import pytest
from spine_engine.project_item.project_item_resource import database_resource
from spinedb_api import import_scenarios
from spinetoolbox.link import Link
from spinetoolbox.project_commands import MoveIconCommand
from spinetoolbox.project_item.logging_connection import LoggingConnection
from spinetoolbox.project_item_icon import ExclamationIcon, ProjectItemIcon, RankIcon
from tests.mock_helpers import (
    TestCaseWithQApplication,
    add_view,
    clean_up_toolbox,
    create_toolboxui_with_project,
)


class TestProjectItemIcon:
    def test_init(self, spine_toolbox_with_project):
        icon = ProjectItemIcon(spine_toolbox_with_project, ":/icons/home.svg", QColor(Qt.GlobalColor.gray))
        assert icon.name() == ""
        assert icon.x() == 0
        assert icon.y() == 0
        assert icon.incoming_links() == []
        assert icon.outgoing_connection_links() == []

    def test_finalize(self, spine_toolbox_with_project):
        icon = ProjectItemIcon(spine_toolbox_with_project, ":/icons/home.svg", QColor(Qt.GlobalColor.gray))
        icon.finalize("new name", -43, 314)
        assert icon.name() == "new name"
        assert icon.x() == -43
        assert icon.y() == 314

    def test_conn_button(self, spine_toolbox_with_project):
        icon = ProjectItemIcon(spine_toolbox_with_project, ":/icons/home.svg", QColor(Qt.GlobalColor.gray))
        button = icon.conn_button("left")
        assert button.position == "left"
        button = icon.conn_button("right")
        assert button.position == "right"
        button = icon.conn_button("bottom")
        assert button.position == "bottom"

    def test_outgoing_and_incoming_links(self, spine_toolbox_with_project):
        toolbox = spine_toolbox_with_project
        source_icon = ProjectItemIcon(toolbox, ":/icons/home.svg", QColor(Qt.GlobalColor.gray))
        target_icon = ProjectItemIcon(toolbox, ":/icons/home.svg", QColor(Qt.GlobalColor.gray))
        toolbox.project().get_item = MagicMock()
        connection = LoggingConnection("source item", "bottom", "destination item", "bottom", toolbox=toolbox)
        link = Link(toolbox, source_icon.conn_button("bottom"), target_icon.conn_button("bottom"), connection)
        link.src_connector.links.append(link)
        link.dst_connector.links.append(link)
        assert source_icon.outgoing_connection_links() == [link]
        assert target_icon.incoming_links() == [link]

    def test_drag_icon(self, spine_toolbox_with_project):
        toolbox = spine_toolbox_with_project
        item = add_view(toolbox.project(), toolbox.item_factories, "View")
        icon = item.get_icon()
        assert icon.x() == 0.0
        assert icon.y() == 0.0
        icon.mousePressEvent(QGraphicsSceneMouseEvent(QEvent.GraphicsSceneMousePress))
        icon.mouseMoveEvent(QGraphicsSceneMouseEvent(QEvent.GraphicsSceneMouseMove))
        icon.moveBy(99.0, 88.0)
        icon.mouseReleaseEvent(QGraphicsSceneMouseEvent(QEvent.GraphicsSceneMouseRelease))
        assert icon.x() == 99.0
        assert icon.y() == 88.0
        assert toolbox.undo_stack.count() == 1
        move_command = toolbox.undo_stack.command(0)
        assert isinstance(move_command, MoveIconCommand)

    def test_context_menu_event(self, spine_toolbox_with_project):
        item = add_view(spine_toolbox_with_project.project(), spine_toolbox_with_project.item_factories, "View")
        icon = item.get_icon()
        with patch("spinetoolbox.ui_main.ToolboxUI.show_project_or_item_context_menu") as mock_show_menu:
            mock_show_menu.return_value = True
            icon.contextMenuEvent(QGraphicsSceneMouseEvent(QEvent.Type.ContextMenu))
            mock_show_menu.assert_called()


class TestExclamationIcon(TestCaseWithQApplication):
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


class TestRankIcon(TestCaseWithQApplication):
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


class TestLink:
    @pytest.fixture()
    def link(self, spine_toolbox_with_project):
        toolbox = spine_toolbox_with_project
        source_item_icon = ProjectItemIcon(toolbox, ":/icons/home.svg", QColor(Qt.GlobalColor.gray))
        source_item_icon.update_name_item("source icon")
        destination_item_icon = ProjectItemIcon(toolbox, ":/icons/home.svg", QColor(Qt.GlobalColor.gray))
        destination_item_icon.update_name_item("destination icon")
        project = toolbox.project()
        project.get_item = MagicMock()
        connection = LoggingConnection("source icon", "right", "destination icon", "left", toolbox=toolbox)
        link = connection.link = Link(
            toolbox, source_item_icon.conn_button(), destination_item_icon.conn_button(), connection
        )
        project.find_connection = MagicMock()
        project.find_connection.return_value = connection
        link.update_icons = MagicMock()
        return link

    def test_scenario_filter_gets_added_to_filter_model(self, db_map_generator, link):
        db_map = db_map_generator()
        with db_map:
            import_scenarios(db_map, (("scenario", True),))
            db_map.commit_session("Add test data.")
        link.connection.receive_resources_from_source(
            [database_resource("provider", db_map.db_url, "my_database", filterable=True)]
        )
        link.connection.refresh_resource_filter_model()
        filter_model = link.connection.resource_filter_model
        assert filter_model.rowCount() == 1
        assert filter_model.columnCount() == 1
        index = filter_model.index(0, 0)
        assert index.data() == "my_database"
        root_item = filter_model.itemFromIndex(index)
        assert root_item.rowCount() == 2
        assert root_item.columnCount() == 1
        scenario_title_item = root_item.child(0, 0)
        assert scenario_title_item.index().data() == "Scenario filter"
        assert scenario_title_item.rowCount() == 2
        assert scenario_title_item.columnCount() == 1
        scenario_item = scenario_title_item.child(0, 0)
        assert scenario_item.index().data() == "Select all"
        scenario_item = scenario_title_item.child(1, 0)
        assert scenario_item.index().data() == "scenario"
        alternative_title_item = root_item.child(1, 0)
        assert alternative_title_item.index().data() == "Alternative filter"
        assert alternative_title_item.rowCount() == 2
        assert alternative_title_item.columnCount() == 1
        alternative_item = alternative_title_item.child(0, 0)
        assert alternative_item.index().data() == "Select all"
        alternative_item = alternative_title_item.child(1, 0)
        assert alternative_item.index().data() == "Base"
        scenario_index = filter_model.indexFromItem(scenario_item)
        assert link.connection.online_filters("my_database", "scenario_filter") == {"scenario": True}
        filter_model.setData(scenario_index, Qt.CheckState.Unchecked.value, role=Qt.ItemDataRole.CheckStateRole)
        assert link.connection.online_filters("my_database", "scenario_filter") == {"scenario": False}
        assert link.connection.online_filters("my_database", "alternative_filter") == {"Base": True}

    def test_toggle_scenario_filter(self, db_map_generator, link):
        db_map = db_map_generator()
        with db_map:
            import_scenarios(db_map, (("scenario", True),))
            db_map.commit_session("Add test data.")
        link.connection.receive_resources_from_source([database_resource("provider", db_map.db_url, filterable=True)])
        link.connection.refresh_resource_filter_model()
        assert link.connection.online_filters(db_map.db_url, "scenario_filter") == {"scenario": True}
        filter_model = link.connection.resource_filter_model
        filter_model.set_online(db_map.db_url, "scenario_filter", {"scenario": False})
        assert link.connection.online_filters(db_map.db_url, "scenario_filter") == {"scenario": False}
