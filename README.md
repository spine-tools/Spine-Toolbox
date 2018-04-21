# Spine Toolbox

An application to define, manage, and execute various energy system
simulation models.

## Requirements

- Python 3.5+
- PySide2 for Qt 5.6+
- datapackage 1.2.3+
- pyodbc 4.0.23+

### Installing requirements

There are three options for installing PySide2, datapackage, and pyodbc.

- Installing for Anaconda & Miniconda (3.5+)
- Installing on a ‘clean’ Python (3.5+)
- Installing PySide2 by building sources (Python 2 & 3)

Each option is presented below.

#### OPTION 1: Installing PySide2, datapackage, and pyodbc for Anaconda & Miniconda Python (3.5+)

PySide2 for Qt 5.6.2 and pyodbc are available on the conda-forge channel. Datapackage 1.2.3 is available on the manulero channel. You can install all requirements by running

    conda install -c conda-forge -c manulero --file requirements.txt

in the Spine Toolbox root folder.

Alternatively, create a separate environment for the Toolbox with

	conda create --name spinetoolbox -c conda-forge -c manulero --file requirements.txt

Last, install datapackage and pyodbc by running

    pip install datapackage
    pip install pyodbc


#### OPTION 2: Installing PySide2, datapackage, and pyodbc on a ‘clean’ Python (3.5+)

Download wheel for PySide2 from [http://hansch.info/PySide2/](http://hansch.info/PySide2/)

The following wheels are available:
PySide2 for Qt 5.6.2 (Python 3.5 and Python 3.6)
PySide2 for Qt 5.9.0 (Python 3.6)

Install with e.g.

    pip install PySide2-5.9-cp36-cp36m-win_amd64.whl

Make text file `qt.conf` into the folder where your `python.exe`
resides with the following contents:

    [Paths]
    Prefix = /Python36/Lib/site-packages/PySide2
    Binaries = /Python36/Lib/site-packages/PySide2

If your PySide2 folder is in another path, modify Prefix and Binaries lines accordingly.

Install datapackage and pyodbc by running

    pip install datapackage
    pip install pyodbc

Spine Toolbox should now work and you are ready to develop the core
application components. If you want to develop the Graphical User
Interface (views, buttons, menus, etc.) you need the PySide2 GUI
development tools.

#### OPTION 3: Installing PySide2 GUI Development Tools

##### Windows

These instructions have been tested when the Qt 5.9.0 wheel
PySide2-5.9-cp36-cp36m-win_amd64.whl has been installed.

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

Add your Python scripts (e.g. C:\Python36\Scripts) and PySide2
(e.g. C:\Python36\Lib\site-packages\PySide2) folders into your PATH
variable.

##### Linux

[Miniconda](https://conda.io/miniconda.html) provides the three required utilities out of the box. After bash installation they can be called from the command line by running `designer`, `pyside2-uic`, and `pyside2-rcc`.

#### Installing PySide2 by building sources (Python 2 & 3)

You can install PySide2 by building the source package yourself. Instructions
on how to do this can be found on the getting started page of the official
PySide2 wiki
[https://wiki.qt.io/PySide2_GettingStarted](https://wiki.qt.io/PySide2_GettingStarted)

Follow the instructions on the page according to your OS.

## Preparing and starting Spine Toolbox

On windows, run `build_ui.bat` from your Python/PySide2 enabled command window to generate
the code for the Spine Toolbox user interface.
After modifying the user interface (*.ui) files with `designer.exe`, re-run
`build_ui.bat` to build the Spine Toolbox interface anew.

On Linux, just use `bash build_ui.sh` instead of `build_ui.bat`, and `designer` instead of `designer.exe`.

From the command prompt, run `python spinetoolbox.py` in the `spinetoolbox` folder.
