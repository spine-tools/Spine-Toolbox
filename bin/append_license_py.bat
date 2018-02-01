REM This script is part of build_ui.bat script. See build_ui.bat for license.

@echo off

if "%1"=="" (goto noargs) else (goto appendlicense)

:appendlicense
echo Appending license to file %1

(
echo #############################################################################
echo # Copyright ^(C^) 2017 - 2018 VTT Technical Research Centre of Finland
echo #
echo # This file is part of Spine Toolbox.
echo #
echo # Spine Toolbox is free software: you can redistribute it and/or modify
echo # it under the terms of the GNU Lesser General Public License as published by
echo # the Free Software Foundation, either version 3 of the License, or
echo # ^(at your option^) any later version.
echo #
echo # This program is distributed in the hope that it will be useful,
echo # but WITHOUT ANY WARRANTY^; without even the implied warranty of
echo # MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
echo # GNU Lesser General Public License for more details.
echo #
echo # You should have received a copy of the GNU Lesser General Public License
echo # along with this program.  If not, see ^<http://www.gnu.org/licenses/^>.
echo #############################################################################
echo.
) > license.txt

type %1 >> license.txt
del %1
REM stdout is redirected to NUL to suppress xcopy output
echo f | xcopy license.txt %1 1>NUL
del license.txt
goto exhit

:noargs
echo No filename given
exit /B 0

:exhit
endlocal
exit /B 0
