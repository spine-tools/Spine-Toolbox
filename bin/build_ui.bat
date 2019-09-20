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

REM Change to project root dir
PUSHD %~dp0\..

SET spinetoolbox_path=spinetoolbox
SET ui_path=spinetoolbox\ui
SET plugins_path=plugins_path


FOR %%f IN (%ui_path%\*.ui) DO (
    SET ui_file=%%f
    SET py_file=%ui_path%\%%~nf.py
    ECHO building !py_file!
    REM Replace backslashes with forward slashes for pyside2-uic
    pyside2-uic -o !py_file!.o !ui_file:\=/!
    findstr /V /C:"# Created:" /C:"#      by:" !py_file!.o > !py_file!
    DEL !py_file!.o > NUL
    CALL bin\append_license_xml.bat !ui_file!
    CALL bin\append_license_py.bat !py_file!
)
FOR %%f IN (%ui_path%\*.qrc) DO (
    SET qrc_file=%%f
    SET py_file=%spinetoolbox_path%\%%~nf_rc.py
    ECHO building !py_file!
    REM Replace backslashes with forward slashes for pyside2-rcc
    pyside2-rcc -o !py_file! !qrc_file:\=/!
)

ECHO.
ECHO --- Building Spine Toolbox Plugins GUI ---

FOR %%f IN (%plugins_path%\*.ui) DO (
    SET ui_file=%%f
    SET py_file=%plugins_path%\%%~nf.py
    ECHO building !py_file!
    REM Replace backslashes with forward slashes for pyside2-uic
    pyside2-uic -o !py_file!.o !ui_file:\=/!
    findstr /V /C:"# Created:" /C:"#      by:" !py_file!.o > !py_file!
    DEL !py_file!.o > NUL
    CALL bin\append_license_xml.bat !ui_file!
    CALL bin\append_license_py.bat !py_file!
)

ECHO --- Build completed ---
POPD
