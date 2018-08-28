#############################################################################
# Copyright (C) 2017 - 2018 VTT Technical Research Centre of Finland
#
# This file is part of Spine Toolbox.
#
# Spine Toolbox is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#############################################################################

"""
A delegate to edit table cells with comboboxes.

:author: Manuel Marin <manuelma@kth.se>
:date:   30.3.2018
"""
from PySide2.QtCore import Qt, Slot, QEvent
from PySide2.QtWidgets import QItemDelegate, QComboBox
from PySide2.QtGui import QStandardItemModel, QStandardItem, QPen
from widgets.lineedit_delegate import LineEditDelegate
import logging

class ComboBoxDelegate(QItemDelegate):
    """A QComboBox delegate."""

    def __init__(self, parent):
        super().__init__(parent)

    def createEditor(self, parent, option, index):
        """Return CustomComboEditor. Combo items are obtained from index's Qt.UserRole."""
        combo = CustomComboEditor(parent)
        combo.index = index
        combo.row = index.row()
        combo.column = index.column()
        combo.previous_data = index.data(Qt.EditRole)
        items = index.data(Qt.UserRole)
        combo.addItems(items)
        combo.setCurrentIndex(-1) # force index change
        combo.currentIndexChanged.connect(self.current_index_changed)
        return combo

    def setEditorData(self, editor, index):
        """Show pop up as soon as editing starts."""
        editor.showPopup()

    def setModelData(self, editor, model, index):
        """Do nothing. Model data is updated by handling the `closeEditor` signal."""
        pass

    @Slot(int, name='current_index_changed')
    def current_index_changed(self):
        """Close combo editor, which causes `closeEditor` signal to be emitted."""
        self.sender().close()


class CheckableComboBoxDelegate(ComboBoxDelegate):
    """A QComboBox delegate with checkboxes."""
    def __init__(self, parent):
        super().__init__(parent)

    def createEditor(self, parent, option, index):
        """Return CustomComboEditor. Combo items are obtained from index's Qt.UserRole."""
        combo = CustomComboEditor(parent)
        combo.index = index
        items = index.data(Qt.UserRole)
        model = QStandardItemModel()
        for item in items:
            q_item = QStandardItem(item)
            q_item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            q_item.setData(Qt.Unchecked, Qt.CheckStateRole)
            model.appendRow(q_item)
        combo.setModel(model)
        # combo.setCurrentIndex(-1) # force index change
        # combo.currentIndexChanged.connect(self.current_index_changed)
        return combo

    def setEditorData(self, editor, index):
        """Show pop up as soon as editing starts."""
        pass


class DataStoreDelegate(ComboBoxDelegate):
    """A custom delegate for the parameter value models and views in DataStoreForm."""
    def __init__(self, parent):
        super().__init__(parent)
        self._parent = parent
        self.mapping = parent.mapping
        self.highlight_pen = QPen(self._parent.palette().highlight(), 1)

    def setEditorData(self, editor, index):
        """Init the line editor with previous data from the index."""
        if isinstance(editor, QComboBox):
            super().setEditorData(editor, index)
        else:
            LineEditDelegate.setEditorData(self, editor, index)


class ParameterValueDelegate(DataStoreDelegate):
    """A QComboBox delegate for the (object and relationship) parameter
    value models and views in DataStoreForm.
    """
    def __init__(self, parent):
        super().__init__(parent)

    def paint(self, painter, option, proxy_index):
        """Paint a blue frame on the work in progress rows."""
        super().paint(painter, option, proxy_index)
        model = proxy_index.model().sourceModel()
        index = proxy_index.model().mapToSource(proxy_index)
        h = model.header.index
        if proxy_index.model().is_work_in_progress(index.row()):
            pen = painter.pen()
            painter.setPen(self.highlight_pen)
            x1, y1, x2, y2 = option.rect.getCoords()
            painter.drawLine(x1, y1, x2, y1)
            painter.drawLine(x1, y2, x2, y2)
            if index.column() == 0:
                painter.drawLine(x1+1, y1, x1+1, y2)
            if index.column() == model.columnCount()-1:
                painter.drawLine(x2, y1, x2, y2)
            painter.setPen(pen)


