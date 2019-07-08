######################################################################################################################
# Copyright (C) 2017 - 2019 Spine project consortium
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
from PySide2.QtWidgets import QItemDelegate, QStyleOptionButton, QStyle, QApplication, QStyledItemDelegate
from PySide2.QtGui import QIcon
from widgets.custom_editors import (
    CustomComboEditor,
    CustomLineEditor,
    SearchBarEditor,
    MultiSearchBarEditor,
    CheckListEditor,
    JSONEditor,
    IconColorEditor,
)


class IconColorDialogDelegate(QStyledItemDelegate):
    """A delegate that opens a color picker dialog.

    Attributes:
        parent (DataStoreForm): tree view form.
    """

    data_committed = Signal("QModelIndex", "QVariant", name="data_committed")

    def __init__(self, parent):
        super().__init__(parent)

    def createEditor(self, parent, option, index):
        """Return QColorDialog."""
        # TODO: Find out how to make IconColorEditor movable
        return IconColorEditor(parent, self.parent().icon_mngr)

    def setEditorData(self, editor, index):
        """Set current color from index data."""
        editor.set_data(index.data(Qt.DisplayRole))

    def setModelData(self, editor, model, index):
        """Emit signal with current color."""
        self.data_committed.emit(index, editor.data())

    def paint(self, painter, option, index):
        """Get a pixmap from the index data and paint it in the middle of the cell."""
        pixmap = self.parent().icon_mngr.create_object_pixmap(index.data(Qt.DisplayRole))
        icon = QIcon(pixmap)
        icon.paint(painter, option.rect, Qt.AlignVCenter | Qt.AlignHCenter)


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
            checkbox_anchor = QPoint(
                option.rect.x() + option.rect.width() / 2 - checkbox_rect.width() / 2,
                option.rect.y() + option.rect.height() / 2 - checkbox_rect.height() / 2,
            )
        else:
            checkbox_anchor = QPoint(
                option.rect.x() + checkbox_rect.width() / 2, option.rect.y() + checkbox_rect.height() / 2
            )
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
        self.json_editor_tab_index = 0

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

    @Slot("int", name="_handle_json_editor_current_changed")
    def _handle_json_editor_current_changed(self, index):
        self.json_editor_tab_index = index


class ObjectParameterValueDelegate(ParameterDelegate):
    """A delegate for the object parameter value model and view in TreeViewForm.

    Attributes:
        parent (QMainWindow): tree or graph view form
    """

    def __init__(self, parent):
        super().__init__(parent)

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
            name_list = [
                x.parameter_name for x in self.db_map.object_parameter_definition_list(object_class_id=object_class_id)
            ]
            editor.set_data(index.data(Qt.EditRole), name_list)
        elif header[index.column()] == 'value':
            parameter_id = index.sibling(index.row(), h('parameter_id')).data(Qt.DisplayRole)
            parameter = self.db_map.parameter_definition_list().filter_by(id=parameter_id).one_or_none()
            if parameter:
                parameter_value_list = (
                    self.db_map.wide_parameter_value_list_list()
                    .filter_by(id=parameter.parameter_value_list_id)
                    .one_or_none()
                )
            else:
                parameter_value_list = None
            if parameter_value_list:
                editor = SearchBarEditor(self._parent, parent, is_json=True)
                value_list = parameter_value_list.value_list.split(",")
                editor.set_data(index.data(Qt.DisplayRole), value_list)
            else:
                editor = JSONEditor(self._parent, parent)
                editor.currentChanged.connect(self._handle_json_editor_current_changed)
                editor.set_data(index.data(Qt.EditRole), self.json_editor_tab_index)
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
        elif header[index.column()] == 'default_value':
            editor = JSONEditor(self._parent, parent)
            editor.currentChanged.connect(self._handle_json_editor_current_changed)
            editor.set_data(index.data(Qt.EditRole), self.json_editor_tab_index)
        elif header[index.column()] == 'parameter_tag_list':
            editor = CheckListEditor(self._parent, parent)
            all_parameter_tag_list = [x.tag for x in self.db_map.parameter_tag_list()]
            try:
                parameter_tag_list = index.data(Qt.EditRole).split(",")
            except AttributeError:
                parameter_tag_list = []
            editor.set_data(all_parameter_tag_list, parameter_tag_list)
        elif header[index.column()] == 'value_list_name':
            editor = SearchBarEditor(self._parent, parent)
            name_list = [x.name for x in self.db_map.wide_parameter_value_list_list()]
            editor.set_data(index.data(Qt.EditRole), name_list)
        else:
            editor = CustomLineEditor(parent)
            editor.set_data(index.data(Qt.EditRole))
        model = index.model()
        editor.data_committed.connect(lambda e=editor, i=index, m=model: self.close_editor(e, i, m))
        return editor


