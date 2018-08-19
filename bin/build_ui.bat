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

ECHO building about.py
CALL pyside2-uic ../spinetoolbox/ui/about.ui -o ../spinetoolbox/ui/about.py.o
findstr /V /C:"# Created:" /C:"#      by:" ..\spinetoolbox\ui\about.py.o > ..\spinetoolbox\ui\about.py
del ..\spinetoolbox\ui\about.py.o

ECHO building add_data_connection.py
CALL pyside2-uic ../spinetoolbox/ui/add_data_connection.ui -o ../spinetoolbox/ui/add_data_connection.py.o
findstr /V /C:"# Created:" /C:"#      by:" ..\spinetoolbox\ui\add_data_connection.py.o > ..\spinetoolbox\ui\add_data_connection.py
del ..\spinetoolbox\ui\add_data_connection.py.o

ECHO building add_data_store.py
CALL pyside2-uic ../spinetoolbox/ui/add_data_store.ui -o ../spinetoolbox/ui/add_data_store.py.o
findstr /V /C:"# Created:" /C:"#      by:" ..\spinetoolbox\ui\add_data_store.py.o > ..\spinetoolbox\ui\add_data_store.py
del ..\spinetoolbox\ui\add_data_store.py.o

ECHO building add_db_reference.py
CALL pyside2-uic ../spinetoolbox/ui/add_db_reference.ui -o ../spinetoolbox/ui/add_db_reference.py.o
findstr /V /C:"# Created:" /C:"#      by:" ..\spinetoolbox\ui\add_db_reference.py.o > ..\spinetoolbox\ui\add_db_reference.py
del ..\spinetoolbox\ui\add_db_reference.py.o

ECHO building add_object_classes.py
CALL pyside2-uic ../spinetoolbox/ui/add_object_classes.ui -o ../spinetoolbox/ui/add_object_classes.py.o
findstr /V /C:"# Created:" /C:"#      by:" ..\spinetoolbox\ui\add_object_classes.py.o > ..\spinetoolbox\ui\add_object_classes.py
del ..\spinetoolbox\ui\add_object_classes.py.o

ECHO building add_relationship_classes.py
CALL pyside2-uic ../spinetoolbox/ui/add_relationship_classes.ui -o ../spinetoolbox/ui/add_relationship_classes.py.o
findstr /V /C:"# Created:" /C:"#      by:" ..\spinetoolbox\ui\add_relationship_classes.py.o > ..\spinetoolbox\ui\add_relationship_classes.py
del ..\spinetoolbox\ui\add_relationship_classes.py.o

ECHO building add_objects.py
CALL pyside2-uic ../spinetoolbox/ui/add_objects.ui -o ../spinetoolbox/ui/add_objects.py.o
findstr /V /C:"# Created:" /C:"#      by:" ..\spinetoolbox\ui\add_objects.py.o > ..\spinetoolbox\ui\add_objects.py
del ..\spinetoolbox\ui\add_objects.py.o

ECHO building add_relationships.py
CALL pyside2-uic ../spinetoolbox/ui/add_relationships.ui -o ../spinetoolbox/ui/add_relationships.py.o
findstr /V /C:"# Created:" /C:"#      by:" ..\spinetoolbox\ui\add_relationships.py.o > ..\spinetoolbox\ui\add_relationships.py
del ..\spinetoolbox\ui\add_relationships.py.o

ECHO building add_parameters.py
CALL pyside2-uic ../spinetoolbox/ui/add_parameters.ui -o ../spinetoolbox/ui/add_parameters.py.o
findstr /V /C:"# Created:" /C:"#      by:" ..\spinetoolbox\ui\add_parameters.py.o > ..\spinetoolbox\ui\add_parameters.py
del ..\spinetoolbox\ui\add_parameters.py.o

ECHO building add_parameter_values.py
CALL pyside2-uic ../spinetoolbox/ui/add_parameter_values.ui -o ../spinetoolbox/ui/add_parameter_values.py.o
findstr /V /C:"# Created:" /C:"#      by:" ..\spinetoolbox\ui\add_parameter_values.py.o > ..\spinetoolbox\ui\add_parameter_values.py
del ..\spinetoolbox\ui\add_parameter_values.py.o

ECHO building add_tool.py
CALL pyside2-uic ../spinetoolbox/ui/add_tool.ui -o ../spinetoolbox/ui/add_tool.py.o
findstr /V /C:"# Created:" /C:"#      by:" ..\spinetoolbox\ui\add_tool.py.o > ..\spinetoolbox\ui\add_tool.py
del ..\spinetoolbox\ui\add_tool.py.o

ECHO building add_view.py
CALL pyside2-uic ../spinetoolbox/ui/add_view.ui -o ../spinetoolbox/ui/add_view.py.o
findstr /V /C:"# Created:" /C:"#      by:" ..\spinetoolbox\ui\add_view.py.o > ..\spinetoolbox\ui\add_view.py
del ..\spinetoolbox\ui\add_view.py.o

