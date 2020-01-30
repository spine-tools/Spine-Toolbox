######################################################################################################################
# Copyright (C) 2017-2020 Spine project consortium
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""
Classes for models dealing with Data Packages.

:authors: M. Marin (KTH)
:date:   24.6.2018
"""

import os
from PySide2.QtCore import Qt
from .minimal_table_model import MinimalTableModel
from .empty_row_model import EmptyRowModel


class DatapackageResourcesModel(MinimalTableModel):
    def __init__(self, parent):
        """A model of datapackage resource data, used by SpineDatapackageWidget.

        Args:
            parent (SpineDatapackageWidget)
        """

        super().__init__(parent)

    def reset_model(self, resources):  # pylint: disable=arguments-differ
        self.clear()
        self.set_horizontal_header_labels(["name", "source"])
        data = list()
        for resource in resources:
            name = resource.name
            source = os.path.basename(resource.source)
            data.append([name, source])
        super().reset_model(data)

    def flags(self, index):
        if index.column() == 1:
            return ~Qt.ItemIsEditable & ~Qt.ItemIsSelectable
        return super().flags(index)


class DatapackageFieldsModel(MinimalTableModel):
    def __init__(self, parent):
        """A model of datapackage field data, used by SpineDatapackageWidget.

        Args:
            parent (SpineDatapackageWidget)
        """
        super().__init__(parent)

    def reset_model(self, schema):  # pylint: disable=arguments-differ
        self.clear()
        self.set_horizontal_header_labels(["name", "type", "primary key?"])
        data = list()
        for field in schema.fields:
            name = field.name
            type_ = field.type
            primary_key = name in schema.primary_key
            data.append([name, type_, primary_key])
        super().reset_model(data)


class DatapackageForeignKeysModel(EmptyRowModel):
    def __init__(self, parent):
        """A model of datapackage foreign key data, used by SpineDatapackageWidget.

        Args:
            parent (SpineDatapackageWidget)
        """
        super().__init__(parent)
        self._parent = parent

    def reset_model(self, foreign_keys):  # pylint: disable=arguments-differ
        self.clear()
        self.set_horizontal_header_labels(["fields", "reference resource", "reference fields", ""])
        data = list()
        for foreign_key in foreign_keys:
            fields = ",".join(foreign_key['fields'])
            reference_resource = foreign_key['reference']['resource']
            reference_fields = ",".join(foreign_key['reference']['fields'])
            data.append([fields, reference_resource, reference_fields, None])
        super().reset_model(data)
