#!/usr/bin/env python

import os.path
import sys

license_text = [
"######################################################################################################################\n",
"# Copyright (C) 2017-2022 Spine project consortium\n",
"# Copyright Spine Toolbox contributors\n",
"# This file is part of Spine Toolbox.\n",
"# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General\n",
"# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)\n",
"# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;\n",
"# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General\n",
"# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with\n",
"# this program. If not, see <http://www.gnu.org/licenses/>.\n",
"######################################################################################################################\n"
]


def append_license(path):
    _, extension = os.path.splitext(path)
    if extension not in [".py", ".ui", ".xml"]:
        raise RuntimeError("Unsupported file type. Can only append license to .py, .ui or .xml files.")
    if extension == ".py":
        _append_license_py(path)
    else:
        _append_license_xml(path)


def _append_license_py(path):
    """Appends a license header to given .py, .ui or .xml file."""
    base_name = os.path.basename(path)
    print("Appending license to " + base_name)
    with open(path) as input_file:
        contents = input_file.readlines()
    if contents[2].startswith("# Copyright"):
        print(base_name + " seems to have a license already. Skipping.")
        return
    with open(path, "w") as output_file:
        output_file.writelines(contents[:1])  # First line contains encoding.
        output_file.writelines(license_text)
        output_file.writelines(contents[1:])


def _append_license_xml(path):
    """Appends a license header to given .py, .ui or .xml file."""
    xml_license = list()
    xml_license.append("<!--\n")
    for line in license_text:
        xml_license.append(line.replace("/", "\\/"))
    xml_license.append("-->\n")
    with open(path) as input_file:
        contents = input_file.readlines()
    base_name = os.path.basename(path)
    if contents[1].startswith("<!--"):
        print(base_name + " seems to have a license already. Skipping.")
        return
    print("Appending license to " + base_name)
    with open(path, "w") as output_file:
        output_file.writelines(contents[:1])  # First line contains XML schema etc.
        output_file.writelines(xml_license)
        output_file.writelines(contents[1:])


if __name__ == '__main__':
    file_name = sys.argv[1]
    append_license(file_name)
