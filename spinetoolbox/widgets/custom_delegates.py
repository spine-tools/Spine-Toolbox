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
from PySide2.QtWidgets import QComboBox, QItemDelegate, QStyleOptionButton, QStyle, QApplication, QStyleOptionComboBox
from PySide2.QtGui import QIcon
from spinedb_api import from_database, DateTime, Duration, Map, ParameterValueFormatError, TimePattern, TimeSeries
from .custom_editors import (
    CustomComboEditor,
    CustomLineEditor,
    SearchBarEditor,
    CheckListEditor,
    NumberParameterInlineEditor,
)


class ComboBoxDelegate(QItemDelegate):
    def __init__(self, parent, choices):
        super().__init__(parent)
        self.editor = None
        self.items = choices

    def createEditor(self, parent, option, index):
        self.editor = QComboBox(parent)
        self.editor.addItems(self.items)
        # self.editor.currentIndexChanged.connect(self.currentItemChanged)
        return self.editor

    def paint(self, painter, option, index):
        value = index.data(Qt.DisplayRole)
        style = QApplication.style()
        opt = QStyleOptionComboBox()
        opt.text = str(value)
        opt.rect = option.rect
        style.drawComplexControl(QStyle.CC_ComboBox, opt, painter)
        QItemDelegate.paint(self, painter, option, index)

    def setEditorData(self, editor, index):
        value = index.data(Qt.DisplayRole)
        num = self.items.index(value)
        editor.setCurrentIndex(num)

    def setModelData(self, editor, model, index):
        value = editor.currentText()
        model.setData(index, value, Qt.EditRole)

    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)

    def currentItemChanged(self):
        self.commitData.emit(self.sender())


class LineEditDelegate(QItemDelegate):
    """A delegate that places a fully functioning QLineEdit.

    Attributes:
        parent (QMainWindow): either data store or spine datapackage widget
    """

    data_committed = Signal("QModelIndex", "QVariant", name="data_committed")

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

    data_committed = Signal("QModelIndex")

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


class PivotTableDelegate(CheckBoxDelegate):

    parameter_value_editor_requested = Signal("QModelIndex", str, object)
    data_committed = Signal("QModelIndex", "QVariant")

    def setModelData(self, editor, model, index):
        """Send signal."""
        self.data_committed.emit(index, editor.data())

    def _is_entity_index(self, index):
        return not self.parent().is_value_input_type() and index.model().sourceModel().index_in_data(index)

    def paint(self, painter, option, index):
        if self._is_entity_index(index):
            super().paint(painter, option, index)
        else:
            QItemDelegate.paint(self, painter, option, index)

    def editorEvent(self, event, model, option, index):
        if self._is_entity_index(index):
            return super().editorEvent(event, model, option, index)
        return QItemDelegate.editorEvent(self, event, model, option, index)

    def createEditor(self, parent, option, index):
        if self._is_entity_index(index):
            return super().createEditor(parent, option, index)
        if self.parent().pivot_table_model.index_in_data(index):
            try:
                value = from_database(index.data(role=Qt.EditRole))
            except ParameterValueFormatError:
                value = None
            if isinstance(value, (DateTime, Duration, Map, TimePattern, TimeSeries)) or value is None:
                value_name = index.model().sourceModel().value_name(index)  # FIXME: get the actual name
                self.parameter_value_editor_requested.emit(index, value_name, value)
                return None
        return CustomLineEditor(parent)


class GetObjectClassIdMixin:
    """Allows getting the object class id from the name."""

    def _get_object_class_id(self, index, db_map):
        h = index.model().header.index
        object_class_name = index.sibling(index.row(), h("object_class_name")).data()
        object_class = self.db_mngr.get_item_by_field(db_map, "object class", "name", object_class_name)
        return object_class.get("id")


class GetRelationshipClassIdMixin:
    """Allows getting the relationship class id from the name."""

    def _get_relationship_class_id(self, index, db_map):
        h = index.model().header.index
        relationship_class_name = index.sibling(index.row(), h("relationship_class_name")).data()
        relationship_class = self.db_mngr.get_item_by_field(
            db_map, "relationship class", "name", relationship_class_name
        )
        return relationship_class.get("id")


