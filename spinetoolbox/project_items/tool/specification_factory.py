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
Tool's specification factory.

:authors: A. Soininen (VTT)
:date:   6.5.2020
"""
from spinetoolbox.project_item_specification_factory import ProjectItemSpecificationFactory
from .item_info import ItemInfo
from .tool_specifications import ToolSpecification


class SpecificationFactory(ProjectItemSpecificationFactory):
    """A factory to make tool specifications."""

    @staticmethod
    def item_type():
        """See base class."""
        return ItemInfo.item_type()

    @staticmethod
    def make_specification(
        definition, definition_path, app_settings, logger, embedded_julia_console, embedded_python_console
    ):
        """Returns a tool specifications."""
        return ToolSpecification.toolbox_load(
            definition, definition_path, app_settings, logger, embedded_julia_console, embedded_python_console
        )
