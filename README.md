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

Run

    pip install -r requirements.txt

If everything goes well, you can now run Spine Toolbox.

To install optional requirements run

    pip install -r optional-requirements.txt

If there are problems in starting Spine Toolbox, the first thing you should check is that you 
don't have Qt, PyQt, and PySide2 packages installed in the same environment. These do not play 
nice together and create conflicts. Also, make sure that you do not have multiple PySide2 versions
installed in the same environment. So, please create a virtual environment and try installing 
the requirements again if you run into problems.

Package `spinedatabase_api` is being actively developed by the Spine project so you should keep 
the package up-to-date. To upgrade spinedatabase_api to the newest version, run

    pip install --upgrade git+https://github.com/Spine-project/Spine-Database-API.git#spinedatabase_api

### Installing requirements for Anaconda & Miniconda Python

The recommended way to install dependencies using Anaconda or Miniconda is:

1. Create a new environment by typing in Anaconda prompt

        conda create -n spinetoolbox python=3.7

2. Activate the new environment

        conda activate spinetoolbox

3. Then install requirements using pip

        pip install -r requirements.txt

in Spine Toolbox root folder.

**Note: Using the *conda-forge* channel for installing the requirements is not recommended.**

Installing the `qtconsole` package from *conda-forge* channel also
installs `qt` and `PyQt` packages. Since this is a PySide2 application, those are 
not needed and there is a chance of conflicts between the packages.

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