class ParameterDelegate(QItemDelegate):
    """Base class for all custom parameter delegates.

    Attributes:
        parent (DataStoreForm): tree or graph view form
        db_mngr (SpineDBManager)
    """

    data_committed = Signal("QModelIndex", "QVariant")

    def __init__(self, parent, db_mngr):
        super().__init__(parent)
        self.db_mngr = db_mngr

    def setModelData(self, editor, model, index):
        """Send signal."""
        self.data_committed.emit(index, editor.data())

    def updateEditorGeometry(self, editor, option, index):
        super().updateEditorGeometry(editor, option, index)
        if isinstance(editor, (SearchBarEditor, CheckListEditor)):
            size = option.rect.size()
            if index.data(Qt.DecorationRole):
                size.setWidth(size.width() - 22)  # FIXME
            editor.set_base_size(size)
            editor.update_geometry()

    def _close_editor(self, editor, index):
        """Closes editor. Needed by SearchBarEditor."""
        self.closeEditor.emit(editor)
        self.setModelData(editor, index.model(), index)

    def _get_db_map(self, index):
        """Returns the db_map for the database at given index or None if not set yet."""
        model = index.model()
        header = model.horizontal_header_labels()
        database = index.sibling(index.row(), header.index("database")).data()
        db_map = next(iter(x for x in self.db_mngr.db_maps if x.codename == database), None)
        if not db_map:
            self.parent().msg_error.emit("Please select database first.")
        return db_map


class DatabaseNameDelegate(ParameterDelegate):
    """A delegate for the database name."""

    def createEditor(self, parent, option, index):
        """Returns editor."""
        editor = SearchBarEditor(self.parent(), parent)
        editor.set_data(index.data(Qt.DisplayRole), [x.codename for x in self.db_mngr.db_maps])
        editor.data_committed.connect(lambda editor=editor, index=index: self._close_editor(editor, index))
        return editor


class ParameterValueOrDefaultValueDelegate(ParameterDelegate):
    """A delegate for the either the value or the default value."""

    parameter_value_editor_requested = Signal("QModelIndex", str, object)

    def setModelData(self, editor, model, index):
        """Emits the data_committed signal with new data."""
        if isinstance(editor, NumberParameterInlineEditor):
            self.data_committed.emit(index, editor.data())
            return
        value = self._str_to_int_or_float(editor.data())
        self.data_committed.emit(index, value)

    @staticmethod
    def _str_to_int_or_float(string):
        try:
            return int(string)
        except ValueError:
            try:
                return float(string)
            except ValueError:
                return string

    def _create_or_request_parameter_value_editor(self, parent, option, index, db_map):
        """Returns a CustomLineEditor or NumberParameterInlineEditor if the data from index is not of special type.
        Otherwise, emit the signal to request a standalone `ParameterValueEditor` from parent widget.
        """
        try:
            value = from_database(index.data(role=Qt.EditRole))
        except ParameterValueFormatError:
            value = None
        if isinstance(value, (DateTime, Duration, Map, TimePattern, TimeSeries)):
            value_name = index.model().value_name(index)
            self.parameter_value_editor_requested.emit(index, value_name, value)
            return None
        if isinstance(value, (float, int)):
            editor = NumberParameterInlineEditor(parent)
        else:
            editor = CustomLineEditor(parent)
        editor.set_data(index.data(Qt.EditRole))
        return editor


class ParameterDefaultValueDelegate(ParameterValueOrDefaultValueDelegate):
    """A delegate for the either the default value."""

    def createEditor(self, parent, option, index):
        """Returns or requests a parameter value editor."""
        db_map = self._get_db_map(index)
        if not db_map:
            return None
        return self._create_or_request_parameter_value_editor(parent, option, index, db_map)


class ParameterValueDelegate(ParameterValueOrDefaultValueDelegate):
    """A delegate for the parameter value."""

    def _get_entity_class_id(self, index, db_map):
        raise NotImplementedError()

    def _get_value_list(self, index, db_map):
        """Returns a value list item for the given index and db_map."""
        h = index.model().header.index
        parameter_name = index.sibling(index.row(), h("parameter_name")).data()
        parameters = self.db_mngr.get_items_by_field(db_map, "parameter definition", "parameter_name", parameter_name)
        entity_class_id = self._get_entity_class_id(index, db_map)
        parameter_ids = {p["id"] for p in parameters if p[self.entity_class_id_key] == entity_class_id}
        value_list_ids = {
            self.db_mngr.get_item(db_map, "parameter definition", id_).get("value_list_id") for id_ in parameter_ids
        }
        if len(value_list_ids) == 1:
            value_list_id = next(iter(value_list_ids))
            return self.db_mngr.get_item(db_map, "parameter value list", value_list_id).get("value_list")

    def createEditor(self, parent, option, index):
        """If the parameter has associated a value list, returns a SearchBarEditor .
        Otherwise returns or requests a dedicated parameter value editor.
        """
        db_map = self._get_db_map(index)
        if not db_map:
            return None
        value_list = self._get_value_list(index, db_map)
        if value_list:
            editor = SearchBarEditor(self.parent(), parent)
            value_list = [from_database(x) for x in value_list.split(",")]
            editor.set_data(index.data(Qt.DisplayRole), value_list)
            editor.data_committed.connect(lambda editor=editor, index=index: self._close_editor(editor, index))
            return editor
        return self._create_or_request_parameter_value_editor(parent, option, index, db_map)


