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
Unit tests for the EmptyParameterModel subclasses.

:author: M. Marin (KTH)
:date:   10.5.2019
"""

import unittest
from unittest import mock
from collections import namedtuple
from PySide2.QtWidgets import QApplication
from mvcmodels.empty_parameter_models import (
    EmptyParameterValueModel,
    EmptyParameterDefinitionModel,
    EmptyObjectParameterValueModel,
    EmptyRelationshipParameterValueModel,
    EmptyObjectParameterDefinitionModel,
    EmptyRelationshipParameterDefinitionModel,
)
from PySide2.QtCore import Qt, QObject


class TestEmptyParameterValueModel(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not QApplication.instance():
            QApplication()

    def test_add_items_to_db(self):
        """Tests the add_items_to_db method."""
        db_map0 = mock.Mock()
        db_map1 = mock.Mock()
        parameter_value = namedtuple('parameter_value', 'id')

        def add_parameter_values(*items):
            unique_ids = set()
            parameter_values = []
            error_log = []
            for item in items:
                if item['id'] not in unique_ids:
                    unique_ids.add(item['id'])
                    parameter_values.append(parameter_value(**item))
                else:
                    error_log.append(f"repeated id {item['id']}")
            return parameter_values, error_log

        db_map0.add_parameter_values.side_effect = add_parameter_values
        db_map1.add_parameter_values.side_effect = add_parameter_values
        items_to_add = {db_map0: {0: dict(id=8), 1: dict(id=4)}, db_map1: {2: dict(id=9), 3: dict(id=9)}}
        model = EmptyParameterValueModel(None)
        model._main_data = [[None], [None], [None], [None]]
        model._parent = mock.Mock()
        model._parent.horizontal_header_labels.return_value = ['id', 'value']
        model.add_items_to_db(items_to_add)
        self.assertEqual(model._main_data, [[8], [4], [9], [None]])
        self.assertEqual(model.added_rows, [0, 1, 2, 3])
        self.assertEqual(model.error_log, ['repeated id 9'])


class TestEmptyParameterDefinitionModel(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not QApplication.instance():
            QApplication()

    def test_add_items_to_db(self):
        """Tests the add_items_to_db method."""
        db_map0 = mock.Mock()
        db_map1 = mock.Mock()
        parameter_definition = namedtuple('parameter_definition', 'id name')

        def add_parameter_definitions(*items):
            unique_ids = set()
            parameter_definitions = []
            error_log = []
            for item in items:
                if item['id'] not in unique_ids:
                    unique_ids.add(item['id'])
                    parameter_definitions.append(parameter_definition(**item))
                else:
                    error_log.append(f"repeated id {item['id']}")
            return parameter_definitions, error_log

        def set_parameter_definition_tags(tag_id_list_dict):
            error_log = []
            for key, value in tag_id_list_dict.items():
                invalid = [x for x in value if x not in (1, 2)]
                if invalid:
                    error_log.append(f"invalid tag ids {invalid}")
            return None, error_log

        db_map0.add_parameter_definitions.side_effect = add_parameter_definitions
        db_map1.add_parameter_definitions.side_effect = add_parameter_definitions
        db_map0.set_parameter_definition_tags.side_effect = set_parameter_definition_tags
        db_map1.set_parameter_definition_tags.side_effect = set_parameter_definition_tags
        items_to_add = {
            db_map0: {
                0: dict(id=8, name='breed', parameter_tag_id_list=[1, 2]),
                1: dict(id=4, name='breed', parameter_tag_id_list=[3]),
            },
            db_map1: {
                2: dict(id=9, name='width', parameter_tag_id_list=[]),
                3: dict(id=9, name='breed', parameter_tag_id_list=[1, 2]),
            },
        }
        model = EmptyParameterDefinitionModel(None)
        model._main_data = [[None], [None], [None], [None]]
        model._parent = mock.Mock()
        model._parent.horizontal_header_labels.return_value = ['id', 'name']
        model.add_items_to_db(items_to_add)
        self.assertEqual(model._main_data, [[8], [4], [9], [None]])
        self.assertEqual(model.added_rows, [0, 1, 2, 3])
        self.assertEqual(model.error_log, ['invalid tag ids [3]', 'repeated id 9'])


class TestEmptyObjectParameterDefinitionModel(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not QApplication.instance():
            QApplication()

    def setUp(self):
        self.model = EmptyObjectParameterDefinitionModel(None)
        self.model._parent = mock.Mock()
        self.model._parent.horizontal_header_labels.return_value = [
            'object_class_id',
            'object_class_name',
            'parameter_name',
            'parameter_tag_id_list',
            'parameter_tag_list',
            'value_list_id',
            'value_list_name',
            'default_value',
            'database',
        ]
        # Create a mock db map that just returns some silly content
        some_db_map = mock.Mock()
        object_class = namedtuple('object_class', 'id name')
        parameter_tag = namedtuple('parameter_tag', 'id tag')
        wide_parameter_value_list = namedtuple('wide_parameter_value_list', 'id name')
        some_db_map.object_class_list.return_value = [
            object_class(id=1, name='some_object_class'),
            object_class(id=2, name='some_other_object_class'),
        ]
        some_db_map.parameter_tag_list.return_value = [
            parameter_tag(id=1, tag='some_tag'),
            parameter_tag(id=2, tag='some_other_tag'),
        ]
        some_db_map.wide_parameter_value_list_list.return_value = [
            wide_parameter_value_list(id=1, name='some_value_list_name'),
            wide_parameter_value_list(id=2, name='some_other_value_list_name'),
        ]
        self.model._parent.db_name_to_map = {'some_db': some_db_map}

    def test_items_to_add_with_something_good(self):
        """Tests the items_to_add method."""
        self.model._main_data = [
            [
                None,
                'some_object_class',
                'some_parameter',
                None,
                'some_tag,some_other_tag',
                None,
                'some_value_list_name',
                'some_default',
                'some_db',
            ],
            [
                None,
                'some_other_object_class',
                'some_other_parameter',
                None,
                'some_tag',
                None,
                'some_other_value_list_name',
                'some_default',
                'some_db',
            ],
        ]

        indexes = [self.model.index(i, 0) for i in range(len(self.model._main_data))]
        items_to_add = self.model.items_to_add(indexes)
        some_db_map = self.model._parent.db_name_to_map['some_db']
        items_to_add = items_to_add[some_db_map]
        self.assertEqual(len(items_to_add), 2)
        self.assertEqual(
            items_to_add[0],
            {
                'name': 'some_parameter',
                'object_class_id': 1,
                'parameter_tag_id_list': '1,2',
                'parameter_value_list_id': 1,
                'default_value': 'some_default',
            },
        )
        self.assertEqual(
            items_to_add[1],
            {
                'name': 'some_other_parameter',
                'object_class_id': 2,
                'parameter_tag_id_list': '1',
                'parameter_value_list_id': 2,
                'default_value': 'some_default',
            },
        )
        self.assertEqual(self.model.error_log, [])

    def test_items_to_add_with_invalid_object_class(self):
        """Tests the items_to_add method."""
        self.model._main_data = [
            [
                None,
                'some_invalid_object_class',
                'some_parameter',
                None,
                'some_tag,some_other_tag',
                None,
                'some_value_list_name',
                'some_default',
                'some_db',
            ]
        ]
        indexes = [self.model.index(i, 0) for i in range(len(self.model._main_data))]
        items_to_add = self.model.items_to_add(indexes)
        self.assertFalse(items_to_add)
        self.assertEqual(len(self.model.error_log), 1)

    def test_items_to_add_with_invalid_tag(self):
        """Tests the items_to_add method."""
        self.model._main_data = [
            [
                None,
                'some_object_class',
                'some_parameter',
                None,
                'some_tag,some_invalid_tag',
                None,
                'some_value_list_name',
                'some_default',
                'some_db',
            ]
        ]
        indexes = [self.model.index(i, 0) for i in range(len(self.model._main_data))]
        items_to_add = self.model.items_to_add(indexes)
        some_db_map = self.model._parent.db_name_to_map['some_db']
        items_to_add = items_to_add[some_db_map]
        self.assertEqual(len(items_to_add), 1)
        self.assertEqual(
            items_to_add[0],
            {
                'name': 'some_parameter',
                'object_class_id': 1,
                'parameter_value_list_id': 1,
                'default_value': 'some_default',
            },
        )
        self.assertEqual(len(self.model.error_log), 1)

    def test_items_to_add_with_invalid_value_list(self):
        """Tests the items_to_add method."""
        self.model._main_data = [
            [
                None,
                'some_object_class',
                'some_parameter',
                None,
                'some_tag,some_other_tag',
                None,
                'some_invalid_value_list_name',
                'some_default',
                'some_db',
            ]
        ]
        indexes = [self.model.index(i, 0) for i in range(len(self.model._main_data))]
        items_to_add = self.model.items_to_add(indexes)
        some_db_map = self.model._parent.db_name_to_map['some_db']
        items_to_add = items_to_add[some_db_map]
        self.assertEqual(len(items_to_add), 1)
        self.assertEqual(
            items_to_add[0],
            {
                'name': 'some_parameter',
                'object_class_id': 1,
                'parameter_tag_id_list': '1,2',
                'default_value': 'some_default',
            },
        )
        self.assertEqual(len(self.model.error_log), 1)


class TestEmptyRelationshipParameterDefinitionModel(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not QApplication.instance():
            QApplication()

    def setUp(self):
        self.model = EmptyRelationshipParameterDefinitionModel(None)
        self.model._parent = mock.Mock()
        self.model._parent.horizontal_header_labels.return_value = [
            'relationship_class_id',
            'relationship_class_name',
            'object_class_id_list',
            'object_class_name_list',
            'parameter_name',
            'parameter_tag_id_list',
            'parameter_tag_list',
            'value_list_id',
            'value_list_name',
            'default_value',
            'database',
        ]
        # Create a mock db map that just returns some silly content
        some_db_map = mock.Mock()
        wide_relationship_class = namedtuple(
            'wide_relationship_class', 'id name object_class_id_list object_class_name_list'
        )
        parameter_tag = namedtuple('parameter_tag', 'id tag')
        wide_parameter_value_list = namedtuple('wide_parameter_value_list', 'id name')
        some_db_map.wide_relationship_class_list.return_value = [
            wide_relationship_class(
                id=1,
                name='some_relationship_class',
                object_class_id_list='1,2',
                object_class_name_list='some_name,some_other_name',
            ),
            wide_relationship_class(
                id=2,
                name='some_other_relationship_class',
                object_class_id_list='2,3',
                object_class_name_list='some_other_name,yet_another_name',
            ),
        ]
        some_db_map.parameter_tag_list.return_value = [
            parameter_tag(id=1, tag='some_tag'),
            parameter_tag(id=2, tag='some_other_tag'),
        ]
        some_db_map.wide_parameter_value_list_list.return_value = [
            wide_parameter_value_list(id=1, name='some_value_list_name'),
            wide_parameter_value_list(id=2, name='some_other_value_list_name'),
        ]
        self.model._parent.db_name_to_map = {'some_db': some_db_map}

        self.model._parent.db_name_to_map = {'some_db': some_db_map}

    def test_items_to_add_with_something_good(self):
        """Tests the items_to_add method."""
        self.model._main_data = [
            [
                None,
                'some_relationship_class',
                None,
                'some_name,some_other_name',
                'some_parameter',
                None,
                'some_tag,some_other_tag',
                None,
                'some_value_list_name',
                'some_default',
                'some_db',
            ],
            [
                None,
                'some_other_relationship_class',
                None,
                'some_other_name,yet_another_name',
                'some_other_parameter',
                None,
                'some_tag',
                None,
                'some_other_value_list_name',
                'some_default',
                'some_db',
            ],
        ]

        indexes = [self.model.index(i, 0) for i in range(len(self.model._main_data))]
        items_to_add = self.model.items_to_add(indexes)
        some_db_map = self.model._parent.db_name_to_map['some_db']
        items_to_add = items_to_add[some_db_map]
        self.assertEqual(len(items_to_add), 2)
        self.assertEqual(
            items_to_add[0],
            {
                'name': 'some_parameter',
                'relationship_class_id': 1,
                'parameter_tag_id_list': '1,2',
                'parameter_value_list_id': 1,
                'default_value': 'some_default',
            },
        )
        self.assertEqual(
            items_to_add[1],
            {
                'name': 'some_other_parameter',
                'relationship_class_id': 2,
                'parameter_tag_id_list': '1',
                'parameter_value_list_id': 2,
                'default_value': 'some_default',
            },
        )
        self.assertEqual(self.model.error_log, [])

    def test_items_to_add_with_invalid_relationship_class(self):
        """Tests the items_to_add method."""
        self.model._main_data = [
            [
                None,
                'some_invalid_relationship_class',
                None,
                'some_name,some_other_name',
                'some_parameter',
                None,
                'some_tag,some_other_tag',
                None,
                'some_value_list_name',
                'some_default',
                'some_db',
            ]
        ]
        indexes = [self.model.index(i, 0) for i in range(len(self.model._main_data))]
        items_to_add = self.model.items_to_add(indexes)
        self.assertFalse(items_to_add)
        self.assertEqual(len(self.model.error_log), 1)

    def test_items_to_add_with_invalid_tag(self):
        """Tests the items_to_add method."""
        self.model._main_data = [
            [
                None,
                'some_relationship_class',
                None,
                'some_name,some_other_name',
                'some_parameter',
                None,
                'some_tag,some_invalid_tag',
                None,
                'some_value_list_name',
                'some_default',
                'some_db',
            ]
        ]
        indexes = [self.model.index(i, 0) for i in range(len(self.model._main_data))]
        items_to_add = self.model.items_to_add(indexes)
        some_db_map = self.model._parent.db_name_to_map['some_db']
        items_to_add = items_to_add[some_db_map]
        self.assertEqual(len(items_to_add), 1)
        self.assertEqual(
            items_to_add[0],
            {
                'name': 'some_parameter',
                'relationship_class_id': 1,
                'parameter_value_list_id': 1,
                'default_value': 'some_default',
            },
        )
        self.assertEqual(len(self.model.error_log), 1)

    def test_items_to_add_with_invalid_value_list(self):
        """Tests the items_to_add method."""
        self.model._main_data = [
            [
                None,
                'some_relationship_class',
                None,
                'some_name,some_other_name',
                'some_parameter',
                None,
                'some_tag,some_other_tag',
                None,
                'some_invalid_value_list_name',
                'some_default',
                'some_db',
            ]
        ]
        indexes = [self.model.index(i, 0) for i in range(len(self.model._main_data))]
        items_to_add = self.model.items_to_add(indexes)
        some_db_map = self.model._parent.db_name_to_map['some_db']
        items_to_add = items_to_add[some_db_map]
        self.assertEqual(len(items_to_add), 1)
        self.assertEqual(
            items_to_add[0],
            {
                'name': 'some_parameter',
                'relationship_class_id': 1,
                'parameter_tag_id_list': '1,2',
                'default_value': 'some_default',
            },
        )
        self.assertEqual(len(self.model.error_log), 1)
