######################################################################################################################
# Copyright (C) 2017 - 2019 Spine project consortium
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""
Unit tests for spine_items.spine_io.exporters.gdx module.

:author: A. Soininen (VTT)
:date:   18.9.2019
"""
import math
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from gdx2py import GdxFile
from PySide2.QtWidgets import QApplication
from spinedb_api import import_functions as dbmanip
from spinedb_api import (
    create_new_spine_database,
    DiffDatabaseMapping,
    from_database,
    Map,
    TimePattern,
    TimeSeriesFixedResolution,
)
from spine_items.spine_io import gdx_utils
from spine_items.spine_io.exporters import gdx


class TestGdx(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Some @busy_effect decorators force the instantiation of QApplication.
        if not QApplication.instance():
            QApplication()

    def test_GdxExportException(self):
        exception = gdx.GdxExportException("message")
        self.assertEqual(exception.message, "message")
        self.assertEqual(str(exception), "message")

    def test_Set_construction(self):
        regular_set = gdx.Set("name", "description", ["domain1", "domain2"])
        self.assertEqual(regular_set.description, "description")
        self.assertEqual(regular_set.domain_names, ["domain1", "domain2"])
        self.assertEqual(regular_set.dimensions, 2)
        self.assertEqual(regular_set.name, "name")
        self.assertEqual(regular_set.records, [])

    def test_Set_from_dict(self):
        original_set = gdx.Set("set name", "description", ["index1", "index2"])
        original_set.records += [gdx.Record(("key1", "key2")), gdx.Record(("key1", "key3"))]
        set_dict = original_set.to_dict()
        restored_set = gdx.Set.from_dict(set_dict)
        self.assertEqual(restored_set.name, "set name")
        self.assertEqual(restored_set.domain_names, ["index1", "index2"])
        self.assertEqual(restored_set.description, "description")
        self.assertEqual(len(restored_set.records), 2)
        self.assertEqual(restored_set.records[0].keys, ("key1", "key2"))
        self.assertEqual(restored_set.records[1].keys, ("key1", "key3"))

    def test_Record_construction(self):
        record = gdx.Record(("key1", "key2"))
        self.assertEqual(record.keys, ("key1", "key2"))
        self.assertEqual(record.name, "key1,key2")

    def test_Record_from_dict(self):
        original = gdx.Record(("keyA", "keyB", "keyC"))
        record_dict = original.to_dict()
        restored = gdx.Record.from_dict(record_dict)
        self.assertEqual(restored.keys, ("keyA", "keyB", "keyC"))

    def test_Parameter_construction(self):
        parameter = gdx.Parameter(["set name1", "set name2"], [("key1", "key2")], [5.5])
        self.assertEqual(parameter.domain_names, ["set name1", "set name2"])
        self.assertEqual(parameter.data, {("key1", "key2"): 5.5})
        self.assertEqual(list(parameter.indexes), [("key1", "key2")])
        self.assertEqual(list(parameter.values), [5.5])

    def test_Parameter_slurp(self):
        parameter = gdx.Parameter(["domain"], [("label1",)], [4.2])
        slurpable = gdx.Parameter(["domain"], [("label2",)], [3.3])
        parameter.slurp(slurpable)
        self.assertEqual(parameter.domain_names, ["domain"])
        self.assertEqual(list(parameter.indexes), [("label1",), ("label2",)])
        self.assertEqual(list(parameter.values), [4.2, 3.3])

    def test_parameter_is_scalar(self):
        parameter = gdx.Parameter(["domain"], [("label",)], [2.0])
        self.assertTrue(parameter.is_scalar())
        parameter = gdx.Parameter(
            ["domain"], [("label",)], [TimeSeriesFixedResolution("2019-12-05T01:01:00", "1h", [4.2, 5.3], False, False)]
        )
        self.assertFalse(parameter.is_scalar())

    def test_parameter_is_indexed(self):
        parameter = gdx.Parameter(["domain"], [("label",)], [2.0])
        self.assertFalse(parameter.is_indexed())
        parameter = gdx.Parameter(
            ["domain"], [("label",)], [TimeSeriesFixedResolution("2019-12-05T01:01:00", "1h", [4.2, 5.3], False, False)]
        )
        self.assertTrue(parameter.is_indexed())

    def test_Parameter_expand_indexes(self):
        time_series1 = TimeSeriesFixedResolution("2019-12-05T01:01:00", "1h", [4.2, 5.3], False, False)
        time_series2 = TimeSeriesFixedResolution("2020-12-05T01:01:00", "1h", [-4.2, -5.3], False, False)
        parameter = gdx.Parameter(
            ["domain1", "domain2"], [("index1", "index2"), ("index1", "index3")], [time_series1, time_series2]
        )
        setting = gdx.IndexingSetting(parameter, "unknown_set")
        setting.indexing_domain_name = "stamp domain"
        setting.index_position = 1
        setting.picking = gdx.FixedPicking([True, True])
        domain1 = gdx.Set("domain1")
        domain1.records = [gdx.Record(("index1",))]
        domain2 = gdx.Set("domain2")
        domain2.records = [gdx.Record(("index2",)), gdx.Record(("index3",))]
        stamp_domain = gdx.Set("stamp domain")
        stamp_domain.records = [gdx.Record(("stamp1",)), gdx.Record(("stamp2",))]
        domains = {"domain1": domain1, "domain2": domain2, "stamp domain": stamp_domain}
        parameter.expand_indexes(setting, domains)
        self.assertEqual(parameter.domain_names, ["domain1", "stamp domain", "domain2"])
        self.assertEqual(
            parameter.data,
            {
                ("index1", "stamp1", "index2"): 4.2,
                ("index1", "stamp2", "index2"): 5.3,
                ("index1", "stamp1", "index3"): -4.2,
                ("index1", "stamp2", "index3"): -5.3,
            },
        )

    def test_Parameter_equality(self):
        parameter1 = gdx.Parameter(["domain"], [("label",)], [2.0])
        parameter2 = gdx.Parameter(["domain"], [("label",)], [2.0])
        self.assertEqual(parameter1, parameter2)

    def test_SetSettings_construction(self):
        domain_names, set_names, records, settings = self._make_settings()
        self.assertEqual(settings.domain_names, domain_names)
        for name in domain_names:
            self.assertEqual(settings.metadata(name), gdx.SetMetadata())
            self.assertIsNotNone(settings.domain_tiers.get(name))
            self.assertEqual(settings.records(name).records, records[name].records)
        self.assertEqual(settings.set_names, set_names)
        for name in set_names:
            self.assertEqual(settings.metadata(name), gdx.SetMetadata())
            self.assertIsNotNone(settings.set_tiers.get(name))
            self.assertEqual(settings.records(name).records, records[name].records)
        self.assertEqual(settings.global_parameters_domain_name, "")

    def test_SetSettings_serialization_to_dictionary(self):
        domain_metadatas = [
            gdx.SetMetadata(gdx.ExportFlag.EXPORTABLE, gdx.Origin.INDEXING),
            gdx.SetMetadata(gdx.ExportFlag.NON_EXPORTABLE),
        ]
        set_metadatas = [
            gdx.SetMetadata(gdx.ExportFlag.NON_EXPORTABLE),
            gdx.SetMetadata(gdx.ExportFlag.EXPORTABLE, gdx.Origin.MERGING),
            gdx.SetMetadata(gdx.ExportFlag.NON_EXPORTABLE),
        ]
        global_domain_name = 'global parameter domain'
        domain_names, set_names, _, settings = self._make_settings(domain_metadatas, set_metadatas, global_domain_name)
        settings_as_dict = settings.to_dict()
        recovered = gdx.SetSettings.from_dict(settings_as_dict)
        self.assertEqual(recovered.domain_names, settings.domain_names)
        self.assertEqual(recovered.domain_tiers, settings.domain_tiers)
        self.assertEqual(recovered.set_names, settings.set_names)
        for name in domain_names | set_names:
            self.assertEqual(recovered.metadata(name), settings.metadata(name))
        self.assertEqual(recovered.global_parameters_domain_name, settings.global_parameters_domain_name)

    @staticmethod
    def _make_database_map(dir_name, file_name):
        """Creates a Spine sqlite database in dir_name/file_name."""
        database_path = Path(dir_name).joinpath(file_name)
        database_url = 'sqlite:///' + str(database_path)
        create_new_spine_database(database_url)
        return DiffDatabaseMapping(database_url)

    def test_object_classes_to_domains(self):
        with TemporaryDirectory() as tmp_dir_name:
            database_map = self._make_database_map(tmp_dir_name, "test_object_classes_to_domains.sqlite")
            dbmanip.import_object_classes(database_map, ["domain"])
            dbmanip.import_objects(database_map, [("domain", "record")])
            domains_with_ids = gdx.object_classes_to_domains(database_map, {"domain"})
            database_map.connection.close()
        domains = list(domains_with_ids.values())
        self.assertEqual(len(domains), 1)
        domain = domains[0]
        self.assertEqual(domain.name, "domain")
        self.assertEqual(domain.description, "")
        records = domain.records
        self.assertEqual(len(records), 1)
        record = records[0]
        self.assertEqual(record.keys, ("record",))

    def test_object_classes_to_domains_filters_domains_not_on_the_list(self):
        with TemporaryDirectory() as tmp_dir_name:
            database_map = self._make_database_map(
                tmp_dir_name, "test_object_classes_to_domains_filters_domains_not_on_the_list.sqlite"
            )
            dbmanip.import_object_classes(database_map, ["domain", "ignored"])
            dbmanip.import_objects(database_map, [("domain", "record"), ("ignored", "ignored_record")])
            domains_with_ids = gdx.object_classes_to_domains(database_map, {"domain"})
            database_map.connection.close()
        domains = list(domains_with_ids.values())
        self.assertEqual(len(domains), 1)
        domain = domains[0]
        self.assertEqual(domain.name, "domain")
        self.assertEqual(domain.description, "")
        records = domain.records
        self.assertEqual(len(records), 1)
        record = records[0]
        self.assertEqual(record.keys, ("record",))

    def test_object_parameters(self):
        with TemporaryDirectory() as tmp_dir_name:
            database_map = self._make_database_map(tmp_dir_name, "test_object_parameters.sqlite")
            dbmanip.import_object_classes(database_map, ["domain"])
            dbmanip.import_objects(database_map, [("domain", "record")])
            dbmanip.import_object_parameters(database_map, [("domain", "parameter", 3.14)])
            dbmanip.import_object_parameter_values(database_map, [("domain", "record", "parameter", 2.3)])
            domains_with_ids = gdx.object_classes_to_domains(database_map, {"domain"})
            parameters = gdx.object_parameters(database_map, domains_with_ids, gdx.NoneFallback.USE_IT, None)
            database_map.connection.close()
        self.assertEqual(parameters, {"parameter": gdx.Parameter(["domain"], [("record",)], [2.3])})

    def test_object_parameters_replaces_nones_by_default_values(self):
        with TemporaryDirectory() as tmp_dir_name:
            database_map = self._make_database_map(
                tmp_dir_name, "test_object_parameters_replaces_nones_by_default_values.sqlite"
            )
            dbmanip.import_object_classes(database_map, ["domain"])
            dbmanip.import_objects(database_map, [("domain", "record")])
            dbmanip.import_object_parameters(database_map, [("domain", "parameter", 3.14)])
            dbmanip.import_object_parameter_values(database_map, [("domain", "record", "parameter", None)])
            domains_with_ids = gdx.object_classes_to_domains(database_map, {"domain"})
            parameters = gdx.object_parameters(database_map, domains_with_ids, gdx.NoneFallback.USE_DEFAULT_VALUE, None)
            database_map.connection.close()
        self.assertEqual(parameters, {"parameter": gdx.Parameter(["domain"], [("record",)], [3.14])})

    def test_relationship_classes_to_sets(self):
        with TemporaryDirectory() as tmp_dir_name:
            database_map = self._make_database_map(tmp_dir_name, "test_relationship_classes_to_sets.sqlite")
            dbmanip.import_object_classes(database_map, ["domain"])
            dbmanip.import_objects(database_map, [("domain", "record")])
            dbmanip.import_relationship_classes(database_map, [("set", ["domain"])])
            dbmanip.import_relationships(database_map, [("set", ["record"])])
            sets_with_ids = gdx.relationship_classes_to_sets(database_map, {"domain"}, {"set"})
            database_map.connection.close()
        sets = list(sets_with_ids.values())
        self.assertEqual(len(sets), 1)
        set_item = sets[0]
        self.assertEqual(set_item.name, "set")
        self.assertEqual(set_item.domain_names, ["domain"])
        self.assertEqual(set_item.dimensions, 1)
        self.assertEqual(len(set_item.records), 1)
        record = set_item.records[0]
        self.assertEqual(record.keys, ("record",))

    def test_relationship_classes_to_sets_filters_sets_not_on_the_list(self):
        with TemporaryDirectory() as tmp_dir_name:
            database_map = self._make_database_map(
                tmp_dir_name, "test_relationship_classes_to_sets_filters_sets_not_on_the_list.sqlite"
            )
            dbmanip.import_object_classes(database_map, ["domain"])
            dbmanip.import_objects(database_map, [("domain", "record")])
            dbmanip.import_relationship_classes(database_map, [("set", ["domain"]), ("ignored", ["domain"])])
            dbmanip.import_relationships(database_map, [("set", ["record"]), ("ignored", ["record"])])
            sets_with_ids = gdx.relationship_classes_to_sets(database_map, {"domain"}, {"set"})
            database_map.connection.close()
        sets = list(sets_with_ids.values())
        self.assertEqual(len(sets), 1)
        set_item = sets[0]
        self.assertEqual(set_item.name, "set")
        self.assertEqual(set_item.domain_names, ["domain"])
        self.assertEqual(set_item.dimensions, 1)
        self.assertEqual(len(set_item.records), 1)
        record = set_item.records[0]
        self.assertEqual(record.keys, ("record",))

    def test_relationship_classes_to_sets_filters_sets_without_indexing_domains(self):
        with TemporaryDirectory() as tmp_dir_name:
            database_map = self._make_database_map(
                tmp_dir_name, "test_relationship_classes_to_sets_filters_sets_without_indexing_domains.sqlite"
            )
            dbmanip.import_object_classes(database_map, ["domain"])
            dbmanip.import_objects(database_map, [("domain", "record")])
            dbmanip.import_relationship_classes(database_map, [("set", ["domain"])])
            dbmanip.import_relationships(database_map, [("set", ["record"])])
            sets_with_ids = gdx.relationship_classes_to_sets(database_map, set(), {"set"})
            database_map.connection.close()
        self.assertFalse(bool(sets_with_ids))

    def test_relationship_parameters(self):
        with TemporaryDirectory() as tmp_dir_name:
            database_map = self._make_database_map(tmp_dir_name, "test_relationship_parameters.sqlite")
            dbmanip.import_object_classes(database_map, ["domain"])
            dbmanip.import_objects(database_map, [("domain", "record")])
            dbmanip.import_relationship_classes(database_map, [("set", ["domain"])])
            dbmanip.import_relationships(database_map, [("set", ["record"])])
            dbmanip.import_relationship_parameters(database_map, [("set", "parameter", 3.14)])
            dbmanip.import_relationship_parameter_values(database_map, [["set", ["record"], "parameter", 2.3]])
            sets_with_ids = gdx.relationship_classes_to_sets(database_map, {"domain"}, {"set"})
            parameters = gdx.relationship_parameters(database_map, sets_with_ids, gdx.NoneFallback.USE_IT, None)
            database_map.connection.close()
        self.assertEqual(parameters, {"parameter": gdx.Parameter(["domain"], [("record",)], [2.3])})

    def test_relationship_parameters_replaces_nones_by_default_values(self):
        with TemporaryDirectory() as tmp_dir_name:
            database_map = self._make_database_map(
                tmp_dir_name, "test_relationship_parameters_replaces_nones_by_default_values.sqlite"
            )
            dbmanip.import_object_classes(database_map, ["domain"])
            dbmanip.import_objects(database_map, [("domain", "record")])
            dbmanip.import_relationship_classes(database_map, [("set", ["domain"])])
            dbmanip.import_relationships(database_map, [("set", ["record"])])
            dbmanip.import_relationship_parameters(database_map, [("set", "parameter", 3.14)])
            dbmanip.import_relationship_parameter_values(database_map, [["set", ["record"], "parameter", None]])
            sets_with_ids = gdx.relationship_classes_to_sets(database_map, {"domain"}, {"set"})
            parameters = gdx.relationship_parameters(
                database_map, sets_with_ids, gdx.NoneFallback.USE_DEFAULT_VALUE, None
            )
            database_map.connection.close()
        self.assertEqual(parameters, {"parameter": gdx.Parameter(["domain"], [("record",)], [3.14])})

    def test_domain_names_and_records(self):
        with TemporaryDirectory() as tmp_dir_name:
            database_map = self._make_database_map(tmp_dir_name, "test_domain_names_and_records.sqlite")
            dbmanip.import_object_classes(database_map, ["domain"])
            dbmanip.import_objects(database_map, [("domain", "recordA"), ("domain", "recordB")])
            domain_names, domain_records = gdx.domain_names_and_records(database_map)
            database_map.connection.close()
        self.assertEqual(domain_names, {"domain"})
        self.assertEqual(domain_records, {"domain": gdx.LiteralRecords([("recordA",), ("recordB",)])})

    def test_set_names_and_records(self):
        with TemporaryDirectory() as tmp_dir_name:
            database_map = self._make_database_map(tmp_dir_name, "test_set_names_and_records.sqlite")
            dbmanip.import_object_classes(database_map, ["domain"])
            dbmanip.import_objects(database_map, [("domain", "record")])
            dbmanip.import_relationship_classes(database_map, [("set", ["domain"])])
            dbmanip.import_relationships(database_map, [("set", ["record"])])
            set_names, set_records = gdx.set_names_and_records(database_map)
            database_map.connection.close()
        self.assertEqual(set_names, {"set"})
        self.assertEqual(set_records, {"set": gdx.LiteralRecords([("record",)])})

    @unittest.skipIf(gdx_utils.find_gams_directory() is None, "No working GAMS installation found.")
    def test_sets_to_gams_with_domain_sets(self):
        domain = gdx.Set("mock_object_class_name")
        record = gdx.Record(("mock_object_name",))
        domain.records.append(record)
        gams_directory = gdx_utils.find_gams_directory()
        with TemporaryDirectory() as temp_directory:
            path_to_gdx = Path(temp_directory).joinpath("test_domains_to_gams.gdx")
            with GdxFile(path_to_gdx, 'w', gams_directory) as gdx_file:
                gdx.sets_to_gams(gdx_file, [domain])
            with GdxFile(path_to_gdx, 'r', gams_directory) as gdx_file:
                self.assertEqual(len(gdx_file), 1)
                gams_set = gdx_file["mock_object_class_name"]
                self.assertEqual(len(gams_set.elements), 1)
                self.assertEqual(gams_set.elements[0], "mock_object_name")

    @unittest.skipIf(gdx_utils.find_gams_directory() is None, "No working GAMS installation found.")
    def test_sets_to_gams(self):
        domain = gdx.Set("mock_object_class_name")
        record = gdx.Record(("mock_object_name",))
        domain.records.append(record)
        set_item = gdx.Set("mock_relationship_class_name", domain_names=["mock_object_class_name"])
        record = gdx.Record(("mock_object_name",))
        set_item.records.append(record)
        gams_directory = gdx_utils.find_gams_directory()
        with TemporaryDirectory() as temp_directory:
            path_to_gdx = Path(temp_directory).joinpath("test_sets_to_gams.gdx")
            with GdxFile(path_to_gdx, 'w', gams_directory) as gdx_file:
                gdx.sets_to_gams(gdx_file, [domain])
                gdx.sets_to_gams(gdx_file, [set_item])
            with GdxFile(path_to_gdx, 'r', gams_directory) as gdx_file:
                self.assertEqual(len(gdx_file), 2)
                gams_set = gdx_file["mock_object_class_name"]
                self.assertEqual(len(gams_set.elements), 1)
                self.assertEqual(gams_set.elements[0], "mock_object_name")
                gams_set = gdx_file["mock_relationship_class_name"]
                self.assertEqual(len(gams_set.elements), 1)
                self.assertEqual(gams_set.elements[0], "mock_object_name")

    @unittest.skipIf(gdx_utils.find_gams_directory() is None, "No working GAMS installation found.")
    def test_sets_to_gams_omits_a_set(self):
        domain = gdx.Set("domain_for_gdx")
        domain.records.append(gdx.Record(("key",)))
        omitted = gdx.Set("omitted_domain")
        omitted.records.append(gdx.Record(("omitted_key",)))
        gams_directory = gdx_utils.find_gams_directory()
        with TemporaryDirectory() as temp_directory:
            path_to_gdx = Path(temp_directory).joinpath("test_sets_to_gams_omits_a_set.gdx")
            with GdxFile(path_to_gdx, 'w', gams_directory) as gdx_file:
                gdx.sets_to_gams(gdx_file, [domain, omitted], omitted)
            with GdxFile(path_to_gdx, 'r', gams_directory) as gdx_file:
                self.assertEqual(len(gdx_file), 1)
                gams_set = gdx_file["domain_for_gdx"]
                self.assertEqual(len(gams_set.elements), 1)
                self.assertEqual(gams_set.elements[0], "key")

    @unittest.skipIf(gdx_utils.find_gams_directory() is None, "No working GAMS installation found.")
    def test_sets_to_gams_raises_with_duplicate_set_names(self):
        domain = gdx.Set("domain")
        domain.records.append(gdx.Record(("a_key",)))
        duplicate = gdx.Set("DOMAIN")
        duplicate.records.append(gdx.Record(("b_key",)))
        gams_directory = gdx_utils.find_gams_directory()
        with TemporaryDirectory() as temp_directory:
            path_to_gdx = Path(temp_directory).joinpath("test_sets_to_gams_raises_with_duplicate_set_names.gdx")
            with GdxFile(path_to_gdx, 'w', gams_directory) as gdx_file:
                self.assertRaises(gdx.GdxExportException, gdx.sets_to_gams, gdx_file, [domain, duplicate])

    @unittest.skipIf(gdx_utils.find_gams_directory() is None, "No working GAMS installation found.")
    def test_parameters_to_gams(self):
        parameters = {"scalar": gdx.Parameter(["domain"], [("key",)], [2.3])}
        gams_directory = gdx_utils.find_gams_directory()
        with TemporaryDirectory() as temp_directory:
            path_to_gdx = Path(temp_directory).joinpath("test_parameters_to_gams.gdx")
            with GdxFile(path_to_gdx, 'w', gams_directory) as gdx_file:
                gdx.parameters_to_gams(gdx_file, parameters, gdx.NoneExport.DO_NOT_EXPORT)
            with GdxFile(path_to_gdx, 'r', gams_directory) as gdx_file:
                self.assertEqual(len(gdx_file), 1)
                gams_parameter = gdx_file["scalar"]
                self.assertEqual(len(gams_parameter.keys()), 1)
                for key, value in gams_parameter:  # pylint: disable=not-an-iterable
                    self.assertEqual(key, "key")
                    self.assertEqual(value, 2.3)

    @unittest.skipIf(gdx_utils.find_gams_directory() is None, "No working GAMS installation found.")
    def test_parameters_to_gams_replaces_none_by_nan(self):
        parameters = {"scalar": gdx.Parameter(["domain"], [("key",)], [None])}
        gams_directory = gdx_utils.find_gams_directory()
        with TemporaryDirectory() as temp_directory:
            path_to_gdx = Path(temp_directory).joinpath("test_parameters_to_gams_replaces_none_by_nan.gdx")
            with GdxFile(path_to_gdx, 'w', gams_directory) as gdx_file:
                gdx.parameters_to_gams(gdx_file, parameters, gdx.NoneExport.EXPORT_AS_NAN)
            with GdxFile(path_to_gdx, 'r', gams_directory) as gdx_file:
                self.assertEqual(len(gdx_file), 1)
                gams_parameter = gdx_file["scalar"]
                self.assertEqual(len(gams_parameter.keys()), 1)
                for key, value in gams_parameter:  # pylint: disable=not-an-iterable
                    self.assertEqual(key, "key")
                    self.assertTrue(math.isnan(value))

    @unittest.skipIf(gdx_utils.find_gams_directory() is None, "No working GAMS installation found.")
    def test_parameters_to_gams_raises_with_duplicate_parameter_names(self):
        parameters = {
            "scalar": gdx.Parameter(["domain"], [("key",)], [2.3]),
            "SCALAR": gdx.Parameter(["domain"], [("key",)], [23.0]),
        }
        gams_directory = gdx_utils.find_gams_directory()
        with TemporaryDirectory() as temp_directory:
            path_to_gdx = Path(temp_directory).joinpath(
                "test_parameters_to_gams_raises_with_duplicate_parameter_names.gdx"
            )
            with GdxFile(path_to_gdx, 'w', gams_directory) as gdx_file:
                self.assertRaises(
                    gdx.GdxExportException, gdx.parameters_to_gams, gdx_file, parameters, gdx.NoneExport.DO_NOT_EXPORT
                )

    @unittest.skipIf(gdx_utils.find_gams_directory() is None, "No working GAMS installation found.")
    def test_domain_parameters_to_gams_scalars(self):
        domain = gdx.Set("object_class_name")
        record = gdx.Record(("mock_object_name",))
        domain.records.append(record)
        parameters = {"mock_parameter_name": gdx.Parameter(["object_class_name"], [("mock_object_name",)], [2.3])}
        gams_directory = gdx_utils.find_gams_directory()
        with TemporaryDirectory() as temp_directory:
            path_to_gdx = Path(temp_directory).joinpath("test_domain_parameters_to_gams_scalars.gdx")
            with GdxFile(path_to_gdx, 'w', gams_directory) as gdx_file:
                gdx.domain_parameters_to_gams_scalars(gdx_file, parameters, "object_class_name")
            with GdxFile(path_to_gdx, 'r', gams_directory) as gdx_file:
                self.assertEqual(len(gdx_file), 1)
                gams_scalar = gdx_file["mock_parameter_name"]
                self.assertEqual(float(gams_scalar), 2.3)

    @unittest.skipIf(gdx_utils.find_gams_directory() is None, "No working GAMS installation found.")
    def test_domain_parameters_to_gams_scalars_raises_with_duplicate_scalar_names(self):
        domain = gdx.Set("domain")
        record = gdx.Record(("key",))
        domain.records.append(record)
        parameters = {
            "parameter": gdx.Parameter(["domain"], [("key",)], [2.3]),
            "PARAMETER": gdx.Parameter(["domain"], [("key",)], [23.0]),
        }
        gams_directory = gdx_utils.find_gams_directory()
        with TemporaryDirectory() as temp_directory:
            path_to_gdx = Path(temp_directory).joinpath(
                "test_domain_parameters_to_gams_scalars_raises_with_duplicate_scalar_names.gdx"
            )
            with GdxFile(path_to_gdx, 'w', gams_directory) as gdx_file:
                self.assertRaises(
                    gdx.GdxExportException, gdx.domain_parameters_to_gams_scalars, gdx_file, parameters, "domain"
                )

    def test_IndexingSetting_construction(self):
        time_series = TimeSeriesFixedResolution("2019-12-05T01:01:00", "1h", [4.2, 5.3], False, False)
        setting = gdx.IndexingSetting(gdx.Parameter(["domain"], [("keyA",)], [time_series]), "domain1")
        self.assertIsNone(setting.indexing_domain_name)
        self.assertIsNone(setting.picking)
        self.assertEqual(setting.index_position, 1)
        self.assertEqual(setting.set_name, "domain1")

    def test_IndexingSetting_append_parameter(self):
        time_series1 = TimeSeriesFixedResolution("2019-12-05T01:01:00", "1h", [4.2, 5.3], False, False)
        setting = gdx.IndexingSetting(gdx.Parameter(["domain"], [("keyA",)], [time_series1]), "domain")
        time_series2 = TimeSeriesFixedResolution("2019-12-05T01:01:00", "1h", [-4.2, -5.3], False, False)
        setting.append_parameter(gdx.Parameter(["domain"], [("keyB",)], [time_series2]))
        self.assertEqual(setting.parameter.domain_names, ["domain"])
        self.assertEqual(list(setting.parameter.indexes), [("keyA",), ("keyB",)])
        self.assertEqual(list(setting.parameter.values), [time_series1, time_series2])

    def test_LiteralRecords_construction(self):
        records = gdx.LiteralRecords([("A",), ("B",)])
        self.assertEqual(len(records), 2)
        self.assertEqual(records.records, [("A",), ("B",)])

    def test_LiteralRecords_shufflable(self):
        records = gdx.LiteralRecords([])
        self.assertTrue(records.is_shufflable())

    def test_LiteralRecords_update(self):
        records = gdx.LiteralRecords([("A",), ("B",), ("C",)])
        new_records = gdx.LiteralRecords([("E",), ("C",), ("B",), ("D",)])
        updated = gdx.LiteralRecords.update(records, new_records)
        self.assertEqual(updated.records, [("B",), ("C",), ("E",), ("D",)])

    def test_LiteralRecords_serialization(self):
        records = gdx.LiteralRecords([("A",), ("B",)])
        records_dict = records.to_dict()
        deserialized = gdx.LiteralRecords.from_dict(records_dict)
        self.assertEqual(records, deserialized)

    def test_GeneratedRecordsConstruction(self):
        records = gdx.GeneratedRecords("f'{i}'", 3)
        self.assertEqual(len(records), 3)
        self.assertEqual(records.records, [("1",), ("2",), ("3",)])
        self.assertEqual(records.expression, "f'{i}'")

    def test_GeneratedRecords_is_shufflable(self):
        records = gdx.GeneratedRecords("", 0)
        self.assertFalse(records.is_shufflable())

    def test_GeneratedRecords_serialization(self):
        records = gdx.GeneratedRecords("f'{i}'", 5)
        records_dict = records.to_dict()
        deserialized = gdx.GeneratedRecords.from_dict(records_dict)
        self.assertEqual(records, deserialized)

    def test_ExtractedRecords_construction(self):
        records = gdx.ExtractedRecords("parameter", [("A",), ("B",)])
        self.assertEqual(len(records), 2)
        self.assertEqual(records.records, [("A",), ("B",)])
        self.assertEqual(records.parameter_name, "parameter")

    def test_ExtractedRecords_extract(self):
        with TemporaryDirectory() as tmp_dir_name:
            database_map = self._make_database_map(
                tmp_dir_name, "test_to_gdx_file_sorts_domains_and_sets_and_records_correctly.sqlite"
            )
            dbmanip.import_object_classes(database_map, [("object_class")])
            dbmanip.import_object_parameters(database_map, [("object_class", "parameter")])
            dbmanip.import_objects(database_map, [("object_class", "object")])
            value = Map(["a", "b", "c"], [5.0, 5.0, 5.0])
            dbmanip.import_object_parameter_values(database_map, [("object_class", "object", "parameter", value)])
            database_map.commit_session("Add data.")
            records = gdx.ExtractedRecords.extract("parameter", database_map)
            self.assertEqual(records.parameter_name, "parameter")
            self.assertEqual(records.records, [("a",), ("b",), ("c",)])
            database_map.connection.close()

    def test_ExtractedRecords_is_shufflable(self):
        records = gdx.ExtractedRecords("", [])
        self.assertFalse(records.is_shufflable())

    def test_ExtractedRecords_update(self):
        records = gdx.ExtractedRecords("parameter", [("A",)])
        new_records = gdx.ExtractedRecords("gyrometer", [("B",)])
        updated = gdx.ExtractedRecords.update(records, new_records)
        self.assertEqual(updated.records, [("B",)])
        self.assertEqual(updated.parameter_name, "parameter")

    def test_ExtractedRecords_serialization(self):
        records = gdx.ExtractedRecords("parameter", [("A",), ("B",)])
        records_dict = records.to_dict()
        deserialized = gdx.ExtractedRecords.from_dict(records_dict)
        self.assertEqual(records, deserialized)

    def test_FixedPicking_construction(self):
        picking = gdx.FixedPicking([True, False])
        self.assertTrue(picking.pick(0))
        self.assertFalse(picking.pick(1))

    def test_FixedPicking_serialization(self):
        picking = gdx.FixedPicking([True, False])
        picking_dict = picking.to_dict()
        deserialized = gdx.FixedPicking.from_dict(picking_dict)
        self.assertEqual(picking, deserialized)

    def test_GeneratedPicking_constrction(self):
        picking = gdx.GeneratedPicking("i == 2")
        self.assertFalse(picking.pick(0))
        self.assertTrue(picking.pick(1))
        self.assertFalse(picking.pick(2))
        self.assertEqual(picking.expression, "i == 2")

    def test_GeneratePicking_serialization(self):
        picking = gdx.GeneratedPicking("i == 2")
        picking_dict = picking.to_dict()
        deserialized = gdx.GeneratedPicking.from_dict(picking_dict)
        self.assertEqual(picking.expression, deserialized.expression)

    def test_sort_sets(self):
        sets = [gdx.Set("set1"), gdx.Set("set2"), gdx.Set("set3")]
        tiers = {"set2": 0, "set1": 1, "set3": 2}
        sorted_sets = gdx.sort_sets(sets, tiers)
        names = [s.name for s in sorted_sets]
        self.assertEqual(names, ["set2", "set1", "set3"])

    def test_sort_records_in_place(self):
        domain1 = gdx.Set("d1")
        domain1.records += [gdx.Record(("rA",)), gdx.Record(("rB",))]
        domain2 = gdx.Set("d2")
        domain2.records += [gdx.Record(("rC",)), gdx.Record(("rD",))]
        set_settings = gdx.SetSettings(
            {"d1", "d2"},
            set(),
            {"d1": gdx.LiteralRecords([("rB",), ("rA",)]), "d2": gdx.LiteralRecords([("rD",), ("rC",)])},
        )
        gdx.sort_records_inplace([domain1, domain2], set_settings)
        self.assertEqual(domain1.records, [gdx.Record(("rB",)), gdx.Record(("rA",))])
        self.assertEqual(domain2.records, [gdx.Record(("rD",)), gdx.Record(("rC",))])

    def test_extract_domain(self):
        domains = [gdx.Set("domain1")]
        domains, extracted = gdx.extract_domain(domains, "domain1")
        self.assertFalse(domains)
        self.assertEqual(extracted.name, "domain1")

    @unittest.skipIf(gdx_utils.find_gams_directory() is None, "No working GAMS installation found.")
    def test_to_gdx_file_sorts_domains_and_sets_and_records_correctly(self):
        gams_directory = gdx_utils.find_gams_directory()
        with TemporaryDirectory() as tmp_dir_name:
            database_map = self._make_database_map(
                tmp_dir_name, "test_to_gdx_file_sorts_domains_and_sets_and_records_correctly.sqlite"
            )
            dbmanip.import_object_classes(database_map, ["domain1", "domain2"])
            dbmanip.import_objects(
                database_map, [("domain1", "record11"), ("domain1", "record12"), ("domain2", "record21")]
            )
            dbmanip.import_relationship_classes(database_map, [("set1", ["domain1"]), ("set2", ["domain1", "domain2"])])
            dbmanip.import_relationships(
                database_map,
                [
                    ("set1", ["record12"]),
                    ("set1", ["record11"]),
                    ("set2", ["record12", "record21"]),
                    ("set2", ["record11", "record21"]),
                ],
            )
            domain_names = {"domain1", "domain2"}
            domain_tiers = {"domain1": 1, "domain2": 0}
            set_names = {"set1", "set2"}
            set_tiers = {"set1": 1, "set2": 0}
            sorted_records = {
                "domain1": gdx.LiteralRecords([("record12",), ("record11",)]),
                "domain2": gdx.LiteralRecords([("record21",)]),
                "set1": gdx.LiteralRecords([("record12",), ("record11",)]),
                "set2": gdx.LiteralRecords([("record12", "record21"), ("record11", "record21")]),
            }
            settings = gdx.SetSettings(
                domain_names, set_names, sorted_records, domain_tiers=domain_tiers, set_tiers=set_tiers
            )
            path_to_gdx = Path(tmp_dir_name).joinpath(
                "test_to_gdx_file_sorts_domains_and_sets_and_records_correctly.gdx"
            )
            gdx.to_gdx_file(
                database_map,
                path_to_gdx,
                settings,
                {},
                {},
                gdx.NoneFallback.USE_IT,
                gdx.NoneExport.DO_NOT_EXPORT,
                gams_directory,
            )
            database_map.connection.close()
            with GdxFile(path_to_gdx, "r", gams_directory) as gdx_file:
                self.assertEqual(len(gdx_file), 4)
                expected_symbol_names = ["domain2", "domain1", "set2", "set1"]
                for gams_symbol, expected_name in zip(gdx_file.keys(), expected_symbol_names):
                    self.assertEqual(gams_symbol, expected_name)
                gams_set = gdx_file["domain1"]
                self.assertEqual(len(gams_set), 2)
                expected_records = ["record12", "record11"]
                for gams_record, expected_name in zip(gams_set, expected_records):
                    self.assertEqual(gams_record, expected_name)
                gams_set = gdx_file["domain2"]
                self.assertEqual(len(gams_set), 1)
                self.assertEqual(gams_set.elements[0], "record21")
                gams_set = gdx_file["set1"]
                self.assertEqual(len(gams_set), 2)
                expected_records = ["record12", "record11"]
                for gams_record, expected_name in zip(gams_set, expected_records):
                    self.assertEqual(gams_record, expected_name)
                gams_set = gdx_file["set2"]
                self.assertEqual(len(gams_set), 2)
                expected_records = [("record12", "record21"), ("record11", "record21")]
                for gams_record, expected_name in zip(gams_set, expected_records):
                    self.assertEqual(gams_record, expected_name)

    @unittest.skipIf(gdx_utils.find_gams_directory() is None, "No working GAMS installation found.")
    def test_to_gdx_file_exports_global_parameters_only_not_the_corresponding_domain(self):
        gams_directory = gdx_utils.find_gams_directory()
        with TemporaryDirectory() as tmp_dir_name:
            database_map = self._make_database_map(
                tmp_dir_name,
                "test_to_gams_workspace_exports_global_parameters_only_not_the_corresponding_domain.sqlite",
            )
            dbmanip.import_object_classes(database_map, ["global_domain"])
            dbmanip.import_objects(database_map, [("global_domain", "record")])
            dbmanip.import_object_parameters(database_map, [("global_domain", "global_parameter")])
            dbmanip.import_object_parameter_values(
                database_map, [("global_domain", "record", "global_parameter", -4.2)]
            )
            settings = gdx.make_set_settings(database_map)
            settings.global_parameters_domain_name = "global_domain"
            path_to_gdx = Path(tmp_dir_name).joinpath(
                "test_to_gdx_file_sorts_domains_and_sets_and_records_correctly.gdx"
            )
            gdx.to_gdx_file(
                database_map,
                path_to_gdx,
                settings,
                {},
                {},
                gdx.NoneFallback.USE_IT,
                gdx.NoneExport.DO_NOT_EXPORT,
                gams_directory,
            )
            database_map.connection.close()
            with GdxFile(path_to_gdx, "r", gams_directory) as gdx_file:
                self.assertEqual(len(gdx_file), 1)
                gams_scalar = gdx_file["global_parameter"]
                self.assertEqual(float(gams_scalar), -4.2)

    @unittest.skipIf(gdx.find_gams_directory() is None, "No working GAMS installation found.")
    def test_to_gdx_file_exports_additional_domains(self):
        gams_directory = gdx.find_gams_directory()
        with TemporaryDirectory() as tmp_dir_name:
            database_map = self._make_database_map(tmp_dir_name, "test_to_gdx_file_exports_additional_domains.sqlite")
            domain_names = {"extra_domain"}
            sorted_records = {"extra_domain": gdx.LiteralRecords([("record1",), ("record2",)])}
            settings = gdx.SetSettings(domain_names, set(), sorted_records)
            settings.metadata("extra_domain").origin = gdx.Origin.INDEXING
            path_to_gdx = Path(tmp_dir_name).joinpath("test_to_gdx_file_exports_additional_domains.gdx")
            gdx.to_gdx_file(
                database_map,
                path_to_gdx,
                settings,
                {},
                {},
                gdx.NoneFallback.USE_IT,
                gdx.NoneExport.DO_NOT_EXPORT,
                gams_directory,
            )
            database_map.connection.close()
            with GdxFile(path_to_gdx, "r", gams_directory) as gdx_file:
                self.assertEqual(len(gdx_file), 1)
                self.assertTrue("extra_domain" in gdx_file)
                additional_gams_domain = gdx_file["extra_domain"]
                self.assertEqual(len(additional_gams_domain), 2)
                # pylint: disable=unsupported-membership-test
                self.assertTrue("record1" in additional_gams_domain)
                self.assertTrue("record2" in additional_gams_domain)

    @unittest.skipIf(gdx.find_gams_directory() is None, "No working GAMS installation found.")
    def test_to_gdx_file_expands_indexed_parameters(self):
        gams_directory = gdx.find_gams_directory()
        with TemporaryDirectory() as tmp_dir_name:
            database_map = self._make_database_map(tmp_dir_name, "test_to_gdx_file_expands_indexed_parameters.sqlite")
            dbmanip.import_object_classes(database_map, ["domain1", "domain2", "internal_indexes"])
            dbmanip.import_objects(
                database_map, [("domain1", "record11"), ("domain1", "record12"), ("domain2", "record21")]
            )
            dbmanip.import_objects(database_map, [("internal_indexes", "stamp1"), ("internal_indexes", "stamp2")])
            dbmanip.import_relationship_classes(database_map, [("set1", ["domain1"]), ("set2", ["domain1", "domain2"])])
            dbmanip.import_relationships(
                database_map,
                [
                    ("set1", ["record12"]),
                    ("set1", ["record11"]),
                    ("set2", ["record12", "record21"]),
                    ("set2", ["record11", "record21"]),
                ],
            )
            dbmanip.import_relationship_parameters(database_map, [("set1", "scalar")])
            dbmanip.import_relationship_parameter_values(database_map, [["set1", ["record11"], "scalar", 3.14]])
            dbmanip.import_relationship_parameter_values(database_map, [["set1", ["record12"], "scalar", 5.5]])
            dbmanip.import_relationship_parameters(database_map, [("set2", "internally_indexed")])
            dbmanip.import_relationship_parameter_values(
                database_map,
                [["set2", ["record12", "record21"], "internally_indexed", {"type": "time_series", "data": [2.2, 1.1]}]],
            )
            dbmanip.import_relationship_parameters(database_map, [("set2", "externally_indexed")])
            dbmanip.import_relationship_parameter_values(
                database_map,
                [
                    [
                        "set2",
                        ["record11", "record21"],
                        "externally_indexed",
                        {"type": "time_series", "data": [-4.2, -2.3, -5.0]},
                    ]
                ],
            )
            domain_names = {"domain1", "domain2", "internal_indexes", "external_indexes"}
            domain_tiers = {"domain1": 2, "domain2": 0, "internal_indexes": 1, "external_indexes": 3}
            set_names = {"set1", "set2"}
            set_tiers = {"set1": 1, "set2": 0}
            sorted_records = {
                "domain1": gdx.LiteralRecords([("record12",), ("record11",)]),
                "internal_indexes": gdx.LiteralRecords([("stamp1",), ("stamp2",)]),
                "domain2": gdx.LiteralRecords([("record21",)]),
                "external_indexes": gdx.LiteralRecords([("T0001",), ("T0002",), ("T0003",)]),
                "set1": gdx.LiteralRecords([("record12",), ("record11",)]),
                "set2": gdx.LiteralRecords([("record12", "record21"), ("record11", "record21")]),
            }
            settings = gdx.SetSettings(
                domain_names, set_names, sorted_records, domain_tiers=domain_tiers, set_tiers=set_tiers
            )
            settings.metadata("external_indexes").origin = gdx.Origin.INDEXING
            externally_indexed_parameter, set_name = gdx._find_indexed_parameter(
                "externally_indexed", database_map, gdx.NoneFallback.USE_IT
            )
            externally_indexed_setting = gdx.IndexingSetting(externally_indexed_parameter, set_name)
            externally_indexed_setting.indexing_domain_name = "external_indexes"
            externally_indexed_setting.picking = gdx.FixedPicking([True, True, True])
            internally_indexed_parameter, set_name = gdx._find_indexed_parameter(
                "internally_indexed", database_map, gdx.NoneFallback.USE_IT
            )
            internally_indexed_setting = gdx.IndexingSetting(internally_indexed_parameter, set_name)
            internally_indexed_setting.indexing_domain_name = "internal_indexes"
            internally_indexed_setting.picking = gdx.GeneratedPicking("True")
            internally_indexed_setting.index_position = 1
            indexing_settings = {
                "externally_indexed": externally_indexed_setting,
                "internally_indexed": internally_indexed_setting,
            }
            path_to_gdx = Path(tmp_dir_name).joinpath("test_to_gdx_file_expands_indexed_parameters.gdx")
            gdx.to_gdx_file(
                database_map,
                path_to_gdx,
                settings,
                indexing_settings,
                {},
                gdx.NoneFallback.USE_IT,
                gdx.NoneExport.DO_NOT_EXPORT,
                gams_directory,
            )
            database_map.connection.close()
            with GdxFile(path_to_gdx, "r", gams_directory) as gdx_file:
                self.assertEqual(len(gdx_file), 9)
                expected_symbol_names = [
                    "domain2",
                    "internal_indexes",
                    "domain1",
                    "external_indexes",
                    "set2",
                    "set1",
                    "scalar",
                    "internally_indexed",
                    "externally_indexed",
                ]
                for gams_symbol, expected_name in zip(gdx_file.keys(), expected_symbol_names):
                    self.assertEqual(gams_symbol, expected_name)
                gams_set = gdx_file["domain1"]
                self.assertEqual(len(gams_set), 2)
                expected_records = ["record12", "record11"]
                for gams_record, expected_name in zip(gams_set, expected_records):
                    self.assertEqual(gams_record, expected_name)
                gams_set = gdx_file["domain2"]
                self.assertEqual(len(gams_set), 1)
                self.assertEqual(gams_set.elements[0], "record21")
                gams_set = gdx_file["internal_indexes"]
                self.assertEqual(len(gams_set), 2)
                # pylint: disable=unsupported-membership-test
                self.assertTrue("stamp1" in gams_set)
                self.assertTrue("stamp2" in gams_set)
                gams_set = gdx_file["external_indexes"]
                self.assertEqual(len(gams_set), 3)
                self.assertTrue(all(key in gams_set for key in ["T0001", "T0002", "T0003"]))
                gams_set = gdx_file["set1"]
                self.assertEqual(len(gams_set), 2)
                expected_records = ["record12", "record11"]
                for gams_record, expected_name in zip(gams_set, expected_records):
                    self.assertEqual(gams_record, expected_name)
                gams_set = gdx_file["set2"]
                self.assertEqual(len(gams_set), 2)
                expected_records = [("record12", "record21"), ("record11", "record21")]
                for gams_record, expected_name in zip(gams_set, expected_records):
                    self.assertEqual(gams_record, expected_name)
                gams_parameter = gdx_file["scalar"]
                self.assertEqual(gams_parameter.domain, ["domain1"])
                self.assertEqual(list(gams_parameter.keys()), ["record12", "record11"])
                self.assertEqual(list(gams_parameter.values()), [5.5, 3.14])
                gams_parameter = gdx_file["internally_indexed"]
                self.assertEqual(gams_parameter.domain, ["domain1", "internal_indexes", "domain2"])
                self.assertEqual(
                    list(gams_parameter.keys()),
                    [("record12", "stamp1", "record21"), ("record12", "stamp2", "record21")],
                )
                self.assertEqual(list(gams_parameter.values()), [2.2, 1.1])
                gams_parameter = gdx_file["externally_indexed"]
                self.assertEqual(gams_parameter.domain, ["domain1", "domain2", "external_indexes"])
                self.assertEqual(
                    list(gams_parameter.keys()),
                    [
                        ("record11", "record21", "T0001"),
                        ("record11", "record21", "T0002"),
                        ("record11", "record21", "T0003"),
                    ],
                )
                self.assertEqual(list(gams_parameter.values()), [-4.2, -2.3, -5.0])

    @unittest.skipIf(gdx_utils.find_gams_directory() is None, "No working GAMS installation found.")
    def test_to_gdx_file_works_with_empty_domains(self):
        gams_directory = gdx.find_gams_directory()
        with TemporaryDirectory() as tmp_dir_name:
            database_map = self._make_database_map(tmp_dir_name, "test_to_gdx_file_works_with_empty_domains.sqlite")
            dbmanip.import_object_classes(database_map, ["domain"])
            domain_names = {"domain"}
            settings = gdx.SetSettings(domain_names, set(), {"domain": gdx.LiteralRecords([])})
            path_to_gdx = Path(tmp_dir_name).joinpath("test_to_gdx_file_works_with_empty_domains.gdx")
            gdx.to_gdx_file(
                database_map,
                path_to_gdx,
                settings,
                {},
                {},
                gdx.NoneFallback.USE_IT,
                gdx.NoneExport.DO_NOT_EXPORT,
                gams_directory,
            )
            database_map.connection.close()
            with GdxFile(path_to_gdx, "r", gams_directory) as gdx_file:
                self.assertEqual(len(gdx_file), 1)
                expected_symbol_names = ["domain"]
                for gams_symbol, expected_name in zip(gdx_file.keys(), expected_symbol_names):
                    self.assertEqual(gams_symbol, expected_name)
                gams_set = gdx_file["domain"]
                self.assertEqual(len(gams_set), 0)

    @unittest.skipIf(gdx_utils.find_gams_directory() is None, "No working GAMS installation found.")
    def test_to_gdx_file_falls_back_to_default_parameter_values(self):
        gams_directory = gdx.find_gams_directory()
        with TemporaryDirectory() as tmp_dir_name:
            database_map = self._make_database_map(
                tmp_dir_name, "test_to_gdx_file_falls_back_to_default_parameter_values.sqlite"
            )
            dbmanip.import_object_classes(database_map, ["domain"])
            dbmanip.import_objects(database_map, [("domain", "record")])
            dbmanip.import_object_parameters(database_map, [("domain", "scalar", 3.14)])
            dbmanip.import_object_parameter_values(database_map, [("domain", "record", "scalar", None)])
            domain_names = {"domain"}
            settings = gdx.SetSettings(domain_names, set(), {"domain": gdx.LiteralRecords([("record",)])})
            path_to_gdx = Path(tmp_dir_name).joinpath("test_to_gdx_file_works_with_empty_parameters.gdx")
            gdx.to_gdx_file(
                database_map,
                path_to_gdx,
                settings,
                {},
                {},
                gdx.NoneFallback.USE_DEFAULT_VALUE,
                gdx.NoneExport.DO_NOT_EXPORT,
                gams_directory,
            )
            database_map.connection.close()
            with GdxFile(path_to_gdx, "r", gams_directory) as gdx_file:
                self.assertEqual(len(gdx_file), 2)
                expected_symbol_names = ["domain"]
                for gams_symbol, expected_name in zip(gdx_file.keys(), expected_symbol_names):
                    self.assertEqual(gams_symbol, expected_name)
                gams_set = gdx_file["domain"]
                self.assertEqual(len(gams_set), 1)
                expected_records = ["record"]
                for gams_record, expected_name in zip(gams_set, expected_records):
                    self.assertEqual(gams_record, expected_name)
                gams_parameter = gdx_file["scalar"]
                self.assertEqual(gams_parameter.domain, ["domain"])
                self.assertEqual(list(gams_parameter.keys()), ["record"])
                self.assertEqual(list(gams_parameter.values()), [3.14])

    @unittest.skipIf(gdx_utils.find_gams_directory() is None, "No working GAMS installation found.")
    def test_to_gdx_file_replaces_nones_with_nans(self):
        gams_directory = gdx.find_gams_directory()
        with TemporaryDirectory() as tmp_dir_name:
            database_map = self._make_database_map(
                tmp_dir_name, "test_to_gdx_file_falls_back_to_default_parameter_values.sqlite"
            )
            dbmanip.import_object_classes(database_map, ["domain"])
            dbmanip.import_objects(database_map, [("domain", "record")])
            dbmanip.import_object_parameters(database_map, [("domain", "scalar")])
            dbmanip.import_object_parameter_values(database_map, [("domain", "record", "scalar", None)])
            domain_names = {"domain"}
            settings = gdx.SetSettings(domain_names, set(), {"domain": gdx.LiteralRecords([("record",)])})
            path_to_gdx = Path(tmp_dir_name).joinpath("test_to_gdx_file_works_with_empty_parameters.gdx")
            gdx.to_gdx_file(
                database_map,
                path_to_gdx,
                settings,
                {},
                {},
                gdx.NoneFallback.USE_IT,
                gdx.NoneExport.EXPORT_AS_NAN,
                gams_directory,
            )
            database_map.connection.close()
            with GdxFile(path_to_gdx, "r", gams_directory) as gdx_file:
                self.assertEqual(len(gdx_file), 2)
                expected_symbol_names = ["domain"]
                for gams_symbol, expected_name in zip(gdx_file.keys(), expected_symbol_names):
                    self.assertEqual(gams_symbol, expected_name)
                gams_set = gdx_file["domain"]
                self.assertEqual(len(gams_set), 1)
                expected_records = ["record"]
                for gams_record, expected_name in zip(gams_set, expected_records):
                    self.assertEqual(gams_record, expected_name)
                gams_parameter = gdx_file["scalar"]
                self.assertEqual(gams_parameter.domain, ["domain"])
                self.assertEqual(list(gams_parameter.keys()), ["record"])
                self.assertEqual(list(gams_parameter.values()), [math.nan])

    def test_make_set_settings(self):
        with TemporaryDirectory() as tmp_dir_name:
            database_map = self._make_database_map(tmp_dir_name, "test_make_settings.sqlite")
            dbmanip.import_object_classes(database_map, ["domain1", "domain2"])
            dbmanip.import_objects(
                database_map, [("domain1", "record11"), ("domain1", "record12"), ("domain2", "record21")]
            )
            dbmanip.import_relationship_classes(database_map, [("set1", ["domain1"]), ("set2", ["domain1", "domain2"])])
            dbmanip.import_relationships(
                database_map,
                [
                    ("set1", ["record12"]),
                    ("set1", ["record11"]),
                    ("set2", ["record12", "record21"]),
                    ("set2", ["record11", "record21"]),
                ],
            )
            settings = gdx.make_set_settings(database_map)
            database_map.connection.close()
        self.assertEqual(settings.domain_names, {"domain1", "domain2"})
        self.assertEqual(settings.domain_tiers, {"domain1": 0, "domain2": 1})
        self.assertEqual(settings.metadata("domain1"), gdx.SetMetadata())
        self.assertEqual(settings.metadata("domain2"), gdx.SetMetadata())
        self.assertEqual(settings.set_names, {"set1", "set2"})
        self.assertEqual(settings.set_tiers, {"set1": 0, "set2": 1})
        self.assertEqual(settings.metadata("set1"), gdx.SetMetadata())
        self.assertEqual(settings.metadata("set2"), gdx.SetMetadata())
        record_keys = settings.records("domain1").records
        self.assertEqual(record_keys, [("record11",), ("record12",)])
        record_keys = settings.records("domain2").records
        self.assertEqual(record_keys, [("record21",)])
        record_keys = settings.records("set1").records
        self.assertEqual(record_keys, [("record12",), ("record11",)])
        record_keys = settings.records("set2").records
        self.assertEqual(record_keys, [("record12", "record21"), ("record11", "record21")])

    def test_SetSettings_update_domains_and_domain_metadatas(self):
        base_settings = gdx.SetSettings(
            {"a", "b"},
            set(),
            {"a": gdx.LiteralRecords([]), "b": gdx.LiteralRecords([])},
            metadatas={
                "a": gdx.SetMetadata(gdx.ExportFlag.NON_EXPORTABLE),
                "b": gdx.SetMetadata(gdx.ExportFlag.NON_EXPORTABLE),
            },
        )
        update_settings = gdx.SetSettings(
            {"b", "c"},
            set(),
            {"b": gdx.LiteralRecords([]), "c": gdx.LiteralRecords([])},
            metadatas={
                "b": gdx.SetMetadata(gdx.ExportFlag.EXPORTABLE),
                "c": gdx.SetMetadata(gdx.ExportFlag.EXPORTABLE, gdx.Origin.INDEXING),
            },
        )
        base_settings.update(update_settings)
        self.assertEqual(base_settings._domain_names, {"b", "c"})
        self.assertEqual(base_settings.metadata("b"), gdx.SetMetadata(gdx.ExportFlag.NON_EXPORTABLE))
        self.assertEqual(base_settings.metadata("c"), gdx.SetMetadata(gdx.ExportFlag.EXPORTABLE, gdx.Origin.INDEXING))
        self.assertEqual(base_settings.domain_tiers, {"b": 0, "c": 1})
        self.assertEqual(base_settings.set_names, set())
        self.assertEqual(base_settings.set_tiers, {})
        self.assertEqual(base_settings.global_parameters_domain_name, "")

    def test_SetSettings_update_sets_and_set_metadatas(self):
        base_settings = gdx.SetSettings(
            set(),
            {"a", "b"},
            {"a": gdx.LiteralRecords([]), "b": gdx.LiteralRecords([])},
            metadatas={
                "a": gdx.SetMetadata(gdx.ExportFlag.NON_EXPORTABLE),
                "b": gdx.SetMetadata(gdx.ExportFlag.NON_EXPORTABLE),
            },
        )
        update_settings = gdx.SetSettings(
            set(),
            {"b", "c"},
            {"b": gdx.LiteralRecords([]), "c": gdx.LiteralRecords([])},
            metadatas={
                "b": gdx.SetMetadata(gdx.ExportFlag.EXPORTABLE, gdx.Origin.INDEXING),
                "c": gdx.SetMetadata(gdx.ExportFlag.NON_EXPORTABLE, gdx.Origin.MERGING),
            },
        )
        base_settings.update(update_settings)
        self.assertEqual(base_settings.domain_names, set())
        self.assertEqual(base_settings.domain_tiers, dict())
        self.assertEqual(base_settings.set_names, {"b", "c"})
        self.assertEqual(base_settings.set_tiers, {"b": 0, "c": 1})
        self.assertEqual(base_settings.metadata("b"), gdx.SetMetadata(gdx.ExportFlag.NON_EXPORTABLE))
        self.assertEqual(
            base_settings.metadata("c"), gdx.SetMetadata(gdx.ExportFlag.NON_EXPORTABLE, gdx.Origin.MERGING)
        )
        self.assertEqual(base_settings.global_parameters_domain_name, "")

    def test_SetSettings_update_global_parameters_domain_name(self):
        base_settings = gdx.SetSettings(
            {"a", "b"},
            set(),
            {"a": gdx.LiteralRecords([]), "b": gdx.LiteralRecords([])},
            global_parameters_domain_name="b",
        )
        update_settings = gdx.SetSettings(
            {"b", "c"},
            set(),
            {"b": gdx.LiteralRecords([]), "c": gdx.LiteralRecords([])},
            global_parameters_domain_name="c",
        )
        base_settings.update(update_settings)
        self.assertEqual(base_settings.domain_names, {"b", "c"})
        self.assertEqual(base_settings.domain_tiers, {"b": 0, "c": 1})
        self.assertEqual(base_settings.metadata("b"), gdx.SetMetadata())
        self.assertEqual(base_settings.metadata("c"), gdx.SetMetadata())
        self.assertEqual(base_settings.set_names, set())
        self.assertEqual(base_settings.set_tiers, dict())
        self.assertEqual(base_settings.global_parameters_domain_name, "b")

    def test_SetSettings_update_records(self):
        base_settings = gdx.SetSettings(
            {"a", "b"},
            {"c"},
            {
                "a": gdx.LiteralRecords([("A",)]),
                "b": gdx.LiteralRecords([("B",), ("BB",)]),
                "c": gdx.LiteralRecords([("C",), ("CC",)]),
            },
            metadatas={
                "a": gdx.SetMetadata(gdx.ExportFlag.EXPORTABLE),
                "b": gdx.SetMetadata(gdx.ExportFlag.NON_EXPORTABLE, gdx.Origin.INDEXING),
                "c": gdx.SetMetadata(gdx.ExportFlag.NON_EXPORTABLE),
            },
        )
        update_settings = gdx.SetSettings(
            {"b", "d"},
            {"c"},
            {
                "b": gdx.LiteralRecords([("BB",), ("BBB",)]),
                "c": gdx.LiteralRecords([("CC",), ("CCC",)]),
                "d": gdx.LiteralRecords([("D",)]),
            },
            metadatas={
                "b": gdx.SetMetadata(gdx.ExportFlag.EXPORTABLE),
                "d": gdx.SetMetadata(gdx.ExportFlag.NON_EXPORTABLE),
                "c": gdx.SetMetadata(gdx.ExportFlag.NON_EXPORTABLE, gdx.Origin.MERGING),
            },
        )
        base_settings.update(update_settings)
        self.assertEqual(base_settings.domain_names, {"b", "d"})
        self.assertEqual(base_settings.domain_tiers, {"b": 0, "d": 1})
        self.assertEqual(
            base_settings.metadata("b"), gdx.SetMetadata(gdx.ExportFlag.NON_EXPORTABLE, gdx.Origin.INDEXING)
        )
        self.assertEqual(base_settings.metadata("d"), gdx.SetMetadata(gdx.ExportFlag.NON_EXPORTABLE))
        self.assertEqual(base_settings.set_names, {"c"})
        self.assertEqual(base_settings.metadata("c"), gdx.SetMetadata(gdx.ExportFlag.NON_EXPORTABLE))
        self.assertEqual(base_settings.global_parameters_domain_name, "")
        self.assertEqual(base_settings.records("b").records, [("BB",), ("BBB",)])
        self.assertEqual(base_settings.records("c").records, [("CC",), ("CCC",)])
        self.assertEqual(base_settings.records("d").records, [("D",)])

    def test_SetSettings_add_domain(self):
        settings = gdx.SetSettings(
            {"a"},
            set(),
            {"a": gdx.LiteralRecords([("A",)])},
            metadatas={"a": gdx.SetMetadata(gdx.ExportFlag.EXPORTABLE, gdx.Origin.MERGING)},
        )
        domain = gdx.Set("b")
        domain.records.append(gdx.Record(("B",)))
        settings.add_or_replace_domain(
            "b", gdx.LiteralRecords([("B",)]), gdx.SetMetadata(gdx.ExportFlag.NON_EXPORTABLE)
        )
        self.assertEqual(settings.domain_names, {"a", "b"})
        self.assertEqual(settings.domain_tiers, {"a": 0, "b": 1})
        self.assertEqual(settings.records("a").records, [("A",)])
        self.assertEqual(settings.records("b").records, [("B",)])
        self.assertEqual(settings.metadata("a"), gdx.SetMetadata(gdx.ExportFlag.EXPORTABLE, gdx.Origin.MERGING))
        self.assertEqual(settings.metadata("b"), gdx.SetMetadata(gdx.ExportFlag.NON_EXPORTABLE))
        self.assertFalse(settings.set_names)
        self.assertFalse(settings.set_tiers)
        self.assertEqual(settings.global_parameters_domain_name, "")

    def test_SetSettings_replace_domain(self):
        settings = gdx.SetSettings(
            {"a"},
            set(),
            {"a": gdx.LiteralRecords([("A",)])},
            metadatas={"a": gdx.SetMetadata(gdx.ExportFlag.EXPORTABLE, gdx.Origin.INDEXING)},
        )
        domain = gdx.Set("a")
        domain.records.append(gdx.Record(("B",)))
        settings.add_or_replace_domain(
            "a", gdx.LiteralRecords([("B",)]), gdx.SetMetadata(gdx.ExportFlag.NON_EXPORTABLE)
        )
        self.assertEqual(settings.domain_names, {"a"})
        self.assertEqual(settings.domain_tiers, {"a": 0})
        self.assertEqual(settings.metadata("a"), gdx.SetMetadata(gdx.ExportFlag.NON_EXPORTABLE))
        self.assertEqual(settings.set_names, set())
        self.assertEqual(settings.global_parameters_domain_name, "")
        self.assertEqual(settings.records("a").records, [("B",)])

    def test_SetSettings_remove_domain(self):
        settings = gdx.SetSettings(
            {"a"},
            set(),
            {"a": gdx.LiteralRecords([("A",)])},
            metadatas={"a": gdx.SetMetadata(gdx.ExportFlag.EXPORTABLE, gdx.Origin.INDEXING)},
        )
        settings.remove_domain("a")
        self.assertEqual(settings.domain_names, set())
        self.assertEqual(settings.domain_tiers, dict())
        self.assertEqual(settings.set_names, set())
        self.assertRaises(KeyError, settings.metadata, "a")
        self.assertEqual(settings.global_parameters_domain_name, "")

    def test_SetSettings_remove_domain_clears_global_parameters_domain_name(self):
        settings = gdx.SetSettings(
            {"a"},
            set(),
            {"a": gdx.LiteralRecords([])},
            metadatas={"a": gdx.SetMetadata()},
            global_parameters_domain_name="a",
        )
        self.assertEqual(settings.global_parameters_domain_name, "a")
        settings.remove_domain("a")
        self.assertEqual(settings.global_parameters_domain_name, "")

    def test_SetSettings_is_exportable_domain(self):
        settings = gdx.SetSettings({"a"}, set(), {"a": gdx.LiteralRecords([])}, metadatas={"a": gdx.SetMetadata()})
        self.assertTrue(settings.is_exportable("a"))
        settings.metadata("a").exportable = gdx.ExportFlag.NON_EXPORTABLE
        self.assertFalse(settings.is_exportable("a"))

    def test_SetSettings_is_exportable_set(self):
        settings = gdx.SetSettings(set(), {"b"}, {"b": gdx.LiteralRecords([])}, metadatas={"b": gdx.SetMetadata()})
        self.assertTrue(settings.is_exportable("b"))
        settings.metadata("b").exportable = gdx.ExportFlag.NON_EXPORTABLE
        self.assertFalse(settings.is_exportable("b"))

    def test_expand_indexed_parameter_values_for_domains(self):
        domain = gdx.Set("domain name")
        record = gdx.Record(("element",))
        domain.records.append(record)
        time_series = TimeSeriesFixedResolution("2019-01-01T12:15", "1D", [3.3, 4.4], False, False)
        parameters = {"time series": gdx.Parameter(["domain name"], [("element",)], [time_series])}
        setting = gdx.IndexingSetting(parameters["time series"], "domain name")
        setting.indexing_domain_name = "indexes"
        setting.picking = gdx.FixedPicking([True, True])
        settings = {"time series": setting}
        domain = gdx.Set("domain name")
        domain.records = [gdx.Record(("element",))]
        indexes_domain = gdx.Set("indexes")
        indexes_domain.records = [gdx.Record(("stamp1",)), gdx.Record(("stamp2",))]
        domains = {"domain name": domain, "indexes": indexes_domain}
        gdx.expand_indexed_parameter_values(parameters, settings, domains)
        self.assertEqual(len(parameters), 1)
        self.assertEqual(parameters["time series"].domain_names, ["domain name", "indexes"])
        self.assertEqual(list(parameters["time series"].indexes), [("element", "stamp1"), ("element", "stamp2")])
        self.assertEqual(list(parameters["time series"].values), [3.3, 4.4])

    def test_expand_indexed_parameter_values_keeps_non_indexed_parameter_intact(self):
        domain = gdx.Set("domain name")
        record = gdx.Record(("element",))
        domain.records.append(record)
        scalar_parameter = gdx.Parameter(["domain name"], [("element",)], [2.2])
        time_series = TimeSeriesFixedResolution("2019-01-01T12:15", "1D", [3.3, 4.4], False, False)
        indexed_parameter = gdx.Parameter(["domain name"], [("element",)], [time_series])
        parameters = {"scalar": scalar_parameter, "time series": indexed_parameter}
        setting = gdx.IndexingSetting(parameters["time series"], "domain name")
        setting.indexing_domain_name = "indexes"
        setting.picking = gdx.GeneratedPicking("True")
        settings = {"time series": setting}
        stamps = gdx.Set("indexes")
        stamps.records = [gdx.Record(("stamp1",)), gdx.Record(("stamp2",))]
        domains = {"domain name": domain, "indexes": stamps}
        gdx.expand_indexed_parameter_values(parameters, settings, domains)
        self.assertEqual(len(parameters), 2)
        self.assertEqual(parameters["scalar"].domain_names, ["domain name"])
        self.assertEqual(parameters["scalar"].data, {("element",): 2.2})
        self.assertEqual(parameters["time series"].domain_names, ["domain name", "indexes"])
        self.assertEqual(parameters["time series"].data, {("element", "stamp1"): 3.3, ("element", "stamp2"): 4.4})

    def test_expand_sets_indexed_parameter_values_with_multidimensional_sets(self):
        original_set = gdx.Set("set name", domain_names=["domain1", "domain2"])
        record = gdx.Record(("domain1_element", "domain2_element"))
        original_set.records.append(record)
        time_series = TimeSeriesFixedResolution("2019-01-01T12:15", "1D", [3.3, 4.4], False, False)
        parameters = {"time series": gdx.Parameter(original_set.domain_names, [record.keys], [time_series])}
        setting = gdx.IndexingSetting(parameters["time series"], "set name")
        setting.indexing_domain_name = "indexes"
        setting.picking = gdx.GeneratedPicking("True")
        settings = {"time series": setting}
        stamps = gdx.Set("indexes")
        stamps.records = [gdx.Record(("stamp1",)), gdx.Record(("stamp2",))]
        sets = {"set name": original_set, "indexes": stamps}
        gdx.expand_indexed_parameter_values(parameters, settings, sets)
        self.assertEqual(len(parameters), 1)
        self.assertEqual(parameters["time series"].domain_names, ["domain1", "domain2", "indexes"])
        self.assertEqual(
            parameters["time series"].data,
            {
                ("domain1_element", "domain2_element", "stamp1"): 3.3,
                ("domain1_element", "domain2_element", "stamp2"): 4.4,
            },
        )

    def test_make_indexing_settings(self):
        with TemporaryDirectory() as tmp_dir_name:
            database_map = self._make_database_map(tmp_dir_name, "test_make_indexing_settings.sqlite")
            dbmanip.import_object_classes(database_map, ["domain"])
            dbmanip.import_objects(database_map, [("domain", "record")])
            dbmanip.import_object_parameters(database_map, [("domain", "parameter")])
            dbmanip.import_object_parameter_values(
                database_map, [("domain", "record", "parameter", {"type": "time_series", "data": [1, 2, 3]})]
            )
            dbmanip.import_relationship_classes(database_map, [("set", ["domain"])])
            dbmanip.import_relationships(database_map, [("set", ["record"])])
            dbmanip.import_relationship_parameters(database_map, [("set", "relationship_parameter")])
            dbmanip.import_relationship_parameter_values(
                database_map,
                [["set", ["record"], "relationship_parameter", {"type": "time_series", "data": [3, 2, 1]}]],
            )
            indexing_settings = gdx.make_indexing_settings(database_map, gdx.NoneFallback.USE_IT, logger=None)
            database_map.connection.close()
        self.assertEqual(len(indexing_settings), 2)
        self.assertEqual(
            list(indexing_settings["parameter"].parameter.values)[0],
            from_database('{"type": "time_series", "data": [1, 2, 3]}'),
        )
        self.assertIsNone(indexing_settings["parameter"].indexing_domain_name)
        self.assertIsNone(indexing_settings["parameter"].picking)
        self.assertEqual(indexing_settings["parameter"].index_position, 1)
        self.assertEqual(
            list(indexing_settings["relationship_parameter"].parameter.values)[0],
            from_database('{"type": "time_series", "data": [3, 2, 1]}'),
        )
        self.assertIsNone(indexing_settings["relationship_parameter"].indexing_domain_name)
        self.assertIsNone(indexing_settings["relationship_parameter"].picking)
        self.assertEqual(indexing_settings["relationship_parameter"].index_position, 1)

    def test_make_indexing_settings_uses_default_values_when_actual_value_is_none(self):
        with TemporaryDirectory() as tmp_dir_name:
            database_map = self._make_database_map(
                tmp_dir_name, "test_make_indexing_settings_uses_default_values_when_actual_value_missing.sqlite"
            )
            dbmanip.import_object_classes(database_map, ["domain"])
            dbmanip.import_objects(database_map, [("domain", "record")])
            dbmanip.import_object_parameters(
                database_map, [("domain", "parameter", {"type": "time_series", "data": [1, 2, 3]}, "")]
            )
            dbmanip.import_object_parameter_values(database_map, [("domain", "record", "parameter", None)])
            dbmanip.import_relationship_classes(database_map, [("set", ["domain"])])
            dbmanip.import_relationships(database_map, [("set", ["record"])])
            dbmanip.import_relationship_parameters(
                database_map, [("set", "relationship_parameter", {"type": "time_series", "data": [3, 2, 1]}, "")]
            )
            dbmanip.import_relationship_parameter_values(
                database_map, [("set", ["record"], "relationship_parameter", None)]
            )
            indexing_settings = gdx.make_indexing_settings(
                database_map, gdx.NoneFallback.USE_DEFAULT_VALUE, logger=None
            )
            database_map.connection.close()
        self.assertEqual(len(indexing_settings), 2)
        self.assertEqual(
            list(indexing_settings["parameter"].parameter.values)[0],
            from_database('{"type": "time_series", "data": [1, 2, 3]}'),
        )
        self.assertIsNone(indexing_settings["parameter"].indexing_domain_name)
        self.assertIsNone(indexing_settings["parameter"].picking)
        self.assertEqual(indexing_settings["parameter"].index_position, 1)
        self.assertEqual(
            list(indexing_settings["relationship_parameter"].parameter.values)[0],
            from_database('{"type": "time_series", "data": [3, 2, 1]}'),
        )
        self.assertIsNone(indexing_settings["relationship_parameter"].indexing_domain_name)
        self.assertIsNone(indexing_settings["relationship_parameter"].picking)
        self.assertEqual(indexing_settings["relationship_parameter"].index_position, 1)

    def test_indexing_settings_from_dict(self):
        with TemporaryDirectory() as tmp_dir_name:
            time_pattern = TimePattern(["Mo", "Tu"], [42.0, -4.2])
            parameter = gdx.Parameter(["domain1"], [("Espoo",)], [time_pattern])
            original = {"parameter": gdx.IndexingSetting(parameter, "domain1")}
            original["parameter"].indexing_domain_name = "indexing name"
            original["parameter"].picking = gdx.FixedPicking([False, True])
            original["parameter"].index_position = 1
            settings_dict = gdx.indexing_settings_to_dict(original)
            database_map = self._make_database_map(tmp_dir_name, "test_indexing_settings_from_dict.sqlite")
            dbmanip.import_object_classes(database_map, ["domain1"])
            dbmanip.import_objects(database_map, [("domain1", "record")])
            dbmanip.import_object_parameters(database_map, [("domain1", "parameter")])
            dbmanip.import_object_parameter_values(
                database_map,
                [("domain1", "record", "parameter", {"type": "time_pattern", "data": {"Mo": 42.0, "Tu": -4.2}})],
            )
            restored = gdx.indexing_settings_from_dict(
                settings_dict, database_map, gdx.NoneFallback.USE_IT, logger=None
            )
            database_map.connection.close()
        self.assertTrue(len(restored), 1)
        self.assertTrue("parameter" in restored)
        self.assertTrue(restored["parameter"].parameter.values, [time_pattern])
        self.assertTrue(restored["parameter"].indexing_domain_name, "indexing name")
        self.assertTrue(restored["parameter"].picking, gdx.FixedPicking([False, True]))
        self.assertTrue(restored["parameter"].index_position, 1)
        self.assertTrue(restored["parameter"].set_name, "domain1")

    def test_update_indexing_settings_with_new_setting_overriding_old_one(self):
        time_series = TimeSeriesFixedResolution("2019-01-01T12:15", "1D", [3.3, 4.4], False, False)
        old_parameter = gdx.Parameter(["old_domain"], [("r1",)], [time_series])
        old_settings = {"old_parameter_name": gdx.IndexingSetting(old_parameter, "old_domain")}
        new_parameter = gdx.Parameter(["new_domain"], [("r1",)], [time_series])
        new_indexing_setting = gdx.IndexingSetting(new_parameter, "new_domain")
        new_settings = {"new_parameter_name": new_indexing_setting}
        settings = gdx.SetSettings({"new_domain"}, set(), {"new_domain": gdx.LiteralRecords([("r1",)])})
        updated = gdx.update_indexing_settings(old_settings, new_settings, settings)
        self.assertEqual(len(updated), 1)
        self.assertTrue("new_parameter_name" in updated)
        self.assertEqual(updated["new_parameter_name"], new_indexing_setting)

    def test_update_indexing_settings_with_old_setting_overriding_new_one_when_additional_domains_present(self):
        time_series = TimeSeriesFixedResolution("2019-01-01T12:15", "1D", [3.3, 4.4], False, False)
        old_parameter = gdx.Parameter(["domain"], [("r1",)], [time_series])
        indexing_setting = gdx.IndexingSetting(old_parameter, "domain")
        indexing_setting.indexing_domain_name = "indexing_domain"
        indexing_setting.picking = gdx.GeneratedPicking("True")
        indexing_setting.index_position = 0
        old_settings = {"parameter_name": indexing_setting}
        new_parameter = gdx.Parameter(["domain"], [("r1",)], [time_series])
        new_settings = {"parameter_name": gdx.IndexingSetting(new_parameter, "domain")}
        settings = gdx.SetSettings({"domain"}, set(), {"domain": gdx.LiteralRecords([("r1",)])})
        updated = gdx.update_indexing_settings(old_settings, new_settings, settings)
        self.assertEqual(len(updated), 1)
        self.assertTrue("parameter_name" in updated)
        self.assertEqual(updated["parameter_name"], indexing_setting)

    def test_update_indexing_settings_with_old_setting_overriding_new_one(self):
        time_series = TimeSeriesFixedResolution("2019-01-01T12:15", "1D", [3.3, 4.4], False, False)
        old_parameter = gdx.Parameter(["domain"], [("r1",)], [time_series])
        indexing_setting = gdx.IndexingSetting(old_parameter, "domain")
        indexing_setting.indexing_domain_name = "indexing_domain"
        indexing_setting.index_position = 0
        old_settings = {"parameter_name": indexing_setting}
        new_parameter = gdx.Parameter(["domain"], [("r1",)], [time_series])
        new_settings = {"parameter_name": gdx.IndexingSetting(new_parameter, "domain")}
        settings = gdx.SetSettings(
            {"domain"},
            set(),
            {"domain": gdx.LiteralRecords([("r1",)]), "indexing_domain": gdx.LiteralRecords([("a",), ("b",)])},
        )
        updated = gdx.update_indexing_settings(old_settings, new_settings, settings)
        self.assertEqual(len(updated), 1)
        self.assertIn("parameter_name", updated)
        self.assertEqual(updated["parameter_name"], indexing_setting)

    def test_update_indexing_settings_new_settings_overriding_when_parameter_length_has_changed(self):
        time_series = TimeSeriesFixedResolution("2019-01-01T12:15", "1D", [3.3, 4.4], False, False)
        old_parameter = gdx.Parameter(["domain"], [("r1",)], [time_series])
        old_indexing_setting = gdx.IndexingSetting(old_parameter, "domain")
        old_indexing_setting.indexing_domain_name = "indexing_domain"
        old_indexing_setting.picking = gdx.FixedPicking([True, True])
        old_indexing_setting.index_position = 0
        old_settings = {"parameter_name": old_indexing_setting}
        new_time_series = TimeSeriesFixedResolution("2019-01-01T12:15", "1D", [3.3, 4.4, 5.5], False, False)
        new_parameter = gdx.Parameter(["domain"], [("r1",)], [new_time_series])
        new_indexing_setting = gdx.IndexingSetting(new_parameter, "domain")
        new_settings = {"parameter_name": new_indexing_setting}
        settings = gdx.SetSettings(
            {"domain", "indexing_domain"},
            set(),
            {"domain": gdx.LiteralRecords([("r1",)]), "indexing_domain": gdx.LiteralRecords([("A",), ("B",)])},
        )
        settings.metadata("indexing_domain").origin = gdx.Origin.INDEXING
        updated = gdx.update_indexing_settings(old_settings, new_settings, settings)
        self.assertEqual(len(updated), 1)
        self.assertTrue("parameter_name" in updated)
        self.assertEqual(updated["parameter_name"], new_indexing_setting)

    def test_MergingSetting_construction(self):
        setting = gdx.MergingSetting(
            ["name1", "name2"], "new domain", "A domain of names.", "set_name", ["domain1", "domain2"]
        )
        self.assertEqual(setting.parameter_names, ["name1", "name2"])
        self.assertEqual(setting.new_domain_name, "new domain")
        self.assertEqual(setting.new_domain_description, "A domain of names.")
        self.assertEqual(setting.previous_set, "set_name")
        self.assertEqual(setting.index_position, 2)
        self.assertEqual(setting.domain_names(), ["domain1", "domain2", "new domain"])

    def test_MergingSetting_index_position(self):
        setting = gdx.MergingSetting(["name"], "new domain", "A domain of names.", "set_name", ["domain1", "domain2"])
        setting.index_position = 0
        self.assertEqual(setting.domain_names(), ["new domain", "domain1", "domain2"])
        setting.index_position = 1
        self.assertEqual(setting.domain_names(), ["domain1", "new domain", "domain2"])
        setting.index_position = 2
        self.assertEqual(setting.domain_names(), ["domain1", "domain2", "new domain"])

    def test_MergingSettings_to_dict(self):
        setting = gdx.MergingSetting(["name"], "new_domain", "A domain of names.", "set_name", ["domain"])
        setting_dict = setting.to_dict()
        self.assertEqual(
            setting_dict,
            {
                "parameters": ["name"],
                "new_domain": "new_domain",
                "domain_description": "A domain of names.",
                "previous_set": "set_name",
                "previous_domains": ["domain"],
                "index_position": 1,
            },
        )

    def test_MergingSettings_from_dict(self):
        setting_dict = {
            "parameters": ["name"],
            "new_domain": "new_domain",
            "domain_description": "A domain of names.",
            "previous_set": "set_name",
            "previous_domains": ["domain"],
            "index_position": 1,
        }
        setting = gdx.MergingSetting.from_dict(setting_dict)
        self.assertEqual(setting.parameter_names, ["name"])
        self.assertEqual(setting.new_domain_name, "new_domain")
        self.assertEqual(setting.new_domain_description, "A domain of names.")
        self.assertEqual(setting.index_position, 1)

    def test_merge_parameters(self):
        parameters = {
            "parameter1": gdx.Parameter(["domain1", "domain2"], [("a1", "b1"), ("a2", "b2")], [1.1, 2.2]),
            "parameter2": gdx.Parameter(["domain1", "domain2"], [("a1", "b1"), ("a2", "b2")], [3.3, 4.4]),
        }
        setting = gdx.MergingSetting(
            ["parameter1", "parameter2"], "new_domain", "A new domain.", "set_name", ["domain1", "domain2"]
        )
        settings = {"merged": setting}
        new_parameters = gdx.merge_parameters(parameters, settings)
        self.assertFalse(parameters)
        self.assertEqual(len(new_parameters), 1)
        self.assertIn("merged", new_parameters)
        new_parameter = new_parameters["merged"]
        self.assertEqual(new_parameter.domain_names, ["domain1", "domain2", "new_domain"])
        self.assertEqual(
            new_parameter.data,
            {
                ("a1", "b1", "parameter1"): 1.1,
                ("a2", "b2", "parameter1"): 2.2,
                ("a1", "b1", "parameter2"): 3.3,
                ("a2", "b2", "parameter2"): 4.4,
            },
        )

    def test_merging_domain(self):
        setting = gdx.MergingSetting(
            ["parameter1", "parameter2"], "new_domain", "A new domain.", "set_name", ["domain1", "domain2"]
        )
        records = gdx.merging_records(setting)
        self.assertEqual(records.records, [("parameter1",), ("parameter2",)])

    def test_update_merging_settings_after_parameter_addition(self):
        settings = gdx.SetSettings({"domain"}, set(), {})
        old_merging_settings = {"merged": gdx.MergingSetting(["parameter1"], "merged_domain", "", "domain", ["domain"])}
        with TemporaryDirectory() as tmp_dir_name:
            database_map = self._make_database_map(tmp_dir_name, "test_make_settings.sqlite")
            dbmanip.import_object_classes(database_map, ["domain"])
            dbmanip.import_object_parameters(database_map, [("domain", "parameter1"), ("domain", "parameter2")])
            updated_merging_settings = gdx.update_merging_settings(old_merging_settings, settings, database_map)
            database_map.connection.close()
        self.assertEqual(len(updated_merging_settings), 1)
        self.assertTrue("merged" in updated_merging_settings)
        setting = updated_merging_settings["merged"]
        self.assertEqual(setting.parameter_names, ["parameter1", "parameter2"])
        self.assertEqual(setting.new_domain_name, "merged_domain")
        self.assertEqual(setting.previous_set, "domain")
        self.assertEqual(setting.index_position, 1)

    def test_update_merging_settings_after_parameter_removal(self):
        settings = gdx.SetSettings({"domain"}, set(), {})
        old_merging_settings = {
            "merged": gdx.MergingSetting(["parameter1", "parameter2"], "merged_domain", "", "domain", ["domain"])
        }
        with TemporaryDirectory() as tmp_dir_name:
            database_map = self._make_database_map(tmp_dir_name, "test_make_settings.sqlite")
            dbmanip.import_object_classes(database_map, ["domain"])
            dbmanip.import_object_parameters(database_map, [("domain", "parameter2")])
            updated_merging_settings = gdx.update_merging_settings(old_merging_settings, settings, database_map)
            database_map.connection.close()
        self.assertEqual(len(updated_merging_settings), 1)
        self.assertTrue("merged" in updated_merging_settings)
        setting = updated_merging_settings["merged"]
        self.assertEqual(setting.parameter_names, ["parameter2"])
        self.assertEqual(setting.new_domain_name, "merged_domain")
        self.assertEqual(setting.previous_set, "domain")
        self.assertEqual(setting.index_position, 1)

    def test_SetMetadata_construction(self):
        metadata = gdx.SetMetadata(gdx.ExportFlag.NON_EXPORTABLE, gdx.Origin.MERGING)
        self.assertEqual(metadata.exportable, gdx.ExportFlag.NON_EXPORTABLE)
        self.assertEqual(metadata.origin, gdx.Origin.MERGING)
        self.assertEqual(metadata.description, "")
        self.assertEqual(metadata.is_additional(), True)

    def test_SetMetadata_from_dict(self):
        original = gdx.SetMetadata(gdx.ExportFlag.NON_EXPORTABLE, gdx.Origin.MERGING)
        original.description = "descriptive"
        meta_dict = original.to_dict()
        restored = gdx.SetMetadata.from_dict(meta_dict)
        self.assertEqual(restored.exportable, gdx.ExportFlag.NON_EXPORTABLE)
        self.assertEqual(restored.origin, gdx.Origin.MERGING)
        self.assertEqual(restored.description, "descriptive")

    @staticmethod
    def _make_settings(domain_exportable_flags=None, set_exportable_flags=None, global_parameters_domain_name=""):
        domain_names = {"domain1", "domain2"}
        set_names = {"set1", "set2", "set3"}
        records = {
            "domain1": gdx.LiteralRecords([("a1",), ("a2",)]),
            "domain2": gdx.LiteralRecords([("b1",)]),
            "set1": gdx.LiteralRecords([("c1", "c2"), ("c3", "c4"), ("c5", "c6")]),
            "set2": gdx.LiteralRecords([("d1",)]),
            "set3": gdx.LiteralRecords([("e1",)]),
        }
        if domain_exportable_flags is None:
            domain_exportable_flags = len(domain_names) * [True]
        if set_exportable_flags is None:
            set_exportable_flags = len(set_names) * [True]
        metadatas = dict()
        for name, exportable in zip(["domain1", "domain2"], domain_exportable_flags):
            flag = gdx.ExportFlag.EXPORTABLE if exportable else gdx.ExportFlag.NON_EXPORTABLE
            metadatas[name] = gdx.SetMetadata(flag)
        if global_parameters_domain_name in domain_names:
            metadatas[global_parameters_domain_name].exportable = gdx.ExportFlag.EXPORTABLE
        for name, exportable in zip(["set1", "set2", "set3"], set_exportable_flags):
            flag = gdx.ExportFlag.EXPORTABLE if exportable else gdx.ExportFlag.NON_EXPORTABLE
            metadatas[name] = gdx.SetMetadata(flag)
        return (
            domain_names,
            set_names,
            records,
            gdx.SetSettings(
                domain_names,
                set_names,
                records,
                metadatas=metadatas,
                global_parameters_domain_name=global_parameters_domain_name,
            ),
        )


if __name__ == '__main__':
    unittest.main()
