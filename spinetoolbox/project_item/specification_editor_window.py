######################################################################################################################
# Copyright (C) 2017-2022 Spine project consortium
# Copyright Spine Toolbox contributors
# This file is part of Spine Items.
# Spine Items is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""Contains base classes and utilities for specification editor windows."""
from __future__ import annotations
from collections.abc import Callable
from enum import IntEnum, unique
from typing import TYPE_CHECKING, ClassVar, Generic, TypeVar
from PySide6.QtCore import QSettings, Qt, Signal, Slot
from PySide6.QtGui import QAction, QIcon, QKeySequence, QUndoCommand, QUndoStack
from PySide6.QtWidgets import (
    QCheckBox,
    QErrorMessage,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMenu,
    QMessageBox,
    QToolBar,
    QToolButton,
    QWidget,
)
from spine_engine.project_item.project_item_specification import ProjectItemSpecification
from ..helpers import CharIconEngine, SealCommand, restore_ui, save_ui
from ..widgets.notification import ChangeNotifier, Notification
from .project_item import ProjectItem

if TYPE_CHECKING:
    from ..ui_main import ToolboxUI


class UniqueCommandId:
    _NEXT_ID: ClassVar[int] = 1

    @classmethod
    def unique_id(cls) -> int:
        """Returns a new unique command id.

        Returns:
            unique id
        """
        new_id = cls._NEXT_ID
        cls._NEXT_ID += 1
        return new_id


@unique
class CommandId(IntEnum):
    NONE = -1
    NAME_UPDATE = UniqueCommandId.unique_id()
    DESCRIPTION_UPDATE = UniqueCommandId.unique_id()


T = TypeVar("T")


class ChangeSpecPropertyCommand(Generic[T], QUndoCommand):
    """Command to set specification properties."""

    def __init__(
        self,
        callback: Callable[[T], None],
        new_value: T,
        old_value: T,
        cmd_name: str,
        command_id: CommandId = CommandId.NONE,
    ):
        """
        Args:
            callback: Function to call to set the spec property.
            new_value: new value
            old_value: old value
            cmd_name: command name
            command_id: command id
        """
        super().__init__()
        self._callback = callback
        self._new_value = new_value
        self._old_value = old_value
        self.setText(cmd_name)
        self.setObsolete(new_value == old_value)
        self._id = command_id
        self._sealed = False

    def redo(self):
        self._callback(self._new_value)

    def undo(self):
        self._callback(self._old_value)

    def id(self):
        return self._id.value

    def mergeWith(self, other):
        if not isinstance(other, ChangeSpecPropertyCommand):
            self._sealed = True
            return False
        if self._sealed or self.id() != other.id():
            return False
        if self._old_value == other._new_value:
            self.setObsolete(True)
        else:
            self._new_value = other._new_value
        return True


UI = TypeVar("UI")


