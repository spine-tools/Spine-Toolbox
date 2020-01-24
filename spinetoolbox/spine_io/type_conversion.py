import re
from dateutil.relativedelta import relativedelta

from PySide2.QtWidgets import QDialog, QDialogButtonBox, QVBoxLayout, QSpinBox, QDateTimeEdit, QLineEdit, QFormLayout
from PySide2.QtCore import Qt


from spinedb_api import DateTime, Duration, ParameterValueFormatError


class NewIntegerSequenceDateTimeConvertSpecDialog(QDialog):
    def __init__(self, *args, **kwargs):
        super(NewIntegerSequenceDateTimeConvertSpecDialog, self).__init__(*args, **kwargs)

        self.setWindowTitle("New integer sequence datetime")

        QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel

        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        self.datetime = QDateTimeEdit()
        self.start_integer = QSpinBox()
        self.duration = QLineEdit("1h")
        self.duration.textChanged.connect(self._validate)

        self.layout = QVBoxLayout()
        self.form = QFormLayout()
        self.form.addRow("Initial datetime", self.datetime)
        self.form.addRow("Initial integer", self.start_integer)
        self.form.addRow("Timestep duration", self.duration)
        self.layout.addLayout(self.form)
        self.layout.addWidget(self.buttonBox)
        self.setLayout(self.layout)

        self._validate()

    def _validate(self):
        try:
            Duration(self.duration.text())
        except ParameterValueFormatError:
            self.buttonBox.button(QDialogButtonBox.Ok).setEnabled(False)
            return
        self.buttonBox.button(QDialogButtonBox.Ok).setEnabled(True)

    def get_spec(self):
        start_datetime = DateTime(self.datetime.dateTime().toString(Qt.ISODate))
        duration = Duration(self.duration.text())
        start_int = self.start_integer.value()
        return IntegerSequenceDateTimeConvertSpec(start_datetime, start_int, duration)


def value_to_convert_spec(value):
    if isinstance(value, ConvertSpec):
        return value
    if isinstance(value, str):
        spec = {
            "datetime": DateTimeConvertSpec,
            "duration": DurationConvertSpec,
            "float": FloatConvertSpec,
            "string": StringConvertSpec,
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
        duration = sum(self.duration.value, relativedelta())
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
            "duration": self.duration.to_text(),
            "start_int": self.start_int,
        }
