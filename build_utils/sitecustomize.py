"""This file modifies the site packages of the embedded python interpreter
in tools/python.exe. It removes two paths from PYTHONPATH and adds
library.zip into it's site-packages."""

import site
import os
import sys

p = sys.path
try:
    p.remove("C:\\Python37\\Lib")
except ValueError:
    pass
try:
    p.remove("C:\\Python37\\DLLs")
except ValueError:
    pass
sys.path = p
python_exe_dir, _ = os.path.split(sys.executable)
site.addsitedir(os.path.join(python_exe_dir, os.pardir, "lib"))
site.addsitedir(os.path.join(python_exe_dir, os.pardir, "lib", "library.zip"))
