REM This script is part of build_ui.bat script. See build_ui.bat for license.

@echo off

if "%1"=="" (goto noargs) else (goto checkforlicense)

:checkforlicense
setlocal
set myvar=0
echo Searching for license from file %1
REM If the string is found tmpFile contains the name of the file
FINDSTR /M /C:"Copyright (C) 2016 - 2017 VTT Technical Research Centre of Finland" %1 > tmpFile
set /p myvar=<tmpFile
del tmpFile
if "%myvar%"=="%1" (goto foundit) else (goto notfound)

:foundit
echo License found
goto exhit

:notfound
goto appendlicense

:appendlicense
echo Appending license
REM Remove first line from ui file (Start tag)
TYPE %1 | FIND /V /I "<?xml version=""1.0"" encoding=""utf-8""?>" > tmp.ui

(
echo ^<?xml version="1.0" encoding="utf-8"?^>
echo ^<!--
echo #############################################################################
echo # Copyright ^(C^) 2016 - 2017 VTT Technical Research Centre of Finland
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
echo --^>
) > license.txt

type tmp.ui >> license.txt
del %1
del tmp.ui
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
