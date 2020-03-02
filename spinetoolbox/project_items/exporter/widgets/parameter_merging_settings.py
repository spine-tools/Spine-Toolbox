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
Parameter merging settings widget.

:author: A. Soininen (VTT)
:date:   19.2.2020
"""

from PySide2.QtCore import QAbstractListModel, QItemSelectionModel, QModelIndex, Qt, Signal, Slot
from PySide2.QtWidgets import QWidget
from spinetoolbox.spine_io.exporters.gdx import MergingSetting
from .merging_error_flag import MergingErrorFlag

_ERROR_MESSAGE = "<span style='color:#ff3333;white-space: pre-wrap;'>{}</span>"


class ParameterMergingSettings(QWidget):
    """A widget for configure parameter merging."""

    removal_requested = Signal("QVariant")
    """Emitted when the settings widget wants to get removed from the parent window."""

    def __init__(self, entity_class_infos, parent, parameter_name=None, merging_setting=None):
        """
        Args:
            entity_class_infos (list): list of EntityClassInfo objects
            parent (QWidget): a parent widget
            parameter_name (str): merged parameter name of None for widget
            merging_setting (MergingSetting): merging settings or None for empty widget
        """
        from ..ui.parameter_merging_settings import Ui_Form

        super().__init__(parent)
        self._error_flags = (
            MergingErrorFlag.DOMAIN_NAME_MISSING
            | MergingErrorFlag.PARAMETER_NAME_MISSING
            | MergingErrorFlag.NO_PARAMETER_SELECTED
        )
        self._parameter_name = ""
        self._selected_domain_row = None
        self._index_position = 0
        self._ui = Ui_Form()
        self._ui.setupUi(self)
        self._ui.parameter_name_edit.textChanged.connect(self._update_parameter_name)
        self._ui.remove_button.clicked.connect(self._remove_self)
        self._domain_names_model = _DomainNameListModel(entity_class_infos)
        self._ui.domains_list_view.setModel(self._domain_names_model)
        self._ui.domains_list_view.selectionModel().selectionChanged.connect(self._handle_domain_selection_change)
        self._parameter_name_list_model = _ParameterNameListModel([])
        self._ui.parameter_name_list_view.setModel(self._parameter_name_list_model)
        self._ui.domain_name_edit.textChanged.connect(self._update_indexing_domain_name)
        self._ui.move_domain_left_button.clicked.connect(self._move_domain_left)
        self._ui.move_domain_right_button.clicked.connect(self._move_domain_right)
        self._ui.message_label.setText("")
        if parameter_name is not None:
            self._ui.parameter_name_edit.setText(parameter_name)
        if merging_setting is not None:
            domain_index = self._domain_names_model.index_for(merging_setting.previous_set)
            self._ui.domains_list_view.selectionModel().select(domain_index, QItemSelectionModel.Select)
            self._ui.domain_name_edit.setText(merging_setting.new_domain_name)
            self._ui.domain_description_edit.setText(merging_setting.new_domain_description)
            self._index_position = merging_setting.index_position
            self._reset_indexing_domains_label()
        self._check_state()

    @property
    def error_flags(self):
        return self._error_flags

    @property
    def parameter_name(self):
        """Name of the merged parameter."""
        return self._parameter_name

    def merging_setting(self):
        """Constructs the MergingSetting object from the widget's contents."""
        parameter_names = self._parameter_name_list_model.selected()
        domain_name = self._ui.domain_name_edit.text()
        domain_description = self._ui.domain_description_edit.text()
        entity_class_info = self._domain_names_model.item_at(self._selected_domain_row)
        previous_set = entity_class_info.name
        previous_domain_names = entity_class_info.domain_names
        setting = MergingSetting(parameter_names, domain_name, domain_description, previous_set, previous_domain_names)
        setting.index_position = self._index_position
        return setting

    def update(self, entity_class_infos):
        """Updates the settings after database commit."""
        selected_entity_class = self._domain_names_model.item_at(self._selected_domain_row)
        if not selected_entity_class.name in [info.name for info in entity_class_infos]:
            self.removal_requested.emit(self)
            return
        self._ui.domains_list_view.selectionModel().selectionChanged.disconnect()
        self._domain_names_model.update(entity_class_infos)
        domain_index = self._domain_names_model.index_for(selected_entity_class.name)
        self._ui.domains_list_view.selectionModel().select(domain_index, QItemSelectionModel.Select)
        self._selected_domain_row = domain_index.row()
        self._ui.domains_list_view.selectionModel().selectionChanged.connect(self._handle_domain_selection_change)
        entity_class_info = self._domain_names_model.item_at(self._selected_domain_row)
        self._parameter_name_list_model.update(entity_class_info.parameter_names)
        if self._index_position >= len(entity_class_info.domain_names):
            self._index_position = len(entity_class_info.domain_names) - 1
        self._reset_indexing_domains_label(domain_names=entity_class_info.domain_names)

    def _check_state(self):
        """Updates the message label according to widget's error state."""
        if self._error_flags & MergingErrorFlag.PARAMETER_NAME_MISSING:
            self._ui.message_label.setText(_ERROR_MESSAGE.format("Parameter name missing."))
        elif self._error_flags & MergingErrorFlag.DOMAIN_NAME_MISSING:
            self._ui.message_label.setText(_ERROR_MESSAGE.format("Domain name missing."))
        elif self._error_flags & MergingErrorFlag.NO_PARAMETER_SELECTED:
            self._ui.message_label.setText(_ERROR_MESSAGE.format("No domain selected."))
        else:
            self._ui.message_label.setText("")

    def _clear_flag(self, state):
        """Clears a state flag."""
        if not self._error_flags:
            return
        self._error_flags &= ~state
        self._check_state()

    def _set_flag(self, state):
        """Sets a state flag."""
        self._error_flags |= state
        self._check_state()

    def _reset_indexing_domains_label(self, domain_name=None, domain_names=None):
        """Rewrites the contents of indexing_domains_label."""
        if domain_name is None:
            domain_name = self._ui.domain_name_edit.text()
        bold_name = "<b>{}</b>".format(domain_name if domain_name else "unnamed")
        if domain_names is None:
            if self._selected_domain_row is not None:
                domain_names = self._domain_names_model.item_at(self._selected_domain_row).domain_names
            else:
                domain_names = list()
        label = (
            "("
            + ", ".join(domain_names[: self._index_position] + [bold_name] + domain_names[self._index_position :])
            + ")"
        )
        self._ui.indexing_domains_label.setText(label)

    @Slot(str)
    def _update_parameter_name(self, name):
        """Updates the merged parameter name."""
        self._parameter_name = name
        if not name:
            self._set_flag(MergingErrorFlag.PARAMETER_NAME_MISSING)
        else:
            self._clear_flag(MergingErrorFlag.PARAMETER_NAME_MISSING)

    @Slot(bool)
    def _remove_self(self, _):
        """Requests removal from the parent window."""
        self.removal_requested.emit(self)

    @Slot("QItemSelection", "QItemSelection")
    def _handle_domain_selection_change(self, selected, _):
        """Resets the settings after another item has been selected in domains_list_view."""
        self._selected_domain_row = selected.indexes()[0].row()
        entity_class_info = self._domain_names_model.item_at(self._selected_domain_row)
        domain_names = entity_class_info.domain_names
        self._index_position = len(domain_names)
        self._parameter_name_list_model.reset(entity_class_info.parameter_names)
        self._reset_indexing_domains_label(domain_names=domain_names)
        self._clear_flag(MergingErrorFlag.NO_PARAMETER_SELECTED)

    @Slot(str)
    def _update_indexing_domain_name(self, name):
        """Resets indexing_domains_label."""
        self._reset_indexing_domains_label(domain_name=name)
        if not name:
            self._set_flag(MergingErrorFlag.DOMAIN_NAME_MISSING)
        else:
            self._clear_flag(MergingErrorFlag.DOMAIN_NAME_MISSING)

    @Slot(bool)
    def _move_domain_left(self, _):
        """Moves the new indexing domain left in indexing_domains_label."""
        if self._index_position > 0:
            self._index_position -= 1
            self._reset_indexing_domains_label()

    @Slot(bool)
    def _move_domain_right(self, _):
        """Moves the new indexing domain left in indexing_domains_label."""
        if self._selected_domain_row is None:
            return
        domain_names = self._domain_names_model.item_at(self._selected_domain_row).domain_names
        if domain_names and self._index_position < len(domain_names):
            self._index_position += 1
            self._reset_indexing_domains_label()


