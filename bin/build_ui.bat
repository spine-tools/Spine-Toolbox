@ECHO OFF
@TITLE Build Spine Toolbox GUI for PySide2

ECHO.
ECHO ^<Script for Building Spine Toolbox GUI^>
ECHO Copyright (C) ^<2016-2017^>  ^<VTT Technical Research Centre of Finland^>
ECHO This program comes with ABSOLUTELY NO WARRANTY; for details see 'about'.
ECHO box in the application. This is free software, and you are welcome to 
ECHO redistribute it under certain conditions; See files COPYING and 
ECHO COPYING.LESSER for details.
ECHO.

PAUSE

ECHO --- pyside2-uic version ---
CALL pyside2-uic --version
ECHO.
ECHO --- Building Spine Toolbox GUI ---

ECHO mainwindow.py
CALL pyside2-uic ../SpineToolbox/ui/mainwindow.ui -o ../SpineToolbox/ui/mainwindow.py.o
findstr /V /C:"# Created:" /C:"#      by:" ..\SpineToolbox\ui\mainwindow.py.o > ..\SpineToolbox\ui\mainwindow.py
del ..\SpineToolbox\ui\mainwindow.py.o

ECHO data_store_form.py
CALL pyside2-uic ../SpineToolbox/ui/data_store_form.ui -o ../SpineToolbox/ui/data_store_form.py.o
findstr /V /C:"# Created:" /C:"#      by:" ..\SpineToolbox\ui\data_store_form.py.o > ..\SpineToolbox\ui\data_store_form.py
del ..\SpineToolbox\ui\data_store_form.py.o
