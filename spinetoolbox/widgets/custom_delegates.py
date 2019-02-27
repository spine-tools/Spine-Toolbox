######################################################################################################################
# Copyright (C) 2017 - 2018 Spine project consortium
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
from PySide2.QtCore import Qt, Signal, Slot, QEvent, QPoint, QRect
from PySide2.QtWidgets import QAbstractItemDelegate, QItemDelegate, QStyleOptionButton, QStyle, \
    QApplication, QStyleOptionViewItem, QWidget
from widgets.custom_editors import CustomComboEditor, CustomLineEditor, SearchBarEditor, \
    MultiSearchBarEditor, CheckListEditor, JSONEditor
from models import MinimalTableModel
import logging


class LineEditDelegate(QItemDelegate):
    """A delegate that places a fully functioning QLineEdit.

    Attributes:
        parent (QMainWindow): either data store or spine datapackage widget
    """
    data_committed = Signal("QModelIndex", "QVariant", name="data_committed")

    def __init__(self, parent):
        super().__init__(parent)

    def createEditor(self, parent, option, index):
        """Return CustomLineEditor. Set up a validator depending on datatype."""
        return CustomLineEditor(parent)

    def setEditorData(self, editor, index):
        """Init the line editor with previous data from the index."""
        editor.set_data(index.data(Qt.EditRole))

    def setModelData(self, editor, model, index):
        """Send signal."""
        self.data_committed.emit(index, editor.data())


class CheckBoxDelegate(QItemDelegate):
    """A delegate that places a fully functioning QCheckBox.

    Attributes:
        parent (QMainWindow): either toolbox or spine datapackage widget
        centered (bool): whether or not the checkbox should be center-aligned in the widget
    """

    data_committed = Signal("QModelIndex", name="data_committed")

    def __init__(self, parent, centered=True):
        super().__init__(parent)
        self._centered = centered
        self.mouse_press_point = QPoint()

    def createEditor(self, parent, option, index):
        """Important, otherwise an editor is created if the user clicks in this cell.
        ** Need to hook up a signal to the model."""
        return None

    def paint(self, painter, option, index):
        """Paint a checkbox without the label."""
        if (option.state & QStyle.State_Selected):
            painter.fillRect(option.rect, option.palette.highlight())
        checked = True
        if index.data() == False:
            checked = False
        elif index.data() == True:
            checked = True
        else:
            checked = None
        checkbox_style_option = QStyleOptionButton()
        if (index.flags() & Qt.ItemIsEditable) > 0:
            checkbox_style_option.state |= QStyle.State_Enabled
        else:
            checkbox_style_option.state |= QStyle.State_ReadOnly
        if checked == True:
            checkbox_style_option.state |= QStyle.State_On
        elif checked == False:
            checkbox_style_option.state |= QStyle.State_Off
        elif checked is None:
            checkbox_style_option.state |= QStyle.State_NoChange
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
                self.mouse_press_point = event.pos()
                return True
        if event.type() == QEvent.MouseButtonRelease:
            checkbox_rect = self.get_checkbox_rect(option)
            if checkbox_rect.contains(self.mouse_press_point) and checkbox_rect.contains(event.pos()):
                # Change the checkbox-state
                self.data_committed.emit(index)
                self.mouse_press_point = QPoint()
                return True
            self.mouse_press_point = QPoint()
        return False

    def setModelData(self, editor, model, index):
        """Do nothing. Model data is updated by handling the `data_committed` signal."""
        pass

    def get_checkbox_rect(self, option):
        checkbox_style_option = QStyleOptionButton()
        checkbox_rect = QApplication.style().subElementRect(QStyle.SE_CheckBoxIndicator, checkbox_style_option, None)
        if self._centered:
            checkbox_anchor = QPoint(option.rect.x() + option.rect.width() / 2 - checkbox_rect.width() / 2,
                                     option.rect.y() + option.rect.height() / 2 - checkbox_rect.height() / 2)
        else:
            checkbox_anchor = QPoint(option.rect.x() + checkbox_rect.width() / 2,
                                     option.rect.y() + checkbox_rect.height() / 2)
        return QRect(checkbox_anchor, checkbox_rect.size())


