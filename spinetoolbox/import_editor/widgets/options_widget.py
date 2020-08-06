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


class OptionsWidget(QWidget):
    """A widget for handling simple options."""

    options_changed = Signal(dict)
    """Emitted whenever an option in the widget is changed."""

    def __init__(self, connector):
        """
        Args:
            connector (ConnectionManager): the connection manager whose current table's options are show on the widget
        """
        super().__init__()
        self._connector = connector
        self._options = connector.connection.OPTIONS
        connector.current_table_changed.connect(self._fetch_options_from_connector)
        self.options_changed.connect(connector.update_options)

        # ui
        QFormLayout(self)
        self._ui_choices = {str: QLineEdit, list: QComboBox, int: QSpinBox, bool: QCheckBox}
        self._ui_elements = {}
        self._build_ui()
        self.set_options()

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
            if isinstance(ui_element, QSpinBox):
                handler = functools.partial(_emit_spin_box_option_changed, option_key=key, options_widget=self)
                ui_element.valueChanged.connect(handler)
            elif isinstance(ui_element, QLineEdit):
                handler = functools.partial(_emit_line_edit_option_changed, option_key=key, options_widget=self)
                ui_element.textChanged.connect(handler)
            elif isinstance(ui_element, QCheckBox):
                handler = functools.partial(_emit_check_box_option_changed, option_key=key, options_widget=self)
                ui_element.stateChanged.connect(handler)
            elif isinstance(ui_element, QComboBox):
                ui_element.addItems([str(x) for x in options["Items"]])
                handler = functools.partial(_emit_combo_box_option_changed, option_key=key, options_widget=self)
                ui_element.currentTextChanged.connect(handler)
            self._ui_elements[key] = ui_element

            # Add to layout:
            self.layout().addRow(QLabel(options['label'] + ':'), ui_element)

    def set_options(self, options=None, set_missing_default=True):
        """Sets state of options

        Args:
            options (dict, optional): Dict with option name as key and value as value (default: {None})
            set_missing_default (bool): Sets missing options to default if True (default: {True})
        """
        if options is None:
            options = {}
        for key, ui_element in self._ui_elements.items():
            default = None
            if set_missing_default:
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

    @Slot()
    def _fetch_options_from_connector(self):
        """Read options from the connector."""
        self.set_options(self._connector.get_current_options())


def _emit_spin_box_option_changed(i, option_key, options_widget):
    """A 'slot' to transform changes in QSpinBox into changes in options."""
    options = {option_key: i}
    options_widget.options_changed.emit(options)


def _emit_line_edit_option_changed(text, option_key, options_widget):
    """A 'slot' to transform changes in QLineEdit into changes in options."""
    options = {option_key: text}
    options_widget.options_changed.emit(options)


def _emit_check_box_option_changed(state, option_key, options_widget):
    """A 'slot' to transform changes in QCheckBox into changes in options."""
    options = {option_key: state == Qt.Checked}
    options_widget.options_changed.emit(options)


def _emit_combo_box_option_changed(text, option_key, options_widget):
    """A 'slot' to transform changes in QComboBox into changes in options."""
    options = {option_key: text}
    options_widget.options_changed.emit(options)
