"""
Spine Toolbox

:author: Pekka Savolainen <pekka.t.savolainen@vtt.fi>
:date:   14.12.2017
"""

import sys
import logging
from PySide2.QtWidgets import QApplication
from ui_main import ToolboxUI


def main(argv):
    """Launch application.

    Args:
        argv (list): Command line arguments
    """
    logging.basicConfig(stream=sys.stderr, level=logging.DEBUG,
                        format='%(asctime)s %(levelname)s: %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')
    app = QApplication(argv)
    window = ToolboxUI()
    window.show()
    # Enter main event loop and wait until exit() is called
    return_code = app.exec_()
    return return_code

if __name__ == '__main__':
    sys.exit(main(sys.argv))
