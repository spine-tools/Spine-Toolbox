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

from numbers import Number
from PySide2.QtCore import QModelIndex, QPoint, Qt, Signal
from PySide2.QtWidgets import QStyledItemDelegate
from PySide2.QtGui import QIcon, QFontMetrics
from spinedb_api import to_database
from ...widgets.custom_editors import CustomLineEditor, SearchBarEditor, CheckListEditor, ParameterValueLineEditor
from ...mvcmodels.shared import PARSED_ROLE
from ...widgets.custom_delegates import CheckBoxDelegate, RankDelegate


class RelationshipPivotTableDelegate(CheckBoxDelegate):

    data_committed = Signal(QModelIndex, object)

    def __init__(self, parent):
        """
        Args:
            parent (SpineDBEditor)
        """
        super().__init__(parent)
        self.data_committed.connect(parent._set_model_data)

    @staticmethod
    def _is_relationship_index(index):
        """
        Checks whether or not the given index corresponds to a relationship,
        in which case we need to use the check box delegate.

        Returns:
            bool
        """
        return index.model().sourceModel().index_in_data(index)

    def setModelData(self, editor, model, index):
        """Send signal."""
        if self._is_relationship_index(index):
            super().setModelData(editor, model, index)
            return
        self.data_committed.emit(index, editor.data())

    def setEditorData(self, editor, index):
        """Do nothing. We're setting editor data right away in createEditor."""

    def paint(self, painter, option, index):
        if self._is_relationship_index(index):
            super().paint(painter, option, index)
        else:
            QStyledItemDelegate.paint(self, painter, option, index)

    def editorEvent(self, event, model, option, index):
        if self._is_relationship_index(index):
            return super().editorEvent(event, model, option, index)
        return QStyledItemDelegate.editorEvent(self, event, model, option, index)

    def createEditor(self, parent, option, index):
        if self._is_relationship_index(index):
            return super().createEditor(parent, option, index)
        editor = CustomLineEditor(parent)
        editor.set_data(index.data(Qt.EditRole))
        return editor


class ScenarioAlternativeTableDelegate(RankDelegate):

    data_committed = Signal(QModelIndex, object)

    def __init__(self, parent):
        """
        Args:
            parent (SpineDBEditor)
        """
        super().__init__(parent)
        self.data_committed.connect(parent._set_model_data)

    @staticmethod
    def _is_scenario_alternative_index(index):
        """
        Checks whether or not the given index corresponds to a scenario alternative,
        in which case we need to use the rank delegate.

        Returns:
            bool
        """
        return index.model().sourceModel().index_in_data(index)

    def setModelData(self, editor, model, index):
        """Send signal."""
        if self._is_scenario_alternative_index(index):
            super().setModelData(editor, model, index)
            return
        self.data_committed.emit(index, editor.data())

    def setEditorData(self, editor, index):
        """Do nothing. We're setting editor data right away in createEditor."""

    def paint(self, painter, option, index):
        if self._is_scenario_alternative_index(index):
            super().paint(painter, option, index)
        else:
            QStyledItemDelegate.paint(self, painter, option, index)

    def editorEvent(self, event, model, option, index):
        if self._is_scenario_alternative_index(index):
            return super().editorEvent(event, model, option, index)
        return QStyledItemDelegate.editorEvent(self, event, model, option, index)

    def createEditor(self, parent, option, index):
        if self._is_scenario_alternative_index(index):
            return super().createEditor(parent, option, index)
        editor = CustomLineEditor(parent)
        editor.set_data(index.data(Qt.EditRole))
        return editor


class ParameterPivotTableDelegate(QStyledItemDelegate):

    parameter_value_editor_requested = Signal(QModelIndex)
    data_committed = Signal(QModelIndex, object)

    def __init__(self, parent):
        """
        Args:
            parent (SpineDBEditor)
        """
        super().__init__(parent)
        self.data_committed.connect(parent._set_model_data)
        self.parameter_value_editor_requested.connect(parent.show_parameter_value_editor)

    def setModelData(self, editor, model, index):
        """Send signal."""
        data = editor.data()
        if isinstance(editor, ParameterValueLineEditor):
            data = to_database(data)
        self.data_committed.emit(index, data)

    def setEditorData(self, editor, index):
        """Do nothing. We're setting editor data right away in createEditor."""

    def createEditor(self, parent, option, index):
        if self.parent().pivot_table_model.index_in_data(index):
            value = index.model().mapToSource(index).data(PARSED_ROLE)
            if value is None or isinstance(value, (Number, str)) and not isinstance(value, bool):
                editor = ParameterValueLineEditor(parent)
                editor.set_data(value)
                return editor
            self.parameter_value_editor_requested.emit(index.model().mapToSource(index))
            return None
        editor = CustomLineEditor(parent)
        editor.set_data(index.data(Qt.EditRole))
        return editor