class RelationshipParameterValueDelegate(ParameterDelegate):
    """A delegate for the relationship parameter value model and view in TreeViewForm.

    Attributes:
        parent (QMainWindow): tree or graph view form
    """

    def __init__(self, parent):
        super().__init__(parent)

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
            parameter_definition_list = self.db_map.relationship_parameter_definition_list(
                relationship_class_id=relationship_class_id
            )
            name_list = [x.parameter_name for x in parameter_definition_list]
            editor.set_data(index.data(Qt.EditRole), name_list)
        elif header[index.column()] == 'value':
            parameter_id = index.sibling(index.row(), h('parameter_id')).data(Qt.DisplayRole)
            parameter = self.db_map.parameter_definition_list().filter_by(id=parameter_id).one_or_none()
            if parameter:
                parameter_value_list = self.db_map.wide_parameter_value_list_list(
                    id_list=[parameter.parameter_value_list_id]
                ).one_or_none()
            else:
                parameter_value_list = None
            if parameter_value_list:
                editor = SearchBarEditor(self._parent, parent, is_json=True)
                value_list = parameter_value_list.value_list.split(",")
                editor.set_data(index.data(Qt.DisplayRole), value_list)
            else:
                editor = JSONEditor(self._parent, parent)
                editor.currentChanged.connect(self._handle_json_editor_current_changed)
                editor.set_data(index.data(Qt.EditRole), self.json_editor_tab_index)
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
        elif header[index.column()] == 'default_value':
            editor = JSONEditor(self._parent, parent)
            editor.currentChanged.connect(self._handle_json_editor_current_changed)
            editor.set_data(index.data(Qt.EditRole), self.json_editor_tab_index)
        elif header[index.column()] == 'parameter_tag_list':
            editor = CheckListEditor(self._parent, parent)
            all_parameter_tag_list = [x.tag for x in self.db_map.parameter_tag_list()]
            try:
                parameter_tag_list = index.data(Qt.EditRole).split(",")
            except AttributeError:
                parameter_tag_list = []
            editor.set_data(all_parameter_tag_list, parameter_tag_list)
        elif header[index.column()] == 'value_list_name':
            editor = SearchBarEditor(self._parent, parent)
            name_list = [x.name for x in self.db_map.wide_parameter_value_list_list()]
            editor.set_data(index.data(Qt.EditRole), name_list)
        else:
            editor = CustomLineEditor(parent)
            editor.set_data(index.data(Qt.EditRole))
        model = index.model()
        editor.data_committed.connect(lambda e=editor, i=index, m=model: self.close_editor(e, i, m))
        return editor


class ManageItemsDelegate(QItemDelegate):
    """A custom delegate for the model in {Add/Edit}ItemDialogs.

    Attributes:
        parent (DataStoreForm): tree or graph view form
    """

    data_committed = Signal("QModelIndex", "QVariant", name="data_committed")

    def __init__(self, parent):
        super().__init__(parent)
        self._parent = parent

    def setModelData(self, editor, model, index):
        """Send signal."""
        self.data_committed.emit(index, editor.data())

    def close_editor(self, editor, index, model):
        self.closeEditor.emit(editor)
        self.setModelData(editor, model, index)

    def updateEditorGeometry(self, editor, option, index):
        super().updateEditorGeometry(editor, option, index)
        if type(editor) in (SearchBarEditor, CheckListEditor):
            size = option.rect.size()
            if index.data(Qt.DecorationRole):
                size.setWidth(size.width() - 22)  # FIXME
            editor.set_base_size(size)
            editor.update_geometry()


class ManageObjectClassesDelegate(ManageItemsDelegate):
    """A delegate for the model and view in {Add/Edit}ObjectClassesDialog.

    Attributes:
        parent (DataStoreForm): tree or graph view form
    """

    def __init__(self, parent):
        super().__init__(parent)
        self.icon_mngr = parent.parent().icon_mngr

    def createEditor(self, parent, option, index):
        """Return editor."""
        header = index.model().horizontal_header_labels()
        if header[index.column()] == 'display icon':
            editor = IconColorEditor(parent, self.icon_mngr)
            editor.set_data(index.data(Qt.DisplayRole))
        elif header[index.column()] == 'databases':
            editor = CheckListEditor(parent)
            all_databases = self._parent.all_databases(index.row())
            databases = index.data(Qt.DisplayRole).split(",")
            editor.set_data(all_databases, databases)
        else:
            editor = CustomLineEditor(parent)
            editor.set_data(index.data(Qt.EditRole))
        model = index.model()
        editor.data_committed.connect(lambda e=editor, i=index, m=model: self.close_editor(e, i, m))
        return editor

    def paint(self, painter, option, index):
        """Get a pixmap from the index data and paint it in the middle of the cell."""
        header = index.model().horizontal_header_labels()
        if header[index.column()] == 'display icon':
            pixmap = self.icon_mngr.create_object_pixmap(index.data(Qt.DisplayRole))
            icon = QIcon(pixmap)
            icon.paint(painter, option.rect, Qt.AlignVCenter | Qt.AlignHCenter)
        else:
            super().paint(painter, option, index)


