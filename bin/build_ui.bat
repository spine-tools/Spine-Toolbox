@ECHO OFF
@TITLE Build Spine Toolbox GUI

ECHO.
ECHO ^<Script for Building Spine Toolbox GUI^>
ECHO Copyright (C) ^<2017-2018^>  ^<Spine project consortium^>
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

ECHO building add_tool.py
CALL pyside2-uic ../spinetoolbox/ui/add_tool.ui -o ../spinetoolbox/ui/add_tool.py.o
findstr /V /C:"# Created:" /C:"#      by:" ..\spinetoolbox\ui\add_tool.py.o > ..\spinetoolbox\ui\add_tool.py
del ..\spinetoolbox\ui\add_tool.py.o

ECHO building add_view.py
CALL pyside2-uic ../spinetoolbox/ui/add_view.ui -o ../spinetoolbox/ui/add_view.py.o
findstr /V /C:"# Created:" /C:"#      by:" ..\spinetoolbox\ui\add_view.py.o > ..\spinetoolbox\ui\add_view.py
del ..\spinetoolbox\ui\add_view.py.o

ECHO building duration_editor.py
CALL pyside2-uic ../spinetoolbox/ui/duration_editor.ui -o ../spinetoolbox/ui/duration_editor.py.o
findstr /V /C:"# Created:" /C:"#      by:" ..\spinetoolbox\ui\duration_editor.py.o > ..\spinetoolbox\ui\duration_editor.py
del ..\spinetoolbox\ui\duration_editor.py.o

ECHO building datetime_editor.py
CALL pyside2-uic ../spinetoolbox/ui/datetime_editor.ui -o ../spinetoolbox/ui/datetime_editor.py.o
findstr /V /C:"# Created:" /C:"#      by:" ..\spinetoolbox\ui\datetime_editor.py.o > ..\spinetoolbox\ui\datetime_editor.py
del ..\spinetoolbox\ui\datetime_editor.py.o

ECHO building graph_view_form.py
CALL pyside2-uic ../spinetoolbox/ui/graph_view_form.ui -o ../spinetoolbox/ui/graph_view_form.py.o
findstr /V /C:"# Created:" /C:"#      by:" ..\spinetoolbox\ui\graph_view_form.py.o > ..\spinetoolbox\ui\graph_view_form.py
del ..\spinetoolbox\ui\graph_view_form.py.o

ECHO building mainwindow.py
CALL pyside2-uic ../spinetoolbox/ui/mainwindow.ui -o ../spinetoolbox/ui/mainwindow.py.o
findstr /V /C:"# Created:" /C:"#      by:" ..\spinetoolbox\ui\mainwindow.py.o > ..\spinetoolbox\ui\mainwindow.py
del ..\spinetoolbox\ui\mainwindow.py.o

ECHO building parameter_value_editor.py
CALL pyside2-uic ../spinetoolbox/ui/parameter_value_editor.ui -o ../spinetoolbox/ui/parameter_value_editor.py.o
findstr /V /C:"# Created:" /C:"#      by:" ..\spinetoolbox\ui\parameter_value_editor.py.o > ..\spinetoolbox\ui\parameter_value_editor.py
del ..\spinetoolbox\ui\parameter_value_editor.py.o

ECHO building plain_parameter_value_editor.py
CALL pyside2-uic ../spinetoolbox/ui/plain_parameter_value_editor.ui -o ../spinetoolbox/ui/plain_parameter_value_editor.py.o
findstr /V /C:"# Created:" /C:"#      by:" ..\spinetoolbox\ui\plain_parameter_value_editor.py.o > ..\spinetoolbox\ui\plain_parameter_value_editor.py
del ..\spinetoolbox\ui\plain_parameter_value_editor.py.o

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

ECHO building tabular_view_form.py
CALL pyside2-uic ../spinetoolbox/ui/tabular_view_form.ui -o ../spinetoolbox/ui/tabular_view_form.py.o
findstr /V /C:"# Created:" /C:"#      by:" ..\spinetoolbox\ui\tabular_view_form.py.o > ..\spinetoolbox\ui\tabular_view_form.py
del ..\spinetoolbox\ui\tabular_view_form.py.o

ECHO building time_pattern_editor.py
CALL pyside2-uic ../spinetoolbox/ui/time_pattern_editor.ui -o ../spinetoolbox/ui/time_pattern_editor.py.o
findstr /V /C:"# Created:" /C:"#      by:" ..\spinetoolbox\ui\time_pattern_editor.py.o > ..\spinetoolbox\ui\time_pattern_editor.py
del ..\spinetoolbox\ui\time_pattern_editor.py.o

ECHO building time_series_fixed_resolution_editor.py
CALL pyside2-uic ../spinetoolbox/ui/time_series_fixed_resolution_editor.ui -o ../spinetoolbox/ui/time_series_fixed_resolution_editor.py.o
findstr /V /C:"# Created:" /C:"#      by:" ..\spinetoolbox\ui\time_series_fixed_resolution_editor.py.o > ..\spinetoolbox\ui\time_series_fixed_resolution_editor.py
del ..\spinetoolbox\ui\time_series_fixed_resolution_editor.py.o

