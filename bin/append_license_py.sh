#!/bin/bash
# This script is part of build_ui.sh script. See build_ui.sh for license.

if [[ $# -eq 0 ]];
then
    echo 'No filename given'
    exit 0
fi

if grep -Fq "Copyright (C) 2017 - 2018 Spine project consortium" $1
then
    echo 'License found'
    exit 0
fi

echo Appending license to file $1

LICENSE="######################################################################################################################\n\
# Copyright (C) 2017 - 2018 Spine project consortium\n\
# This file is part of Spine Toolbox.\n\
# Spine Toolbox is free software: you can redistribute it and\/or modify it under the terms of the GNU Lesser General\n\
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)\n\
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;\n\
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General\n\
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with\n\
# this program. If not, see <http:\/\/www.gnu.org\/licenses\/>.\n\
######################################################################################################################\n\
"

sed -i "1i${LICENSE}" $1
