#!/usr/bin/env python

from argparse import ArgumentParser
import sys
import locale
import logging
from PySide6.QtGui import QFontDatabase
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QSettings
from spinetoolbox import resources_icons_rc  # pylint: disable=unused-import
from spinetoolbox.spine_db_manager import SpineDBManager
from spinetoolbox.helpers import pyside6_version_check
from spinetoolbox.spine_db_editor.widgets.multi_spine_db_editor import MultiSpineDBEditor


def main():
    """Launches Spine Db Editor as its own application."""
    if not pyside6_version_check():
        return 1
    parser = _make_argument_parser()
    args = parser.parse_args()
    app = QApplication(sys.argv)
    status = QFontDatabase.addApplicationFont(":/fonts/fontawesome5-solid-webfont.ttf")
    if status < 0:
        logging.warning("Could not load fonts from resources file. Some icons may not render properly.")
    locale.setlocale(locale.LC_NUMERIC, "C")
    settings = QSettings("SpineProject", "Spine Toolbox")
    db_mngr = SpineDBManager(settings, None)
    editor = MultiSpineDBEditor(db_mngr)
    if args.separate_tabs:
        for url in args.url:
            editor.add_new_tab({url: None})
    else:
        editor.add_new_tab({url: None for url in args.url})
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
