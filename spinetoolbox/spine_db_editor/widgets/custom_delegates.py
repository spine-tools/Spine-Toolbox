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
from numbers import Number
from PySide6.QtCore import QEvent, QModelIndex, QRect, QSize, Qt, Signal
from PySide6.QtGui import QColor, QFont, QFontMetrics, QIcon
from PySide6.QtWidgets import QStyledItemDelegate
from spinedb_api import to_database
from spinedb_api.parameter_value import join_value_and_type
from spinetoolbox.spine_db_editor.widgets.custom_editors import (
    BooleanSearchBarEditor,
    CheckListEditor,
    CustomComboBoxEditor,
    CustomLineEditor,
    ParameterTypeEditor,
    ParameterValueLineEditor,
    PivotHeaderTableLineEditor,
    SearchBarEditor,
    SearchBarEditorWithCreation,
)
from ...font import TOOLBOX_FONT
from ...helpers import object_icon
from ...mvcmodels.shared import DB_MAP_ROLE, INVALID_TYPE, PARAMETER_TYPE_VALIDATION_ROLE, PARSED_ROLE
from ...widgets.custom_delegates import CheckBoxDelegate, RankDelegate
from ..mvcmodels.metadata_table_model_base import Column as MetadataColumn


class PivotTableDelegateMixin:
    """A mixin that fixes Pivot table's header table editor position."""

    def updateEditorGeometry(self, editor, option, index):
        """Fixes position of header table editors."""
        super().updateEditorGeometry(editor, option, index)
        if isinstance(editor, PivotHeaderTableLineEditor):
            editor.fix_geometry()


class RelationshipPivotTableDelegate(PivotTableDelegateMixin, CheckBoxDelegate):
    data_committed = Signal(QModelIndex, object)

    def __init__(self, parent):
        """
        Args:
            parent (SpineDBEditor): parent widget, i.e. the database editor
        """
        super().__init__(parent)
        self.data_committed.connect(parent._set_model_data)

    @staticmethod
    def _is_relationship_index(index):
        """
        Checks whether the given index corresponds to a relationship,
        in which case we need to use the check box delegate.

        Args:
            index (QModelIndex): index to check

        Returns:
            bool: True if index corresponds to relationship, False otherwise
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
        editor = PivotHeaderTableLineEditor(parent)
        editor.set_data(index.data(Qt.ItemDataRole.EditRole))
        return editor


class ScenarioAlternativeTableDelegate(PivotTableDelegateMixin, RankDelegate):
    data_committed = Signal(QModelIndex, object)

    def __init__(self, parent):
        """
        Args:
            parent (SpineDBEditor): database editor
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
        editor = PivotHeaderTableLineEditor(parent)
        editor.set_data(index.data(Qt.ItemDataRole.EditRole))
        return editor


class ParameterPivotTableDelegate(PivotTableDelegateMixin, QStyledItemDelegate):
    parameter_value_editor_requested = Signal(QModelIndex)
    data_committed = Signal(QModelIndex, object)

    def __init__(self, parent):
        """
        Args:
            parent (SpineDBEditor): parent widget, i.e. database editor
        """
        super().__init__(parent)
        self.data_committed.connect(parent._set_model_data)
        self.parameter_value_editor_requested.connect(parent.show_parameter_value_editor)

    def setModelData(self, editor, model, index):
        """Send signal."""
        data = editor.data()
        if isinstance(editor, ParameterValueLineEditor):
            data = join_value_and_type(*to_database(data))
        self.data_committed.emit(index, data)

    def setEditorData(self, editor, index):
        """Do nothing. We're setting editor data right away in createEditor."""

    def createEditor(self, parent, option, index):
        if self.parent().pivot_table_model.index_in_data(index):
            value = index.data(PARSED_ROLE)
            if value is None or isinstance(value, (Number, str)) and not isinstance(value, bool):
                editor = ParameterValueLineEditor(parent)
                editor.set_data(value)
                return editor
            self.parameter_value_editor_requested.emit(index.model().mapToSource(index))
            return None
        editor = PivotHeaderTableLineEditor(parent)
        editor.set_data(index.data(Qt.ItemDataRole.EditRole))
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
        value = index.data(Qt.ItemDataRole.EditRole)
        if value is None or isinstance(value, (Number, str)) and not isinstance(value, bool):
            editor = ParameterValueLineEditor(parent)
            editor.set_data(value)
            return editor
        self.value_editor_requested.emit(index)
        return None


