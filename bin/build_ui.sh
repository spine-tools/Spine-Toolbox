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
ui_path="$path/../spinetoolbox/ui/"

for diff_file in $(git diff --name-only $ui_path); do
    full_dif_file="$path/../$diff_file"
    extension="${full_dif_file##*.}"
    if [ "$extension" == "ui" ]
    then
      py_file="${full_dif_file%.ui}.py"
      echo building $(basename "$py_file")
      pyside2-uic $full_dif_file -o $py_file
      sed -i '/# Created:/d;/#      by:/d' $py_file
      bash "$path/append_license_xml.sh" $full_dif_file
      bash "$path/append_license_py.sh" $py_file
    elif [ "$extension" == "qrc" ]
    then
      py_file="${full_dif_file%.qrc}.py"
      echo building $(basename "$py_file")
      pyside2-rcc -o $py_file $full_dif_file
      sed -i '/# Created:/d;/#      by:/d' $py_file
    fi
done

echo --- Build completed ---
