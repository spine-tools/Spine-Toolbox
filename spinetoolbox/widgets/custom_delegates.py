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
Custom item delegates.

:author: M. Marin (KTH)
:date:   1.9.2018
"""
from PySide2.QtCore import Qt, Signal, QEvent, QPoint, QRect
from PySide2.QtWidgets import QAbstractItemDelegate, QItemDelegate, QStyleOptionButton, QStyle, QApplication
from PySide2.QtGui import QPen
from widgets.custom_editors import CustomComboEditor, CustomLineEditor, CustomSimpleToolButtonEditor


class LineEditDelegate(QItemDelegate):
    """A delegate that places a fully functioning QLineEdit.

    Attributes:
        parent (QMainWindow): either data store or spine datapackage widget
    """
    def __init__(self, parent):
        super().__init__(parent)

    def createEditor(self, parent, option, index):
        """Return CustomLineEditor. Set up a validator depending on datatype."""
        return CustomLineEditor(parent, index)

    def setEditorData(self, editor, index):
        """Init the line editor with previous data from the index."""
        data = index.data(Qt.EditRole)
        if data:
            editor.setText(str(data))

    def setModelData(self, editor, model, index):
        """Do nothing. Model data is updated by handling the `closeEditor` signal."""
        pass


class CheckBoxDelegate(QItemDelegate):
    """A delegate that places a fully functioning QCheckBox.

    Attributes:
        parent (QMainWindow): either toolbox or spine datapackage widget
    """

    commit_data = Signal("QModelIndex", name="commit_data")

    def __init__(self, parent):
        super().__init__(parent)
        self.checkbox_pressed = False

    def createEditor(self, parent, option, index):
        """Important, otherwise an editor is created if the user clicks in this cell.
        ** Need to hook up a signal to the model."""
        return None

    def paint(self, painter, option, index):
        """Paint a checkbox without the label."""
        checked = True
        if index.data() == "False" or not index.data():
            checked = False
        checkbox_style_option = QStyleOptionButton()
        if (index.flags() & Qt.ItemIsEditable) > 0:
            checkbox_style_option.state |= QStyle.State_Enabled
        else:
            checkbox_style_option.state |= QStyle.State_ReadOnly
        if checked:
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
            if event.button() == Qt.LeftButton and self.get_checkbox_rect(option).contains(event.pos()):
                self.checkbox_pressed = True
                return True
        if event.type() == QEvent.MouseButtonRelease:
            if self.checkbox_pressed and self.get_checkbox_rect(option).contains(event.pos()):
                # Change the checkbox-state
                # self.setModelData(None, model, index)
                self.commit_data.emit(index)
                self.checkbox_pressed = False
                return True
            self.checkbox_pressed = False
        return False

    def setModelData(self, editor, model, index):
        """Do nothing. Model data is updated by handling the `commit_data` signal."""
        pass

    def get_checkbox_rect(self, option):
        checkbox_style_option = QStyleOptionButton()
        checkbox_rect = QApplication.style().subElementRect(QStyle.SE_CheckBoxIndicator, checkbox_style_option, None)
        checkbox_point = QPoint(option.rect.x() + option.rect.width() / 2 - checkbox_rect.width() / 2,
                                option.rect.y() + option.rect.height() / 2 - checkbox_rect.height() / 2)
        return QRect(checkbox_point, checkbox_rect.size())


class DataStoreDelegate(QItemDelegate):
    """A custom delegate for the parameter value models and views in DataStoreForm.

    Attributes:
        parent (DataStoreForm): data store widget
    """
    def __init__(self, parent):
        super().__init__(parent)
        self._parent = parent
        self.db_mngr = parent.db_mngr

    def setEditorData(self, editor, index):
        """Do nothing."""
        if isinstance(editor, CustomComboEditor):
            editor.showPopup()
        elif isinstance(editor, CustomLineEditor):
            data = editor.index().data(Qt.EditRole)
            if data:
                editor.setText(str(data))

    def setModelData(self, editor, model, index):
        """Do nothing. Model data is updated by handling the `commitData` signal."""
        pass


class HighlightFrameDelegate(QItemDelegate):
    """A delegate that paints a blue frame around the row.

    Attributes:
        parent (QMainWindow): either data store or spine datapackage widget
    """
    def __init__(self, parent):
        super().__init__(parent)
        self.highlight_pen = QPen(parent.palette().highlight(), 1)

    def paint(self, painter, option, index):
        """Paint a blue frame on the work in progress rows."""
        super().paint(painter, option, index)
        model = index.model()
        if model.is_work_in_progress(index.row()):
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


class ObjectParameterValueDelegate(DataStoreDelegate, HighlightFrameDelegate):
    """A delegate for the object parameter value model and view in DataStoreForm.

    Attributes:
        parent (DataStoreForm): data store widget
    """
    def __init__(self, parent):
        super().__init__(parent)

    def createEditor(self, parent, option, proxy_index):
        """Return editor."""
        model = proxy_index.model().sourceModel()
        index = proxy_index.model().mapToSource(proxy_index)
        h = model.horizontal_header_labels().index
        if index.column() == h('object_class_name'):
            object_class_name_list = [x.name for x in self.db_mngr.object_class_list()]
            return CustomComboEditor(parent, proxy_index, object_class_name_list)
        elif index.column() == h('object_name'):
            parameter_name = index.sibling(index.row(), h('parameter_name')).data(Qt.DisplayRole)
            parameter = self.db_mngr.single_parameter(name=parameter_name).one_or_none()
            if parameter:
                object_list = self.db_mngr.unvalued_object_list(parameter_id=parameter.id)
            else:
                object_class_name = index.sibling(index.row(), h('object_class_name')).data(Qt.DisplayRole)
                object_class = self.db_mngr.single_object_class(name=object_class_name).one_or_none()
                object_class_id = object_class.id if object_class else None
                object_list = self.db_mngr.object_list(class_id=object_class_id)
            object_name_list = [x.name for x in object_list]
            return CustomComboEditor(parent, proxy_index, object_name_list)
        elif index.column() == h('parameter_name'):
            object_name = index.sibling(index.row(), h('object_name')).data(Qt.DisplayRole)
            object_ = self.db_mngr.single_object(name=object_name).one_or_none()
            if object_:
                parameter_list = self.db_mngr.unvalued_object_parameter_list(object_id=object_.id)
                parameter_name_list = [x.name for x in parameter_list]
            else:
                object_class_name = index.sibling(index.row(), h('object_class_name')).data(Qt.DisplayRole)
                object_class = self.db_mngr.single_object_class(name=object_class_name).one_or_none()
                object_class_id = object_class.id if object_class else None
                parameter_list = self.db_mngr.object_parameter_list(object_class_id=object_class_id)
                parameter_name_list = [x.parameter_name for x in parameter_list]
            return CustomComboEditor(parent, proxy_index, parameter_name_list)
        else:
            return CustomLineEditor(parent, proxy_index)


class ObjectParameterDelegate(DataStoreDelegate, HighlightFrameDelegate):
    """A delegate for the object parameter model and view in DataStoreForm.

    Attributes:
        parent (DataStoreForm): data store widget
    """
    def __init__(self, parent):
        super().__init__(parent)

    def createEditor(self, parent, option, proxy_index):
        """Return editor."""
        model = proxy_index.model().sourceModel()
        index = proxy_index.model().mapToSource(proxy_index)
        header = model.horizontal_header_labels()
        h = header.index
        if not index.column() == h('object_class_name'):
            return CustomLineEditor(parent, proxy_index)
        object_class_name_list = [x.name for x in self.db_mngr.object_class_list()]
        return CustomComboEditor(parent, proxy_index, object_class_name_list)


class RelationshipParameterValueDelegate(DataStoreDelegate, HighlightFrameDelegate):
    """A delegate for the relationship parameter value model and view in DataStoreForm.

    Attributes:
        parent (DataStoreForm): data store widget
    """
    def __init__(self, parent):
        super().__init__(parent)

    def createEditor(self, parent, option, proxy_index):
        """Return editor."""
        model = proxy_index.model().sourceModel()
        index = proxy_index.model().mapToSource(proxy_index)
        header = model.horizontal_header_labels()
        h = header.index
        if header[index.column()] == 'relationship_class_name':
            relationship_class_name_list = [x.name for x in self.db_mngr.wide_relationship_class_list()]
            return CustomComboEditor(parent, proxy_index, relationship_class_name_list)
        elif header[index.column()].startswith('object_name_'):
            # Get relationship class
            relationship_class_name = index.sibling(index.row(), h('relationship_class_name')).data(Qt.DisplayRole)
            relationship_class = self.db_mngr.single_wide_relationship_class(name=relationship_class_name).\
                one_or_none()
            if not relationship_class:
                return None
            # Get object class
            dimension = int(header[index.column()].split('object_name_')[1]) - 1
            object_class_name_list = relationship_class.object_class_name_list.split(',')
            try:
                object_class_name = object_class_name_list[dimension]
            except IndexError:
                return None
            object_class = self.db_mngr.single_object_class(name=object_class_name).one_or_none()
            if not object_class:
                return None
            # Get object name list
            object_name_list = [x.name for x in self.db_mngr.object_list(class_id=object_class.id)]
            return CustomComboEditor(parent, proxy_index, object_name_list)
        elif header[index.column()] == 'parameter_name':
            # Get relationship class
            relationship_class_name = index.sibling(index.row(), h('relationship_class_name')).data(Qt.DisplayRole)
            relationship_class = self.db_mngr.single_wide_relationship_class(name=relationship_class_name).\
                one_or_none()
            # Get parameter name list
            if not relationship_class:
                parameter_list = self.db_mngr.relationship_parameter_list()
                parameter_name_list = [x.parameter_name for x in parameter_list]
            else:
                # Get object name list
                object_name_list = list()
                object_class_count = len(relationship_class.object_class_id_list.split(','))
                for j in range(h('object_name_1'), h('object_name_1') + object_class_count):
                    object_name = index.sibling(index.row(), j).data(Qt.DisplayRole)
                    if not object_name:
                        break
                    object_name_list.append(object_name)
                # Get relationship
                relationship = self.db_mngr.single_wide_relationship(
                    class_id=relationship_class.id,
                    object_name_list=",".join(object_name_list)).one_or_none()
                if relationship:
                    parameter_list = self.db_mngr.unvalued_relationship_parameter_list(relationship.id)
                    parameter_name_list = [x.name for x in parameter_list]
                else:
                    parameter_list = self.db_mngr.relationship_parameter_list(
                        relationship_class_id=relationship_class.id)
                    parameter_name_list = [x.parameter_name for x in parameter_list]
            return CustomComboEditor(parent, proxy_index, parameter_name_list)
        else:
            return CustomLineEditor(parent, proxy_index)


class RelationshipParameterDelegate(DataStoreDelegate, HighlightFrameDelegate):
    """A delegate for the object parameter model and view in DataStoreForm.

    Attributes:
        parent (DataStoreForm): data store widget
    """
    def __init__(self, parent):
        super().__init__(parent)

    def createEditor(self, parent, option, proxy_index):
        """Return editor."""
        model = proxy_index.model().sourceModel()
        index = proxy_index.model().mapToSource(proxy_index)
        header = model.horizontal_header_labels()
        h = header.index
        if not index.column() == h('relationship_class_name'):
            return CustomLineEditor(parent, proxy_index)
        relationship_class_name_list = [x.name for x in self.db_mngr.wide_relationship_class_list()]
        return CustomComboEditor(parent, proxy_index, relationship_class_name_list)


class AddObjectsDelegate(DataStoreDelegate):
    """A delegate for the model and view in AddObjectsDialog.

    Attributes:
        parent (DataStoreForm): data store widget
    """
    def __init__(self, parent):
        super().__init__(parent)

    def createEditor(self, parent, option, index):
        """Return editor."""
        model = index.model()
        header = model.horizontal_header_labels()
        h = header.index
        if index.column() != h('object class name'):
            return CustomLineEditor(parent, index)
        object_class_name_list = [x.name for x in self.db_mngr.object_class_list()]
        return CustomComboEditor(parent, index, object_class_name_list)


class AddRelationshipClassesDelegate(DataStoreDelegate):
    """A delegate for the model and view in AddRelationshipClassesDialog.

    Attributes:
        parent (DataStoreForm): data store widget
    """
    def __init__(self, parent):
        super().__init__(parent)

    def createEditor(self, parent, option, index):
        """Return editor."""
        model = index.model()
        header = model.horizontal_header_labels()
        h = header.index
        if index.column() == h('relationship class name'):
            return CustomLineEditor(parent, index)
        object_class_name_list = [x.name for x in self.db_mngr.object_class_list()]
        return CustomComboEditor(parent, index, object_class_name_list)


class AddRelationshipsDelegate(DataStoreDelegate):
    """A delegate for the model and view in AddRelationshipsDialog.

    Attributes:
        parent (DataStoreForm): data store widget
    """
    def __init__(self, parent):
        super().__init__(parent)

    def createEditor(self, parent, option, index):
        """Return editor."""
        model = index.model()
        header = model.horizontal_header_labels()
        h = header.index
        if index.column() == h('relationship name'):
            return CustomLineEditor(parent, index)
        object_class_name = header[index.column()].split(' ', 1)[0]
        object_class = self.db_mngr.single_object_class(name=object_class_name).one_or_none()
        if not object_class:
            object_name_list = list()
        else:
            object_name_list = [x.name for x in self.db_mngr.object_list(class_id=object_class.id)]
        return CustomComboEditor(parent, index, object_name_list)


class ResourceNameDelegate(QItemDelegate):
    """A QComboBox delegate with checkboxes.

    Attributes:
        parent (SpineDatapackageWidget): spine datapackage widget
    """
    def __init__(self, parent):
        super().__init__(parent)
        self._parent = parent

    def createEditor(self, parent, option, index):
        """Return CustomComboEditor. Combo items are obtained from index's Qt.UserRole."""
        items = self._parent.object_class_name_list
        return CustomComboEditor(parent, index, items)

    def setEditorData(self, editor, index):
        """Show pop up as soon as editing starts."""
        editor.showPopup()

    def setModelData(self, editor, model, index):
        """Do nothing. Model data is updated by handling the `commitData` signal."""
        pass


