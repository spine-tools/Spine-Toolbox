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
Unit tests for Excel import and export.

:author: P. Vennström (VTT)
:date:   12.11.2018
"""

import os
import tempfile
import unittest

from unittest import mock
from unittest.mock import MagicMock
from collections import namedtuple
from spinedb_api import (
    DiffDatabaseMapping,
    create_new_spine_database,
    TimeSeriesVariableResolution,
    to_database,
    TimePattern,
)
import numpy as np
from excel_import_export import (
    stack_list_of_tuples,
    unstack_list_of_tuples,
    validate_sheet,
    SheetData,
    read_parameter_sheet,
    read_json_sheet,
    merge_spine_xlsx_data,
    read_spine_xlsx,
    export_spine_database_to_xlsx,
    import_xlsx_to_db,
)


UUID_STR = 'f7f92ced-faff-4315-900e-704d2a786a65'
TEMP_EXCEL_FILENAME = os.path.join(tempfile.gettempdir(), UUID_STR + '-excel.xlsx')
TEMP_SQLITE_FILENAME = os.path.join(tempfile.gettempdir(), UUID_STR + '-first.sqlite')
TEMP_SQLITE_TEST_FILENAME = os.path.join(tempfile.gettempdir(), UUID_STR + '-second.sqlite')


class TestExcelIntegration(unittest.TestCase):
    def delete_temp_files(self):
        # remove temp files
        try:
            os.remove(TEMP_EXCEL_FILENAME)
        except OSError:
            pass
        try:
            os.remove(TEMP_SQLITE_FILENAME)
        except OSError:
            pass
        try:
            os.remove(TEMP_SQLITE_TEST_FILENAME)
        except OSError:
            pass

    def setUp(self):
        """Overridden method. Runs before each test."""
        # create a in memory database with objects, relationship, parameters and values
        create_new_spine_database('sqlite:///' + TEMP_SQLITE_FILENAME)
        db_map = DiffDatabaseMapping('sqlite:///' + TEMP_SQLITE_FILENAME, username='IntegrationTest', upgrade=True)

        # create empty database for loading excel into
        create_new_spine_database('sqlite:///' + TEMP_SQLITE_TEST_FILENAME)
        db_map_test = DiffDatabaseMapping(
            'sqlite:///' + TEMP_SQLITE_TEST_FILENAME, username='IntegrationTest', upgrade=True
        )

        # delete all object_classes to empty database
        oc = set(oc.id for oc in db_map_test.object_class_list().all())
        if oc:
            db_map_test.remove_items(object_class_ids=oc)
        db_map_test.commit_session('empty database')

        oc = set(oc.id for oc in db_map.object_class_list().all())
        if oc:
            db_map.remove_items(object_class_ids=oc)
        db_map.commit_session('empty database')

        # create object classes
        oc_1 = db_map.add_object_class(**{'name': 'object_class_1'})
        oc_2 = db_map.add_object_class(**{'name': 'object_class_2'})
        oc_3 = db_map.add_object_class(**{'name': 'object_class_3'})

        # create relationship classes
        relc1 = db_map.add_wide_relationship_class(
            **{'name': 'relationship_class', 'object_class_id_list': [oc_1.id, oc_2.id]}
        )
        relc2 = db_map.add_wide_relationship_class(
            **{'name': 'relationship_class2', 'object_class_id_list': [oc_1.id, oc_2.id]}
        )

        # create objects
        oc1_obj1 = db_map.add_object(**{'name': 'oc1_obj1', 'class_id': oc_1.id})
        oc1_obj2 = db_map.add_object(**{'name': 'oc1_obj2', 'class_id': oc_1.id})
        oc2_obj1 = db_map.add_object(**{'name': 'oc2_obj1', 'class_id': oc_2.id})
        oc2_obj2 = db_map.add_object(**{'name': 'oc2_obj2', 'class_id': oc_2.id})
        oc3_obj1 = db_map.add_object(**{'name': 'oc3_obj1', 'class_id': oc_3.id})

        # add relationships
        rel1 = db_map.add_wide_relationship(
            **{'name': 'rel1', 'class_id': relc1.id, 'object_id_list': [oc1_obj1.id, oc2_obj1.id]}
        )
        rel2 = db_map.add_wide_relationship(
            **{'name': 'rel2', 'class_id': relc1.id, 'object_id_list': [oc1_obj2.id, oc2_obj2.id]}
        )

        # create parameters
        p1 = db_map.add_parameter_definitions(*[{'name': 'parameter1', 'object_class_id': oc_1.id}])[0].first()
        p2 = db_map.add_parameter_definitions(*[{'name': 'parameter2', 'object_class_id': oc_1.id}])[0].first()
        p3 = db_map.add_parameter_definitions(*[{'name': 'parameter3', 'object_class_id': oc_2.id}])[0].first()
        p4 = db_map.add_parameter_definitions(*[{'name': 'parameter4', 'object_class_id': oc_2.id}])[0].first()
        p5 = db_map.add_parameter_definitions(*[{'name': 'parameter5', 'object_class_id': oc_3.id}])[0].first()
        p6 = db_map.add_parameter_definitions(*[{'name': 'parameter6', 'object_class_id': oc_3.id}])[0].first()
        rel_p1 = db_map.add_parameter_definitions(*[{'name': 'rel_parameter1', 'relationship_class_id': relc1.id}])[
            0
        ].first()
        rel_p2 = db_map.add_parameter_definitions(*[{'name': 'rel_parameter2', 'relationship_class_id': relc1.id}])[
            0
        ].first()
        rel_p3 = db_map.add_parameter_definitions(*[{'name': 'rel_parameter3', 'relationship_class_id': relc1.id}])[
            0
        ].first()
        rel_p4 = db_map.add_parameter_definitions(*[{'name': 'rel_parameter4', 'relationship_class_id': relc1.id}])[
            0
        ].first()

        # add parameter values
        db_map.add_parameter_value(**{'parameter_definition_id': p1.id, 'object_id': oc1_obj1.id, 'value': '0'})
        db_map.add_parameter_value(**{'parameter_definition_id': p2.id, 'object_id': oc1_obj2.id, 'value': '3.5'})
        db_map.add_parameter_value(
            **{'parameter_definition_id': p3.id, 'object_id': oc2_obj1.id, 'value': '[1, 2, 3, 4]'}
        )
        db_map.add_parameter_value(**{'parameter_definition_id': p4.id, 'object_id': oc2_obj2.id, 'value': '[5, 6, 7]'})
        db_map.add_parameter_value(**{'parameter_definition_id': rel_p1.id, 'relationship_id': rel1.id, 'value': '0'})
        db_map.add_parameter_value(**{'parameter_definition_id': rel_p2.id, 'relationship_id': rel2.id, 'value': '4'})
        db_map.add_parameter_value(
            **{'parameter_definition_id': rel_p3.id, 'relationship_id': rel1.id, 'value': '[5, 6, 7]'}
        )
        db_map.add_parameter_value(
            **{'parameter_definition_id': rel_p4.id, 'relationship_id': rel2.id, 'value': '[1, 2, 3, 4]'}
        )

        time = [np.datetime64('2005-02-25T00:00'), np.datetime64('2005-02-25T01:00'), np.datetime64('2005-02-25T02:00')]
        value = [1, 2, 3]
        ts_val = to_database(TimeSeriesVariableResolution(time, value, False, False))
        db_map.add_parameter_value(**{'parameter_definition_id': p5.id, 'object_id': oc3_obj1.id, 'value': ts_val})

        timepattern = ['m1', 'm2', 'm3']
        value = [1.1, 2.2, 3.3]
        ts_val = to_database(TimePattern(timepattern, value))
        db_map.add_parameter_value(**{'parameter_definition_id': p6.id, 'object_id': oc3_obj1.id, 'value': ts_val})

        # commit
        db_map.commit_session('test')

        self.db_map = db_map
        self.empty_db_map = db_map_test

    def tearDown(self):
        """Overridden method. Runs after each test.
        Use this to free resources after a test if needed.
        """
        self.delete_temp_files()

    def compare_dbs(self, db1, db2):
        # compare imported database with exported database
        # don't check ids since they might be different
        # object classes
        oc = db1.object_class_list().all()
        oc = {c.id: c.name for c in oc}
        oc_org = db2.object_class_list().all()
        oc_org = {c.id: c.name for c in oc_org}
        self.assertEqual(set(oc.values()), set(oc_org.values()), msg='Difference in objects classes')
        # objects
        ol = db1.object_list().all()
        ol_id = {o.id: o.name for o in ol}
        ol = {o.name: oc[o.class_id] for o in ol}
        ol_org = db2.object_list().all()
        ol_id_org = {o.id: o.name for o in ol_org}
        ol_org = {o.name: oc_org[o.class_id] for o in ol_org}
        self.assertEqual(ol, ol_org, msg='Difference in objects')
        # relationship classes
        rc = db1.query(db1.relationship_class_sq).all()
        rc = {c.id: (c.name, tuple(oc[o.object_class_id] for o in rc if o.name == c.name)) for c in rc}
        rc_org = db2.query(db2.relationship_class_sq).all()
        rc_org = {c.id: (c.name, tuple(oc_org[o.object_class_id] for o in rc_org if o.name == c.name)) for c in rc_org}
        self.assertEqual(set(rc.values()), set(rc_org.values()), msg='Difference in relationship classes')
        # relationships
        rel = db1.query(db1.relationship_sq).all()
        rel = {c.id: (rc[c.class_id][0], tuple(ol_id[o.object_id] for o in rel if o.id == c.id)) for c in rel}
        rel_org = db2.query(db2.relationship_sq).all()
        rel_org = {
            c.id: (rc_org[c.class_id][0], tuple(ol_id_org[o.object_id] for o in rel_org if o.id == c.id))
            for c in rel_org
        }
        self.assertEqual(set(rc.values()), set(rc_org.values()), msg='Difference in relationships')
        # parameters
        par = db1.parameter_definition_list().all()
        par = {
            p.id: (p.name, oc[p.object_class_id] if p.object_class_id else rc[p.relationship_class_id][0]) for p in par
        }
        par_org = db2.parameter_definition_list().all()
        par_org = {
            p.id: (p.name, oc_org[p.object_class_id] if p.object_class_id else rc_org[p.relationship_class_id][0])
            for p in par_org
        }
        self.assertEqual(set(par.values()), set(par_org.values()), msg='Difference in parameters')
        # parameters values
        parv = db1.parameter_value_list().all()
        parv = set(
            (
                par[p.parameter_definition_id][0],
                p.value,
                ol_id[p.object_id] if p.object_id else None,
                rel[p.relationship_id][1] if p.relationship_id else None,
            )
            for p in parv
        )
        parv_org = db2.parameter_value_list().all()
        parv_org = set(
            (
                par_org[p.parameter_definition_id][0],
                p.value,
                ol_id_org[p.object_id] if p.object_id else None,
                rel_org[p.relationship_id][1] if p.relationship_id else None,
            )
            for p in parv_org
        )
        self.assertEqual(parv, parv_org, msg='Difference in parameter values')

    def test_export_import(self):
        """Integration test exporting an excel and then importing it to a new database."""
        # export to excel
        export_spine_database_to_xlsx(self.db_map, TEMP_EXCEL_FILENAME)

        # import into empty database
        import_xlsx_to_db(self.empty_db_map, TEMP_EXCEL_FILENAME)
        self.empty_db_map.commit_session('Excel import')

        # compare dbs
        self.compare_dbs(self.empty_db_map, self.db_map)

    def test_import_to_existing_data(self):
        """Integration test importing data to a database with existing items"""
        # export to excel
        export_spine_database_to_xlsx(self.db_map, TEMP_EXCEL_FILENAME)

        # import into empty database
        import_xlsx_to_db(self.empty_db_map, TEMP_EXCEL_FILENAME)
        self.empty_db_map.commit_session('Excel import')

        # delete 1 object class
        self.db_map.remove_items(object_class_ids=set([1]))
        self.db_map.commit_session("Delete class")

        # reimport data
        import_xlsx_to_db(self.db_map, TEMP_EXCEL_FILENAME)
        self.db_map.commit_session("reimport data")

        # compare dbs
        self.compare_dbs(self.empty_db_map, self.db_map)


class TestExcelImport(unittest.TestCase):
    def setUp(self):
        """Overridden method. Runs before each test.
        """
        Cell = namedtuple('cell', ['value'])

        # mock data for relationship sheets
        ws_mock = {}
        ws_mock['A2'] = MagicMock(value='relationship')
        ws_mock['B2'] = MagicMock(value='parameter')
        ws_mock['C2'] = MagicMock(value='relationship_name')
        ws_mock['D2'] = MagicMock(value=2)
        ws_mock['A4:B4'] = [[MagicMock(value='object_class_name1'), MagicMock(value='object_class_name2')]]
        ws_mock[4] = [
            MagicMock(value='object_class_name1'),
            MagicMock(value='object_class_name2'),
            MagicMock(value='parameter1'),
            MagicMock(value='parameter2'),
        ]
        ws_mock['A'] = [1, 2, 3, 4, 5, 6]
        ws = MagicMock()
        ws.__getitem__.side_effect = ws_mock.__getitem__
        ws.title = 'title'
        mock_row_generator_data1 = [
            [],
            [],
            [],
            [
                Cell('object_class_name1'),
                Cell('object_class_name2'),
                Cell('parameter1'),
                Cell('parameter2'),
                Cell(None),
            ],
            [Cell('a_obj1'), Cell('b_obj1'), Cell(1), Cell('a'), Cell(None)],
            [Cell('a_obj2'), Cell('b_obj2'), Cell(2), Cell('b'), Cell(None)],
        ]
        ws.iter_rows.side_effect = lambda: iter(mock_row_generator_data1)
        self.ws_rel = ws
        self.data_parameter = ['parameter1', 'parameter2']
        self.data_class_rel = [['object_class_name1', 'object_class_name2']]
        self.data_rel = [['a_obj1', 'b_obj1', 1, 'a'], ['a_obj2', 'b_obj2', 2, 'b']]
        self.class_obj_rel = [['a_obj1', 'b_obj1'], ['a_obj2', 'b_obj2']]
        self.RelData = namedtuple('Data', ['parameter_type', 'object0', 'object1', 'parameter', 'value'])

        # mock data for object sheets
        ws_mock = {}
        ws_mock['A2'] = MagicMock(value='object')
        ws_mock['B2'] = MagicMock(value='parameter')
        ws_mock['C2'] = MagicMock(value='object_class_name')
        ws_mock[4] = [
            MagicMock(value='object_class_name'),
            MagicMock(value='parameter1'),
            MagicMock(value='parameter2'),
        ]
        ws_mock['A'] = [1, 2, 3, 4, 5, 6]
        ws = MagicMock()
        ws.__getitem__.side_effect = ws_mock.__getitem__
        ws.title = 'title'
        mock_row_generator_data2 = [
            [],
            [],
            [],
            [Cell('object_class_name'), Cell('parameter1'), Cell('parameter2')],
            [Cell('obj1'), Cell(1), Cell('a')],
            [Cell('obj2'), Cell(2), Cell('b')],
        ]
        ws.iter_rows.side_effect = lambda: iter(mock_row_generator_data2)
        self.ws_obj = ws
        self.data_parameter = ['parameter1', 'parameter2']
        self.data_class_obj = [['object_class_name']]
        self.data_obj = [['obj1', 1, 'a'], ['obj2', 2, 'b']]
        self.class_obj_obj = ['obj1', 'obj2']
        self.ObjData = namedtuple('Data', ['parameter_type', 'object0', 'parameter', 'value'])

        # mock data for json sheet object

        ws_mock = {}
        ws_mock['A2'] = MagicMock(value='object')
        ws_mock['B2'] = MagicMock(value='json array')
        ws_mock['C2'] = MagicMock(value='object_class_name')
        ws_mock['A4'] = MagicMock(value='object_class_name')
        ws_mock[4] = [MagicMock(value='object_class_name'), MagicMock(value='obj1'), MagicMock(value='obj2')]
        ws_mock['B'] = [
            MagicMock(value=None),
            MagicMock(value=None),
            MagicMock(value=None),
            MagicMock(value='obj1'),
            MagicMock(value='parameter1'),
            MagicMock(value=1),
            MagicMock(value=2),
            MagicMock(value=3),
        ]
        ws_mock['C'] = [
            MagicMock(value=None),
            MagicMock(value=None),
            MagicMock(value=None),
            MagicMock(value='obj2'),
            MagicMock(value='parameter2'),
            MagicMock(value=4),
            MagicMock(value=5),
            MagicMock(value=6),
        ]
        ws = MagicMock()
        ws.__getitem__.side_effect = ws_mock.__getitem__
        ws.title = 'title'
        mock_row_generator_data3 = [
            [],
            [],
            [],
            [Cell('object_class_name'), Cell('obj1'), Cell('obj2')],
            [Cell('json parameter'), Cell('parameter1'), Cell('parameter2')],
            [Cell(None), Cell(1), Cell(4)],
            [Cell(None), Cell(2), Cell(5)],
            [Cell(None), Cell(3), Cell(6)],
        ]
        ws.iter_rows.side_effect = lambda: iter(mock_row_generator_data3)
        self.ws_obj_json = ws

        # mock data for json sheets relationship
        ws_mock = {}
        ws_mock['A2'] = MagicMock(value='relationship')
        ws_mock['B2'] = MagicMock(value='json array')
        ws_mock['C2'] = MagicMock(value='relationship_name')
        ws_mock['D2'] = MagicMock(value=2)
        ws_mock['A4'] = MagicMock(value='object_class_name1')
        ws_mock['A5'] = MagicMock(value='object_class_name2')
        ws_mock['A4:A5'] = [[MagicMock(value='object_class_name1')], [MagicMock(value='object_class_name2')]]
        ws_mock[4] = [MagicMock(value='object_class_name1'), MagicMock(value='a_obj1'), MagicMock(value='a_obj2')]
        ws_mock['B'] = [
            MagicMock(value=None),
            MagicMock(value=None),
            MagicMock(value=None),
            MagicMock(value='a_obj1'),
            MagicMock(value='b_obj1'),
            MagicMock(value='parameter1'),
            MagicMock(value=1),
            MagicMock(value=2),
            MagicMock(value=3),
        ]
        ws_mock['C'] = [
            MagicMock(value=None),
            MagicMock(value=None),
            MagicMock(value=None),
            MagicMock(value='a_obj2'),
            MagicMock(value='b_obj2'),
            MagicMock(value='parameter2'),
            MagicMock(value=4),
            MagicMock(value=5),
            MagicMock(value=6),
        ]

        ws = MagicMock()
        ws.__getitem__.side_effect = ws_mock.__getitem__
        ws.title = 'title'
        mock_row_generator_data4 = [
            [],
            [],
            [],
            [Cell('object_class_name1'), Cell('a_obj1'), Cell('a_obj2'), Cell(None)],
            [Cell('object_class_name2'), Cell('b_obj1'), Cell('b_obj2'), Cell(None)],
            [Cell('json parameter'), Cell('parameter1'), Cell('parameter2'), Cell(None)],
            [Cell(None), Cell(1), Cell(4), Cell(None)],
            [Cell(None), Cell(2), Cell(5), Cell(None)],
            [Cell(None), Cell(3), Cell(6), Cell(None)],
        ]
        ws.iter_rows.side_effect = lambda: iter(mock_row_generator_data4)
        self.ws_rel_json = ws

    def tearDown(self):
        """Overridden method. Runs after each test.
        Use this to free resources after a test if needed.
        """

    def assertEqualSheetData(self, d1, d2):
        self.assertEqual(d1.sheet_name, d2.sheet_name)
        self.assertEqual(d1.class_name, d2.class_name)
        self.assertEqual(d1.object_classes, d2.object_classes)
        self.assertEqual(set(d1.parameters), set(d2.parameters))
        d1_pval = {p[1:-1]: p[-1] for p in d1.parameter_values}
        d2_pval = {p[1:-1]: p[-1] for p in d2.parameter_values}
        self.assertEqual(d1_pval, d2_pval)
        if d1.class_type == 'relationship':
            self.assertEqual(set(tuple(r) for r in d1.objects), set(tuple(r) for r in d2.objects))
        else:
            self.assertEqual(set(d1.objects), set(d2.objects))
        self.assertEqual(d1.class_type, d2.class_type)

    @mock.patch('excel_import_export.load_workbook')
    @mock.patch('excel_import_export.read_parameter_sheet')
    @mock.patch('excel_import_export.read_json_sheet')
    def test_read_spine_xlsx(self, mock_read_json_sheet, mock_read_parameter_sheet, mock_load_workbook):
        # workbook mock
        wb_dict = {
            'object': self.ws_obj,
            'object_json': self.ws_obj_json,
            'relationship': self.ws_rel,
            'relationship_json': self.ws_rel_json,
        }
        wb_mock = MagicMock()
        wb_mock.__getitem__.side_effect = wb_dict.__getitem__
        wb_mock.sheetnames = ['object', 'object_json', 'relationship', 'relationship_json']
        mock_load_workbook.side_effect = [wb_mock]

        # data for object parameter sheet
        parameter_values = [
            self.ObjData('value', 'obj1', 'parameter1', 1),
            self.ObjData('value', 'obj1', 'parameter2', 'a'),
            self.ObjData('value', 'obj2', 'parameter1', 2),
            self.ObjData('value', 'obj2', 'parameter2', 'b'),
        ]
        data_obj = SheetData(
            'object',
            'object_class_name',
            self.data_class_obj[0],
            self.data_parameter,
            parameter_values,
            self.class_obj_obj,
            'object',
        )
        # data for object json sheet
        parameter_values = [
            self.ObjData('json', 'obj1', 'parameter1', [1, 2, 3]),
            self.ObjData('json', 'obj2', 'parameter2', [4, 5, 6]),
        ]
        data_obj_json = SheetData(
            'object_json',
            'object_class_name',
            self.data_class_obj[0],
            list(set(self.data_parameter)),
            parameter_values,
            [],
            'object',
        )
        # data for relationship parameter sheet
        parameter_values = [
            self.RelData('value', 'a_obj1', 'b_obj1', 'parameter1', 1),
            self.RelData('value', 'a_obj1', 'b_obj1', 'parameter2', 'a'),
            self.RelData('value', 'a_obj2', 'b_obj2', 'parameter1', 2),
            self.RelData('value', 'a_obj2', 'b_obj2', 'parameter2', 'b'),
        ]
        data_rel = SheetData(
            'relationship',
            'relationship_name',
            self.data_class_rel[0],
            self.data_parameter,
            parameter_values,
            self.class_obj_rel,
            'relationship',
        )
        # data for relationship json sheet
        parameter_values = [
            self.RelData('json', 'a_obj1', 'b_obj1', 'parameter1', [1, 2, 3]),
            self.RelData('json', 'a_obj2', 'b_obj2', 'parameter2', [4, 5, 6]),
        ]
        data_rel_json = SheetData(
            'relationship_json',
            'relationship_name',
            self.data_class_rel[0],
            list(set(self.data_parameter)),
            parameter_values,
            [],
            'relationship',
        )

        mock_read_json_sheet.side_effect = [data_obj_json, data_rel_json]
        mock_read_parameter_sheet.side_effect = [data_obj, data_rel]

        obj_data, rel_data, error_log = read_spine_xlsx('filepath_mocked_away')

        # only test that lenght is correct since all other functions is tested elsewhere
        self.assertTrue(len(error_log) == 0)
        self.assertTrue(len(obj_data) == 1)
        self.assertTrue(len(rel_data) == 1)

    def test_merge_spine_xlsx_data(self):
        """Test merging array of SheetData"""
        parameter_values1 = [
            self.RelData('value', 'a_obj1', 'b_obj1', 'parameter1', 1),
            self.RelData('value', 'a_obj2', 'b_obj2', 'parameter2', 2),
        ]
        parameter_values2 = [
            self.RelData('value', 'a_obj1', 'b_obj1', 'parameter1', 1),
            self.RelData('value', 'a_obj3', 'b_obj3', 'parameter3', 3),
        ]
        data1 = SheetData(
            'title',
            'relationship_name',
            self.data_class_rel[0],
            ['parameter1', 'parameter2'],
            parameter_values1,
            [['a_obj1', 'b_obj1'], ['a_obj2', 'b_obj2']],
            'relationship',
        )
        data2 = SheetData(
            'title',
            'relationship_name',
            self.data_class_rel[0],
            ['parameter1', 'parameter3'],
            parameter_values2,
            [['a_obj1', 'b_obj1'], ['a_obj3', 'b_obj3']],
            'relationship',
        )

        parameter_values3 = parameter_values1 + parameter_values2
        valid_data = SheetData(
            'title',
            'relationship_name',
            self.data_class_rel[0],
            ['parameter1', 'parameter2', 'parameter3'],
            parameter_values3,
            [['a_obj1', 'b_obj1'], ['a_obj2', 'b_obj2'], ['a_obj3', 'b_obj3']],
            'relationship',
        )

        test_data, test_log = merge_spine_xlsx_data([data1, data2])

        self.assertEqual(len(test_log), 0)
        self.assertEqual(len(test_data), 1)
        self.assertEqualSheetData(test_data[0], valid_data)

    def test_merge_spine_xlsx_data_diffent_obj_class_names(self):
        """Test merging array of SheetData with different object class names, keep only first SheetData"""
        parameter_values1 = [
            self.RelData('value', 'a_obj1', 'b_obj1', 'parameter1', 1),
            self.RelData('value', 'a_obj2', 'b_obj2', 'parameter2', 2),
        ]
        parameter_values2 = [
            self.RelData('value', 'a_obj1', 'b_obj1', 'parameter1', 1),
            self.RelData('value', 'a_obj3', 'b_obj3', 'parameter3', 2),
        ]
        data1 = SheetData(
            'title',
            'relationship_name',
            self.data_class_rel[0],
            ['parameter1', 'parameter2'],
            parameter_values1,
            [['a_obj1', 'b_obj1'], ['a_obj2', 'b_obj2']],
            'relationship',
        )
        data2 = SheetData(
            'title',
            'relationship_name',
            ['object_class_name', 'wrong_name'],
            ['parameter1', 'parameter3'],
            parameter_values2,
            [['a_obj1', 'b_obj1'], ['a_obj3', 'b_obj3']],
            'relationship',
        )

        test_data, test_log = merge_spine_xlsx_data([data1, data2])

        self.assertEqual(len(test_log), 1)
        self.assertEqual(len(test_data), 1)
        self.assertEqualSheetData(test_data[0], data1)

    def test_read_json_sheet_all_valid_relationship(self):
        """Test reading a sheet with object parameter"""
        ws = self.ws_rel_json
        parameter_values = [
            self.RelData('json', 'a_obj1', 'b_obj1', 'parameter1', [1, 2, 3]),
            self.RelData('json', 'a_obj2', 'b_obj2', 'parameter2', [4, 5, 6]),
        ]
        test_data = SheetData(
            'title',
            'relationship_name',
            self.data_class_rel[0],
            list(set(self.data_parameter)),
            parameter_values,
            [],
            'relationship',
        )

        with mock.patch('excel_import_export.read_2d') as mock_read_2d:
            mock_read_2d.side_effect = self.data_class_rel
            out_data = read_json_sheet(ws, 'relationship')
        self.assertEqualSheetData(test_data, out_data)

    def test_read_json_sheet_all_valid_object(self):
        """Test reading a sheet with object parameter"""
        ws = self.ws_obj_json
        parameter_values = [
            self.ObjData('json', 'obj1', 'parameter1', [1, 2, 3]),
            self.ObjData('json', 'obj2', 'parameter2', [4, 5, 6]),
        ]
        test_data = SheetData(
            'title',
            'object_class_name',
            self.data_class_obj[0],
            list(set(self.data_parameter)),
            parameter_values,
            [],
            'object',
        )

        with mock.patch('excel_import_export.read_2d') as mock_read_2d:
            mock_read_2d.side_effect = self.data_class_obj
            out_data = read_json_sheet(ws, 'object')
        self.assertEqualSheetData(test_data, out_data)

    def test_read_parameter_sheet_all_valid_object(self):
        """Test reading a sheet with object parameter"""
        ws = self.ws_obj
        parameter_values = [
            self.ObjData('value', 'obj1', 'parameter1', 1),
            self.ObjData('value', 'obj1', 'parameter2', 'a'),
            self.ObjData('value', 'obj2', 'parameter1', 2),
            self.ObjData('value', 'obj2', 'parameter2', 'b'),
        ]
        test_data = SheetData(
            'title',
            'object_class_name',
            self.data_class_obj[0],
            self.data_parameter,
            parameter_values,
            self.class_obj_obj,
            'object',
        )

        with mock.patch('excel_import_export.read_2d') as mock_read_2d:
            mock_read_2d.side_effect = [self.data_class_obj, self.data_obj]
            out_data = read_parameter_sheet(ws)
        self.assertEqualSheetData(test_data, out_data)

    def test_read_parameter_sheet_all_valid_relationship(self):
        """Test reading a sheet with object parameter"""
        ws = self.ws_rel
        parameter_values = [
            self.RelData('value', 'a_obj1', 'b_obj1', 'parameter1', 1),
            self.RelData('value', 'a_obj1', 'b_obj1', 'parameter2', 'a'),
            self.RelData('value', 'a_obj2', 'b_obj2', 'parameter1', 2),
            self.RelData('value', 'a_obj2', 'b_obj2', 'parameter2', 'b'),
        ]
        test_data = SheetData(
            'title',
            'relationship_name',
            self.data_class_rel[0],
            self.data_parameter,
            parameter_values,
            self.class_obj_rel,
            'relationship',
        )

        with mock.patch('excel_import_export.read_2d') as mock_read_2d:
            mock_read_2d.side_effect = [self.data_class_rel, self.data_rel]
            out_data = read_parameter_sheet(ws)
        self.assertEqualSheetData(test_data, out_data)

    def test_read_parameter_sheet_with_None_containing_rels(self):
        """Test reading a sheet where one relationship contains a None value
        to make sure invalid rows are not read"""
        ws = self.ws_rel
        # make last row in data invalid
        self.data_rel[1][0] = None
        self.class_obj_rel.pop(1)
        Cell = namedtuple('cell', ['value'])
        data = list(ws.iter_rows())
        data.pop(-1)
        data.append([Cell(None), Cell('b_obj2'), Cell(2), Cell('b'), Cell(None)])
        ws.iter_rows.side_effect = lambda: iter(data)

        parameter_values = [
            self.RelData('value', 'a_obj1', 'b_obj1', 'parameter1', 1),
            self.RelData('value', 'a_obj1', 'b_obj1', 'parameter2', 'a'),
        ]
        test_data = SheetData(
            'title',
            'relationship_name',
            self.data_class_rel[0],
            self.data_parameter,
            parameter_values,
            self.class_obj_rel,
            'relationship',
        )

        with mock.patch('excel_import_export.read_2d') as mock_read_2d:
            mock_read_2d.side_effect = [self.data_class_rel, self.data_rel]
            out_data = read_parameter_sheet(ws)
        self.assertEqualSheetData(test_data, out_data)

    def test_read_parameter_sheet_with_None_parameter_values(self):
        """Test reading a sheet with None values in parameter value cells"""
        ws = self.ws_obj
        self.data_obj[1][1] = None
        Cell = namedtuple('cell', ['value'])
        data = list(ws.iter_rows())
        data[5][1] = Cell(None)
        ws.iter_rows.side_effect = lambda: iter(data)

        parameter_values = [
            self.ObjData('value', 'obj1', 'parameter1', 1),
            self.ObjData('value', 'obj1', 'parameter2', 'a'),
            self.ObjData('value', 'obj2', 'parameter2', 'b'),
        ]
        test_data = SheetData(
            'title',
            'object_class_name',
            self.data_class_obj[0],
            self.data_parameter,
            parameter_values,
            self.class_obj_obj,
            'object',
        )

        with mock.patch('excel_import_export.read_2d') as mock_read_2d:
            mock_read_2d.side_effect = [self.data_class_obj, self.data_obj]
            out_data = read_parameter_sheet(ws)
        self.assertEqualSheetData(test_data, out_data)

    def test_validate_sheet_valid_relationship(self):
        """Test that a valid sheet with relationship as sheet_type will return true"""
        with mock.patch('excel_import_export.read_2d') as mock_read_2d:
            mock_read_2d.return_value = [['obj_class1', 'obj_class2']]
            ws_mock = self.ws_rel
            self.assertTrue(validate_sheet(ws_mock))
            # check that validation is case insensitive
            ws_mock['A2'].value = 'RelatIonShip'
            ws_mock['B2'].value = 'paRameTer'
            self.assertTrue(validate_sheet(ws_mock))
            # check json array as Data type
            ws_mock['B2'].value = 'json array'
            mock_read_2d.return_value = [['obj_class1'], ['obj_class2']]
            self.assertTrue(validate_sheet(ws_mock))

    def test_validate_sheet_invalid_relationship(self):
        """Test that an invalid sheet with relationship as sheet_type will return false"""
        ws_mock = self.ws_rel
        # check invalid type
        with mock.patch('excel_import_export.read_2d') as mock_read_2d:
            mock_read_2d.return_value = [['obj_class1', 'obj_class2']]
            # wrong relationship name
            ws_mock['C2'].value = ''
            self.assertFalse(validate_sheet(ws_mock))
            ws_mock['C2'].value = None
            self.assertFalse(validate_sheet(ws_mock))
            ws_mock['C2'].value = 3
            self.assertFalse(validate_sheet(ws_mock))
            # wrong number of relationship classes
            ws_mock['C2'].value = 'relationship_name'
            mock_read_2d.return_value = [['obj_class1', None]]
            self.assertFalse(validate_sheet(ws_mock))
            mock_read_2d.return_value = [['obj_class1', 1]]
            self.assertFalse(validate_sheet(ws_mock))
            mock_read_2d.return_value = [['obj_class1', '']]
            self.assertFalse(validate_sheet(ws_mock))
            # wrong number of relationship supplied
            mock_read_2d.return_value = [['obj_class1', 'obj_class2']]
            ws_mock['D2'].value = 0
            self.assertFalse(validate_sheet(ws_mock))
            ws_mock['D2'].value = 'abc'
            self.assertFalse(validate_sheet(ws_mock))
            ws_mock['D2'].value = 1
            self.assertFalse(validate_sheet(ws_mock))

    def test_validate_sheet_valid_object(self):
        """Test that a valid sheet with object as sheet_type will return true"""
        ws_mock = self.ws_obj
        self.assertTrue(validate_sheet(ws_mock))
        # check json array as Data type
        ws_mock['B2'].value = 'json array'
        self.assertTrue(validate_sheet(ws_mock))
        # check that validation is case insensitive
        ws_mock['A2'].value = 'oBjeCt'
        ws_mock['B2'].value = 'paRameTer'
        self.assertTrue(validate_sheet(ws_mock))

    def test_validate_sheet_invalid_object(self):
        """Test that an invalid sheet with object as sheet_type will return false"""
        ws_mock = self.ws_obj
        # check invalid type
        ws_mock['A2'].value = 1
        self.assertFalse(validate_sheet(ws_mock))
        ws_mock['A2'].value = 'object'
        ws_mock['B2'].value = 4
        ws_mock['C2'].value = 'some_name'
        self.assertFalse(validate_sheet(ws_mock))
        ws_mock['A2'].value = 'object'
        ws_mock['B2'].value = 'parameter'
        ws_mock['C2'].value = 6
        # check invalid name
        ws_mock['A2'].value = 'invalid_sheet_type'
        ws_mock['B2'].value = 'parameter'
        ws_mock['C2'].value = 'some_name'
        self.assertFalse(validate_sheet(ws_mock))
        ws_mock['A2'].value = 'object'
        ws_mock['B2'].value = 'invalid_parameter_type'
        ws_mock['C2'].value = 'some_name'
        self.assertFalse(validate_sheet(ws_mock))
        # check invlad object name
        ws_mock['A2'].value = 'object'
        ws_mock['B2'].value = 'parameter'
        ws_mock['C2'].value = ''
        self.assertFalse(validate_sheet(ws_mock))
        # check empty values
        ws_mock['A2'].value = None
        ws_mock['B2'].value = 'parameter'
        ws_mock['C2'].value = 'some_name'
        self.assertFalse(validate_sheet(ws_mock))
        ws_mock['A2'].value = 'object'
        ws_mock['B2'].value = None
        ws_mock['C2'].value = 'some_name'
        self.assertFalse(validate_sheet(ws_mock))
        ws_mock['A2'].value = 'object'
        ws_mock['B2'].value = 'parameter'
        ws_mock['C2'].value = None
        self.assertFalse(validate_sheet(ws_mock))


class TestStackUnstack(unittest.TestCase):
    def test_stack_list_of_tuples(self):
        """Test transformation of pivoted table into a stacked table"""

        fieldnames = ["col1", "col2", "parameter", "value"]
        TestDataTuple = namedtuple("Data", fieldnames)
        headers = ["col1", "col2", "pivot_col1", "pivot_col2"]
        key_cols = [0, 1]
        value_cols = [2, 3]
        data_in = [
            ["col1_v1", "col2_v1", "pivot_col1_v1", "pivot_col2_v1"],
            ["col1_v2", "col2_v2", "pivot_col1_v2", "pivot_col2_v2"],
            ["col1_v3", "col2_v3", "pivot_col1_v3", "pivot_col2_v3"],
        ]
        data_out = sorted(
            [
                TestDataTuple("col1_v1", "col2_v1", "pivot_col1", "pivot_col1_v1"),
                TestDataTuple("col1_v2", "col2_v2", "pivot_col1", "pivot_col1_v2"),
                TestDataTuple("col1_v1", "col2_v1", "pivot_col2", "pivot_col2_v1"),
                TestDataTuple("col1_v2", "col2_v2", "pivot_col2", "pivot_col2_v2"),
                TestDataTuple("col1_v3", "col2_v3", "pivot_col1", "pivot_col1_v3"),
                TestDataTuple("col1_v3", "col2_v3", "pivot_col2", "pivot_col2_v3"),
            ]
        )

        test_data_out = sorted(stack_list_of_tuples(data_in, headers, key_cols, value_cols))

        for d, t in zip(data_out, test_data_out):
            for f in fieldnames:
                self.assertEqual(getattr(d, f), getattr(t, f))
        # self.assertEqual(data_out, test_data_out)

    def test_unstack_list_of_tuples(self):
        """Test transformation of unpivoted table into a pivoted table"""

        fieldnames = ["col1", "col2", "pivot_col1", "pivot_col2"]
        headers = ["col1", "col2", "parameter", "value"]
        key_cols = [0, 1]
        value_name_col = 2
        value_col = 3
        data_in = [
            ["col1_v1", "col2_v1", "pivot_col1", "pivot_col1_v1"],
            ["col1_v2", "col2_v2", "pivot_col1", "pivot_col1_v2"],
            ["col1_v1", "col2_v1", "pivot_col2", "pivot_col2_v1"],
            ["col1_v2", "col2_v2", "pivot_col2", "pivot_col2_v2"],
            ["col1_v3", "col2_v3", "pivot_col2", "pivot_col2_v3"],
        ]

        data_out = [
            ["col1_v1", "col2_v1", "pivot_col1_v1", "pivot_col2_v1"],
            ["col1_v2", "col2_v2", "pivot_col1_v2", "pivot_col2_v2"],
            ["col1_v3", "col2_v3", None, "pivot_col2_v3"],
        ]

        test_data_out, new_headers = unstack_list_of_tuples(data_in, headers, key_cols, value_name_col, value_col)

        self.assertEqual(test_data_out, data_out)
        self.assertEqual(new_headers, fieldnames)

    def test_unstack_list_of_tuples_with_bad_names(self):
        """Test transformation of unpivoted table into a pivoted table when column to pivot has name not supported by namedtuple"""

        fieldnames = ["col1", "col2", "pivot col1", "pivot col2"]
        headers = ["col1", "col2", "parameter", "value"]
        key_cols = [0, 1]
        value_name_col = 2
        value_col = 3
        data_in = [
            ["col1_v1", "col2_v1", "pivot col1", "pivot_col1_v1"],
            ["col1_v2", "col2_v2", "pivot col1", "pivot_col1_v2"],
            ["col1_v1", "col2_v1", "pivot col2", "pivot_col2_v1"],
            ["col1_v2", "col2_v2", "pivot col2", "pivot_col2_v2"],
            ["col1_v3", "col2_v3", "pivot col2", "pivot_col2_v3"],
        ]

        data_out = [
            ["col1_v1", "col2_v1", "pivot_col1_v1", "pivot_col2_v1"],
            ["col1_v2", "col2_v2", "pivot_col1_v2", "pivot_col2_v2"],
            ["col1_v3", "col2_v3", None, "pivot_col2_v3"],
        ]

        test_data_out, new_headers = unstack_list_of_tuples(data_in, headers, key_cols, value_name_col, value_col)

        self.assertEqual(test_data_out, data_out)
        self.assertEqual(new_headers, fieldnames)

    # TODO: add functionality to function
    def test_unstack_list_of_tuples_multiple_pivot_cols(self):
        """Test transformation of unpivoted table into a pivoted table with multiple pivot columns"""
        headers = ["col1", "col2", "parameter", "value"]
        key_cols = [0]
        value_name_col = [1, 2]
        value_col = 3
        data_in = [
            ["col1_v1", "col2_v1", "pivot_col1", "pivot_col1_v1"],
            ["col1_v2", "col2_v2", "pivot_col1", "pivot_col1_v2"],
            ["col1_v1", "col2_v1", "pivot_col2", "pivot_col2_v1"],
            ["col1_v2", "col2_v2", "pivot_col2", "pivot_col2_v2"],
            ["col1_v3", "col2_v3", "pivot_col2", "pivot_col2_v3"],
        ]

        headers_out = [
            "col1",
            ("col2_v1", "pivot_col1"),
            ("col2_v1", "pivot_col2"),
            ("col2_v2", "pivot_col1"),
            ("col2_v2", "pivot_col2"),
            ("col2_v3", "pivot_col2"),
        ]
        data_out = [
            ["col1_v1", "pivot_col1_v1", "pivot_col2_v1", None, None, None],
            ["col1_v2", None, None, "pivot_col1_v2", "pivot_col2_v2", None],
            ["col1_v3", None, None, None, None, "pivot_col2_v3"],
        ]

        test_data_out, test_header_out = unstack_list_of_tuples(data_in, headers, key_cols, value_name_col, value_col)

        self.assertEqual(data_out, test_data_out)
        self.assertEqual(headers_out, test_header_out)


if __name__ == '__main__':
    unittest.main()