class TableDelegate(QStyledItemDelegate):
    """Base class for all custom stacked table delegates.

    Attributes:
        db_mngr (SpineDBManager): database manager
    """

    data_committed = Signal(QModelIndex, object)

    def __init__(self, parent, db_mngr):
        """
        Args:
            parent (QWidget): parent widget
            db_mngr (SpineDBManager): database manager
        """
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
            editor.update_geometry(option)

    def _close_editor(self, editor, index):
        """Closes editor. Needed by SearchBarEditor."""
        self.closeEditor.emit(editor)
        self.setModelData(editor, index.model(), index)

    def _get_db_map(self, index):
        """Returns the db_map for the database at given index or None if not set yet."""
        model = index.model()
        header = model.horizontal_header_labels()
        db_map = index.sibling(index.row(), header.index("database")).data(DB_MAP_ROLE)
        if db_map is None:
            self.parent().msg_error.emit("Please select database first.")
        return db_map


class DatabaseNameDelegate(TableDelegate):
    """A delegate for the database name."""

    def createEditor(self, parent, option, index):
        """Returns editor."""
        editor = SearchBarEditor(self.parent(), parent)
        editor.set_data(
            index.data(Qt.ItemDataRole.DisplayRole),
            list(self.db_mngr.name_registry.display_name_iter(self.db_mngr.db_maps)),
        )
        editor.data_committed.connect(lambda *_: self._close_editor(editor, index))
        return editor


def _make_exclamation_font():
    """Creates font for invalid parameter type notification.

    Returns:
        QFont: font
    """
    font = QFont(TOOLBOX_FONT.family)
    font.setPixelSize(12)
    return font


class ParameterValueOrDefaultValueDelegate(TableDelegate):
    """A delegate for either the value or the default value."""

    parameter_value_editor_requested = Signal(QModelIndex)
    EXCLAMATION_COLOR = QColor("red")
    INDICATOR_WIDTH = 18

    def __init__(self, parent, db_mngr):
        """
        Args:
            parent (QWidget): parent widget
            db_mngr (SpineDBManager): database manager
        """
        super().__init__(parent, db_mngr)
        self._exclamation_font = _make_exclamation_font()
        self._db_value_list_lookup = {}

    def paint(self, painter, option, index):
        validation_state = index.data(PARAMETER_TYPE_VALIDATION_ROLE)
        if validation_state == INVALID_TYPE:
            left = option.rect.x()
            width = option.rect.width()
            height = option.rect.height()
            indicator_left = left + width - self.INDICATOR_WIDTH
            indicator_rect = QRect(indicator_left, option.rect.y(), self.INDICATOR_WIDTH, height)
            option.rect.setRight(indicator_left)
            text_position = indicator_rect.center()
            text_position.setY(text_position.y() + 5)
            text_position.setX(text_position.x() - 5)
            painter.setFont(self._exclamation_font)
            painter.setPen(self.EXCLAMATION_COLOR)
            painter.drawText(text_position, "\uf06a")
        super().paint(painter, option, index)

    def setModelData(self, editor, model, index):
        """Send signal."""
        display_value = editor.data()
        if display_value in self._db_value_list_lookup:
            value = self._db_value_list_lookup[display_value]
        else:
            value = join_value_and_type(*to_database(display_value))
        self.data_committed.emit(index, value)

    def _create_or_request_parameter_value_editor(self, parent, index):
        """Emits the signal to request a standalone `ParameterValueEditor` from parent widget.

        Args:
            parent (QWidget): editor's parent widget
            index (QModelIndex): index to parameter value model

        Returns:
            ParameterValueLineEditor: editor or None if ``parameter_value_editor_request`` signal was emitted
        """
        value = index.data(PARSED_ROLE)
        if value is None or isinstance(value, (Number, str)) and not isinstance(value, bool):
            editor = ParameterValueLineEditor(parent)
            editor.set_data(value)
            return editor
        self.parameter_value_editor_requested.emit(index)

    def _get_value_list_id(self, index, db_map):
        """Returns a value list id for the given index and db_map.

        Args:
            index (QModelIndex): value list's index
            db_map (DatabaseMapping): database mapping

        Returns:
            int: value list id
        """
        raise NotImplementedError()

    def createEditor(self, parent, option, index):
        """If the parameter has associated a value list, returns a SearchBarEditor.
        Otherwise, returns or requests a dedicated parameter_value editor.
        """
        self._db_value_list_lookup = {}
        db_map = self._get_db_map(index)
        if not db_map:
            return None
        value_list_id = self._get_value_list_id(index, db_map)
        if value_list_id:
            display_value_list = self.db_mngr.get_parameter_value_list(
                db_map, value_list_id, Qt.ItemDataRole.DisplayRole
            )
            db_value_list = self.db_mngr.get_parameter_value_list(db_map, value_list_id, Qt.ItemDataRole.EditRole)
            self._db_value_list_lookup = dict(zip(display_value_list, db_value_list))
            editor = SearchBarEditor(self.parent(), parent)
            editor.set_data(index.data(), self._db_value_list_lookup)
            editor.data_committed.connect(lambda *_: self._close_editor(editor, index))
            return editor
        return self._create_or_request_parameter_value_editor(parent, index)


