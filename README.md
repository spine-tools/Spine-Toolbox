# Spine Toolbox

An application to define, manage, and execute various energy system
simulation models.

## Requirements

- Python 3.5+
- PySide2 for Qt 5.6+
- datapackage 1.2.3+
- pyodbc 4.0.23+

### Installing requirements

datapackage and pyodbc packages are available on pip. Run

    pip install datapackage
    pip install pyodbc

to install. NOTE: these packages are automatically installed
if you use Anaconda or Miniconda (see below).

There are three options for installing PySide2.

- Installing for Anaconda & Miniconda Python (3.5+)
- Installing on a ‘clean’ Python (3.5+)
- Installing PySide2 by building sources (Python 2 & 3)

Each option is presented below.

#### OPTION 1: Installing for Anaconda & Miniconda Python (3.5+)

PySide2 for Qt 5.6.2 and pyodbc are available on the conda-forge
channel. Datapackage 1.2.3 is available on the manulero channel.
You can install all requirements by running

    conda install -c conda-forge -c manulero --file requirements.txt

in the Spine Toolbox root folder.

Alternatively, create a separate environment for Spine Toolbox with

	conda create --name spinetoolbox -c conda-forge -c manulero "python>=3.5" --file requirements.txt

The PySide2 GUI development tools (`designer`, `pyside2-uic`, and `pyside2-rcc`)
are included for both Windows and Linux in the PySide2 installation.

#### OPTION 2: Installing on a ‘clean’ Python (3.5+)

NOTE: This option is complicated because there still is no official PySide2 wheel 
available. This is likely to be simpler when the first official release 
version of PySide2 is released.

Download wheel for PySide2 from [http://hansch.info/PySide2/](http://hansch.info/PySide2/)

The following wheels are available:
PySide2 for Qt 5.6.2 (Python 3.5 and Python 3.6)
PySide2 for Qt 5.9.0 (Python 3.6)

Install with e.g.

    pip install PySide2-5.9-cp36-cp36m-win_amd64.whl

Make text file `qt.conf` into the directory where your `python.exe`
resides with the following content:

    [Paths]
    Prefix = /Python36/Lib/site-packages/PySide2
    Binaries = /Python36/Lib/site-packages/PySide2

If your PySide2 folder is in another path, modify Prefix and Binaries lines accordingly.
NOTE: There's no need for the drive letter on Windows. Use ‘/’ character to separate
directories also on Windows.

Install datapackage and pyodbc by running

    pip install datapackage
    pip install pyodbc

Spine Toolbox is now ready to run and you can also develop the
core application components. If you want to run the application,
skip next section and see "Running Spine Toolbox". If you want to develop
the Graphical User Interface (views, buttons, menus, etc.) you need
the PySide2 GUI development tools.

#### Installing PySide2 GUI Development Tools

These instructions have been tested with the Qt 5.9.0 wheel
PySide2-5.9-cp36-cp36m-win_amd64.whl installed on Windows.

Developing Spine Toolbox GUI requires

- `designer.exe`
- `pyside2-uic.exe`
- `pyside2-rcc.exe`

To make `designer.exe` work, copy `qt.conf` file into the folder where
it is located. It should be in the folder where PySide2 was installed
(e.g. C:\Python36\Lib\site-packages\PySide2)

`designer.exe` should now work.

`pyside2-uic.exe` is in your Python scripts folder
(e.g. C:\Python36\Scripts). To make it work, clone `pyside-setup`
project from https://code.qt.io/pyside/pyside-setup.git.

Checkout branch `dev`.

Go to folder \pyside-setup\sources\pyside2-tools\pyside2uic

Copy folders:

    \Compiler
    \port_v2
    \port_v3
    \widget-plugins

into your local pyside2uic folder
(e.g. C:\Python36\Lib\site-packages\pyside2uic)

At least \Compiler and \port_v3 folders are required.

`pyside2-rcc.exe` should be in the same folder as `designer.exe`.

Add your Python scripts path (e.g. C:\Python36\Scripts) and PySide2
(e.g. C:\Python36\Lib\site-packages\PySide2) path into your system PATH
variable.

#### OPTION #3: Installing PySide2 by building sources (Python 2 & 3)

You can install PySide2 by building the source package yourself. Instructions
on how to do this can be found on the getting started page of the official
PySide2 wiki
[https://wiki.qt.io/PySide2_GettingStarted](https://wiki.qt.io/PySide2_GettingStarted)

Follow the instructions on the page according to your OS.

## Running Spine Toolbox

To start the application run

    python spinetoolbox.py

from the command prompt in the `spinetoolbox` directory.

If you have modified the user interface files (.ui), with Qt Designer
(`designer.exe`) you need to build the UI for the changes to take effect.
On windows, run `build_ui.bat` to generate the code for Spine Toolbox
user interface. This requires the PySide2 GUI development tools described
previously.

On Linux, just use `bash build_ui.sh` instead of `build_ui.bat`, and `designer`
instead of `designer.exe`.
