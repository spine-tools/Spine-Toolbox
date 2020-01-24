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
Unit tests for GDXConnector class.

:author: A. Soininen (VTT)
:date:   7.1.2020
"""

import os.path
from tempfile import TemporaryDirectory
import unittest
from gdx2py import GdxFile
from spinetoolbox.spine_io.gdx_utils import find_gams_directory
from spinetoolbox.spine_io.importers.gdx_connector import GdxConnector, GAMSParameter, GAMSScalar, GAMSSet


@unittest.skipIf(find_gams_directory() is None, "No working GAMS installation found.")
class TestGdxConnector(unittest.TestCase):
    def test_get_tables(self):
        connector = GdxConnector()
        gams_directory = find_gams_directory()
        with TemporaryDirectory() as temporary_dir:
            path = os.path.join(temporary_dir, "test_get_tables.gdx")
            with GdxFile(path, "w", gams_directory) as gdx_file:
                domain = GAMSSet([("key1",)])
                gdx_file["domain1"] = domain
                domain = GAMSSet([("key2",)])
                gdx_file["domain2"] = domain
                gams_set = GAMSSet([("key1", "key2")], ["domain1", "domain2"])
                gdx_file["set"] = gams_set
                gams_parameter = GAMSParameter({("key1", "key2"): 3.14}, domain=["domain1", "domain2"])
                gdx_file["parameter"] = gams_parameter
                gams_scalar = GAMSScalar(2.3)
                gdx_file["scalar"] = gams_scalar
            connector.connect_to_source(path)
            tables = connector.get_tables()
            connector.disconnect()
        self.assertEqual(len(tables), 5)
        self.assertTrue("domain1" in tables)
        self.assertTrue("domain2" in tables)
        self.assertTrue("set" in tables)
        self.assertTrue("parameter" in tables)
        self.assertTrue("scalar" in tables)

    def test_get_data_iterator_for_domains(self):
        connector = GdxConnector()
        gams_directory = find_gams_directory()
        with TemporaryDirectory() as temporary_dir:
            path = os.path.join(temporary_dir, "test_get_data_iterator_for_domains.gdx")
            with GdxFile(path, "w", gams_directory) as gdx_file:
                domain = GAMSSet([("key1",), ("key2",)])
                gdx_file["domain"] = domain
            connector.connect_to_source(path)
            data_iterator, header, column_count = connector.get_data_iterator("domain", {})
            connector.disconnect()
        self.assertEqual(column_count, 1)
        self.assertEqual(header, ["*"])
        self.assertEqual(next(data_iterator), ["key1"])
        self.assertEqual(next(data_iterator), ["key2"])
        with self.assertRaises(StopIteration):
            next(data_iterator)

    def test_get_data_iterator_for_sets_with_single_indexing_domain(self):
        connector = GdxConnector()
        gams_directory = find_gams_directory()
        with TemporaryDirectory() as temporary_dir:
            path = os.path.join(temporary_dir, "test_get_data_iterator_for_sets_with_single_indexing_domain.gdx")
            with GdxFile(path, "w", gams_directory) as gdx_file:
                domain = GAMSSet([("key1",), ("key2",)])
                gdx_file["domain"] = domain
                gams_set = GAMSSet([("key1",), ("key2",)], ["domain"])
                gdx_file["set"] = gams_set
            connector.connect_to_source(path)
            data_iterator, header, column_count = connector.get_data_iterator("set", {})
            connector.disconnect()
        self.assertEqual(column_count, 1)
        self.assertEqual(header, ["domain"])
        self.assertEqual(next(data_iterator), ["key1"])
        self.assertEqual(next(data_iterator), ["key2"])
        with self.assertRaises(StopIteration):
            next(data_iterator)

    def test_get_data_iterator_for_sets_with_multiple_indexing_domains(self):
        connector = GdxConnector()
        gams_directory = find_gams_directory()
        with TemporaryDirectory() as temporary_dir:
            path = os.path.join(temporary_dir, "test_get_data_iterator_for_sets_with_single_indexing_domain.gdx")
            with GdxFile(path, "w", gams_directory) as gdx_file:
                domain = GAMSSet([("key1",), ("key2",)])
                gdx_file["domain1"] = domain
                domain = GAMSSet([("keyA",), ("keyB",)])
                gdx_file["domainA"] = domain
                gams_set = GAMSSet([("key1", "keyA"), ("key2", "keyB")], ["domain1", "domainA"])
                gdx_file["set"] = gams_set
            connector.connect_to_source(path)
            data_iterator, header, column_count = connector.get_data_iterator("set", {})
            connector.disconnect()
        self.assertEqual(column_count, 2)
        self.assertEqual(header, ["domain1", "domainA"])
        self.assertEqual(next(data_iterator), ["key1", "keyA"])
        self.assertEqual(next(data_iterator), ["key2", "keyB"])
        with self.assertRaises(StopIteration):
            next(data_iterator)

    def test_get_data_iterator_for_parameters_with_single_indexing_domain(self):
        connector = GdxConnector()
        gams_directory = find_gams_directory()
        with TemporaryDirectory() as temporary_dir:
            path = os.path.join(temporary_dir, "test_get_data_iterator_for_parameters_with_single_indexing_domain.gdx")
            with GdxFile(path, "w", gams_directory) as gdx_file:
                domain = GAMSSet([("key1",), ("key2",)])
                gdx_file["domain"] = domain
                gams_parameter = GAMSParameter({("key1",): 3.14, ("key2",): -2.3}, domain=["domain"])
                gdx_file["parameter"] = gams_parameter
            connector.connect_to_source(path)
            data_iterator, header, column_count = connector.get_data_iterator("parameter", {})
            connector.disconnect()
        self.assertEqual(column_count, 2)
        self.assertEqual(header, ["domain", "Value"])
        self.assertEqual(next(data_iterator), ["key1", 3.14])
        self.assertEqual(next(data_iterator), ["key2", -2.3])
        with self.assertRaises(StopIteration):
            next(data_iterator)

    def test_get_data_iterator_for_parameters_with_multiple_indexing_domains(self):
        connector = GdxConnector()
        gams_directory = find_gams_directory()
        with TemporaryDirectory() as temporary_dir:
            path = os.path.join(
                temporary_dir, "test_get_data_iterator_for_parameters_with_multiple_indexing_domains.gdx"
            )
            with GdxFile(path, "w", gams_directory) as gdx_file:
                domain = GAMSSet([("key1",), ("key2",)])
                gdx_file["domain"] = domain
                domain = GAMSSet([("keyA",), ("keyB",)])
                gdx_file["domainA"] = domain
                gams_parameter = GAMSParameter(
                    {("key1", "keyA"): 3.14, ("key2", "keyB"): -2.3}, domain=["domain1", "domainA"]
                )
                gdx_file["parameter"] = gams_parameter
            connector.connect_to_source(path)
            data_iterator, header, column_count = connector.get_data_iterator("parameter", {})
            connector.disconnect()
        self.assertEqual(column_count, 3)
        self.assertEqual(header, ["domain1", "domainA", "Value"])
        self.assertEqual(next(data_iterator), ["key1", "keyA", 3.14])
        self.assertEqual(next(data_iterator), ["key2", "keyB", -2.3])
        with self.assertRaises(StopIteration):
            next(data_iterator)

    def test_get_data_iterator_for_scalars(self):
        connector = GdxConnector()
        gams_directory = find_gams_directory()
        with TemporaryDirectory() as temporary_dir:
            path = os.path.join(temporary_dir, "test_get_data_iterator_for_scalars.gdx")
            with GdxFile(path, "w", gams_directory) as gdx_file:
                gams_scalar = GAMSScalar(2.3)
                gdx_file["scalar"] = gams_scalar
            connector.connect_to_source(path)
            data_iterator, header, column_count = connector.get_data_iterator("scalar", {})
            connector.disconnect()
        self.assertEqual(column_count, 1)
        self.assertEqual(header, ["Value"])
        self.assertEqual(next(data_iterator), [2.3])
        with self.assertRaises(StopIteration):
            next(data_iterator)


if __name__ == '__main__':
    unittest.main()
