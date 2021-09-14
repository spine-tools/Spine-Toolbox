#!/usr/bin/env python

import os

print(
    """This is a script for upgrading Spine DB API, Spine Engine and Spine Items.
Copyright (C) <2017-2021>  <Spine project consortium>
This program comes with ABSOLUTELY NO WARRANTY; This is free software, and you are welcome to redistribute it
under certain conditions; See files COPYING and COPYING.LESSER for details.
"""
)
print("")
os.system("pip uninstall -y spinedb-api spine-engine spine-items")
print("")
os.system("pip install --upgrade git+https://github.com/Spine-project/Spine-Database-API.git#egg=spinedb_api")
os.system("pip install --upgrade git+https://github.com/Spine-project/spine-engine.git#egg=spine_engine")
os.system("pip install --upgrade git+https://github.com/Spine-project/spine-items.git#egg=spine_items")
