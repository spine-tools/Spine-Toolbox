#!/usr/bin/env python

import os.path

print("Building Spine Toolbox documentation")

script_dir = os.path.dirname(os.path.realpath(__file__))
make_docs_dir = os.path.join(script_dir, os.path.pardir, "docs")
current_working_dir = os.getcwd()
os.chdir(make_docs_dir)
status = os.system("make html")
os.chdir(current_working_dir)
exit(status)
