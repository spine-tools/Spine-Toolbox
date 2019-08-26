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

ui_path="../spinetoolbox/ui"
spinetoolbox_path="../spinetoolbox"

for diff_file in $(git diff --name-only -- $ui_path); do
    extension="${diff_file##*.}"
    if [ "$extension" == "ui" ]
    then
      ui_file="../$diff_file"
      py_file="${ui_file%.ui}.py"
      py_file=$(basename "$py_file")
      py_file=$ui_path/$py_file
      echo building $(basename "$py_file")
      pyside2-uic $ui_file -o $py_file
      sed -i '/# Created:/d;/#      by:/d' $py_file
      bash "append_license_xml.sh" $ui_file
      bash "append_license_py.sh" $py_file
    elif [ "$extension" == "qrc" ]
    then
      qrc_file="../$diff_file"
      py_file="${qrc_file%.qrc}_rc.py"
      py_file=$(basename "$py_file")
      py_file=$spinetoolbox_path/$py_file
      echo building $(basename "$py_file")
      pyside2-rcc -o $py_file $qrc_file
      sed -i '/# Created:/d;/#      by:/d' $py_file
    fi
done

echo --- Build completed ---
