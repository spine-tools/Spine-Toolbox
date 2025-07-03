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
from PySide6.QtCore import QModelIndex, Qt
from PySide6.QtGui import QStandardItem, QStandardItemModel
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QTableView, QWidget
import pytest
from spinetoolbox.spine_db_editor.stacked_table_seam import AboveSeam, BelowSeam, StackedTableSeam


class TopTable(AboveSeam, QTableView):
    pass


class Bottomtable(BelowSeam, QTableView):
    pass


class TestStackedTableSeam:
    def test_navigating_from_top_to_bottom_and_back(self, parent_widget):
        top_table = TopTable(parent_widget)
        top_model = QStandardItemModel(parent_widget)
        top_model.appendRow([QStandardItem("top A"), QStandardItem("top B")])
        top_table.setModel(top_model)
        bottom_table = Bottomtable(parent_widget)
        bottom_model = QStandardItemModel(parent_widget)
        bottom_model.appendRow([QStandardItem("bottom A"), QStandardItem("bottom B")])
        bottom_table.setModel(bottom_model)
        seam = StackedTableSeam(top_table, bottom_table)
        assert bottom_table.currentIndex() == QModelIndex()
        top_table.setCurrentIndex(top_model.index(0, 0))
        QTest.keyClick(top_table, Qt.Key.Key_Down)
        assert bottom_table.currentIndex() == bottom_model.index(0, 0)
        QTest.keyClick(bottom_table, Qt.Key.Key_Right)
        assert bottom_table.currentIndex() == bottom_model.index(0, 1)
        QTest.keyClick(bottom_table, Qt.Key.Key_Up)
        assert top_table.currentIndex() == top_model.index(0, 1)
