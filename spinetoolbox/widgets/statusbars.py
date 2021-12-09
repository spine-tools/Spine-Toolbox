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
Functions to make and handle QStatusBars.
"""
from PySide2.QtCore import Slot
from PySide2.QtGui import QFont
from PySide2.QtWidgets import QStatusBar, QToolButton
from ..config import STATUSBAR_SS


class MainStatusBar(QStatusBar):
    """A status bar for the main toolbox window."""

    def __init__(self, toolbox):
        """
        Args:
            toolbox (ToolboxUI)
        """
        super().__init__(toolbox)
        self._toolbox = toolbox
        self._current_doc = None
        self._item_buttons = {}
        self._item_log_is_visible = False
        self.setStyleSheet(STATUSBAR_SS)  # Initialize QStatusBar
        self._event_log_button = _EventLogButton(
            self._toolbox.ui.dockWidget_eventlog, self._toolbox.ui.textBrowser_eventlog, "\uf075"
        )
        self.addWidget(self._event_log_button)
        self._toolbox.ui.textBrowser_itemlog.textChanged.connect(self._handle_item_log_text_changed)
        self._toolbox.ui.dockWidget_itemlog.visibilityChanged.connect(self._handle_item_log_visibility_changed)

    @Slot(bool)
    def _handle_item_log_visibility_changed(self, visible):
        """Stores item log visible status to create ``_ItemLogButton`` instances later.
        See ``_handle_item_log_text_changed``"""
        self._item_log_is_visible = visible

    @Slot()
    def _handle_item_log_text_changed(self):
        """Runs when the text of the item log document changes.
        Creates an ``_ItemLogButton`` for the current item and adds it to the status bar.
        """
        doc = self._toolbox.ui.textBrowser_itemlog.document()
        if doc.owner is not None and doc not in self._item_buttons:
            factory = self._toolbox.item_factories.get(doc.owner.item_type())
            if factory is None:
                return
            color = factory.icon_color()
            self._item_buttons[doc] = button = _ItemLogButton(
                self._toolbox.ui.dockWidget_itemlog,
                self._toolbox.ui.textBrowser_itemlog,
                "\uf086",
                visible=self._item_log_is_visible,
                color_name=color.name(),
            )
        button = self._item_buttons.get(doc)
        if button is not None:
            self.addWidget(button)


class _LogButton(QToolButton):
    def __init__(self, widget, log, icon, visible=False, color_name="", parent=None):
        """A button to report unseen log messages, and show said log if clicked.

        Args:
            widget (QDockWidget): the dock widget that contains the log
            log (CustomQTextBrowser): the log
            icon (str): icon for the button
            visible (bool): whether or not the widget is visible at the moment of creating this button
            color_name (str): color for the button
            parent (QObject): passed to QToolButton constructor
        """
        super().__init__(parent)
        self.setFont(QFont("Font Awesome 5 Free Solid"))
        self.setStyleSheet(f"QToolButton{{border: none; color: {color_name}}}")
        self.setText(icon)
        self._widget = widget
        self._log = log
        self._widget_is_visible = visible
        self._widget.visibilityChanged.connect(self._handle_widget_visibility_changed)
        self._widget.visibilityChanged.connect(self.setChecked)
        self._log.textChanged.connect(self._handle_log_changed)
        self.clicked.connect(self._handle_clicked)

    @Slot(bool)
    def _handle_clicked(self, checked):
        """Runs when the button is clicked, shows and raises the widget."""
        if not self._widget_is_visible:
            self._widget.show()
            self._widget.raise_()

    @Slot(bool)
    def _handle_widget_visibility_changed(self, visible):
        raise NotImplementedError()

    @Slot()
    def _handle_log_changed(self):
        raise NotImplementedError()


class _EventLogButton(_LogButton):
    def __init__(self, widget, log, icon, visible=False, color_name="", parent=None):
        super().__init__(widget, log, icon, visible=visible, color_name=color_name, parent=parent)
        self.setToolTip("<html>New event log messages</html>")

    @Slot(bool)
    def _handle_widget_visibility_changed(self, visible):
        """Hides the button when the widget becomes visible."""
        self._widget_is_visible = visible
        if self._widget_is_visible:
            self.hide()

    @Slot()
    def _handle_log_changed(self):
        """Shows the button when the log text changes and the widget is non-visible."""
        if not self._widget_is_visible:
            self.show()


class _ItemLogButton(_LogButton):
    def __init__(self, widget, log, icon, visible=False, color_name="", parent=None):
        """Reimplemented to store the document currently in the log and the character count,
        for monitoring that document only.
        """
        super().__init__(widget, log, icon, visible=visible, color_name=color_name, parent=parent)
        self._doc = self._log.document()
        self._char_count = self._doc.characterCount()
        self.setToolTip(f"<html>New <b>{self._doc.owner.name}</b> execution log messages</html>")

    @Slot(bool)
    def _handle_clicked(self, checked):
        """Reimplemented to select the item before showing the widget."""
        icon = self._doc.owner.get_icon()
        icon.scene().clearSelection()
        icon.setSelected(True)
        super()._handle_clicked(checked)

    @Slot(bool)
    def _handle_widget_visibility_changed(self, visible):
        """Hides the button when the widget becomes visible while showing the monitored document."""
        self._widget_is_visible = visible
        if self._widget_is_visible and self._log.document() == self._doc:
            self.hide()

    @Slot()
    def _handle_log_changed(self):
        """Shows the button when the log text changes and the widget is non-visible,
        but only if the log's document is the one being monitored."""
        doc = self._log.document()
        if doc != self._doc:
            return
        if self._widget_is_visible:
            self.hide()
        elif self._doc.characterCount() > self._char_count:
            self.show()

    def hideEvent(self, ev):
        """Reimplemented to update the current character count."""
        super().hideEvent(ev)
        self._char_count = self._doc.characterCount()
