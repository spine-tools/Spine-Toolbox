# Spine Toolbox

An application to define, manage, and execute various energy system simulation models.

## License

Spine Toolbox is released under the GNU Lesser General Public License (LGPL) license. All accompanying
documentation, original graphics, and manual are released under the Creative Commons BY-SA 4.0 license.
Licenses of all packages used by Spine Toolbox are in the Spine Toolbox User Guide.

## Running Spine Toolbox

To start the application run

    python spinetoolbox.py

from the command prompt in the `spinetoolbox` directory.

## Building the User Guide
Source files for the User Guide can be found in ``docs/source`` directory. Build HTML pages from the source files 
by using ``bin/build_doc.bat`` (Windows) or ``bin/build_doc.sh`` (Linux) scripts. After running the script, the 
index page can be found in ``docs/build/html/index.html``. The User Guide can also be opened from Spine Toolbox 
menu Help->User Guide (F2).

## Requirements

Spine Toolbox requires Python 3.5 or higher.

See requirements.txt for must have packages and optional-requirements.txt for optional ones. Users can 
choose the SQL dialect API (pymysql, pyodbc psycopg2, and cx_Oracle) they want to use. These can 
be installed in Spine Toolbox when needed. Sphinx, recommonmark, and cx_Freeze packages 
are needed for building the user guide and for deploying the application.

### Installing requirements on Python 3.5+

The first official release of PySide2 module was released in June, 2018. To learn more about 
the release, check out the [blog post](http://blog.qt.io/blog/2018/06/13/qt-python-5-11-released/)
on the official Qt for Python pages.

To install PySide2 with pip, run

    pip install pyside2

It is also possible to build PySide2 from sources. Instructions for doing so can be found in
[here](https://wiki.qt.io/Qt_for_Python/GettingStarted). All other requirements,
except cx_Freeze (v6.0b1) and spinedatabase_api, can be installed from PyPi with pip.
For example, to install the datapackage module, run

    pip install datapackage

To install cx_Freeze, download the correct wheel for your OS, for example,
`cx_Freeze-6.0b1-cp36-cp36m-win_amd64.whl` from
[here](https://pypi.org/project/cx_Freeze/6.0b1/#files) and install by running

    pip install cx_Freeze-6.0b1-cp36-cp36m-win_amd64.whl

To install spinedatabase_api run

    pip install git+https://gitlab.vtt.fi/spine/data.git@database_api

### Installing requirements for Anaconda & Miniconda Python (3.5+)

..
**TODO: This should be updated**

PySide2 for Qt 5.6.2 and pyodbc are available on the conda-forge
channel. Datapackage 1.2.3 is available on the manulero channel.
You can install all requirements by running

    conda install -c conda-forge -c manulero --file requirements.txt

in the Spine Toolbox root folder.

Alternatively, create a separate environment for Spine Toolbox with

	conda create --name spinetoolbox -c conda-forge -c manulero "python>=3.5" --file requirements.txt

## Contribution Guide

All are welcome to contribute!

See detailed instructions for contribution in Spine Toolbox User Guide.

Below are the bare minimum things you need to know.

### Coding Style
- Follow the style you see used in the repository
- Max line length 120 characters
- Google style docstrings
- [PEP-8](https://www.python.org/dev/peps/pep-0008/)

### Reporting bugs
If you think you have found a bug, please check the following before creating a new issue:
1. **Make sure you’re on the latest version.** 
2. **Try older versions.**
3. **Try upgrading/downgrading the dependencies**
4. **Search the project’s bug/issue tracker to make sure it’s not a known issue.**

What to put in your bug report:
1. **Python version**. What version of the Python interpreter are you using? 32-bit or 64-bit?
2. **OS**. What operating system are you on?
3. **Application Version**. Which version or versions of the software are you using? If you have forked the project from Git,
   which branch and which commit? Otherwise, supply the application version number (Help->About menu).
4. **How to recreate**. How can the developers recreate the bug? A screenshot demonstrating the bug is usually the most 
   helpful thing you can report. Relevant output from the Event Log and debug messages from the console 
   of your run, should also be included.

### Feature Requests
The developers of Spine Toolbox are happy to hear new ideas for features or improvements to existing functionality.
The format for requesting new features is free. Just fill out the required fields on the issue tracker and give a
description of the new feature. A picture accompanying the description is a good way to get your idea into development
faster. But before you make a new issue, check that there isn't a related idea already open in the issue tracker.
