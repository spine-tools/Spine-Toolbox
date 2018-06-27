# Spine Toolbox

An application to define, manage, and execute various energy system
simulation models.

## Requirements

All version numbers next to the package name are minimum version numbers.

- Python 3.5
- PySide2 for Qt 5.6
- datapackage 1.2.3
- pyodbc 4.0.23
- mysqlclient 1.3.12
- qtconsole 4.3.1
- sqlalchemy 1.2.6

For building the documentation you need the following packages:

- Sphinx 1.7.5
- sphinx-rtd-theme 0.4.0
- recommonmark 0.4.0

In addition, for deploying Spine Toolbox application you need:

cx-Freeze 6.0b1

### Installing requirements on a 'clean' Python (3.5+)

The first official release of PySide2 module is now available. To learn more about the release, 
check out the [blog post](http://blog.qt.io/blog/2018/06/13/qt-python-5-11-released/) 
on the official Qt for Python pages. 

To install PySide2 with pip, run

    pip install --index-url=https://download.qt.io/official_releases/QtForPython/ pyside2

It is also possible to build PySide2 from sources. Instructions for doing that can be found in 
[here](https://wiki.qt.io/Qt_for_Python/GettingStarted). All other requirements, 
except cx_Freeze (v6.0b1), can be installed from PyPi with pip. For example, to 
install the datapackage module, run 

    pip install datapackage

To install cx_Freeze, download the correct wheel for your OS, for example, 
`cx_Freeze-6.0b1-cp36-cp36m-win_amd64.whl` from 
[here](https://pypi.org/project/cx_Freeze/6.0b1/#files) and install by running

    pip install cx_Freeze-6.0b1-cp36-cp36m-win_amd64.whl 

### Installing requirements for Anaconda & Miniconda Python (3.5+)

PySide2 for Qt 5.6.2 and pyodbc are available on the conda-forge
channel. Datapackage 1.2.3 is available on the manulero channel.
You can install all requirements by running

    conda install -c conda-forge -c manulero --file requirements.txt

in the Spine Toolbox root folder.

Alternatively, create a separate environment for Spine Toolbox with

	conda create --name spinetoolbox -c conda-forge -c manulero "python>=3.5" --file requirements.txt

## Running Spine Toolbox

To start the application run

    python spinetoolbox.py

from the command prompt in the `spinetoolbox` directory.

If you have modified the user interface files (.ui), with Qt Designer
(`designer.exe` on Windows, `designer` on Linux) you need to build 
the UI for the changes to take effect. On windows, run `build_ui.bat` 
to generate Python code from the .ui files for Spine Toolbox user 
interface. On Linux, use `bash build_ui.sh` instead of `build_ui.bat`.