class ParameterDelegate(QItemDelegate):
    """A custom delegate for the parameter models and views in TreeViewForm.

    Attributes:
        parent (QMainWindow): tree or graph view form
    """
    data_committed = Signal("QModelIndex", "QVariant", name="data_committed")

    def __init__(self, parent):
        super().__init__(parent)
        self._parent = parent
        self.db_map = parent.db_map

    def setModelData(self, editor, model, index):
        """Send signal."""
        self.data_committed.emit(index, editor.data())

    def close_editor(self, editor, index, model):
        self.closeEditor.emit(editor)
        self.setModelData(editor, model, index)

    def updateEditorGeometry(self, editor, option, index):
        super().updateEditorGeometry(editor, option, index)
        if type(editor) in (SearchBarEditor, CheckListEditor, MultiSearchBarEditor, JSONEditor):
            size = option.rect.size()
            if index.data(Qt.DecorationRole):
                size.setWidth(size.width() - 22)  # FIXME
            editor.set_base_size(size)
            editor.update_geometry()


class ParameterValueDelegate(ParameterDelegate):
    """A custom delegate for the parameter value models and views in TreeViewForm.

    Attributes:
        parent (QMainWindow): tree or graph view form
    """
    def __init__(self, parent):
        super().__init__(parent)
        self.json_editor_index = 0
        self.json_popup = None
        self.last_index = None
        self.view = None

    @Slot("int", name="_handle_json_editor_current_changed")
    def _handle_json_editor_current_changed(self, index):
        self.json_editor_index = index

    def editorEvent(self, event, model, option, index):
        """Show json popup on hover.
        """
        if event.type() != QEvent.MouseMove:
            return super().editorEvent(event, model, option, index)
        if self.last_index == index:
            return super().editorEvent(event, model, option, index)
        self.last_index = index
        self.destroy_json_popup()
        header = index.model().horizontal_header_labels()
        if header[index.column()] != 'json':
            return super().editorEvent(event, model, option, index)
        if not index.data(Qt.EditRole):
            return super().editorEvent(event, model, option, index)
        self.json_popup = JSONEditor(self._parent, self.view, popup=True)
        self.json_popup.currentChanged.connect(self._handle_json_editor_current_changed)
        self.json_popup.set_data(index.data(Qt.EditRole), self.json_editor_index)
        self.json_popup.data_committed.connect(self.destroy_json_popup)
        self.updateEditorGeometry(self.json_popup, option, index)
        self.json_popup.show()
        return True

    def destroy_json_popup(self):
        if self.json_popup:
            self.json_popup.deleteLater()
            self.json_popup = None


class ObjectParameterValueDelegate(ParameterValueDelegate):
    """A delegate for the object parameter value model and view in TreeViewForm.

    Attributes:
        parent (QMainWindow): tree or graph view form
    """
    def __init__(self, parent):
        super().__init__(parent)
        self.view = parent.ui.tableView_object_parameter_value

    def createEditor(self, parent, option, index):
        """Return editor."""
        header = index.model().horizontal_header_labels()
        h = header.index
        if header[index.column()] == 'object_class_name':
            editor = SearchBarEditor(self._parent, parent)
            name_list = [x.name for x in self.db_map.object_class_list()]
            editor.set_data(index.data(Qt.EditRole), name_list)
        elif header[index.column()] == 'object_name':
            editor = SearchBarEditor(self._parent, parent)
            object_class_id = index.sibling(index.row(), h('object_class_id')).data(Qt.DisplayRole)
            name_list = [x.name for x in self.db_map.object_list(class_id=object_class_id)]
            editor.set_data(index.data(Qt.EditRole), name_list)
        elif header[index.column()] == 'parameter_name':
            editor = SearchBarEditor(self._parent, parent)
            object_class_id = index.sibling(index.row(), h('object_class_id')).data(Qt.DisplayRole)
            name_list = [x.parameter_name for x in self.db_map.object_parameter_list(object_class_id=object_class_id)]
            editor.set_data(index.data(Qt.EditRole), name_list)
        elif header[index.column()] == 'value':
            parameter_id = index.sibling(index.row(), h('parameter_id')).data(Qt.DisplayRole)
            parameter = self.db_map.single_parameter(id=parameter_id).one_or_none()
            if parameter:
                enum = self.db_map.wide_parameter_enum_list(id_list=[parameter.enum_id]).one_or_none()
            else:
                enum = None
            if enum:
                editor = SearchBarEditor(self._parent, parent)
                editor.set_data(index.data(Qt.EditRole), enum.value_list.split(","))
            else:
                editor = CustomLineEditor(parent)
                editor.set_data(index.data(Qt.EditRole))
        elif header[index.column()] == 'json':
            self.destroy_json_popup()
            editor = JSONEditor(self._parent, parent)
            editor.currentChanged.connect(self._handle_json_editor_current_changed)
            editor.set_data(index.data(Qt.EditRole), self.json_editor_index)
        else:
            editor = CustomLineEditor(parent)
        model = index.model()
        editor.data_committed.connect(lambda e=editor, i=index, m=model: self.close_editor(e, i, m))
        return editor


