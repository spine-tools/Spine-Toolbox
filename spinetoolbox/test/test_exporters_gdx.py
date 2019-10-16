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
from spinedb_api.helpers import create_new_spine_database
from spinetoolbox.spine_io.exporters import gdx
from spinetoolbox.helpers import get_db_map


class TextExportersGdx(unittest.TestCase):
    class _MockObjectClass:
        description = "mock_object_class_description"
        name = "mock_object_class_name"

    class _MockRelationshipClass:
        object_class_name_list = 'mock_object_class_name'
        name = "mock_relationship_class_name"

    class _MockObject:
        name = "mock_object_name"

    class _MockRelationship:
        object_name_list = "mock_object_name"

    class _MockParameter:
        parameter_name = "mock_parameter_name"
        value = "2.3"

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

    def test_DomainSet_construction(self):
        domain = gdx.DomainSet(self._MockObjectClass())
        self.assertEqual(domain.description, self._MockObjectClass.description)
        self.assertEqual(domain.dimensions, 1)
        self.assertEqual(domain.name, self._MockObjectClass.name)
        self.assertEqual(domain.records, [])

    def test_Set_construction(self):
        regular_set = gdx.Set(self._MockRelationshipClass())
        self.assertEqual(regular_set.domain_names, ["mock_object_class_name"])
        self.assertEqual(regular_set.dimensions, 1)
        self.assertEqual(regular_set.name, self._MockRelationshipClass.name)
        self.assertEqual(regular_set.records, [])

    def test_Record_construction(self):
        record = gdx.Record(self._MockObject())
        self.assertEqual(record.keys, [self._MockObject.name])
        self.assertEqual(record.parameters, [])

    def test_Parameter_construction(self):
        parameter = gdx.Parameter(self._MockParameter())
        self.assertEqual(parameter.name, self._MockParameter.parameter_name)
        self.assertEqual(parameter.value, 2.3)

    @staticmethod
    def make_settings(domain_exportable_flags=None, set_exportable_flags=None, global_parameters_domain_name=''):
        domain_names = ["domain1", "domain2"]
        set_names = ["set1", "set2", "set3"]
        records = {
            "domain1": [["a1"], ["a2"]],
            "domain2": [["b1"]],
            "set1": [["c1", "c2"], ["c3", "c4"], ["c5", "c6"]],
            "set2": [["d1"]],
            "set3": [["e1"]],
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

    def test_Settings_construction(self):
        domain_names, set_names, records, settings = self.make_settings()
        self.assertEqual(settings.sorted_domain_names, domain_names)
        self.assertEqual(settings.domain_exportable_flags, 2 * [True])
        self.assertEqual(settings.sorted_set_names, set_names)
        self.assertEqual(settings.set_exportable_flags, 3 * [True])
        for keys in records:
            self.assertEqual(settings.sorted_record_key_lists(keys), records[keys])
        self.assertEqual(settings.global_parameters_domain_name, "")

    def test_Settings_serialization_to_dictionary(self):
        domain_flags = [False, True]
        set_flags = [False, True, False]
        global_domain_name = 'global parameter domain'
        domain_names, set_names, _, settings = self.make_settings(domain_flags, set_flags, global_domain_name)
        settings_as_dict = settings.to_dict()
        recovered = gdx.Settings.from_dict(settings_as_dict)
        self.assertEqual(recovered.sorted_domain_names, settings.sorted_domain_names)
        self.assertEqual(recovered.domain_exportable_flags, settings.domain_exportable_flags)
        self.assertEqual(recovered.sorted_set_names, settings.sorted_set_names)
        self.assertEqual(recovered.set_exportable_flags, settings.set_exportable_flags)
        for name in domain_names + set_names:
            self.assertEqual(recovered.sorted_record_key_lists(name), settings.sorted_record_key_lists(name))
        self.assertEqual(recovered.global_parameters_domain_name, settings.global_parameters_domain_name)

    @staticmethod
    def _make_database_map(dir_name, file_name):
        """Creates a Spine sqlite database in dir_name/file_name."""
        database_path = Path(dir_name).joinpath(file_name)
        database_url = 'sqlite:///' + str(database_path)
        create_new_spine_database(database_url)
        return get_db_map(database_url)

    def test_domains_are_read_correctly_form_database(self):
        with TemporaryDirectory() as tmp_dir_name:
            database_map = self._make_database_map(tmp_dir_name, "test_domains_are_read_correctly_form_database.sqlite")
            dbmanip.import_object_classes(database_map, ['domain'])
            dbmanip.import_objects(database_map, [('domain', 'record')])
            dbmanip.import_object_parameters(database_map, [('domain', 'parameter')])
            dbmanip.import_object_parameter_values(database_map, [('domain', 'record', 'parameter', -123.4)])
            domains = gdx.object_classes_to_domains(database_map)
            database_map.connection.close()
        self.assertEqual(len(domains), 1)
        domain = domains[0]
        self.assertEqual(domain.name, 'domain')
        self.assertEqual(domain.description, '')
        records = domain.records
        self.assertEqual(len(records), 1)
        record = records[0]
        self.assertEqual(record.keys, ['record'])
        parameters = record.parameters
        self.assertEqual(len(parameters), 1)
        parameter = parameters[0]
        self.assertEqual(parameter.name, 'parameter')
        self.assertEqual(parameter.value, -123.4)

    def test_sets_are_read_correctly_form_database(self):
        with TemporaryDirectory() as tmp_dir_name:
            database_map = self._make_database_map(tmp_dir_name, "test_sets_are_read_correctly_form_database.sqlite")
            dbmanip.import_object_classes(database_map, ['domain'])
            dbmanip.import_objects(database_map, [('domain', 'record')])
            dbmanip.import_relationship_classes(database_map, [('set', ['domain'])])
            dbmanip.import_relationships(database_map, [('set', ['record'])])
            dbmanip.import_relationship_parameters(database_map, [('set', 'parameter')])
            dbmanip.import_relationship_parameter_values(database_map, [['set', ['record'], 'parameter', 3.14]])
            sets = gdx.relationship_classes_to_sets(database_map)
            database_map.connection.close()
        self.assertEqual(len(sets), 1)
        set_item = sets[0]
        self.assertEqual(set_item.name, 'set')
        self.assertEqual(set_item.domain_names, ['domain'])
        self.assertEqual(set_item.dimensions, 1)
        self.assertEqual(len(set_item.records), 1)
        record = set_item.records[0]
        self.assertEqual(record.keys, ['record'])
        self.assertEqual(len(record.parameters), 1)
        parameter = record.parameters[0]
        self.assertEqual(parameter.name, 'parameter')
        self.assertEqual(parameter.value, 3.14)

    @unittest.skipIf(gdx.find_gams_directory() is None, "Could not find system GAMS directory.")
    def test_domains_to_gams(self):
        domain = gdx.DomainSet(self._MockObjectClass())
        record = gdx.Record(self._MockObject())
        parameter = gdx.Parameter(self._MockParameter())
        record.parameters.append(parameter)
        domain.records.append(record)
        gams_directory = gdx.find_gams_directory()
        with TemporaryDirectory() as temp_directory:
            path_to_gdx = Path(temp_directory).joinpath("test_domains_to_gams.gdx")
            with GdxFile(path_to_gdx, 'w', gams_directory) as gdx_file:
                gdx.domains_to_gams(gdx_file, [domain])
            with GdxFile(path_to_gdx, 'r', gams_directory) as gdx_file:
                self.assertEqual(len(gdx_file), 2)
                gams_set = gdx_file["mock_object_class_name"]
                self.assertEqual(len(gams_set.elements), 1)
                self.assertEqual(gams_set.elements[0], "mock_object_name")
                gams_parameter = gdx_file["mock_parameter_name"]
                self.assertEqual(len(gams_parameter.keys()), 1)
                for key, value in gams_parameter:
                    self.assertEqual(key, "mock_object_name")
                    self.assertEqual(value, 2.3)

    @unittest.skipIf(gdx.find_gams_directory() is None, "Could not find system GAMS directory.")
    def test_sets_to_gams(self):
        domain = gdx.DomainSet(self._MockObjectClass())
        record = gdx.Record(self._MockObject())
        domain.records.append(record)
        set_item = gdx.Set(self._MockRelationshipClass())
        record = gdx.Record(self._MockRelationship())
        set_item.records.append(record)
        parameter = gdx.Parameter(self._MockParameter())
        record.parameters.append(parameter)
        gams_directory = gdx.find_gams_directory()
        with TemporaryDirectory() as temp_directory:
            path_to_gdx = Path(temp_directory).joinpath("test_sets_to_gams.gdx")
            with GdxFile(path_to_gdx, 'w', gams_directory) as gdx_file:
                gdx.domains_to_gams(gdx_file, [domain])
                gdx.sets_to_gams(gdx_file, [set_item])
            with GdxFile(path_to_gdx, 'r', gams_directory) as gdx_file:
                self.assertEqual(len(gdx_file), 3)
                gams_set = gdx_file["mock_object_class_name"]
                self.assertEqual(len(gams_set.elements), 1)
                self.assertEqual(gams_set.elements[0], "mock_object_name")
                gams_set = gdx_file["mock_relationship_class_name"]
                self.assertEqual(len(gams_set.elements), 1)
                self.assertEqual(gams_set.elements[0], "mock_object_name")
                gams_parameter = gdx_file["mock_parameter_name"]
                self.assertEqual(len(gams_parameter.keys()), 1)
                for key, value in gams_parameter:
                    self.assertEqual(key, "mock_object_name")
                    self.assertEqual(value, 2.3)

    @unittest.skipIf(gdx.find_gams_directory() is None, "Could not find system GAMS directory.")
    def test_domain_parameters_to_gams(self):
        domain = gdx.DomainSet(self._MockObjectClass())
        record = gdx.Record(self._MockObject())
        domain.records.append(record)
        parameter = gdx.Parameter(self._MockParameter())
        record.parameters.append(parameter)
        gams_directory = gdx.find_gams_directory()
        with TemporaryDirectory() as temp_directory:
            path_to_gdx = Path(temp_directory).joinpath("test_domain_parameters_to_gams.gdx")
            with GdxFile(path_to_gdx, 'w', gams_directory) as gdx_file:
                gdx.domain_parameters_to_gams(gdx_file, domain)
            with GdxFile(path_to_gdx, 'r', gams_directory) as gdx_file:
                self.assertEqual(len(gdx_file), 1)
                gams_scalar = gdx_file["mock_parameter_name"]
                self.assertEqual(float(gams_scalar), 2.3)

    def test_filter_and_sort_sets(self):
        set_object = self._NamedObject
        sets = [set_object("set1"), set_object("set2"), set_object("set3")]
        set_names = ["set2", "set1", "set3"]
        set_flags = [True, True, False]
        filtered = gdx.filter_and_sort_sets(sets, set_names, set_flags)
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

    def text_extract_domain(self):
        domain_set = self._NamedObject
        domains = [domain_set("domain1")]
        domains, extracted = gdx.extract_domain(domains, "domain1")
        self.assertFalse(domains)
        self.assertEqual(extracted.name, "domain1")

    @unittest.skipIf(gdx.find_gams_directory() is None, "Could not find system GAMS directory.")
    def test_to_gdx_file_sorts_domains_and_sets_and_records_correctly(self):
        gams_directory = gdx.find_gams_directory()
        with TemporaryDirectory() as tmp_dir_name:
            database_map = self._make_database_map(tmp_dir_name, "test_to_gams_workspace.sqlite")
            dbmanip.import_object_classes(database_map, ['domain1', 'domain2'])
            dbmanip.import_objects(
                database_map, [('domain1', 'record11'), ('domain1', 'record12'), ('domain2', 'record21')]
            )
            dbmanip.import_relationship_classes(database_map, [('set1', ['domain1']), ('set2', ['domain1', 'domain2'])])
            dbmanip.import_relationships(
                database_map,
                [
                    ('set1', ['record12']),
                    ('set1', ['record11']),
                    ('set2', ['record12', 'record21']),
                    ('set2', ['record11', 'record21']),
                ],
            )
            sorted_domain_names = ['domain2', 'domain1']
            sorted_set_names = ['set2', 'set1']
            sorted_records = {
                'domain1': [['record12'], ['record11']],
                'domain2': [['record21']],
                'set1': [['record12'], ['record11']],
                'set2': [['record12', 'record21'], ['record11', 'record21']],
            }
            settings = gdx.Settings(sorted_domain_names, sorted_set_names, sorted_records)
            path_to_gdx = Path(tmp_dir_name).joinpath(
                "test_to_gdx_file_sorts_domains_and_sets_and_records_correctly.gdx"
            )
            gdx.to_gdx_file(database_map, path_to_gdx, settings, gams_directory)
            database_map.connection.close()
            with GdxFile(path_to_gdx, 'r', gams_directory) as gdx_file:
                self.assertEqual(len(gdx_file), 4)
                expected_symbol_names = ['domain2', 'domain1', 'set2', 'set1']
                for gams_symbol, expected_name in zip(gdx_file.keys(), expected_symbol_names):
                    self.assertEqual(gams_symbol, expected_name)
                gams_set = gdx_file['domain1']
                self.assertEqual(len(gams_set), 2)
                expected_records = ['record12', 'record11']
                for gams_record, expected_name in zip(gams_set, expected_records):
                    self.assertEqual(gams_record, expected_name)
                gams_set = gdx_file['domain2']
                self.assertEqual(len(gams_set), 1)
                self.assertEqual(gams_set.elements[0], 'record21')
                gams_set = gdx_file['set1']
                self.assertEqual(len(gams_set), 2)
                expected_records = ['record12', 'record11']
                for gams_record, expected_name in zip(gams_set, expected_records):
                    self.assertEqual(gams_record, expected_name)
                gams_set = gdx_file['set2']
                self.assertEqual(len(gams_set), 2)
                expected_records = [('record12', 'record21'), ('record11', 'record21')]
                for gams_record, expected_name in zip(gams_set, expected_records):
                    self.assertEqual(gams_record, expected_name)

    @unittest.skipIf(gdx.find_gams_directory() is None, "Could not find system GAMS directory.")
    def test_to_gdx_file_exports_global_parameters_only_not_the_corresponding_domain(self):
        gams_directory = gdx.find_gams_directory()
        with TemporaryDirectory() as tmp_dir_name:
            database_map = self._make_database_map(
                tmp_dir_name,
                "test_to_gams_workspace_exports_global_parameters_only_not_the_corresponding_domain.sqlite",
            )
            dbmanip.import_object_classes(database_map, ['global_domain'])
            dbmanip.import_objects(database_map, [('global_domain', 'record')])
            dbmanip.import_object_parameters(database_map, [('global_domain', 'global_parameter')])
            dbmanip.import_object_parameter_values(
                database_map, [('global_domain', 'record', 'global_parameter', -4.2)]
            )
            settings = gdx.make_settings(database_map)
            settings.global_parameters_domain_name = 'global_domain'
            path_to_gdx = Path(tmp_dir_name).joinpath(
                "test_to_gdx_file_sorts_domains_and_sets_and_records_correctly.gdx"
            )
            gdx.to_gdx_file(database_map, path_to_gdx, settings, gams_directory)
            database_map.connection.close()
            with GdxFile(path_to_gdx, 'r', gams_directory) as gdx_file:
                self.assertEqual(len(gdx_file), 1)
                gams_scalar = gdx_file['global_parameter']
                self.assertEqual(float(gams_scalar), -4.2)

    def test_make_settings(self):
        with TemporaryDirectory() as tmp_dir_name:
            database_map = self._make_database_map(tmp_dir_name, "test_make_settings.sqlite")
            dbmanip.import_object_classes(database_map, ['domain1', 'domain2'])
            dbmanip.import_objects(
                database_map, [('domain1', 'record11'), ('domain1', 'record12'), ('domain2', 'record21')]
            )
            dbmanip.import_relationship_classes(database_map, [('set1', ['domain1']), ('set2', ['domain1', 'domain2'])])
            dbmanip.import_relationships(
                database_map,
                [
                    ('set1', ['record12']),
                    ('set1', ['record11']),
                    ('set2', ['record12', 'record21']),
                    ('set2', ['record11', 'record21']),
                ],
            )
            settings = gdx.make_settings(database_map)
            database_map.connection.close()
        domain_names = settings.sorted_domain_names
        self.assertEqual(len(domain_names), 2)
        for name in domain_names:
            self.assertTrue(name in ['domain1', 'domain2'])
        self.assertEqual(settings.domain_exportable_flags, [True, True])
        set_names = settings.sorted_set_names
        self.assertEqual(len(set_names), 2)
        for name in set_names:
            self.assertTrue(name in ['set1', 'set2'])
        self.assertEqual(settings.set_exportable_flags, [True, True])
        record_keys = settings.sorted_record_key_lists('domain1')
        self.assertEqual(record_keys, [['record11'], ['record12']])
        record_keys = settings.sorted_record_key_lists('domain2')
        self.assertEqual(record_keys, [['record21']])
        record_keys = settings.sorted_record_key_lists('set1')
        self.assertEqual(record_keys, [['record12'], ['record11']])
        record_keys = settings.sorted_record_key_lists('set2')
        self.assertEqual(record_keys, [['record12', 'record21'], ['record11', 'record21']])

    def test_Settings_update_domains_and_domain_exportable_flags(self):
        base_settings = gdx.Settings(['a', 'b'], [], {}, [True, True], [], '')
        update_settings = gdx.Settings(['b', 'c'], [], {}, [False, False], [], '')
        base_settings.update(update_settings)
        self.assertEqual(base_settings.sorted_domain_names, ['b', 'c'])
        self.assertEqual(base_settings.domain_exportable_flags, [True, False])
        self.assertEqual(base_settings.sorted_set_names, [])
        self.assertEqual(base_settings.set_exportable_flags, [])
        self.assertEqual(base_settings.global_parameters_domain_name, '')

    def test_Settings_update_sets_and_set_exportable_flags(self):
        base_settings = gdx.Settings([], ['a', 'b'], {}, [], [True, True], '')
        update_settings = gdx.Settings([], ['b', 'c'], {}, [], [False, False], '')
        base_settings.update(update_settings)
        self.assertEqual(base_settings.sorted_domain_names, [])
        self.assertEqual(base_settings.domain_exportable_flags, [])
        self.assertEqual(base_settings.sorted_set_names, ['b', 'c'])
        self.assertEqual(base_settings.set_exportable_flags, [True, False])
        self.assertEqual(base_settings.global_parameters_domain_name, '')

    def test_Settings_update_global_parameters_domain_name(self):
        base_settings = gdx.Settings(['a', 'b'], [], {}, [True, False], [], 'b')
        update_settings = gdx.Settings(['b', 'c'], [], {}, [True, False], [], 'c')
        base_settings.update(update_settings)
        self.assertEqual(base_settings.sorted_domain_names, ['b', 'c'])
        self.assertEqual(base_settings.domain_exportable_flags, [False, False])
        self.assertEqual(base_settings.sorted_set_names, [])
        self.assertEqual(base_settings.set_exportable_flags, [])
        self.assertEqual(base_settings.global_parameters_domain_name, 'b')

    def test_Settings_update_records(self):
        base_settings = gdx.Settings(
            ['a', 'b'], ['c'], {'a': ['A'], 'b': ['B', 'BB'], 'c': ['C', 'CC']}, [True, True], [True], ''
        )
        update_settings = gdx.Settings(
            ['b', 'd'], ['c'], {'b': ['BB', 'BBB'], 'c': ['CC', 'CCC'], 'd': ['D']}, [False, False], [False], ''
        )
        base_settings.update(update_settings)
        self.assertEqual(base_settings.sorted_domain_names, ['b', 'd'])
        self.assertEqual(base_settings.domain_exportable_flags, [True, False])
        self.assertEqual(base_settings.sorted_set_names, ['c'])
        self.assertEqual(base_settings.set_exportable_flags, [True])
        self.assertEqual(base_settings.global_parameters_domain_name, '')
        self.assertEqual(base_settings.sorted_record_key_lists('b'), ['BB', 'BBB'])
        self.assertEqual(base_settings.sorted_record_key_lists('c'), ['CC', 'CCC'])
        self.assertEqual(base_settings.sorted_record_key_lists('d'), ['D'])


if __name__ == '__main__':
    unittest.main()
