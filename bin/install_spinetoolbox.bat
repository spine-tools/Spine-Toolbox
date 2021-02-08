@echo OFF

echo. 
echo [92m     ____     _            ______          ____            ^| [0m
echo [92m    / __/__  (_)__  ___   /_  __/__  ___  / / /  ___ __ __ ^| [0m
echo [92m   _\ \/ _ \/ / _ \/ -_)   / / / _ \/ _ \/ / _ \/ _ \\ \ / ^| Easy Installer [0m
echo [94m  /___/ .__/_/_//_/\__/   /_/  \___/\___/_/_.__/\___/_\_\  ^| Version 0.1.0 (2021-02-07) [0m
echo [94m     /_/                                                   ^| [0m
echo. 

setlocal EnableDelayedExpansion

:: Set default installation folder
set default_toolbox_folder=%UserProfile%\SpineToolbox
mkdir %default_toolbox_folder% >nul 2>&1

:: Prompt user to select a folder
:select_folder
set "dialog="powershell -sta Add-Type -AssemblyName System.windows.forms;^
$f = New-Object System.Windows.Forms.FolderBrowserDialog;^
$f.SelectedPath = '%default_toolbox_folder%';^
$f.Description = 'Please select a folder to install Spine Toolbox.';^
$f.ShowNewFolderButton = $true;^
$a = $f.ShowDialog();^
$b = $f.SelectedPath;^
Write-Host "$a-$b"""

for /f "tokens=1,2 delims=-" %%a in ('%dialog%') do (
	set button=%%a
	set toolbox_folder=%%b
)
if "!button!" neq "OK" goto end

:: If installation folder is not empty, prompt user to confirm that overwritting is ok
for /f "delims=" %%a in ('dir /a /b %toolbox_folder%') do set contents=%%a
if {%contents%} == {} (goto install) else (goto confirm_folder)

:confirm_folder
set "dialog="powershell -sta Add-Type -AssemblyName PresentationCore,PresentationFramework;^
$message_title = 'Confirm selection';^
$message_body = 'The folder `%toolbox_folder%` is not empty.' + \"`n`n\"^
+ 'Do you want to overwrite its contents?';^
$button_type = [System.Windows.MessageBoxButton]::YesNoCancel;^
$message_icon = [System.Windows.MessageBoxImage]::Warning;^
[System.Windows.MessageBox]::Show($message_body, $message_title, $button_type, $message_icon)""

for /f "delims=" %%I in ('%dialog%') do set button=%%I
if "!button!" == "Cancel" goto end
if "!button!" == "No" goto select_folder

:: Begin installation
:install
echo Installing into %toolbox_folder%...

:: Query architecture from registry and use it to pick the right Miniconda installer
reg Query "HKLM\Hardware\Description\System\CentralProcessor\0" | find /i "x86" >nul && set os=32bit || set os=64bit
if %os%==32bit set miniconda_exe=Miniconda3-latest-Windows-x86.exe
if %os%==64bit set miniconda_exe=Miniconda3-latest-Windows-x86_64.exe
set miniconda_url=https://repo.anaconda.com/miniconda/%miniconda_exe%
set miniconda_installer=%TEMP%\%miniconda_exe%
set miniconda_dir=%toolbox_folder%\Miniconda3
set julia_install_dir=%toolbox_folder%\julias
set julia_symlink_dir=%julia_install_dir%\bin
set julia=%julia_symlink_dir%\julia.cmd
set toolbox_pkg_folder=%toolbox_folder%\Spine-Toolbox
set toolbox_exe=%toolbox_folder%\spinetoolbox.bat
set toolbox_up=%toolbox_folder%\upgrade.bat

:: Download miniconda
echo Downloading Miniconda...
call bitsadmin /transfer download_miniconda /download /priority FOREGROUND %miniconda_url% %miniconda_installer% >nul 2>&1

:: Install miniconda
echo Installing Miniconda...
start /wait "" %miniconda_installer% /InstallationType=JustMe /RegisterPython=0 /S /D=%miniconda_dir%

:: Install SpineToolbox
echo Installing Spine Toolbox package...
call %miniconda_dir%\Scripts\activate.bat %miniconda_dir%
call conda create -n spinetoolbox python=3.7 -y
call conda activate spinetoolbox
call conda install -c anaconda git -y
call rmdir %toolbox_pkg_folder% /S /Q
call git clone https://github.com/Spine-project/Spine-Toolbox.git %toolbox_pkg_folder%
cd %toolbox_pkg_folder%
call python -m pip install -r requirements.txt

:: Install Julia using the `jill` python package
echo Installing Julia...
call python -m pip install jill
call jill install --install_dir=%julia_install_dir% --symlink_dir=%julia_symlink_dir% --confirm
:: Install SpineOpt
echo Installing SpineOpt package...
call %julia% --project="%toolbox_pkg_folder%" -e^
 "using Pkg; pkg\"registry add https://github.com/Spine-project/SpineJuliaRegistry\"; pkg\"add SpineOpt\""
call python bin\configure_julia.py %julia% %toolbox_pkg_folder%

:: Create executables
:: - spinetoolbox
echo call %miniconda_dir%\Scripts\activate.bat %miniconda_dir%> %toolbox_exe%
echo call conda activate spinetoolbox>> %toolbox_exe%
echo call python -m spinetoolbox>> %toolbox_exe%
:: - upgrade
echo call %miniconda_dir%\Scripts\activate.bat %miniconda_dir%> %toolbox_up%
echo call conda activate spinetoolbox>> %toolbox_up%
echo call cd %toolbox_pkg_folder%>> %toolbox_up%
echo call git pull>> %toolbox_up%
echo call python -m pip install -U -r requirements.txt>> %toolbox_up%
echo call %julia% --project="." -e "using Pkg; pkg\"up SpineOpt\"">> %toolbox_up%

:: Tell the user that everything went well. TODO: How do we know if something went wrong?
powershell -sta Add-Type -AssemblyName PresentationCore,PresentationFramework;^
$message_title = 'Spine Toolbox installation complete';^
$message_body = 'We will now take you to the installation folder.' + \"`n`n\"^
+ '- Run `spinetoolbox` to launch the application.' + \"`n`n\"^
+ '- Run `upgrade` to upgrade to the most recent version.';^
$button_type = [System.Windows.MessageBoxButton]::OK;^
$message_icon = [System.Windows.MessageBoxImage]::Information;^
[System.Windows.MessageBox]::Show($message_body, $message_title, $button_type, $message_icon) >nul 2>&1

:: Take them to the Spine Toolbox folder
explorer /select,%toolbox_exe%

:end
endlocal