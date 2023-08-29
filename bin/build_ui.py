#!/usr/bin/env python

import os.path
import argparse
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


def build_ui(input_path, output_path, force):
    """Converts given .ui file to .py."""
    print("Building " + os.path.basename(output_path))
    status = os.system(f"pyside6-uic --from-imports \"{input_path}\" -o \"{output_path}\"")
    if status != 0:
        print("Stop. Build failed.")
        exit(1)
    append_license(output_path)
    fix_resources_imports(output_path)
    append_license(input_path)


def build_qrc(input_path, output_path, force):
    """Converts given .qrc file to .py."""
    print("Building " + os.path.basename(output_path))
    status = os.system(f"pyside6-rcc -o \"{output_path}\" \"{input_path}\"")
    if status != 0:
        print("Stop. Build failed.")
        exit(1)
    append_license(output_path)


print(
    """<Script for Building Spine Toolbox GUI>
Copyright (C) <2017-2021>  <Spine project consortium>
This program comes with ABSOLUTELY NO WARRANTY; for details see 'about'
box in the application. This is free software, and you are welcome to
redistribute it under certain conditions; See files COPYING and
COPYING.LESSER for details."""
)
parser = argparse.ArgumentParser()
parser.add_argument("--force", help="force building of all .ui files", action="store_true")
args = parser.parse_args()
script_dir = os.path.dirname(os.path.realpath(__file__))
project_source_dir = os.path.join(script_dir, os.path.pardir, "spinetoolbox")
ui_dirs = find_ui_dirs(project_source_dir)
for ui_dir in ui_dirs:
    print(f"--- Entering {os.path.abspath(ui_dir)} ---")
    ui_entries = list()
    py_entries = dict()
    for entry in os.scandir(ui_dir):
        if entry.is_file():
            base, extension = os.path.splitext(entry.name)
            if extension == ".ui":
                ui_entries.append(entry)
            elif extension == ".py":
                py_entries[base] = entry
    for ui_entry in ui_entries:
        base, _ = os.path.splitext(ui_entry.name)
        py_entry = py_entries.get(base)
        if py_entry is None or args.force:
            output_name = base + ".py"
            output_path = os.path.join(ui_dir, output_name)
            build_ui(ui_entry.path, output_path, args.force)
            continue
        ui_modification_time = ui_entry.stat().st_mtime
        py_modification_time = py_entry.stat().st_mtime
        if ui_modification_time > py_modification_time:
            build_ui(ui_entry.path, py_entry.path, args.force)
resources_dir = os.path.join(project_source_dir, "ui", "resources")
qrc_entries = list()
py_paths = dict()
for entry in os.scandir(resources_dir):
    if entry.is_file():
        base, extension = os.path.splitext(entry.name)
        if extension == ".qrc":
            qrc_entries.append(entry)
            output_name = base + "_rc.py"
            output_path = os.path.join(project_source_dir, output_name)
            py_paths[base] = output_path
for qrc_entry in qrc_entries:
    base, _ = os.path.splitext(qrc_entry.name)
    py_path = py_paths.get(base)
    if py_path is None or not os.path.isfile(py_path) or args.force:
        output_name = base + "_rc.py"
        output_path = os.path.join(project_source_dir, output_name)
        build_qrc(qrc_entry.path, output_path, args.force)
        continue
    qrc_modification_time = qrc_entry.stat().st_mtime
    py_modification_time = os.path.getmtime(py_path)
    if qrc_modification_time > py_modification_time:
        build_qrc(qrc_entry.path, py_path, args.force)

print("--- Build completed ---")
