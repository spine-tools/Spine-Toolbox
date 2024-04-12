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

"""Classes and functions that can be shared among unit test modules."""
from contextlib import contextmanager
from unittest import mock
from PySide6.QtCore import QModelIndex, Qt
from PySide6.QtWidgets import QApplication
import spinetoolbox.resources_icons_rc  # pylint: disable=unused-import
from spinetoolbox.ui_main import ToolboxUI
from spinetoolbox.spine_db_manager import SpineDBManager


def create_toolboxui():
    """Returns ToolboxUI, where QSettings among others has been mocked."""
    with mock.patch("spinetoolbox.plugin_manager.PluginManager.load_installed_plugins"), mock.patch(
        "spinetoolbox.ui_main.QSettings.value"
    ) as mock_qsettings_value:
        mock_qsettings_value.side_effect = qsettings_value_side_effect
        toolbox = ToolboxUI()
    return toolbox


def create_project(toolbox, project_dir):
    """Creates a project for the given ToolboxUI."""
    with mock.patch("spinetoolbox.ui_main.ToolboxUI.update_recent_projects"), mock.patch(
        "spinetoolbox.ui_main.QSettings.setValue"
    ), mock.patch("spinetoolbox.ui_main.QSettings.sync"):
        toolbox.create_project(project_dir)


def create_toolboxui_with_project(project_dir):
    """Returns ToolboxUI with a project instance where
    QSettings among others has been mocked."""
    with mock.patch("spinetoolbox.ui_main.ToolboxUI.save_project"), mock.patch(
        "spinetoolbox.ui_main.QSettings.value"
    ) as mock_qsettings_value, mock.patch("spinetoolbox.ui_main.QSettings.setValue"), mock.patch(
        "spinetoolbox.ui_main.QSettings.sync"
    ), mock.patch(
        "spinetoolbox.plugin_manager.PluginManager.load_installed_plugins"
    ), mock.patch(
        "spinetoolbox.ui_main.QScrollArea.setWidget"
    ):
        mock_qsettings_value.side_effect = qsettings_value_side_effect
        toolbox = ToolboxUI()
        toolbox.create_project(project_dir)
    return toolbox


def clean_up_toolbox(toolbox):
    """Cleans up toolbox and project."""
    with mock.patch("spinetoolbox.ui_main.QSettings.value") as mock_qsettings_value:
        mock_qsettings_value.side_effect = qsettings_value_side_effect
        if toolbox.project():
            toolbox.close_project(ask_confirmation=False)
            QApplication.processEvents()  # Makes sure Design view animations finish properly.
            mock_qsettings_value.assert_called()  # The call in _shutdown_engine_kernels()
    toolbox.db_mngr.close_all_sessions()
    toolbox.db_mngr.clean_up()
    toolbox.db_mngr = None
    # Delete undo stack explicitly to prevent emitting certain signals well after ToolboxUI has been destroyed.
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
        return "0"  # Do not open previous project when instantiating ToolboxUI
    elif key == "engineSettings/remoteExecutionEnabled":
        return "false"
    return defaultValue


def add_ds(project, item_factories, name, x=0.0, y=0.0):
    """Helper function to create a Data Store to given project.

    Args:
        project (SpineToolboxProject): project where to add the item
        item_factories (dict): mapping from item type to ProjectItemFactory
        name (str): item's name
        x (float): item's x coordinate
        y (float): item's y coordinate

    Returns:
        DataStore: added project item
    """
    item_dict = {name: {"type": "Data Store", "description": "", "url": dict(), "x": x, "y": y}}
    project.restore_project_items(item_dict, item_factories)
    return project.get_item(name)


def add_dc(project, item_factories, name, x=0, y=0, file_refs=None):
    """Helper function to create a Data Connection to given project.

    Args:
        project (SpineToolboxProject): project where to add the item
        item_factories (dict): mapping from item type to ProjectItemFactory
        name (str): item's name
        x (float): item's x coordinate
        y (float): item's y coordinate
        file_refs (list): File references

    Returns:
        DataConnection: added project item
    """
    frefs = list() if not file_refs else file_refs
    item_dict = {name: {"type": "Data Connection", "description": "", "references": frefs, "x": x, "y": y}}
    project.restore_project_items(item_dict, item_factories)
    return project.get_item(name)


