@ECHO OFF
@TITLE Build Spine Toolbox GUI
SETLOCAL ENABLEDELAYEDEXPANSION

ECHO.
ECHO ^<Script for Building Spine Toolbox GUI^>
ECHO Copyright (C) ^<2017-2019^>  ^<Spine project consortium^>
ECHO This program comes with ABSOLUTELY NO WARRANTY; for details see 'about'.
ECHO box in the application. This is free software, and you are welcome to
ECHO redistribute it under certain conditions; See files COPYING and
ECHO COPYING.LESSER for details.
ECHO.

PAUSE

ECHO --- pyside2-uic version ---
pyside2-uic --version
ECHO --- pyside2-rcc version ---
pyside2-rcc -version
ECHO.
ECHO --- Building Spine Toolbox GUI ---

SET ui_path=..\spinetoolbox\ui
SET spinetoolbox_path=..\spinetoolbox

FOR /F %%f IN ('git diff --name-only -- %ui_path%') DO (
    SET filepath=%%f
    REM Process given file path with forward slashes replaced with backslashes
    CALL :process_filepath ..\!filepath:/=\!
)
ECHO --- Build completed ---
GOTO :EOF

:process_filepath
IF "%~x1"==".ui" (
    SET ui_file=%1
    SET py_file=%ui_path%\%~n1.py
    ECHO building !py_file!
    REM Replace backslashes with forward slashes for pyside2-uic
    pyside2-uic -o !py_file!.o !ui_file:\=/!
    findstr /V /C:"# Created:" /C:"#      by:" !py_file!.o > !py_file!
    DEL !py_file!.o > NUL
    CALL append_license_xml.bat !ui_file!
    CALL append_license_py.bat !py_file!
)

IF "%~x1"==".qrc" (
    SET qrc_file=%1
    SET py_file=%spinetoolbox_path%\%~n1_rc.py
    ECHO building !py_file!
    REM Replace backslashes with forward slashes for pyside2-rcc
    pyside2-rcc -o !py_file! !qrc_file:\=/!
)

