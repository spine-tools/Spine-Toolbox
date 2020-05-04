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
Unit tests for ExporterExecutable.

:author: A. Soininen (VTT)
:date:   6.4.2020
"""

from pathlib import Path
from tempfile import gettempdir, TemporaryDirectory
import unittest
from unittest import mock
from gdx2py import GdxFile
from spine_engine import ExecutionDirection
from spinedb_api import create_new_spine_database, DiffDatabaseMapping, import_functions
from spinetoolbox.project_item import ProjectItemResource
from spinetoolbox.project_items.exporter.exporter import SettingsPack
from spinetoolbox.project_items.exporter.exporter_executable import ExporterExecutable
from spinetoolbox.project_items.exporter.settings_state import SettingsState
from spinetoolbox.spine_io import gdx_utils
from spinetoolbox.spine_io.exporters import gdx


class TestExporterExecutable(unittest.TestCase):
    def test_item_type(self):
        self.assertEqual(ExporterExecutable.item_type(), "Exporter")

    def test_execute_backward(self):
        executable = ExporterExecutable("name", {}, "", "", mock.MagicMock())
        self.assertTrue(executable.execute([], ExecutionDirection.BACKWARD))

    @unittest.skipIf(gdx_utils.find_gams_directory() is None, "No working GAMS installation found.")
    def test_execute_forward_no_output(self):
        executable = ExporterExecutable("name", {}, "", "", mock.MagicMock())
        self.assertTrue(executable.execute([], ExecutionDirection.FORWARD))

    @unittest.skipIf(gdx_utils.find_gams_directory() is None, "No working GAMS installation found.")
    def test_execute_forward_exports_simple_database_to_gdx(self):
        with TemporaryDirectory() as tmp_dir_name:
            database_path = Path(tmp_dir_name).joinpath("test_execute_forward.sqlite")
            database_url = 'sqlite:///' + str(database_path)
            create_new_spine_database(database_url)
            database_map = DiffDatabaseMapping(database_url)
            import_functions.import_object_classes(database_map, ["domain"])
            import_functions.import_objects(database_map, [("domain", "record")])
            settings_pack = SettingsPack("output.gdx")
            settings_pack.settings = gdx.make_set_settings(database_map)
            settings_pack.indexing_settings = gdx.make_indexing_settings(database_map, logger=mock.MagicMock())
            settings_pack.state = SettingsState.OK
            database_map.commit_session("Add an entity class and an entity for unit tests.")
            database_map.connection.close()
            packs = {database_url: settings_pack}
            executable = ExporterExecutable("name", packs, tmp_dir_name, "", mock.MagicMock())
            resources = [ProjectItemResource(None, "database", database_url)]
            self.assertTrue(executable.execute(resources, ExecutionDirection.FORWARD))
            self.assertTrue(Path(tmp_dir_name, "output.gdx").exists())
            gams_directory = gdx.find_gams_directory()
            with GdxFile(str(Path(tmp_dir_name, "output.gdx")), "r", gams_directory) as gdx_file:
                self.assertEqual(len(gdx_file), 1)
                expected_symbol_names = ["domain"]
                for gams_symbol, expected_name in zip(gdx_file.keys(), expected_symbol_names):
                    self.assertEqual(gams_symbol, expected_name)
                gams_set = gdx_file["domain"]
                self.assertEqual(len(gams_set), 1)
                expected_records = ["record"]
                for gams_record, expected_name in zip(gams_set, expected_records):
                    self.assertEqual(gams_record, expected_name)

    def test_output_resources_backward(self):
        executable = ExporterExecutable("name", {}, "", "", mock.MagicMock())
        self.assertEqual(executable.output_resources(ExecutionDirection.BACKWARD), [])

    def test_output_resources_forward(self):
        data_dir = gettempdir()
        settings_pack1 = SettingsPack("output.gdx")
        settings_pack2 = SettingsPack("exported.gdx")
        packs = {"sqlite:///first_database.sqlite": settings_pack1, "sqlite:///second_database.sqlite": settings_pack2}
        executable = ExporterExecutable("name", packs, data_dir, "", mock.MagicMock())
        resources = executable.output_resources(ExecutionDirection.FORWARD)
        self.assertEqual(len(resources), 2)


if __name__ == '__main__':
    unittest.main()
