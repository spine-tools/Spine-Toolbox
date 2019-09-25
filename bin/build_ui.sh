#!/bin/bash
#@TITLE Build Spine Toolbox GUI

printf '\n'
echo "<Script for Building Spine Toolbox GUI>
Copyright (C) <2017-2019>  <Spine project consortium>
This program comes with ABSOLUTELY NO WARRANTY; for details see 'about'.
box in the application. This is free software, and you are welcome to
redistribute it under certain conditions; See files COPYING and
COPYING.LESSER for details."
printf '\n'

# read -n 1 -s -r -p "Press any key to continue"
printf '\n'
echo --- pyside2-uic version ---
pyside2-uic --version
echo --- pyside2-rcc version ---
pyside2-rcc -version
printf '\n'
echo --- Building Spine Toolbox GUI ---

path="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )" # path of this script

# Change to project root dir
pushd $path/..

ui_path="spinetoolbox/ui"
spinetoolbox_path="spinetoolbox"
project_items_path="spinetoolbox/project_items"

for ui_file in $(find $ui_path -name '*.ui'); do
  py_file="${ui_file%.ui}.py"
  py_file=$(basename "$py_file")
  py_file=$ui_path/$py_file
  echo building $(basename "$py_file")
  pyside2-uic $ui_file -o $py_file
  sed -i '/# Created:/d;/#      by:/d' $py_file
  bash "bin/append_license_xml.sh" $ui_file
  bash "bin/append_license_py.sh" $py_file
done
for qrc_file in $(find $ui_path -name '*.qrc'); do
  py_file="${qrc_file%.qrc}_rc.py"
  py_file=$(basename "$py_file")
  py_file=$spinetoolbox_path/$py_file
  echo building $(basename "$py_file")
  pyside2-rcc -o $py_file $qrc_file
  sed -i '/# Created:/d;/#      by:/d' $py_file
done

# Build project items ui
printf '\n'
echo --- Building Spine Toolbox Project Items GUI ---

for ui_file in $(find $project_items_path -name '*.ui'); do
    py_file="${ui_file%.ui}.py"
    echo building $(basename "$py_file")
    pyside2-uic $ui_file -o $py_file
    sed -i '/# Created:/d;/#      by:/d' $py_file
    bash "bin/append_license_xml.sh" $ui_file
    bash "bin/append_license_py.sh" $py_file
done

echo --- Build completed ---

popd
