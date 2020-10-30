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
Type conversion functions.

:author: P. Vennström (VTT)
:date:   21.11.2019
"""

import re
from distutils.util import strtobool
from spinedb_api import DateTime, Duration, ParameterValueFormatError


def value_to_convert_spec(value):
    if isinstance(value, ConvertSpec):
        return value
    if isinstance(value, str):
        spec = {
            "datetime": DateTimeConvertSpec,
            "duration": DurationConvertSpec,
            "float": FloatConvertSpec,
            "string": StringConvertSpec,
            "boolean": BooleanConvertSpec,
        }.get(value)
        return spec()
    if isinstance(value, dict):
        start_datetime = DateTime(value.get("start_datetime"))
        duration = Duration(value.get("duration"))
        start_int = value.get("start_int")
        return IntegerSequenceDateTimeConvertSpec(start_datetime, start_int, duration)
    raise TypeError(f"value must be str or dict instead got {type(value).__name__}")


class ConvertSpec:
    DISPLAY_NAME = ""
    RETURN_TYPE = str

    def convert_function(self):
        constructor = self.RETURN_TYPE

        def convert(value):
            return constructor(value)

        return convert

    def to_json_value(self):
        return self.DISPLAY_NAME


class DateTimeConvertSpec(ConvertSpec):
    DISPLAY_NAME = "datetime"
    RETURN_TYPE = DateTime


class DurationConvertSpec(ConvertSpec):
    DISPLAY_NAME = "duration"
    RETURN_TYPE = Duration


class FloatConvertSpec(ConvertSpec):
    DISPLAY_NAME = "float"
    RETURN_TYPE = float


class StringConvertSpec(ConvertSpec):
    DISPLAY_NAME = "string"
    RETURN_TYPE = str


class BooleanConvertSpec(ConvertSpec):
    DISPLAY_NAME = "boolean"
    RETURN_TYPE = bool

    def convert_function(self):
        constructor = self.RETURN_TYPE

        def convert(value):
            return constructor(strtobool(str(value)))

        return convert


class IntegerSequenceDateTimeConvertSpec(ConvertSpec):
    DISPLAY_NAME = "integer sequence datetime"
    RETURN_TYPE = DateTime

    def __init__(self, start_datetime, start_int, duration):
        if not isinstance(start_datetime, DateTime):
            start_datetime = DateTime(start_datetime)
        if not isinstance(duration, Duration):
            duration = Duration(duration)
        self.start_datetime = start_datetime
        self.start_int = start_int
        self.duration = duration

    def convert_function(self):
        pattern = re.compile(r"[0-9]+|$")
        start_datetime = self.start_datetime.value
        duration = self.duration.value
        start_int = self.start_int

        def convert(value):
            try:
                int_str = pattern.search(str(value)).group()
                int_value = int(int_str) - start_int
                return DateTime(start_datetime + int_value * duration)
            except (ValueError, ParameterValueFormatError):
                raise ValueError(f"Could not convert '{value}' to a DateTime")

        return convert

    def to_json_value(self):
        return {
            "name": self.DISPLAY_NAME,
            "start_datetime": self.start_datetime.value.isoformat(),
            "duration": str(self.duration),
            "start_int": self.start_int,
        }
