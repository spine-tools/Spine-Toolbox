import sys
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon
from PySide6.QtGui import QPixmap

from PySide6.QtCore import QSettings


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


class StartUpMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Spine - Magic ToolBox")
        # Set the window icon to the PNG version
        self.setWindowIcon(QIcon("image/spinetoolbox_on_wht.png"))
        self.resize(800, 600)

        self.menu_bar = self.create_menu_bar()

        menu_frame = QFrame()
        menu_frame.setFrameShape(QFrame.StyledPanel)
        menu_frame.setStyleSheet("background-color: lightgray;")
        menu_frame.setFixedWidth(200)

        menu_layout = QVBoxLayout(menu_frame)
        menu_layout.setAlignment(Qt.AlignTop)

        menu_layout.addItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Fixed))

        folder_icon = self.style().standardIcon(QStyle.SP_DirIcon)
        folder_icon_button = QPushButton("Open Project...")
        folder_icon_button.setIcon(folder_icon)
        folder_icon_button.setIconSize(folder_icon.actualSize(QSize(32, 32)))
        folder_icon_button.setFlat(True)
        folder_icon_button.setStyleSheet("color: black;")
        folder_icon_button.setFixedSize(130, 30)
        folder_icon_button.setIconSize(folder_icon.actualSize(QSize(24, 24)))

        menu_layout.addWidget(folder_icon_button)

        # add spacer
        menu_layout.addItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Fixed))

        self.dropdown_groupbox = QGroupBox()
        self.dropdown_layout = QVBoxLayout()
        self.dropdown_groupbox.setLayout(self.dropdown_layout)
        self.dropdown_groupbox.hide()

        # Create a QPushButton for the dropdown menu item
        self.menu_item_2_button = QPushButton("Recent")
        self.menu_item_2_button.setFlat(True)
        self.menu_item_2_button.setStyleSheet("color: black;")

        # Add an arrow icon to the button
        self.arrow_icon = self.style().standardIcon(QStyle.SP_MediaPlay)
        self.menu_item_2_button.setIcon(self.arrow_icon)
        self.menu_item_2_button.setFixedSize(80, 30)
        self.menu_item_2_button.setIconSize(self.arrow_icon.actualSize(QSize(20, 20)))

        # Connect the button to the toggle_dropdown function
        self.menu_item_2_button.clicked.connect(self.toggle_dropdown)

        menu_layout.addWidget(self.menu_item_2_button)
        menu_layout.addWidget(self.dropdown_groupbox)

        # Add spacer
        menu_layout.addItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Fixed))

        menu_layout.addWidget(QLabel("Menu Item 3"))

        # Add central menu layout
        central_widget = QWidget()
        main_layout = QHBoxLayout(central_widget)
        main_layout.addWidget(menu_frame)

        self.setup_central_content(main_layout)

        self.setCentralWidget(central_widget)

    def setup_central_content(self, main_layout):
        central_layout = QVBoxLayout()
        main_layout.addLayout(central_layout)

        row1_layout = QHBoxLayout()
        row2_layout = QHBoxLayout()

        central_layout.addLayout(row1_layout)
        central_layout.addLayout(row2_layout)

        self.top_button1 = QPushButton("Beginner Tutorials")
        row1_layout.addWidget(self.top_button1)
        self.top_button1.setStyleSheet("text-align: left;")
        self.top_button1.setIcon(self.arrow_icon)
        self.top_button1.setIconSize(self.arrow_icon.actualSize(QSize(20, 20)))

        self.dropdown_groupbox1 = QGroupBox()
        self.dropdown_layout1 = QVBoxLayout()
        self.dropdown_groupbox1.setLayout(self.dropdown_layout1)
        self.dropdown_groupbox1.hide()

        self.top_button1.clicked.connect(self.toggle_dropdown1)
        central_layout.addWidget(self.dropdown_groupbox1)

        self.top_button2 = QPushButton("Advanced Tutorials")
        row2_layout.addWidget(self.top_button2)
        self.top_button2.setStyleSheet("text-align: left;")
        self.top_button2.setIcon(self.arrow_icon)
        self.top_button2.setIconSize(self.arrow_icon.actualSize(QSize(20, 20)))

        self.dropdown_groupbox2 = QGroupBox()
        self.dropdown_layout2 = QVBoxLayout()
        self.dropdown_groupbox2.setLayout(self.dropdown_layout2)
        self.dropdown_groupbox2.hide()

        self.top_button2.clicked.connect(self.toggle_dropdown2)
        central_layout.addWidget(self.dropdown_groupbox2)

        central_layout.addWidget(QLabel(""))

        self.create_dropdown_cards_beginners()


    def toggle_dropdown(self):
        # Toggle the dropdown state
        if self.dropdown_groupbox.isHidden():
            # Show the dropdown
            self.dropdown_groupbox.show()
            # Change icon to arrow down when expanding
            self.menu_item_2_button.setIcon(self.style().standardIcon(QStyle.SP_TitleBarUnshadeButton))

            # Add subitems
            self.add_subitems()
        else:
            # Hide the dropdown
            self.dropdown_groupbox.hide()
            # Change icon to arrow right when collapsing
            self.menu_item_2_button.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))

    def create_dropdown_cards_beginners(self):
        self.card1 = self.create_card(
            "This tutorial provides a step-by-step guide to setup a simple energy system with Spine Toolbox for SpineOpt. "
            "Spine Toolbox is used to create a workflow with databases and tools and SpineOpt is the tool that simulates/optimizes the energy system.",
            "C:/Users/ErmannoLoCascio/Spine-Toolbox/docs/source/img/tutorials_images/simple_system_schematic.png",
            "Open",
            self.open_tutorial1)

        self.card2 = self.create_card(
            "This tutorial provides a step-by-step guide to include reserve requirements in a simple energy system with Spine Toolbox for SpineOpt.",
            "C:/Users/ErmannoLoCascio/Spine-Toolbox/docs/source/img/tutorials_images/reserves_tutorial_schematic.png",
            "Open",
            self.open_tutorial2)

        self.card3 = self.create_card(
            "Welcome to this Spine Toolbox Case Study tutorial. Case Study A5 is one of the Spine Project case studies designed to verify Toolbox and Model capabilities. To this end, it reproduces an already existing study about hydropower on the Skellefte river, which models one week of operation of the fifteen power stations along the river.",
            "C:/Users/ErmannoLoCascio/Spine-Toolbox/docs/source/img/tutorials_images/case_study_a5_schematic.png",
            "Open",
            self.open_tutorial3)

        # Add three more cards to the second dropdown menu (Advanced Tutorials)
        self.card4 = self.create_card(
            "Tutorial 4 description",
            "image_path_for_tutorial4.png",
            "Open",
            self.open_tutorial4)

        self.card5 = self.create_card(
            "Tutorial 5 description",
            "image_path_for_tutorial5.png",
            "Open",
            self.open_tutorial5)

        self.card6 = self.create_card(
            "Tutorial 6 description",
            "image_path_for_tutorial6.png",
            "Open",
            self.open_tutorial6)

        # Add the newly created cards to dropdown_layout2
        self.dropdown_layout2.addWidget(self.card4)
        self.dropdown_layout2.addWidget(self.card5)
        self.dropdown_layout2.addWidget(self.card6)

    def add_subitems(self):
        # Clear existing subitems
        for i in reversed(range(self.dropdown_layout.count())):
            self.dropdown_layout.itemAt(i).widget().setParent(None)

        # Add subitems
        for i in range(5):
            subitem_label = QLabel(f"Subitem {i + 1}")
            self.dropdown_layout.addWidget(subitem_label)

    def adjust_layout(self, expand_card1):
        # Adjust layout to move Button 2 down if expand_card1 is True, else move Button 2 up
        central_layout = self.centralWidget().layout()
        row2_layout = central_layout.itemAt(1)

        if expand_card1:
            row2_layout.addWidget(self.top_button2)
        else:
            row2_layout.removeWidget(self.top_button2)
            row2_layout.insertWidget(1, self.top_button2)


    def create_card(self, title, image_path, button_text, button_function):
        card = QWidget()
        card_layout = QHBoxLayout(card)
        card.setMaximumWidth(500)

        card_image = QLabel()
        pixmap = QPixmap(image_path)
        smaller_pixmap = pixmap.scaled(QSize(200, 200))
        card_image.setPixmap(smaller_pixmap)
        card_layout.addWidget(card_image, alignment=Qt.AlignCenter)

        card_layout.addItem(QSpacerItem(50, 50, QSizePolicy.Expanding, QSizePolicy.Minimum))

        card_text = QLabel(title)
        card_text.setWordWrap(True)
        card_layout.addWidget(card_text, alignment=Qt.AlignCenter)

        card_layout.addItem(QSpacerItem(20, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))

        card_button = QPushButton(button_text)
        card_button.setFixedSize(80, 25)
        card_layout.addWidget(card_button, alignment=Qt.AlignCenter)

        card_button.clicked.connect(button_function)
        card_layout.setSpacing(10)

        self.dropdown_layout1.addWidget(card)
        return card

    def toggle_dropdown1(self):
        if self.dropdown_groupbox1.isHidden():
            # Show the dropdown
            self.dropdown_groupbox1.show()

            # Change icon to arrow down when expanding
            self.top_button1.setIcon(self.style().standardIcon(QStyle.SP_TitleBarUnshadeButton))

            # Adjust layout to move Button 2 down
            self.adjust_layout(True)

            if self.dropdown_groupbox2.isVisible():
                self.dropdown_groupbox2.hide()
                self.top_button2.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
                # Adjust layout to move Button 2 up
                self.adjust_layout(True)


        else:
            # Hide the dropdown
            self.dropdown_groupbox1.hide()

            # Change icon to arrow right when collapsing
            self.top_button1.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))

            # Adjust layout to move Button 2 up
            self.adjust_layout(False)


    def toggle_dropdown2(self):
        # Toggle the dropdown state
        if self.dropdown_groupbox2.isHidden():
            # Show the dropdown
            self.dropdown_groupbox2.show()
            # Change icon to arrow down when expanding
            self.top_button2.setIcon(self.style().standardIcon(QStyle.SP_TitleBarUnshadeButton))

            if self.dropdown_groupbox1.isVisible():
                self.dropdown_groupbox1.hide()
                self.top_button1.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
                # Adjust layout to move Button 2 up
                self.adjust_layout(False)

        else:
            # Hide the dropdown
            self.dropdown_groupbox2.hide()
            # Change icon to arrow right when collapsing
            self.top_button2.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))

    def open_tutorial1(self):
        print("Open tutorial 1")

    def open_tutorial2(self):
        print("Open tutorial 2")

    def open_tutorial3(self):
        print("Open tutorial 3")

    def open_tutorial4(self):
        print("Open tutorial 4")

    def open_tutorial5(self):
        print("Open tutorial 5")

    def open_tutorial6(self):
        print("Open tutorial 6")

    def create_menu_bar(self):
        menu_bar = self.menuBar()





app = QApplication(sys.argv)
window = StartUpMainWindow()
window.show()
sys.exit(app.exec())