ECHO building data_store_form.py
CALL pyside2-uic ../spinetoolbox/ui/data_store_form.ui -o ../spinetoolbox/ui/data_store_form.py.o
findstr /V /C:"# Created:" /C:"#      by:" ..\spinetoolbox\ui\data_store_form.py.o > ..\spinetoolbox\ui\data_store_form.py
del ..\spinetoolbox\ui\data_store_form.py.o

ECHO building edit_datapackage_primary_keys.py
CALL pyside2-uic ../spinetoolbox/ui/edit_datapackage_primary_keys.ui -o ../spinetoolbox/ui/edit_datapackage_primary_keys.py.o
findstr /V /C:"# Created:" /C:"#      by:" ..\spinetoolbox\ui\edit_datapackage_primary_keys.py.o > ..\spinetoolbox\ui\edit_datapackage_primary_keys.py
del ..\spinetoolbox\ui\edit_datapackage_primary_keys.py.o

ECHO building edit_datapackage_foreign_keys.py
CALL pyside2-uic ../spinetoolbox/ui/edit_datapackage_foreign_keys.ui -o ../spinetoolbox/ui/edit_datapackage_foreign_keys.py.o
findstr /V /C:"# Created:" /C:"#      by:" ..\spinetoolbox\ui\edit_datapackage_foreign_keys.py.o > ..\spinetoolbox\ui\edit_datapackage_foreign_keys.py
del ..\spinetoolbox\ui\edit_datapackage_foreign_keys.py.o

ECHO building mainwindow.py
CALL pyside2-uic ../spinetoolbox/ui/mainwindow.ui -o ../spinetoolbox/ui/mainwindow.py.o
findstr /V /C:"# Created:" /C:"#      by:" ..\spinetoolbox\ui\mainwindow.py.o > ..\spinetoolbox\ui\mainwindow.py
del ..\spinetoolbox\ui\mainwindow.py.o

ECHO building project_form.py
CALL pyside2-uic ../spinetoolbox/ui/project_form.ui -o ../spinetoolbox/ui/project_form.py.o
findstr /V /C:"# Created:" /C:"#      by:" ..\spinetoolbox\ui\project_form.py.o > ..\spinetoolbox\ui\project_form.py
del ..\spinetoolbox\ui\project_form.py.o

ECHO building settings.py
CALL pyside2-uic ../spinetoolbox/ui/settings.ui -o ../spinetoolbox/ui/settings.py.o
findstr /V /C:"# Created:" /C:"#      by:" ..\spinetoolbox\ui\settings.py.o > ..\spinetoolbox\ui\settings.py
del ..\spinetoolbox\ui\settings.py.o

ECHO building spine_datapackage_form.py
CALL pyside2-uic ../spinetoolbox/ui/spine_datapackage_form.ui -o ../spinetoolbox/ui/spine_datapackage_form.py.o
findstr /V /C:"# Created:" /C:"#      by:" ..\spinetoolbox\ui\spine_datapackage_form.py.o > ..\spinetoolbox\ui\spine_datapackage_form.py
del ..\spinetoolbox\ui\spine_datapackage_form.py.o

ECHO building subwindow_data_connection.py
CALL pyside2-uic ../spinetoolbox/ui/subwindow_data_connection.ui -o ../spinetoolbox/ui/subwindow_data_connection.py.o
findstr /V /C:"# Created:" /C:"#      by:" ..\spinetoolbox\ui\subwindow_data_connection.py.o > ..\spinetoolbox\ui\subwindow_data_connection.py
del ..\spinetoolbox\ui\subwindow_data_connection.py.o

ECHO building subwindow_data_store.py
CALL pyside2-uic ../spinetoolbox/ui/subwindow_data_store.ui -o ../spinetoolbox/ui/subwindow_data_store.py.o
findstr /V /C:"# Created:" /C:"#      by:" ..\spinetoolbox\ui\subwindow_data_store.py.o > ..\spinetoolbox\ui\subwindow_data_store.py
del ..\spinetoolbox\ui\subwindow_data_store.py.o

ECHO building subwindow_tool.py
CALL pyside2-uic ../spinetoolbox/ui/subwindow_tool.ui -o ../spinetoolbox/ui/subwindow_tool.py.o
findstr /V /C:"# Created:" /C:"#      by:" ..\spinetoolbox\ui\subwindow_tool.py.o > ..\spinetoolbox\ui\subwindow_tool.py
del ..\spinetoolbox\ui\subwindow_tool.py.o

ECHO building subwindow_view.py
CALL pyside2-uic ../spinetoolbox/ui/subwindow_view.ui -o ../spinetoolbox/ui/subwindow_view.py.o
findstr /V /C:"# Created:" /C:"#      by:" ..\spinetoolbox\ui\subwindow_view.py.o > ..\spinetoolbox\ui\subwindow_view.py
del ..\spinetoolbox\ui\subwindow_view.py.o

