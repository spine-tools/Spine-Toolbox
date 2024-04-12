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

"""Helper utilities for unit tests that test Database editor's table and tree views."""
from types import MethodType
from unittest import mock
from PySide6.QtCore import QEvent, Qt
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import QApplication
from spinetoolbox.spine_db_editor.widgets.add_items_dialogs import AddEntityClassesDialog, AddEntitiesDialog
from spinetoolbox.helpers import signal_waiter
from spinetoolbox.spine_db_editor.widgets.custom_editors import SearchBarEditor


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


def add_zero_dimension_entity_class(view, name):
    view._context_item = view.model().root_item
    add_entity_tree_item({0: name}, view, "Add entity classes", AddEntityClassesDialog)


def add_entity(view, name, entity_class_index=0):
    model = view.model()
    root_index = model.index(0, 0)
    class_index = model.index(entity_class_index, 0, root_index)
    view._context_item = model.item_from_index(class_index)
    add_entity_tree_item({0: name}, view, "Add entities", AddEntitiesDialog)
