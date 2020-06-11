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
from PySide2.QtCore import Qt, Slot
from spinedb_api import DatabaseMapping, SpineDBAPIError
from spinetoolbox.project_item import ProjectItem
from spinetoolbox.project_item_resource import ProjectItemResource
from spinetoolbox.helpers import deserialize_path, serialize_url
from spinetoolbox.spine_io.exporters import gdx
from .commands import UpdateExporterOutFileNameCommand, UpdateExporterSettingsCommand
from ..shared.commands import UpdateCancelOnErrorCommand
from .db_utils import latest_database_commit_time_stamp
from .executable_item import ExecutableItem
from .item_info import ItemInfo
from .notifications import Notifications
from .settings_pack import SettingsPack
from .settings_state import SettingsState
from .widgets.gdx_export_settings import GdxExportSettings
from .widgets.export_list_item import ExportListItem
from .worker import Worker


class Exporter(ProjectItem):
    """
    This project item handles all functionality regarding exporting a database to a file.

    Currently, only .gdx format is supported.
    """

    def __init__(
        self,
        toolbox,
        project,
        logger,
        name,
        description,
        settings_packs,
        x,
        y,
        cancel_on_export_error=None,
        cancel_on_error=None,
    ):
        """
        Args:
            toolbox (ToolboxUI): a ToolboxUI instance
            project (SpineToolboxProject): the project this item belongs to
            logger (LoggerInterface): a logger instance
            name (str): item name
            description (str): item description
            settings_packs (list): dicts mapping database URLs to _SettingsPack objects
            x (float): initial X coordinate of item icon
            y (float): initial Y coordinate of item icon
            cancel_on_export_error (bool, options): legacy ``cancel_on_error`` option
            cancel_on_error (bool, options): True if execution should fail on all export errors,
                False to ignore certain error cases; optional to provide backwards compatibility
        """
        super().__init__(name, description, x, y, project, logger)
        self._toolbox = toolbox
        if cancel_on_error is not None:
            self._cancel_on_error = cancel_on_error
        else:
            self._cancel_on_error = cancel_on_export_error if cancel_on_export_error is not None else True
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
            except gdx.GdxExportException as error:
                logger.msg_error.emit(f"Failed to fully restore Exporter settings: {error}")
                settings_pack = SettingsPack("")
            settings_pack.notifications.changed_due_to_settings_state.connect(self._report_notifications)
            self._settings_packs[url] = settings_pack
        for url, pack in self._settings_packs.items():
            if pack.state not in (SettingsState.OK, SettingsState.INDEXING_PROBLEM):
                self._start_worker(url)
            elif pack.last_database_commit != _latest_database_commit_time_stamp(url):
                self._start_worker(url, update_settings=True)

    def set_up(self):
        """See base class."""
        self._project.db_mngr.session_committed.connect(self._update_settings_after_db_commit)
        self._project.db_mngr.database_created.connect(self._update_settings_after_db_creation)

    @staticmethod
    def item_type():
        """See base class."""
        return ItemInfo.item_type()

    @staticmethod
    def item_category():
        """See base class."""
        return ItemInfo.item_category()

    def execution_item(self):
        """Creates Exporter's execution counterpart."""
        gams_path = self._project.settings.value("appSettings/gamsPath", defaultValue=None)
        executable = ExecutableItem(
            self.name, self._settings_packs, self._cancel_on_error, self.data_dir, gams_path, self._logger
        )
        return executable

    def settings_pack(self, database_path):
        return self._settings_packs[database_path]

    def make_signal_handler_dict(self):
        """Returns a dictionary of all shared signals and their handlers."""
        s = {
            self._properties_ui.open_directory_button.clicked: self.open_directory,
            self._properties_ui.cancel_on_error_check_box.stateChanged: self._cancel_on_error_option_changed,
        }
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
        self._properties_ui.cancel_on_error_check_box.setCheckState(
            Qt.Checked if self._cancel_on_error else Qt.Unchecked
        )

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
        worker = self._workers.get(database_url)
        if worker is not None:
            worker.thread.quit()
            worker.thread.wait()
        worker = Worker(database_url)
        self._workers[database_url] = worker
        worker.database_unavailable.connect(self._cancel_worker)
        worker.finished.connect(self._worker_finished)
        worker.errored.connect(self._worker_failed)
        worker.msg.connect(self._worker_msg)
        worker.msg_warning.connect(self._worker_msg_warning)
        worker.msg_error.connect(self._worker_msg_error)
        if update_settings:
            pack = self._settings_packs[database_url]
            worker.set_previous_settings(
                pack.settings, pack.indexing_settings, pack.indexing_domains, pack.merging_settings
            )
        self._settings_packs[database_url].state = SettingsState.FETCHING
        worker.thread.start()

    @Slot(str, str)
    def _worker_msg(self, database_url, text):
        if database_url in self._workers:
            message = f"<b>{self.name}</b>: While initializing export settings database '{database_url}': {text}"
            self._logger.msg.emit(message)

    @Slot(str, str)
    def _worker_msg_warning(self, database_url, text):
        if database_url in self._workers:
            warning = f"<b>{self.name}</b>: While initializing export settings for database '{database_url}': {text}"
            self._logger.msg_warning.emit(warning)

    @Slot(str, str)
    def _worker_msg_error(self, database_url, text):
        if database_url in self._workers:
            error = f"<b>{self.name}</b>: While initializing export settings database '{database_url}': {text}"
            self._logger.msg_error.emit(error)

    @Slot(str, "Qvariant", "QVariant")
    def _worker_finished(self, database_url, result):
        """Gets and updates and export settings pack from a worker."""
        worker = self._workers.get(database_url)
        if worker is None:
            return
        worker.thread.wait()
        worker.deleteLater()
        del self._workers[database_url]
        pack = self._settings_packs.get(database_url)
        if pack is None:
            return
        pack.last_database_commit = result.commit_time_stamp
        pack.settings = result.set_settings
        pack.indexing_settings = result.indexing_settings
        pack.indexing_domains = result.indexing_domains
        pack.merging_settings = result.merging_settings
        pack.merging_domains = result.merging_domains
        if pack.settings_window is not None:
            self._send_settings_to_window(database_url)
        pack.state = SettingsState.OK
        self._toolbox.update_window_modified(False)
        self._check_state()

    @Slot(str, "QVariant")
    def _worker_failed(self, database_url, exception):
        """Clean up after a worker has failed fetching export settings."""
        worker = self._workers[database_url]
        if worker is None:
            return
        worker.thread.quit()
        worker.thread.wait()
        worker.deleteLater()
        del self._workers[database_url]
        if database_url in self._settings_packs:
            self._logger.msg_error.emit(
                f"<b>[{self.name}]</b> Initializing settings for database {database_url} failed: {exception}"
            )
            self._settings_packs[database_url].state = SettingsState.ERROR
            self._report_notifications()

    @Slot(str)
    def _cancel_worker(self, database_url):
        """Cleans up after worker has given up fetching export settings."""
        worker = self._workers[database_url]
        if worker is None:
            return
        worker.thread.quit()
        worker.thread.wait()
        worker.deleteLater()
        del self._workers[database_url]
        self._settings_packs[database_url].state = SettingsState.ERROR

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
                    if setting.indexing_domain is None and pack.settings.is_exportable(setting.set_name):
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
        merged = Notifications()
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
        settings = window.set_settings
        indexing_settings = window.indexing_settings
        indexing_domains = window.indexing_domains
        merging_settings = window.merging_settings
        merging_domains = window.merging_domains
        self._toolbox.undo_stack.push(
            UpdateExporterSettingsCommand(
                self, settings, indexing_settings, indexing_domains, merging_settings, merging_domains, database_path
            )
        )

    @Slot(int)
    def _cancel_on_error_option_changed(self, checkbox_state):
        """Handles changes to the Cancel export on error option."""
        cancel = checkbox_state == Qt.Checked
        if self._cancel_on_error == cancel:
            return
        self._toolbox.undo_stack.push(UpdateCancelOnErrorCommand(self, cancel))

    def set_cancel_on_error(self, cancel):
        """Sets the Cancel export on error option."""
        self._cancel_on_error = cancel
        if not self._active:
            return
        # This does not trigger the stateChanged signal.
        self._properties_ui.cancel_on_error_check_box.setCheckState(Qt.Checked if cancel else Qt.Unchecked)

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
        d["cancel_on_error"] = self._cancel_on_error
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

    def notify_destination(self, source_item):
        """See base class."""
        if source_item.item_type() == "Data Store":
            self._logger.msg.emit(
                f"Link established. Data Store <b>{source_item.name}</b> will be "
                f"exported to a .gdx file by <b>{self.name}</b> when executing."
            )
        else:
            super().notify_destination(source_item)

    @Slot(set, "QVariant")
    def _update_settings_after_db_commit(self, committed_db_maps, cookie):
        """Refreshes export settings for databases after data has been committed to them."""
        for db_map in committed_db_maps:
            url = str(db_map.db_url)
            pack = self._settings_packs.get(url)
            if pack is not None:
                latest_stamp = _latest_database_commit_time_stamp(url)
                if latest_stamp != pack.last_database_commit:
                    self._start_worker(url, update_settings=True)

    @Slot(object)
    def _update_settings_after_db_creation(self, url):
        """Triggers settings override."""
        url_string = url.drivername + ":///" + url.database
        if url_string in self._settings_packs:
            self._start_worker(url_string)

    @staticmethod
    def default_name_prefix():
        """See base class."""
        return "Exporter"

    def resources_for_direct_successors(self):
        """See base class."""
        files = [pack.output_file_name for pack in self._settings_packs.values()]
        paths = [os.path.join(self.data_dir, file_name) for file_name in files]
        resources = [ProjectItemResource(self, "file", url=pathlib.Path(path).as_uri()) for path in paths]
        return resources

    def tear_down(self):
        """See base class."""
        self._project.db_mngr.session_committed.disconnect(self._update_settings_after_db_commit)
        self._project.db_mngr.database_created.disconnect(self._update_settings_after_db_creation)
        for worker in self._workers.values():
            worker.thread.quit()
        for worker in self._workers.values():
            worker.thread.wait()
            worker.deleteLater()
        self._workers.clear()


def _normalize_url(url):
    """
    Normalized url's path separators to their OS specific characters.

    This function is needed during the transition period from no-version to version 1 project files.
    It should be removed once we are using version 1 files.
    """
    return "sqlite:///" + url[10:].replace("/", os.sep)


def _latest_database_commit_time_stamp(url):
    """Returns the latest commit timestamp from database at given URL or None."""
    try:
        database_map = DatabaseMapping(url)
    except SpineDBAPIError:
        return None
    else:
        time_stamp = latest_database_commit_time_stamp(database_map)
        database_map.connection.close()
        return time_stamp