class ParameterDefaultValueDelegate(ParameterValueOrDefaultValueDelegate):
    """A delegate for the default value."""

    def _get_value_list_id(self, index, db_map):
        """See base class"""
        h = index.model().header.index
        value_list_name = index.sibling(index.row(), h("value_list_name")).data()
        value_lists = self.db_mngr.get_items_by_field(db_map, "parameter_value_list", "name", value_list_name)
        if len(value_lists) == 1:
            return value_lists[0]["id"]


class ParameterValueDelegate(ParameterValueOrDefaultValueDelegate):
    """A delegate for the parameter_value."""

    def _get_value_list_id(self, index, db_map):
        """See base class."""
        h = index.model().header.index
        parameter_name = index.sibling(index.row(), h("parameter_name")).data()
        parameters = self.db_mngr.get_items_by_field(db_map, "parameter_definition", "name", parameter_name)
        entity_class_id = index.model().get_entity_class_id(index, db_map)
        parameter_ids = {p["id"] for p in parameters if p["entity_class_id"] == entity_class_id}
        value_list_ids = {
            self.db_mngr.get_item(db_map, "parameter_definition", id_).get("value_list_id") for id_ in parameter_ids
        }
        if len(value_list_ids) == 1:
            return next(iter(value_list_ids))


class ValueListDelegate(TableDelegate):
    """A delegate for the parameter value list."""

    def createEditor(self, parent, option, index):
        """Returns editor."""
        db_map = self._get_db_map(index)
        if not db_map:
            return None
        editor = SearchBarEditor(self.parent(), parent)
        name_list = [x["name"] for x in self.db_mngr.get_items(db_map, "parameter_value_list")]
        editor.set_data(index.data(Qt.ItemDataRole.EditRole), name_list)
        editor.data_committed.connect(lambda *_: self._close_editor(editor, index))
        return editor


class EntityClassNameDelegate(TableDelegate):
    """A delegate for the object_class name."""

    def createEditor(self, parent, option, index):
        """Returns editor."""
        db_map = self._get_db_map(index)
        if not db_map:
            return None
        editor = SearchBarEditor(self.parent(), parent)
        object_classes = self.db_mngr.get_items(db_map, "entity_class")
        editor.set_data(index.data(Qt.ItemDataRole.EditRole), [x["name"] for x in object_classes])
        editor.data_committed.connect(lambda *_: self._close_editor(editor, index))
        return editor


