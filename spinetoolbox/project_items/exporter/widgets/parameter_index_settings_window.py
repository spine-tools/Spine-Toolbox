######################################################################################################################
# Copyright (C) 2017-2019 Spine project consortium
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""
Parameter indexing settings window for .gdx export.

:author: A. Soininen (VTT)
:date:   25.11.2019
"""

from PySide2.QtCore import Qt, Signal, Slot
from PySide2.QtWidgets import QMessageBox, QWidget
from .parameter_index_settings import IndexSettingsState, ParameterIndexSettings


class ParameterIndexSettingsWindow(QWidget):
    """A window which shows a list of ParameterIndexSettings widgets, one for each parameter with indexed values."""

    settings_approved = Signal()
    """Emitted when the settings have been approved."""
    settings_rejected = Signal()
    """Emitted when the settings have been rejected."""

    def __init__(self, indexing_settings, available_existing_domains, new_domains, database_path, parent):
        """
        Args:
            indexing_settings (dict): a map from parameter name to IndexingSettings
            available_existing_domains (dict): a map from existing domain names to lists of record keys
            new_domains (dict): a map from new domain names to lists of record keys
            database_path (str): a database url
            parent (QWidget): a parent widget
        """
        from ..ui.parameter_index_settings_window import Ui_Form

        super().__init__(parent, f=Qt.Window)
        self._available_existing_domains = dict(available_existing_domains)
        self._indexing_settings = indexing_settings
        self._new_domains = list()
        self._ui = Ui_Form()
        self._ui.setupUi(self)
        self.setWindowTitle("Gdx Parameter Indexing Settings    -- {} --".format(database_path))
        self.setAttribute(Qt.WA_DeleteOnClose, True)
        self._ui.button_box.accepted.connect(self._collect_and_hide)
        self._ui.button_box.rejected.connect(self._reject_and_close)
        self._settings_widgets = dict()
        for parameter_name, indexing_setting in indexing_settings.items():
            settings_widget = ParameterIndexSettings(
                parameter_name,
                indexing_setting,
                self._available_existing_domains,
                new_domains,
                self._ui.settings_area_contents,
            )
            self._ui.settings_area_layout.insertWidget(0, settings_widget)
            self._settings_widgets[parameter_name] = settings_widget
        if not indexing_settings:
            self._ui.widget_stack.setCurrentIndex(1)
            return
        self._ui.widget_stack.setCurrentIndex(0)

    @property
    def indexing_settings(self):
        """indexing settings dictionary"""
        return self._indexing_settings

    @property
    def new_domains(self):
        """list of additional domains needed for indexing"""
        return self._new_domains

    @Slot(str, list)
    def reorder_indexes(self, domain_name, first, last, target):
        for widget in self._settings_widgets.values():
            if widget.is_using_domain(domain_name):
                widget.reorder_indexes(first, last, target)

    @Slot()
    def _collect_and_hide(self):
        """Collects settings from individual ParameterIndexSettings widgets and hides the window."""
        for parameter_name, settings_widget in self._settings_widgets.items():
            if settings_widget.state != IndexSettingsState.OK:
                self._ui.settings_area.ensureWidgetVisible(settings_widget)
                message = "Parameter '{}' indexing not well-defined.".format(parameter_name)
                QMessageBox.warning(self, "Bad Parameter Indexing", message)
                return
            if settings_widget.new_domain_name in self._available_existing_domains:
                self._ui.settings_area.ensureWidgetVisible(settings_widget)
                settings_widget.state = IndexSettingsState.DOMAIN_NAME_CLASH
                message = "Parameter '{}' indexing domain name already exists.".format(parameter_name)
                QMessageBox.warning(self, "Domain Name Clash", message)
                return
        self._new_domains.clear()
        for parameter_name, settings_widget in self._settings_widgets.items():
            indexing_domain, new_domain = settings_widget.indexing_domain()
            self._indexing_settings[parameter_name].indexing_domain = indexing_domain
            if new_domain is not None:
                self._new_domains.append(new_domain)
        self.settings_approved.emit()
        self.hide()

    @Slot()
    def _reject_and_close(self):
        self.close()

    def closeEvent(self, event):
        super().closeEvent(event)
        self.settings_rejected.emit()
