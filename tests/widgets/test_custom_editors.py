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

"""
Unit tests for custom editor widgets.

:author: A. Soininen (VTT)
:date:   11.3.20.21
"""

import unittest
from PySide2.QtCore import Qt
from PySide2.QtGui import QColor
from PySide2.QtWidgets import QApplication
from spinetoolbox.widgets.custom_editors import (
    CheckListEditor,
    IconColorEditor,
    CustomLineEditor,
    ParameterValueLineEditor,
    SearchBarEditor,
)
from spinetoolbox.helpers import default_icon_id, interpret_icon_id, make_icon_id
from spinetoolbox.resources_icons_rc import qInitResources


class TestCustomLineEditor(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not QApplication.instance():
            QApplication()

    def test_get_set_data(self):
        editor = CustomLineEditor()
        editor.set_data(2.3)
        self.assertEqual(editor.data(), "2.3")


class TestParameterValueLineEditor(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not QApplication.instance():
            QApplication()

    def test_set_data_aligns_text_correctly(self):
        editor = ParameterValueLineEditor()
        editor.set_data("align_left")
        self.assertTrue(editor.alignment() & Qt.AlignLeft)
        editor.set_data(2.3)
        self.assertTrue(editor.alignment() & Qt.AlignRight)

    def test_data_convert_text_to_number(self):
        editor = ParameterValueLineEditor()
        editor.set_data("2.3")
        self.assertEqual(editor.data(), 2.3)


class TestSearchBarEditor(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not QApplication.instance():
            QApplication()

    def test_set_data(self):
        editor = SearchBarEditor(None)
        editor.set_data("current", ["current", "other"])
        self.assertEqual(editor.data(), "current")


class TestCheckListEditor(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not QApplication.instance():
            QApplication()

    def test_set_data(self):
        editor = CheckListEditor(None)
        editor.set_data(["first", "second", "third"], ["first", "third"])
        self.assertEqual(editor.data(), "first,third")

    def test_toggle_selection(self):
        editor = CheckListEditor(None)
        editor.set_data(["first", "second", "third"], ["first", "third"])
        self.assertEqual(editor.data(), "first,third")
        index = editor.model.index(1, 0)
        editor.toggle_selected(index)
        self.assertEqual(editor.data(), "first,third,second")
        editor.toggle_selected(index)
        self.assertEqual(editor.data(), "first,third")

    def test_toggle_selection_when_ranked(self):
        editor = CheckListEditor(None, ranked=True)
        editor.set_data(["first", "second", "third"], ["first", "third"])
        self.assertEqual(editor.data(), "first,third")
        index = editor.model.index(1, 0)
        editor.toggle_selected(index)
        self.assertEqual(editor.data(), "first,third,second")
        editor.toggle_selected(index)
        self.assertEqual(editor.data(), "first,third")


class TestIconColorEditor(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        qInitResources()
        if not QApplication.instance():
            QApplication()

    def test_set_data(self):
        editor = IconColorEditor(None)
        cog_symbol = 0xF013
        gray = 0xFFAAAAAA
        icon_id = make_icon_id(cog_symbol, gray)
        editor.set_data(icon_id)
        self.assertEqual(editor.data(), icon_id)


if __name__ == '__main__':
    unittest.main()
