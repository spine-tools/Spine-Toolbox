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
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication, QWidget
import pytest
from tests.mock_helpers import MockSpineDBManager


@pytest.fixture(scope="module")
def application():
    if QApplication.instance() is None:
        QApplication()
    application_instance = QApplication.instance()
    yield application_instance
    QTimer.singleShot(0, lambda: application_instance.quit())
    application_instance.exec()


@pytest.fixture
def parent_widget(application):
    parent = QWidget()
    yield parent
    parent.deleteLater()


@pytest.fixture
def app_settings():
    return mock.MagicMock()


@pytest.fixture
def logger():
    return mock.MagicMock()


@pytest.fixture
def db_mngr(application, app_settings, logger):
    mngr = MockSpineDBManager(app_settings, None)
    yield mngr
    mngr.close_all_sessions()
    mngr.clean_up()
    mngr.deleteLater()


@pytest.fixture
def db_map(db_mngr, logger, request):
    db_map = db_mngr.get_db_map("sqlite://", logger, create=True)
    db_name = "mock_db" if request.cls is None else request.cls.__name__ + "_db"
    db_mngr.name_registry.register(db_map.sa_url, db_name)
    return db_map