class SpecificationEditorWindowBase(Generic[UI], QMainWindow):
    """Base class for spec editors."""

    def __init__(
        self, toolbox: ToolboxUI, specification: ProjectItemSpecification | None = None, item: ProjectItem | None = None
    ):
        """
        Args:
            toolbox: QMainWindow instance
            specification: If given, the form is pre-filled with this specification
            item: Sets the spec for this item if accepted
        """
        super().__init__()
        # Class attributes
        self._toolbox = toolbox
        self._original_spec_name = None if specification is None else specification.name
        self.specification = specification
        self.item = item
        self._app_settings = toolbox.qsettings()
        # Setup UI from Qt Designer file
        self._ui: UI = self._make_ui()
        self._ui.setupUi(self)
        self._ui_error = QErrorMessage(self)
        self._ui_error.setWindowFlag(Qt.WindowType.WindowContextHelpButtonHint, False)
        self._ui_error.setWindowTitle("Error")
        self.setWindowTitle(specification.name if specification else "")
        # Restore ui
        self._restore_dock_widgets()
        restore_ui(self, self._app_settings, self.settings_group)
        # Setup undo stack and change notifier
        self._undo_stack = QUndoStack(self)
        self._change_notifier = ChangeNotifier(self, self._undo_stack, self._app_settings, "appSettings/specShowUndo")
        # Setup toolbar
        self._spec_toolbar = SpecNameDescriptionToolbar(self, specification, self._undo_stack)
        self._spec_toolbar.show_toolbox_action.triggered.connect(self._toolbox.restore_and_activate)
        self._spec_toolbar.name_changed.connect(self._set_window_title)
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, self._spec_toolbar)
        self._populate_main_menu()
        self._spec_toolbar.save_action.triggered.connect(self._save)
        self._spec_toolbar.duplicate_action.triggered.connect(self._duplicate)
        self._undo_stack.cleanChanged.connect(self._update_window_modified)

    @property
    def settings_group(self) -> str:
        """Returns the settings group for this spec type."""
        raise NotImplementedError()

    def _make_ui(self) -> UI:
        """Returns the ui object from Qt designer."""
        raise NotImplementedError()

    def _restore_dock_widgets(self) -> None:
        """Restores dockWidgets to some default state. Called in the constructor, before restoring the ui from settings.
        Reimplement in subclasses if needed."""

    def _make_new_specification(self, spec_name: str) -> ProjectItemSpecification:
        """Returns a ProjectItemSpecification from current form settings."""
        raise NotImplementedError()

    def spec_toolbar(self) -> SpecNameDescriptionToolbar:
        """Returns spec editor window's toolbar, which contains e.g. the hamburger menu."""
        return self._spec_toolbar

    @Slot(str)
    def show_error(self, message: str) -> None:
        self._ui_error.showMessage(message)

    def _show_status_bar_msg(self, msg: str) -> None:
        word_count = len(msg.split(" "))
        mspw = 60000 / 140  # Assume we can read ~140 words per minute
        duration = mspw * word_count
        Notification(self, msg, life_span=duration, corner=Qt.Corner.BottomRightCorner).show()

    def _populate_main_menu(self) -> None:
        undo_action = self._undo_stack.createUndoAction(self)
        redo_action = self._undo_stack.createRedoAction(self)
        undo_action.setShortcuts(QKeySequence.StandardKey.Undo)
        undo_action.setIcon(QIcon(":/icons/menu_icons/undo.svg"))
        redo_action.setShortcuts(QKeySequence.StandardKey.Redo)
        redo_action.setIcon(QIcon(":/icons/menu_icons/redo.svg"))
        self._spec_toolbar.menu.insertActions(self._spec_toolbar.save_action, [redo_action, undo_action])
        self._spec_toolbar.menu.insertSeparator(self._spec_toolbar.save_action)

    @Slot(bool)
    def _update_window_modified(self, clean: bool) -> None:
        self.setWindowModified(not clean)
        self._spec_toolbar.save_action.setEnabled(not clean)
        self.setWindowTitle(self._spec_toolbar.name())
        self.windowTitleChanged.emit(self.windowTitle())

    @Slot(str)
    def _set_window_title(self, title: str) -> None:
        """Sets window title.

        Args:
            title: new window title
        """
        self.setWindowTitle(title)
        self.windowTitleChanged.emit(self.windowTitle())

    def _save(self, exiting: bool = False) -> bool:
        """Saves spec.

        Args:
            exiting: Set to True if called when trying to exit the editor window

        Returns:
            True if operation was successful, False otherwise
        """
        if not self._toolbox.project():
            self.show_error("Please open or create a project first")
            return False
        name = self._spec_toolbar.name()
        if not name:
            if exiting:
                return self.prompt_exit_without_saving()
            self.show_error("Please enter a name for the specification.")
            return False
        spec = self._make_new_specification(name)
        if spec is None:
            return self.prompt_exit_without_saving() if exiting else False
        if not self._original_spec_name:
            if self._toolbox.project().is_specification_name_reserved(name):
                self.show_error("Specification name already in use. Please enter a new name.")
                return False
            self._toolbox.add_specification(spec)
            if not self._toolbox.project().is_specification_name_reserved(name):
                return False
            if self.item is not None:
                self.item.set_specification(spec)
        else:
            if name != self._original_spec_name and self._toolbox.project().is_specification_name_reserved(name):
                self.show_error("Specification name already in use. Please enter a new name.")
                return False
            spec.definition_file_path = self.specification.definition_file_path
            self._toolbox.replace_specification(self._original_spec_name, spec)
            if not self._toolbox.project().is_specification_name_reserved(name):
                return False
        self._original_spec_name = name
        self._undo_stack.setClean()
        self.specification = spec
        self._spec_toolbar.duplicate_action.setEnabled(True)
        self.setWindowTitle(self.specification.name)
        return True

    def prompt_exit_without_saving(self) -> bool:
        """Prompts whether the user wants to exit without saving or cancel the exit.

        Returns:
            False if the user chooses to cancel, in which case we don't close the form.
        """

        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Icon.Question)
        msg.setWindowTitle(self.windowTitle())
        msg.setText("Can't save unfinished specification.\nDo you want to exit without saving?")
        msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel)
        answer = msg.exec()
        if answer == QMessageBox.StandardButton.Cancel:
            return False
        if answer == QMessageBox.StandardButton.Yes:
            return True
        raise RuntimeError("logic error: answer not recognized")

    @property
    def _duplicate_kwargs(self) -> dict:
        return {}

    def _duplicate(self) -> None:
        if not self._toolbox.project():
            self.show_error("Please open or create a project first")
            return
        new_spec = self._make_new_specification("")
        self._toolbox.show_specification_form(new_spec.item_type, new_spec, **self._duplicate_kwargs)

    def tear_down(self) -> bool:
        if self.focusWidget():
            self.focusWidget().clearFocus()
        if not self._undo_stack.isClean() and not prompt_to_save_changes(
            self, self._toolbox.qsettings(), self._save, True
        ):
            return False
        self._change_notifier.tear_down()
        self._undo_stack.cleanChanged.disconnect(self._update_window_modified)
        save_ui(self, self._app_settings, self.settings_group)
        return True

    def closeEvent(self, event):
        if not self.tear_down():
            event.ignore()
            return
        super().closeEvent(event)


