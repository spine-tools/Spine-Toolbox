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
SET dc_ui_path=spinetoolbox\project_items\data_connection\ui
SET di_ui_path=spinetoolbox\project_items\data_interface\ui
SET ds_ui_path=spinetoolbox\project_items\data_store\ui
SET tool_ui_path=spinetoolbox\project_items\tool\ui
SET view_ui_path=spinetoolbox\project_items\view\ui


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
    ECHO.
)
FOR %%f IN (%ui_path%\resources\*.qrc) DO (
    SET qrc_file=%%f
    SET py_file=%spinetoolbox_path%\%%~nf_rc.py
    ECHO building !py_file!
    REM Replace backslashes with forward slashes for pyside2-rcc
    pyside2-rcc -o !py_file! !qrc_file:\=/!
    ECHO.
)

ECHO.
ECHO --- Building Spine Toolbox Project Item Data Connection UI ---
FOR %%f IN (%dc_ui_path%\*.ui) DO (
    SET ui_file=%%f
    SET py_file=%dc_ui_path%\%%~nf.py
    ECHO building !py_file!
    REM Replace backslashes with forward slashes for pyside2-uic
    pyside2-uic -o !py_file!.o !ui_file:\=/!
    findstr /V /C:"# Created:" /C:"#      by:" !py_file!.o > !py_file!
    DEL !py_file!.o > NUL
    CALL bin\append_license_xml.bat !ui_file!
    CALL bin\append_license_py.bat !py_file!
)
ECHO.
ECHO --- Building Spine Toolbox Project Item Data Interface UI ---
FOR %%f IN (%di_ui_path%\*.ui) DO (
    SET ui_file=%%f
    SET py_file=%di_ui_path%\%%~nf.py
    ECHO building !py_file!
    REM Replace backslashes with forward slashes for pyside2-uic
    pyside2-uic -o !py_file!.o !ui_file:\=/!
    findstr /V /C:"# Created:" /C:"#      by:" !py_file!.o > !py_file!
    DEL !py_file!.o > NUL
    CALL bin\append_license_xml.bat !ui_file!
    CALL bin\append_license_py.bat !py_file!
)
ECHO.
ECHO --- Building Spine Toolbox Project Item Data Store UI ---
FOR %%f IN (%ds_ui_path%\*.ui) DO (
    SET ui_file=%%f
    SET py_file=%ds_ui_path%\%%~nf.py
    ECHO building !py_file!
    REM Replace backslashes with forward slashes for pyside2-uic
    pyside2-uic -o !py_file!.o !ui_file:\=/!
    findstr /V /C:"# Created:" /C:"#      by:" !py_file!.o > !py_file!
    DEL !py_file!.o > NUL
    CALL bin\append_license_xml.bat !ui_file!
    CALL bin\append_license_py.bat !py_file!
)
ECHO.
ECHO --- Building Spine Toolbox Project Item Tool UI ---
FOR %%f IN (%tool_ui_path%\*.ui) DO (
    SET ui_file=%%f
    SET py_file=%tool_ui_path%\%%~nf.py
    ECHO building !py_file!
    REM Replace backslashes with forward slashes for pyside2-uic
    pyside2-uic -o !py_file!.o !ui_file:\=/!
    findstr /V /C:"# Created:" /C:"#      by:" !py_file!.o > !py_file!
    DEL !py_file!.o > NUL
    CALL bin\append_license_xml.bat !ui_file!
    CALL bin\append_license_py.bat !py_file!
)
ECHO.
ECHO --- Building Spine Toolbox Project View UI ---
FOR %%f IN (%view_ui_path%\*.ui) DO (
    SET ui_file=%%f
    SET py_file=%view_ui_path%\%%~nf.py
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