class ParameterNameDelegate(TableDelegate):
    """A delegate for the object parameter name."""

    def createEditor(self, parent, option, index):
        """Returns editor."""
        db_map = self._get_db_map(index)
        if not db_map:
            return None
        editor = SearchBarEditor(self.parent(), parent)
        entity_class_id = index.model().get_entity_class_id(index, db_map)
        if entity_class_id is not None:
            parameter_definitions = self.db_mngr.get_items_by_field(
                db_map, "parameter_definition", "entity_class_id", entity_class_id
            )
        else:
            parameter_definitions = self.db_mngr.get_items(db_map, "parameter_definition")
        name_list = list({x["name"]: None for x in parameter_definitions})
        editor.set_data(index.data(Qt.ItemDataRole.EditRole), name_list)
        editor.data_committed.connect(lambda *_: self._close_editor(editor, index))
        return editor


class EntityBynameDelegate(TableDelegate):
    """A delegate for the entity byname."""

    element_name_list_editor_requested = Signal(QModelIndex, object, object)

    def createEditor(self, parent, option, index):
        """Returns editor."""
        db_map = self._get_db_map(index)
        if not db_map:
            return None
        entity_class_id = index.model().get_entity_class_id(index, db_map)
        if entity_class_id is not None:
            entity_class = self.db_mngr.get_item(db_map, "entity_class", entity_class_id)
            if entity_class["dimension_id_list"]:
                self.element_name_list_editor_requested.emit(index, entity_class_id, db_map)
                return
            entities = self.db_mngr.get_items_by_field(db_map, "entity", "class_id", entity_class_id)
        else:
            entities = self.db_mngr.get_items(db_map, "entity")
        editor = SearchBarEditorWithCreation(self.parent(), parent)
        name_list = list({x["name"]: None for x in entities})
        editor.set_data(index.data(Qt.ItemDataRole.EditRole), name_list)
        editor.data_committed.connect(lambda *_: self._close_editor(editor, index))
        return editor


class AlternativeNameDelegate(TableDelegate):
    """A delegate for the alternative name."""

    def createEditor(self, parent, option, index):
        """Returns editor."""
        db_map = self._get_db_map(index)
        if not db_map:
            return None
        editor = SearchBarEditor(self.parent(), parent)
        name_list = [x["name"] for x in self.db_mngr.get_items(db_map, "alternative")]
        editor.set_data(index.data(Qt.ItemDataRole.EditRole), name_list)
        editor.data_committed.connect(lambda *_: self._close_editor(editor, index))
        return editor


class BooleanValueDelegate(TableDelegate):
    def setModelData(self, editor, model, index):
        """Sends signal."""
        value = editor.data()
        if not isinstance(value, bool):
            return
        self.data_committed.emit(index, value)

    def createEditor(self, parent, option, index):
        """Returns editor."""
        db_map = self._get_db_map(index)
        if not db_map:
            return None
        editor = self.make_editor(self.parent(), parent, index)
        editor.data_committed.connect(lambda *_: self._close_editor(editor, index))
        return editor

    @classmethod
    def make_editor(cls, parent, tutor, index):
        editor = BooleanSearchBarEditor(parent, tutor)
        editor.set_data(index.data(Qt.ItemDataRole.EditRole), None)
        return editor


class AlternativeDelegate(QStyledItemDelegate):
    """A delegate for the alternative tree."""

    data_committed = Signal(QModelIndex, object)

    def setModelData(self, editor, model, index):
        """Send signal."""
        index_data = index.data(Qt.ItemDataRole.EditRole)
        editor_data = editor.data()
        if editor_data == index_data:
            return
        self.data_committed.emit(index, editor_data)

    def setEditorData(self, editor, index):
        """Do nothing. We're setting editor data right away in createEditor."""

    def createEditor(self, parent, option, index):
        """Returns editor."""
        editor = CustomLineEditor(parent)
        editor.set_data(index.data(Qt.ItemDataRole.EditRole))
        return editor

    def _close_editor(self, editor, index):
        """Closes editor.

        Needed by SearchBarEditor.

        Args:
            editor (QWidget): editor widget
            index (QModelIndex): index that is being edited
        """
        self.closeEditor.emit(editor)
        self.setModelData(editor, index.model(), index)


