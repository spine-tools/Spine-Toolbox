#!/bin/bash
# This script is part of build_ui.sh script. See build_ui.sh for license.

if [[ $# -eq 0 ]];
then
    echo 'No filename given'
    exit 0
fi

if grep -Fq "Copyright (C) 2017 - 2018 VTT Technical Research Centre of Finland" $1
then
    echo 'License found'
    exit 0
fi

echo Appending license to file $1

LICENSE="#############################################################################\n\
# Copyright (C) 2017 - 2018 VTT Technical Research Centre of Finland\n\
#\n\
# This file is part of Spine Toolbox.\n\
#\n\
# Spine Toolbox is free software: you can redistribute it and\/or modify\n\
# it under the terms of the GNU Lesser General Public License as published by\n\
# the Free Software Foundation, either version 3 of the License, or\n\
# (at your option) any later version.\n\
#\n\
# This program is distributed in the hope that it will be useful,\n\
# but WITHOUT ANY WARRANTY; without even the implied warranty of\n\
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the\n\
# GNU Lesser General Public License for more details.\n\
#\n\
# You should have received a copy of the GNU Lesser General Public License\n\
# along with this program.  If not, see <http:\/\/www.gnu.org\/licenses\/>.\n\
#############################################################################\n\
"

sed -i "1i${LICENSE}" $1
