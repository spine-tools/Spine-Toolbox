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

from PySide2.QtCore import QItemSelection, QItemSelectionModel, Signal, Slot
from PySide2.QtWidgets import QWidget
from spinetoolbox.spine_io.exporters.gdx import MergingSetting
from .merging_error_flag import MergingErrorFlag
from ..mvcmodels.domain_name_list_model import DomainNameListModel
from ..mvcmodels.parameter_name_list_model import ParameterNameListModel

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
        from ..ui.parameter_merging_settings import Ui_Form  # pylint: disable=import-outside-toplevel

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
        self._domain_names_model = DomainNameListModel(entity_class_infos)
        self._ui.domains_list_view.setModel(self._domain_names_model)
        self._ui.domains_list_view.selectionModel().selectionChanged.connect(self._handle_domain_selection_change)
        self._parameter_name_list_model = ParameterNameListModel([])
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

    @Slot(QItemSelection, QItemSelection)
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
