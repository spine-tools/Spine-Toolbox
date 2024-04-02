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

"""Unit tests for the custom QTextBrowser."""
import logging
import unittest
import sys
from PySide6.QtWidgets import QApplication
from spinetoolbox.widgets.custom_qtextbrowser import CustomQTextBrowser


class TestCustomQTextBrowser(unittest.TestCase):
    """Tests the CustomQTextBrowser class."""

    @classmethod
    def setUpClass(cls):
        """Overridden method. Runs once before all tests in this class."""
        try:
            cls.app = QApplication().processEvents()
        except RuntimeError:
            pass
        logging.basicConfig(
            stream=sys.stderr,
            level=logging.DEBUG,
            format="%(asctime)s %(levelname)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    def test_default_max_blocks(self):
        browser = CustomQTextBrowser(None)
        self.assertEqual(browser.document().maximumBlockCount(), 2000)

    def test_append_obeys_max_blocks(self):
        browser = CustomQTextBrowser(None)
        self.assertEqual(browser.document().blockCount(), 1)
        browser.document().setMaximumBlockCount(5)
        for _ in range(5):
            browser.append("test text")
        self.assertEqual(browser.document().blockCount(), 5)
        for _ in range(5):
            browser.append("new text")
        self.assertEqual(browser.document().blockCount(), 5)

    def test_extra_blocks_removed_from_start(self):
        browser = CustomQTextBrowser(None)
        self.assertEqual(browser.document().blockCount(), 1)
        browser.document().setMaximumBlockCount(3)
        texts = ["1", "2", "3", "4", "5"]
        for t in texts:
            browser.append(t)
        self.assertEqual(browser.document().blockCount(), 3)
        text_block = browser.document().begin()
        for t in texts[2:]:
            self.assertEqual(text_block.text(), t)
            text_block = text_block.next()


if __name__ == "__main__":
    unittest.main()
