######################################################################################################################
# Copyright (C) 2017-2019 Spine project consortium
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""
Tests for ParameterIndexSettings widget and its models.

:author: A. Soininen (VTT)
:date:   17.12.2019
"""

import unittest
from PySide2.QtWidgets import QApplication
from spinedb_api.parameter_value import Map
import spinetoolbox.spine_io.exporters.gdx as gdx
from spinetoolbox.project_items.exporter.widgets.parameter_index_settings import (
    IndexSettingsState,
    ParameterIndexSettings,
)


_ERROR_PREFIX = "<span style='color:#ff3333;white-space: pre-wrap;'>"
_ERROR_SUFFIX = "</span>"


class TestParameterIndexSettings(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not QApplication.instance():
            QApplication()

    def test_construction(self):
        value = Map(["s1", "s2"], [-1.1, -2.2])
        parameter = gdx.Parameter(["domain name"], [("key_1",)], [value])
        indexing_setting = gdx.IndexingSetting(parameter, "set name")
        existing_domains = {"domain name": [("key_1",)]}
        settings_widget = ParameterIndexSettings("parameter name", indexing_setting, existing_domains, None)
        self.assertEqual(settings_widget.state, IndexSettingsState.DOMAIN_MISSING_INDEXES)


if __name__ == '__main__':
    unittest.main()
