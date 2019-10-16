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
Classes to hold parameters.

:authors: M. Marin (KTH)
:date:   2.10.2019
"""

from collections import namedtuple


class ParameterItem:
    """Class to hold parameter definitions or values within a subclass of MinimalTableModel.
    It provides __getitem__ and __setitem__ methods so the item behaves more or less like a list.
    """

    def __init__(self, id_):
        """Init class.

        Args:
            id (int): the id of the item in the db_map table
        """
        self.id = id_

    @property
    def item_type(self):
        raise NotImplementedError()


class ParameterValueItem(ParameterItem):
    @property
    def item_type(self):
        return "parameter value"


class ParameterDefinitionItem(ParameterItem):
    @property
    def item_type(self):
        return "parameter definition"
