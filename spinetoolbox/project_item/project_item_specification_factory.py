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
Contains project item specification factory.

:authors: A. Soininen (VTT)
:date:   6.5.2020
"""


class ProjectItemSpecificationFactory:
    """A factory to make project item specifications."""

    @staticmethod
    def item_type():
        """Returns the project item's type."""
        raise NotImplementedError()

    @staticmethod
    def make_specification(definition, app_settings, logger, embedded_julia_console=None, embedded_python_console=None):
        """
        Makes a project item specification.

        Args:
            definition (dict): specification's definition dictionary
            app_settings (QSettings): Toolbox settings
            logger (LoggerInterface): a logger
            embedded_julia_console (JuliaREPLWidget, optional): a console widget for specifications that need one
            embedded_python_console (PythonReplWidget, optional): a console widget for specifications that need one

        Returns:
            ProjectItemSpecification: a specification built from the given definition
        """
        raise NotImplementedError()
