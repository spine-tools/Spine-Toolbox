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

"""Regression tests: (re)loading a db into an editor must not leave the trees stuck-filtered.

Reproduces the bug where a per-level regex tree filter active while another database is opened into the
same editor left the tree stuck-filtered (entities stayed hidden and never returned). Opening another db
re-runs ``init_models``/``build_tree``, which used to keep the stale filter state on the model, the text
in the filter bar and the captured expansion on the view.
"""

from PySide6.QtWidgets import QApplication
import pytest
from tests.spine_db_editor.widgets.spine_db_editor_test_base import DBEditorTestBase


def _visible_entity_names(model):
    """Walks the model's visible tree and returns the names of every visible entity item."""
    names = []
    stack = list(model.root_item.visible_children)
    while stack:
        item = stack.pop()
        if item.item_type == "entity":
            names.append(item.name)
        stack.extend(item.visible_children)
    return names


@pytest.fixture
def editor_env(application):
    env = DBEditorTestBase()
    env.setUp()
    try:
        yield env
    finally:
        env.tearDown()
        env.doCleanups()


def test_reload_clears_stale_entity_filter_and_entities_return(editor_env):
    editor_env.put_mock_object_classes_in_db_mngr()
    editor_env.put_mock_objects_in_db_mngr()
    editor_env.fetch_entity_tree_model()
    model = editor_env.spine_db_editor.entity_tree_model
    assert sorted(_visible_entity_names(model)) == ["nemo", "pluto", "scooby"]
    # A lower-level (entity) regex filter hides all entities but nemo.
    model.set_level_filter("entity", "nemo")
    model._apply_level_filters()
    assert model.has_level_filters()
    assert _visible_entity_names(model) == ["nemo"]
    # Simulate opening another database into the SAME editor: the reload path re-runs init_models.
    editor_env.spine_db_editor.init_models()
    QApplication.processEvents()
    # The stale filter must not carry over: the tree comes back unfiltered and the hidden entities return.
    assert not model.has_level_filters()
    editor_env.fetch_entity_tree_model()
    assert sorted(_visible_entity_names(model)) == ["nemo", "pluto", "scooby"]
    # The filter bar must be empty too.
    for editor in editor_env.spine_db_editor.ui.entity_tree_filter_bar.editors():
        assert editor.text() == ""


def test_reload_clears_filters_and_bars_on_all_four_trees(editor_env):
    editor = editor_env.spine_db_editor
    models_and_types = [
        (editor.entity_tree_model, "entity"),
        (editor.alternative_model, "alternative"),
        (editor.scenario_model, "scenario"),
        (editor.parameter_value_list_model, "parameter_value_list"),
    ]
    bars = [
        editor.ui.entity_tree_filter_bar,
        editor.ui.alternative_tree_filter_bar,
        editor.ui.scenario_tree_filter_bar,
        editor.ui.value_list_tree_filter_bar,
    ]
    for model, item_type in models_and_types:
        model.set_level_filter(item_type, "no_match_pattern")
        assert model.has_level_filters()
    editor.init_models()
    QApplication.processEvents()
    for model, _ in models_and_types:
        assert not model.has_level_filters()
    for bar in bars:
        for line_edit in bar.editors():
            assert line_edit.text() == ""