class ParameterValueElementDelegate(QStyledItemDelegate):
    """Delegate for Array and Map editors' table cells."""

    value_editor_requested = Signal(QModelIndex)
    """Emitted when editing the value requires the full blown editor dialog."""

    def setModelData(self, editor, model, index):
        """
        Sets data in the model.

        editor (CustomLineEditor): editor widget
        model (QAbstractItemModel): model
        index (QModelIndex): target index
        """
        data = editor.data()
        model.setData(index, data)

    def createEditor(self, parent, option, index):
        """
        Creates an editor widget or emits ``value_editor_requested`` for complex values.

        Args:
            parent (QWidget): parent widget
            option (QStyleOptionViewItem): unused
            index (QModelIndex): element's model index

        Returns:
            ParameterValueLineEditor: editor widget
        """
        value = index.data(Qt.EditRole)
        if value is None or isinstance(value, (Number, str)) and not isinstance(value, bool):
            editor = ParameterValueLineEditor(parent)
            editor.set_data(value)
            return editor
        self.value_editor_requested.emit(index)
        return None


class ParameterDelegate(QStyledItemDelegate):
    """Base class for all custom parameter delegates.

    Attributes:
        parent (SpineDBEditor): tree or graph view form
        db_mngr (SpineDBManager)
    """

    data_committed = Signal("QModelIndex", "QVariant")

    def __init__(self, parent, db_mngr):
        super().__init__(parent)
        self.db_mngr = db_mngr

    def setModelData(self, editor, model, index):
        """Send signal."""
        self.data_committed.emit(index, editor.data())

    def setEditorData(self, editor, index):
        """Do nothing. We're setting editor data right away in createEditor."""

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

    parameter_value_editor_requested = Signal("QModelIndex")

    def __init__(self, parent, db_mngr):
        super().__init__(parent, db_mngr)
        self._db_value_list_lookup = {}

    def setModelData(self, editor, model, index):
        """Send signal."""
        display_value = editor.data()
        db_value = self._db_value_list_lookup.get(display_value, to_database(display_value))
        self.data_committed.emit(index, db_value)

    def _create_or_request_parameter_value_editor(self, parent, option, index, db_map):
        """Emits the signal to request a standalone `ParameterValueEditor` from parent widget."""
        value = index.data(PARSED_ROLE)
        if value is None or isinstance(value, (Number, str)) and not isinstance(value, bool):
            editor = ParameterValueLineEditor(parent)
            editor.set_data(value)
            return editor
        self.parameter_value_editor_requested.emit(index)

    def createEditor(self, parent, option, index):
        """If the parameter has associated a value list, returns a SearchBarEditor.
        Otherwise returns or requests a dedicated parameter_value editor.
        """
        db_map = self._get_db_map(index)
        if not db_map:
            return None
        value_list_id = self._get_value_list_id(index, db_map)
        if value_list_id:
            display_value_list = self.db_mngr.get_parameter_value_list(db_map, value_list_id, Qt.DisplayRole)
            db_value_list = self.db_mngr.get_parameter_value_list(db_map, value_list_id, Qt.EditRole)
            self._db_value_list_lookup = dict(zip(display_value_list, db_value_list))
            editor = SearchBarEditor(self.parent(), parent)
            editor.set_data(index.data(), self._db_value_list_lookup)
            editor.data_committed.connect(lambda editor=editor, index=index: self._close_editor(editor, index))
            return editor
        return self._create_or_request_parameter_value_editor(parent, option, index, db_map)