class ObjectParameterValueDelegate(GetObjectClassIdMixin, ParameterValueDelegate):
    """A delegate for the object parameter value."""

    @property
    def entity_class_id_key(self):
        return "object_class_id"

    def _get_entity_class_id(self, index, db_map):
        return self._get_object_class_id(index, db_map)


class RelationshipParameterValueDelegate(GetRelationshipClassIdMixin, ParameterValueDelegate):
    """A delegate for the relationship parameter value."""

    @property
    def entity_class_id_key(self):
        return "relationship_class_id"

    def _get_entity_class_id(self, index, db_map):
        return self._get_relationship_class_id(index, db_map)


class TagListDelegate(ParameterDelegate):
    """A delegate for the parameter tag list."""

    def createEditor(self, parent, option, index):
        """Returns editor."""
        db_map = self._get_db_map(index)
        if not db_map:
            return None
        editor = CheckListEditor(self.parent(), parent)
        all_parameter_tag_list = [x["tag"] for x in self.db_mngr.get_parameter_tags(db_map)]
        try:
            parameter_tag_list = index.data(Qt.EditRole).split(",")
        except AttributeError:
            # Gibberish in the cell
            parameter_tag_list = []
        editor.set_data(all_parameter_tag_list, parameter_tag_list)
        return editor


class ValueListDelegate(ParameterDelegate):
    """A delegate for the parameter value-list."""

    def createEditor(self, parent, option, index):
        """Returns editor."""
        db_map = self._get_db_map(index)
        if not db_map:
            return None
        editor = SearchBarEditor(self.parent(), parent)
        name_list = [x["name"] for x in self.db_mngr.get_parameter_value_lists(db_map)]
        editor.set_data(index.data(Qt.EditRole), name_list)
        editor.data_committed.connect(lambda editor=editor, index=index: self._close_editor(editor, index))
        return editor


class ObjectClassNameDelegate(ParameterDelegate):
    """A delegate for the object class name."""

    def createEditor(self, parent, option, index):
        """Returns editor."""
        db_map = self._get_db_map(index)
        if not db_map:
            return None
        editor = SearchBarEditor(self.parent(), parent)
        object_classes = self.db_mngr.get_object_classes(db_map)
        editor.set_data(index.data(Qt.EditRole), [x["name"] for x in object_classes])
        editor.data_committed.connect(lambda editor=editor, index=index: self._close_editor(editor, index))
        return editor


class RelationshipClassNameDelegate(ParameterDelegate):
    """A delegate for the relationship class name."""

    def createEditor(self, parent, option, index):
        """Returns editor."""
        db_map = self._get_db_map(index)
        if not db_map:
            return None
        editor = SearchBarEditor(self.parent(), parent)
        relationship_classes = self.db_mngr.get_relationship_classes(db_map)
        editor.set_data(index.data(Qt.EditRole), [x["name"] for x in relationship_classes])
        editor.data_committed.connect(lambda editor=editor, index=index: self._close_editor(editor, index))
        return editor


class ObjectParameterNameDelegate(GetObjectClassIdMixin, ParameterDelegate):
    """A delegate for the object parameter name."""

    def createEditor(self, parent, option, index):
        """Returns editor."""
        db_map = self._get_db_map(index)
        if not db_map:
            return None
        editor = SearchBarEditor(self.parent(), parent)
        object_class_id = self._get_object_class_id(index, db_map)
        parameter_definitions = self.db_mngr.get_object_parameter_definitions(db_map, object_class_id=object_class_id)
        name_list = [x["parameter_name"] for x in parameter_definitions]
        editor.set_data(index.data(Qt.EditRole), name_list)
        editor.data_committed.connect(lambda editor=editor, index=index: self._close_editor(editor, index))
        return editor


