#############################################################################
# Copyright (C) 2016 - 2017 VTT Technical Research Centre of Finland
#
# This file is part of Spine Toolbox.
#
# Spine Toolbox is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#############################################################################

"""
Spine Toolbox default configurations.

:author: Pekka Savolainen <pekka.t.savolainen@vtt.fi>
:date:   2.1.2018
"""

import sys
import os
from PySide2.QtGui import QColor

# General
SPINE_TOOLBOX_VERSION = '0.0.2'
ERROR_COLOR = QColor('red')
SUCCESS_COLOR = QColor('green')
NEUTRAL_COLOR = QColor('blue')
BLACK_COLOR = QColor('black')

# Application path
if getattr(sys, 'frozen', False):
    APPLICATION_PATH = os.path.realpath(os.path.dirname(sys.executable))
else:
    APPLICATION_PATH = os.path.realpath(os.path.dirname(__file__))
