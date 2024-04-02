######################################################################################################################
# Copyright (C) 2017-2022 Spine project consortium
# Copyright Spine Toolbox contributors
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""Test for `scenario_generator` module."""
import unittest
from PySide6.QtCore import Qt
from spinetoolbox.spine_db_editor.widgets.scenario_generator import ScenarioGenerator
from tests.spine_db_editor.helpers import TestBase


class TestScenarioGenerator(TestBase):
    def test_alternative_list_contains_alternatives(self):
        self._db_mngr.add_alternatives({self._db_map: [{"name": "alt1"}]})
        alternatives = self._db_mngr.get_items(self._db_map, "alternative")
        scenario_generator = ScenarioGenerator(self._db_editor, self._db_map, alternatives, self._db_editor)
        list_widget = scenario_generator._ui.alternative_list
        listed_alternatives = [list_widget.item(row).text() for row in range(list_widget.count())]
        unique_names = set(listed_alternatives)
        self.assertEqual(len(unique_names), len(listed_alternatives))
        self.assertEqual({a["name"] for a in alternatives}, unique_names)

    def test_zero_padding_in_generated_scenario_names(self):
        db_map_items = [{"name": f"alt{n}"} for n in range(13)]
        self._db_mngr.add_alternatives({self._db_map: db_map_items})
        alternatives = self._db_mngr.get_items(self._db_map, "alternative")
        scenario_generator = ScenarioGenerator(self._db_editor, self._db_map, alternatives, self._db_editor)
        scenario_generator._ui.scenario_prefix_edit.setText("S_")
        scenario_generator._ui.operation_combo_box.setCurrentText("Scenario for each alternative")
        scenario_generator._ui.use_base_alternative_check_box.setCheckState(Qt.CheckState.Unchecked)
        scenario_generator._ui.button_box.accepted.emit()
        scenarios = self._db_mngr.get_items(self._db_map, "scenario")
        scenario_names = {s["name"] for s in scenarios}
        self.assertEqual(scenario_names, {f"S_{n:02}" for n in range(1, 15)})
        scenario_id_to_name = {s["id"]: s["name"] for s in scenarios}
        alternatives = self._db_mngr.get_items(self._db_map, "alternative")
        alternative_id_to_name = {a["id"]: a["name"] for a in alternatives}
        scenario_alternatives = self._db_mngr.get_items(self._db_map, "scenario_alternative")
        scenario_alternatives_by_name = {
            scenario_id_to_name[item["scenario_id"]]: (alternative_id_to_name[item["alternative_id"]], item["rank"])
            for item in scenario_alternatives
        }
        self.assertEqual(
            scenario_alternatives_by_name,
            {
                "S_01": ("Base", 1),
                "S_02": ("alt0", 1),
                "S_03": ("alt1", 1),
                "S_04": ("alt2", 1),
                "S_05": ("alt3", 1),
                "S_06": ("alt4", 1),
                "S_07": ("alt5", 1),
                "S_08": ("alt6", 1),
                "S_09": ("alt7", 1),
                "S_10": ("alt8", 1),
                "S_11": ("alt9", 1),
                "S_12": ("alt10", 1),
                "S_13": ("alt11", 1),
                "S_14": ("alt12", 1),
            },
        )


if __name__ == "__main__":
    unittest.main()
