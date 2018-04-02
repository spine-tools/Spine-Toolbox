"""
QWidget that is used whenever we need to ask for the user's confirmation.

:author: Manuel Marin <manuelma@kth.se>
:date:   2.4.2018
"""

from PySide2.QtCore import Qt, Signal
from PySide2.QtWidgets import QWidget
import ui.generic_qdialog


class ConfirmationDialog(QWidget):
    """A widget to ask confirmation (Cancel|Yes) from the user.

    Attributes:
        message (str): Message to show in the dialog
    """
    button_clicked_signal = Signal(bool, name="button_clicked_signal")

    def __init__(self, message):
        """Initialize class."""
        super().__init__(f=Qt.Window)
        self.ui = ui.generic_qdialog.Ui_Dialog()
        self.ui.setupUi(self)
        self.ui.label_message.setText(message)
        self.setAttribute(Qt.WA_DeleteOnClose)

    def reject(self):
        self.button_clicked_signal.emit(False)
        self.close()

    def accept(self):
        self.button_clicked_signal.emit(True)
        self.close()

    def keyPressEvent(self, e):
        """Close Setup form when escape key is pressed.

        Args:
            e (QKeyEvent): Received key press event.
        """
        if e.key() == Qt.Key_Escape:
            self.close()

    def closeEvent(self, event=None):
        """Handle close window.

        Args:
            event (QEvent): Closing event if 'X' is clicked.
        """
        if event:
            event.accept()
