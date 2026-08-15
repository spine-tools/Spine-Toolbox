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

"""View-layer tests for the trees' per-level regex filter bar and auto-expand.

Exercises ``TreeLevelFilterBar`` wiring, ``TreeSearchFocusMixin`` navigation, the header-hide logic and the
lower-level-filter auto-fetch/expand on real trees built by a ``DBEditorTestBase`` editor.

The debounced model apply and the view's auto-expand debounce are driven directly (``_apply_level_filters``,
``_run_force_fetch``, ``_apply_auto_expand``) so no wall-clock timer is relied upon; the force-fetch cascade
itself continues on 0 ms timers that fire while the event loop is pumped.
"""

from unittest import mock
from PySide6.QtCore import QEvent, Qt
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import QApplication
import pytest
from tests.spine_db_editor.widgets.spine_db_editor_test_base import DBEditorTestBase

FOCUS_WIDGET = "spinetoolbox.spine_db_editor.widgets.search_bar_base.QApplication.focusWidget"


def _key_event(key, modifiers, text=""):
    return QKeyEvent(QEvent.Type.KeyPress, key, modifiers, text)


def _visible_entity_names(model):
    names = []
    stack = list(model.root_item.visible_children)
    while stack:
        item = stack.pop()
        if item.item_type == "entity":
            names.append(item.name)
        stack.extend(item.visible_children)
    return names


def _class_item(model, name):
    return next(item for item in model.root_item.children if item.display_data == name)


def _drive_force_fetch(model):
    """Runs the force-fetch cascade to completion, pumping the event loop between batches."""
    for _ in range(500):
        model._run_force_fetch()
        if not model._force_fetching:
            break
        QApplication.processEvents()
    model._apply_level_filters()


@pytest.fixture
def editor_env(application):
    env = DBEditorTestBase()
    env.setUp()
    try:
        yield env
    finally:
        env.tearDown()
        env.doCleanups()


def test_each_tree_has_a_filter_bar_with_expected_editor_count(editor_env):
    editor = editor_env.spine_db_editor
    assert len(editor.ui.entity_tree_filter_bar.editors()) == 2
    assert len(editor.ui.alternative_tree_filter_bar.editors()) == 1
    assert len(editor.ui.scenario_tree_filter_bar.editors()) == 2
    assert len(editor.ui.value_list_tree_filter_bar.editors()) == 2


def test_typing_filters_entity_nodes_and_clearing_restores(editor_env):
    editor_env.put_mock_object_classes_in_db_mngr()
    editor_env.put_mock_objects_in_db_mngr()
    editor_env.fetch_entity_tree_model()
    model = editor_env.spine_db_editor.entity_tree_model
    bar = editor_env.spine_db_editor.ui.entity_tree_filter_bar
    assert sorted(_visible_entity_names(model)) == ["nemo", "pluto", "scooby"]
    bar._editors["entity"].setText("nemo")
    model._apply_level_filters()
    assert _visible_entity_names(model) == ["nemo"]
    bar._editors["entity"].setText("")
    model._apply_level_filters()
    assert sorted(_visible_entity_names(model)) == ["nemo", "pluto", "scooby"]


def test_typing_filters_alternative_tree(editor_env):
    editor_env._assert_success(editor_env.mock_db_map.add_alternative_item(name="apple"))
    model = editor_env.spine_db_editor.alternative_model
    bar = editor_env.spine_db_editor.ui.alternative_tree_filter_bar
    db_item = model.item_from_index(model.index(0, 0))
    while db_item.can_fetch_more():
        db_item.fetch_more()
        QApplication.processEvents()
    names = [child.name for child in db_item.children if getattr(child, "id", None) is not None]
    assert "Base" in names
    assert "apple" in names
    bar._editors["alternative"].setText("apple")
    model._apply_level_filters()
    visible = [child.name for child in db_item.visible_children if getattr(child, "id", None) is not None]
    assert visible == ["apple"]
    bar._editors["alternative"].setText("")
    model._apply_level_filters()
    visible = [child.name for child in db_item.visible_children if getattr(child, "id", None) is not None]
    assert "Base" in visible
    assert "apple" in visible


def test_value_list_header_hidden(editor_env):
    assert editor_env.spine_db_editor.ui.treeView_parameter_value_list.isHeaderHidden()


def test_scenario_and_alternative_headers_shown(editor_env):
    assert not editor_env.spine_db_editor.ui.scenario_tree_view.isHeaderHidden()
    assert not editor_env.spine_db_editor.ui.alternative_tree_view.isHeaderHidden()


def test_entity_header_follows_database_column_visibility(editor_env):
    view = editor_env.spine_db_editor.ui.treeView_entity
    # A single database leaves only the "name" column, so the redundant header is hidden.
    assert view.isHeaderHidden()
    view.set_db_column_visibility(True)
    assert not view.isHeaderHidden()
    view.set_db_column_visibility(False)
    assert view.isHeaderHidden()


def _entity_tree_with_classes_fetched(env):
    env.put_mock_object_classes_in_db_mngr()
    env.put_mock_objects_in_db_mngr()
    view = env.spine_db_editor.ui.treeView_entity
    model = env.spine_db_editor.entity_tree_model
    root_index = model.index(0, 0)
    while model.rowCount(root_index) < 2:
        model.fetchMore(root_index)
        QApplication.processEvents()
    return view, model