def add_tool(project, item_factories, name, tool_spec="", x=0, y=0):
    """Helper function to create a Tool to given project.

    Args:
        project (SpineToolboxProject): project where to add the item
        item_factories (dict): mapping from item type to ProjectItemFactory
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
    project.restore_project_items(item, item_factories)
    return project.get_item(name)


def add_view(project, item_factories, name, x=0, y=0):
    """Helper function to create a View to given project.

    Args:
        project (SpineToolboxProject): project where to add the item
        item_factories (dict): mapping from item type to ProjectItemFactory
        name (str): item's name
        x (float): item's x coordinate
        y (float): item's y coordinate

    Returns:
        View: added project item
    """
    item = {name: {"type": "View", "description": "", "x": x, "y": y}}
    project.restore_project_items(item, item_factories)
    return project.get_item(name)


def add_importer(project, item_factories, name, x=0, y=0):
    """Helper function to create an Importer to given project.

    Args:
        project (SpineToolboxProject): project where to add the item
        item_factories (dict): mapping from item type to ProjectItemFactory
        name (str): item's name
        x (float): item's x coordinate
        y (float): item's y coordinate

    Returns:
        Importer: added project item
    """
    item = {name: {"type": "Importer", "description": "", "specification": "", "x": x, "y": y}}
    project.restore_project_items(item, item_factories)
    return project.get_item(name)


def add_data_transformer(project, item_factories, name, x=0, y=0):
    """Helper function to create a Data Transformer to given project.

    Args:
        project (SpineToolboxProject): project where to add the item
        item_factories (dict): mapping from item type to ProjectItemFactory
        name (str): item's name
        x (float): item's x coordinate
        y (float): item's y coordinate

    Returns:
        DataTransformer: added project item
    """
    item = {name: {"type": "Data Transformer", "description": "", "x": x, "y": y, "specification": ""}}
    project.restore_project_items(item, item_factories)
    return project.get_item(name)


def add_exporter(project, item_factories, name, x=0, y=0):
    """Helper function to create an Exporter to given project.

    Args:
        project (SpineToolboxProject): project where to add the item
        item_factories (dict): mapping from item type to ProjectItemFactory
        name (str): item's name
        x (float): item's x coordinate
        y (float): item's y coordinate

    Returns:
        Exporter: added project item
    """
    item = {name: {"type": "Exporter", "description": "", "x": x, "y": y, "specification": None}}
    project.restore_project_items(item, item_factories)
    return project.get_item(name)


def add_merger(project, item_factories, name, x=0, y=0):
    """Helper function to create a Merger to given project.

    Args:
        project (SpineToolboxProject): project where to add the item
        item_factories (dict): mapping from item type to ProjectItemFactory
        name (str): item's name
        x (float): item's x coordinate
        y (float): item's y coordinate

    Returns:
        Merger: added project item
    """
    item = {name: {"type": "Merger", "description": "", "x": x, "y": y}}
    project.restore_project_items(item, item_factories)
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


class TestSpineDBManager(SpineDBManager):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs, synchronous=True)

    def can_fetch_more(self, db_map, parent):
        parent.apply_changes_immediately()
        return super().can_fetch_more(db_map, parent)


@contextmanager
def q_object(o):
    """Deletes given QObject after the context runs out.

    Args:
        o (QObject): object to delete

    Yields:
        QObject: object
    """
    try:
        yield o
    finally:
        o.deleteLater()


def model_data_to_dict(model, parent=QModelIndex()):
    """"""
    rows = list()
    for row in range(model.rowCount(parent)):
        row_data = []
        for column in range(model.columnCount()):
            index = model.index(row, column, parent)
            child_data = model_data_to_dict(model, index)
            row_data.append({index.data(): child_data} if child_data else index.data())
        rows.append(row_data)
    return rows


def model_data_to_table(model, parent=QModelIndex(), role=Qt.ItemDataRole.DisplayRole):
    """Puts model data into Python table.

    Args:
        model (QAbstractItemModel): model to process
        parent (QModelIndex): parent index
        role (Qt.ItemDataRole): data role

    Returns:
        list of list: model data
    """
    data = []
    for row in range(model.rowCount()):
        data.append([model.index(row, column, parent).data(role) for column in range(model.columnCount())])
    return data


def fetch_model(model):
    while model.canFetchMore(QModelIndex()):
        model.fetchMore(QModelIndex())
        qApp.processEvents()


class FakeDataStore:
    def __init__(self, n):
        self.name = n

    def item_type(self):
        return "Data Store"

    def sql_alchemy_url(self):
        return f"{self.name}_sql_alchemy_url"

    def is_url_validated(self):
        return True

    def tear_down(self):
        return True
