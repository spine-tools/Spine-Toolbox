#!/usr/bin/env python

import sys
from PySide2.QtCore import QSettings


def main(argv):
    """Configures julia executable and project in Spine Toolbox settings.

    Args:
        argv (list): Command line arguments
    """
    julia, julia_project = argv[1:]
    settings = QSettings("SpineProject", "Spine Toolbox")
    settings.setValue("appSettings/juliaPath", julia)
    settings.setValue("appSettings/juliaProjectPath", julia_project)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