class ForeignKeysDelegate(HighlightFrameDelegate):
    """A QComboBox delegate with checkboxes.

    Attributes:
        parent (SpineDatapackageWidget): spine datapackage widget
    """
    def __init__(self, parent):
        super().__init__(parent)
        self._parent = parent
        self.datapackage = parent.datapackage
        self.selected_resource_name = None

    def createEditor(self, parent, option, index):
        """Return editor."""
        self.selected_resource_name = self._parent.selected_resource_name
        model = index.model()
        header = [model.headerData(j, Qt.Horizontal, Qt.DisplayRole) for j in range(model.columnCount())]
        h = header.index
        if index.column() == h('fields'):
            current_field_names = index.data(Qt.DisplayRole).split(',') if index.data(Qt.DisplayRole) else []
            field_names = self.datapackage.get_resource(self.selected_resource_name).schema.field_names
            return CustomSimpleToolButtonEditor(parent, index, field_names, current_field_names)
        elif index.column() == h('reference resource'):
            return CustomComboEditor(parent, index, self.datapackage.resource_names)
        elif index.column() == h('reference fields'):
            current_field_names = index.data(Qt.DisplayRole).split(',') if index.data(Qt.DisplayRole) else []
            reference_resource_name = index.sibling(index.row(), h('reference resource')).data(Qt.DisplayRole)
            reference_resource = self.datapackage.get_resource(reference_resource_name)
            if not reference_resource:
                return None
            field_names = reference_resource.schema.field_names
            return CustomSimpleToolButtonEditor(parent, index, field_names, current_field_names)
        else:
            return None

    def setEditorData(self, editor, index):
        """Do nothing."""
        pass

    def setModelData(self, editor, model, index):
        """Do nothing."""
        pass

    def eventFilter(self, editor, event):
        """Setup editor in show event, and wrap it up in hide events."""
        if event.type() == QEvent.ShowToParent:
            if isinstance(editor, CustomComboEditor):
                editor.showPopup()
            elif isinstance(editor, CustomSimpleToolButtonEditor):
                editor.click()
            return True
        elif event.type() == QEvent.HideToParent:
            if isinstance(editor, CustomSimpleToolButtonEditor):
                self.commitData.emit(editor)
                self.closeEditor.emit(editor, QAbstractItemDelegate.NoHint)
                return True
        return super().eventFilter(editor, event)
