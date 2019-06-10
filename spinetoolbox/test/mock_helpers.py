######################################################################################################################
# Copyright (C) 2017 - 2019 Spine project consortium
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""
Classes and functions that can be shared among unit test modules.

:author: P. Savolainen (VTT)
:date:   18.4.2019
"""

from PySide2.QtWidgets import QWidget


class MockQWidget(QWidget):
    """Dummy QWidget for mocking test_push_vars method in PythonReplWidget class."""
    def __init__(self):
        super().__init__()

    # noinspection PyMethodMayBeStatic
    def test_push_vars(self):
        return True


# noinspection PyMethodMayBeStatic, PyPep8Naming,SpellCheckingInspection
def qsettings_value_side_effect(key, defaultValue="0"):
    """Side effect for calling QSettings.value() method. Used to
    override default value for key 'appSettings/openPreviousProject'
    so that previous project is not opened in background when
    ToolboxUI is instantiated.

    Args:
        key (str): Key to read
        defaultValue (QVariant): Default value if key is missing
    """
    # logging.debug("in qsettings_value_side_effect. key:{0}, defaultValue:{1}".format(key, defaultValue))
    if key == "appSettings/openPreviousProject":
        return "0"  # Do not open previos project when instantiating ToolboxUI
    return defaultValue
