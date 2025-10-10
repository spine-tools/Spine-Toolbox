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
from spinetoolbox.project_settings import ProjectSettings


class TestProjectSettings:
    def test_serialization(self):
        settings = ProjectSettings(False, True)
        serialized = settings.to_dict()
        assert ProjectSettings.from_dict(serialized) == settings

    def test_deserialize_v1(self):
        serialized = {"enable_execute_all": False}
        assert ProjectSettings.from_dict(serialized) == ProjectSettings(enable_execute_all=False)
