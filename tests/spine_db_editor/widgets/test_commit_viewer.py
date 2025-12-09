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

"""Unit tests for ``commit_viewer`` module."""
from contextlib import contextmanager
from unittest import mock
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication
import pytest
from spinetoolbox.fetch_parent import FlexibleFetchParent
from spinetoolbox.spine_db_editor.widgets.commit_viewer import CommitViewer, QSplitter
from tests.mock_helpers import assert_table_model_data_pytest, q_object


@pytest.fixture()
def ui_settings():
    mock_settings = mock.Mock()
    mock_settings.value.side_effect = lambda *args, **kwargs: 0
    yield mock_settings


@contextmanager
def create_commit_viewer(db_mngr, db_map, ui_settings, parent_widget):
    with mock.patch.object(QSplitter, "restoreState"):
        commit_viewer = CommitViewer(ui_settings, db_mngr, db_map, parent=parent_widget)
    yield commit_viewer
    commit_viewer.close()


class TestCommitViewer:

    def test_tab_count(self, db_mngr, db_map, ui_settings, parent_widget):
        with create_commit_viewer(db_mngr, db_map, ui_settings, parent_widget) as commit_viewer:
            assert commit_viewer.centralWidget().count() == 1

    def test_initial_commit_shows_in_list(self, db_mngr, db_map, ui_settings, parent_widget):
        with create_commit_viewer(db_mngr, db_map, ui_settings, parent_widget) as commit_viewer:
            tab_widget = commit_viewer.centralWidget()
            assert tab_widget.currentIndex() == 0
            current_tab = tab_widget.currentWidget()
            commit_list = current_tab._ui.commit_list
            assert commit_list.topLevelItemCount() == 1
            initial_commit_item = commit_list.topLevelItem(0)
            commit_db_items = db_map.get_items("commit")
            assert initial_commit_item.data(0, Qt.ItemDataRole.UserRole + 1) == commit_db_items[0]["id"]

    def test_selecting_initial_commit_shows_base_alternative(self, db_mngr, db_map, ui_settings, parent_widget):
        with create_commit_viewer(db_mngr, db_map, ui_settings, parent_widget) as commit_viewer:
            with q_object(FlexibleFetchParent("alternative")) as fetch_parent:
                db_mngr.fetch_more(db_map, fetch_parent)
                tab_widget = commit_viewer.centralWidget()
                assert tab_widget.currentIndex() == 0
                current_tab = tab_widget.currentWidget()
                commit_list = current_tab._ui.commit_list
                initial_commit_item = commit_list.topLevelItem(0)
                commit_list.setCurrentItem(initial_commit_item)
                affected_item_tab_widget = current_tab._ui.affected_item_tab_widget
                while affected_item_tab_widget.count() != 1:
                    QApplication.processEvents()
                affected_items_table = affected_item_tab_widget.widget(0).table
                while affected_items_table.rowCount() != 1:
                    QApplication.processEvents()
                assert affected_items_table.columnCount() == 2
                assert affected_items_table.horizontalHeaderItem(0).text() == "name"
                assert affected_items_table.horizontalHeaderItem(1).text() == "description"
                expected = [["Base", "Base alternative"]]
                assert_table_model_data_pytest(affected_items_table.model(), expected)

    def test_element_byname_lists_work(self, db_mngr, db_map, ui_settings, parent_widget):
        with db_map:
            db_map.add_entity_class(name="A")
            db_map.add_entity(entity_class_name="A", name="a")
            db_map.add_entity_class(name="B")
            db_map.add_entity(entity_class_name="B", name="b")
            db_map.add_entity_class(dimension_name_list=["A", "B"])
            db_map.add_entity(entity_class_name="A__B", entity_byname=["a", "b"])
            db_map.commit_session("Add test data")
        db_mngr.reset_session(db_map)
        with create_commit_viewer(db_mngr, db_map, ui_settings, parent_widget) as commit_viewer:
            with (
                q_object(FlexibleFetchParent("alternative")) as alternative_fetch_parent,
                q_object(FlexibleFetchParent("entity")) as entity_fetch_parent,
            ):
                db_mngr.fetch_more(db_map, alternative_fetch_parent)
                db_mngr.fetch_more(db_map, entity_fetch_parent)
                tab_widget = commit_viewer.centralWidget()
                assert tab_widget.currentIndex() == 0
                current_tab = tab_widget.currentWidget()
                commit_list = current_tab._ui.commit_list
                assert commit_list.topLevelItemCount() == 2
                initial_commit_item = commit_list.topLevelItem(0)
                commit_list.setCurrentItem(initial_commit_item)
                affected_item_tab_widget = current_tab._ui.affected_item_tab_widget
                while affected_item_tab_widget.count() != 1:
                    QApplication.processEvents()
                affected_items_table = affected_item_tab_widget.widget(0).table
                while affected_items_table.rowCount() == 0:
                    QApplication.processEvents()
                assert affected_items_table.rowCount() == 3
                expected_header = [
                    "name",
                    "description",
                    "element_name_list",
                    "lat",
                    "lon",
                    "alt",
                    "shape_name",
                    "shape_blob",
                    "entity_class_name",
                    "dimension_name_list",
                    "superclass_name",
                    "element_byname_list",
                ]
                assert affected_items_table.columnCount() == len(expected_header)
                for column, expected_text in enumerate(expected_header):
                    assert affected_items_table.horizontalHeaderItem(column).text() == expected_text
                expected = [
                    ["a", "", "", "", "", "", "", "", "A", "", "", ""],
                    ["b", "", "", "", "", "", "", "", "B", "", "", ""],
                    ["a__b", "", "a ǀ b", "", "", "", "", "", "A__B", "A ǀ B", "", "a ǀ b"],
                ]
                assert_table_model_data_pytest(affected_items_table.model(), expected)
