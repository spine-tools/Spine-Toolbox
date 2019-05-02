# -*- coding: utf-8 -*-

from PySide2.QtWidgets import QWidget, QApplication, QListWidget, QVBoxLayout, QDialogButtonBox, QMainWindow, QDialog
from PySide2.QtCore import Qt

from spine_io.importers.csv_reader import CSVConnector
from spine_io.importers.odbc_reader import ODBCConnector
from spine_io.importers.excel_reader import ExcelConnector
from spine_io.widgets.import_preview_widget import ImportPreviewWidget

class ImportDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # state
        self._mapped_data = None
        self._mapping_errors = []
        self.connector_list = [CSVConnector, ExcelConnector]
        self.connector_list = {c.DISPLAY_NAME: c for c in self.connector_list}
        self._selected_connector = None
        self.active_connector = None
        
        # create widgets
        self._ui_list = QListWidget()
        self._dialog_buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)

        # layout
        self.select_widget = QWidget()
        self.select_widget.setLayout(QVBoxLayout())
        self.select_widget.layout().addWidget(self._ui_list)
        self.select_widget.layout().addWidget(self._dialog_buttons)
        
        self.setLayout(QVBoxLayout())
        self.layout().addWidget(self.select_widget)
        
        # set list items
        self._ui_list.blockSignals(True)
        self._ui_list.addItems([c for c in self.connector_list.keys()])
        self._ui_list.clearSelection()
        self._ui_list.blockSignals(False)
        
        # connect signals
        self._ui_list.currentItemChanged.connect(self.connector_selected)
        self._ui_list.activated.connect(self.ok_clicked)
        self._dialog_buttons.button(QDialogButtonBox.Ok).clicked.connect(self.ok_clicked)
        self._dialog_buttons.button(QDialogButtonBox.Cancel).clicked.connect(self.reject)
        
        # init ok button
        self.set_ok_button_availability()
    
    @property
    def mapped_data(self):
        return self._mapped_data
    
    @property
    def mapping_errors(self):
        return self._mapping_errors
    
    def connector_selected(self, selection):
        connector = None
        if selection:
            connector = self.connector_list.get(selection.text(), None)
        self._selected_connector = connector
        self.set_ok_button_availability()

    def set_ok_button_availability(self):
        if self._selected_connector:
            self._dialog_buttons.button(QDialogButtonBox.Ok).setEnabled(True)
        else:
            self._dialog_buttons.button(QDialogButtonBox.Ok).setEnabled(False)
    
    def data_ready(self, data, errors):
        self._mapped_data = data
        self._mapping_errors = errors
        self.accept()

    def ok_clicked(self):
        if self._selected_connector:
            # create instance of connector
            self.active_connector = self._selected_connector()
            ok = self.active_connector.connection_ui()
            if ok:
                import_preview = ImportPreviewWidget(self.active_connector, self)
                import_preview.set_loading_status(True)
                import_preview.rejected.connect(self.reject)
                import_preview.mappedDataReady.connect(self.data_ready)
                self.layout().addWidget(import_preview)
                self.select_widget.hide()
                self.active_connector.init_connection()
            else:
                # remove connector object.
                self.active_connector.deleteLater()
                self.active_connector = None


if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    m = QMainWindow()
    m.setAttribute(Qt.WA_DeleteOnClose, True)
    w = ImportDialog()
    m.show()
    w.exec()
    #m.setCentralWidget(w)
    #m.setLayout(QVBoxLayout())
    
    sys.exit(app.exec_())

