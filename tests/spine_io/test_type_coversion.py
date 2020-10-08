import unittest

from spinedb_api import DateTime, Duration

from spinetoolbox.spine_io.type_conversion import (
    value_to_convert_spec,
    StringConvertSpec,
    FloatConvertSpec,
    DateTimeConvertSpec,
    DurationConvertSpec,
    IntegerSequenceDateTimeConvertSpec,
)


class TestValueToConvertSpec(unittest.TestCase):
    def test_string(self):
        self.assertIsInstance(value_to_convert_spec("string"), StringConvertSpec)

    def test_float(self):
        self.assertIsInstance(value_to_convert_spec("float"), FloatConvertSpec)

    def test_DateTime(self):
        self.assertIsInstance(value_to_convert_spec("datetime"), DateTimeConvertSpec)

    def test_Duration(self):
        self.assertIsInstance(value_to_convert_spec("duration"), DurationConvertSpec)

    def test_interger_sequence_datetime(self):
        self.assertIsInstance(
            value_to_convert_spec({"start_datetime": "2019-01-01T00:00", "start_int": 0, "duration": "1h"}),
            IntegerSequenceDateTimeConvertSpec,
        )


class TestConvertSpec(unittest.TestCase):
    def test_string(self):
        self.assertEqual(StringConvertSpec().convert_function()(1), "1")

    def test_float(self):
        self.assertEqual(FloatConvertSpec().convert_function()("1"), 1.0)

    def test_DateTime(self):
        self.assertEqual(DateTimeConvertSpec().convert_function()("2019-01-01T00:00"), DateTime("2019-01-01T00:00"))

    def test_Duration(self):
        self.assertEqual(DurationConvertSpec().convert_function()("1h"), Duration("1h"))

    def test_interger_sequence_datetime(self):
        converter = IntegerSequenceDateTimeConvertSpec("2019-01-01T00:00", 0, "1h")
        self.assertEqual(converter.convert_function()("t00000"), DateTime("2019-01-01T00:00"))
        self.assertEqual(converter.convert_function()("t00002"), DateTime("2019-01-01T02:00"))

    def test_interger_sequence_datetime_shifted_start_int(self):
        converter = IntegerSequenceDateTimeConvertSpec("2019-01-01T00:00", 1, "1h")
        self.assertEqual(converter.convert_function()("t00000"), DateTime("2018-12-31T23:00"))
        self.assertEqual(converter.convert_function()("t00002"), DateTime("2019-01-01T01:00"))

    def test_interger_sequence_datetime_different_duration(self):
        converter = IntegerSequenceDateTimeConvertSpec("2019-01-01T00:00", 0, "2h")
        self.assertEqual(converter.convert_function()("t00000"), DateTime("2019-01-01T00:00"))
        self.assertEqual(converter.convert_function()("t00002"), DateTime("2019-01-01T04:00"))

    def test_interger_sequence_datetime_non_int_string(self):
        converter = IntegerSequenceDateTimeConvertSpec("2019-01-01T00:00", 0, "2h")
        with self.assertRaises(ValueError) as cm:
            converter.convert_function()("not a sequence")


class TestConvertSpecToJsonValue(unittest.TestCase):
    def test_string(self):
        self.assertEqual(StringConvertSpec().to_json_value(), "string")

    def test_float(self):
        self.assertEqual(FloatConvertSpec().to_json_value(), "float")

    def test_DateTime(self):
        self.assertEqual(DateTimeConvertSpec().to_json_value(), "datetime")

    def test_Duration(self):
        self.assertEqual(DurationConvertSpec().to_json_value(), "duration")

    def test_interger_sequence_datetime(self):
        converter = IntegerSequenceDateTimeConvertSpec("2019-01-01T00:00", 0, "1h")
        self.assertEqual(
            converter.to_json_value(),
            {
                "name": "integer sequence datetime",
                "start_datetime": "2019-01-01T00:00:00",
                "start_int": 0,
                "duration": "1h",
            },
        )
