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
import unittest
from unittest import mock
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication
from spinetoolbox.fetch_parent import FlexibleFetchParent
import spinetoolbox.resources_icons_rc  # pylint: disable=unused-import
from spinetoolbox.spine_db_editor.widgets.commit_viewer import CommitViewer, QSplitter
from spinetoolbox.spine_db_manager import SpineDBManager
from tests.mock_helpers import TestCaseWithQApplication, q_object


class TestCommitViewer(TestCaseWithQApplication):
    def setUp(self):
        with mock.patch("spinetoolbox.spine_db_editor.widgets.spine_db_editor.SpineDBEditor.restore_ui"):
            mock_settings = mock.Mock()
            mock_settings.value.side_effect = lambda *args, **kwargs: 0
            self._db_mngr = SpineDBManager(mock_settings, None, synchronous=True)
            logger = mock.MagicMock()
            url = "sqlite://"
            self._db_map = self._db_mngr.get_db_map(url, logger, create=True)
            with mock.patch.object(QSplitter, "restoreState"):
                self._commit_viewer = CommitViewer(mock_settings, self._db_mngr, self._db_map)

    def tearDown(self):
        self._commit_viewer.close()
        self._db_mngr.close_all_sessions()
        while not self._db_map.closed:
            QApplication.processEvents()
        self._db_mngr.clean_up()

    def test_tab_count(self):
        self.assertEqual(self._commit_viewer.centralWidget().count(), 1)

    def test_initial_commit_shows_in_list(self):
        tab_widget = self._commit_viewer.centralWidget()
        self.assertEqual(tab_widget.currentIndex(), 0)
        current_tab = tab_widget.currentWidget()
        commit_list = current_tab._ui.commit_list
        self.assertEqual(commit_list.topLevelItemCount(), 1)
        initial_commit_item = commit_list.topLevelItem(0)
        commit_db_items = self._db_map.get_items("commit")
        self.assertEqual(initial_commit_item.data(0, Qt.ItemDataRole.UserRole + 1), commit_db_items[0]["id"])

    def test_selecting_initial_commit_shows_base_alternative(self):
        with q_object(FlexibleFetchParent("alternative")) as fetch_parent:
            self._db_mngr.fetch_more(self._db_map, fetch_parent)
            tab_widget = self._commit_viewer.centralWidget()
            self.assertEqual(tab_widget.currentIndex(), 0)
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
            self.assertEqual(affected_items_table.columnCount(), 2)
            self.assertEqual(affected_items_table.horizontalHeaderItem(0).text(), "name")
            self.assertEqual(affected_items_table.horizontalHeaderItem(1).text(), "description")
            expected = [["Base", "Base alternative"]]
            for row in range(affected_items_table.rowCount()):
                expected_row = expected[row]
                for column in range(affected_items_table.columnCount()):
                    with self.subTest(row=row, column=column):
                        self.assertEqual(affected_items_table.item(row, column).text(), expected_row[column])


if __name__ == "__main__":
    unittest.main()
