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
    with mock.patch("spinetoolbox.ui_main.QSettings.value") as mock_qsettings_value:
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
    ):
        mock_qsettings_value.side_effect = qsettings_value_side_effect
        toolbox = ToolboxUI()
        toolbox.create_project("UnitTest Project", "Project for unit tests.", project_dir)
    return toolbox


def clean_up_toolbox(toolbox):
    """Cleans up toolbox and project."""
    if toolbox.project():
        while toolbox.project().is_busy():
            QApplication.processEvents()
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


def add_ds(project, name, x=0, y=0):
    """Helper function to create a Data Store to given project with given name and coordinates."""
    item = {name: {"type": "Data Store", "description": "", "url": dict(), "x": x, "y": y}}
    project.add_project_items(item)


def add_dc(project, name, x=0, y=0):
    """Helper function to create a Data Connection to given project with given name and coordinates."""
    item = {name: {"type": "Data Connection", "description": "", "references": list(), "x": x, "y": y}}
    project.add_project_items(item)


def add_tool(project, name, tool_spec="", x=0, y=0):
    """Helper function to add a Tool to given project."""
    item = {
        name: {"type": "Tool", "description": "", "specification": tool_spec, "execute_in_work": False, "x": x, "y": y}
    }
    project.add_project_items(item)


def add_view(project, name, x=0, y=0):
    """Helper function to add a View to given project."""
    item = {name: {"type": "View", "description": "", "x": x, "y": y}}
    project.add_project_items(item)


def add_importer(project, name, x=0, y=0):
    """Helper function to add an Importer View to given project."""
    item = {name: {"type": "Importer", "description": "", "mappings": None, "x": x, "y": y}}
    project.add_project_items(item)


def add_gdx_exporter(project, name, x=0, y=0):
    """Helper function to add an gdx exporter to given project."""
    item = {name: {"type": "GdxExporter", "description": "", "x": x, "y": y, "settings_packs": None}}
    project.add_project_items(item)