class ParameterDefaultValueDelegate(ParameterValueOrDefaultValueDelegate):
    """A delegate for the either the default value."""

    def _get_value_list_id(self, index, db_map):
        """Returns a value list item for the given index and db_map."""
        h = index.model().header.index
        value_list_name = index.sibling(index.row(), h("value_list_name")).data()
        value_lists = self.db_mngr.get_items_by_field(db_map, "parameter_value_list", "name", value_list_name)
        if len(value_lists) == 1:
            return value_lists[0]["id"]


class ParameterValueDelegate(ParameterValueOrDefaultValueDelegate):
    """A delegate for the parameter_value."""

    def _get_value_list_id(self, index, db_map):
        """Returns a value list item for the given index and db_map."""
        h = index.model().header.index
        parameter_name = index.sibling(index.row(), h("parameter_name")).data()
        parameters = self.db_mngr.get_items_by_field(db_map, "parameter_definition", "parameter_name", parameter_name)
        entity_class_id = index.model().get_entity_class_id(index, db_map)
        parameter_ids = {p["id"] for p in parameters if p["entity_class_id"] == entity_class_id}
        value_list_ids = {
            self.db_mngr.get_item(db_map, "parameter_definition", id_).get("value_list_id") for id_ in parameter_ids
        }
        if len(value_list_ids) == 1:
            return next(iter(value_list_ids))


class TagListDelegate(ParameterDelegate):
    """A delegate for the parameter_tag list."""

    def createEditor(self, parent, option, index):
        """Returns editor."""
        db_map = self._get_db_map(index)
        if not db_map:
            return None
        editor = CheckListEditor(self.parent(), parent)
        all_parameter_tag_list = [x["tag"] for x in self.db_mngr.get_items(db_map, "parameter_tag")]
        try:
            parameter_tag_list = index.data(Qt.EditRole).split(",")
        except AttributeError:
            # Gibberish in the cell
            parameter_tag_list = []
        editor.set_data(all_parameter_tag_list, parameter_tag_list)
        return editor


class ValueListDelegate(ParameterDelegate):
    """A delegate for the parameter_value-list."""

    def createEditor(self, parent, option, index):
        """Returns editor."""
        db_map = self._get_db_map(index)
        if not db_map:
            return None
        editor = SearchBarEditor(self.parent(), parent)
        name_list = [x["name"] for x in self.db_mngr.get_items(db_map, "parameter_value_list")]
        editor.set_data(index.data(Qt.EditRole), name_list)
        editor.data_committed.connect(lambda editor=editor, index=index: self._close_editor(editor, index))
        return editor


class ObjectClassNameDelegate(ParameterDelegate):
    """A delegate for the object_class name."""

    def createEditor(self, parent, option, index):
        """Returns editor."""
        db_map = self._get_db_map(index)
        if not db_map:
            return None
        editor = SearchBarEditor(self.parent(), parent)
        object_classes = self.db_mngr.get_items(db_map, "object_class")
        editor.set_data(index.data(Qt.EditRole), [x["name"] for x in object_classes])
        editor.data_committed.connect(lambda editor=editor, index=index: self._close_editor(editor, index))
        return editor


class RelationshipClassNameDelegate(ParameterDelegate):
    """A delegate for the relationship_class name."""

    def createEditor(self, parent, option, index):
        """Returns editor."""
        db_map = self._get_db_map(index)
        if not db_map:
            return None
        editor = SearchBarEditor(self.parent(), parent)
        relationship_classes = self.db_mngr.get_items(db_map, "relationship_class")
        editor.set_data(index.data(Qt.EditRole), [x["name"] for x in relationship_classes])
        editor.data_committed.connect(lambda editor=editor, index=index: self._close_editor(editor, index))
        return editor


class ParameterNameDelegate(ParameterDelegate):
    """A delegate for the object parameter name."""

    def createEditor(self, parent, option, index):
        """Returns editor."""
        db_map = self._get_db_map(index)
        if not db_map:
            return None
        editor = SearchBarEditor(self.parent(), parent)
        entity_class_id = index.model().get_entity_class_id(index, db_map)
        parameter_definitions = self.db_mngr.get_items_by_field(
            db_map, "parameter_definition", "entity_class_id", entity_class_id
        )
        name_list = [x["parameter_name"] for x in parameter_definitions]
        editor.set_data(index.data(Qt.EditRole), name_list)
        editor.data_committed.connect(lambda editor=editor, index=index: self._close_editor(editor, index))
        return editor


