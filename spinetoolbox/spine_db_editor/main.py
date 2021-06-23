#!/usr/bin/env python

import sys
import locale
import logging
from PySide2.QtGui import QFontDatabase
from PySide2.QtWidgets import QApplication
from PySide2.QtCore import QSettings

from .. import resources_icons_rc  # pylint: disable=unused-import
from ..spine_db_manager import SpineDBManager
from ..helpers import pyside2_version_check
from .widgets.multi_spine_db_editor import MultiSpineDBEditor


def main(argv=sys.argv):
    """Launches Spine Db Editor as it's own application.

    Args:
        argv (list): Command line arguments
    """
    if not pyside2_version_check():
        return 1
    try:
        urls = argv[1:]
    except IndexError:
        return 2
    app = QApplication(argv)
    status = QFontDatabase.addApplicationFont(":/fonts/fontawesome5-solid-webfont.ttf")
    if status < 0:
        logging.warning("Could not load fonts from resources file. Some icons may not render properly.")
    locale.setlocale(locale.LC_NUMERIC, 'C')
    settings = QSettings("SpineProject", "Spine Toolbox")
    db_mngr = SpineDBManager(settings, None)
    editor = MultiSpineDBEditor(db_mngr, {url: None for url in urls})
    editor.show()
    return_code = app.exec_()
    return return_code


if __name__ == '__main__':
    sys.exit(main(sys.argv))
