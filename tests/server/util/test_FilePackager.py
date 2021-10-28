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
:author: P. Pääkkönen (VTT)
:date:   03.09.2021
"""

import unittest

import os
import sys

sys.path.append('./../../../spinetoolbox/server/util')

from FilePackager import FilePackager


class TestFilePackager(unittest.TestCase):

    #    def test_folder_packaging(self):
    #        ret=FilePackager.package('/home/ubuntu/sw/Spine-Toolbox/tests/server/util/testfolder','/home/ubuntu/sw/Spine-Toolbox/tests/server/util/','testing')
    #        self.assertEqual(os.path.isfile('/home/ubuntu/sw/Spine-Toolbox/tests/server/util/testing.zip'),True)
    #        os.remove('/home/ubuntu/sw/Spine-Toolbox/tests/server/util/testing.zip')

    def test_folder_packaging_relative_folder(self):
        FilePackager.package('./testfolder', './', 'testing')
        self.assertEqual(os.path.isfile('./testing.zip'), True)
        os.remove('./testing.zip')

    def test_source_folder_notexists(self):
        with self.assertRaises(ValueError):
            FilePackager.package('./testfolder2', './', 'testing')

    def test_sourcefolder_invalid1(self):
        with self.assertRaises(ValueError):
            FilePackager.package(None, './', 'testing')

    def test_dest_folder_invalid1(self):
        with self.assertRaises(ValueError):
            FilePackager.package('./testfolder', '', 'testing')

    def test_dest_folder_invalid2(self):
        with self.assertRaises(ValueError):
            FilePackager.package('./testfolder', None, 'testing')

    def test_nofilename(self):
        with self.assertRaises(ValueError):
            FilePackager.package('./testfolder', './', '')

    def test_packaging_removing(self):
        FilePackager.package('./testfolder', './', 'testing')
        FilePackager.deleteFile('./testing.zip')
        self.assertEqual(os.path.isfile('./testing.zip'), False)


if __name__ == '__main__':
    unittest.main()
