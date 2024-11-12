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

"""Contains the DBEditorToolBar class and helpers."""
from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QAction, QIcon, QKeySequence, QTextCursor
from PySide6.QtWidgets import QDialog, QSizePolicy, QTextEdit, QToolBar, QToolButton, QVBoxLayout, QWidget
from spinetoolbox.helpers import CharIconEngine, add_keyboard_shortcut_to_tool_tip, plain_to_rich


class DBEditorToolBar(QToolBar):
    def __init__(self, db_editor):
        super().__init__(db_editor)
        self.setObjectName("spine_db_editor_toolbar")
        self._db_editor = db_editor
        self.reload_action = QAction(QIcon(CharIconEngine("\uf021")), "Reload")
        self.reload_action.setToolTip(plain_to_rich("Reload data from database keeping changes"))
        self.reload_action.setShortcut(QKeySequence(Qt.Modifier.CTRL | Qt.Key.Key_R))
        add_keyboard_shortcut_to_tool_tip(self.reload_action)
        self.reload_action.setEnabled(False)
        self.reset_docks_action = QAction(QIcon(CharIconEngine("\uf2d2")), "Reset docks")
        self.reset_docks_action.setToolTip(plain_to_rich("Reset window back to default configuration"))
        self.show_toolbox_action = QAction(QIcon(":/symbols/Spine_symbol.png"), "Show Toolbox")
        self.show_toolbox_action.setShortcut(QKeySequence(Qt.Modifier.CTRL | Qt.Key.Key_Escape))
        self.show_toolbox_action.setToolTip(plain_to_rich("Show Spine Toolbox window"))
        add_keyboard_shortcut_to_tool_tip(self.show_toolbox_action)
        self.show_url_action = QAction(QIcon(CharIconEngine("\uf550")), "Show URLs")
        self.show_url_action.setToolTip(plain_to_rich("Show URLs of currently databases in the session"))
        self._add_actions()
        self._connect_signals()
        self.setMovable(False)
        self.setIconSize(QSize(20, 20))

    def _add_actions(self):
        """Creates buttons for the actions and adds them to the toolbar"""
        self.create_button_for_action(self._db_editor.ui.actionNew_db_file)
        self.create_button_for_action(self._db_editor.ui.actionAdd_db_file)
        self.create_button_for_action(self._db_editor.ui.actionOpen_db_file)
        self.addSeparator()
        self.create_button_for_action(self._db_editor.ui.actionUndo)
        self.create_button_for_action(self._db_editor.ui.actionRedo)
        self.addSeparator()
        self.create_button_for_action(self._db_editor.ui.actionCommit)
        self.create_button_for_action(self._db_editor.ui.actionMass_remove_items)
        self.create_button_for_action(self.reload_action)
        self.addSeparator()
        self.create_button_for_action(self._db_editor.ui.actionStacked_style)
        self.create_button_for_action(self._db_editor.ui.actionGraph_style)
        self.addSeparator()
        self.create_button_for_action(self._db_editor.ui.actionValue)
        self.create_button_for_action(self._db_editor.ui.actionIndex)
        self.create_button_for_action(self._db_editor.ui.actionElement)
        self.create_button_for_action(self._db_editor.ui.actionScenario)
        self.addSeparator()
        self.create_button_for_action(self.reset_docks_action)
        self.addSeparator()
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.addWidget(spacer)
        self.addSeparator()
        self.create_button_for_action(self.show_url_action)
        self.addSeparator()
        self.create_button_for_action(self.show_toolbox_action)

    def _connect_signals(self):
        """Connects signals"""
        self.reload_action.triggered.connect(self._db_editor.refresh_session)
        self.reset_docks_action.triggered.connect(self._db_editor.reset_docks)
        self.show_url_action.triggered.connect(self._show_url_codename_widget)

    def create_button_for_action(self, action):
        """Creates a button for the given action and adds it to the widget"""
        tool_button = QToolButton()
        tool_button.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        tool_button.setPopupMode(QToolButton.InstantPopup)
        tool_button.setDefaultAction(action)
        self.addWidget(tool_button)

    def _show_url_codename_widget(self):
        """Shows the url widget"""
        dialog = _URLDialog(self._db_editor.db_urls, self._db_editor.db_mngr.name_registry, self)
        dialog.show()


class _URLDialog(QDialog):
    """Class for showing URLs and database names in the editor"""

    def __init__(self, urls, name_registry, parent=None):
        super().__init__(parent=parent, f=Qt.Popup)
        self.textEdit = QTextEdit(self)
        self.textEdit.setObjectName("textEdit")
        text = "<br>".join([f"<b>{name_registry.display_name(url)}</b>: {url}" for url in urls])
        self.textEdit.setHtml(text)
        self.textEdit.setReadOnly(True)
        self.textEdit.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.textEdit.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.textEdit.setLineWrapMode(QTextEdit.NoWrap)
        layout = QVBoxLayout(self)
        layout.addWidget(self.textEdit)
        self.setLayout(layout)
        self.resize(500, 200)

    def showEvent(self, event):
        super().showEvent(event)
        self.textEdit.moveCursor(QTextCursor.Start)
        self.textEdit.setFocus()

    def keyPressEvent(self, event):
        if event.key() in (
            Qt.Key_Return,
            Qt.Key_Escape,
            Qt.Key_Enter,
        ):
            self.close()
