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

"""Unit tests for ``custom_editors`` module."""
import unittest
from PySide6.QtWidgets import QApplication, QWidget, QStyleOptionViewItem
from PySide6.QtGui import QKeyEvent, QFocusEvent, QStandardItemModel, QStandardItem
from PySide6.QtCore import QEvent, Qt, QPoint
from spinetoolbox.spine_db_editor.widgets.custom_editors import (
    CustomLineEditor,
    CustomComboBoxEditor,
    ParameterValueLineEditor,
    PivotHeaderTableLineEditor,
    CheckListEditor,
    IconColorEditor,
    _CustomLineEditDelegate,
    SearchBarEditor,
    BooleanSearchBarEditor,
)
from spinetoolbox.helpers import make_icon_id
from spinetoolbox.resources_icons_rc import qInitResources
from tests.mock_helpers import q_object


class TestEditors(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        qInitResources()
        if not QApplication.instance():
            QApplication()

    def test_searchbar_editor_set_data_sorts_items_case_insensitively(self):
        with q_object(QWidget()) as parent:
            editor = SearchBarEditor(parent)
            editor.set_data("a", ["d", "b", "a", "C"])
            rows = [editor.proxy_model.index(row, 0).data() for row in range(editor.proxy_model.rowCount())]
            self.assertEqual(rows, ["a", "a", "b", "C", "d"])
            editor.set_base_offset(QPoint(0, 0))
            editor.update_geometry(QStyleOptionViewItem())
            editor.refit()

    def test_custom_line_editor(self):
        with q_object(QWidget()) as parent:
            editor = CustomLineEditor(parent)
            editor.set_data("abc")
            self.assertEqual("abc", editor.data())
            keypress_event = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_A, Qt.KeyboardModifier.NoModifier)
            QApplication.sendEvent(editor, keypress_event)
            so_event = QKeyEvent(
                QEvent.Type.ShortcutOverride, Qt.Key.Key_Backspace, Qt.KeyboardModifier.ControlModifier
            )
            QApplication.sendEvent(editor, so_event)

    def test_custom_combobox_editor(self):
        with q_object(QWidget()) as parent:
            editor = CustomComboBoxEditor(parent)

    def test_parameter_value_line_editor(self):
        with q_object(QWidget()) as parent:
            editor = ParameterValueLineEditor(parent)
            editor.set_data(123)
            self.assertEqual(123, editor.data())

    def test_parameter_value_line_editor_set_data_aligns_text_correctly(self):
        with q_object(QWidget()) as parent:
            editor = ParameterValueLineEditor(parent)
            editor.set_data("align_left")
            self.assertTrue(editor.alignment() & Qt.AlignLeft)
            editor.set_data(2.3)
            self.assertTrue(editor.alignment() & Qt.AlignRight)

    def test_pivot_header_line_editor(self):
        with q_object(QWidget()) as parent:
            editor = PivotHeaderTableLineEditor(parent)
            editor.fix_geometry()

    def test_custom_line_edit_delegate(self):
        with q_object(QWidget()) as parent:
            editor = SearchBarEditor(parent)
            delegate = _CustomLineEditDelegate(editor)
            model = QStandardItemModel()
            model.appendRow(QStandardItem("abc"))
            index = model.index(0, 0)
            delegate.setModelData(editor, model, index)
            editor = delegate.createEditor(parent, None, index)
            editor.deleteLater()
            delegate.eventFilter(
                editor, QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Tab, Qt.KeyboardModifier.NoModifier)
            )
            delegate.eventFilter(editor, QFocusEvent(QEvent.Type.FocusOut, Qt.FocusReason.OtherFocusReason))
            delegate.eventFilter(
                editor, QKeyEvent(QEvent.Type.ShortcutOverride, Qt.Key.Key_Escape, Qt.KeyboardModifier.NoModifier)
            )

    def test_checklist_editor_set_data(self):
        with q_object(QWidget()) as parent:
            editor = CheckListEditor(parent)
            editor.set_data(["first", "second", "third"], ["first", "third"])
            self.assertEqual(editor.data(), "first,third")

    def test_checklist_editor_toggle_selection(self):
        with q_object(QWidget()) as parent:
            editor = CheckListEditor(parent)
            editor.set_data(["first", "second", "third"], ["first", "third"])
            self.assertEqual(editor.data(), "first,third")
            index = editor.model().index(1, 0)
            editor.toggle_selected(index)
            self.assertEqual(editor.data(), "first,third,second")
            editor.toggle_selected(index)
            self.assertEqual(editor.data(), "first,third")

    def test_checklist_editor_update_geometry(self):
        with q_object(QWidget()) as parent:
            editor = CheckListEditor(parent)
            editor.update_geometry(QStyleOptionViewItem())

    def test_icon_color_editor_set_data(self):
        with q_object(QWidget()) as parent:
            editor = IconColorEditor(parent)
            cog_symbol = 0xF013
            gray = 0xFFAAAAAA
            icon_id = make_icon_id(cog_symbol, gray)
            editor.set_data(icon_id)
            self.assertEqual(editor.data(), icon_id)

    def test_boolean_searchbar_editor(self):
        with q_object(QWidget()) as parent:
            editor = BooleanSearchBarEditor(parent)
            editor.set_data(True, None)
            retval = editor.data()
            self.assertEqual(True, retval)


if __name__ == "__main__":
    unittest.main()