class ScenarioDelegate(QStyledItemDelegate):
    """A delegate for the scenario tree."""

    data_committed = Signal(QModelIndex, object)

    def __init__(self, *args, **kwargs):
        """
        Args:
            *args: arguments passed to QStyledItemDelegate
            **kwargs: keyword arguments passed to QStyledItemDelegate
        """
        super().__init__(*args, **kwargs)
        self._alternative_ids = {}

    def setModelData(self, editor, model, index):
        """Send signal."""
        item = index.model().item_from_index(index)
        index_data = index.data(Qt.ItemDataRole.EditRole)
        editor_data = editor.data()
        if editor_data == index_data:
            return
        if item.item_type == "scenario_alternative":
            editor_data = self._alternative_ids.get(editor_data)
            if editor_data is None:
                return
        self.data_committed.emit(index, editor_data)

    def setEditorData(self, editor, index):
        """Do nothing. We're setting editor data right away in createEditor."""

    def _update_alternative_ids(self, item):
        """Updates available alternatives avoiding duplicates in a scenario.

        Excludes alternatives that are already in the scenario

        Args:
            item (ScenarioAlternativeItem): one of scenario's scenario alternatives

        Returns:
            list of str: available alternative names
        """
        excluded_ids = set(item.parent_item.alternative_id_list)
        self._alternative_ids = {
            x["name"]: x["id"]
            for x in item.db_mngr.get_items(item.db_map, "alternative")
            if x["id"] not in excluded_ids
        }
        return list(self._alternative_ids)

    def createEditor(self, parent, option, index):
        """Returns editor."""
        model = index.model()
        item = model.item_from_index(index)
        if item.item_type == "scenario_alternative":
            editor = SearchBarEditor(self.parent(), parent)
            index_data = index.data(Qt.ItemDataRole.EditRole)
            self._update_alternative_ids(item)
            names = sorted(self._alternative_ids)
            editor.set_data(index_data, names)
            editor.data_committed.connect(lambda *_: self._close_editor(editor, index))
        else:
            editor = CustomLineEditor(parent)
            editor.set_data(index.data(Qt.ItemDataRole.EditRole))
        return editor

    def updateEditorGeometry(self, editor, option, index):
        super().updateEditorGeometry(editor, option, index)
        item = index.model().item_from_index(index)
        if item.item_type == "scenario_alternative":
            editor.update_geometry(option)

    def _close_editor(self, editor, index):
        """Closes editor.

        Needed by SearchBarEditor.

        Args:
            editor (QWidget): editor widget
            index (QModelIndex): index that is being edited
        """
        self.closeEditor.emit(editor)
        self.setModelData(editor, index.model(), index)


class ParameterDefinitionNameAndDescriptionDelegate(TableDelegate):
    """A delegate for the parameter_name and description columns in Parameter Definition Table View."""

    def setEditorData(self, editor, index):
        editor.setText(index.data(Qt.ItemDataRole.DisplayRole))

    def createEditor(self, parent, option, index):
        editor = CustomLineEditor(parent)
        return editor


class ParameterValueListDelegate(QStyledItemDelegate):
    """A delegate for the parameter value list tree."""

    data_committed = Signal(QModelIndex, object)
    parameter_value_editor_requested = Signal(QModelIndex)

    def setModelData(self, editor, model, index):
        """Send signal."""
        self.closeEditor.emit(editor)
        item = model.item_from_index(index)
        data = editor.data()
        if item.item_type == "list_value":
            data = to_database(data)
        self.data_committed.emit(index, data)

    def setEditorData(self, editor, index):
        """Do nothing. We're setting editor data right away in createEditor."""

    def createEditor(self, parent, option, index):
        """Returns editor."""
        model = index.model()
        item = model.item_from_index(index)
        if item.item_type != "list_value":
            editor = CustomLineEditor(parent)
            editor.set_data(index.data(Qt.ItemDataRole.EditRole))
            return editor
        value = index.data(PARSED_ROLE)
        if value is None or isinstance(value, (Number, str)) and not isinstance(value, bool):
            editor = ParameterValueLineEditor(parent)
            editor.set_data(value)
            return editor
        self.parameter_value_editor_requested.emit(index)

    def _close_editor(self, editor, index):
        """Closes editor.

        Needed by SearchBarEditor.

        Args:
            editor (QWidget): editor widget
            index (QModelIndex): index that is being edited
        """
        self.closeEditor.emit(editor)
        self.setModelData(editor, index.model(), index)


