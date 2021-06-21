# Spine Toolbox

[![Python](https://img.shields.io/badge/python-3.7%20|%203.8-blue.svg)](https://www.python.org/downloads/release/python-379/)
[![Documentation Status](https://readthedocs.org/projects/spine-toolbox/badge/?version=latest)](https://spine-toolbox.readthedocs.io/en/latest/?badge=latest)
[![Unit tests](https://github.com/Spine-project/Spine-Toolbox/workflows/Unit%20tests/badge.svg)](https://github.com/Spine-project/Spine-Toolbox/actions?query=workflow%3A"Unit+tests")
[![codecov](https://codecov.io/gh/Spine-project/Spine-Toolbox/branch/master/graph/badge.svg)](https://codecov.io/gh/Spine-project/Spine-Toolbox)
[![PyPI version](https://badge.fury.io/py/spinetoolbox.svg)](https://badge.fury.io/py/spinetoolbox)

An application to define, manage, and execute various energy system simulation models.

## Programming language

- Python 3.7
- Python 3.8

Please note that Python 3.9 is not supported yet. 

## License

Spine Toolbox is released under the GNU Lesser General Public License (LGPL) license. All accompanying
documentation, original graphics and other material are released under the 
[Creative Commons BY-SA 4.0 license](https://creativecommons.org/licenses/by-sa/4.0/).
Licenses of all packages used by Spine Toolbox are listed in the Spine Toolbox User 
Guide.

## Installation

Three options for installing Spine toolbox exist: as an application within
an existing Python installation, using stand-alone installation package and using 
the source files directly (for developers).

### With standard Python installation

Spine Toolbox is available on [The Python Package Index (PyPI)](https://pypi.org/project/spinetoolbox/).
This option is the recommended way to get the most recent release version but a
working Python installation is also required. 

---
**NOTE:** If you already have Spine toolbox installed globally using pip, please first 
uninstall using `pip uninstall spinetoolbox`.

---

1. Install Python 3.8. On Windows systems, the easiest way is through **Microsoft Store** 
or [Python.org](https://www.python.org/downloads/windows/). On OS X, get 
[the latest release at Python.org](https://www.python.org/downloads/mac-osx/). 
Most Linux distributions have Python preinstalled, but please check which version 
you have and update if necessary.

2. Make sure you have the latest version of pip installed:

        python3 -m pip install --upgrade pip

3. Install [pipx](https://pypa.github.io/pipx/). Open a terminal and type

        python3 -m pip install pipx
        python3 -m pipx ensurepath
        
4. Install the latest Spine Toolbox release using

        pipx install spinetoolbox

You can now start Spine Toolbox by calling `spinetoolbox` on the command line.
To update the installation, run

    pipx upgrade spinetoolbox

If you need a more recent version, you can install the latest development version
using

    pipx install git+https://github.com/Spine-project/Spine-Toolbox.git#egg=spinetoolbox

Please note that the stability of the latest version is not quaranteed.

### Stand-alone installer packages

We offer stand-alone binary installers for the Windows platform (64-bit). 
This option is suitable for users who cannot install Python or don’t care so much 
about updates. Download the latest version from [here](https://github.com/Spine-project/Spine-Toolbox/releases),
install and run `spinetoolbox.exe`. 


### Getting the source

This option is for the developers who wish to debug or edit the Spine Toolbox
source code. First, follow the above instructions on installing Python and upgrading pip.

1. Clone or download the latest source code of Spine Toolbox from its 
   [GitHub repository](https://github.com/Spine-project/Spine-Toolbox).
   
2. Browse to the folder and create a virtual environment using

    python3 -m venv .venv

3. Activate the environment using `.venv\Scripts\activate.bat` (Windows cmd.exe) 
   or `source .venv/bin/activate` (bash, zsh). 

4. Install Spine Toolbox using pip. Note that the terminal prompt should indicate 
   the activated environment.

        pip install -r requirements.txt

5. (Optional) Install additional development packages with

        pip install -r dev-requirements.txt

You can now run Spine Toolbox by calling `spinetoolbox` when the environment 
is activated. To update, just pull or copy the latest changes from the repository
and run 

    pip install --upgrade -r requirements.txt [-r dev-requirements.txt]


### About requirements

Python 3.7 or Python 3.8 is required.

See file `setup.py` and `requirements.txt` for packages required to run Spine Toolbox.
(Additional packages needed for development are listed in `dev-requirements.txt`.)

The requirements include three packages ([`spinedb_api`](https://github.com/Spine-project/Spine-Database-API),
[`spine_engine`](https://github.com/Spine-project/spine-engine), and [`spine_items`](https://github.com/Spine-project/spine-items)),
developed by the Spine project consortium. Since these packages are developed very actively at the moment, 
they may get upgraded quite regularly whenever you run `python -m pip install --upgrade -r requirements.txt`.


### Building the User Guide

You can find the latest documentation on [readthedocs](https://spine-toolbox.readthedocs.io/en/latest/index.html).
If you want to build the documentation yourself,
source files for the User Guide can be found in `docs/source` directory. In order to 
build the HTML docs, you need to install the *optional requirements* (see section 
'Installing requirements' above). This installs Sphinx (among other things), which 
is required in building the documentation. When Sphinx is installed, you can build the 
HTML pages from the user guide source files by using the `bin/build_doc.bat` script on 
Windows or the `bin/build_doc.sh` script on Linux and Mac. After running the script, the 
index page can be found in `docs/build/html/index.html`. The User Guide can also 
be opened from Spine Toolbox menu Help->User Guide (F2).

### Troubleshooting

#### Installation fails

Please make sure you are using Python 3.7 or Python 3.8 to install the requirements.

#### Installation fails on Linux
If Python runs into errors while installing on Linux systems, running the 
following commands in a terminal may help:

```shell
sudo apt install libpq-dev
sudo apt-get install unixodbc-dev
```

#### Problems in starting the application

If there are problems in starting Spine Toolbox, the chances are that the required 
packages were not installed successfully. In case this happens, the first thing you 
should check is that you don't have `Qt`, `PyQt4`, `PyQt5`, `PySide`, and `PySide2` 
packages installed in the same environment. These do not play nice together and may 
introduce conflicts. In addition, make sure that you do not have multiple versions 
of these `Qt` related packages installed in the same environment. The easiest way 
to solve this problem is to create a blank (e.g. virtual environment) Python 
environment just for `PySide2` applications and installing the requirements again.

**Warning: Using the *conda-forge* channel for installing the requirements is not 
recommended.**

The required `qtconsole` package from the ***conda-forge*** channel also
installs `qt` and `PyQt` packages. Since this is a `PySide2` application, those are 
not needed and there is a chance of conflicts between the packages.

**Note**: Supported PySide2 version is **5.14**. Spine Toolbox does not support PySide2 
version 5.15 (yet).

#### ImportError: DLL load failed while importing win32api

If you installed Spine Toolbox *without Conda* on **Python 3.8 on Windows**, 
you may see this error when trying to execute a project item. The cause of this error 
is the package `pywin32` version 225. To fix this error, upgrade the package to version 
300 using the following command

```shell
pip install --upgrade "pywin32==300"
```

After the process has finished, restart the application. **Note: pywin32 v301 does not work**.

## Contribution Guide

All are welcome to contribute!

See detailed instructions for contribution in [Spine Toolbox User Guide](https://spine-toolbox.readthedocs.io/en/latest/contribution_guide.html).

Below are the bare minimum things you need to know.

### Setting up development environment

1. Install the developer requirements:

        pip install -r dev-requirements.txt

2. Optionally, run `pre-commit install` in project's root directory. This sets up some git hooks.

### Coding style

- [Black](https://github.com/python/black) is used for Python code formatting.
  The project's GitHub page includes instructions on how to integrate Black in IDEs.
- Google style docstrings

### Linting

It is advisable to run [`pylint`](https://pylint.readthedocs.io/en/latest/) regularly on files that have been changed.
The project root includes a configuration file for `pylint`.
`pylint`'s user guide includes instructions on how to [integrate the tool in IDEs](https://pylint.readthedocs.io/en/latest/user_guide/ide-integration.html#pylint-in-pycharm).

### Unit tests

Unit tests are located in the `tests` directory.
You can run the entire test suite from project root by

```shell
python -m unittest
```

### Reporting bugs
If you think you have found a bug, please check the following before creating a new 
issue:
1. **Make sure you’re on the latest version.** 
2. **Try older versions.**
3. **Try upgrading/downgrading the dependencies**
4. **Search the project’s bug/issue tracker to make sure it’s not a known issue.**

What to put in your bug report:
1. **Python version**. What version of the Python interpreter are you using? 32-bit 
    or 64-bit?
2. **OS**. What operating system are you on?
3. **Application Version**. Which version or versions of the software are you using? 
    If you have forked the project from Git, which branch and which commit? Otherwise, 
    supply the application version number (Help->About menu).
4. **How to recreate**. How can the developers recreate the bug? A screenshot 
    demonstrating the bug is usually the most helpful thing you can report. Relevant 
    output from the Event Log and debug messages from the console of your run, should 
    also be included.

### Feature requests
The developers of Spine Toolbox are happy to hear new ideas for features or improvements 
to existing functionality. The format for requesting new features is free. Just fill 
out the required fields on the issue tracker and give a description of the new feature. 
A picture accompanying the description is a good way to get your idea into development
faster. But before you make a new issue, please check that there isn't a related idea 
already open in the issue tracker.

&nbsp;
<hr>
<center>
<table width=500px frame="none">
<tr>
<td valign="middle" width=100px>
<img src=https://europa.eu/european-union/sites/europaeu/files/docs/body/flag_yellow_low.jpg alt="EU emblem" width=100%></td>
<td valign="middle">This project has received funding from the European Union’s Horizon 2020 research and innovation programme under grant agreement No 774629.</td>
</table>
</center>