ECHO building tool_template_form.py
CALL pyside2-uic ../spinetoolbox/ui/tool_template_form.ui -o ../spinetoolbox/ui/tool_template_form.py.o
findstr /V /C:"# Created:" /C:"#      by:" ..\spinetoolbox\ui\tool_template_form.py.o > ..\spinetoolbox\ui\tool_template_form.py
del ..\spinetoolbox\ui\tool_template_form.py.o

ECHO building resources_icons_rc.py
CALL pyside2-rcc -o ../spinetoolbox/resources_icons_rc.py ../spinetoolbox/ui/resources/resources_icons.qrc

ECHO building resources_logos_rc.py
CALL pyside2-rcc -o ../spinetoolbox/resources_logos_rc.py ../spinetoolbox/ui/resources/resources_logos.qrc

ECHO --- Build completed ---
ECHO.
ECHO --- APPENDING LICENSE TO .UI FILES ---
CALL append_license_xml ..\spinetoolbox\ui\about.ui
CALL append_license_xml ..\spinetoolbox\ui\add_data_connection.ui
CALL append_license_xml ..\spinetoolbox\ui\add_data_store.ui
CALL append_license_xml ..\spinetoolbox\ui\add_db_reference.ui
CALL append_license_xml ..\spinetoolbox\ui\add_objects.ui
CALL append_license_xml ..\spinetoolbox\ui\add_object_classes.ui
CALL append_license_xml ..\spinetoolbox\ui\add_relationship_classes.ui
CALL append_license_xml ..\spinetoolbox\ui\add_relationships.ui
CALL append_license_xml ..\spinetoolbox\ui\add_parameters.ui
CALL append_license_xml ..\spinetoolbox\ui\add_parameter_values.ui
CALL append_license_xml ..\spinetoolbox\ui\add_tool.ui
CALL append_license_xml ..\spinetoolbox\ui\add_view.ui
CALL append_license_xml ..\spinetoolbox\ui\data_store_form.ui
CALL append_license_xml ..\spinetoolbox\ui\edit_datapackage_primary_keys.ui
CALL append_license_xml ..\spinetoolbox\ui\edit_datapackage_foreign_keys.ui
CALL append_license_xml ..\spinetoolbox\ui\mainwindow.ui
CALL append_license_xml ..\spinetoolbox\ui\project_form.ui
CALL append_license_xml ..\spinetoolbox\ui\settings.ui
CALL append_license_xml ..\spinetoolbox\ui\spine_datapackage_form.ui
CALL append_license_xml ..\spinetoolbox\ui\subwindow_data_connection.ui
CALL append_license_xml ..\spinetoolbox\ui\subwindow_data_store.ui
CALL append_license_xml ..\spinetoolbox\ui\subwindow_tool.ui
CALL append_license_xml ..\spinetoolbox\ui\subwindow_view.ui
CALL append_license_xml ..\spinetoolbox\ui\tool_template_form.ui
ECHO.
ECHO --- APPENDING LICENSE TO AUTOGENERATED .PY FILES ---
CALL append_license_py ..\spinetoolbox\ui\about.py
CALL append_license_py ..\spinetoolbox\ui\add_data_connection.py
CALL append_license_py ..\spinetoolbox\ui\add_data_store.py
CALL append_license_py ..\spinetoolbox\ui\add_db_reference.py
CALL append_license_py ..\spinetoolbox\ui\add_objects.py
CALL append_license_py ..\spinetoolbox\ui\add_object_classes.py
CALL append_license_py ..\spinetoolbox\ui\add_relationship_classes.py
CALL append_license_py ..\spinetoolbox\ui\add_relationships.py
CALL append_license_py ..\spinetoolbox\ui\add_parameters.py
CALL append_license_py ..\spinetoolbox\ui\add_parameter_values.py
CALL append_license_py ..\spinetoolbox\ui\add_tool.py
CALL append_license_py ..\spinetoolbox\ui\add_view.py
CALL append_license_py ..\spinetoolbox\ui\data_store_form.py
CALL append_license_py ..\spinetoolbox\ui\edit_datapackage_primary_keys.py
CALL append_license_py ..\spinetoolbox\ui\edit_datapackage_foreign_keys.py
CALL append_license_py ..\spinetoolbox\ui\mainwindow.py
CALL append_license_py ..\spinetoolbox\ui\project_form.py
CALL append_license_py ..\spinetoolbox\ui\settings.py
CALL append_license_py ..\spinetoolbox\ui\spine_datapackage_form.py
CALL append_license_py ..\spinetoolbox\ui\subwindow_data_connection.py
CALL append_license_py ..\spinetoolbox\ui\subwindow_data_store.py
CALL append_license_py ..\spinetoolbox\ui\subwindow_tool.py
CALL append_license_py ..\spinetoolbox\ui\subwindow_view.py
CALL append_license_py ..\spinetoolbox\ui\tool_template_form.py
CALL append_license_py ..\spinetoolbox\resources_icons_rc.py
CALL append_license_py ..\spinetoolbox\resources_logos_rc.py
