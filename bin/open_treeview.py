import sys
import locale
from PySide2.QtWidgets import QApplication
from spinetoolbox.spine_db_manager import SpineDBManager
from spinetoolbox.widgets.tree_view_widget import TreeViewForm
from spinetoolbox.helpers import spinedb_api_version_check, pyside2_version_check


def main(argv):
    """Launch application.

    Args:
        argv (list): Command line arguments
    """
    if not pyside2_version_check():
        return 0
    if not spinedb_api_version_check():
        return 0
    try:
        path = argv[1]
    except IndexError:
        return 0
    app = QApplication(argv)
    locale.setlocale(locale.LC_NUMERIC, 'C')
    url = f"sqlite:///{path}"
    db_mngr = SpineDBManager()
    tree = TreeViewForm(db_mngr, (url, "main"))
    tree.show()
    return_code = app.exec_()
    return return_code


if __name__ == '__main__':
    sys.exit(main(sys.argv))
