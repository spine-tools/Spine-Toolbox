from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QLabel, QVBoxLayout, QWidget, QHBoxLayout

import sys

from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon
from PySide6.QtGui import QPixmap

from PySide6.QtCore import QSettings
from spinetoolbox.ui_main import ToolboxUI

from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QVBoxLayout,
    QWidget,
    QSpacerItem,
    QSizePolicy,
    QPushButton,
    QStyle,
    QGroupBox,
    QGridLayout
)

class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.w = None  # No external window yet.
        self.button = QPushButton("Push for Window")
        self.button.clicked.connect(self.show_new_window)
        self.setCentralWidget(self.button)

        # Startup window
        self.w = StartUpWindow()
        self.w.show()

    def show_new_window(self, checked):
        if self.w is None:
            self.w = StartUpWindow()
        self.w.show()

class StartUpWindow(QWidget):
    """
    This "window" is a QWidget. If it has no parent, it
    will appear as a free-floating window as we want.
    """
    def __init__(self):
        super().__init__()

        # Left bar menu
        left_menu = QWidget()
        left_menu.setFixedWidth(100)  # Set the width as desired, for example, 100 pixels
        left_layout = QVBoxLayout()
        # Button
        button = QPushButton("Click me!")
        button.clicked.connect(self.open_tutorial)  # Connect clicked signal to open_tutorial function
        left_layout.addWidget(button)

        left_layout.addWidget(QPushButton("Button 1"))
        left_layout.addWidget(QPushButton("Button 2"))
        left_menu.setLayout(left_layout)

        # Central layout
        central_layout = QVBoxLayout()
        self.label = QLabel("Start Up window")
        central_layout.addWidget(self.label)

        # Main layout combining left bar menu and central layout
        main_layout = QHBoxLayout()
        main_layout.addWidget(left_menu)
        main_layout.addLayout(central_layout)
        self.setLayout(main_layout)

        self.setWindowTitle("Spine - Magic ToolBox")
        # Set the window icon to the PNG version
        self.setWindowIcon(QIcon("image/spinetoolbox_on_wht.png"))
        self.resize(1000, 800)


    def open_tutorial(self):
        print("Open tutorial button clicked!")



app = QApplication(sys.argv)
w = MainWindow()
w.show()
sys.exit(app.exec())
