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
Unit tests for spinetoolbox.spine_io.exporters.gdx module.

:author: A. Soininen (VTT)
:date:   18.9.2019
"""

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from gdx2py import GdxFile
from PySide2.QtWidgets import QApplication
from spinedb_api import import_functions as dbmanip
from spinedb_api import create_new_spine_database, DiffDatabaseMapping, from_database
from spinedb_api.parameter_value import TimePattern, TimeSeriesFixedResolution
from spinetoolbox.spine_io import gdx_utils
from spinetoolbox.spine_io.exporters import gdx


class TestGdx(unittest.TestCase):
    class _NamedObject:
        def __init__(self, name):
            self.name = name

        def __eq__(self, other):
            return self.name == other.name

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

    def test_Set_from_object_class(self):
        with TemporaryDirectory() as tmp_dir_name:
            database_map = self._make_database_map(tmp_dir_name, "test_Set_from_object_class.sqlite")
            dbmanip.import_object_classes(database_map, ["domain"])
            domain = gdx.Set.from_object_class(database_map.object_class_list()[0])
            database_map.connection.close()
        self.assertEqual(domain.description, "")
        self.assertEqual(domain.domain_names, [None])
        self.assertEqual(domain.dimensions, 1)
        self.assertEqual(domain.name, "domain")
        self.assertEqual(domain.records, [])
        self.assertTrue(domain.is_domain())

    def test_Set_from_relationship_class(self):
        with TemporaryDirectory() as tmp_dir_name:
            database_map = TestGdx._make_database_map(tmp_dir_name, "test_Set_from_relationship_class.sqlite")
            dbmanip.import_object_classes(database_map, ["domain1"])
            dbmanip.import_object_classes(database_map, ["domain2"])
            dbmanip.import_relationship_classes(database_map, [("set", ["domain1", "domain2"])])
            regular_set = gdx.Set.from_relationship_class(database_map.wide_relationship_class_list()[0])
            database_map.connection.close()
        self.assertEqual(regular_set.description, "")
        self.assertEqual(regular_set.domain_names, ["domain1", "domain2"])
        self.assertEqual(regular_set.dimensions, 2)
        self.assertEqual(regular_set.name, "set")
        self.assertEqual(regular_set.records, [])
        self.assertFalse(regular_set.is_domain())

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

    def test_Record_from_object(self):
        with TemporaryDirectory() as tmp_dir_name:
            database_map = self._make_database_map(tmp_dir_name, "test_Record_from_object.sqlite")
            dbmanip.import_object_classes(database_map, ["domain"])
            dbmanip.import_objects(database_map, [("domain", "record")])
            record = gdx.Record.from_object(database_map.object_list()[0])
            database_map.connection.close()
        self.assertEqual(record.keys, ("record",))

    def test_Record_from_relationship(self):
        with TemporaryDirectory() as tmp_dir_name:
            database_map = self._make_database_map(tmp_dir_name, "test_Record_from_relationship.sqlite")
            dbmanip.import_object_classes(database_map, ["domain"])
            dbmanip.import_objects(database_map, [("domain", "record")])
            dbmanip.import_relationship_classes(database_map, [("set", ["domain"])])
            dbmanip.import_relationships(database_map, [("set", ["record"])])
            record = gdx.Record.from_relationship(database_map.wide_relationship_list()[0])
            database_map.connection.close()
        self.assertEqual(record.keys, ("record",))

    def test_Record_from_dict(self):
        original = gdx.Record(("keyA", "keyB", "keyC"))
        record_dict = original.to_dict()
        restored = gdx.Record.from_dict(record_dict)
        self.assertEqual(restored.keys, ("keyA", "keyB", "keyC"))

    def test_Parameter_construction(self):
        parameter = gdx.Parameter(["set name1", "set name2"], [("key1", "key2")], [5.5])
        self.assertEqual(parameter.domain_names, ["set name1", "set name2"])
        self.assertEqual(len(parameter.indexes), 1)
        self.assertEqual(parameter.indexes[0], ("key1", "key2"))
        self.assertEqual(len(parameter.values), 1)
        self.assertEqual(parameter.values[0], 5.5)

    def test_Parameter_from_object_parameter(self):
        parameter = self._object_parameter()
        self.assertEqual(parameter.domain_names, ["domain"])
        self.assertEqual(parameter.indexes, [("record",)])
        self.assertEqual(parameter.values, [-4.2])

    def test_Parameter_from_relationship_parameter(self):
        parameter = self._relationship_parameter()
        self.assertEqual(parameter.domain_names, ["domain1", "domain2"])
        self.assertEqual(parameter.indexes, [("recordA", "recordB")])
        self.assertEqual(parameter.values, [3.14])

    def test_Parameter_append_value(self):
        parameter = gdx.Parameter(["domain"], [("index1",)], [-1.1])
        parameter.append_value(("index2",), -2.2)
        self.assertEqual(parameter.indexes, [("index1",), ("index2",)])
        self.assertEqual(parameter.values, [-1.1, -2.2])

    def test_Parameter_append_object_parameter(self):
        with TemporaryDirectory() as tmp_dir_name:
            database_map = self._make_database_map(tmp_dir_name, "test_Parameter_append_object_parameter.sqlite")
            dbmanip.import_object_classes(database_map, ["domain"])
            dbmanip.import_objects(database_map, [("domain", "record1")])
            dbmanip.import_objects(database_map, [("domain", "record2")])
            dbmanip.import_object_parameters(database_map, [("domain", "parameter")])
            dbmanip.import_object_parameter_values(database_map, [("domain", "record1", "parameter", 1.1)])
            dbmanip.import_object_parameter_values(database_map, [("domain", "record2", "parameter", 2.2)])
            parameter = gdx.Parameter.from_object_parameter(database_map.object_parameter_value_list()[0])
            parameter.append_object_parameter(database_map.object_parameter_value_list()[1])
            database_map.connection.close()
        self.assertEqual(parameter.domain_names, ["domain"])
        self.assertEqual(parameter.indexes, [("record1",), ("record2",)])
        self.assertEqual(parameter.values, [1.1, 2.2])

    def test_Parameter_append_relationship_parameter(self):
        with TemporaryDirectory() as tmp_dir_name:
            database_map = self._make_database_map(tmp_dir_name, "test_Parameter_append_relationship_parameter.sqlite")
            dbmanip.import_object_classes(database_map, ["domain"])
            dbmanip.import_objects(database_map, [("domain", "record1")])
            dbmanip.import_objects(database_map, [("domain", "record2")])
            dbmanip.import_relationship_classes(database_map, [("set", ["domain"])])
            dbmanip.import_relationships(database_map, [("set", ["record1"])])
            dbmanip.import_relationships(database_map, [("set", ["record2"])])
            dbmanip.import_relationship_parameters(database_map, [("set", "parameter")])
            dbmanip.import_relationship_parameter_values(database_map, [["set", ["record1"], "parameter", 3.14]])
            dbmanip.import_relationship_parameter_values(database_map, [["set", ["record2"], "parameter", 6.28]])
            parameter = gdx.Parameter.from_relationship_parameter(database_map.relationship_parameter_value_list()[0])
            parameter.append_relationship_parameter(database_map.relationship_parameter_value_list()[1])
            database_map.connection.close()
        self.assertEqual(parameter.domain_names, ["domain"])
        self.assertEqual(parameter.indexes, [("record1",), ("record2",)])
        self.assertEqual(parameter.values, [3.14, 6.28])

    def test_Parameter_slurp(self):
        parameter = gdx.Parameter(["domain"], [("label1",)], [4.2])
        slurpable = gdx.Parameter(["domain"], [("label2",)], [3.3])
        parameter.slurp(slurpable)
        self.assertEqual(parameter.domain_names, ["domain"])
        self.assertEqual(parameter.indexes, [("label1",), ("label2",)])
        self.assertEqual(parameter.values, [4.2, 3.3])

    def test_parameter_is_scalar(self):
        parameter = gdx.Parameter(["domain"], [("label",)], [2.0])
        self.assertTrue(parameter.is_scalar())
        parameter.values = [TimeSeriesFixedResolution("2019-12-05T01:01:00", "1h", [4.2, 5.3], False, False)]
        self.assertFalse(parameter.is_scalar())

    def test_parameter_is_indexed(self):
        parameter = gdx.Parameter(["domain"], [("label",)], [2.0])
        self.assertFalse(parameter.is_indexed())
        parameter.values = [TimeSeriesFixedResolution("2019-12-05T01:01:00", "1h", [4.2, 5.3], False, False)]
        self.assertTrue(parameter.is_indexed())

    def test_Parameter_expand_indexes(self):
        time_series1 = TimeSeriesFixedResolution("2019-12-05T01:01:00", "1h", [4.2, 5.3], False, False)
        time_series2 = TimeSeriesFixedResolution("2020-12-05T01:01:00", "1h", [-4.2, -5.3], False, False)
        parameter = gdx.Parameter(
            ["domain1", "domain2"], [("index1", "index2"), ("index1", "index3")], [time_series1, time_series2]
        )
        setting = gdx.IndexingSetting(parameter)
        setting.index_position = 1
        setting.indexing_domain = gdx.IndexingDomain(
            "stamp domain", "description", [("stamp1",), ("stamp2",)], [True, True]
        )
        parameter.expand_indexes(setting)
        self.assertEqual(parameter.domain_names, ["domain1", "stamp domain", "domain2"])
        self.assertEqual(
            parameter.indexes,
            [
                ("index1", "stamp1", "index2"),
                ("index1", "stamp2", "index2"),
                ("index1", "stamp1", "index3"),
                ("index1", "stamp2", "index3"),
            ],
        )
        self.assertEqual(parameter.values, [4.2, 5.3, -4.2, -5.3])

    def test_Parameter_equality(self):
        parameter1 = gdx.Parameter(["domain"], [("label",)], [2.0])
        parameter2 = gdx.Parameter(["domain"], [("label",)], [2.0])
        self.assertEqual(parameter1, parameter2)

    def test_IndexingDomain_from_base_domain(self):
        domain = gdx.Set("domain name", "domain description")
        domain.records = [gdx.Record(("key1",)), gdx.Record(("key2",)), gdx.Record(("key3",))]
        indexing_domain = gdx.IndexingDomain.from_base_domain(domain, [True, False, True])
        self.assertEqual(indexing_domain.name, "domain name")
        self.assertEqual(indexing_domain.description, "domain description")
        self.assertEqual(indexing_domain.all_indexes, [("key1",), ("key2",), ("key3",)])
        self.assertEqual(indexing_domain.indexes, [("key1",), ("key3",)])
        self.assertEqual(indexing_domain.pick_list, [True, False, True])

    def test_IndexingDomain_from_dict(self):
        original = gdx.IndexingDomain("domain name", "domain description", [("A", "B"), ("C", "B")], [True, False])
        domain_dict = original.to_dict()
        restored = gdx.IndexingDomain.from_dict(domain_dict)
        self.assertEqual(restored.name, "domain name")
        self.assertEqual(restored.description, "domain description")
        self.assertEqual(restored.all_indexes, [("A", "B"), ("C", "B")])
        self.assertEqual(restored.indexes, [("A", "B")])
        self.assertEqual(restored.pick_list, [True, False])

    def test_Settings_construction(self):
        domain_names, set_names, records, settings = self._make_settings()
        self.assertEqual(settings.sorted_domain_names, domain_names)
        self.assertEqual(settings.domain_metadatas, 2 * [gdx.SetMetadata()])
        self.assertEqual(settings.sorted_set_names, set_names)
        self.assertEqual(settings.set_metadatas, 3 * [gdx.SetMetadata()])
        for keys in records:
            self.assertEqual(settings.sorted_record_key_lists(keys), records[keys])
        self.assertEqual(settings.global_parameters_domain_name, "")

    def test_Settings_serialization_to_dictionary(self):
        domain_metadatas = [
            gdx.SetMetadata(gdx.ExportFlag.FORCED_NON_EXPORTABLE, True),
            gdx.SetMetadata(gdx.ExportFlag.FORCED_EXPORTABLE, False),
        ]
        set_metadatas = [
            gdx.SetMetadata(gdx.ExportFlag.NON_EXPORTABLE, False),
            gdx.SetMetadata(gdx.ExportFlag.EXPORTABLE, True),
            gdx.SetMetadata(gdx.ExportFlag.NON_EXPORTABLE, False),
        ]
        global_domain_name = 'global parameter domain'
        domain_names, set_names, _, settings = self._make_settings(domain_metadatas, set_metadatas, global_domain_name)
        settings_as_dict = settings.to_dict()
        recovered = gdx.Settings.from_dict(settings_as_dict)
        self.assertEqual(recovered.sorted_domain_names, settings.sorted_domain_names)
        self.assertEqual(recovered.domain_metadatas, settings.domain_metadatas)
        self.assertEqual(recovered.sorted_set_names, settings.sorted_set_names)
        self.assertEqual(recovered.set_metadatas, settings.set_metadatas)
        for name in domain_names + set_names:
            self.assertEqual(recovered.sorted_record_key_lists(name), settings.sorted_record_key_lists(name))
        self.assertEqual(recovered.global_parameters_domain_name, settings.global_parameters_domain_name)

    @staticmethod
    def _make_database_map(dir_name, file_name):
        """Creates a Spine sqlite database in dir_name/file_name."""
        database_path = Path(dir_name).joinpath(file_name)
        database_url = 'sqlite:///' + str(database_path)
        create_new_spine_database(database_url)
        return DiffDatabaseMapping(database_url)

    def test_domains_are_read_correctly_form_database(self):
        with TemporaryDirectory() as tmp_dir_name:
            database_map = self._make_database_map(tmp_dir_name, "test_domains_are_read_correctly_form_database.sqlite")
            dbmanip.import_object_classes(database_map, ["domain"])
            dbmanip.import_objects(database_map, [("domain", "record")])
            dbmanip.import_object_parameters(database_map, [("domain", "parameter")])
            dbmanip.import_object_parameter_values(database_map, [("domain", "record", "parameter", -123.4)])
            domains, parameters = gdx.object_classes_to_domains(database_map)
            database_map.connection.close()
        self.assertEqual(len(domains), 1)
        domain = domains[0]
        self.assertEqual(domain.name, "domain")
        self.assertEqual(domain.description, "")
        records = domain.records
        self.assertEqual(len(records), 1)
        record = records[0]
        self.assertEqual(record.keys, ("record",))
        self.assertEqual(len(parameters), 1)
        parameter = parameters["parameter"]
        self.assertEqual(parameter.domain_names, ["domain"])
        self.assertEqual(parameter.indexes, [("record",)])
        self.assertEqual(parameter.values, [-123.4])

    def test_sets_are_read_correctly_form_database(self):
        with TemporaryDirectory() as tmp_dir_name:
            database_map = self._make_database_map(tmp_dir_name, "test_sets_are_read_correctly_form_database.sqlite")
            dbmanip.import_object_classes(database_map, ["domain"])
            dbmanip.import_objects(database_map, [("domain", "record")])
            dbmanip.import_relationship_classes(database_map, [("set", ["domain"])])
            dbmanip.import_relationships(database_map, [("set", ["record"])])
            dbmanip.import_relationship_parameters(database_map, [("set", "parameter")])
            dbmanip.import_relationship_parameter_values(database_map, [["set", ["record"], "parameter", 3.14]])
            sets, set_parameters = gdx.relationship_classes_to_sets(database_map)
            database_map.connection.close()
        self.assertEqual(len(sets), 1)
        set_item = sets[0]
        self.assertEqual(set_item.name, "set")
        self.assertEqual(set_item.domain_names, ["domain"])
        self.assertEqual(set_item.dimensions, 1)
        self.assertEqual(len(set_item.records), 1)
        record = set_item.records[0]
        self.assertEqual(record.keys, ("record",))
        self.assertEqual(len(set_parameters), 1)
        self.assertEqual(set_parameters["parameter"].domain_names, ["domain"])
        self.assertEqual(set_parameters["parameter"].indexes, [("record",)])
        self.assertEqual(set_parameters["parameter"].values, [3.14])

    def test_domain_names_and_records(self):
        with TemporaryDirectory() as tmp_dir_name:
            database_map = self._make_database_map(tmp_dir_name, "test_domain_names_and_records.sqlite")
            dbmanip.import_object_classes(database_map, ["domain"])
            dbmanip.import_objects(database_map, [("domain", "recordA"), ("domain", "recordB")])
            domain_names, domain_records = gdx.domain_names_and_records(database_map)
            database_map.connection.close()
        self.assertEqual(domain_names, ["domain"])
        self.assertEqual(domain_records, {"domain": [("recordA",), ("recordB",)]})

    def test_set_names_and_records(self):
        with TemporaryDirectory() as tmp_dir_name:
            database_map = self._make_database_map(tmp_dir_name, "test_set_names_and_records.sqlite")
            dbmanip.import_object_classes(database_map, ["domain"])
            dbmanip.import_objects(database_map, [("domain", "record")])
            dbmanip.import_relationship_classes(database_map, [("set", ["domain"])])
            dbmanip.import_relationships(database_map, [("set", ["record"])])
            set_names, set_records = gdx.set_names_and_records(database_map)
            database_map.connection.close()
        self.assertEqual(set_names, ["set"])
        self.assertEqual(set_records, {"set": [("record",)]})

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
    def test_parameters_to_gams(self):
        parameters = {"scalar": gdx.Parameter(["domain"], [("key",)], [2.3])}
        gams_directory = gdx_utils.find_gams_directory()
        with TemporaryDirectory() as temp_directory:
            path_to_gdx = Path(temp_directory).joinpath("test_parameters_to_gams.gdx")
            with GdxFile(path_to_gdx, 'w', gams_directory) as gdx_file:
                gdx.parameters_to_gams(gdx_file, parameters)
            with GdxFile(path_to_gdx, 'r', gams_directory) as gdx_file:
                self.assertEqual(len(gdx_file), 1)
                gams_parameter = gdx_file["scalar"]
                self.assertEqual(len(gams_parameter.keys()), 1)
                for key, value in gams_parameter:  # pylint: disable=not-an-iterable
                    self.assertEqual(key, "key")
                    self.assertEqual(value, 2.3)

    @unittest.skipIf(gdx_utils.find_gams_directory() is None, "No working GAMS installation found.")
    def test_domain_parameters_to_gams_scalars(self):
        domain = gdx.Set("object_class_name")
        record = gdx.Record(("mock_object_name",))
        domain.records.append(record)
        parameters = {"mock_parameter_name": gdx.Parameter(["object_class_name"], [["mock_object_name"]], [2.3])}
        gams_directory = gdx_utils.find_gams_directory()
        with TemporaryDirectory() as temp_directory:
            path_to_gdx = Path(temp_directory).joinpath("test_domain_parameters_to_gams_scalars.gdx")
            with GdxFile(path_to_gdx, 'w', gams_directory) as gdx_file:
                gdx.domain_parameters_to_gams_scalars(gdx_file, parameters, "object_class_name")
            with GdxFile(path_to_gdx, 'r', gams_directory) as gdx_file:
                self.assertEqual(len(gdx_file), 1)
                gams_scalar = gdx_file["mock_parameter_name"]
                self.assertEqual(float(gams_scalar), 2.3)

    def test_IndexingSetting_construction(self):
        time_series = TimeSeriesFixedResolution("2019-12-05T01:01:00", "1h", [4.2, 5.3], False, False)
        setting = gdx.IndexingSetting(gdx.Parameter(["domain"], [("keyA",)], [time_series]))
        self.assertIsNone(setting.indexing_domain)
        self.assertEqual(setting.index_position, 1)

    def test_IndexingSetting_append_parameter(self):
        time_series1 = TimeSeriesFixedResolution("2019-12-05T01:01:00", "1h", [4.2, 5.3], False, False)
        setting = gdx.IndexingSetting(gdx.Parameter(["domain"], [("keyA",)], [time_series1]))
        time_series2 = TimeSeriesFixedResolution("2019-12-05T01:01:00", "1h", [-4.2, -5.3], False, False)
        setting.append_parameter(gdx.Parameter(["domain"], [("keyB",)], [time_series2]))
        self.assertEqual(setting.parameter.domain_names, ["domain"])
        self.assertEqual(setting.parameter.indexes, [("keyA",), ("keyB",)])
        self.assertEqual(setting.parameter.values, [time_series1, time_series2])

    def test_filter_and_sort_sets(self):
        set_object = self._NamedObject
        sets = [set_object("set1"), set_object("set2"), set_object("set3")]
        set_names = ["set2", "set1", "set3"]
        set_metadata = [
            gdx.SetMetadata(gdx.ExportFlag.EXPORTABLE),
            gdx.SetMetadata(gdx.ExportFlag.FORCED_EXPORTABLE),
            gdx.SetMetadata(gdx.ExportFlag.NON_EXPORTABLE),
        ]
        filtered = gdx.filter_and_sort_sets(sets, set_names, set_metadata)
        self.assertEqual(filtered, [set_object("set2"), set_object("set1")])

    def test_sort_records_in_place(self):
        class Settings:
            # pylint: disable=no-self-use
            def sorted_record_key_lists(self, domain_name):
                if domain_name == "d1":
                    return [["rB"], ["rA"]]
                if domain_name == "d2":
                    return [["rD"], ["rC"]]
                raise NotImplementedError()

        class Domain:
            def __init__(self, name, records):
                self.name = name
                self.records = records

        class Record:
            def __init__(self, keys):
                self.keys = keys

            def __eq__(self, other):
                return self.keys == other.keys

        domains = [Domain("d1", [Record(["rA"]), Record(["rB"])]), Domain("d2", [Record(["rC"]), Record(["rD"])])]
        gdx.sort_records_inplace(domains, Settings())
        self.assertEqual(domains[0].records, [Record(["rB"]), Record(["rA"])])
        self.assertEqual(domains[1].records, [Record(["rD"]), Record(["rC"])])

    def test_extract_domain(self):
        domain_set = self._NamedObject
        domains = [domain_set("domain1")]
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
            sorted_domain_names = ["domain2", "domain1"]
            sorted_set_names = ["set2", "set1"]
            sorted_records = {
                "domain1": [("record12",), ("record11",)],
                "domain2": [("record21",)],
                "set1": [("record12",), ("record11",)],
                "set2": [("record12", "record21"), ("record11", "record21")],
            }
            settings = gdx.Settings(sorted_domain_names, sorted_set_names, sorted_records)
            path_to_gdx = Path(tmp_dir_name).joinpath(
                "test_to_gdx_file_sorts_domains_and_sets_and_records_correctly.gdx"
            )
            gdx.to_gdx_file(database_map, path_to_gdx, [], settings, {}, {}, gams_directory)
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
            settings = gdx.make_settings(database_map)
            settings.global_parameters_domain_name = "global_domain"
            path_to_gdx = Path(tmp_dir_name).joinpath(
                "test_to_gdx_file_sorts_domains_and_sets_and_records_correctly.gdx"
            )
            gdx.to_gdx_file(database_map, path_to_gdx, [], settings, {}, {}, gams_directory)
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
            sorted_domain_names = ["extra_domain"]
            sorted_records = {"extra_domain": [("record1",), ("record2",)]}
            additional_domains = [gdx.Set("extra_domain", "A bonus domain")]
            additional_domains[0].records.append(gdx.Record(("record1",)))
            additional_domains[0].records.append(gdx.Record(("record2",)))
            settings = gdx.Settings(sorted_domain_names, [], sorted_records)
            path_to_gdx = Path(tmp_dir_name).joinpath("test_to_gdx_file_exports_additional_domains.gdx")
            gdx.to_gdx_file(database_map, path_to_gdx, additional_domains, settings, {}, {}, gams_directory)
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
            additional_domains = [gdx.Set("external_indexes")]
            additional_domains[0].records.append(gdx.Record(("T0001",)))
            additional_domains[0].records.append(gdx.Record(("T0002",)))
            additional_domains[0].records.append(gdx.Record(("T0003",)))
            sorted_domain_names = ["domain2", "internal_indexes", "domain1", "external_indexes"]
            sorted_set_names = ["set2", "set1"]
            sorted_records = {
                "domain1": [("record12",), ("record11",)],
                "internal_indexes": [("stamp1",), ("stamp2",)],
                "domain2": [("record21",)],
                "external_indexes": [("T0001",), ("T0002",), ("T0003",)],
                "set1": [("record12",), ("record11",)],
                "set2": [("record12", "record21"), ("record11", "record21")],
            }
            settings = gdx.Settings(sorted_domain_names, sorted_set_names, sorted_records)
            externally_indexed_parameter = gdx._find_parameter("externally_indexed", database_map)
            externally_indexed_setting = gdx.IndexingSetting(externally_indexed_parameter)
            externally_indexed_setting.indexing_domain = gdx.IndexingDomain(
                "external_indexes", "", [("T0001",), ("T0002",), ("T0003",)], [True, True, True]
            )
            internally_indexed_parameter = gdx._find_parameter("internally_indexed", database_map)
            internally_indexed_setting = gdx.IndexingSetting(internally_indexed_parameter)
            internally_indexed_setting.indexing_domain = gdx.IndexingDomain(
                "internal_indexes", "", [("stamp1",), ("stamp2",)], [True, True]
            )
            internally_indexed_setting.index_position = 1
            indexing_settings = {
                "externally_indexed": externally_indexed_setting,
                "internally_indexed": internally_indexed_setting,
            }
            path_to_gdx = Path(tmp_dir_name).joinpath("test_to_gdx_file_expands_indexed_parameters.gdx")
            gdx.to_gdx_file(
                database_map, path_to_gdx, additional_domains, settings, indexing_settings, {}, gams_directory
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
                self.assertEqual(list(gams_parameter.keys()), ["record11"])
                self.assertEqual(list(gams_parameter.values()), [3.14])
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
            sorted_domain_names = ["domain"]
            settings = gdx.Settings(sorted_domain_names, [], {"domain": []})
            path_to_gdx = Path(tmp_dir_name).joinpath("test_to_gdx_file_works_with_empty_domains.gdx")
            gdx.to_gdx_file(database_map, path_to_gdx, [], settings, {}, {}, gams_directory)
            database_map.connection.close()
            with GdxFile(path_to_gdx, "r", gams_directory) as gdx_file:
                self.assertEqual(len(gdx_file), 1)
                expected_symbol_names = ["domain"]
                for gams_symbol, expected_name in zip(gdx_file.keys(), expected_symbol_names):
                    self.assertEqual(gams_symbol, expected_name)
                gams_set = gdx_file["domain"]
                self.assertEqual(len(gams_set), 0)

    @unittest.skipIf(gdx_utils.find_gams_directory() is None, "No working GAMS installation found.")
    def test_to_gdx_file_works_with_empty_parameters(self):
        gams_directory = gdx.find_gams_directory()
        with TemporaryDirectory() as tmp_dir_name:
            database_map = self._make_database_map(tmp_dir_name, "test_to_gdx_file_works_with_empty_parameters.sqlite")
            dbmanip.import_object_classes(database_map, ["domain"])
            dbmanip.import_objects(
                database_map, [("domain", "record")]
            )
            dbmanip.import_object_parameters(database_map, [("domain", "scalar")])
            sorted_domain_names = ["domain"]
            settings = gdx.Settings(sorted_domain_names, [], {"domain": [("record", )]})
            path_to_gdx = Path(tmp_dir_name).joinpath("test_to_gdx_file_works_with_empty_parameters.gdx")
            gdx.to_gdx_file(database_map, path_to_gdx, [], settings, {}, {}, gams_directory)
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
                self.assertEqual(list(gams_parameter.keys()), [])
                self.assertEqual(list(gams_parameter.values()), [])

    def test_make_settings(self):
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
            settings = gdx.make_settings(database_map)
            database_map.connection.close()
        domain_names = settings.sorted_domain_names
        self.assertEqual(len(domain_names), 2)
        for name in domain_names:
            self.assertTrue(name in ["domain1", "domain2"])
        self.assertEqual(settings.domain_metadatas, [gdx.SetMetadata(), gdx.SetMetadata()])
        set_names = settings.sorted_set_names
        self.assertEqual(len(set_names), 2)
        for name in set_names:
            self.assertTrue(name in ["set1", "set2"])
        self.assertEqual(settings.set_metadatas, [gdx.SetMetadata(), gdx.SetMetadata()])
        record_keys = settings.sorted_record_key_lists("domain1")
        self.assertEqual(record_keys, [("record11",), ("record12",)])
        record_keys = settings.sorted_record_key_lists("domain2")
        self.assertEqual(record_keys, [("record21",)])
        record_keys = settings.sorted_record_key_lists("set1")
        self.assertEqual(record_keys, [("record12",), ("record11",)])
        record_keys = settings.sorted_record_key_lists("set2")
        self.assertEqual(record_keys, [("record12", "record21"), ("record11", "record21")])

    def test_Settings_update_domains_and_domain_metadatas(self):
        base_settings = gdx.Settings(
            ["a", "b"],
            [],
            {},
            [
                gdx.SetMetadata(gdx.ExportFlag.NON_EXPORTABLE, True),
                gdx.SetMetadata(gdx.ExportFlag.FORCED_EXPORTABLE, False),
            ],
            [],
            "",
        )
        update_settings = gdx.Settings(
            ["b", "c"],
            [],
            {},
            [
                gdx.SetMetadata(gdx.ExportFlag.EXPORTABLE, False),
                gdx.SetMetadata(gdx.ExportFlag.FORCED_NON_EXPORTABLE, True),
            ],
            [],
            "",
        )
        base_settings.update(update_settings)
        self.assertEqual(base_settings.sorted_domain_names, ["b", "c"])
        self.assertEqual(
            base_settings.domain_metadatas,
            [
                gdx.SetMetadata(gdx.ExportFlag.FORCED_EXPORTABLE, False),
                gdx.SetMetadata(gdx.ExportFlag.FORCED_NON_EXPORTABLE, True),
            ],
        )
        self.assertEqual(base_settings.sorted_set_names, [])
        self.assertEqual(base_settings.set_metadatas, [])
        self.assertEqual(base_settings.global_parameters_domain_name, "")

    def test_Settings_update_sets_and_set_metadatas(self):
        base_settings = gdx.Settings(
            [],
            ["a", "b"],
            {},
            [],
            [
                gdx.SetMetadata(gdx.ExportFlag.NON_EXPORTABLE, False),
                gdx.SetMetadata(gdx.ExportFlag.FORCED_EXPORTABLE, False),
            ],
            "",
        )
        update_settings = gdx.Settings(
            [],
            ["b", "c"],
            {},
            [],
            [
                gdx.SetMetadata(gdx.ExportFlag.EXPORTABLE, True),
                gdx.SetMetadata(gdx.ExportFlag.FORCED_NON_EXPORTABLE, True),
            ],
            "",
        )
        base_settings.update(update_settings)
        self.assertEqual(base_settings.sorted_domain_names, [])
        self.assertEqual(base_settings.domain_metadatas, [])
        self.assertEqual(base_settings.sorted_set_names, ["b", "c"])
        self.assertEqual(
            base_settings.set_metadatas,
            [
                gdx.SetMetadata(gdx.ExportFlag.FORCED_EXPORTABLE, False),
                gdx.SetMetadata(gdx.ExportFlag.FORCED_NON_EXPORTABLE, True),
            ],
        )
        self.assertEqual(base_settings.global_parameters_domain_name, "")

    def test_Settings_update_global_parameters_domain_name(self):
        base_settings = gdx.Settings(["a", "b"], [], {}, [gdx.SetMetadata(), gdx.SetMetadata()], [], "b")
        update_settings = gdx.Settings(["b", "c"], [], {}, [gdx.SetMetadata(), gdx.SetMetadata()], [], "c")
        base_settings.update(update_settings)
        self.assertEqual(base_settings.sorted_domain_names, ["b", "c"])
        self.assertEqual(base_settings.domain_metadatas, [gdx.SetMetadata(), gdx.SetMetadata()])
        self.assertEqual(base_settings.sorted_set_names, [])
        self.assertEqual(base_settings.set_metadatas, [])
        self.assertEqual(base_settings.global_parameters_domain_name, "b")

    def test_Settings_update_records(self):
        base_settings = gdx.Settings(
            ["a", "b"],
            ["c"],
            {"a": [("A",)], "b": [("B",), ("BB",)], "c": [("C",), ("CC",)]},
            [
                gdx.SetMetadata(gdx.ExportFlag.FORCED_EXPORTABLE, True),
                gdx.SetMetadata(gdx.ExportFlag.NON_EXPORTABLE, True),
            ],
            [gdx.SetMetadata(gdx.ExportFlag.FORCED_NON_EXPORTABLE, False)],
            "",
        )
        update_settings = gdx.Settings(
            ["b", "d"],
            ["c"],
            {"b": [("BB",), ("BBB",)], "c": [("CC",), ("CCC",)], "d": [("D",)]},
            [
                gdx.SetMetadata(gdx.ExportFlag.EXPORTABLE, False),
                gdx.SetMetadata(gdx.ExportFlag.FORCED_EXPORTABLE, False),
            ],
            [gdx.SetMetadata(gdx.ExportFlag.EXPORTABLE, True)],
            "",
        )
        base_settings.update(update_settings)
        self.assertEqual(base_settings.sorted_domain_names, ["b", "d"])
        self.assertEqual(
            base_settings.domain_metadatas,
            [
                gdx.SetMetadata(gdx.ExportFlag.NON_EXPORTABLE, True),
                gdx.SetMetadata(gdx.ExportFlag.FORCED_EXPORTABLE, False),
            ],
        )
        self.assertEqual(base_settings.sorted_set_names, ["c"])
        self.assertEqual(base_settings.set_metadatas, [gdx.SetMetadata(gdx.ExportFlag.FORCED_NON_EXPORTABLE, False)])
        self.assertEqual(base_settings.global_parameters_domain_name, "")
        self.assertEqual(base_settings.sorted_record_key_lists("b"), [("BB",), ("BBB",)])
        self.assertEqual(base_settings.sorted_record_key_lists("c"), [("CC",), ("CCC",)])
        self.assertEqual(base_settings.sorted_record_key_lists("d"), [("D",)])

    def test_Settings_add_domain(self):
        settings = gdx.Settings(
            ["a"], [], {"a": [("A",)]}, [gdx.SetMetadata(gdx.ExportFlag.FORCED_EXPORTABLE, True)], [], ""
        )
        domain = gdx.Set("b")
        domain.records.append(gdx.Record(("B",)))
        settings.add_or_replace_domain(domain, gdx.SetMetadata(gdx.ExportFlag.NON_EXPORTABLE, False))
        self.assertEqual(settings.sorted_domain_names, ["a", "b"])
        self.assertEqual(
            settings.domain_metadatas,
            [
                gdx.SetMetadata(gdx.ExportFlag.FORCED_EXPORTABLE, True),
                gdx.SetMetadata(gdx.ExportFlag.NON_EXPORTABLE, False),
            ],
        )
        self.assertEqual(settings.sorted_set_names, [])
        self.assertEqual(settings.set_metadatas, [])
        self.assertEqual(settings.global_parameters_domain_name, "")
        self.assertEqual(settings.sorted_record_key_lists("a"), [("A",)])
        self.assertEqual(settings.sorted_record_key_lists("b"), [("B",)])

    def test_Settings_replace_domain(self):
        settings = gdx.Settings(
            ["a"], [], {"a": [("A",)]}, [gdx.SetMetadata(gdx.ExportFlag.FORCED_EXPORTABLE, True)], [], ""
        )
        domain = gdx.Set("a")
        domain.records.append(gdx.Record(("B",)))
        settings.add_or_replace_domain(domain, gdx.SetMetadata(gdx.ExportFlag.NON_EXPORTABLE, False))
        self.assertEqual(settings.sorted_domain_names, ["a"])
        self.assertEqual(settings.domain_metadatas, [gdx.SetMetadata(gdx.ExportFlag.NON_EXPORTABLE, False)])
        self.assertEqual(settings.sorted_set_names, [])
        self.assertEqual(settings.set_metadatas, [])
        self.assertEqual(settings.global_parameters_domain_name, "")
        self.assertEqual(settings.sorted_record_key_lists("a"), [("B",)])

    def test_Settings_del_domain_at(self):
        settings = gdx.Settings(
            ["a"], [], {"a": [("A",)]}, [gdx.SetMetadata(gdx.ExportFlag.FORCED_EXPORTABLE, True)], [], ""
        )
        domain = gdx.Set("a")
        i = settings.domain_index(domain)
        settings.del_domain_at(i)
        self.assertEqual(settings.sorted_domain_names, [])
        self.assertEqual(settings.domain_metadatas, [])
        self.assertEqual(settings.sorted_set_names, [])
        self.assertEqual(settings.set_metadatas, [])
        self.assertEqual(settings.global_parameters_domain_name, "")
        self.assertRaises(KeyError, settings.sorted_record_key_lists, "a")

    def test_Settings_del_domain_at_clears_global_parameters_domain_name(self):
        settings = gdx.Settings(["a"], [], {"a": []}, [gdx.SetMetadata()], [], "a")
        self.assertEqual(settings.global_parameters_domain_name, "a")
        domain = gdx.Set("a")
        i = settings.domain_index(domain)
        settings.del_domain_at(i)
        self.assertEqual(settings.global_parameters_domain_name, "")

    def test_expand_indexed_parameter_values_for_domains(self):
        domain = gdx.Set("domain name")
        record = gdx.Record(("element",))
        domain.records.append(record)
        time_series = TimeSeriesFixedResolution("2019-01-01T12:15", "1D", [3.3, 4.4], False, False)
        parameters = {"time series": gdx.Parameter(["domain name"], [("element",)], [time_series])}
        indexing_domain = gdx.IndexingDomain("indexes", "", [("stamp1",), ("stamp2",)], [True, True])
        setting = gdx.IndexingSetting(parameters["time series"])
        setting.indexing_domain = indexing_domain
        settings = {"time series": setting}
        gdx.expand_indexed_parameter_values(parameters, settings)
        self.assertEqual(len(parameters), 1)
        self.assertEqual(parameters["time series"].domain_names, ["domain name", "indexes"])
        self.assertEqual(parameters["time series"].indexes, [("element", "stamp1"), ("element", "stamp2")])
        self.assertEqual(parameters["time series"].values, [3.3, 4.4])

    def test_expand_indexed_parameter_values_keeps_non_indexed_parameter_intact(self):
        domain = gdx.Set("domain name")
        record = gdx.Record(("element",))
        domain.records.append(record)
        scalar_parameter = gdx.Parameter(["domain name"], [("element",)], [2.2])
        time_series = TimeSeriesFixedResolution("2019-01-01T12:15", "1D", [3.3, 4.4], False, False)
        indexed_parameter = gdx.Parameter(["domain name"], [("element",)], [time_series])
        parameters = {"scalar": scalar_parameter, "time series": indexed_parameter}
        indexing_domain = gdx.IndexingDomain("indexes", "", [("stamp1",), ("stamp2",)], [True, True])
        setting = gdx.IndexingSetting(parameters["time series"])
        setting.indexing_domain = indexing_domain
        settings = {"time series": setting}
        gdx.expand_indexed_parameter_values(parameters, settings)
        self.assertEqual(len(parameters), 2)
        self.assertEqual(parameters["scalar"].domain_names, ["domain name"])
        self.assertEqual(parameters["scalar"].indexes, [("element",)])
        self.assertEqual(parameters["scalar"].values, [2.2])
        self.assertEqual(parameters["time series"].domain_names, ["domain name", "indexes"])
        self.assertEqual(parameters["time series"].indexes, [("element", "stamp1"), ("element", "stamp2")])
        self.assertEqual(parameters["time series"].values, [3.3, 4.4])

    def test_expand_sets_indexed_parameter_values_with_multidimensional_sets(self):
        original_set = gdx.Set("set name", domain_names=["domain1", "domain2"])
        record = gdx.Record(("domain1_element", "domain2_element"))
        original_set.records.append(record)
        time_series = TimeSeriesFixedResolution("2019-01-01T12:15", "1D", [3.3, 4.4], False, False)
        parameters = {"time series": gdx.Parameter(original_set.domain_names, [record.keys], [time_series])}
        indexing_domain = gdx.IndexingDomain("indexes", "", [("stamp1",), ("stamp2",)], [True, True])
        setting = gdx.IndexingSetting(parameters["time series"])
        setting.indexing_domain = indexing_domain
        settings = {"time series": setting}
        gdx.expand_indexed_parameter_values(parameters, settings)
        self.assertEqual(len(parameters), 1)
        self.assertEqual(parameters["time series"].domain_names, ["domain1", "domain2", "indexes"])
        self.assertEqual(parameters["time series"].indexes[0], ("domain1_element", "domain2_element", "stamp1"))
        self.assertEqual(parameters["time series"].values[0], 3.3)
        self.assertEqual(parameters["time series"].indexes[1], ("domain1_element", "domain2_element", "stamp2"))
        self.assertEqual(parameters["time series"].values[1], 4.4)

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
            indexing_settings = gdx.make_indexing_settings(database_map)
            database_map.connection.close()
        self.assertEqual(len(indexing_settings), 2)
        self.assertEqual(
            indexing_settings["parameter"].parameter.values[0],
            from_database('{"type": "time_series", "data": [1, 2, 3]}'),
        )
        self.assertIsNone(indexing_settings["parameter"].indexing_domain)
        self.assertEqual(indexing_settings["parameter"].index_position, 1)
        self.assertEqual(
            indexing_settings["relationship_parameter"].parameter.values[0],
            from_database('{"type": "time_series", "data": [3, 2, 1]}'),
        )
        self.assertIsNone(indexing_settings["relationship_parameter"].indexing_domain)
        self.assertEqual(indexing_settings["relationship_parameter"].index_position, 1)

    def test_indexing_settings_from_dict(self):
        with TemporaryDirectory() as tmp_dir_name:
            time_pattern = TimePattern(["Mo", "Tu"], [42.0, -4.2])
            parameter = gdx.Parameter(["domain1"], [("Espoo",)], [time_pattern])
            original = {"parameter": gdx.IndexingSetting(parameter)}
            original["parameter"].indexing_domain = gdx.IndexingDomain(
                "indexing name", "indexing description", [("First",), ("Second",)], [False, True]
            )
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
            restored = gdx.indexing_settings_from_dict(settings_dict, database_map)
            database_map.connection.close()
        self.assertTrue(len(restored), 1)
        self.assertTrue("parameter" in restored)
        self.assertTrue(restored["parameter"].parameter.values, [time_pattern])
        self.assertTrue(restored["parameter"].indexing_domain.name, "indexing name")
        self.assertTrue(restored["parameter"].indexing_domain.description, "indexing description")
        self.assertTrue(restored["parameter"].indexing_domain.all_indexes, [("First",), ("Second",)])
        self.assertTrue(restored["parameter"].indexing_domain.pick_list, [False, True])
        self.assertTrue(restored["parameter"].index_position, 1)

    def test_update_indexing_settings_with_new_setting_overriding_old_one(self):
        time_series = TimeSeriesFixedResolution("2019-01-01T12:15", "1D", [3.3, 4.4], False, False)
        old_parameter = gdx.Parameter(["old_domain"], [("r1",)], [time_series])
        old_settings = {"old_parameter_name": gdx.IndexingSetting(old_parameter)}
        new_parameter = gdx.Parameter(["new_domain"], [("r1",)], [time_series])
        new_indexing_setting = gdx.IndexingSetting(new_parameter)
        new_settings = {"new_parameter_name": new_indexing_setting}
        settings = gdx.Settings(["new_domain"], [], {"new_domain": [("r1",)]})
        updated = gdx.update_indexing_settings(old_settings, new_settings, settings)
        self.assertEqual(len(updated), 1)
        self.assertTrue("new_parameter_name" in updated)
        self.assertEqual(updated["new_parameter_name"], new_indexing_setting)

    def test_update_indexing_settings_with_old_setting_overriding_new_one_when_additional_domains_present(self):
        time_series = TimeSeriesFixedResolution("2019-01-01T12:15", "1D", [3.3, 4.4], False, False)
        old_parameter = gdx.Parameter(["domain"], [("r1",)], [time_series])
        indexing_setting = gdx.IndexingSetting(old_parameter)
        indexing_setting.indexing_domain = gdx.IndexingDomain("indexing_domain", "", [("a",), ("b",)], [True, True])
        indexing_setting.index_position = 0
        old_settings = {"parameter_name": indexing_setting}
        new_parameter = gdx.Parameter(["domain"], [("r1",)], [time_series])
        new_settings = {"parameter_name": gdx.IndexingSetting(new_parameter)}
        settings = gdx.Settings(["domain"], [], {"domain": [("r1",)]})
        updated = gdx.update_indexing_settings(old_settings, new_settings, settings)
        self.assertEqual(len(updated), 1)
        self.assertTrue("parameter_name" in updated)
        self.assertEqual(updated["parameter_name"], indexing_setting)

    def test_update_indexing_settings_with_old_setting_overriding_new_one(self):
        time_series = TimeSeriesFixedResolution("2019-01-01T12:15", "1D", [3.3, 4.4], False, False)
        old_parameter = gdx.Parameter(["domain"], [("r1",)], [time_series])
        indexing_setting = gdx.IndexingSetting(old_parameter)
        indexing_setting.indexing_domain = gdx.IndexingDomain("indexing_domain", "", [("a",), ("b",)], [True, True])
        indexing_setting.index_position = 0
        old_settings = {"parameter_name": indexing_setting}
        new_parameter = gdx.Parameter(["domain"], [("r1",)], [time_series])
        new_settings = {"parameter_name": gdx.IndexingSetting(new_parameter)}
        settings = gdx.Settings(["domain"], [], {"domain": [("r1",)], "indexing_domain": [("a",), ("b",)]})
        updated = gdx.update_indexing_settings(old_settings, new_settings, settings)
        self.assertEqual(len(updated), 1)
        self.assertTrue("parameter_name" in updated)
        self.assertEqual(updated["parameter_name"], indexing_setting)

    def test_update_indexing_settings_new_settings_overriding_when_domain_has_changed(self):
        time_series = TimeSeriesFixedResolution("2019-01-01T12:15", "1D", [3.3, 4.4], False, False)
        old_parameter = gdx.Parameter(["domain"], [("r1",)], [time_series])
        old_indexing_setting = gdx.IndexingSetting(old_parameter)
        old_indexing_setting.indexing_domain = gdx.IndexingDomain("indexing_domain", "", [("a",), ("b",)], [True, True])
        old_indexing_setting.index_position = 0
        old_settings = {"parameter_name": old_indexing_setting}
        new_parameter = gdx.Parameter(["domain"], [("r1",)], [time_series])
        new_indexing_setting = gdx.IndexingSetting(new_parameter)
        new_settings = {"parameter_name": new_indexing_setting}
        settings = gdx.Settings(
            ["domain", "indexing_domain"], [], {"domain": [("r1",)], "indexing_domain": [("A",), ("B",)]}
        )
        updated = gdx.update_indexing_settings(old_settings, new_settings, settings)
        self.assertEqual(len(updated), 1)
        self.assertTrue("parameter_name" in updated)
        self.assertEqual(updated["parameter_name"], new_indexing_setting)

    def test_sort_indexing_domain_indexes(self):
        settings = gdx.Settings(
            ["domain2", "domain1"], [], {"domain1": [("a1",), ("a2",)], "domain2": [("b1",), ("b2",), ("b3",)]}
        )
        indexing_domain = gdx.IndexingDomain("domain2", "", [("b3",), ("b2",), ("b1",)], [False, True, True])
        time_series = TimeSeriesFixedResolution("2019-01-01T12:15", "1D", [3.3, 4.4], False, False)
        indexed_parameter = gdx.Parameter(["domain1"], [("a1",)], [time_series])
        indexing_setting = gdx.IndexingSetting(indexed_parameter)
        indexing_setting.indexing_domain = indexing_domain
        indexing_settings = {"parameter": indexing_setting}
        gdx.sort_indexing_domain_indexes(indexing_settings, settings)
        self.assertEqual(indexing_domain.indexes, [("b2",), ("b3",)])

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
            new_parameter.indexes,
            [
                ("a1", "b1", "parameter1"),
                ("a2", "b2", "parameter1"),
                ("a1", "b1", "parameter2"),
                ("a2", "b2", "parameter2"),
            ],
        )
        self.assertEqual(new_parameter.values, [1.1, 2.2, 3.3, 4.4])

    def test_merging_domain(self):
        setting = gdx.MergingSetting(
            ["parameter1", "parameter2"], "new_domain", "A new domain.", "set_name", ["domain1", "domain2"]
        )
        domain = gdx.merging_domain(setting)
        self.assertEqual(domain.name, "new_domain")
        self.assertEqual(domain.description, "A new domain.")
        self.assertEqual(domain.domain_names, [None])
        self.assertEqual(domain.records, [gdx.Record(("parameter1",)), gdx.Record(("parameter2",))])

    def test_update_merging_settings_after_parameter_addition(self):
        settings = gdx.Settings(["domain"], [], {})
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
        settings = gdx.Settings(["domain"], [], {})
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
        metadata = gdx.SetMetadata(gdx.ExportFlag.NON_EXPORTABLE, True)
        self.assertEqual(metadata.exportable, gdx.ExportFlag.NON_EXPORTABLE)
        self.assertEqual(metadata.is_additional, True)

    def test_SetMetadata_from_dict(self):
        original = gdx.SetMetadata(gdx.ExportFlag.NON_EXPORTABLE, True)
        meta_dict = original.to_dict()
        restored = gdx.SetMetadata.from_dict(meta_dict)
        self.assertEqual(restored.exportable, gdx.ExportFlag.NON_EXPORTABLE)
        self.assertEqual(restored.is_additional, True)

    @staticmethod
    def _object_parameter():
        with TemporaryDirectory() as tmp_dir_name:
            database_map = TestGdx._make_database_map(tmp_dir_name, "_object_parameter.sqlite")
            dbmanip.import_object_classes(database_map, ["domain"])
            dbmanip.import_objects(database_map, [("domain", "record")])
            dbmanip.import_object_parameters(database_map, [("domain", "parameter")])
            dbmanip.import_object_parameter_values(database_map, [("domain", "record", "parameter", -4.2)])
            object_parameters = database_map.object_parameter_value_list()
            parameter = gdx.Parameter.from_object_parameter(object_parameters[0])
            database_map.connection.close()
        return parameter

    @staticmethod
    def _relationship_parameter():
        with TemporaryDirectory() as tmp_dir_name:
            database_map = TestGdx._make_database_map(tmp_dir_name, "test_Parameter_from_relationship_parameter.sqlite")
            dbmanip.import_object_classes(database_map, ["domain1"])
            dbmanip.import_objects(database_map, [("domain1", "recordA")])
            dbmanip.import_object_classes(database_map, ["domain2"])
            dbmanip.import_objects(database_map, [("domain2", "recordB")])
            dbmanip.import_relationship_classes(database_map, [("set", ["domain1", "domain2"])])
            dbmanip.import_relationships(database_map, [("set", ["recordA", "recordB"])])
            dbmanip.import_relationship_parameters(database_map, [("set", "parameter")])
            dbmanip.import_relationship_parameter_values(
                database_map, [["set", ["recordA", "recordB"], "parameter", 3.14]]
            )
            relationship_parameters = database_map.relationship_parameter_value_list()
            parameter = gdx.Parameter.from_relationship_parameter(relationship_parameters[0])
            database_map.connection.close()
        return parameter

    @staticmethod
    def _make_settings(domain_exportable_flags=None, set_exportable_flags=None, global_parameters_domain_name=''):
        domain_names = ["domain1", "domain2"]
        set_names = ["set1", "set2", "set3"]
        records = {
            "domain1": [("a1",), ("a2",)],
            "domain2": [("b1",)],
            "set1": [("c1", "c2"), ("c3", "c4"), ("c5", "c6")],
            "set2": [("d1",)],
            "set3": [("e1",)],
        }
        return (
            domain_names,
            set_names,
            records,
            gdx.Settings(
                domain_names,
                set_names,
                records,
                domain_exportable_flags,
                set_exportable_flags,
                global_parameters_domain_name,
            ),
        )


if __name__ == '__main__':
    unittest.main()
