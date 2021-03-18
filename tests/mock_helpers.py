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
Classes and functions that can be shared among unit test modules.

:author: P. Savolainen (VTT)
:date:   18.4.2019
"""

from unittest import mock
from PySide2.QtWidgets import QApplication
import spinetoolbox.resources_icons_rc  # pylint: disable=unused-import
from spinetoolbox.ui_main import ToolboxUI


def create_toolboxui():
    """Returns ToolboxUI, where QSettings among others has been mocked."""
    with mock.patch("spinetoolbox.plugin_manager.PluginManager.load_plugins"), mock.patch(
        "spinetoolbox.ui_main.QSettings.value"
    ) as mock_qsettings_value:
        mock_qsettings_value.side_effect = qsettings_value_side_effect
        toolbox = ToolboxUI()
    return toolbox


def create_project(toolbox, project_dir):
    """Creates a project for the given ToolboxUI."""
    with mock.patch("spinetoolbox.ui_main.ToolboxUI.update_recent_projects"), mock.patch(
        "spinetoolbox.widgets.open_project_widget.OpenProjectDialog.update_recents"
    ):
        toolbox.create_project("UnitTest Project", "Project for unit tests.", project_dir)


def create_toolboxui_with_project(project_dir):
    """Returns ToolboxUI with a project instance where
    QSettings among others has been mocked."""
    with mock.patch("spinetoolbox.ui_main.ToolboxUI.save_project"), mock.patch(
        "spinetoolbox.ui_main.ToolboxUI.update_recent_projects"
    ), mock.patch("spinetoolbox.ui_main.QSettings.value") as mock_qsettings_value, mock.patch(
        "spinetoolbox.widgets.open_project_widget.OpenProjectDialog.update_recents"
    ), mock.patch(
        "spinetoolbox.plugin_manager.PluginManager.load_plugins"
    ):
        mock_qsettings_value.side_effect = qsettings_value_side_effect
        toolbox = ToolboxUI()
        toolbox.create_project("UnitTest Project", "Project for unit tests.", project_dir)
    return toolbox


def clean_up_toolbox(toolbox):
    """Cleans up toolbox and project."""
    if toolbox.project():
        toolbox.project().tear_down()
        toolbox.project().deleteLater()
    toolbox.db_mngr.close_all_sessions()
    toolbox.db_mngr.clean_up()
    toolbox.project_item_model.remove_leaves()
    toolbox.undo_stack.deleteLater()
    toolbox.deleteLater()


# noinspection PyMethodMayBeStatic, PyPep8Naming,SpellCheckingInspection
def qsettings_value_side_effect(key, defaultValue="0"):
    """Side effect for calling QSettings.value() method. Used to
    override default value for key 'appSettings/openPreviousProject'
    so that previous project is not opened in background when
    ToolboxUI is instantiated.

    Args:
        key (str): Key to read
        defaultValue (QVariant): Default value if key is missing
    """
    if key == "appSettings/openPreviousProject":
        return "0"  # Do not open previos project when instantiating ToolboxUI
    return defaultValue


def add_ds(project, name, x=0.0, y=0.0):
    """Helper function to create a Data Store to given project.

    Args:
        project (SpineToolboxProject): project where to add the item
        name (str): item's name
        x (float): item's x coordinate
        y (float): item's y coordinate

    Returns:
        DataStore: added project item
    """
    item_dict = {name: {"type": "Data Store", "description": "", "url": dict(), "x": x, "y": y}}
    project.add_project_items(item_dict)
    return project.get_item(name)


def add_dc(project, name, x=0, y=0):
    """Helper function to create a Data Connection to given project.

    Args:
        project (SpineToolboxProject): project where to add the item
        name (str): item's name
        x (float): item's x coordinate
        y (float): item's y coordinate

    Returns:
        DataConnection: added project item
    """
    item_dict = {name: {"type": "Data Connection", "description": "", "references": list(), "x": x, "y": y}}
    project.add_project_items(item_dict)
    return project.get_item(name)


def add_tool(project, name, tool_spec="", x=0, y=0):
    """Helper function to create a Tool to given project.

    Args:
        project (SpineToolboxProject): project where to add the item
        name (str): item's name
        tool_spec (str): Tool specification's name
        x (float): item's x coordinate
        y (float): item's y coordinate

    Returns:
        Tool: added project item
    """
    item = {
        name: {"type": "Tool", "description": "", "specification": tool_spec, "execute_in_work": False, "x": x, "y": y}
    }
    project.add_project_items(item)
    return project.get_item(name)


def add_view(project, name, x=0, y=0):
    """Helper function to create a View to given project.

    Args:
        project (SpineToolboxProject): project where to add the item
        name (str): item's name
        x (float): item's x coordinate
        y (float): item's y coordinate

    Returns:
        View: added project item
    """
    item = {name: {"type": "View", "description": "", "x": x, "y": y}}
    project.add_project_items(item)
    return project.get_item(name)


def add_importer(project, name, x=0, y=0):
    """Helper function to create an Importer to given project.

    Args:
        project (SpineToolboxProject): project where to add the item
        name (str): item's name
        x (float): item's x coordinate
        y (float): item's y coordinate

    Returns:
        Importer: added project item
    """
    item = {name: {"type": "Importer", "description": "", "specification": "", "x": x, "y": y}}
    project.add_project_items(item)
    return project.get_item(name)


def add_gimlet(project, name, x=0, y=0):
    """Helper function to create a Gimlet to given project.

    Args:
        project (SpineToolboxProject): project where to add the item
        name (str): item's name
        x (float): item's x coordinate
        y (float): item's y coordinate

    Returns:
        Gimlet: added project item
    """
    item = {name: {"type": "Gimlet", "description": "", "x": x, "y": y}}
    project.add_project_items(item)
    return project.get_item(name)


def add_data_transformer(project, name, x=0, y=0):
    """Helper function to create a Data Transformer to given project.

    Args:
        project (SpineToolboxProject): project where to add the item
        name (str): item's name
        x (float): item's x coordinate
        y (float): item's y coordinate

    Returns:
        DataTransformer: added project item
    """
    item = {name: {"type": "Data Transformer", "description": "", "x": x, "y": y}}
    project.add_project_items(item)
    return project.get_item(name)


def add_exporter(project, name, x=0, y=0):
    """Helper function to create an Exporter to given project.

    Args:
        project (SpineToolboxProject): project where to add the item
        name (str): item's name
        x (float): item's x coordinate
        y (float): item's y coordinate

    Returns:
        Exporter: added project item
    """
    item = {name: {"type": "Exporter", "description": "", "x": x, "y": y, "specification": None}}
    project.add_project_items(item)
    return project.get_item(name)


def add_gdx_exporter(project, name, x=0, y=0):
    """Helper function to create a GdxExporter to given project.

    Args:
        project (SpineToolboxProject): project where to add the item
        name (str): item's name
        x (float): item's x coordinate
        y (float): item's y coordinate

    Returns:
        GdxExporter: added project item
    """
    item = {name: {"type": "GdxExporter", "description": "", "x": x, "y": y, "settings_packs": None}}
    project.add_project_items(item)
    return project.get_item(name)


class _FakeSignal:
    """A fake Signal that just remembers all slots it's connected to."""

    def __init__(self):
        self.slots = []
        self.connect = self.slots.append


class _FakeQByteArray:
    """A fake QByteArray."""

    def __init__(self, data):
        self._data = data

    def data(self):
        return self._data


class MockInstantQProcess(mock.Mock):
    """A mock QProcess that calls all slots connected to ``finished`` as soon as ``start()`` is called."""

    def __init__(self, *args, finished_args=(), stdout=b"", stderr=b"", **kwargs):
        """
        Args:
            finished_args (tuple): A tuple (exit_code, exit_status) to pass as arguments to ``finished`` slots
        """
        super().__init__(*args, **kwargs)
        self._finished_args = finished_args
        self._stdout = stdout
        self._stderr = stderr
        self.finished = _FakeSignal()

    def readAllStandardOutput(self):
        return _FakeQByteArray(self._stdout)

    def readAllStandardError(self):
        return _FakeQByteArray(self._stderr)

    def start(self, *args, **kwargs):
        for slot in self.finished.slots:
            slot(*self._finished_args)
