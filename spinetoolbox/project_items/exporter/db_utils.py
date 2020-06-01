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
Contains utility functions to help with Spine databases.

:author: A. Soininen (VTT)
:date:   5.9.2019
"""


def latest_database_commit_time_stamp(database_map):
    """Returns the latest commit timestamp from given database or None if there are no commits."""
    try:
        return max(commit.date for commit in database_map.query(database_map.Commit).all())
    except ValueError:
        return None