class ObjectParameterDefinitionDelegate(ParameterDelegate):
    """A delegate for the object parameter definition model and view in TreeViewForm.

    Attributes:
        parent (QMainWindow): tree or graph view form
    """
    def __init__(self, parent):
        super().__init__(parent)

    def createEditor(self, parent, option, index):
        """Return editor."""
        header = index.model().horizontal_header_labels()
        if header[index.column()] == 'object_class_name':
            editor = SearchBarEditor(self._parent, parent)
            name_list = [x.name for x in self.db_map.object_class_list()]
            editor.set_data(index.data(Qt.EditRole), name_list)
        elif header[index.column()] == 'parameter_tag_list':
            editor = CheckListEditor(self._parent, parent)
            all_parameter_tag_list = [x.tag for x in self.db_map.parameter_tag_list()]
            try:
                parameter_tag_list = index.data(Qt.EditRole).split(",")
            except AttributeError:
                parameter_tag_list = []
            editor.set_data(all_parameter_tag_list, parameter_tag_list)
        elif header[index.column()] == 'enum_name':
            editor = SearchBarEditor(self._parent, parent)
            name_list = [x.name for x in self.db_map.wide_parameter_enum_list()]
            editor.set_data(index.data(Qt.EditRole), name_list)
        else:
            editor = CustomLineEditor(parent)
            editor.set_data(index.data(Qt.EditRole))
        model = index.model()
        editor.data_committed.connect(lambda e=editor, i=index, m=model: self.close_editor(e, i, m))
        return editor


class RelationshipParameterValueDelegate(ParameterValueDelegate):
    """A delegate for the relationship parameter value model and view in TreeViewForm.

    Attributes:
        parent (QMainWindow): tree or graph view form
    """
    def __init__(self, parent):
        super().__init__(parent)
        self.view = parent.ui.tableView_relationship_parameter_value

    def createEditor(self, parent, option, index):
        """Return editor."""
        header = index.model().horizontal_header_labels()
        h = header.index
        if header[index.column()] == 'relationship_class_name':
            editor = SearchBarEditor(self._parent, parent)
            name_list = [x.name for x in self.db_map.wide_relationship_class_list()]
            editor.set_data(index.data(Qt.EditRole), name_list)
        elif header[index.column()] == 'object_name_list':
            object_class_id_list = index.sibling(index.row(), h('object_class_id_list')).data(Qt.DisplayRole)
            if not object_class_id_list:
                editor = CustomLineEditor(parent)
            else:
                editor = MultiSearchBarEditor(self._parent, parent)
                object_class_ids = [int(x) for x in object_class_id_list.split(',')]
                object_class_dict = {x.id: x.name for x in self.db_map.object_class_list(id_list=object_class_ids)}
                object_class_names = [object_class_dict[x] for x in object_class_ids]
                object_name_list = index.data(Qt.EditRole)
                current_object_names = object_name_list.split(",") if object_name_list else []
                all_object_names_list = list()
                for class_id in object_class_ids:
                    all_object_names_list.append([x.name for x in self.db_map.object_list(class_id=class_id)])
                editor.set_data(object_class_names, current_object_names, all_object_names_list)
        elif header[index.column()] == 'parameter_name':
            editor = SearchBarEditor(self._parent, parent)
            relationship_class_id = index.sibling(index.row(), h('relationship_class_id')).data(Qt.DisplayRole)
            parameter_list = self.db_map.relationship_parameter_list(relationship_class_id=relationship_class_id)
            name_list = [x.parameter_name for x in parameter_list]
            editor.set_data(index.data(Qt.EditRole), name_list)
        elif header[index.column()] == 'value':
            parameter_id = index.sibling(index.row(), h('parameter_id')).data(Qt.DisplayRole)
            parameter = self.db_map.single_parameter(id=parameter_id).one_or_none()
            if parameter:
                enum = self.db_map.wide_parameter_enum_list(id_list=[parameter.enum_id]).one_or_none()
            else:
                enum = None
            if enum:
                editor = SearchBarEditor(self._parent, parent)
                editor.set_data(index.data(Qt.EditRole), enum.value_list.split(","))
            else:
                editor = CustomLineEditor(parent)
                editor.set_data(index.data(Qt.EditRole))
        elif header[index.column()] == 'json':
            self.destroy_json_popup()
            editor = JSONEditor(self._parent, parent)
            editor.currentChanged.connect(self._handle_json_editor_current_changed)
            editor.set_data(index.data(Qt.EditRole), self.json_editor_index)
        else:
            editor = CustomLineEditor(parent)
            editor.set_data(index.data(Qt.EditRole))
        model = index.model()
        editor.data_committed.connect(lambda e=editor, i=index, m=model: self.close_editor(e, i, m))
        return editor