class SpecNameDescriptionToolbar(QToolBar):
    """QToolBar for line edits and a hamburger menu."""

    name_changed = Signal(str)

    def __init__(self, parent: SpecificationEditorWindowBase, spec: ProjectItemSpecification, undo_stack: QUndoStack):
        """
        Args:
            parent: specification editor window instance
            spec`: specification that is being edited
            undo_stack`: an undo stack
        """
        super().__init__("Specification name and description", parent=parent)
        self._undo_stack = undo_stack
        self._current_name = ""
        self._current_description = ""
        self._line_edit_name = QLineEdit()
        self._line_edit_description = QLineEdit()
        self._line_edit_name.setPlaceholderText("Enter specification name here...")
        self._line_edit_description.setPlaceholderText("Enter specification description here...")
        self.setAllowedAreas(Qt.ToolBarArea.TopToolBarArea)
        self.setFloatable(False)
        self.setMovable(False)
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.addWidget(QLabel("Name:"))
        layout.addWidget(self._line_edit_name)
        layout.addWidget(QLabel("Description:"))
        layout.addWidget(self._line_edit_description)
        layout.setContentsMargins(3, 3, 3, 3)
        layout.setStretchFactor(self._line_edit_name, 1)
        layout.setStretchFactor(self._line_edit_description, 3)
        self.addWidget(widget)
        toolbox_icon = QIcon(":/symbols/Spine_symbol.png")
        self.show_toolbox_action = self.addAction(toolbox_icon, "Show Spine Toolbox (Ctrl+ESC)")
        self.show_toolbox_action.setShortcut(QKeySequence(Qt.Modifier.CTRL.value | Qt.Key.Key_Escape.value))
        self.menu = self._make_main_menu()
        self.save_action = self.menu.addAction("Save")
        self.duplicate_action = self.menu.addAction("Duplicate")
        self.close_action = self.menu.addAction("Close")
        self.save_action.setEnabled(False)
        self.duplicate_action.setEnabled(self.parent().specification is not None)
        self.save_action.setShortcut(QKeySequence.StandardKey.Save)
        self.save_action.setIcon(QIcon(":/icons/menu_icons/save_solid.svg"))
        self.duplicate_action.setShortcut(QKeySequence(Qt.Modifier.CTRL.value | Qt.Key.Key_D.value))
        self.duplicate_action.setIcon(QIcon(":/icons/menu_icons/copy.svg"))
        self.close_action.setShortcut(QKeySequence.StandardKey.Close)
        self.close_action.setIcon(QIcon(":/icons/menu_icons/window-close.svg"))
        self.setObjectName("_SpecNameDescriptionToolbar")
        if spec:
            self.do_set_name(spec.name)
            self.do_set_description(spec.description)
        self._line_edit_name.textEdited.connect(self._update_name)
        self._line_edit_name.editingFinished.connect(self._finish_name_editing)
        self._line_edit_description.textEdited.connect(self._update_description)
        self._line_edit_description.editingFinished.connect(self._finish_description_editing)

    def _make_main_menu(self) -> QMenu:
        menu = QMenu(self)
        menu_action = self.addAction(QIcon(CharIconEngine("\uf0c9")), "")
        menu_action.setMenu(menu)
        menu_button = self.widgetForAction(menu_action)
        menu_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        action = QAction(self)
        action.triggered.connect(menu_button.showMenu)
        keys = [
            QKeySequence(Qt.Modifier.ALT.value | Qt.Key.Key_F.value),
            QKeySequence(Qt.Modifier.ALT.value | Qt.Key.Key_E.value),
        ]
        action.setShortcuts(keys)
        self.parent().addAction(action)
        keys_str = ", ".join([key.toString() for key in keys])
        menu_button.setToolTip(f"<p>Main menu ({keys_str})</p>")
        return menu

    @Slot(str)
    def _update_name(self, name: str) -> None:
        """Pushes a command to undo stack that updates the specification name.

        Args:
            name: updated name
        """
        self._undo_stack.push(
            ChangeSpecPropertyCommand(
                self.do_set_name, name, self._current_name, "change specification name", CommandId.NAME_UPDATE
            )
        )

    @Slot()
    def _finish_name_editing(self) -> None:
        """Seals the last undo command."""
        self._undo_stack.push(SealCommand(CommandId.NAME_UPDATE.value))

    @Slot(str)
    def _update_description(self, description: str) -> None:
        """Pushes a command to undo stack that updates the specification description.

        Args:
            description: updated description
        """
        self._undo_stack.push(
            ChangeSpecPropertyCommand(
                self.do_set_description,
                self.description(),
                self._current_description,
                "change specification description",
                CommandId.DESCRIPTION_UPDATE,
            )
        )

    @Slot()
    def _finish_description_editing(self) -> None:
        """Seals the last undo command."""
        self._undo_stack.push(SealCommand(CommandId.DESCRIPTION_UPDATE.value))

    def do_set_name(self, name: str) -> None:
        self.name_changed.emit(name)
        if self._line_edit_name.text() == name:
            return
        self._current_name = name
        self._line_edit_name.setText(name)

    def do_set_description(self, description: str) -> None:
        if self._line_edit_description.text() == description:
            return
        self._current_description = description
        self._line_edit_description.setText(description)

    def name(self) -> str:
        return self._line_edit_name.text()

    def description(self) -> str:
        return self._line_edit_description.text()


