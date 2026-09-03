######################################################################################################################
# Copyright (C) 2017-2022 Spine project consortium
# Copyright Spine Toolbox contributors
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################
from typing import ClassVar
from spinedb_api.helpers import ItemType
from spinetoolbox.spine_db_editor.mvcmodels.db_item_table_model import DBItemTableModel
from spinetoolbox.spine_db_editor.mvcmodels.utils import PARAMETER_GROUP_FIELD_MAP


class ParameterGroupModel(DBItemTableModel):
    ITEM_TYPE: ClassVar[ItemType] = "parameter_group"
    HEADER: ClassVar[list[str]] = list(PARAMETER_GROUP_FIELD_MAP)
    HEADER_TO_FIELD: ClassVar[dict[str, str]] = PARAMETER_GROUP_FIELD_MAP
