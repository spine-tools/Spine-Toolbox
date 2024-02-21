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

"""Custom item delegates."""
from PySide6.QtCore import Qt, Signal, QEvent, QPoint, QRect, QModelIndex
from PySide6.QtWidgets import (
    QComboBox,
    QStyledItemDelegate,
    QStyleOptionButton,
    QStyle,
    QApplication,
    QStyleOptionComboBox,
)


class ComboBoxDelegate(QStyledItemDelegate):
    def __init__(self, items):
        super().__init__()
        self._items = {item: k for k, item in enumerate(items)}

    def createEditor(self, parent, option, index):
        editor = QComboBox(parent)
        editor.addItems(self._items)
        editor.activated.connect(lambda _: self._finalize_editing(editor))
        return editor

    def paint(self, painter, option, index):
        value = index.data(Qt.ItemDataRole.DisplayRole)
        style = QApplication.style()
        opt = QStyleOptionComboBox()
        opt.text = str(value)
        opt.rect = option.rect
        style.drawComplexControl(QStyle.ComplexControl.CC_ComboBox, opt, painter)
        super().paint(painter, option, index)

    def setEditorData(self, editor, index):
        value = index.data(Qt.ItemDataRole.DisplayRole)
        ind = self._items.get(value, -1)
        editor.setCurrentIndex(ind)

    def setModelData(self, editor, model, index):
        value = editor.currentText()
        model.setData(index, value, Qt.ItemDataRole.EditRole)

    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)
        editor.showPopup()

    def _finalize_editing(self, editor):
        self.commitData.emit(editor)
        self.closeEditor.emit(editor)


class CheckBoxDelegate(QStyledItemDelegate):
    """A delegate that places a fully functioning QCheckBox."""

    data_committed = Signal(QModelIndex, object)

    def __init__(self, parent, centered=True):
        """
        Args:
            parent (QWiget)
            centered (bool): whether or not the checkbox should be center-aligned in the widget
        """
        super().__init__(parent)
        self._centered = centered

    def createEditor(self, parent, option, index):
        """Important, otherwise an editor is created if the user clicks in this cell.
        ** Need to hook up a signal to the model."""
        return None

    def paint(self, painter, option, index):
        """Paint a checkbox without the label."""
        if option.state & QStyle.StateFlag.State_Selected:
            painter.fillRect(option.rect, option.palette.highlight())
        checkbox_style_option = QStyleOptionButton()
        checkbox_style_option.rect = self.get_checkbox_rect(option)
        if index.flags() & Qt.ItemIsEditable:
            checkbox_style_option.state |= QStyle.StateFlag.State_Enabled
        else:
            checkbox_style_option.state |= QStyle.StateFlag.State_ReadOnly
        self._do_paint(painter, checkbox_style_option, index)

    @staticmethod
    def _do_paint(painter, checkbox_style_option, index):
        checked = index.data()
        if checked is None:
            checkbox_style_option.state |= QStyle.StateFlag.State_NoChange
        elif checked:
            checkbox_style_option.state |= QStyle.StateFlag.State_On
        else:
            checkbox_style_option.state |= QStyle.StateFlag.State_Off
        # noinspection PyArgumentList
        QApplication.style().drawControl(QStyle.ControlElement.CE_CheckBox, checkbox_style_option, painter)

    def editorEvent(self, event, model, option, index):
        """Change the data in the model and the state of the checkbox
        when user presses left mouse button and this cell is editable.
        Otherwise do nothing."""
        if not index.flags() & Qt.ItemIsEditable:
            return False
        # Do nothing on double-click
        if event.type() == QEvent.MouseButtonDblClick:
            return True
        if event.type() == QEvent.MouseButtonPress and self.get_checkbox_rect(option).contains(event.pos()):
            self.data_committed.emit(index, not index.data(Qt.ItemDataRole.EditRole))
            return True
        return False

    def setModelData(self, editor, model, index):
        """Do nothing. Model data is updated by handling the `data_committed` signal."""

    def get_checkbox_rect(self, option):
        checkbox_style_option = QStyleOptionButton()
        checkbox_rect = QApplication.style().subElementRect(
            QStyle.SubElement.SE_CheckBoxIndicator, checkbox_style_option, None
        )
        if self._centered:
            checkbox_anchor = QPoint(
                option.rect.x() + option.rect.width() / 2 - checkbox_rect.width() / 2,
                option.rect.y() + option.rect.height() / 2 - checkbox_rect.height() / 2,
            )
        else:
            checkbox_anchor = QPoint(
                option.rect.x() + checkbox_rect.width() / 2, option.rect.y() + checkbox_rect.height() / 2
            )
        return QRect(checkbox_anchor, checkbox_rect.size())


class RankDelegate(CheckBoxDelegate):
    """A delegate that places a QCheckBox but draws a number instead of the check."""

    @staticmethod
    def _do_paint(painter, checkbox_style_option, index):
        checkbox_style_option.state |= QStyle.StateFlag.State_Off
        QApplication.style().drawControl(QStyle.ControlElement.CE_CheckBox, checkbox_style_option, painter)
        rank = index.data()
        if not rank:
            return
        painter.drawText(checkbox_style_option.rect, Qt.AlignCenter, str(rank))