def prompt_to_save_changes(
    parent: SpecificationEditorWindowBase,
    settings: QSettings,
    save_callback: Callable[[bool], bool],
    exiting: bool = False,
) -> bool:
    """Prompts to save changes.

    Args:
        parent: Spec editor widget
        settings: Toolbox settings
        save_callback: A function to call if the user chooses Save.
            It must return True or False depending on the outcome of the 'saving'.
        exiting: Set as True if called when trying to exit the editor window

    Returns:
        False if the user chooses to cancel, in which case we don't close the form.
    """
    save_spec = int(settings.value("appSettings/saveSpecBeforeClosing", defaultValue="1"))
    if save_spec == 0:
        return True
    if save_spec == 2:
        return save_callback(exiting)
    msg = QMessageBox(parent)
    msg.setIcon(QMessageBox.Icon.Question)
    msg.setWindowTitle(parent.windowTitle())
    msg.setText("Do you want to save your changes to the specification?")
    msg.setStandardButtons(
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel
    )
    chkbox = QCheckBox()
    chkbox.setText("Do not ask me again")
    msg.setCheckBox(chkbox)
    answer = msg.exec()
    if answer == QMessageBox.StandardButton.Cancel:
        return False
    if chkbox.checkState() == 2:
        # Save preference
        preference = "2" if answer == QMessageBox.StandardButton.Yes else "0"
        settings.setValue("appSettings/saveSpecBeforeClosing", preference)
    if answer == QMessageBox.StandardButton.Yes:
        return save_callback(exiting)
    return True