class ObjectNameDelegate(ParameterDelegate):
    """A delegate for the object name."""

    def createEditor(self, parent, option, index):
        """Returns editor."""
        db_map = self._get_db_map(index)
        if not db_map:
            return None
        editor = SearchBarEditor(self.parent(), parent)
        object_class_id = index.model().get_entity_class_id(index, db_map)
        name_list = [x["name"] for x in self.db_mngr.get_items_by_field(db_map, "object", "class_id", object_class_id)]
        editor.set_data(index.data(Qt.EditRole), name_list)
        editor.data_committed.connect(lambda editor=editor, index=index: self._close_editor(editor, index))
        return editor


class AlternativeNameDelegate(ParameterDelegate):
    """A delegate for the object name."""

    def createEditor(self, parent, option, index):
        """Returns editor."""
        db_map = self._get_db_map(index)
        if not db_map:
            return None
        editor = SearchBarEditor(self.parent(), parent)
        name_list = [x["name"] for x in self.db_mngr.get_alternatives(db_map)]
        editor.set_data(index.data(Qt.EditRole), name_list)
        editor.data_committed.connect(lambda editor=editor, index=index: self._close_editor(editor, index))
        return editor


class ObjectNameListDelegate(ParameterDelegate):
    """A delegate for the object name list."""

    object_name_list_editor_requested = Signal("QModelIndex", int, "QVariant")

    def createEditor(self, parent, option, index):
        """Returns editor."""
        db_map = self._get_db_map(index)
        if not db_map:
            return None
        relationship_class_id = index.model().get_entity_class_id(index, db_map)
        if not relationship_class_id:
            editor = CustomLineEditor(parent)
            editor.set_data(index.data(Qt.EditRole))
            return editor
        self.object_name_list_editor_requested.emit(index, relationship_class_id, db_map)


class ToolFeatureDelegate(QStyledItemDelegate):
    """A delegate for the tool feature tree."""

    data_committed = Signal("QModelIndex", "QVariant")

    @staticmethod
    def _get_names(item, model):
        if item.item_type == "feature":
            names = model.get_all_feature_names(item.db_map)
            if not names:
                model._parent.error_box.emit(
                    "Error", "There aren't any listed parameter definitions to create features from. "
                )
                return None
            return names
        if item.item_type == "tool_feature required":
            return ["yes", "no"]
        if item.item_type == "tool_feature_method":
            tool_feat_item = item.tool_feature_item
            return model.get_all_feature_methods(
                tool_feat_item.db_map, tool_feat_item.item_data["parameter_value_list_id"]
            )

    @staticmethod
    def _get_index_data(item, index):
        index_data = index.data(Qt.EditRole)
        if item.item_type == "tool_feature required":
            return index_data.split(": ")[1]
        return index_data

    def setModelData(self, editor, model, index):
        """Send signal."""
        item = index.model().item_from_index(index)
        index_data = self._get_index_data(item, index)
        if editor.data() == index_data:
            return
        self.data_committed.emit(index, editor.data())

    def setEditorData(self, editor, index):
        """Do nothing. We're setting editor data right away in createEditor."""

    def createEditor(self, parent, option, index):
        """Returns editor."""
        model = index.model()
        item = model.item_from_index(index)
        if item.item_type in ("feature", "tool_feature required", "tool_feature_method"):
            editor = SearchBarEditor(self.parent(), parent)
            index_data = self._get_index_data(item, index)
            names = self._get_names(item, model)
            if names is None:
                return None
            editor.set_data(index_data, names)
            editor.data_committed.connect(lambda editor=editor, index=index: self._close_editor(editor, index))
            return editor
        editor = CustomLineEditor(parent)
        editor.set_data(index.data(Qt.EditRole))
        return editor

    def updateEditorGeometry(self, editor, option, index):
        super().updateEditorGeometry(editor, option, index)
        item = index.model().item_from_index(index)
        if item.item_type in ("feature", "tool_feature required", "tool_feature_method"):
            size = option.rect.size()
            if item.item_type == "tool_feature required":
                dx = QFontMetrics(index.data(Qt.FontRole)).horizontalAdvance("required:")
                size.setWidth(size.width() - dx)
                editor.set_base_offset(QPoint(dx, 0))
            editor.set_base_size(size)
            editor.update_geometry()

    def _close_editor(self, editor, index):
        """Closes editor. Needed by SearchBarEditor."""
        self.closeEditor.emit(editor)
        self.setModelData(editor, index.model(), index)