class ManageItemsDelegate(QStyledItemDelegate):
    """A custom delegate for the model in {Add/Edit}ItemDialogs."""

    data_committed = Signal(QModelIndex, object)

    def setModelData(self, editor, model, index):
        """Send signal."""
        self.data_committed.emit(index, editor.data())

    def close_editor(self, editor, index):
        """Closes editor.

        Needed by SearchBarEditor.

        Args:
            editor (QWidget): editor widget
            index (QModelIndex): index that is being edited
        """
        self.closeEditor.emit(editor)
        self.setModelData(editor, index.model(), index)

    def updateEditorGeometry(self, editor, option, index):
        super().updateEditorGeometry(editor, option, index)
        if isinstance(editor, (SearchBarEditor, CheckListEditor)):
            editor.update_geometry(option)

    def connect_editor_signals(self, editor, index):
        """Connect editor signals if necessary.

        Args:
            editor (QWidget): editor widget
            index (QModelIndex): index being edited
        """
        if isinstance(editor, SearchBarEditor):
            editor.data_committed.connect(lambda *_: self.close_editor(editor, index))

    def _create_alternative_editor(self, parent, index):
        """Creates an editor.

        Args:
            parent (QWidget): parent widget
            index (QModelIndex): index being edited

        Returns:
            QWidget: editor
        """
        editor = SearchBarEditor(self.parent(), parent)
        name_list = set()
        dbs_by_alternative_name = {}
        database_column = self.parent().model.horizontal_header_labels().index("databases")
        database_index = index.model().index(index.row(), database_column)
        databases = database_index.data(Qt.ItemDataRole.DisplayRole).split(", ")
        for db_map_codename in databases:  # Filter possible alternatives based on selected databases
            db_map = self.parent().keyed_db_maps[db_map_codename]
            alternatives = self.parent().db_mngr.get_items(db_map, "alternative")
            for alternative in alternatives:
                dbs_by_alternative_name.setdefault(alternative["name"], set()).add(db_map)
        for alternative, db_maps in dbs_by_alternative_name.items():
            name_list.add(self.parent().append_db_codenames(alternative, db_maps))
        editor.set_data(index.data(Qt.ItemDataRole.EditRole), name_list)
        return editor

    def _create_entity_group_editor(self, parent, index):
        """Creates an editor.

        Args:
            parent (QWidget): parent widget
            index (QModelIndex): index being edited

        Returns:
            QWidget: editor
        """
        database_column = self.parent().model.horizontal_header_labels().index("databases")
        database_index = index.model().index(index.row(), database_column)
        databases = database_index.data(Qt.ItemDataRole.DisplayRole).split(", ")
        entity_class = self.parent().class_item
        dbs_by_entity_group = {}
        db_mngr = self.parent().db_mngr
        for db_map in entity_class.db_maps:
            if parent.db_mngr.name_registry.display_name(db_map.sa_url) not in databases:
                # Allow groups that are in selected DBs under "databases" column.
                continue
            class_item = db_mngr.get_item_by_field(db_map, "entity_class", "name", entity_class.name)
            if not class_item:
                continue
            ent_groups = db_mngr.get_items_by_field(db_map, "entity_group", "entity_class_id", class_item["id"])
            for ent_group in ent_groups:
                dbs_by_entity_group.setdefault(ent_group["group_name"], set()).add(db_map)
        name_list = set()
        for entity_group, db_maps in dbs_by_entity_group.items():
            name_list.add(self.parent().append_db_codenames(entity_group, db_maps))
        editor = SearchBarEditorWithCreation(self.parent(), parent)
        editor.set_data(index.data(Qt.ItemDataRole.EditRole), name_list)
        return editor

    def _create_database_editor(self, parent, index):
        """Creates an editor.

        Args:
            parent (QWidget): parent widget
            index (QModelIndex): index being edited

        Returns:
            QWidget: editor
        """
        editor = CheckListEditor(parent)
        all_databases = self.parent().all_databases(index.row())
        databases = index.data(Qt.ItemDataRole.DisplayRole).split(", ")
        editor.set_data(all_databases, databases)
        return editor

    def createEditor(self, parent, option, index):
        """Returns an editor."""
        header = index.model().horizontal_header_labels()
        if header[index.column()] == "databases":
            editor = self._create_database_editor(parent, index)
        else:
            editor = CustomLineEditor(parent)
            editor.set_data(index.data(Qt.ItemDataRole.EditRole))
        self.connect_editor_signals(editor, index)
        return editor


