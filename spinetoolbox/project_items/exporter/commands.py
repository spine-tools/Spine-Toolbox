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


class UpdateExporterOutFileNameCommand(SpineToolboxCommand):
    def __init__(self, exporter, file_name, database_path):
        """Command to update Exporter output file name.

        Args:
            exporter (Exporter): the Exporter
            export_list_item (ExportListItem): the widget that holds the name
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


class UpdateExporterSettingsCommand(SpineToolboxCommand):
    def __init__(self, exporter, settings, indexing_settings, merging_settings, database_path):
        """Command to update Exporter settings.

        Args:
            exporter (Exporter): the Exporter
            settings (SetSettings): gdx settings
            indexing_settings (dict): parameter indexing settings
            merging_settings (dict): parameter merging settings
            database_path (str): the db path to update settings for
        """
        super().__init__()
        self.exporter = exporter
        self.database_path = database_path
        self.redo_settings_tuple = (settings, indexing_settings, merging_settings)
        p = exporter.settings_pack(database_path)
        self.undo_settings_tuple = (p.settings, p.indexing_settings, p.merging_settings)
        self.setText(f"change settings of {exporter.name}")

    def redo(self):
        self.exporter.undo_or_redo_settings(*self.redo_settings_tuple, self.database_path)

    def undo(self):
        self.exporter.undo_or_redo_settings(*self.undo_settings_tuple, self.database_path)