class ParameterDelegate(DataStoreDelegate):
    """A QComboBox delegate for the (object and relationship) parameter
    models and views in DataStoreForm.
    """
    def __init__(self, parent):
        super().__init__(parent)

    def paint(self, painter, option, proxy_index):
        """Paint a blue frame on the work in progress rows."""
        super().paint(painter, option, proxy_index)
        model = proxy_index.model().sourceModel()
        index = proxy_index.model().mapToSource(proxy_index)
        h = model.header.index
        if proxy_index.model().is_work_in_progress(index.row()):
            pen = painter.pen()
            painter.setPen(self.highlight_pen)
            x1, y1, x2, y2 = option.rect.getCoords()
            painter.drawLine(x1, y1, x2, y1)
            painter.drawLine(x1, y2, x2, y2)
            if index.column() == 0:
                painter.drawLine(x1+1, y1, x1+1, y2)
            if index.column() == model.columnCount()-1:
                painter.drawLine(x2, y1, x2, y2)
            painter.setPen(pen)


class ObjectParameterValueDelegate(ParameterValueDelegate):
    """A QComboBox delegate for the object parameter value model and view in DataStoreForm."""
    def __init__(self, parent):
        super().__init__(parent)

    def createEditor(self, parent, option, proxy_index):
        """Return CustomComboEditor."""
        model = proxy_index.model().sourceModel()
        index = proxy_index.model().mapToSource(proxy_index)
        h = model.header.index
        if index.column() not in (h('object_class_name'), h('object_name'), h('parameter_name')):
            return LineEditDelegate.createEditor(self, parent, option, proxy_index)
        combo = CustomComboEditor(parent)
        combo.index = proxy_index
        if index.column() == h('object_class_name'):
            object_class_name_list = [x.name for x in self.mapping.object_class_list()]
            combo.addItems(object_class_name_list)
        elif index.column() == h('object_name'):
            object_class_name = index.sibling(index.row(), h('object_class_name')).data(Qt.DisplayRole)
            object_class = self.mapping.single_object_class(name=object_class_name).one_or_none()
            if not object_class:
                object_name_list = list()
            else:
                object_name_list = [x.name for x in self.mapping.object_list(class_id=object_class.id)]
            combo.addItems(object_name_list)
        elif index.column() == h('parameter_name'):
            object_name = index.sibling(index.row(), h('object_name')).data(Qt.DisplayRole)
            object_ = self.mapping.single_object(name=object_name).one_or_none()
            if not object_:
                parameter_list = list()
            else:
                parameter_list = self.mapping.unvalued_object_parameter_list(object_.id)
            parameter_name_list = [x.name for x in parameter_list]
            combo.addItems(parameter_name_list)
        combo.setCurrentIndex(-1) # force index change
        combo.currentIndexChanged.connect(self.current_index_changed)
        return combo


class ObjectParameterDelegate(ParameterDelegate):
    """A QComboBox delegate for the object parameter model and view in DataStoreForm."""
    def __init__(self, parent):
        super().__init__(parent)

    def createEditor(self, parent, option, proxy_index):
        """Return CustomComboEditor."""
        combo = CustomComboEditor(parent)
        combo.index = proxy_index
        model = proxy_index.model().sourceModel()
        index = proxy_index.model().mapToSource(proxy_index)
        header = model.header
        h = header.index
        if not index.column() == h('object_class_name'):
            return LineEditDelegate.createEditor(self, parent, option, proxy_index)
        object_class_name_list = [x.name for x in self.mapping.object_class_list()]
        combo.addItems(object_class_name_list)
        combo.setCurrentIndex(-1) # force index change
        combo.currentIndexChanged.connect(self.current_index_changed)
        return combo


class RelationshipParameterValueDelegate(ParameterValueDelegate):
    """A QComboBox delegate for the relationship parameter value model and view in DataStoreForm."""
    def __init__(self, parent):
        super().__init__(parent)

    def createEditor(self, parent, option, proxy_index):
        """Return CustomComboEditor."""
        model = proxy_index.model().sourceModel()
        index = proxy_index.model().mapToSource(proxy_index)
        header = model.header
        h = header.index
        if index.column() not in (h('relationship_class_name'), h('relationship_name'), h('parameter_name')):
            return LineEditDelegate.createEditor(self, parent, option, proxy_index)
        combo = CustomComboEditor(parent)
        combo.index = proxy_index
        if index.column() == h('relationship_class_name'):
            relationship_class_name_list = [x.name for x in self.mapping.wide_relationship_class_list()]
            combo.addItems(relationship_class_name_list)
        elif index.column() == h('relationship_name'):
            relationship_class_name = index.sibling(index.row(), h('relationship_class_name')).data(Qt.DisplayRole)
            relationship_class = self.mapping.single_wide_relationship_class(name=relationship_class_name).one_or_none()
            if not relationship_class:
                relationship_name_list = list()
            else:
                wide_relationship_list = self.mapping.wide_relationship_list(class_id=relationship_class.id)
                relationship_name_list = [x.name for x in wide_relationship_list]
            combo.addItems(relationship_name_list)
        elif index.column() == h('parameter_name'):
            relationship_name = index.sibling(index.row(), h('relationship_name')).data(Qt.DisplayRole)
            relationship = self.mapping.single_wide_relationship(name=relationship_name).one_or_none()
            if not relationship:
                parameter_list = list()
            else:
                parameter_list = self.mapping.unvalued_relationship_parameter_list(relationship.id)
            parameter_name_list = [x.name for x in parameter_list]
            combo.addItems(parameter_name_list)
        combo.setCurrentIndex(-1) # force index change
        combo.currentIndexChanged.connect(self.current_index_changed)
        return combo