class ManageObjectsDelegate(ManageItemsDelegate):
    """A delegate for the model and view in {Add/Edit}ObjectsDialog.

    Attributes:
        parent (DataStoreForm): tree or graph view form
    """

    def __init__(self, parent):
        super().__init__(parent)

    def createEditor(self, parent, option, index):
        """Return editor."""
        header = index.model().horizontal_header_labels()
        if header[index.column()] == 'object class name':
            editor = SearchBarEditor(parent)
            object_class_name_list = self._parent.object_class_name_list(index.row())
            editor.set_data(index.data(Qt.EditRole), object_class_name_list)
        elif header[index.column()] == 'databases':
            editor = CheckListEditor(parent)
            all_databases = self._parent.all_databases(index.row())
            databases = index.data(Qt.DisplayRole).split(",")
            editor.set_data(all_databases, databases)
        else:
            editor = CustomLineEditor(parent)
            editor.set_data(index.data(Qt.EditRole))
        model = index.model()
        editor.data_committed.connect(lambda e=editor, i=index, m=model: self.close_editor(e, i, m))
        return editor


class ManageRelationshipClassesDelegate(ManageItemsDelegate):
    """A delegate for the model and view in {Add/Edit}RelationshipClassesDialog.

    Attributes:
        parent (DataStoreForm): tree or graph view form
    """

    def __init__(self, parent):
        super().__init__(parent)

    def createEditor(self, parent, option, index):
        """Return editor."""
        header = index.model().horizontal_header_labels()
        if header[index.column()] == 'relationship class name':
            editor = CustomLineEditor(parent)
            data = index.data(Qt.EditRole)
            editor.set_data(index.data(Qt.EditRole))
        elif header[index.column()] == 'databases':
            editor = CheckListEditor(parent)
            all_databases = self._parent.all_databases(index.row())
            databases = index.data(Qt.DisplayRole).split(",")
            editor.set_data(all_databases, databases)
        else:
            editor = SearchBarEditor(parent)
            object_class_name_list = self._parent.object_class_name_list(index.row())
            editor.set_data(index.data(Qt.EditRole), object_class_name_list)
        model = index.model()
        editor.data_committed.connect(lambda e=editor, i=index, m=model: self.close_editor(e, i, m))
        return editor


class ManageRelationshipsDelegate(ManageItemsDelegate):
    """A delegate for the model and view in {Add/Edit}RelationshipsDialog.

    Attributes:
        parent (DataStoreForm): tree or graph view form
    """

    def __init__(self, parent):
        super().__init__(parent)

    def createEditor(self, parent, option, index):
        """Return editor."""
        header = index.model().horizontal_header_labels()
        if header[index.column()] == 'relationship name':
            editor = CustomLineEditor(parent)
            data = index.data(Qt.EditRole)
            editor.set_data(data)
        elif header[index.column()] == 'databases':
            editor = CheckListEditor(parent)
            all_databases = self._parent.all_databases(index.row())
            databases = index.data(Qt.DisplayRole).split(",")
            editor.set_data(all_databases, databases)
        else:
            editor = SearchBarEditor(parent)
            object_name_list = self._parent.object_name_list(index.row(), index.column())
            editor.set_data(index.data(Qt.EditRole), object_name_list)
        model = index.model()
        editor.data_committed.connect(lambda e=editor, i=index, m=model: self.close_editor(e, i, m))
        return editor


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
            editor.data_committed.connect(lambda e=editor, i=index, m=model: self.close_field_name_list_editor(e, i, m))
            return editor
        elif header[index.column()] == 'reference resource':
            return CustomComboEditor(parent)
        elif header[index.column()] == 'reference fields':
            editor = CheckListEditor(self._parent, parent)
            model = index.model()
            editor.data_committed.connect(lambda e=editor, i=index, m=model: self.close_field_name_list_editor(e, i, m))
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
