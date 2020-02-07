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
Contains unit tests for Tool specification classes.

:authors: A. Soininen (VTT)
:date:   28.1.2020
"""

import unittest
from spinetoolbox.tool_specifications import ToolSpecification


class TestToolSpecification(unittest.TestCase):
    def test_get_cmdline_args_without_expansion(self):
        specification = ToolSpecification("", "", "", [], None, None)
        self.assertFalse(specification.get_cmdline_args([], {}, {}))
        specification.cmdline_args = ["-a", "--version", "-xvf"]
        self.assertEqual(specification.get_cmdline_args([], {}, {}), ["-a", "--version", "-xvf"])

    def test_get_cmdline_args_with_optional_inputs(self):
        specification = ToolSpecification("", "", "", [], None, None)
        specification.cmdline_args = ["@@optional_inputs@@"]
        args = specification.get_cmdline_args([], {}, {})
        self.assertEqual(args, [""])
        specification.cmdline_args = ["@@optional_inputs@@"]
        args = specification.get_cmdline_args(["file.dat", "table.csv"], {}, {})
        self.assertEqual(args, ["file.dat", "table.csv"])
        specification.cmdline_args = ["--inputs=@@optional_inputs@@"]
        args = specification.get_cmdline_args(["file.dat", "table.csv"], {}, {})
        self.assertEqual(args, ["--inputs=file.dat", "table.csv"])

    def test_get_cmdline_args_with_datastore_urls(self):
        specification = ToolSpecification("", "", "", [], None, None)
        specification.cmdline_args = ["@@url:ds1@@"]
        args = specification.get_cmdline_args([], {"ds1": "sqlite:///Q:\\databases\\base.sqlite"}, {})
        self.assertEqual(args, ["sqlite:///Q:\\databases\\base.sqlite"])
        specification.cmdline_args = ["--url=@@url:ds1@@"]
        args = specification.get_cmdline_args([], {}, {"ds1": "sqlite:///Q:\\databases\\base.sqlite"})
        self.assertEqual(args, ["--url=sqlite:///Q:\\databases\\base.sqlite"])

    def test_get_cmdline_args_with_input_datastore_urls(self):
        specification = ToolSpecification("", "", "", [], None, None)
        specification.cmdline_args = ["@@url_inputs@@"]
        args = specification.get_cmdline_args(
            [], {"ds1": "sqlite:///Q:\\databases\\input.sqlite"}, {"ds2": "sqlite:///Q:\\databases\\output.sqlite"}
        )
        self.assertEqual(args, ["sqlite:///Q:\\databases\\input.sqlite"])
        specification.cmdline_args = ["@@url_inputs@@"]
        args = specification.get_cmdline_args(
            [], {"ds1": "sqlite:///Q:\\databases\\input1.sqlite", "ds2": "sqlite:///Q:\\databases\\input2.sqlite"}, {}
        )
        self.assertEqual(args, ["sqlite:///Q:\\databases\\input1.sqlite", "sqlite:///Q:\\databases\\input2.sqlite"])
        specification.cmdline_args = ["--url=@@url_inputs@@"]
        args = specification.get_cmdline_args([], {"ds1": "sqlite:///Q:\\databases\\input.sqlite"}, {})
        self.assertEqual(args, ["--url=sqlite:///Q:\\databases\\input.sqlite"])

    def test_get_cmdline_args_with_output_datastore_urls(self):
        specification = ToolSpecification("", "", "", [], None, None)
        specification.cmdline_args = ["@@url_outputs@@"]
        args = specification.get_cmdline_args(
            [], {"ds1": "sqlite:///Q:\\databases\\input.sqlite"}, {"ds2": "sqlite:///Q:\\databases\\output.sqlite"}
        )
        self.assertEqual(args, ["sqlite:///Q:\\databases\\output.sqlite"])
        specification.cmdline_args = ["@@url_outputs@@"]
        args = specification.get_cmdline_args(
            [], {}, {"ds1": "sqlite:///Q:\\databases\\output1.sqlite", "ds2": "sqlite:///Q:\\databases\\output2.sqlite"}
        )
        self.assertEqual(args, ["sqlite:///Q:\\databases\\output1.sqlite", "sqlite:///Q:\\databases\\output2.sqlite"])
        specification.cmdline_args = ["--url=@@url_outputs@@"]
        args = specification.get_cmdline_args([], {}, {"ds1": "sqlite:///Q:\\databases\\output.sqlite"})
        self.assertEqual(args, ["--url=sqlite:///Q:\\databases\\output.sqlite"])

    def test_get_cmdline_args_consecutive_tags(self):
        specification = ToolSpecification("", "", "", [], None, None)
        specification.cmdline_args = ["@@optional_inputs@@@@optional_inputs@@"]
        args = specification.get_cmdline_args([], {}, {})
        self.assertEqual(args, [""])
        specification.cmdline_args = ["@@optional_inputs@@@@optional_inputs@@"]
        args = specification.get_cmdline_args(["file.dat", "table.csv"], {}, {})
        self.assertEqual(args, ['file.dat', 'table.csvfile.dat', 'table.csv'])
        specification.cmdline_args = ["--inputs=@@optional_inputs@@@@optional_inputs@@"]
        args = specification.get_cmdline_args(["file.dat", "table.csv"], {}, {})
        self.assertEqual(args, ["--inputs=file.dat", "table.csvfile.dat", "table.csv"])

    def test_split_cmdline_args(self):
        splitted = ToolSpecification.split_cmdline_args("")
        self.assertFalse(bool(splitted))
        splitted = ToolSpecification.split_cmdline_args("--version")
        self.assertEqual(splitted, ["--version"])
        splitted = ToolSpecification.split_cmdline_args("--input=data.dat -h 5")
        self.assertEqual(splitted, ["--input=data.dat", "-h", "5"])
        splitted = ToolSpecification.split_cmdline_args('--output="a long file name.txt"')
        self.assertEqual(splitted, ['--output=a long file name.txt'])
        splitted = ToolSpecification.split_cmdline_args("--file='file name with spaces.dat' -i 3")
        self.assertEqual(splitted, ["--file=file name with spaces.dat", "-i", "3"])
        splitted = ToolSpecification.split_cmdline_args("'quotation \"within\" a quotation'")
        self.assertEqual(splitted, ['quotation \"within\" a quotation'])

    def test_split_cmdline_args_with_expandable_tags(self):
        splitted = ToolSpecification.split_cmdline_args("@@optional_inputs@@")
        self.assertEqual(splitted, ["@@optional_inputs@@"])
        splitted = ToolSpecification.split_cmdline_args("@@url:database name with spaces@@")
        self.assertEqual(splitted, ["@@url:database name with spaces@@"])
        splitted = ToolSpecification.split_cmdline_args("@@url:spaced name@@ -a @@url:another spaced tag@@")
        self.assertEqual(splitted, ["@@url:spaced name@@", "-a", "@@url:another spaced tag@@"])

    def test_split_cmdline_args_with_consecutive_tags(self):
        splitted = ToolSpecification.split_cmdline_args("@@optional_inputs@@@@optional_inputs@@")
        self.assertEqual(splitted, ["@@optional_inputs@@@@optional_inputs@@"])


if __name__ == '__main__':
    unittest.main()
