# -*- coding: utf-8 -*-

from PySide2.QtWidgets import QWidget, QApplication, QListWidget, QVBoxLayout, QDialogButtonBox, QMainWindow

from importers.csv_reader import CSVConnector
from importers.odbc_reader import ODBCConnector
from importers.excel_reader import ExcelConnector
from widgets.import_preview_widget import ImportPreviewWidget

class ImportWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # state
        self.connector_list = [CSVConnector(), ODBCConnector(), ExcelConnector()]
        self.connector_list = {c.source_name: c for c in self.connector_list}
        self._selected_connector = None
        
        # create widgets
        self._ui_list = QListWidget()
        self._dialog_buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)

        # layout
        self.setLayout(QVBoxLayout())
        self.layout().addWidget(self._ui_list)
        self.layout().addWidget(self._dialog_buttons)
        
        # set list items
        self._ui_list.blockSignals(True)
        self._ui_list.addItems([c for c in self.connector_list.keys()])
        self._ui_list.clearSelection()
        self._ui_list.blockSignals(False)
        
        # connect signals
        self._ui_list.currentItemChanged.connect(self._connector_selected)
        self._ui_list.activated.connect(self._ok_clicked)
        self._dialog_buttons.button(QDialogButtonBox.Ok).clicked.connect(self._ok_clicked)
        
        # init ok button
        self._set_ok_button_availability()

    def _connector_selected(self, selection):
        connector = None
        if selection:
            connector = self.connector_list.get(selection.text(), None)
        self._selected_connector = connector
        self._set_ok_button_availability()

    def _set_ok_button_availability(self):
        if self._selected_connector:
            self._dialog_buttons.button(QDialogButtonBox.Ok).setEnabled(True)
        else:
            self._dialog_buttons.button(QDialogButtonBox.Ok).setEnabled(False)
    
    def _ok_clicked(self):
        if self._selected_connector:
            ok = self._selected_connector.source_selector()
            if ok:
                self.w = QMainWindow()
                import_preview = ImportPreviewWidget(self._selected_connector, self.w)
                self.w.setCentralWidget(import_preview)
                self.w.show()


if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    m = QMainWindow()
    w = ImportWidget()
    m.setCentralWidget(w)
    #m.setLayout(QVBoxLayout())
    m.show()
    sys.exit(app.exec_())

