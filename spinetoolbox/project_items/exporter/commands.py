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
Undo/redo commands for the Exporter project item.

:authors: A. Soininen (VTT)
:date:   30.4.2020
"""
from spinetoolbox.project_commands import SpineToolboxCommand


class UpdateExporterOutFileName(SpineToolboxCommand):
    def __init__(self, exporter, file_name, database_path):
        """Command to update Exporter output file name.

        Args:
            exporter (Exporter): the Exporter
            file_name (str): the output filename
            database_path (str): the associated db path
        """
        super().__init__()
        self.exporter = exporter
        self.redo_file_name = file_name
        self.undo_file_name = self.exporter._settings_packs[database_path].output_file_name
        self.database_path = database_path
        self.setText(f"change output file in {exporter.name}")

    def redo(self):
        self.exporter.undo_redo_out_file_name(self.redo_file_name, self.database_path)

    def undo(self):
        self.exporter.undo_redo_out_file_name(self.undo_file_name, self.database_path)


class UpdateScenario(SpineToolboxCommand):
    def __init__(self, exporter, scenario, database_url):
        """
        Args:
            exporter (Exporter): the Exporter
            scenario (str, optional): new scenario name
            database_url (str): database URL
        """
        super().__init__()
        self._exporter = exporter
        self._scenario = scenario
        self._previous_scenario = exporter.settings_pack(database_url).scenario
        self._url = database_url
        self.setText(f"change {exporter.name}'s scenario")

    def redo(self):
        self._exporter.set_scenario(self._scenario, self._url)

    def undo(self):
        self._exporter.set_scenario(self._previous_scenario, self._url)


class UpdateExporterSettings(SpineToolboxCommand):
    def __init__(
        self, exporter, settings, indexing_settings, merging_settings, none_fallback, none_export, database_path
    ):
        """Command to update Exporter settings.

        Args:
            exporter (Exporter): the Exporter
            settings (SetSettings): gdx settings
            indexing_settings (dict): parameter indexing settings
            merging_settings (dict): parameter merging settings
            none_fallback (NoneFallback): fallback option on None values
            none_export (NoneExport): how to handle Nones while exporting
            database_path (str): the db path to update settings for
        """
        super().__init__()
        self._exporter = exporter
        self._database_path = database_path
        self._redo_settings_tuple = (settings, indexing_settings, merging_settings, none_fallback, none_export)
        p = exporter.settings_pack(database_path)
        self._undo_settings_tuple = (p.settings, p.indexing_settings, p.merging_settings)
        self.setText(f"change settings of {exporter.name}")

    def redo(self):
        self._exporter.undo_or_redo_settings(*self._redo_settings_tuple, self._database_path)

    def undo(self):
        self._exporter.undo_or_redo_settings(*self._undo_settings_tuple, self._database_path)
