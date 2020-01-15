#!/usr/bin/env python

import os

print("""This is a script for upgrading spine-engine.
Copyright (C) <2017-2020>  <Spine project consortium>
This program comes with ABSOLUTELY NO WARRANTY; This is free software, and you are welcome to redistribute it
under certain conditions; See files COPYING and COPYING.LESSER for details.
""")
print("")
os.system("pip install --upgrade git+https://github.com/Spine-project/spine-engine.git#egg=spine_engine")
