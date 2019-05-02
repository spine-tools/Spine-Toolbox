@ECHO OFF
@TITLE Upgrading spinedb_api

ECHO This is a script for upgrading spinedb_api.
ECHO Copyright (C) ^<2017-2018^>  ^<Spine project consortium^>
ECHO This program comes with ABSOLUTELY NO WARRANTY; This is free software, and you are welcome to redistribute it
ECHO under certain conditions; See files COPYING and COPYING.LESSER for details.
ECHO.

ECHO USAGE:
ECHO 'upgrade_spinedb_api.bat'            upgrade from master branch
ECHO 'upgrade_spinedb_api.bat dev'        upgrade from dev branch
ECHO.

if "%1"=="" goto :update_master
if "%1"=="dev" goto :update_dev
goto :unknown_arg

:update_master
ECHO.
ECHO Upgrading from 'master' branch
ECHO.
call pip install --upgrade git+https://github.com/Spine-project/Spine-Database-API.git@master
goto :exhit

:update_dev
ECHO.
ECHO Upgrading from 'dev' branch
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
