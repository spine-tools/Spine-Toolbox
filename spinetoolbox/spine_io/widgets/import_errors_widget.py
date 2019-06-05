from spinedb_api import ObjectClassMapping, Mapping

from PySide2.QtWidgets import QWidget, QListWidget, QVBoxLayout, QDialogButtonBox, QPushButton, QLabel
from PySide2.QtCore import Signal


class ImportErrorWidget(QWidget):
    importWithErrors = Signal()
    goBack = Signal()
    rejected = Signal()

    def __init__(self, parent=None):
        super(ImportErrorWidget, self).__init__(parent)

        # state
        self._error_list = []
        self._num_imported = 0

        # create widgets
        self._ui_num_errors = QLabel()
        self._ui_num_imports = QLabel()
        self._ui_error_list = QListWidget()

        self._dialog_buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Abort | QDialogButtonBox.Cancel)
        self._dialog_buttons.button(QDialogButtonBox.Abort).setText("Back")

        # layout
        self.setLayout(QVBoxLayout())
        self.layout().addWidget(self._ui_num_imports)
        self.layout().addWidget(self._ui_num_errors)
        self.layout().addWidget(self._ui_error_list)
        self.layout().addWidget(self._dialog_buttons)

        # ok button
        self._dialog_buttons.button(QDialogButtonBox.Ok).clicked.connect(self.importWithErrors.emit)
        self._dialog_buttons.button(QDialogButtonBox.Cancel).clicked.connect(self.rejected.emit)
        self._dialog_buttons.button(QDialogButtonBox.Abort).clicked.connect(self.goBack.emit)

    def set_import_state(self, num_imported, errors):
        self._ui_num_errors.setText(f"Number of errors: {len(errors)}")
        self._ui_num_imports.setText(f"Number of imports: {num_imported}")
        self._ui_error_list.clear()
        self._ui_error_list.addItems([f"{e.db_type}: {e.msg}" for e in errors])
