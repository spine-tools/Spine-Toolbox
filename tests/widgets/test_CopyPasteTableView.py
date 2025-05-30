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

"""Unit tests for CopyPasteTableView class."""
import locale
import unittest
from unittest import mock
from PySide6.QtCore import QAbstractTableModel, QItemSelection, QItemSelectionModel, QModelIndex, Qt
from PySide6.QtWidgets import QApplication
from spinetoolbox.widgets.custom_qtableview import CopyPasteTableView
from tests.mock_helpers import TestCaseWithQApplication, mock_clipboard_patch


class _MockModel(QAbstractTableModel):
    def __init__(self):
        super().__init__()
        self._data = [["a", "b", "1.1"], ["c", "d", "2.2"], ["e", "f", "3.3"]]

    def batch_set_data(self, indexes, data):
        for index, value in zip(indexes, data):
            self._data[index.row()][index.column()] = value
        return True

    def columnCount(self, parent=QModelIndex()):
        return len(self._data[0])

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or role not in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole):
            return None
        return self._data[index.row()][index.column()]

    def flags(self, index):
        return Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEditable | Qt.ItemFlag.ItemIsEnabled

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role not in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole):
            return None
        if orientation == Qt.Orientation.Horizontal:
            return f"Column {section}"
        return f"Row {section}"

    def insertColumns(self, column, count, parent=QModelIndex()):
        self.beginInsertColumns(parent, column, column + count)
        if column < self.columnCount():
            for row in self._data:
                row.insert(column, count * [None])
        else:
            for row in self._data:
                row.append(count * [None])
        self.endInsertColumns()

    def insertRows(self, row, count, parent=QModelIndex()):
        self.beginInsertRows(parent, row, row + count)
        empty = count * [self.columnCount() * [None]]
        if row < self.rowCount():
            self._data.insert(row, empty)
        else:
            self._data.append(empty)
        self.endInsertRows()

    def rowCount(self, parent=QModelIndex()):
        return len(self._data)

    def begin_paste(self):
        pass

    def end_paste(self):
        pass


class TestCopyPasteTableView(TestCaseWithQApplication):
    def test_copy_single_number(self):
        view = CopyPasteTableView()
        model = _MockModel()
        view.setModel(model)
        selection_model = view.selectionModel()
        selection_model.select(model.index(0, 2), QItemSelectionModel.SelectionFlag.Select)
        self.assertTrue(view.copy())
        clipboard = QApplication.clipboard()
        copied = clipboard.text()
        self.assertEqual(copied, f"{str(1.1)}\r\n")

    def test_copy_row_with_hidden_column(self):
        view = CopyPasteTableView()
        model = _MockModel()
        view.setModel(model)
        view.setColumnHidden(1, True)
        selection_model = view.selectionModel()
        selection_model.select(
            model.index(0, 0), QItemSelectionModel.SelectionFlag.Rows | QItemSelectionModel.SelectionFlag.Select
        )
        self.assertTrue(view.copy())
        clipboard = QApplication.clipboard()
        copied = clipboard.text()
        self.assertEqual(copied, f"a\t{str(1.1)}\r\n")

    def test_paste_single_localized_number(self):
        view = CopyPasteTableView()
        model = _MockModel()
        view.setModel(model)
        view.setCurrentIndex(model.index(0, 2))
        QApplication.clipboard().setText(locale.str(-1.1))
        self.assertTrue(view.paste())
        self.assertEqual(model.index(0, 2).data(), "-1.1")

    def test_paste_single_localized_row(self):
        view = CopyPasteTableView()
        model = _MockModel()
        view.setModel(model)
        selection_model = view.selectionModel()
        selection_model.select(
            model.index(0, 0), QItemSelectionModel.SelectionFlag.Rows | QItemSelectionModel.SelectionFlag.Select
        )
        QApplication.clipboard().setText(f"A\tB\t{locale.str(-1.1)}")
        self.assertTrue(view.paste())
        self.assertEqual(model.index(0, 0).data(), "A")
        self.assertEqual(model.index(0, 1).data(), "B")
        self.assertEqual(model.index(0, 2).data(), "-1.1")

    def test_paste_single_comma_separated_string(self):
        view = CopyPasteTableView()
        model = _MockModel()
        view.setModel(model)
        view.setCurrentIndex(model.index(0, 2))
        QApplication.clipboard().setText("unit,node")
        self.assertTrue(view.paste())
        self.assertEqual(model.index(0, 2).data(), "unit,node")

    def test_pasting_normal_with_converter(self):
        view = CopyPasteTableView()
        model = _MockModel()
        view.setModel(model)
        selection_model = view.selectionModel()
        selection_model.setCurrentIndex(model.index(0, 2), QItemSelectionModel.SelectionFlag.ClearAndSelect)
        with mock_clipboard_patch("3.14", "spinetoolbox.widgets.custom_qtableview.QApplication.clipboard"):
            with mock.patch.object(view, "_convert_pasted") as convert_pasted:
                convert_pasted.side_effect = lambda row, column, value, model: float(value)
                self.assertTrue(view.paste())
                convert_pasted.assert_called_once_with(0, 2, "3.14", model)
        data = model.index(0, 2).data()
        self.assertIsInstance(data, float)
        self.assertEqual(data, 3.14)

    def test_pasting_selection_with_converter(self):
        view = CopyPasteTableView()
        model = _MockModel()
        view.setModel(model)
        selection = QItemSelection(model.index(1, 0), model.index(1, 2))
        selection_model = view.selectionModel()
        selection_model.select(selection, QItemSelectionModel.SelectionFlag.ClearAndSelect)
        with mock_clipboard_patch("G\tH\t3.14", "spinetoolbox.widgets.custom_qtableview.QApplication.clipboard"):
            with mock.patch.object(view, "_convert_pasted") as convert_pasted:
                convert_pasted.side_effect = lambda row, column, value, model: float(value) if column == 2 else value
                self.assertTrue(view.paste())
                convert_pasted.assert_called()
        data = [model.index(1, column).data() for column in range(3)]
        self.assertEqual(data, ["G", "H", 3.14])

    def test_cull_rows(self):
        self.assertEqual(
            CopyPasteTableView._cull_rows(2, [3, 0, 2, 1], [[33], [100], [22], [11]]), ([0, 1], [[100], [11]])
        )


if __name__ == "__main__":
    unittest.main()