class RelationshipParameterDelegate(ParameterDelegate):
    """A QComboBox delegate for the object parameter model and view in DataStoreForm."""
    def __init__(self, parent):
        super().__init__(parent)

    def createEditor(self, parent, option, proxy_index):
        """Return CustomComboEditor."""
        combo = CustomComboEditor(parent)
        combo.index = proxy_index
        model = proxy_index.model().sourceModel()
        index = proxy_index.model().mapToSource(proxy_index)
        header = model.header
        h = header.index
        if not index.column() == h('relationship_class_name'):
            return LineEditDelegate.createEditor(self, parent, option, proxy_index)
        relationship_class_name_list = [x.name for x in self.mapping.wide_relationship_class_list()]
        combo.addItems(relationship_class_name_list)
        combo.setCurrentIndex(-1) # force index change
        combo.currentIndexChanged.connect(self.current_index_changed)
        return combo

class AddObjectsDelegate(DataStoreDelegate):
    """A QComboBox delegate for the model and view in AddObjectsDialog."""
    def __init__(self, parent):
        super().__init__(parent)

    def createEditor(self, parent, option, index):
        """Return CustomComboEditor."""
        combo = CustomComboEditor(parent)
        combo.index = index
        model = index.model()
        header = model.header
        h = header.index
        if index.column() != h('object class name'):
            return LineEditDelegate.createEditor(self, parent, option, index)
        object_class_name_list = [x.name for x in self.mapping.object_class_list()]
        combo.addItems(object_class_name_list)
        combo.setCurrentIndex(-1) # force index change
        combo.currentIndexChanged.connect(self.current_index_changed)
        return combo


class AddRelationshipClassesDelegate(DataStoreDelegate):
    """A QComboBox delegate for the model and view in AddRelationshipClassesDialog."""
    def __init__(self, parent):
        super().__init__(parent)

    def createEditor(self, parent, option, index):
        """Return CustomComboEditor."""
        combo = CustomComboEditor(parent)
        combo.index = index
        model = index.model()
        header = model.header
        h = header.index
        if index.column() == h('relationship class name'):
            return LineEditDelegate.createEditor(self, parent, option, index)
        object_class_name_list = [x.name for x in self.mapping.object_class_list()]
        combo.addItems(object_class_name_list)
        combo.setCurrentIndex(-1) # force index change
        combo.currentIndexChanged.connect(self.current_index_changed)
        return combo


class AddRelationshipsDelegate(DataStoreDelegate):
    """A QComboBox delegate for the model and view in AddRelationshipsDialog."""
    def __init__(self, parent):
        super().__init__(parent)

    def createEditor(self, parent, option, index):
        """Return CustomComboEditor."""
        combo = CustomComboEditor(parent)
        combo.index = index
        model = index.model()
        header = model.header
        h = header.index
        if index.column() == h('relationship name'):
            return LineEditDelegate.createEditor(self, parent, option, index)
        object_class_name = header[index.column()].split(' ', 1)[0]
        object_class = self.mapping.single_object_class(name=object_class_name).one_or_none()
        if not object_class:
            object_name_list = list()
        else:
            object_name_list = [x.name for x in self.mapping.object_list(class_id=object_class.id)]
        combo.addItems(object_name_list)
        combo.setCurrentIndex(-1) # force index change
        combo.currentIndexChanged.connect(self.current_index_changed)
        return combo


class CustomComboEditor(QComboBox):
    """A custom QComboBox to handle data from the model."""
    def __init__(self, parent):
        super().__init__(parent)
        self.text = self.currentText
        self.index = None
        self.previous_data = None
        self.row = None
        self.column = None