class AlternativeScenarioDelegate(QStyledItemDelegate):
    """A delegate for the alternative scenario tree."""

    data_committed = Signal("QModelIndex", "QVariant")

    def setModelData(self, editor, model, index):
        """Send signal."""
        if editor.data() == index.data():
            return
        self.data_committed.emit(index, editor.data())

    def setEditorData(self, editor, index):
        """Do nothing. We're setting editor data right away in createEditor."""

    def createEditor(self, parent, option, index):
        """Returns editor."""
        model = index.model()
        item = model.item_from_index(index)
        if item.item_type != "scenario active":
            editor = CustomLineEditor(parent)
            editor.set_data(index.data(Qt.EditRole))
            return editor
        editor = SearchBarEditor(self.parent(), parent)
        active = index.data(Qt.EditRole).split(": ")[1]
        editor.set_data(active, ["yes", "no"])
        editor.data_committed.connect(lambda editor=editor, index=index: self._close_editor(editor, index))
        return editor

    def updateEditorGeometry(self, editor, option, index):
        super().updateEditorGeometry(editor, option, index)
        item = index.model().item_from_index(index)
        if item.item_type == "scenario active":
            size = option.rect.size()
            fm = QFontMetrics(index.data(Qt.FontRole))
            dx = fm.horizontalAdvance("active:")
            size.setWidth(size.width() - dx)
            editor.set_base_size(size)
            editor.set_base_offset(QPoint(dx, 0))
            editor.update_geometry()

    def _close_editor(self, editor, index):
        """Closes editor. Needed by SearchBarEditor."""
        self.closeEditor.emit(editor)
        self.setModelData(editor, index.model(), index)


class ParameterValueListDelegate(QStyledItemDelegate):
    """A delegate for the parameter value list tree."""

    data_committed = Signal("QModelIndex", "QVariant")
    parameter_value_editor_requested = Signal("QModelIndex")

    def setModelData(self, editor, model, index):
        """Send signal."""
        if editor.data() == index.data(Qt.EditRole):
            return
        self.data_committed.emit(index, editor.data())

    def setEditorData(self, editor, index):
        """Do nothing. We're setting editor data right away in createEditor."""

    def createEditor(self, parent, option, index):
        """Returns editor."""
        model = index.model()
        item = model.item_from_index(index)
        if item.item_type != "value":
            editor = CustomLineEditor(parent)
            editor.set_data(index.data(Qt.EditRole))
            return editor
        value = index.data(PARSED_ROLE)
        if value is None or isinstance(value, (Number, str)) and not isinstance(value, bool):
            editor = ParameterValueLineEditor(parent)
            editor.set_data(value)
            return editor
        self.parameter_value_editor_requested.emit(index)

    def _close_editor(self, editor, index):
        """Closes editor. Needed by SearchBarEditor."""
        self.closeEditor.emit(editor)
        self.setModelData(editor, index.model(), index)


class ManageItemsDelegate(QStyledItemDelegate):
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

    def createEditor(self, parent, option, index):
        """Returns an editor."""
        header = index.model().horizontal_header_labels()
        if header[index.column()] == 'databases':
            editor = self._create_database_editor(parent, option, index)
        else:
            editor = CustomLineEditor(parent)
            editor.set_data(index.data(Qt.EditRole))
        self.connect_editor_signals(editor, index)
        return editor


class ManageObjectClassesDelegate(ManageItemsDelegate):
    """A delegate for the model and view in {Add/Edit}ObjectClassesDialog.

    Attributes:
        parent (ManageItemsDialog): parent dialog
    """

    icon_color_editor_requested = Signal("QModelIndex")

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
            pixmap = self.parent().create_object_pixmap(index)
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
        if header[index.column()] == 'object_class name':
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
        if header[index.column()] in ('relationship_class name', 'description'):
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
