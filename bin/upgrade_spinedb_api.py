#!/usr/bin/env python

import os

print("""This is a script for upgrading spinedb_api.
Copyright (C) <2017-2020>  <Spine project consortium>
This program comes with ABSOLUTELY NO WARRANTY; This is free software, and you are welcome to redistribute it
under certain conditions; See files COPYING and COPYING.LESSER for details.
""")
print("")
print("Upgrading from 'master' branch")
print("")
os.system("pip install --upgrade git+https://github.com/Spine-project/Spine-Database-API.git@master")
