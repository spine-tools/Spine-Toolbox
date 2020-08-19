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
Custom item delegates.

:author: M. Marin (KTH)
:date:   1.9.2018
"""

from PySide2.QtCore import Qt, Signal, QEvent, QPoint, QRect
from PySide2.QtWidgets import (
    QComboBox,
    QStyledItemDelegate,
    QStyleOptionButton,
    QStyle,
    QApplication,
    QStyleOptionComboBox,
)
from .custom_editors import CustomLineEditor, SearchBarEditor, CheckListEditor


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
        value = index.data(Qt.DisplayRole)
        style = QApplication.style()
        opt = QStyleOptionComboBox()
        opt.text = str(value)
        opt.rect = option.rect
        style.drawComplexControl(QStyle.CC_ComboBox, opt, painter)
        super().paint(painter, option, index)

    def setEditorData(self, editor, index):
        value = index.data(Qt.DisplayRole)
        ind = self._items.get(value, -1)
        editor.setCurrentIndex(ind)

    def setModelData(self, editor, model, index):
        value = editor.currentText()
        model.setData(index, value, Qt.EditRole)

    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)
        editor.showPopup()

    def _finalize_editing(self, editor):
        self.commitData.emit(editor)
        self.closeEditor.emit(editor)


class LineEditDelegate(QStyledItemDelegate):
    """A delegate that places a fully functioning QLineEdit.

    Attributes:
        parent (QMainWindow): either data store or spine datapackage widget
    """

    data_committed = Signal("QModelIndex", "QVariant", name="data_committed")

    def createEditor(self, parent, option, index):
        """Return CustomLineEditor."""
        return CustomLineEditor(parent)

    def setEditorData(self, editor, index):
        """Init the line editor with previous data from the index."""
        editor.set_data(index.data(Qt.EditRole))

    def setModelData(self, editor, model, index):
        """Send signal."""
        self.data_committed.emit(index, editor.data())


class CheckBoxDelegate(QStyledItemDelegate):
    """A delegate that places a fully functioning QCheckBox.

    Attributes:
        parent (QMainWindow): either toolbox or spine datapackage widget
        centered (bool): whether or not the checkbox should be center-aligned in the widget
    """

    data_committed = Signal("QModelIndex", "QVariant")

    def __init__(self, parent, centered=True):
        super().__init__(parent)
        self._centered = centered
        self._checkbox_pressed = None

    def createEditor(self, parent, option, index):
        """Important, otherwise an editor is created if the user clicks in this cell.
        ** Need to hook up a signal to the model."""
        return None

    def paint(self, painter, option, index):
        """Paint a checkbox without the label."""
        if option.state & QStyle.State_Selected:
            painter.fillRect(option.rect, option.palette.highlight())
        checkbox_style_option = QStyleOptionButton()
        if (index.flags() & Qt.ItemIsEditable) > 0:
            checkbox_style_option.state |= QStyle.State_Enabled
        else:
            checkbox_style_option.state |= QStyle.State_ReadOnly
        checked = index.data()
        if checked is None:
            checkbox_style_option.state |= QStyle.State_NoChange
        elif checked:
            checkbox_style_option.state |= QStyle.State_On
        else:
            checkbox_style_option.state |= QStyle.State_Off
        checkbox_style_option.rect = self.get_checkbox_rect(option)
        # noinspection PyArgumentList
        QApplication.style().drawControl(QStyle.CE_CheckBox, checkbox_style_option, painter)

    def editorEvent(self, event, model, option, index):
        """Change the data in the model and the state of the checkbox
        when user presses left mouse button and this cell is editable.
        Otherwise do nothing."""
        if not (index.flags() & Qt.ItemIsEditable) > 0:
            return False
        # Do nothing on double-click
        if event.type() == QEvent.MouseButtonDblClick:
            return True
        if event.type() == QEvent.MouseButtonPress:
            self._checkbox_pressed = self.get_checkbox_rect(option).contains(event.pos())
        if event.type() == QEvent.MouseButtonPress:
            if self._checkbox_pressed and self.get_checkbox_rect(option).contains(event.pos()):
                self._checkbox_pressed = False
                self.data_committed.emit(index, not index.data(Qt.EditRole))
                return True
        return False

    def setModelData(self, editor, model, index):
        """Do nothing. Model data is updated by handling the `data_committed` signal."""

    def get_checkbox_rect(self, option):
        checkbox_style_option = QStyleOptionButton()
        checkbox_rect = QApplication.style().subElementRect(QStyle.SE_CheckBoxIndicator, checkbox_style_option, None)
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


class ForeignKeysDelegate(QStyledItemDelegate):
    """A QComboBox delegate with checkboxes.

    Attributes:
        parent (SpineDatapackageWidget): spine datapackage widget
    """

    data_committed = Signal("QModelIndex", "QVariant")

    def _close_editor(self, editor, index):
        """Closes editor. Needed by SearchBarEditor."""
        self.closeEditor.emit(editor)
        self.setModelData(editor, index.model(), index)

    def createEditor(self, parent, option, index):
        """Return editor."""
        model = index.model()
        header = model.horizontal_header_labels()
        if header[index.column()] == 'fields':
            editor = CheckListEditor(self.parent(), parent, ranked=True)
            current_field_names = index.data(Qt.DisplayRole).split(',') if index.data(Qt.DisplayRole) else []
            field_names = model.datapackage.resources[model.resource_index].schema.field_names
            editor.set_data(field_names, current_field_names)
            return editor
        if header[index.column()] == 'reference resource':
            editor = SearchBarEditor(self.parent(), parent)
            editor.set_data(index.data(Qt.DisplayRole), model.datapackage.resource_names)
            editor.data_committed.connect(lambda editor=editor, index=index: self._close_editor(editor, index))
            return editor
        if header[index.column()] == 'reference fields':
            editor = CheckListEditor(self.parent(), parent, ranked=True)
            current_field_names = index.data(Qt.DisplayRole).split(',') if index.data(Qt.DisplayRole) else []
            reference_resource_name = index.sibling(index.row(), header.index('reference resource')).data(
                Qt.DisplayRole
            )
            reference_resource = model.datapackage.get_resource(reference_resource_name)
            if not reference_resource:
                field_names = []
            else:
                field_names = reference_resource.schema.field_names
            editor.set_data(field_names, current_field_names)
            return editor
        return None

    def updateEditorGeometry(self, editor, option, index):
        super().updateEditorGeometry(editor, option, index)
        if isinstance(editor, (SearchBarEditor, CheckListEditor)):
            size = option.rect.size()
            editor.set_base_size(size)
            editor.update_geometry()

    def setModelData(self, editor, model, index):
        """Send signal."""
        self.data_committed.emit(index, editor.data())
