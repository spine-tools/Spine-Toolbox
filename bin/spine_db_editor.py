#!/usr/bin/env python

import sys
import locale
from PySide2.QtGui import QFontDatabase
from PySide2.QtWidgets import QApplication, QErrorMessage
from PySide2.QtCore import Signal, Slot, Qt, QSettings
import spinetoolbox.resources_icons_rc  # pylint: disable=unused-import
from spinetoolbox.logger_interface import LoggerInterface
from spinetoolbox.spine_db_manager import SpineDBManager
from spinetoolbox.helpers import pyside2_version_check
from spinetoolbox.spinedb_api_version_check import spinedb_api_version_check

# Check for spinedb_api version before we try to import possibly non-existent stuff below.
if not spinedb_api_version_check():
    sys.exit(1)


class SimpleLogger(LoggerInterface):

    msg_error = Signal(str)

    def __init__(self):
        super().__init__()
        self.error_box.connect(self._show_error_box)
        self.box = QErrorMessage()
        self.box.setWindowModality(Qt.ApplicationModal)
        self.msg_error.connect(print)

    @Slot(str, str)
    def _show_error_box(self, title, message):
        self.box.setWindowTitle(title)
        self.box.showMessage(message)


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
    logger = SimpleLogger()
    db_mngr = SpineDBManager(settings, logger, None)
    if not db_mngr.show_spine_db_editor({url: None for url in urls}, logger, create=True):
        return 3
    return_code = app.exec_()
    return return_code


if __name__ == '__main__':
    sys.exit(main(sys.argv))
