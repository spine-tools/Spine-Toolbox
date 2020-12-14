#!/usr/bin/env python

import sys
import locale
from PySide2.QtGui import QFontDatabase
from PySide2.QtWidgets import QApplication
from PySide2.QtCore import QSettings
import spinetoolbox.resources_icons_rc  # pylint: disable=unused-import
from spinetoolbox.spine_db_manager import SpineDBManager
from spinetoolbox.helpers import pyside2_version_check
from spinetoolbox.spinedb_api_version_check import spinedb_api_version_check
from spinetoolbox.spine_db_editor.widgets.multi_spine_db_editor import MultiSpineDBEditor

# Check for spinedb_api version before we try to import possibly non-existent stuff below.
if not spinedb_api_version_check():
    sys.exit(1)


def main(argv):
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
    QFontDatabase.addApplicationFont(":/fonts/fontawesome5-solid-webfont.ttf")
    locale.setlocale(locale.LC_NUMERIC, 'C')
    settings = QSettings("SpineProject", "Spine Toolbox")
    db_mngr = SpineDBManager(settings, None)
    editor = MultiSpineDBEditor(db_mngr, {url: None for url in urls}, create=True)
    editor.show()
    return_code = app.exec_()
    return return_code


if __name__ == '__main__':
    sys.exit(main(sys.argv))