class RelationshipParameterNameDelegate(GetRelationshipClassIdMixin, ParameterDelegate):
    """A delegate for the relationship parameter name."""

    def createEditor(self, parent, option, index):
        """Returns editor."""
        db_map = self._get_db_map(index)
        if not db_map:
            return None
        editor = SearchBarEditor(self.parent(), parent)
        relationship_class_id = self._get_relationship_class_id(index, db_map)
        parameter_definitions = self.db_mngr.get_relationship_parameter_definitions(
            db_map, relationship_class_id=relationship_class_id
        )
        name_list = [x["parameter_name"] for x in parameter_definitions]
        editor.set_data(index.data(Qt.EditRole), name_list)
        editor.data_committed.connect(lambda editor=editor, index=index: self._close_editor(editor, index))
        return editor


class ObjectNameDelegate(GetObjectClassIdMixin, ParameterDelegate):
    """A delegate for the object name."""

    def createEditor(self, parent, option, index):
        """Returns editor."""
        db_map = self._get_db_map(index)
        if not db_map:
            return None
        editor = SearchBarEditor(self.parent(), parent)
        object_class_id = self._get_object_class_id(index, db_map)
        name_list = [x["name"] for x in self.db_mngr.get_objects(db_map, class_id=object_class_id)]
        editor.set_data(index.data(Qt.EditRole), name_list)
        editor.data_committed.connect(lambda editor=editor, index=index: self._close_editor(editor, index))
        return editor


class ObjectNameListDelegate(GetRelationshipClassIdMixin, ParameterDelegate):
    """A delegate for the object name list."""

    object_name_list_editor_requested = Signal("QModelIndex", int, "QVariant")

    def createEditor(self, parent, option, index):
        """Returns editor."""
        db_map = self._get_db_map(index)
        if not db_map:
            return None
        relationship_class_id = self._get_relationship_class_id(index, db_map)
        if not relationship_class_id:
            editor = CustomLineEditor(parent)
            editor.set_data(index.data(Qt.EditRole))
            return editor
        self.object_name_list_editor_requested.emit(index, relationship_class_id, db_map)


class ManageItemsDelegate(QItemDelegate):
    """A custom delegate for the model in {Add/Edit}ItemDialogs.

    Attributes:
        parent (ManageItemsDialog): parent dialog
    """

    data_committed = Signal("QModelIndex", "QVariant", name="data_committed")

    def setModelData(self, editor, model, index):
        """Send signal."""
        self.data_committed.emit(index, editor.data())

    def close_editor(self, editor, index, model):
        self.closeEditor.emit(editor)
        self.setModelData(editor, model, index)

    def updateEditorGeometry(self, editor, option, index):
        super().updateEditorGeometry(editor, option, index)
        if isinstance(editor, (SearchBarEditor, CheckListEditor)):
            size = option.rect.size()
            if index.data(Qt.DecorationRole):
                size.setWidth(size.width() - 22)  # FIXME
            editor.set_base_size(size)
            editor.update_geometry()

    def connect_editor_signals(self, editor, index):
        """Connect editor signals if necessary.
        """
        if isinstance(editor, SearchBarEditor):
            model = index.model()
            editor.data_committed.connect(lambda e=editor, i=index, m=model: self.close_editor(e, i, m))

    def _create_database_editor(self, parent, option, index):
        editor = CheckListEditor(parent)
        all_databases = self.parent().all_databases(index.row())
        databases = index.data(Qt.DisplayRole).split(",")
        editor.set_data(all_databases, databases)
        return editor


class ManageObjectClassesDelegate(ManageItemsDelegate):
    """A delegate for the model and view in {Add/Edit}ObjectClassesDialog.

    Attributes:
        parent (ManageItemsDialog): parent dialog
    """

    icon_color_editor_requested = Signal("QModelIndex", name="icon_color_editor_requested")

    def createEditor(self, parent, option, index):
        """Return editor."""
        header = index.model().horizontal_header_labels()
        if header[index.column()] == 'display icon':
            self.icon_color_editor_requested.emit(index)
            editor = None
        elif header[index.column()] == 'databases':
            editor = self._create_database_editor(parent, option, index)
        else:
            editor = CustomLineEditor(parent)
            editor.set_data(index.data(Qt.EditRole))
        self.connect_editor_signals(editor, index)
        return editor

    def paint(self, painter, option, index):
        """Get a pixmap from the index data and paint it in the middle of the cell."""
        header = index.model().horizontal_header_labels()
        if header[index.column()] == 'display icon':
            pixmap = self.parent().create_object_pixmap(index.data(Qt.DisplayRole))
            icon = QIcon(pixmap)
            icon.paint(painter, option.rect, Qt.AlignVCenter | Qt.AlignHCenter)
        else:
            super().paint(painter, option, index)


