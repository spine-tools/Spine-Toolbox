######################################################################################################################
# Copyright (C) 2017-2022 Spine project consortium
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################
"""Helper utilites for unit tests that test Database manager's table and tree views."""
from types import MethodType
import unittest
from unittest import mock
from PySide6.QtCore import QEvent, Qt
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import QApplication

from spinetoolbox.spine_db_editor.widgets.spine_db_editor import SpineDBEditor
from spinetoolbox.spine_db_editor.widgets.add_items_dialogs import AddObjectClassesDialog, AddObjectsDialog
from spinetoolbox.helpers import signal_waiter
from spinetoolbox.widgets.custom_editors import SearchBarEditor
from ...mock_helpers import TestSpineDBManager


class EditorDelegateMocking:
    """Mock editor delegate that can be used to enter data to table and tree views."""

    def __init__(self):
        self._cell_editor = None

    def write_to_index(self, view, index, value):
        delegate = view.itemDelegateForIndex(index)
        if self._cell_editor is None:
            original_create_editor = delegate.createEditor

            def create_and_store_editor(instance, parent, option, target_index):
                self._cell_editor = original_create_editor(parent, option, target_index)
                return self._cell_editor

            delegate.createEditor = MethodType(create_and_store_editor, delegate)
        view.setCurrentIndex(index)
        view.edit(index)
        if self._cell_editor is None:
            # Native editor widget is being used, fall back to setting value directly in model.
            view.model().setData(index, value)
            return
        if isinstance(self._cell_editor, SearchBarEditor):
            key_press_event = QKeyEvent(QEvent.KeyPress, Qt.Key_Down, Qt.NoModifier, 0, 0, 0)
            i = 0
            while self._cell_editor.data() != value:
                if i == self._cell_editor._model.rowCount():
                    raise RuntimeError("Value not found in editor widget.")
                self._cell_editor.keyPressEvent(key_press_event)
                i += 1
        else:
            self._cell_editor.setText(str(value))
        delegate.commitData.emit(self._cell_editor)
        delegate.closeEditor.emit(self._cell_editor)

    def try_to_edit_index(self, view, index):
        delegate = view.itemDelegateForIndex(index)
        if self._cell_editor is None:
            original_create_editor = delegate.createEditor

            def create_and_store_editor(instance, parent, option, target_index):
                self._cell_editor = original_create_editor(parent, option, target_index)
                return self._cell_editor

            delegate.createEditor = MethodType(create_and_store_editor, delegate)
        view.setCurrentIndex(index)
        view.edit(index)

    def reset(self):
        self._cell_editor = None


def add_entity_tree_item(item_names, view, menu_action_text, dialog_class):
    """Adds an entity to object or relationship tree view.

    Args:
        item_names (dict): row data keyed by column index
        view (QTreeView): object or relationship tree view
        menu_action_text (str): entry in tree view's context menu
        dialog_class (Type): relevant QDialog class for adding the entity
    """
    add_items_action = None
    for action in view._menu.actions():
        if action.text() == menu_action_text:
            add_items_action = action
            break
    if add_items_action is None:
        raise RuntimeError("Menu action not found.")
    patched = "spinetoolbox.spine_db_editor.widgets.tree_view_mixin." + dialog_class.__name__
    with mock.patch(patched) as mock_dialog:
        add_items_action.trigger()
        arguments_list = mock_dialog.call_args_list
    for arguments in arguments_list:
        add_items_dialog = dialog_class(*arguments[0])
        with signal_waiter(add_items_dialog.model.rowsInserted) as waiter:
            QApplication.processEvents()
            waiter.wait()
        for column, name in item_names.items():
            item_name_index = add_items_dialog.model.index(0, column)
            add_items_dialog.set_model_data(item_name_index, name)
        add_items_dialog.accept()


def add_object_class(view, class_name):
    add_entity_tree_item({0: class_name}, view, "Add object classes", AddObjectClassesDialog)


def add_object(view, object_name, object_class_index=0):
    model = view.model()
    root_index = model.index(0, 0)
    class_index = model.index(object_class_index, 0, root_index)
    view._context_item = model.item_from_index(class_index)
    add_entity_tree_item({1: object_name}, view, "Add objects", AddObjectsDialog)


class TestBase(unittest.TestCase):
    """Base class for Database editor's table and tree view tests."""

    @classmethod
    def setUpClass(cls):
        if not QApplication.instance():
            QApplication()

    def _common_setup(self, url, create):
        with mock.patch("spinetoolbox.spine_db_editor.widgets.spine_db_editor.SpineDBEditor.restore_ui"), mock.patch(
            "spinetoolbox.spine_db_editor.widgets.spine_db_editor.SpineDBEditor.show"
        ):
            mock_settings = mock.MagicMock()
            mock_settings.value.side_effect = lambda *args, **kwargs: 0
            self._db_mngr = TestSpineDBManager(mock_settings, None)
            logger = mock.MagicMock()
            self._db_map = self._db_mngr.get_db_map(url, logger, codename="database", create=create)
            self._db_editor = SpineDBEditor(self._db_mngr, {url: "database"})
        QApplication.processEvents()

    def _common_tear_down(self):
        with mock.patch(
            "spinetoolbox.spine_db_editor.widgets.spine_db_editor.SpineDBEditor.save_window_state"
        ), mock.patch("spinetoolbox.spine_db_manager.QMessageBox"):
            self._db_editor.close()
        self._db_mngr.close_all_sessions()
        while not self._db_map.connection.closed:
            QApplication.processEvents()
        self._db_mngr.clean_up()
        self._db_editor.deleteLater()
        self._db_editor = None

    def _commit_changes_to_database(self, commit_message):
        with mock.patch.object(self._db_editor, "_get_commit_msg") as commit_msg:
            commit_msg.return_value = commit_message
            with signal_waiter(self._db_mngr.session_committed) as waiter:
                self._db_editor.ui.actionCommit.trigger()
                waiter.wait()
