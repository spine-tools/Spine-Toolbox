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
Contains OptionsWidget class.

:author: P. Vennström (VTT)
:date:   1.6.2019
"""
import functools
from PySide2.QtCore import Qt, Signal, Slot
from PySide2.QtWidgets import QLabel, QLineEdit, QComboBox, QCheckBox, QSpinBox, QWidget, QFormLayout
from ..commands import SetConnectorOption


class OptionsWidget(QWidget):
    """A widget for handling simple options."""

    options_changed = Signal(dict)
    """Emitted whenever an option in the widget is changed."""
    about_to_undo = Signal(str)
    """Emitted before undo action."""

    def __init__(self, connector, undo_stack):
        """
        Args:
            connector (ConnectionManager): the connection manager whose current table's options are show on the widget
            undo_stack (QUndoStack): undo stack
        """
        super().__init__()
        self._connector = connector
        self._options = connector.connection.OPTIONS
        self._undo_stack = undo_stack
        self._undo_enabled = True
        self._current_source_table = None
        connector.current_table_changed.connect(self._fetch_options_from_connector)
        self.options_changed.connect(connector.update_options)

        # ui
        QFormLayout(self)
        self._ui_choices = {str: QLineEdit, list: QComboBox, int: QSpinBox, bool: QCheckBox}
        self._ui_elements = {}
        self._build_ui()
        self._set_options(self._connector.current_table)

    def _build_ui(self):
        """Builds ui from specification in dict
        """
        for key, options in self._options.items():
            ui_element = self._ui_choices[options["type"]]()
            maximum = options.get('Maximum', None)
            if maximum is not None:
                ui_element.setMaximum(maximum)
            minimum = options.get('Minimum', None)
            if minimum is not None:
                ui_element.setMinimum(minimum)
            max_length = options.get('MaxLength', None)
            if max_length is not None:
                ui_element.setMaxLength(max_length)
            bound_arguments = dict(option_key=key, options_widget=self)
            if isinstance(ui_element, QSpinBox):
                handler = functools.partial(_emit_spin_box_option_changed, **bound_arguments)
                ui_element.valueChanged.connect(handler)
            elif isinstance(ui_element, QLineEdit):
                handler = functools.partial(_emit_line_edit_option_changed, **bound_arguments)
                ui_element.textChanged.connect(handler)
            elif isinstance(ui_element, QCheckBox):
                handler = functools.partial(_emit_check_box_option_changed, **bound_arguments)
                ui_element.stateChanged.connect(handler)
            elif isinstance(ui_element, QComboBox):
                ui_element.addItems([str(x) for x in options["Items"]])
                handler = functools.partial(_emit_combo_box_option_changed, **bound_arguments)
                ui_element.currentTextChanged.connect(handler)
            self._ui_elements[key] = ui_element

            # Add to layout:
            self.layout().addRow(QLabel(options['label'] + ':'), ui_element)

    @property
    def connector(self):
        """The connection manager linked to this options widget."""
        return self._connector

    @property
    def undo_stack(self):
        return self._undo_stack

    @property
    def undo_enabled(self):
        return self._undo_enabled

    @property
    def current_source_table(self):
        return self._current_source_table

    def _set_options(self, source_table, options=None):
        """Sets state of options

        Args:
            source_table (str): name of the source table
            options (dict, optional): Dict with option name as key and value as value (default: {None})
        """
        self._current_source_table = source_table
        if options is None:
            options = {}
        for key, ui_element in self._ui_elements.items():
            default = self._options[key]['default']
            value = options.get(key, default)
            if value is None:
                continue
            ui_element.blockSignals(True)
            if isinstance(ui_element, QSpinBox):
                ui_element.setValue(value)
            elif isinstance(ui_element, QLineEdit):
                ui_element.setText(value)
            elif isinstance(ui_element, QCheckBox):
                ui_element.setChecked(value)
            elif isinstance(ui_element, QComboBox):
                ui_element.setCurrentText(value)
            ui_element.blockSignals(False)

    def set_option_without_undo(self, source_table, option_key, value):
        self.about_to_undo.emit(source_table)
        ui_element = self._ui_elements[option_key]
        if isinstance(ui_element, QSpinBox):
            current_value = ui_element.value()
            if value == current_value:
                return
            self._undo_enabled = False
            ui_element.setValue(value)
            self._undo_enabled = True
        elif isinstance(ui_element, QLineEdit):
            current_value = ui_element.text()
            if value == current_value:
                return
            self._undo_enabled = False
            ui_element.setText(value)
            self._undo_enabled = True
        elif isinstance(ui_element, QCheckBox):
            current_value = ui_element.isChecked()
            if value == current_value:
                return
            self._undo_enabled = False
            ui_element.setChecked(value)
            self._undo_enabled = True
        elif isinstance(ui_element, QComboBox):
            current_value = ui_element.currentText()
            if value == current_value:
                return
            self._undo_enabled = False
            ui_element.setCurrentText(value)
            self._undo_enabled = True

    @Slot()
    def _fetch_options_from_connector(self):
        """Read options from the connector."""
        table_name = self._connector.current_table
        self._set_options(table_name, self._connector.get_current_options())


def _emit_spin_box_option_changed(i, option_key, options_widget):
    """
    A 'slot' to transform changes in QSpinBox into changes in options.

    Args:
        text (str): text for undo/redo
        option_key (str): option's key
        options_widget (OptionsWidget): options widget
    """
    if options_widget.undo_enabled:
        previous_value = options_widget.connector.get_current_option_value(option_key)
        options_widget.undo_stack.push(
            SetConnectorOption(options_widget.current_source_table, option_key, options_widget, i, previous_value)
        )
    options = {option_key: i}
    options_widget.options_changed.emit(options)


def _emit_line_edit_option_changed(text, option_key, options_widget):
    """
    A 'slot' to transform changes in QLineEdit into changes in options.

    Args:
        text (str): text for undo/redo
        option_key (str): option's key
        options_widget (OptionsWidget): options widget
    """
    if options_widget.undo_enabled:
        previous_value = options_widget.connector.get_current_option_value(option_key)
        options_widget.undo_stack.push(
            SetConnectorOption(options_widget.current_source_table, option_key, options_widget, text, previous_value)
        )
    options = {option_key: text}
    options_widget.options_changed.emit(options)


def _emit_check_box_option_changed(state, option_key, options_widget):
    """
    A 'slot' to transform changes in QCheckBox into changes in options.

    Args:
        text (str): text for undo/redo
        option_key (str): option's key
        options_widget (OptionsWidget): options widget
    """
    if options_widget.undo_enabled:
        previous_value = options_widget.connector.get_current_option_value(option_key)
        options_widget.undo_stack.push(
            SetConnectorOption(options_widget.current_source_table, option_key, options_widget, state, previous_value)
        )
    options = {option_key: state == Qt.Checked}
    options_widget.options_changed.emit(options)


def _emit_combo_box_option_changed(text, option_key, options_widget):
    """
    A 'slot' to transform changes in QComboBox into changes in options.

    Args:
        text (str): text for undo/redo
        option_key (str): option's key
        options_widget (OptionsWidget): options widget
    """
    if options_widget.undo_enabled:
        previous_value = options_widget.connector.get_current_option_value(option_key)
        options_widget.undo_stack.push(
            SetConnectorOption(options_widget.current_source_table, option_key, options_widget, text, previous_value)
        )
    options = {option_key: text}
    options_widget.options_changed.emit(options)
