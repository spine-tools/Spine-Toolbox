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
Exporter project item.

:author: A. Soininen (VTT)
:date:   5.9.2019
"""

from copy import deepcopy
import pathlib
import os.path
from PySide2.QtCore import QObject, Signal, Slot
from spinedb_api import DatabaseMapping, SpineDBAPIError
from spinetoolbox.project_item import ProjectItem, ProjectItemResource
from spinetoolbox.project_commands import UpdateExporterOutFileNameCommand, UpdateExporterSettingsCommand
from spinetoolbox.helpers import deserialize_path, serialize_url
from spinetoolbox.spine_io import gdx_utils
from spinetoolbox.spine_io.exporters import gdx
from .settings_state import SettingsState
from .widgets.gdx_export_settings import GdxExportSettings
from .widgets.export_list_item import ExportListItem
from .worker import Worker


class Exporter(ProjectItem):
    """
    This project item handles all functionality regarding exporting a database to a file.

    Currently, only .gdx format is supported.
    """

    def __init__(self, name, description, settings_packs, x, y, toolbox, project, logger):
        """

        Args:
            name (str): item name
            description (str): item description
            settings_packs (list): dicts mapping database URLs to _SettingsPack objects
            x (float): initial X coordinate of item icon
            y (float): initial Y coordinate of item icon
            toolbox (ToolboxUI): a ToolboxUI instance
            project (SpineToolboxProject): the project this item belongs to
            logger (LoggerInterface): a logger instance
        """
        super().__init__(name, description, x, y, project, logger)
        self._toolbox = toolbox
        self._settings_packs = dict()
        self._export_list_items = dict()
        self._workers = dict()
        if settings_packs is None:
            settings_packs = list()
        for pack in settings_packs:
            serialized_url = pack["database_url"]
            url = deserialize_path(serialized_url, self._project.project_dir)
            url = _normalize_url(url)
            try:
                settings_pack = SettingsPack.from_dict(pack, url, logger)
            except gdx.GdxExportException:
                settings_pack = SettingsPack("")
            settings_pack.notifications.changed_due_to_settings_state.connect(self._report_notifications)
            self._settings_packs[url] = settings_pack
        for url, pack in self._settings_packs.items():
            if pack.state != SettingsState.OK:
                self._start_worker(url)

    def set_up(self):
        """See base class."""
        self._project.db_mngr.session_committed.connect(self._update_settings_after_db_commit)

    @staticmethod
    def item_type():
        """See base class."""
        return "Exporter"

    @staticmethod
    def category():
        """See base class."""
        return "Exporters"

    def settings_pack(self, database_path):
        return self._settings_packs[database_path]

    def make_signal_handler_dict(self):
        """Returns a dictionary of all shared signals and their handlers."""
        s = {self._properties_ui.open_directory_button.clicked: self.open_directory}
        return s

    def restore_selections(self):
        """Restores selections and connects signals."""
        self._properties_ui.item_name_label.setText(self.name)
        self._update_properties_tab()

    def _connect_signals(self):
        super()._connect_signals()
        for url, pack in self._settings_packs.items():
            if pack.state == SettingsState.ERROR:
                self._start_worker(url)

    def _update_properties_tab(self):
        """Updates the database list in the properties tab."""
        database_list_storage = self._properties_ui.databases_list_layout
        while not database_list_storage.isEmpty():
            widget_to_remove = database_list_storage.takeAt(0)
            widget_to_remove.widget().deleteLater()
        self._export_list_items.clear()
        for url, pack in self._settings_packs.items():
            item = self._export_list_items[url] = ExportListItem(url, pack.output_file_name, pack.state)
            database_list_storage.addWidget(item)
            item.open_settings_clicked.connect(self._show_settings)
            item.file_name_changed.connect(self._update_out_file_name)
            pack.state_changed.connect(item.handle_settings_state_changed)

    def execute_forward(self, resources):
        """See base class."""
        database_urls = [r.url for r in resources if r.type_ == "database"]
        gams_system_directory = self._resolve_gams_system_directory()
        if gams_system_directory is None:
            self._logger.msg_error.emit(f"<b>{self.name}</b>: Cannot proceed. No GAMS installation found.")
            return False
        for url in database_urls:
            settings_pack = self._settings_packs.get(url, None)
            if settings_pack is None:
                self._logger.msg_error.emit(f"<b>{self.name}</b>: No export settings defined for database {url}.")
                return False
            if not settings_pack.output_file_name:
                self._logger.msg_error.emit(f"<b>{self.name}</b>: No file name given to export database {url}.")
                return False
            if settings_pack.state == SettingsState.FETCHING:
                self._logger.msg_error.emit(f"<b>{self.name}</b>: Settings not ready for database {url}.")
                return False
            if settings_pack.state == SettingsState.INDEXING_PROBLEM:
                self._logger.msg_error.emit(
                    f"<b>{self.name}</b>: Parameters missing indexing information for database {url}."
                )
                return False
            if settings_pack.state == SettingsState.ERROR:
                self._logger.msg_error.emit(f"<b>{self.name}</b>: Ill formed database {url}.")
                return False
            out_path = os.path.join(self.data_dir, settings_pack.output_file_name)
            try:
                database_map = DatabaseMapping(url)
                gdx.to_gdx_file(
                    database_map,
                    out_path,
                    settings_pack.indexing_domains + settings_pack.merging_domains,
                    settings_pack.settings,
                    settings_pack.indexing_settings,
                    settings_pack.merging_settings,
                    gams_system_directory,
                )
            except (gdx.GdxExportException, SpineDBAPIError) as error:
                self._logger.msg_error.emit(f"Failed to export <b>{url}</b> to .gdx: {error}")
                return False
            finally:
                database_map.connection.close()
            self._logger.msg_success.emit(f"File <b>{out_path}</b> written")
        return True

    def _do_handle_dag_changed(self, resources):
        """See base class."""
        database_urls = set(r.url for r in resources if r.type_ == "database")
        if database_urls == set(self._settings_packs):
            self._check_state()
            return
        # Drop settings packs without connected databases.
        for database_url in list(self._settings_packs):
            if database_url not in database_urls:
                pack = self._settings_packs[database_url]
                if pack.settings_window is not None:
                    pack.settings_window.close()
                del self._settings_packs[database_url]
        # Add new databases.
        for database_url in database_urls:
            if database_url not in self._settings_packs:
                self._settings_packs[database_url] = SettingsPack("")
                self._start_worker(database_url)
        if self._active:
            self._update_properties_tab()
        self._check_state()

    def _start_worker(self, database_url, update_settings=False):
        """Starts fetching settings using a worker in another thread."""
        worker = self._workers.get(database_url, None)
        if worker is not None and worker.isRunning():
            worker.requestInterruption()
            worker.wait()
        elif worker is None:
            worker = Worker(database_url)
            worker.settings_read.connect(self._update_export_settings)
            worker.indexing_settings_read.connect(self._update_indexing_settings)
            worker.indexing_domains_read.connect(self._update_indexing_domains)
            worker.merging_settings_read.connect(self._update_merging_settings)
            worker.merging_domains_read.connect(self._update_merging_domains)
            worker.finished.connect(self._worker_finished)
            worker.errored.connect(self._worker_failed)
            self._workers[database_url] = worker
        if update_settings:
            pack = self._settings_packs[database_url]
            worker.set_previous_settings(
                pack.settings, pack.indexing_settings, pack.indexing_domains, pack.merging_settings
            )
        else:
            worker.reset_previous_settings()
        self._settings_packs[database_url].state = SettingsState.FETCHING
        worker.start()

    @Slot(str, "QVariant")
    def _update_export_settings(self, database_url, settings):
        """Sets new settings for given database."""
        pack = self._settings_packs.get(database_url)
        if pack is None:
            return
        pack.settings = settings

    @Slot(str, "QVariant")
    def _update_indexing_settings(self, database_url, indexing_settings):
        """Sets new indexing settings for given database."""
        pack = self._settings_packs.get(database_url)
        if pack is None:
            return
        pack.indexing_settings = indexing_settings

    @Slot(str, "QVariant")
    def _update_indexing_domains(self, database_url, domains):
        """Sets new indexing domains for given database."""
        pack = self._settings_packs.get(database_url)
        if pack is None:
            return
        pack.indexing_domains = domains

    @Slot(str, "QVariant")
    def _update_merging_settings(self, database_url, settings):
        """Sets new merging settings for given database."""
        pack = self._settings_packs.get(database_url)
        if pack is None:
            return
        pack.merging_settings = settings

    @Slot(str, "QVariant")
    def _update_merging_domains(self, database_url, domains):
        """Sets new merging domains for given database."""
        pack = self._settings_packs.get(database_url)
        if pack is None:
            return
        pack.merging_domains = domains

    @Slot(str)
    def _worker_finished(self, database_url):
        """Cleans up after a worker has finished fetching export settings."""
        if database_url in self._workers:
            worker = self._workers[database_url]
            worker.wait()
            worker.deleteLater()
            del self._workers[database_url]
            if database_url in self._settings_packs:
                settings_pack = self._settings_packs[database_url]
                if settings_pack.settings_window is not None:
                    self._send_settings_to_window(database_url)
                settings_pack.state = SettingsState.OK
            self._check_state()

    @Slot(str, "QVariant")
    def _worker_failed(self, database_url, exception):
        """Clean up after a worker has failed fetching export settings."""
        if database_url in self._settings_packs:
            self._logger.msg_error.emit(
                f"<b>[{self.name}]</b> Initializing settings for database {database_url}" f" failed: {exception}"
            )
            self._settings_packs[database_url].state = SettingsState.ERROR
            self._report_notifications()
        if database_url in self._workers:
            worker = self._workers[database_url]
            worker.wait()
            worker.deleteLater()
            del self._workers[database_url]

    def _check_state(self, clear_before_check=True):
        """
        Checks the status of database export settings.

        Updates both the notification message (exclamation icon) and settings states.
        """
        self._check_missing_file_names()
        self._check_duplicate_file_names()
        self._check_missing_parameter_indexing()
        self._check_erroneous_databases()
        self._report_notifications()

    def _check_missing_file_names(self):
        """Checks the status of output file names."""
        for pack in self._settings_packs.values():
            pack.notifications.missing_output_file_name = not pack.output_file_name

    def _check_duplicate_file_names(self):
        """Checks for duplicate output file names."""
        packs = list(self._settings_packs.values())
        for pack in packs:
            pack.notifications.duplicate_output_file_name = False
        for index, pack in enumerate(packs):
            if not pack.output_file_name:
                continue
            for other_pack in packs[index + 1 :]:
                if pack.output_file_name == other_pack.output_file_name:
                    pack.notifications.duplicate_output_file_name = True
                    other_pack.notifications.duplicate_output_file_name = True
                    break

    def _check_missing_parameter_indexing(self):
        """Checks the status of parameter indexing settings."""
        for pack in self._settings_packs.values():
            missing_indexing = False
            if pack.state not in (SettingsState.FETCHING, SettingsState.ERROR):
                pack.state = SettingsState.OK
                for setting in pack.indexing_settings.values():
                    if setting.indexing_domain is None:
                        pack.state = SettingsState.INDEXING_PROBLEM
                        missing_indexing = True
                        break
            pack.notifications.missing_parameter_indexing = missing_indexing

    def _check_erroneous_databases(self):
        """Checks errors in settings fetching from a database."""
        for pack in self._settings_packs.values():
            pack.notifications.erroneous_database = pack.state == SettingsState.ERROR

    @Slot()
    def _report_notifications(self):
        """Updates the exclamation icon and notifications labels."""
        if self._icon is None:
            return
        self.clear_notifications()
        merged = _Notifications()
        for pack in self._settings_packs.values():
            merged |= pack.notifications
        if merged.duplicate_output_file_name:
            self.add_notification("Duplicate output file names.")
        if merged.missing_output_file_name:
            self.add_notification("Output file name(s) missing.")
        if merged.missing_parameter_indexing:
            self.add_notification("Parameter indexing settings need to be updated.")
        if merged.erroneous_database:
            self.add_notification("Failed to initialize export settings for a database.")

    @Slot(str)
    def _show_settings(self, database_url):
        """Opens the item's settings window."""
        settings_pack = self._settings_packs[database_url]
        if settings_pack.state == SettingsState.FETCHING:
            return
        # Give window its own settings and indexing domains so Cancel doesn't change anything here.
        settings = deepcopy(settings_pack.settings)
        indexing_settings = deepcopy(settings_pack.indexing_settings)
        additional_parameter_indexing_domains = list(settings_pack.indexing_domains)
        merging_settings = deepcopy(settings_pack.merging_settings)
        additional_merging_domains = list(settings_pack.merging_domains)
        if settings_pack.settings_window is None:
            settings_pack.settings_window = GdxExportSettings(
                settings,
                indexing_settings,
                additional_parameter_indexing_domains,
                merging_settings,
                additional_merging_domains,
                database_url,
                self._toolbox,
            )
            settings_pack.settings_window.settings_accepted.connect(self._update_settings_from_settings_window)
            settings_pack.settings_window.settings_rejected.connect(self._dispose_settings_window)
            settings_pack.settings_window.reset_requested.connect(self._reset_settings_window)
            settings_pack.state_changed.connect(settings_pack.settings_window.handle_settings_state_changed)
        settings_pack.settings_window.show()

    @Slot(str)
    def _reset_settings_window(self, database_url):
        """Sends new settings to Gdx Export Settings window."""
        pack = self._settings_packs[database_url]
        pack.merging_settings = dict()
        pack.merging_domains = list()
        self._start_worker(database_url)

    @Slot(str)
    def _dispose_settings_window(self, database_url):
        """Deletes rejected export settings windows."""
        self._settings_packs[database_url].settings_window = None

    @Slot(str, str)
    def _update_out_file_name(self, file_name, database_path):
        """Pushes a new UpdateExporterOutFileNameCommand to the toolbox undo stack."""
        self._toolbox.undo_stack.push(UpdateExporterOutFileNameCommand(self, file_name, database_path))

    @Slot(str)
    def _update_settings_from_settings_window(self, database_path):
        """Pushes a new UpdateExporterSettingsCommand to the toolbox undo stack."""
        window = self._settings_packs[database_path].settings_window
        settings = window.settings
        indexing_settings = window.indexing_settings
        indexing_domains = window.indexing_domains
        merging_settings = window.merging_settings
        merging_domains = window.merging_domains
        self._toolbox.undo_stack.push(
            UpdateExporterSettingsCommand(
                self, settings, indexing_settings, indexing_domains, merging_settings, merging_domains, database_path
            )
        )

    def undo_redo_out_file_name(self, file_name, database_path):
        """Updates the output file name for given database"""
        if self._active:
            export_list_item = self._export_list_items.get(database_path)
            export_list_item.out_file_name_edit.setText(file_name)
        self._settings_packs[database_path].output_file_name = file_name
        self._settings_packs[database_path].notifications.missing_output_file_name = not file_name
        self._check_duplicate_file_names()
        self._report_notifications()

    def undo_or_redo_settings(
        self, settings, indexing_settings, indexing_domains, merging_settings, merging_domains, database_path
    ):
        """Updates the export settings for given database."""
        settings_pack = self._settings_packs[database_path]
        settings_pack.settings = settings
        settings_pack.indexing_settings = indexing_settings
        settings_pack.indexing_domains = indexing_domains
        settings_pack.merging_settings = merging_settings
        settings_pack.merging_domains = merging_domains
        window = settings_pack.settings_window
        if window is not None:
            self._send_settings_to_window(database_path)
        self._check_missing_parameter_indexing()
        self._report_notifications()

    def item_dict(self):
        """Returns a dictionary corresponding to this item's configuration."""
        d = super().item_dict()
        packs = list()
        for url, pack in self._settings_packs.items():
            pack_dict = pack.to_dict()
            serialized_url = serialize_url(url, self._project.project_dir)
            pack_dict["database_url"] = serialized_url
            packs.append(pack_dict)
        d["settings_packs"] = packs
        return d

    def _discard_settings_window(self, database_path):
        """Discards the settings window for given database."""
        del self._settings_windows[database_path]

    def _send_settings_to_window(self, database_url):
        """Resets settings in given export settings window."""
        settings_pack = self._settings_packs[database_url]
        window = settings_pack.settings_window
        settings = deepcopy(settings_pack.settings)
        indexing_settings = deepcopy(settings_pack.indexing_settings)
        indexing_domains = list(settings_pack.indexing_domains)
        merging_settings = deepcopy(settings_pack.merging_settings)
        merging_domains = list(settings_pack.merging_domains)
        window.reset_settings(settings, indexing_settings, indexing_domains, merging_settings, merging_domains)

    def update_name_label(self):
        """See base class."""
        self._properties_ui.item_name_label.setText(self.name)

    def _resolve_gams_system_directory(self):
        """Returns GAMS system path from Toolbox settings or None if GAMS default is to be used."""
        path = self._project.settings.value("appSettings/gamsPath", defaultValue=None)
        if not path:
            path = gdx_utils.find_gams_directory()
        if path is not None and os.path.isfile(path):
            path = os.path.dirname(path)
        return path

    def notify_destination(self, source_item):
        """See base class."""
        if source_item.item_type() == "Data Store":
            self._logger.msg.emit(
                f"Link established. Data Store <b>{source_item.name}</b> will be "
                f"exported to a .gdx file by <b>{self.name}</b> when executing."
            )
        else:
            super().notify_destination(source_item)

    @Slot("QVariant")
    def _update_settings_after_db_commit(self, committed_db_maps):
        """Refreshes export settings for databases after data has been committed to them."""
        for db_map in committed_db_maps:
            url = str(db_map.db_url)
            if url in self._settings_packs:
                self._start_worker(url, update_settings=True)

    @staticmethod
    def default_name_prefix():
        """See base class."""
        return "Exporter"

    def output_resources_forward(self):
        """See base class."""
        files = [pack.output_file_name for pack in self._settings_packs.values()]
        paths = [os.path.join(self.data_dir, file_name) for file_name in files]
        resources = [ProjectItemResource(self, "file", url=pathlib.Path(path).as_uri()) for path in paths]
        return resources

    def tear_down(self):
        """See base class."""
        self._project.db_mngr.session_committed.disconnect(self._update_settings_after_db_commit)


