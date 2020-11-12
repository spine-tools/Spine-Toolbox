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
Contains the spine_engine_version_check function.

This module should import as few things as possible to avoid accidentally importing anything from spine_engine
that is not available in the current spine_engine version.

:authors: M. Marin (KTH)
:date:   12.11.2020
"""

import sys
import spine_engine
from .config import REQUIRED_SPINE_ENGINE_VERSION


def spine_engine_version_check():
    """Check if spine engine package is the correct version and explain how to upgrade if it is not."""
    try:
        current_version = spine_engine.__version__
        current_split = [int(x) for x in current_version.split(".")]
        required_split = [int(x) for x in REQUIRED_SPINE_ENGINE_VERSION.split(".")]
        if current_split >= required_split:
            return True
    except AttributeError:
        current_version = "not reported"
    script = "upgrade_spine_engine.bat" if sys.platform == "win32" else "upgrade_spine_engine.py"
    print(
        """SPINE ENGINE OUTDATED.

        Spine Toolbox failed to start because spine_engine is outdated.
        (Required version is {0}, whereas current is {1})
        Please upgrade spine_engine to v{0} and start Spine Toolbox again.

        To upgrade, run script '{2}' in the '/bin' folder.

        Or upgrade it manually by running,

            pip install --upgrade git+https://github.com/Spine-project/spine-engine.git#egg=spine_engine

        """.format(
            REQUIRED_SPINE_ENGINE_VERSION, current_version, script
        )
    )
    return False
