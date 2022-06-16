######################################################################################################################
# Copyright (C) 2017-2021 Spine project consortium
# This file is part of Spine Toolbox.
# Spine Engine is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""
Unit tests for FilePackager class.
:author: P. Pääkkönen (VTT), P. Savolainen (VTT)
:date:   03.09.2021
"""

import unittest
import os
from pathlib import Path
from spinetoolbox.server.util.file_packager import FilePackager


class TestFilePackager(unittest.TestCase):

    def test_package_and_delete_file(self):
        src = os.path.join(str(Path(__file__).parent), "projectforpackagingtests")
        dst = os.path.join(src, os.pardir)
        FilePackager.package(src, dst, "packager_test_zip")
        zip_file = os.path.join(dst, "packager_test_zip.zip")
        self.assertTrue(os.path.isfile(zip_file))
        FilePackager.remove_file(zip_file)
        self.assertFalse(os.path.isfile(zip_file))


if __name__ == "__main__":
    unittest.main()
