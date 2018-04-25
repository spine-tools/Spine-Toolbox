@ECHO OFF
@TITLE Build Spine Toolbox GUI

ECHO.
ECHO ^<Script for Building Spine Toolbox GUI^>
ECHO Copyright (C) ^<2017-2018^>  ^<VTT Technical Research Centre of Finland^>
ECHO This program comes with ABSOLUTELY NO WARRANTY; for details see 'about'.
ECHO box in the application. This is free software, and you are welcome to
ECHO redistribute it under certain conditions; See files COPYING and
ECHO COPYING.LESSER for details.
ECHO.

PAUSE

ECHO --- pyside2-uic version ---
CALL pyside2-uic --version
ECHO --- pyside2-rcc version ---
CALL pyside2-rcc -version
ECHO.
ECHO --- Building Spine Toolbox GUI ---

ECHO building mainwindow.py
CALL pyside2-uic ../spinetoolbox/ui/mainwindow.ui -o ../spinetoolbox/ui/mainwindow.py.o
findstr /V /C:"# Created:" /C:"#      by:" ..\spinetoolbox\ui\mainwindow.py.o > ..\spinetoolbox\ui\mainwindow.py
del ..\spinetoolbox\ui\mainwindow.py.o

ECHO building data_store_form.py
CALL pyside2-uic ../spinetoolbox/ui/data_store_form.ui -o ../spinetoolbox/ui/data_store_form.py.o
findstr /V /C:"# Created:" /C:"#      by:" ..\spinetoolbox\ui\data_store_form.py.o > ..\spinetoolbox\ui\data_store_form.py
del ..\spinetoolbox\ui\data_store_form.py.o

ECHO building about.py
CALL pyside2-uic ../spinetoolbox/ui/about.ui -o ../spinetoolbox/ui/about.py.o
findstr /V /C:"# Created:" /C:"#      by:" ..\spinetoolbox\ui\about.py.o > ..\spinetoolbox\ui\about.py
del ..\spinetoolbox\ui\about.py.o

REM ECHO building subwindow.py
REM CALL pyside2-uic ../spinetoolbox/ui/subwindow.ui -o ../spinetoolbox/ui/subwindow.py.o
REM findstr /V /C:"# Created:" /C:"#      by:" ..\spinetoolbox\ui\subwindow.py.o > ..\spinetoolbox\ui\subwindow.py
REM del ..\spinetoolbox\ui\subwindow.py.o

ECHO building subwindow_data_store.py
CALL pyside2-uic ../spinetoolbox/ui/subwindow_data_store.ui -o ../spinetoolbox/ui/subwindow_data_store.py.o
findstr /V /C:"# Created:" /C:"#      by:" ..\spinetoolbox\ui\subwindow_data_store.py.o > ..\spinetoolbox\ui\subwindow_data_store.py
del ..\spinetoolbox\ui\subwindow_data_store.py.o

ECHO building subwindow_data_connection.py
CALL pyside2-uic ../spinetoolbox/ui/subwindow_data_connection.ui -o ../spinetoolbox/ui/subwindow_data_connection.py.o
findstr /V /C:"# Created:" /C:"#      by:" ..\spinetoolbox\ui\subwindow_data_connection.py.o > ..\spinetoolbox\ui\subwindow_data_connection.py
del ..\spinetoolbox\ui\subwindow_data_connection.py.o

ECHO building subwindow_tool.py
CALL pyside2-uic ../spinetoolbox/ui/subwindow_tool.ui -o ../spinetoolbox/ui/subwindow_tool.py.o
findstr /V /C:"# Created:" /C:"#      by:" ..\spinetoolbox\ui\subwindow_tool.py.o > ..\spinetoolbox\ui\subwindow_tool.py
del ..\spinetoolbox\ui\subwindow_tool.py.o

ECHO building subwindow_view.py
CALL pyside2-uic ../spinetoolbox/ui/subwindow_view.ui -o ../spinetoolbox/ui/subwindow_view.py.o
findstr /V /C:"# Created:" /C:"#      by:" ..\spinetoolbox\ui\subwindow_view.py.o > ..\spinetoolbox\ui\subwindow_view.py
del ..\spinetoolbox\ui\subwindow_view.py.o

ECHO building project_form.py
CALL pyside2-uic ../spinetoolbox/ui/project_form.ui -o ../spinetoolbox/ui/project_form.py.o
findstr /V /C:"# Created:" /C:"#      by:" ..\spinetoolbox\ui\project_form.py.o > ..\spinetoolbox\ui\project_form.py
del ..\spinetoolbox\ui\project_form.py.o

ECHO building settings.py
CALL pyside2-uic ../spinetoolbox/ui/settings.ui -o ../spinetoolbox/ui/settings.py.o
findstr /V /C:"# Created:" /C:"#      by:" ..\spinetoolbox\ui\settings.py.o > ..\spinetoolbox\ui\settings.py
del ..\spinetoolbox\ui\settings.py.o

ECHO building add_data_store.py
CALL pyside2-uic ../spinetoolbox/ui/add_data_store.ui -o ../spinetoolbox/ui/add_data_store.py.o
findstr /V /C:"# Created:" /C:"#      by:" ..\spinetoolbox\ui\add_data_store.py.o > ..\spinetoolbox\ui\add_data_store.py
del ..\spinetoolbox\ui\add_data_store.py.o

