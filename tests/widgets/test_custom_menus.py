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

"""Unit tests for the ``custom_menus`` module."""

from unittest import mock
from PySide6.QtWidgets import QMessageBox
from spinetoolbox.widgets.custom_menus import RecentProjectsPopupMenu
from spinetoolbox.helpers import update_recent_projects
from spinetoolbox.config import LATEST_PROJECT_VERSION


class TestRecentProjectsPopUpMenu:
    def test_recent_projects_with_different_versions(self, parent_widget_with_settings):
        menu = self.make_menu_with_projects(parent_widget_with_settings)
        actions = menu.actions()
        # Test in LIFO order
        assert actions[0].text() == "unknown"
        assert actions[0].toolTip() == "/toolbox/unknown"
        assert "future" in actions[1].text()
        assert "requires newer Spine Toolbox" in actions[1].toolTip()
        assert actions[2].text() == "old"
        assert "upgrades to" in actions[2].toolTip()
        assert actions[3].text() == "current"
        assert "(current)" in actions[3].toolTip()
        assert actions[4].text() == ""  # separator
        assert actions[5].text() == "Clear"

    def test_clear_menu(self, application, parent_widget_with_settings):
        update_recent_projects(parent_widget_with_settings.qsettings(), "A", "/toolbox/A")
        update_recent_projects(parent_widget_with_settings.qsettings(), "B", "/toolbox/B")
        menu = RecentProjectsPopupMenu(parent_widget_with_settings)
        assert len(menu.actions()) == 4
        assert menu.actions()[0].text() == "B"
        assert menu.actions()[1].text() == "A"
        assert menu.actions()[2].text() == ""
        assert menu.actions()[3].text() == "Clear"
        with mock.patch("spinetoolbox.helpers.QMessageBox.exec") as mock_exec:
            mock_exec.return_value = QMessageBox.StandardButton.Yes
            menu.actions()[3].trigger()  # Clicks Clear button
        menu.close()
        menu = RecentProjectsPopupMenu(parent_widget_with_settings)
        assert len(menu.actions()) == 2
        assert menu.actions()[0].text() == ""
        assert menu.actions()[1].text() == "Clear"

    def test_open_project(self, application, parent_widget_with_settings):
        menu = self.make_menu_with_projects(parent_widget_with_settings)
        parent_widget_with_settings.open_project = mock.Mock()
        with (
            mock.patch("spinetoolbox.widgets.custom_menus.os.path.exists", return_value=True),
            mock.patch("spinetoolbox.widgets.custom_menus.QMessageBox.warning") as mock_warning,
        ):
            menu.actions()[0].trigger()  # Trigger unknown project
            assert mock_warning.call_count == 1
            parent_widget_with_settings.open_project.assert_not_called()
            menu.actions()[1].trigger()  # Trigger future project
            assert mock_warning.call_count == 2
            parent_widget_with_settings.open_project.assert_not_called()
            # Project already open
            project = mock.Mock()
            project.project_dir = "/toolbox/current"
            parent_widget_with_settings.project = mock.Mock(return_value=project)
            parent_widget_with_settings.msg = mock.Mock()
            menu.actions()[3].trigger()  # Trigger current project
            parent_widget_with_settings.msg.emit.assert_called_once_with("Project already open")
            parent_widget_with_settings.open_project.assert_not_called()
            # Project not already open
            parent_widget_with_settings.open_project.reset_mock()
            project.project_dir = "/something/else"
            parent_widget_with_settings.project = mock.Mock(return_value=project)
            parent_widget_with_settings.msg = mock.Mock()
            menu.actions()[3].trigger()
            parent_widget_with_settings.open_project.assert_called_once_with("/toolbox/current")

    @staticmethod
    def make_menu_with_projects(parent_widget_with_settings):
        update_recent_projects(parent_widget_with_settings.qsettings(), "current", "/toolbox/current")
        update_recent_projects(parent_widget_with_settings.qsettings(), "old", "/toolbox/old")
        update_recent_projects(parent_widget_with_settings.qsettings(), "future", "/toolbox/future")
        update_recent_projects(parent_widget_with_settings.qsettings(), "unknown", "/toolbox/unknown")
        versions = {
            "/toolbox/current": LATEST_PROJECT_VERSION,
            "/toolbox/old": LATEST_PROJECT_VERSION - 1,
            "/toolbox/future": LATEST_PROJECT_VERSION + 1,
        }

        def mock_isdir(path):
            return path != "/toolbox/unknown"

        def mock_load_project_dict(path):
            return {"project": {"version": versions[path]}}

        with (
            mock.patch("spinetoolbox.widgets.custom_menus.os.path.isdir", side_effect=mock_isdir),
            mock.patch("spinetoolbox.widgets.custom_menus.load_project_dict", side_effect=mock_load_project_dict),
        ):
            menu = RecentProjectsPopupMenu(parent_widget_with_settings)
        return menu