class RelationshipParameterDefinitionDelegate(ParameterDelegate):
    """A delegate for the object parameter definition model and view in TreeViewForm.

    Attributes:
        parent (QMainWindow): tree or graph view form
    """
    def __init__(self, parent):
        super().__init__(parent)

    def createEditor(self, parent, option, index):
        """Return editor."""
        header = index.model().horizontal_header_labels()
        if header[index.column()] == 'relationship_class_name':
            editor = SearchBarEditor(self._parent, parent)
            name_list = [x.name for x in self.db_map.wide_relationship_class_list()]
            editor.set_data(index.data(Qt.EditRole), name_list)
        elif header[index.column()] == 'parameter_tag_list':
            editor = CheckListEditor(self._parent, parent)
            all_parameter_tag_list = [x.tag for x in self.db_map.parameter_tag_list()]
            try:
                parameter_tag_list = index.data(Qt.EditRole).split(",")
            except AttributeError:
                parameter_tag_list = []
            editor.set_data(all_parameter_tag_list, parameter_tag_list)
        elif header[index.column()] == 'enum_name':
            editor = SearchBarEditor(self._parent, parent)
            name_list = [x.name for x in self.db_map.wide_parameter_enum_list()]
            editor.set_data(index.data(Qt.EditRole), name_list)
        else:
            editor = CustomLineEditor(parent)
            editor.set_data(index.data(Qt.EditRole))
        model = index.model()
        editor.data_committed.connect(lambda e=editor, i=index, m=model: self.close_editor(e, i, m))
        return editor


class AddItemsDelegate(QItemDelegate):
    """A custom delegate for the model in AddItemDialogs.

    Attributes:
        parent (QMainWindow): tree or graph view form
    """
    data_committed = Signal("QModelIndex", "QVariant", name="data_committed")

    def __init__(self, parent):
        super().__init__(parent)
        self._parent = parent
        self.db_map = parent.db_map

    def setModelData(self, editor, model, index):
        """Send signal."""
        self.data_committed.emit(index, editor.data())

    def close_editor(self, editor, index, model):
        self.closeEditor.emit(editor)
        self.setModelData(editor, model, index)


class AddObjectsDelegate(AddItemsDelegate):
    """A delegate for the model and view in AddObjectsDialog.

    Attributes:
        parent (QMainWindow): tree or graph view form
    """
    def __init__(self, parent):
        super().__init__(parent)

    def createEditor(self, parent, option, index):
        """Return editor."""
        header = index.model().horizontal_header_labels()
        if header[index.column()] == 'object class name':
            editor = CustomComboEditor(parent)
        else:
            editor = CustomLineEditor(parent)
        model = index.model()
        editor.data_committed.connect(lambda e=editor, i=index, m=model: self.close_editor(e, i, m))
        return editor

    def setEditorData(self, editor, index):
        """Set editor data."""
        header = index.model().horizontal_header_labels()
        if header[index.column()] == 'object class name':
            object_class_name_list = [x.name for x in self.db_map.object_class_list()]
            editor.set_data(index.data(Qt.EditRole), object_class_name_list)
        else:
            editor.set_data(index.data(Qt.EditRole))


class AddRelationshipClassesDelegate(AddItemsDelegate):
    """A delegate for the model and view in AddRelationshipClassesDialog.

    Attributes:
        parent (QMainWindow): tree or graph view form
    """
    def __init__(self, parent):
        super().__init__(parent)

    def createEditor(self, parent, option, index):
        """Return editor."""
        header = index.model().horizontal_header_labels()
        if header[index.column()] == 'relationship class name':
            editor = CustomLineEditor(parent)
        else:
            editor = CustomComboEditor(parent)
        model = index.model()
        editor.data_committed.connect(lambda e=editor, i=index, m=model: self.close_editor(e, i, m))
        return editor

    def setEditorData(self, editor, index):
        """Set editor data."""
        header = index.model().horizontal_header_labels()
        if header[index.column()] == 'relationship class name':
            data = index.data(Qt.EditRole)
            if data:
                editor.set_data(index.data(Qt.EditRole))
            else:
                editor.set_data(self.relationship_class_name(index))
        else:
            object_class_name_list = [x.name for x in self.db_map.object_class_list()]
            editor.set_data(index.data(Qt.EditRole), object_class_name_list)

    def relationship_class_name(self, index):
        """A relationship class name composed by concatenating object class names."""
        object_class_name_list = list()
        for column in range(index.column()):
            object_class_name = index.sibling(index.row(), column).data(Qt.DisplayRole)
            if object_class_name:
                object_class_name_list.append(object_class_name)
        return "__".join(object_class_name_list)


