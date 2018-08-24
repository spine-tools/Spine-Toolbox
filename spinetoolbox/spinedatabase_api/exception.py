#############################################################################
# Copyright (C) 2017 - 2018 VTT Technical Research Centre of Finland
#
# This file is part of Spine Database API.
#
# Spine Spine Database API is free software: you can redistribute it and/or modify
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
Classes to handle exceptions while using the Spine database API.

:author: Manuel Marin <manuelma@kth.se>
:date:   15.8.2018
"""

class SpineDBAPIError(Exception):
    """Basic exception for errors raised by the API."""
    def __init__(self, msg=None):
        super().__init__(msg)
        self.msg = msg


class TableNotFoundError(SpineDBAPIError):
    """Can't find one of the tables."""
    def __init__(self, table):
        super().__init__(msg="Table '{}' is missing from the database.".format(table))
        self.table = table


class RecordNotFoundError(SpineDBAPIError):
    """Can't find one record in one of the tables."""
    def __init__(self, table, name=None, id=None):
        super().__init__(msg="Unable to find item in table '{}'.".format(table))
        self.table = table
        self.name = name
        self.id = id


class ParameterValueError(SpineDBAPIError):
    """The value given for a parameter does not fit the datatype."""
    def __init__(self, value):
        super().__init__(msg="The value {} does not fit the datatype '{}'.".format(value))
        self.value = value