class ManageObjectsDelegate(ManageItemsDelegate):
    """A delegate for the model and view in {Add/Edit}ObjectsDialog.

    Attributes:
        parent (ManageItemsDialog): parent dialog
    """

    def createEditor(self, parent, option, index):
        """Return editor."""
        header = index.model().horizontal_header_labels()
        if header[index.column()] == 'object class name':
            editor = SearchBarEditor(parent)
            object_class_name_list = self.parent().object_class_name_list(index.row())
            editor.set_data(index.data(Qt.EditRole), object_class_name_list)
        elif header[index.column()] == 'databases':
            editor = self._create_database_editor(parent, option, index)
        else:
            editor = CustomLineEditor(parent)
            editor.set_data(index.data(Qt.EditRole))
        self.connect_editor_signals(editor, index)
        return editor


class ManageRelationshipClassesDelegate(ManageItemsDelegate):
    """A delegate for the model and view in {Add/Edit}RelationshipClassesDialog.

    Attributes:
        parent (ManageItemsDialog): parent dialog
    """

    def createEditor(self, parent, option, index):
        """Return editor."""
        header = index.model().horizontal_header_labels()
        if header[index.column()] == 'relationship class name':
            editor = CustomLineEditor(parent)
            editor.set_data(index.data(Qt.EditRole))
        elif header[index.column()] == 'databases':
            editor = self._create_database_editor(parent, option, index)
        else:
            editor = SearchBarEditor(parent)
            object_class_name_list = self.parent().object_class_name_list(index.row())
            editor.set_data(index.data(Qt.EditRole), object_class_name_list)
        self.connect_editor_signals(editor, index)
        return editor


class ManageRelationshipsDelegate(ManageItemsDelegate):
    """A delegate for the model and view in {Add/Edit}RelationshipsDialog.

    Attributes:
        parent (ManageItemsDialog): parent dialog
    """

    def createEditor(self, parent, option, index):
        """Return editor."""
        header = index.model().horizontal_header_labels()
        if header[index.column()] == 'relationship name':
            editor = CustomLineEditor(parent)
            data = index.data(Qt.EditRole)
            editor.set_data(data)
        elif header[index.column()] == 'databases':
            editor = self._create_database_editor(parent, option, index)
        else:
            editor = SearchBarEditor(parent)
            object_name_list = self.parent().object_name_list(index.row(), index.column())
            editor.set_data(index.data(Qt.EditRole), object_name_list)
        self.connect_editor_signals(editor, index)
        return editor


class RemoveEntitiesDelegate(ManageItemsDelegate):
    """A delegate for the model and view in RemoveEntitiesDialog.

    Attributes:
        parent (ManageItemsDialog): parent dialog
    """

    def createEditor(self, parent, option, index):
        """Return editor."""
        header = index.model().horizontal_header_labels()
        if header[index.column()] == 'databases':
            editor = self._create_database_editor(parent, option, index)
            self.connect_editor_signals(editor, index)
            return editor


class ManageParameterTagsDelegate(ManageItemsDelegate):
    """A delegate for the model and view in ManageParameterTagsDialog.

    Attributes:
        parent (ManageItemsDialog): parent dialog
    """

    def createEditor(self, parent, option, index):
        """Return editor."""
        header = index.model().horizontal_header_labels()
        if header[index.column()] == 'remove':
            return None
        if header[index.column()] == 'databases':
            editor = self._create_database_editor(parent, option, index)
        else:
            editor = CustomLineEditor(parent)
            editor.set_data(index.data(Qt.EditRole))
        self.connect_editor_signals(editor, index)
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
        self.datapackage = None
        self.selected_resource_name = None

    def createEditor(self, parent, option, index):
        """Return editor."""
        header = index.model().horizontal_header_labels()
        if header[index.column()] == 'fields':
            editor = CheckListEditor(self.parent(), parent)
            model = index.model()
            editor.data_committed.connect(lambda e=editor, i=index, m=model: self.close_field_name_list_editor(e, i, m))
            return editor
        if header[index.column()] == 'reference resource':
            return CustomComboEditor(parent)
        if header[index.column()] == 'reference fields':
            editor = CheckListEditor(self.parent(), parent)
            model = index.model()
            editor.data_committed.connect(lambda e=editor, i=index, m=model: self.close_field_name_list_editor(e, i, m))
            return editor
        return None

    def setEditorData(self, editor, index):
        """Set editor data."""
        self.datapackage = self.parent().datapackage
        self.selected_resource_name = self.parent().selected_resource_name
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
