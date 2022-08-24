######################################################################################################################
# Copyright (C) 2017-2021 Spine project consortium
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################
"""Unit tests for the ``logging_connection`` module."""
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import MagicMock
from spinedb_api import DatabaseMapping, import_tools
from spine_engine.project_item.project_item_resource import database_resource
from spinetoolbox.project_item.logging_connection import LoggingConnection


class TestLoggingConnection(unittest.TestCase):
    def test_replace_resource_from_source(self):
        toolbox = MagicMock()
        disabled_filters = {"database": {"scenario_filter": {"Base"}}}
        connection = LoggingConnection(
            "source", "bottom", "destination", "top", toolbox=toolbox, disabled_filter_names=disabled_filters
        )
        connection.link = MagicMock()
        original = database_resource("source", "sqlite:///db.sqlite", label="database")
        connection.receive_resources_from_source([original])
        self.assertEqual(connection.database_resources, {original})
        modified = database_resource("source", "sqlite:///db2.sqlite", label="new database")
        connection.replace_resources_from_source([original], [modified])
        self.assertEqual(connection.database_resources, {modified})
        self.assertEqual(connection._disabled_filter_names, {"new database": {"scenario_filter": {"Base"}}})

    def test_set_online(self):
        toolbox = MagicMock()
        disabled_filters = {"label": {"scenario_filter": {"Base"}}}
        connection = LoggingConnection(
            "source", "bottom", "destination", "top", toolbox=toolbox, disabled_filter_names=disabled_filters
        )
        connection.set_online("label", "scenario_filter", {"Base": True})
        self.assertEqual(connection.disabled_filter_names("label", "scenario_filter"), set())


if __name__ == '__main__':
    unittest.main()