def test_lower_filter_reveals_unfetched_matches(editor_env):
    view, model = _entity_tree_with_classes_fetched(editor_env)
    bar = editor_env.spine_db_editor.ui.entity_tree_filter_bar
    # The entities under the classes have not been fetched yet.
    assert _visible_entity_names(model) == []
    bar._editors["entity"].setText("nemo")
    _drive_force_fetch(model)
    view._apply_auto_expand()
    # The matching entity is revealed under its auto-expanded class without manual expansion.
    assert _visible_entity_names(model) == ["nemo"]
    fish_index = model.index_from_item(_class_item(model, "fish"))
    assert view.isExpanded(fish_index)


def test_no_match_pattern_collapses(editor_env):
    view, model = _entity_tree_with_classes_fetched(editor_env)
    bar = editor_env.spine_db_editor.ui.entity_tree_filter_bar
    bar._editors["entity"].setText("no_such_entity")
    _drive_force_fetch(model)
    view._apply_auto_expand()
    assert _visible_entity_names(model) == []


def test_clearing_lower_filter_restores_prior_expansion(editor_env):
    view, model = _entity_tree_with_classes_fetched(editor_env)
    bar = editor_env.spine_db_editor.ui.entity_tree_filter_bar
    # Fetch the entities and expand the fish class so there is an expansion state worth restoring.
    for item in model.visit_all():
        while item.can_fetch_more():
            item.fetch_more()
            QApplication.processEvents()
    fish_index = model.index_from_item(_class_item(model, "fish"))
    dog_index = model.index_from_item(_class_item(model, "dog"))
    view.expand(fish_index)
    view.collapse(dog_index)
    assert view.isExpanded(fish_index)
    # A lower-level filter captures this expansion and reveals only nemo.
    bar._editors["entity"].setText("nemo")
    _drive_force_fetch(model)
    view._apply_auto_expand()
    assert _visible_entity_names(model) == ["nemo"]
    # Clearing it restores the captured expansion and brings the hidden entities back.
    bar._editors["entity"].setText("")
    model._apply_level_filters()
    view._apply_auto_expand()
    assert sorted(_visible_entity_names(model)) == ["nemo", "pluto", "scooby"]
    assert view.isExpanded(fish_index)


def _entity_tree(env):
    env.put_mock_object_classes_in_db_mngr()
    env.put_mock_objects_in_db_mngr()
    env.fetch_entity_tree_model()
    return env.spine_db_editor.ui.treeView_entity, env.spine_db_editor.entity_tree_model


def test_down_from_filter_focuses_first_tree_item(editor_env):
    view, model = _entity_tree(editor_env)
    bar = editor_env.spine_db_editor.ui.entity_tree_filter_bar
    bar._editors["entity_class"].go_down.emit()
    current = view.currentIndex()
    assert current.isValid()
    assert current == model.index(0, 0)


def test_up_at_top_jumps_into_filter_bar(editor_env):
    view, model = _entity_tree(editor_env)
    top_index = model.index(0, 0)
    view.setCurrentIndex(top_index)
    assert view._at_top_for_search_focus()
    with mock.patch.object(view, "_focus_search_row_from_view") as focus:
        view.keyPressEvent(_key_event(Qt.Key.Key_Up, Qt.KeyboardModifier.NoModifier))
        focus.assert_called_once()


def test_activate_search_focus_from_view_focuses_bar(editor_env):
    view, _ = _entity_tree(editor_env)
    bar = editor_env.spine_db_editor.ui.entity_tree_filter_bar
    with (
        mock.patch(FOCUS_WIDGET, return_value=view),
        mock.patch.object(bar, "focus_last_used_cell") as focus,
    ):
        view.activate_search_focus()
        focus.assert_called_once()


def test_activate_search_focus_before_bar_connected_is_safe(editor_env):
    view, _ = _entity_tree(editor_env)
    with mock.patch.object(view, "_level_filter_bar", None):
        with mock.patch.object(view, "setFocus") as set_focus:
            view.activate_search_focus()
            set_focus.assert_called_once()


def test_focus_hooks_delegate_to_filter_bar(editor_env):
    view, _ = _entity_tree(editor_env)
    bar = editor_env.spine_db_editor.ui.entity_tree_filter_bar
    with mock.patch.object(bar, "focus_last_used_cell") as focus:
        view._focus_search_row_from_view()
        view._restore_search_row_focus()
    assert focus.call_count == 2


def test_alt_key_not_typed_in_tree_filter_editor(editor_env):
    _entity_tree(editor_env)
    editor = editor_env.spine_db_editor.ui.entity_tree_filter_bar._editors["entity"]
    editor.keyPressEvent(_key_event(Qt.Key.Key_2, Qt.KeyboardModifier.AltModifier, "2"))
    assert editor.text() == ""
    editor.keyPressEvent(_key_event(Qt.Key.Key_2, Qt.KeyboardModifier.NoModifier, "2"))
    assert editor.text() == "2"