class SettingsPack(QObject):
    """
    Keeper of all settings and stuff needed for exporting a database.

    Attributes:
        output_file_name (str): name of the export file
        settings (Settings): export settings
        indexing_settings (dict): parameter indexing settings
        indexing_domains (list): extra domains needed for parameter indexing
        merging_settings (dict): parameter merging settings
        merging_domains (list): extra domains needed for parameter merging
        settings_window (GdxExportSettings): settings editor window
    """

    state_changed = Signal("QVariant")
    """Emitted when the pack's state changes."""

    def __init__(self, output_file_name):
        """
        Args:
            output_file_name (str): name of the export file
        """
        super().__init__()
        self.output_file_name = output_file_name
        self.settings = None
        self.indexing_settings = None
        self.indexing_domains = list()
        self.merging_settings = dict()
        self.merging_domains = list()
        self.settings_window = None
        self._state = SettingsState.FETCHING
        self.notifications = _Notifications()
        self.state_changed.connect(self.notifications.update_settings_state)

    @property
    def state(self):
        """State of the pack."""
        return self._state

    @state.setter
    def state(self, state):
        self._state = state
        self.state_changed.emit(state)

    def to_dict(self):
        """Stores the settings pack into a JSON compatible dictionary."""
        d = dict()
        d["output_file_name"] = self.output_file_name
        # Override ERROR by FETCHING so we'll retry reading the database when reopening the project.
        d["state"] = self.state.value
        if self.state != SettingsState.OK:
            return d
        d["settings"] = self.settings.to_dict()
        d["indexing_settings"] = gdx.indexing_settings_to_dict(self.indexing_settings)
        d["indexing_domains"] = [domain.to_dict() for domain in self.indexing_domains]
        d["merging_settings"] = {
            parameter_name: setting.to_dict() for parameter_name, setting in self.merging_settings.items()
        }
        d["merging_domains"] = [domain.to_dict() for domain in self.merging_domains]
        return d

    @staticmethod
    def from_dict(pack_dict, database_url, logger):
        """Restores the settings pack from a dictionary."""
        pack = SettingsPack(pack_dict["output_file_name"])
        pack.state = SettingsState(pack_dict["state"])
        if pack.state != SettingsState.OK:
            return pack
        pack.settings = gdx.Settings.from_dict(pack_dict["settings"])
        try:
            db_map = DatabaseMapping(database_url)
            pack.indexing_settings = gdx.indexing_settings_from_dict(pack_dict["indexing_settings"], db_map)
        except SpineDBAPIError as error:
            logger.msg_error.emit(
                f"Failed to fully restore Exporter settings. Error while reading database '{database_url}': {error}"
            )
            return pack
        else:
            db_map.connection.close()
        pack.indexing_domains = [gdx.Set.from_dict(set_dict) for set_dict in pack_dict["indexing_domains"]]
        pack.merging_settings = {
            parameter_name: gdx.MergingSetting.from_dict(setting_dict)
            for parameter_name, setting_dict in pack_dict["merging_settings"].items()
        }
        pack.merging_domains = [gdx.Set.from_dict(set_dict) for set_dict in pack_dict["merging_domains"]]
        return pack