ECHO building add_data_connection.py
CALL pyside2-uic ../spinetoolbox/ui/add_data_connection.ui -o ../spinetoolbox/ui/add_data_connection.py.o
findstr /V /C:"# Created:" /C:"#      by:" ..\spinetoolbox\ui\add_data_connection.py.o > ..\spinetoolbox\ui\add_data_connection.py
del ..\spinetoolbox\ui\add_data_connection.py.o

ECHO building add_tool.py
CALL pyside2-uic ../spinetoolbox/ui/add_tool.ui -o ../spinetoolbox/ui/add_tool.py.o
findstr /V /C:"# Created:" /C:"#      by:" ..\spinetoolbox\ui\add_tool.py.o > ..\spinetoolbox\ui\add_tool.py
del ..\spinetoolbox\ui\add_tool.py.o

ECHO building add_view.py
CALL pyside2-uic ../spinetoolbox/ui/add_view.ui -o ../spinetoolbox/ui/add_view.py.o
findstr /V /C:"# Created:" /C:"#      by:" ..\spinetoolbox\ui\add_view.py.o > ..\spinetoolbox\ui\add_view.py
del ..\spinetoolbox\ui\add_view.py.o

ECHO building edit_datapackage_keys.py
CALL pyside2-uic ../spinetoolbox/ui/edit_datapackage_keys.ui -o ../spinetoolbox/ui/edit_datapackage_keys.py.o
findstr /V /C:"# Created:" /C:"#      by:" ..\spinetoolbox\ui\edit_datapackage_keys.py.o > ..\spinetoolbox\ui\edit_datapackage_keys.py
del ..\spinetoolbox\ui\edit_datapackage_keys.py.o

ECHO building add_connection_string.py
CALL pyside2-uic ../spinetoolbox/ui/add_connection_string.ui -o ../spinetoolbox/ui/add_connection_string.py.o
findstr /V /C:"# Created:" /C:"#      by:" ..\spinetoolbox\ui\add_connection_string.py.o > ..\spinetoolbox\ui\add_connection_string.py
del ..\spinetoolbox\ui\add_connection_string.py.o

ECHO building Spine_data_explorer.py
CALL pyside2-uic ../spinetoolbox/ui/Spine_data_explorer.ui -o ../spinetoolbox/ui/Spine_data_explorer.py.o
findstr /V /C:"# Created:" /C:"#      by:" ..\spinetoolbox\ui\Spine_data_explorer.py.o > ..\spinetoolbox\ui\Spine_data_explorer.py
del ..\spinetoolbox\ui\Spine_data_explorer.py.o

ECHO building resources_icons_rc.py
CALL pyside2-rcc -o ../spinetoolbox/resources_icons_rc.py ../spinetoolbox/ui/resources/resources_icons.qrc

ECHO building resources_logos_rc.py
CALL pyside2-rcc -o ../spinetoolbox/resources_logos_rc.py ../spinetoolbox/ui/resources/resources_logos.qrc

ECHO --- Build completed ---
ECHO.
ECHO --- APPENDING LICENSE TO .UI FILES ---
CALL append_license_xml ..\spinetoolbox\ui\mainwindow.ui
CALL append_license_xml ..\spinetoolbox\ui\data_store_form.ui
CALL append_license_xml ..\spinetoolbox\ui\about.ui
REM CALL append_license_xml ..\spinetoolbox\ui\subwindow.ui
CALL append_license_xml ..\spinetoolbox\ui\subwindow_data_store.ui
CALL append_license_xml ..\spinetoolbox\ui\subwindow_data_connection.ui
CALL append_license_xml ..\spinetoolbox\ui\subwindow_tool.ui
CALL append_license_xml ..\spinetoolbox\ui\subwindow_view.ui
CALL append_license_xml ..\spinetoolbox\ui\project_form.ui
CALL append_license_xml ..\spinetoolbox\ui\settings.ui
CALL append_license_xml ..\spinetoolbox\ui\add_data_store.ui
CALL append_license_xml ..\spinetoolbox\ui\add_data_connection.ui
CALL append_license_xml ..\spinetoolbox\ui\add_tool.ui
CALL append_license_xml ..\spinetoolbox\ui\add_view.ui
CALL append_license_xml ..\spinetoolbox\ui\edit_datapackage_keys.ui
ECHO.
ECHO --- APPENDING LICENSE TO AUTOGENERATED .PY FILES ---
CALL append_license_py ..\spinetoolbox\ui\mainwindow.py
CALL append_license_py ..\spinetoolbox\ui\data_store_form.py
CALL append_license_py ..\spinetoolbox\ui\about.py
REM CALL append_license_py ..\spinetoolbox\ui\subwindow.py
CALL append_license_py ..\spinetoolbox\ui\subwindow_data_store.py
CALL append_license_py ..\spinetoolbox\ui\subwindow_data_connection.py
CALL append_license_py ..\spinetoolbox\ui\subwindow_tool.py
CALL append_license_py ..\spinetoolbox\ui\subwindow_view.py
CALL append_license_py ..\spinetoolbox\ui\project_form.py
CALL append_license_py ..\spinetoolbox\ui\settings.py
CALL append_license_py ..\spinetoolbox\ui\add_data_store.py
CALL append_license_py ..\spinetoolbox\ui\add_data_connection.py
CALL append_license_py ..\spinetoolbox\ui\add_tool.py
CALL append_license_py ..\spinetoolbox\ui\add_view.py
CALL append_license_py ..\spinetoolbox\ui\edit_datapackage_keys.py
CALL append_license_py ..\spinetoolbox\resources_icons_rc.py
CALL append_license_py ..\spinetoolbox\resources_logos_rc.py