class ManageEntityClassesDelegate(ManageItemsDelegate):
    """A delegate for the model and view in {Add/Edit}EntityClassesDialog."""

    icon_color_editor_requested = Signal(QModelIndex)

    def paint(self, painter, option, index):
        """Get a pixmap from the index data and paint it in the middle of the cell."""
        header = index.model().horizontal_header_labels()
        if header[index.column()] == "display icon":
            icon = object_icon(index.data())
            icon.paint(painter, option.rect, Qt.AlignVCenter | Qt.AlignHCenter)
        else:
            super().paint(painter, option, index)

    def createEditor(self, parent, option, index):
        """Return editor."""
        header = index.model().horizontal_header_labels()
        label = header[index.column()]
        if label == "display icon":
            self.icon_color_editor_requested.emit(index)
            editor = None
        elif label in ("entity class name", "description"):
            editor = CustomLineEditor(parent)
            editor.set_data(index.data(Qt.ItemDataRole.EditRole))
        elif label == "databases":
            editor = self._create_database_editor(parent, index)
        elif label == "active by default":
            editor = BooleanValueDelegate.make_editor(self.parent(), parent, index)
        else:
            editor = SearchBarEditor(parent)
            entity_class_name_list = self.parent().entity_class_name_list(index.row())
            editor.set_data(index.data(Qt.ItemDataRole.EditRole), entity_class_name_list)
        self.connect_editor_signals(editor, index)
        return editor


class ManageEntitiesDelegate(ManageItemsDelegate):
    """A delegate for the model and view in {Add/Edit}EntitiesDialog."""

    def createEditor(self, parent, option, index):
        """Return editor."""
        header = index.model().horizontal_header_labels()
        if header[index.column()] == "entity name":
            editor = CustomLineEditor(parent)
            data = index.data(Qt.ItemDataRole.EditRole)
            editor.set_data(data)
        elif header[index.column()] == "databases":
            editor = self._create_database_editor(parent, index)
        elif header[index.column()] == "alternative":
            editor = self._create_alternative_editor(parent, index)
        elif header[index.column()] == "entity group":
            editor = self._create_entity_group_editor(parent, index)
        else:
            editor = SearchBarEditor(parent)
            entity_name_list = self.parent().entity_name_list(index.row(), index.column())
            editor.set_data(index.data(Qt.ItemDataRole.EditRole), entity_name_list)
        self.connect_editor_signals(editor, index)
        return editor


class RemoveEntitiesDelegate(ManageItemsDelegate):
    """A delegate for the model and view in RemoveEntitiesDialog."""

    def createEditor(self, parent, option, index):
        """Return editor."""
        header = index.model().horizontal_header_labels()
        if header[index.column()] == "databases":
            editor = self._create_database_editor(parent, index)
            self.connect_editor_signals(editor, index)
            return editor


class MetadataDelegate(QStyledItemDelegate):
    """A delegate for the name and value columns in Metadata Table View."""

    def setEditorData(self, editor, index):
        editor.setText(index.data(Qt.ItemDataRole.DisplayRole))

    def createEditor(self, parent, option, index):
        editor = CustomLineEditor(parent)
        return editor


class ItemMetadataDelegate(QStyledItemDelegate):
    """A delegate for name and value columns in item metadata editor."""

    def __init__(self, item_metadata_model, metadata_model, column, parent):
        """
        Args:
            item_metadata_model (ItemMetadataModel): item metadata model
            metadata_model (MetadataTableModel): metadata model
            column (int): item metadata table column
            parent (QObject, optional): parent object
        """
        super().__init__(parent)
        self._item_metadata_model = item_metadata_model
        self._metadata_model = metadata_model
        self._column = column

    def createEditor(self, parent, option, index):
        editor = CustomComboBoxEditor(parent)
        editor.setEditable(True)
        database_codename = self._item_metadata_model.index(index.row(), MetadataColumn.DB_MAP).data()
        items = set()
        if database_codename:
            for i in range(self._metadata_model.rowCount() - 1):
                if self._metadata_model.index(i, MetadataColumn.DB_MAP).data() == database_codename:
                    items.add(self._metadata_model.index(i, self._column).data())
        else:
            for i in range(self._metadata_model.rowCount() - 1):
                items.add(self._metadata_model.index(i, self._column).data())
        editor.addItems(sorted(items))
        return editor


