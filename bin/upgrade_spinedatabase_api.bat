@ECHO OFF
@TITLE Upgrading spinedatabase_api

ECHO This is a script for upgrading spinedatabase_api.
ECHO Copyright (C) ^<2017-2018^>  ^<Spine project consortium^>
ECHO This program comes with ABSOLUTELY NO WARRANTY; This is free software, and you are welcome to redistribute it
ECHO under certain conditions; See files COPYING and COPYING.LESSER for details.
ECHO.

REM The weird looking character is the ESC character (escape symbol). L-ALT+0+2+7
ECHO [1mUSAGE:[0m
ECHO run [1mupgrade_spinedatabase_api.bat[0m command to upgrade from master branch
ECHO run [1mupgrade_spinedatabase_api.bat dev[0m command to upgrade from dev branch
ECHO.

if "%1"=="" goto :update_master
if "%1"=="dev" goto :update_dev
goto :unknown_arg

:update_master
ECHO.
ECHO Upgrading from [1mmaster[0m branch
ECHO.
call pip install --upgrade git+https://github.com/Spine-project/Spine-Database-API.git@master
goto :exhit

:update_dev
ECHO.
ECHO Upgrading from [1mdev[0m branch
ECHO.
call pip install --upgrade git+https://github.com/Spine-project/Spine-Database-API.git@dev
goto :exhit

:unknown_arg
ECHO.
ECHO Unknown argument '%1'. Please see USAGE.
ECHO.
goto :exhit

:exhit
exit /B 0
