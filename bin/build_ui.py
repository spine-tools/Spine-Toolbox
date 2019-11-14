#!/usr/bin/env python

import os.path
import argparse
import datetime as dt
from append_license import append_license


def find_ui_dirs(path, found_dirs=None):
    """Recursively searches for 'ui' directories and returns their paths as a list."""
    if found_dirs is None:
        found_dirs = list()
    for entry in os.scandir(path):
        if entry.is_dir():
            if entry.name == 'ui':
                found_dirs.append(entry.path)
            else:
                find_ui_dirs(entry.path, found_dirs)
    return found_dirs


def fix_resources_imports(path):
    """Fixes resources imports in a given automatically generated Python ui file."""
    lines = list()
    with open(path, 'r') as in_file:
        for line in in_file:
            if line == "from . import resources_icons_rc\n":
                lines.append("from spinetoolbox import resources_icons_rc\n")
            elif line == "from . import resources_logos_rc\n":
                lines.append("from spinetoolbox import resources_logos_rc\n")
            else:
                lines.append(line)
    with open(path, 'w') as out_file:
        out_file.writelines(lines)


print(
    """<Script for Building Spine Toolbox GUI>
Copyright (C) <2017-2019>  <Spine project consortium>
This program comes with ABSOLUTELY NO WARRANTY; for details see 'about'
box in the application. This is free software, and you are welcome to
redistribute it under certain conditions; See files COPYING and
COPYING.LESSER for details."""
)
parser = argparse.ArgumentParser()
parser.add_argument("-m", "--minutes", type=int, help="only build files changed in the last m minutes")
args = parser.parse_args()
start = dt.datetime.now() - dt.timedelta(minutes=args.minutes) if args.minutes else None
script_dir = os.path.dirname(os.path.realpath(__file__))
project_source_dir = os.path.join(script_dir, os.path.pardir, "spinetoolbox")
ui_dirs = find_ui_dirs(project_source_dir)
for ui_dir in ui_dirs:
    for entry in os.scandir(ui_dir):
        if entry.is_file():
            modified = dt.datetime.fromtimestamp(os.stat(entry.path).st_mtime)
            if start and modified < start:
                continue
            base, extension = os.path.splitext(entry.name)
            if extension == ".ui":
                output_name = base + ".py"
                output_path = os.path.join(ui_dir, output_name)
                print("Building " + output_name)
                os.system("pyside2-uic --from-imports {} -o {}".format(entry.path, output_path))
                append_license(output_path)
                fix_resources_imports(output_path)
                append_license(entry.path)
resources_dir = os.path.join(project_source_dir, "ui", "resources")
for entry in os.scandir(resources_dir):
    if entry.is_file():
        modified = dt.datetime.fromtimestamp(os.stat(entry.path).st_mtime)
        if start and modified < start:
            continue
        base, extension = os.path.splitext(entry.name)
        if extension == ".qrc":
            output_name = base + "_rc.py"
            output_path = os.path.join(project_source_dir, output_name)
            print("Building " + output_name)
            os.system("pyside2-rcc -o {} {}".format(output_path, entry.path))
            append_license(output_path)
print("--- Build completed ---")