class AddEntityButtonDelegate(QStyledItemDelegate):
    """A delegate for adding entities from a button in Entity Tree View."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.plus_icon = QIcon(":/icons/menu_icons/cube_plus.svg")

    def paint(self, painter, option, index):
        super().paint(painter, option, index)
        if not self.is_entity_class(index):  # Add the button only for entity classes
            return
        text_width, icon_size = self.get_text_width_and_icon_size(option, index)
        button_rect = self.get_button_rect(option, icon_size.width(), text_width)
        self.plus_icon.paint(painter, button_rect)

    @staticmethod
    def is_entity_class(index):
        """Check if index refers to entity class"""
        parent_index = index.parent()
        grand_parent = parent_index.parent()
        return index.column() == 0 and (parent_index.isValid() and not grand_parent.isValid())

    @staticmethod
    def get_button_rect(option, icon_width, text_width):
        size = 16
        margin = 18
        x = option.rect.left() + icon_width + text_width + margin
        y = option.rect.center().y() - size // 2
        return QRect(x, y, size, size)

    @staticmethod
    def get_text_width_and_icon_size(option, index):
        text = index.data(Qt.DisplayRole)
        font_metrics = QFontMetrics(option.font)
        text_width = font_metrics.horizontalAdvance(text)
        # For some reason the longer the text, the more its length is underestimated. Manual correction
        # term "needed" to make sure that the icon doesn't end up on top of the class name.
        text_width += (text_width - 8) * 0.06
        icon_size = option.decorationSize
        return text_width, icon_size

    def editorEvent(self, event, model, option, index):
        if event.type() == QEvent.MouseButtonPress and event.buttons() & Qt.LeftButton:
            text_width, icon_size = self.get_text_width_and_icon_size(option, index)
            button_rect = self.get_button_rect(option, icon_size.width(), text_width)
            if button_rect.contains(event.pos()) and self.is_entity_class(index):
                self.handle_button_click(index)
                return True
        return super().editorEvent(event, model, option, index)

    def handle_button_click(self, index):
        """Opens the Add Entities -dialog for the selected entity class item"""
        entity_tree_view = self.parent()
        entity_tree_view._context_item = entity_tree_view.model().item_from_index(index)
        entity_tree_view.add_entities()

    def sizeHint(self, option, index):
        size = super().sizeHint(option, index)
        if self.is_entity_class(index):
            # Add the width of the button so that the database column does not overlap with the button
            text_width, icon_size = self.get_text_width_and_icon_size(option, index)
            button_width = self.get_button_rect(option, icon_size.width(), text_width).width() * 2
            return QSize(size.width() + button_width, size.height())
        return size


class ParameterTypeListDelegate(QStyledItemDelegate):
    """Delegate for the 'valid types' column in Parameter definition table."""

    data_committed = Signal(QModelIndex, object)

    def __init__(self, db_editor, db_mngr):
        """
        Args:
            db_editor (SpineDBEditor): database editor widget
            db_mngr (SpineDBManager): database manager
        """
        super().__init__(db_editor)

    def setModelData(self, editor, model, index):
        self.data_committed.emit(index, editor.data())

    def setEditorData(self, editor, index):
        editor.set_data(index.data())

    def createEditor(self, parent, option, index):
        return ParameterTypeEditor(parent)

    def updateEditorGeometry(self, editor, option, index):
        top_left = option.rect.topLeft()
        popup_position = editor.parent().mapToGlobal(top_left)
        size_hint = editor.sizeHint()
        editor.setGeometry(
            popup_position.x(), popup_position.y(), max(option.rect.width(), size_hint.width()), size_hint.height()
        )
