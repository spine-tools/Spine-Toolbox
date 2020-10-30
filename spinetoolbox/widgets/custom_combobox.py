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
A widget for presenting basic information about the application.

:author: P. Savolainen (VTT)
:date: 14.12.2017
"""

from PySide2.QtCore import Qt
from PySide2.QtWidgets import QComboBox, QStyle, QStylePainter, QStyleOptionComboBox


class ElidedCombobox(QComboBox):
    """Combobox with elided text."""

    def paintEvent(self, event):
        opt = QStyleOptionComboBox()
        self.initStyleOption(opt)
        p = QStylePainter(self)
        p.drawComplexControl(QStyle.CC_ComboBox, opt)

        text_rect = self.style().subControlRect(QStyle.CC_ComboBox, opt, QStyle.SC_ComboBoxEditField, self)
        opt.currentText = p.fontMetrics().elidedText(opt.currentText, Qt.ElideLeft, text_rect.width())
        p.drawControl(QStyle.CE_ComboBoxLabel, opt)