class AddRelationshipsDelegate(AddItemsDelegate):
    """A delegate for the model and view in AddRelationshipsDialog.

    Attributes:
        parent (QMainWindow): tree or graph view form
    """
    def __init__(self, parent):
        super().__init__(parent)

    def createEditor(self, parent, option, index):
        """Return editor."""
        header = index.model().horizontal_header_labels()
        if header[index.column()] == 'relationship name':
            editor = CustomLineEditor(parent)
        else:
            editor = CustomComboEditor(parent)
        model = index.model()
        editor.data_committed.connect(lambda e=editor, i=index, m=model: self.close_editor(e, i, m))
        return editor

    def setEditorData(self, editor, index):
        """Set editor data."""
        header = index.model().horizontal_header_labels()
        if header[index.column()] == 'relationship name':
            data = index.data(Qt.EditRole)
            if data:
                editor.set_data(data)
            else:
                editor.set_data(self.relationship_name(index))
        else:
            object_class_name = header[index.column()].split(' ', 1)[0]
            object_class = self.db_map.single_object_class(name=object_class_name).one_or_none()
            if not object_class:
                object_name_list = list()
            else:
                object_name_list = [x.name for x in self.db_map.object_list(class_id=object_class.id)]
            editor.set_data(index.data(Qt.EditRole), object_name_list)

    def relationship_name(self, index):
        """A relationship name composed by concatenating object names."""
        object_name_list = list()
        for column in range(index.column()):
            object_name = index.sibling(index.row(), column).data(Qt.DisplayRole)
            if object_name:
                object_name_list.append(object_name)
        return "__".join(object_name_list)


class AddParameterEnumsDelegate(LineEditDelegate):
    """A delegate for the model and view in AddRelationshipsDialog.

    Attributes:
        parent (QMainWindow): tree or graph view form
    """
    def __init__(self, parent):
        super().__init__(parent)


class ForeignKeysDelegate(QItemDelegate):
    """A QComboBox delegate with checkboxes.

    Attributes:
        parent (SpineDatapackageWidget): spine datapackage widget
    """
    data_committed = Signal("QModelIndex", "QVariant", name="data_committed")

    def close_field_name_list_editor(self, editor, index, model):
        self.closeEditor.emit(editor)
        self.data_committed.emit(index, editor.data())

    def __init__(self, parent):
        super().__init__(parent)
        self._parent = parent
        self.datapackage = None
        self.selected_resource_name = None

    def createEditor(self, parent, option, index):
        """Return editor."""
        header = index.model().horizontal_header_labels()
        if header[index.column()] == 'fields':
            editor = CheckListEditor(self._parent, parent)
            model = index.model()
            editor.data_committed.connect(
                lambda e=editor, i=index, m=model: self.close_field_name_list_editor(e, i, m))
            return editor
        elif header[index.column()] == 'reference resource':
            return CustomComboEditor(parent)
        elif header[index.column()] == 'reference fields':
            editor = CheckListEditor(self._parent, parent)
            model = index.model()
            editor.data_committed.connect(
                lambda e=editor, i=index, m=model: self.close_field_name_list_editor(e, i, m))
            return editor
        else:
            return None

    def setEditorData(self, editor, index):
        """Set editor data."""
        self.datapackage = self._parent.datapackage
        self.selected_resource_name = self._parent.selected_resource_name
        header = index.model().horizontal_header_labels()
        h = header.index
        if header[index.column()] == 'fields':
            current_field_names = index.data(Qt.DisplayRole).split(',') if index.data(Qt.DisplayRole) else []
            field_names = self.datapackage.get_resource(self.selected_resource_name).schema.field_names
            editor.set_data(field_names, current_field_names)
        elif header[index.column()] == 'reference resource':
            editor.set_data(index.data(Qt.EditRole), self.datapackage.resource_names)
        elif header[index.column()] == 'reference fields':
            current_field_names = index.data(Qt.DisplayRole).split(',') if index.data(Qt.DisplayRole) else []
            reference_resource_name = index.sibling(index.row(), h('reference resource')).data(Qt.DisplayRole)
            reference_resource = self.datapackage.get_resource(reference_resource_name)
            if not reference_resource:
                field_names = []
            else:
                field_names = reference_resource.schema.field_names
            editor.set_data(field_names, current_field_names)

    def setModelData(self, editor, model, index):
        """Send signal."""
        self.data_committed.emit(index, editor.data())
