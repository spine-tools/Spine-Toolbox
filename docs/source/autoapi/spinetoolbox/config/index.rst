:mod:`spinetoolbox.config`
==========================

.. py:module:: spinetoolbox.config

.. autoapi-nested-parse::

   Application constants and style sheets

   :author: P. Savolainen (VTT)
   :date:   2.1.2018



Module Contents
---------------

.. data:: REQUIRED_SPINE_ENGINE_VERSION
   :annotation: = 0.4.0

   

.. data:: REQUIRED_SPINEDB_API_VERSION
   :annotation: = 0.1.14

   

.. data:: LATEST_PROJECT_VERSION
   :annotation: = 1

   

.. data:: INVALID_CHARS
   :annotation: = ['<', '>', ':', '"', '/', '\\', '|', '?', '*', '.']

   

.. data:: INVALID_FILENAME_CHARS
   :annotation: = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']

   

.. data:: _frozen
   

   

.. data:: _path_to_executable
   

   

.. data:: APPLICATION_PATH
   

   

.. data:: _program_root
   

   

.. data:: DEFAULT_WORK_DIR
   

   

.. data:: DOCUMENTATION_PATH
   

   

.. data:: PLUGINS_PATH
   

   

.. data:: TOOL_OUTPUT_DIR
   :annotation: = output

   

.. data:: _on_windows
   

   

.. function:: _executable(name)

   Appends a .exe extension to `name` on Windows platform.


.. data:: GAMS_EXECUTABLE
   

   

.. data:: GAMSIDE_EXECUTABLE
   

   

.. data:: JULIA_EXECUTABLE
   

   

.. data:: PYTHON_EXECUTABLE
   

   

.. data:: TOOL_TYPES
   :annotation: = ['Julia', 'Python', 'GAMS', 'Executable']

   

.. data:: REQUIRED_KEYS
   :annotation: = ['name', 'tooltype', 'includes']

   

.. data:: OPTIONAL_KEYS
   :annotation: = ['description', 'short_name', 'inputfiles', 'inputfiles_opt', 'outputfiles', 'cmdline_args', 'execute_in_work']

   

.. data:: LIST_REQUIRED_KEYS
   :annotation: = ['includes', 'inputfiles', 'inputfiles_opt', 'outputfiles']

   

.. data:: JL_REPL_TIME_TO_DEAD
   :annotation: = 5.0

   

.. data:: JL_REPL_RESTART_LIMIT
   :annotation: = 3

   

.. data:: PROJECT_FILENAME
   :annotation: = project.json

   

.. data:: STATUSBAR_SS
   :annotation: = QStatusBar{background-color: #EBEBE0;border-width: 1px;border-color: gray;border-style: groove;}

   

.. data:: SETTINGS_SS
   :annotation: = #SettingsForm{background-color: ghostwhite;}QLabel{color: black;}QLineEdit{font-size: 11px;}QGroupBox{border: 2px solid gray; background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: 0 #80B0FF, stop: 1 #e6efff);border-radius: 5px;margin-top: 0.5em;}QGroupBox:title{border-radius: 2px; background-color: ghostwhite;subcontrol-origin: margin;subcontrol-position: top center;padding-top: 0px;padding-bottom: 0px;padding-right: 3px;padding-left: 3px;}QCheckBox{outline-style: dashed; outline-width: 1px; outline-color: white;}QPushButton{background-color: #505F69; border: 1px solid #29353d; color: #F0F0F0; border-radius: 4px; padding: 3px; outline: none;}QPushButton:disabled {background-color: #32414B; border: 1px solid #29353d; color: #787878; border-radius: 4px; padding: 3px;}QPushButton::menu-indicator {subcontrol-origin: padding; subcontrol-position: bottom right; bottom: 4px;}QPushButton:focus{background-color: #637683; border: 1px solid #148CD2;}QPushButton:hover{border: 1px solid #148CD2; color: #F0F0F0;}QPushButton:pressed{background-color: #19232D; border: 1px solid #19232D;}QSlider::groove:horizontal{background: #e1e1e1; border: 1px solid #a4a4a4; height: 5px; margin: 2px 0; border-radius: 2px;}QSlider::handle:horizontal{background: #fafafa; border: 1px solid #a4a4a4; width: 12px; margin: -5px 0; border-radius: 2px;}QSlider::add-page:horizontal{background: transparent;}QSlider::sub-page:horizontal{background: transparent;}

   

.. data:: ICON_TOOLBAR_SS
   :annotation: = QToolBar{spacing: 6px; background: qlineargradient(x1: 1, y1: 1, x2: 0, y2: 0, stop: 0 #cce0ff, stop: 1 #66a1ff);padding: 3px;border-style: solid;}QToolButton{background-color: white;border-width: 1px;border-style: inset;border-color: darkslategray;border-radius: 2px;}QToolButton:pressed {background-color: lightGray;}QLabel{color:black;padding: 3px;}

   

.. data:: PARAMETER_TAG_TOOLBAR_SS
   

   

.. data:: TEXTBROWSER_SS
   :annotation: = QTextBrowser {background-color: #19232D; border: 1px solid #32414B; color: #F0F0F0; border-radius: 2px;}QTextBrowser:hover,QTextBrowser:selected,QTextBrowser:pressed {border: 1px solid #668599;}

   

.. data:: MAINWINDOW_SS
   :annotation: = QMainWindow::separator{width: 3px; background-color: lightgray; border: 1px solid white;}QPushButton{background-color: #505F69; border: 1px solid #29353d; color: #F0F0F0; border-radius: 4px; padding: 3px; outline: none; min-width: 75px;}QPushButton:disabled {background-color: #32414B; border: 1px solid #29353d; color: #787878; border-radius: 4px; padding: 3px;}QPushButton::menu-indicator {subcontrol-origin: padding; subcontrol-position: bottom right; bottom: 4px;}QPushButton:focus{background-color: #637683; border: 1px solid #148CD2;}QPushButton:hover{border: 1px solid #148CD2; color: #F0F0F0;}QPushButton:pressed{background-color: #19232D; border: 1px solid #19232D;}QToolButton:focus{border-color: black; border-width: 1px; border-style: ridge;}QToolButton:pressed{background-color: #f2f2f2;}QToolButton::menu-indicator{width: 0px;}QCheckBox{padding: 2px; spacing: 10px; outline-style: dashed; outline-width: 1px; outline-color: black;}QComboBox:focus{border-color: black; border-width: 1px; border-style: ridge;}QLineEdit:focus{border-color: black; border-width: 1px; border-style: ridge;}QTextEdit:focus{border-color: black; border-width: 1px; border-style: ridge;}QTreeView:focus{border-color: darkslategray; border-width: 2px; border-style: ridge;}

   

.. data:: TREEVIEW_HEADER_SS
   :annotation: = QHeaderView::section{background-color: #ecd8c6; font-size: 12px;}

   

.. data:: PIVOT_TABLE_HEADER_COLOR
   :annotation: = #efefef

   

