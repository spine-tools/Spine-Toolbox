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
from unittest import mock
from PySide6.QtWidgets import QApplication
import pytest
from spinetoolbox.spine_db_editor.widgets.spine_db_editor import SpineDBEditor


@pytest.fixture
def db_editor(db_mngr, db_map, logger):
    with (
        mock.patch("spinetoolbox.spine_db_editor.widgets.spine_db_editor.SpineDBEditor.restore_ui"),
        mock.patch("spinetoolbox.spine_db_editor.widgets.spine_db_editor.SpineDBEditor.show"),
    ):
        mock_settings = mock.MagicMock()
        mock_settings.value.side_effect = lambda *args, **kwargs: 0
        db_editor = SpineDBEditor(db_mngr, [db_map.db_url])
    QApplication.processEvents()
    yield db_editor
    with (
        mock.patch("spinetoolbox.spine_db_editor.widgets.spine_db_editor.SpineDBEditor.save_window_state"),
        mock.patch("spinetoolbox.spine_db_manager.QMessageBox"),
    ):
        db_editor.close()
    db_editor.deleteLater()
