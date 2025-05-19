######################################################################################################################
# Copyright (C) 2017-2022 Spine project consortium
# Copyright Spine Database API contributors
# This file is part of Spine Database API.
# Spine Database API is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser
# General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your
# option) any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################
import unittest
from unittest import mock
from PySide6.QtWidgets import QApplication
from spinedb_api import to_database
from spinetoolbox.helpers import signal_waiter
from spinetoolbox.parameter_type_validation import ValidationKey
from tests.mock_helpers import TestCaseWithQApplication, MockSpineDBManager


class TestTypeValidator(TestCaseWithQApplication):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.db_codename = cls.__name__ + "_db"

    def setUp(self):
        mock_settings = mock.MagicMock()
        mock_settings.value.side_effect = lambda *args, **kwargs: 0
        self._db_mngr = MockSpineDBManager(mock_settings, None)
        logger = mock.MagicMock()
        self._db_map = self._db_mngr.get_db_map("sqlite://", logger, create=True)
        self._db_mngr.name_registry.register(self._db_map.sa_url, self.db_codename)
        self._db_mngr.parameter_type_validator.set_interval(0)

    def tearDown(self):
        self._db_mngr.close_all_sessions()
        while not self._db_map.closed:
            QApplication.processEvents()
        self._db_mngr.clean_up()

    def _assert_success(self, result):
        item, error = result
        self.assertIsNone(error)
        return item

    def test_valid_parameter_default_value(self):
        self._assert_success(self._db_map.add_entity_class_item(name="Recipe"))
        value, value_type = to_database(23.0)
        price = self._assert_success(
            self._db_map.add_parameter_definition_item(
                name="price", entity_class_name="Recipe", default_value=value, default_type=value_type
            )
        )
        self._db_map.commit_session("Add test data.")
        with signal_waiter(self._db_mngr.parameter_type_validator.validated, timeout=5.0) as waiter:
            self._db_mngr.parameter_type_validator.start_validating(self._db_mngr, self._db_map, [price["id"]])
            waiter.wait()
            self.assertEqual(
                waiter.args,
                ([ValidationKey("parameter_definition", id(self._db_map), price["id"].private_id)], [True]),
            )

    def test_invalid_parameter_default_value(self):
        self._assert_success(self._db_map.add_entity_class_item(name="Recipe"))
        value, value_type = to_database(23.0)
        price = self._assert_success(
            self._db_map.add_parameter_definition_item(
                name="price",
                entity_class_name="Recipe",
                parameter_type_list=("str",),
                default_value=value,
                default_type=value_type,
            )
        )
        with signal_waiter(self._db_mngr.parameter_type_validator.validated, timeout=5.0) as waiter:
            self._db_mngr.parameter_type_validator.start_validating(self._db_mngr, self._db_map, [price["id"]])
            waiter.wait()
            self.assertEqual(
                waiter.args,
                ([ValidationKey("parameter_definition", id(self._db_map), price["id"].private_id)], [False]),
            )

    def test_valid_parameter_value(self):
        self._assert_success(self._db_map.add_entity_class_item(name="Recipe"))
        self._assert_success(self._db_map.add_entity_item(name="fish_n_chips", entity_class_name="Recipe"))
        self._assert_success(self._db_map.add_parameter_definition_item(name="price", entity_class_name="Recipe"))
        value, value_type = to_database(23.0)
        fish_n_chips_price = self._assert_success(
            self._db_map.add_parameter_value_item(
                entity_class_name="Recipe",
                parameter_definition_name="price",
                entity_byname=("fish_n_chips",),
                alternative_name="Base",
                value=value,
                type=value_type,
            )
        )
        with signal_waiter(self._db_mngr.parameter_type_validator.validated, timeout=5.0) as waiter:
            self._db_mngr.parameter_type_validator.start_validating(
                self._db_mngr, self._db_map, [fish_n_chips_price["id"]]
            )
            waiter.wait()
            self.assertEqual(
                waiter.args,
                ([ValidationKey("parameter_value", id(self._db_map), fish_n_chips_price["id"].private_id)], [True]),
            )


if __name__ == "__main__":
    unittest.main()
