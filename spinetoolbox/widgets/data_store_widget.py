"""
Widget to show Data Store Form.

:author: Pekka Savolainen <pekka.t.savolainen@vtt.fi>
:date:   14.12.2017
"""

from PySide2.QtWidgets import QWidget
from PySide2.QtCore import Qt
import ui.data_store_form


class DataStoreWidget(QWidget):
    """Class constructor.

    Attributes:
        parent (QWidget): Parent widget.
    """
    def __init__(self, parent):
        """ Initialize class. """
        super().__init__(f=Qt.Window)
        self._parent = parent  # QWidget parent
        #  Set up the form from designer files.
        self.ui = ui.data_store_form.Ui_DataStoreForm()
        self.ui.setupUi(self)
        # Ensure this window gets garbage-collected when closed
        self.setAttribute(Qt.WA_DeleteOnClose)

    def closeEvent(self, event=None):
        """Handle close window.

        Args:
            event (QEvent): Closing event if 'X' is clicked.
        """
        if event:
            event.accept()
