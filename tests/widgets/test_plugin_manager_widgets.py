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

"""Unit tests for the classes in ``plugin_manager_widgets`` module."""
from PySide6.QtWidgets import QWidget
from spinetoolbox.widgets.plugin_manager_widgets import InstallPluginDialog, ManagePluginsDialog
from tests.mock_helpers import TestCaseWithQApplication


class TestPluginManagerWidgets(TestCaseWithQApplication):
    def test_install_plugins_dialog(self):
        parent = QWidget()
        d = InstallPluginDialog(parent)
        d.populate_list(["Plugin1", "Plugin2"])
        d.close()
        parent.deleteLater()

    def test_manage_plugins_dialog(self):
        parent = QWidget()
        d = ManagePluginsDialog(parent)
        d.populate_list([("Plugin", True)])
        d._emit_item_removed("Plugin")
        d.close()
        parent.deleteLater()
