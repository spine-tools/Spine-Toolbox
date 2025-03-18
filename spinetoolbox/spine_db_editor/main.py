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
#!/usr/bin/env python

from argparse import ArgumentParser
import locale
import sys
from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication
from spinetoolbox.font import TOOLBOX_FONT
from spinetoolbox.helpers import pyside6_version_check
from spinetoolbox.spine_db_editor.widgets.multi_spine_db_editor import MultiSpineDBEditor
from spinetoolbox.spine_db_manager import SpineDBManager


def main():
    """Launches Spine Db Editor as its own application."""
    if not pyside6_version_check():
        return 1
    parser = _make_argument_parser()
    args = parser.parse_args()
    app = QApplication(sys.argv)
    TOOLBOX_FONT.get_family_from_font_database()
    locale.setlocale(locale.LC_NUMERIC, "C")
    settings = QSettings("SpineProject", "Spine Toolbox")
    db_mngr = SpineDBManager(settings, None)
    editor = MultiSpineDBEditor(db_mngr)
    if args.separate_tabs:
        for url in args.url:
            editor.add_new_tab([url])
    else:
        editor.add_new_tab(args.url)
    editor.show()
    return_code = app.exec()
    return return_code


def _make_argument_parser():
    """Builds a command line argument parser.

    Returns:
        ArgumentParser: parser
    """
    parser = ArgumentParser()
    parser.add_argument("-s", "--separate-tabs", action="store_true", help="open databases in separate tabs")
    parser.add_argument("url", nargs="*", help="database URL")
    return parser


if __name__ == "__main__":
    sys.exit(main())