class _DomainNameListModel(QAbstractListModel):
    """
    Model for domains_list_view.

    Stores EntityClassInfo objects displaying the entity name in domains_list_view.
    """

    def __init__(self, entity_classes):
        """
        Args:
            entity_classes (list): a list of EntityClassObjects
        """
        super().__init__()
        self._entity_classes = entity_classes

    def data(self, index, role=Qt.DisplayRole):
        """Returns model's data for given index."""
        if role != Qt.DisplayRole or not index.isValid():
            return None
        return self._entity_classes[index.row()].name

    def headerData(self, section, orientation):
        """Returns None."""
        return None

    def index_for(self, set_name):
        """Returns the QModelIndex for given set name."""
        try:
            row = [entity_class.name for entity_class in self._entity_classes].index(set_name)
        except ValueError:
            return QModelIndex()
        else:
            return self.index(row, 0)

    def item_at(self, row):
        """Returns the EntityClassInfo object at given row."""
        return self._entity_classes[row]

    def rowCount(self, parent=QModelIndex()):
        """Returns the size of the model."""
        return len(self._entity_classes)

    def update(self, entity_classes):
        """Updates the model."""
        self.beginResetModel()
        self._entity_classes = entity_classes
        self.endResetModel()


class _ParameterNameListModel(QAbstractListModel):
    """Model for parameter_name_list_view."""

    def __init__(self, names):
        """
        Args:
            names (list): list of parameter names to show in the view
        """
        super().__init__()
        self._names = names
        self._selected = len(names) * [True]

    def data(self, index, role=Qt.DisplayRole):
        """Returns the model's data."""
        if not index.isValid():
            return None
        if role == Qt.DisplayRole:
            return self._names[index.row()]
        if role == Qt.CheckStateRole:
            return Qt.Checked if self._selected[index.row()] else Qt.Unchecked
        return None

    def flags(self, index):
        """Returns flags for given index."""
        if not index.isValid():
            return Qt.NoItemFlags
        return Qt.ItemIsSelectable | Qt.ItemIsUserCheckable | Qt.ItemIsEnabled

    def headerData(self, section, orientation):
        """Returns None."""
        return None

    def reset(self, names):
        """Resets the model's contents when a new index is selected in domains_list_view."""
        self.beginResetModel()
        self._names = names
        self._selected = len(names) * [True]
        self.endResetModel()

    def rowCount(self, parent=QModelIndex()):
        """Returns the number of parameter names."""
        return len(self._names)

    def select(self, names):
        """Selects parameters for inclusion in the merged parameter."""
        for i, existing_name in enumerate(self._names):
            self._selected[i] = existing_name in names

    def selected(self):
        """Returns a list of the selected parameters."""
        return [name for name, select in zip(self._names, self._selected) if select]

    def setData(self, index, value, role=Qt.EditRole):
        """Selects or deselects the parameter at given index for inclusion in the merged parameter."""
        if role != Qt.CheckStateRole or not index.isValid():
            return False
        self._selected[index.row()] = value == Qt.Checked
        return True

    def update(self, names):
        """Updates the parameter names keeping the previous selection where it makes sense."""
        self.beginResetModel()
        updated_selection = len(names) * [True]
        for index, name in enumerate(names):
            try:
                old_index = self._names.index(name)
            except ValueError:
                continue
            else:
                updated_selection[index] = self._selected[old_index]
        self._names = names
        self._selected = updated_selection
        self.endResetModel()
