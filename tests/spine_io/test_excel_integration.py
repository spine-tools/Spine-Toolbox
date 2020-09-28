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
Integration tests for Excel import and export.

:author: P. Vennström (VTT), A. Soininen (VTT)
:date:   31.1.2020
"""

import os
from pathlib import PurePath
from tempfile import TemporaryDirectory
import unittest
import numpy as np
from spinedb_api import (
    create_new_spine_database,
    DiffDatabaseMapping,
    import_data,
    TimePattern,
    TimeSeriesVariableResolution,
    to_database,
)
from spine_items.spine_io.exporters.excel import export_spine_database_to_xlsx
from spine_items.spine_io.importers.excel_reader import get_mapped_data_from_xlsx

_TEMP_EXCEL_FILENAME = 'excel.xlsx'
_TEMP_SQLITE_FILENAME = 'first.sqlite'
_TEMP_SQLITE_TEST_FILENAME = 'second.sqlite'


class TestExcelIntegration(unittest.TestCase):
    @staticmethod
    def _sqlite_url(file_name, directory):
        return "sqlite:///" + os.path.abspath(os.path.join(directory, file_name))

    @staticmethod
    def _create_database(directory):
        """Creates a database with objects, relationship, parameters and values."""
        url = TestExcelIntegration._sqlite_url(_TEMP_SQLITE_FILENAME, directory)
        create_new_spine_database(url)
        db_map = DiffDatabaseMapping(url, username='IntegrationTest', upgrade=True)

        # create empty database for loading excel into
        url = TestExcelIntegration._sqlite_url(_TEMP_SQLITE_TEST_FILENAME, directory)
        create_new_spine_database(url)
        db_map_test = DiffDatabaseMapping(url, username='IntegrationTest', upgrade=True)

        # delete all object_classes to empty database
        oc = set(oc.id for oc in db_map_test.object_class_list().all())
        if oc:
            db_map_test.cascade_remove_items(object_class_ids=oc)
            db_map_test.commit_session('empty database')

        oc = set(oc.id for oc in db_map.object_class_list().all())
        if oc:
            db_map.cascade_remove_items(object_class_ids=oc)
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
        p1 = db_map.add_parameter_definition(**{'name': 'parameter1', 'object_class_id': oc_1.id})
        p2 = db_map.add_parameter_definition(**{'name': 'parameter2', 'object_class_id': oc_1.id})
        p3 = db_map.add_parameter_definition(**{'name': 'parameter3', 'object_class_id': oc_2.id})
        p4 = db_map.add_parameter_definition(**{'name': 'parameter4', 'object_class_id': oc_2.id})
        p5 = db_map.add_parameter_definition(**{'name': 'parameter5', 'object_class_id': oc_3.id})
        p6 = db_map.add_parameter_definition(**{'name': 'parameter6', 'object_class_id': oc_3.id})
        rel_p1 = db_map.add_parameter_definition(**{'name': 'rel_parameter1', 'relationship_class_id': relc1.id})
        rel_p2 = db_map.add_parameter_definition(**{'name': 'rel_parameter2', 'relationship_class_id': relc1.id})
        rel_p3 = db_map.add_parameter_definition(**{'name': 'rel_parameter3', 'relationship_class_id': relc1.id})
        rel_p4 = db_map.add_parameter_definition(**{'name': 'rel_parameter4', 'relationship_class_id': relc1.id})

        # add parameter values
        db_map.add_parameter_value(
            **{
                'parameter_definition_id': p1.id,
                'object_id': oc1_obj1.id,
                'object_class_id': oc_1.id,
                'value': '0',
                "alternative_id": 1,
            }
        )
        db_map.add_parameter_value(
            **{
                'parameter_definition_id': p2.id,
                'object_id': oc1_obj2.id,
                'object_class_id': oc_1.id,
                'value': '3.5',
                "alternative_id": 1,
            }
        )
        db_map.add_parameter_value(
            **{
                'parameter_definition_id': p3.id,
                'object_id': oc2_obj1.id,
                'object_class_id': oc_2.id,
                'value': '[1, 2, 3, 4]',
                "alternative_id": 1,
            }
        )
        db_map.add_parameter_value(
            **{
                'parameter_definition_id': p4.id,
                'object_id': oc2_obj2.id,
                'object_class_id': oc_2.id,
                'value': '[5, 6, 7]',
                "alternative_id": 1,
            }
        )
        db_map.add_parameter_value(
            **{
                'parameter_definition_id': rel_p1.id,
                'relationship_id': rel1.id,
                'relationship_class_id': relc1.id,
                'value': '0',
                "alternative_id": 1,
            }
        )
        db_map.add_parameter_value(
            **{
                'parameter_definition_id': rel_p2.id,
                'relationship_id': rel2.id,
                'relationship_class_id': relc1.id,
                'value': '4',
                "alternative_id": 1,
            }
        )
        db_map.add_parameter_value(
            **{
                'parameter_definition_id': rel_p3.id,
                'relationship_id': rel1.id,
                'relationship_class_id': relc1.id,
                'value': '[5, 6, 7]',
                "alternative_id": 1,
            }
        )
        db_map.add_parameter_value(
            **{
                'parameter_definition_id': rel_p4.id,
                'relationship_id': rel2.id,
                'relationship_class_id': relc1.id,
                'value': '[1, 2, 3, 4]',
                "alternative_id": 1,
            }
        )

        time = [np.datetime64('2005-02-25T00:00'), np.datetime64('2005-02-25T01:00'), np.datetime64('2005-02-25T02:00')]
        value = [1, 2, 3]
        ts_val = to_database(TimeSeriesVariableResolution(time, value, False, False))
        db_map.add_parameter_value(
            **{
                'parameter_definition_id': p5.id,
                'object_id': oc3_obj1.id,
                'object_class_id': oc_3.id,
                'value': ts_val,
                "alternative_id": 1,
            }
        )

        timepattern = ['m1', 'm2', 'm3']
        value = [1.1, 2.2, 3.3]
        ts_val = to_database(TimePattern(timepattern, value))
        db_map.add_parameter_value(
            **{
                'parameter_definition_id': p6.id,
                'object_id': oc3_obj1.id,
                'object_class_id': oc_3.id,
                'value': ts_val,
                "alternative_id": 1,
            }
        )

        # commit
        db_map.commit_session('test')

        return db_map, db_map_test

    def _compare_dbs(self, db1, db2):
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

    def _import_xlsx_to_database(self, excel_file_name, db_map):
        data, _errors = get_mapped_data_from_xlsx(excel_file_name)
        # table_mappings (Excel file) contains a sheet json_relationship_class which
        # adds a duplicate 'relationship_class' to data. A duplicate is considered
        # an error by spinedb_api import_data() function. Is this intentional?
        # TODO: Check if db_map is supposed to have two relationship classes called relationship_class or not?
        import_num, import_errors = import_data(db_map, **data)
        self.assertEqual(import_errors, [])
        db_map.commit_session('Excel import')
        return import_num

    def test_export_import(self):
        """Integration test exporting an excel and then importing it to a new database."""
        with TemporaryDirectory() as directory:
            db_map, empty_db_map = self._create_database(directory)
            try:
                excel_file_name = str(PurePath(directory, _TEMP_EXCEL_FILENAME))
                # export_spine_database_to_xlsx exports db_map to an Excel that has a
                # sheet called json_relationship_class. When this Excel is imported
                # back to a database in _import_xlsx_to_database() function there
                # is a duplicate relationship_class called relationship_class.
                # Is this intentional?
                export_spine_database_to_xlsx(db_map, excel_file_name)
                import_num = self._import_xlsx_to_database(excel_file_name, empty_db_map)
                self.assertEqual(import_num, 32)
                self._compare_dbs(empty_db_map, db_map)
            finally:
                db_map.connection.close()
                empty_db_map.connection.close()

    def test_import_to_existing_data(self):
        """Integration test importing data to a database with existing items"""
        with TemporaryDirectory() as directory:
            db_map, empty_db_map = self._create_database(directory)
            try:
                excel_file_name = str(PurePath(directory, _TEMP_EXCEL_FILENAME))
                # export to excel
                export_spine_database_to_xlsx(db_map, excel_file_name)

                # import into empty database
                import_num = self._import_xlsx_to_database(excel_file_name, empty_db_map)
                self.assertEqual(import_num, 32)

                # delete 1 object_class
                db_map.cascade_remove_items(object_class={1})
                db_map.commit_session("Delete class")

                # reimport data
                import_num = self._import_xlsx_to_database(excel_file_name, db_map)
                self.assertEqual(import_num, 19)

                # compare dbs
                self._compare_dbs(empty_db_map, db_map)
            finally:
                db_map.connection.close()
                empty_db_map.connection.close()


if __name__ == '__main__':
    unittest.main()
