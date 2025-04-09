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

"""Provides Toolbox icon font."""
import logging
from typing import ClassVar, Optional
from PySide6.QtGui import QFontDatabase
from PySide6.QtWidgets import QApplication

# Importing resources_icons_rc initializes resources and Font Awesome gets added to the application
from . import resources_icons_rc  # pylint: disable=unused-import  # isort: skip


class Font:
    family: ClassVar[Optional[str]] = None

    @staticmethod
    def get_family_from_font_database():
        """Sets the family attribute to Font Awesome family name from font database.

        QApplication must be instantiated before calling this function.
        """
        font_id = QFontDatabase.addApplicationFont(":/fonts/fontawesome5-solid-webfont.ttf")
        if font_id < 0:
            logging.warning("Could not load fonts from resources file. Some icons may not render properly.")
            Font.family = QApplication.font().family()
        else:
            Font.family = QFontDatabase().applicationFontFamilies(font_id)[0]


TOOLBOX_FONT = Font()
