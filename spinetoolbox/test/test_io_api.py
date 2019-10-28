import unittest
from unittest.mock import MagicMock

from spine_io.io_api import SourceConnection, TypeConversionException


class TestSourceConnection(unittest.TestCase):
    def setUp(self):
        pass

    def test_type_conversion(self):
        data = iter([['1', 'asd'], ['4.5', 'asd']])
        data = SourceConnection.convert_data_to_types_generator({0: "float"}, data, 2)
        converted_data = list(data)
        self.assertEqual([[1, 'asd'], [4.5, 'asd']], converted_data)

    def test_type_conversion_throws_error(self):
        data = iter([['1', 'asd'], ['invalid number string', 'asd']])
        data = SourceConnection.convert_data_to_types_generator({0: "float"}, data, 2)
        self.assertRaises(list(data), TypeConversionException)
