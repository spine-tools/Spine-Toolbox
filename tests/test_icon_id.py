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
Unit tests for icon display id related functions in the helpers module.

:authors: A. Soininen (VTT)
:date:   20.8.2019
"""

import unittest
from spinetoolbox.helpers import interpret_icon_id, make_icon_id


class MyTestCase(unittest.TestCase):
    def test_make_icon_id(self):
        icon_id = make_icon_id(3, 7)
        self.assertEqual(icon_id, 3 + (7 << 16))

    def test_interpret_icon_id(self):
        icon_code, color_code = interpret_icon_id(None)
        self.assertEqual(icon_code, 0xF1B2)
        self.assertEqual(color_code, 0)
        icon_code, color_code = interpret_icon_id(3 + (7 << 16))
        self.assertEqual(icon_code, 3)
        self.assertEqual(color_code, 7)


if __name__ == '__main__':
    unittest.main()
