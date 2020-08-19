import sys
import os
import locale
from PySide2.QtGui import QFontDatabase
from PySide2.QtWidgets import QApplication, QErrorMessage
from PySide2.QtCore import Slot, Qt, QSettings
import spinetoolbox.resources_icons_rc  # pylint: disable=unused-import
from spinetoolbox.logger_interface import LoggerInterface
from spinetoolbox.spine_db_manager import SpineDBManager
from spinetoolbox.helpers import pyside2_version_check
from spinetoolbox.spinedb_api_version_check import spinedb_api_version_check

# Check for spinedb_api version before we try to import possibly non-existent stuff below.
if not spinedb_api_version_check():
    sys.exit(1)


class SimpleLogger(LoggerInterface):
    def __init__(self):
        super().__init__()
        self.error_box.connect(self._show_error_box)
        self.box = QErrorMessage()
        self.box.setWindowModality(Qt.ApplicationModal)

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
        file_path = argv[1]
    except IndexError:
        return 0
    app = QApplication(argv)
    QFontDatabase.addApplicationFont(":/fonts/fontawesome5-solid-webfont.ttf")
    locale.setlocale(locale.LC_NUMERIC, 'C')
    url = f"sqlite:///{file_path}"
    settings = QSettings("SpineProject", "Spine Toolbox")
    logger = SimpleLogger()
    db_mngr = SpineDBManager(settings, logger, None)
    codename = os.path.splitext(os.path.basename(file_path))[0]
    db_mngr.show_data_store_form({url: codename}, logger)
    return_code = app.exec_()
    return return_code


if __name__ == '__main__':
    sys.exit(main(sys.argv))