ECHO building time_series_variable_resolution_editor.py
CALL pyside2-uic ../spinetoolbox/ui/time_series_variable_resolution_editor.ui -o ../spinetoolbox/ui/time_series_variable_resolution_editor.py.o
findstr /V /C:"# Created:" /C:"#      by:" ..\spinetoolbox\ui\time_series_variable_resolution_editor.py.o > ..\spinetoolbox\ui\time_series_variable_resolution_editor.py
del ..\spinetoolbox\ui\time_series_variable_resolution_editor.py.o

ECHO building tool_configuration_assistant.py
CALL pyside2-uic ../spinetoolbox/ui/tool_configuration_assistant.ui -o ../spinetoolbox/ui/tool_configuration_assistant.py.o
findstr /V /C:"# Created:" /C:"#      by:" ..\spinetoolbox\ui\tool_configuration_assistant.py.o > ..\spinetoolbox\ui\tool_configuration_assistant.py
del ..\spinetoolbox\ui\tool_configuration_assistant.py.o

ECHO building tool_template_form.py
CALL pyside2-uic ../spinetoolbox/ui/tool_template_form.ui -o ../spinetoolbox/ui/tool_template_form.py.o
findstr /V /C:"# Created:" /C:"#      by:" ..\spinetoolbox\ui\tool_template_form.py.o > ..\spinetoolbox\ui\tool_template_form.py
del ..\spinetoolbox\ui\tool_template_form.py.o

ECHO building tree_view_form.py
CALL pyside2-uic ../spinetoolbox/ui/tree_view_form.ui -o ../spinetoolbox/ui/tree_view_form.py.o
findstr /V /C:"# Created:" /C:"#      by:" ..\spinetoolbox\ui\tree_view_form.py.o > ..\spinetoolbox\ui\tree_view_form.py
del ..\spinetoolbox\ui\tree_view_form.py.o

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
CALL append_license_xml ..\spinetoolbox\ui\add_tool.ui
CALL append_license_xml ..\spinetoolbox\ui\add_view.ui
CALL append_license_xml ..\spinetoolbox\ui\duration_editor.ui
CALL append_license_xml ..\spinetoolbox\ui\datetime_editor.ui
CALL append_license_xml ..\spinetoolbox\ui\graph_view_form.ui
CALL append_license_xml ..\spinetoolbox\ui\mainwindow.ui
CALL append_license_xml ..\spinetoolbox\ui\parameter_value_editor.ui
CALL append_license_xml ..\spinetoolbox\ui\plain_parameter_value_editor.ui
CALL append_license_xml ..\spinetoolbox\ui\project_form.ui
CALL append_license_xml ..\spinetoolbox\ui\settings.ui
CALL append_license_xml ..\spinetoolbox\ui\spine_datapackage_form.ui
CALL append_license_xml ..\spinetoolbox\ui\tabular_view_form.ui
CALL append_license_xml ..\spinetoolbox\ui\time_pattern_editor.ui
CALL append_license_xml ..\spinetoolbox\ui\time_series_fixed_resolution_editor.ui
CALL append_license_xml ..\spinetoolbox\ui\time_series_variable_resolution_editor.ui
CALL append_license_xml ..\spinetoolbox\ui\tool_configuration_assistant.ui
CALL append_license_xml ..\spinetoolbox\ui\tool_template_form.ui
CALL append_license_xml ..\spinetoolbox\ui\tree_view_form.ui
ECHO.
ECHO --- APPENDING LICENSE TO AUTOGENERATED .PY FILES ---
CALL append_license_py ..\spinetoolbox\ui\about.py
CALL append_license_py ..\spinetoolbox\ui\add_data_connection.py
CALL append_license_py ..\spinetoolbox\ui\add_data_store.py
CALL append_license_py ..\spinetoolbox\ui\add_tool.py
CALL append_license_py ..\spinetoolbox\ui\add_view.py
CALL append_license_py ..\spinetoolbox\ui\duration_editor.py
CALL append_license_py ..\spinetoolbox\ui\datetime_editor.py
CALL append_license_py ..\spinetoolbox\ui\graph_view_form.py
CALL append_license_py ..\spinetoolbox\ui\mainwindow.py
CALL append_license_py ..\spinetoolbox\ui\parameter_value_editor.py
CALL append_license_py ..\spinetoolbox\ui\plain_parameter_value_editor.py
CALL append_license_py ..\spinetoolbox\ui\project_form.py
CALL append_license_py ..\spinetoolbox\ui\settings.py
CALL append_license_py ..\spinetoolbox\ui\spine_datapackage_form.py
CALL append_license_py ..\spinetoolbox\ui\tabular_view_form.py
CALL append_license_py ..\spinetoolbox\ui\time_pattern_editor.py
CALL append_license_py ..\spinetoolbox\ui\time_series_fixed_resolution_editor.py
CALL append_license_py ..\spinetoolbox\ui\time_series_variable_resolution_editor.py
CALL append_license_py ..\spinetoolbox\ui\tool_configuration_assistant.py
CALL append_license_py ..\spinetoolbox\ui\tool_template_form.py
CALL append_license_py ..\spinetoolbox\ui\tree_view_form.py
CALL append_license_py ..\spinetoolbox\resources_icons_rc.py
CALL append_license_py ..\spinetoolbox\resources_logos_rc.py
