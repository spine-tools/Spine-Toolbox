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
Contains ImportErrorWidget class.

:author: P. Vennström (VTT)
:date:   1.6.2019
"""

from PySide2.QtWidgets import QWidget


class ImportErrorWidget(QWidget):
    """Widget to display errors while importing and ask user for action."""

    def __init__(self, parent=None):
        from ..ui.import_errors import Ui_ImportErrors

        super().__init__(parent)

        # state
        self._error_list = []
        self._num_imported = 0

        # ui
        self._ui = Ui_ImportErrors()
        self._ui.setupUi(self)

    def set_import_state(self, num_imported, errors):
        """Sets state of error widget.

        Arguments:
            num_imported {int} -- number of successfully imported items
            errors {list} -- list of errors.
        """
        self._ui.error_count_label.setText(f"Number of errors: {len(errors)}")
        self._ui.import_count_label.setText(f"Number of imports: {num_imported}")
        self._ui.error_list.clear()
        self._ui.error_list.addItems(errors)
