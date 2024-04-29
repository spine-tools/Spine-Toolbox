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

"""Contains custom combo box classes."""
import os
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QComboBox, QStyle, QStylePainter, QStyleOptionComboBox, QDialog, QAbstractItemView
from PySide6.QtGui import QValidator
from .notification import Notification


class CustomQComboBox(QComboBox):
    """A custom QComboBox for showing kernels in Settings->Tools."""

    def mouseMoveEvent(self, e):
        """Catch mouseMoveEvent and accept it because the comboBox
        popup (QListView) has mouse tracking on as default.
        This makes sure the comboBox popup appears in correct
        position and clicking on the combobox repeatedly does
        not move the Settings window."""
        e.accept()


class ElidedCombobox(QComboBox):
    """Combobox with elided text."""

    def paintEvent(self, event):
        opt = QStyleOptionComboBox()
        self.initStyleOption(opt)
        p = QStylePainter(self)
        p.drawComplexControl(QStyle.ComplexControl.CC_ComboBox, opt)
        text_rect = self.style().subControlRect(
            QStyle.ComplexControl.CC_ComboBox, opt, QStyle.SubControl.SC_ComboBoxEditField, self
        )
        opt.currentText = p.fontMetrics().elidedText(opt.currentText, Qt.ElideLeft, text_rect.width())
        p.drawControl(QStyle.ControlElement.CE_ComboBoxLabel, opt)


class OpenProjectDialogComboBox(QComboBox):
    def keyPressEvent(self, e):
        """Interrupts Enter and Return key presses when QComboBox is in focus.
        This is needed to prevent showing the 'Not a valid Spine Toolbox project'
        Notifier every time Enter is pressed.

        Args:
            e (QKeyEvent): Received key press event.
        """
        parent = self.parent()
        if e.key() == Qt.Key_Enter or e.key() == Qt.Key_Return:
            state = self.validator().state
            fm_current_index = parent.ui.treeView_file_system.currentIndex()
            if state == QValidator.State.Intermediate:
                # Remove path from qsettings
                # This is done because pressing enter adds an entry to combobox drop-down list automatically
                # and we don't want to clog it with irrelevant paths
                parent.remove_directory_from_recents(os.path.abspath(parent.selection()), parent._toolbox.qsettings())
                # Remove path from combobox as well
                cb_index = self.findText(os.path.abspath(parent.selection()))
                if cb_index == -1:
                    pass
                else:
                    self.removeItem(cb_index)
                notification = Notification(parent, "Path does not exist")
                notification.show()
            elif state == QValidator.State.Acceptable:
                p = self.currentText()
                fm_index = parent.file_model.index(p)
                if not fm_current_index == fm_index:
                    parent.ui.treeView_file_system.collapseAll()
                    parent.ui.treeView_file_system.setCurrentIndex(fm_index)
                    parent.ui.treeView_file_system.expand(fm_index)
                    parent.ui.treeView_file_system.scrollTo(fm_index, hint=QAbstractItemView.PositionAtTop)
                else:
                    project_json_fp = os.path.abspath(os.path.join(parent.selection(), ".spinetoolbox", "project.json"))
                    if os.path.isfile(project_json_fp):
                        parent.done(QDialog.DialogCode.Accepted)
            else:
                # INVALID (or None). Happens if Enter key is pressed and the combobox text has not been edited yet.
                pass
            e.accept()
        else:
            super().keyPressEvent(e)
