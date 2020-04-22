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
Classes and functions that can be shared among unit test modules.

:author: P. Savolainen (VTT)
:date:   18.4.2019
"""

import os
import os.path
import shutil
from unittest import mock
from PySide2.QtWidgets import QWidget
import spinetoolbox.resources_icons_rc  # pylint: disable=unused-import
from spinetoolbox.ui_main import ToolboxUI


class MockQWidget(QWidget):
    """Dummy QWidget for mocking test_push_vars method in PythonReplWidget class."""

    # noinspection PyMethodMayBeStatic
    def test_push_vars(self):
        return True


def create_toolboxui():
    """Returns ToolboxUI, where QSettings among others has been mocked."""
    with mock.patch("spinetoolbox.ui_main.JuliaREPLWidget") as mock_julia_repl, mock.patch(
        "spinetoolbox.ui_main.PythonReplWidget"
    ) as mock_python_repl, mock.patch("spinetoolbox.ui_main.QSettings.value") as mock_qsettings_value:
        # Replace Julia REPL Widget with a QWidget so that the DeprecationWarning from qtconsole is not printed
        mock_julia_repl.return_value = QWidget()
        mock_python_repl.return_value = MockQWidget()
        mock_qsettings_value.side_effect = qsettings_value_side_effect
        toolbox = ToolboxUI()
    return toolbox


def create_project(toolbox):
    """Creates a project for the given ToolboxUI."""
    with mock.patch("spinetoolbox.ui_main.ToolboxUI.save_project") as mock_save_project, mock.patch(
        "spinetoolbox.project.create_dir"
    ) as mock_create_dir, mock.patch(
        "spinetoolbox.ui_main.ToolboxUI.update_recent_projects"
    ) as mock_upd_rec_projects, mock.patch(
        "spinetoolbox.widgets.open_project_widget.OpenProjectDialog.update_recents"
    ) as mock_upd_recents:
        project_dir = os.path.abspath(
            os.path.join(os.curdir, "tests", "test_resources", "This dir should not exist after tests")
        )
        toolbox.create_project("UnitTest Project", "Project for unit tests.", project_dir)
    return


def create_toolboxui_with_project():
    """Returns ToolboxUI with a project instance where
    QSettings among others has been mocked."""
    with mock.patch("spinetoolbox.ui_main.JuliaREPLWidget") as mock_julia_repl, mock.patch(
        "spinetoolbox.ui_main.PythonReplWidget"
    ) as mock_python_repl, mock.patch("spinetoolbox.project.create_dir") as mock_create_dir, mock.patch(
        "spinetoolbox.ui_main.ToolboxUI.save_project"
    ) as mock_save_project, mock.patch(
        "spinetoolbox.ui_main.ToolboxUI.update_recent_projects"
    ) as mock_update_recents, mock.patch(
        "spinetoolbox.ui_main.QSettings.value"
    ) as mock_qsettings_value, mock.patch(
        "spinetoolbox.widgets.open_project_widget.OpenProjectDialog.update_recents"
    ) as mock_upd_recents:
        # Replace Julia REPL Widget with a QWidget so that the DeprecationWarning from qtconsole is not printed
        mock_julia_repl.return_value = QWidget()
        mock_python_repl.return_value = MockQWidget()
        mock_qsettings_value.side_effect = qsettings_value_side_effect
        toolbox = ToolboxUI()
        project_dir = os.path.abspath(
            os.path.join(os.curdir, "tests", "test_resources", "This dir should not exist after tests")
        )
        toolbox.create_project("UnitTest Project", "Project for unit tests.", project_dir)
    return toolbox


def clean_up_toolboxui_with_project(toolbox):
    """Removes project directories and work directory."""
    project_dir = toolbox.project().project_dir
    if os.path.exists(project_dir):
        shutil.rmtree(project_dir)
    work_dir = toolbox.work_dir
    if os.path.exists(work_dir):
        shutil.rmtree(work_dir)
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
    # logging.debug("in qsettings_value_side_effect. key:{0}, defaultValue:{1}".format(key, defaultValue))
    if key == "appSettings/openPreviousProject":
        return "0"  # Do not open previos project when instantiating ToolboxUI
    return defaultValue


def add_ds(project, name, x=0, y=0):
    """Helper function to create a Data Store to given project with given name and coordinates."""
    item = dict(name=name, description="", url=dict(), x=x, y=y)
    # This mocks create_dir in both project_item.py and in data_store.py
    with mock.patch("spinetoolbox.project_item.create_dir") as mock_create_dir, mock.patch(
        "spinetoolbox.project_items.data_store.data_store.create_dir"
    ) as mock_create_dir2:
        project.add_project_items("Data Stores", item)
    return


def add_dc(project, name, x=0, y=0):
    """Helper function to create a Data Connection to given project with given name and coordinates."""
    item = dict(name=name, description="", references=list(), x=x, y=y)
    with mock.patch("spinetoolbox.project_item.create_dir") as mock_create_dir:
        project.add_project_items("Data Connections", item)
    return


def add_tool(project, name, tool_spec="", x=0, y=0):
    """Helper function to add a Tool to given project."""
    item = dict(name=name, description="", tool=tool_spec, execute_in_work=False, x=x, y=y)
    with mock.patch("spinetoolbox.project_item.create_dir"):
        project.add_project_items("Tools", item)
    return


def add_view(project, name, x=0, y=0):
    """Helper function to add a View to given project."""
    item = dict(name=name, description="", x=x, y=y)
    with mock.patch("spinetoolbox.project_item.create_dir"):
        project.add_project_items("Views", item)
    return


def add_importer(project, name, x=0, y=0):
    """Helper function to add an Importer View to given project."""
    item = dict(name=name, description="", mappings=None, x=x, y=y)
    # This mocks create_dir in both project_item.py and in importer.py
    with mock.patch("spinetoolbox.project_item.create_dir") as mock_create_dir, mock.patch(
        "spinetoolbox.project_items.importer.importer.create_dir"
    ) as mock_create_dir2:
        project.add_project_items("Importers", item)
    return


def add_exporter(project, name, x=0, y=0):
    """Helper function to add an exporter to given project."""
    item = dict(name=name, description="", x=x, y=y, settings_packs=None)
    with mock.patch("spinetoolbox.project_item.create_dir"):
        project.add_project_items("Exporters", item)
    return