class _Notifications(QObject):
    """
    Holds flags for different error conditions.

    Attributes:
        duplicate_output_file_name (bool): if True there are duplicate output file names
        missing_output_file_name (bool): if True the output file name is missing
        missing_parameter_indexing (bool): if True there are indexed parameters without indexing domains
        erroneous_database (bool): if True the database has issues
    """

    changed_due_to_settings_state = Signal()
    """Emitted when notifications have changed due to changes in settings state."""

    def __init__(self):
        super().__init__()
        self.duplicate_output_file_name = False
        self.missing_output_file_name = False
        self.missing_parameter_indexing = False
        self.erroneous_database = False

    def __ior__(self, other):
        """
        ORs the flags with another notifications.

        Args:
            other (_Notifications): a _Notifications object
        """
        self.duplicate_output_file_name |= other.duplicate_output_file_name
        self.missing_output_file_name |= other.missing_output_file_name
        self.missing_parameter_indexing |= other.missing_parameter_indexing
        self.erroneous_database |= other.erroneous_database
        return self

    @Slot("QVariant")
    def update_settings_state(self, state):
        """Updates the notifications according to settings state."""
        changed = False
        is_erroneous = state == SettingsState.ERROR
        if self.erroneous_database != is_erroneous:
            self.erroneous_database = is_erroneous
            changed = True
        is_problem = state == state.INDEXING_PROBLEM
        if self.missing_parameter_indexing != is_problem:
            self.missing_parameter_indexing = is_problem
            changed = True
        if changed:
            self.changed_due_to_settings_state.emit()


def _normalize_url(url):
    """
    Normalized url's path separators to their OS specific characters.

    This function is needed during the transition period from no-version to version 1 project files.
    It should be removed once we are using version 1 files.
    """
    return "sqlite:///" + url[10:].replace("/", os.sep)
