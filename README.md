# Spine Toolbox

[![Documentation Status](https://readthedocs.org/projects/spine-toolbox/badge/?version=latest)](https://spine-toolbox.readthedocs.io/en/latest/?badge=latest)
[![Build Status](https://travis-ci.com/Spine-project/Spine-Toolbox.svg?branch=master)](https://travis-ci.com/Spine-project/Spine-Toolbox)

An application to define, manage, and execute various energy system simulation models.

## Programming language

- Python 3.6
- Python 3.7

Please note that Python 3.8 is **not** supported yet.

## License

Spine Toolbox is released under the GNU Lesser General Public License (LGPL) license. All accompanying
documentation, original graphics and other material are released under the 
[Creative Commons BY-SA 4.0 license](https://creativecommons.org/licenses/by-sa/4.0/).
Licenses of all packages used by Spine Toolbox are listed in the Spine Toolbox User 
Guide.

## Installing Spine Toolbox

Installing requires you to [clone](https://help.github.com/articles/cloning-a-repository/) or 
download the latest version of the source code to your computer.

The development happens on the `dev` branch and all the latest features and bug fixes will be added there
first. The `master` branch contains the most stable version of the application. 

The **recommended** way to install and run Spine Toolbox is by using Anaconda or Miniconda environments.

Step-by-step instructions:

1. Install either [anaconda](https://www.anaconda.com/distribution/) or 
[miniconda](https://docs.conda.io/en/latest/miniconda.html)

2. Open Anaconda prompt
3. Install **git** into the base environment

        conda install -c anaconda git

4. Create a new environment by typing

        conda create -n spinetoolbox python=3.7

5. Activate the new environment

        conda activate spinetoolbox

6. Clone either the `master` or `dev` branch from Spine Toolbox 
repository on GitHub onto your computer. 
7. cd to Spine Toolbox root directory (the one with requirements.txt)
8. Install requirements using **pip**

        pip install -r requirements.txt

9. Run

        python -m spinetoolbox

### Installing from the shell (i.e. command prompt on Windows)

Optionally, you can also install Spine Toolbox on a Python without using 
Anaconda or Miniconda. If you run into problems by following the instructions 
here, please see [Troubleshooting](#troubleshooting) section below.

Step-by-step instructions:

1. Clone either the `master` or `dev` branch onto your computer
2. Install either Python 3.6 or Python 3.7
3. Install requirements

        pip install -r requirements.txt

4. Run 

        python -m spinetoolbox

Remember to update your clone occasionally with the 
[git pull](https://www.atlassian.com/git/tutorials/syncing/git-pull) command.


### Official releases

Release versions of Spine Toolbox can be found 
[here](https://drive.google.com/drive/folders/1t-AIIwRMl3HiYgka4ex5bCccI2gpbspK).
(only available for 64-bit Windows for now). Download the latest version, install and
run `spinetoolbox.exe`.

### About requirements

Python 3.6 or Python 3.7 is required.

See file `setup.py` and `requirements.txt` for packages required to run Spinetoolbox.

Additional packages needed for development are listed in `dev-requirements.txt`.
To install the development requirements, run:

    pip install -r dev-requirements.txt

#### Upgrading Requirements

To upgrade all required packages for Spine Toolbox, run

    pip install --upgrade -r requirements.txt

You may want to do this occasionally if it has been a long time (i.e. several months) 
since you first installed the requirements.

The developer requirements can be updated similarly by running

    pip install --upgrade -r dev-requirements.txt

The requirements include two packages (`spinedb_api` and `spine_engine`) developed by 
the Spine project consortium. Since they are developed very actively at the moment, you 
may need to upgrade these regularly.

#### Upgrading [spinedb_api](https://github.com/Spine-project/Spine-Database-API)

The package `spinedb_api` is required for running Spine Toolbox. Whenever you 
merge the latest changes from the remote server onto your local copy of the 
application (i.e. do a `git pull`), the application may request you to upgrade 
this package. You can either do this manually or by running an upgrade script, 
which has been added for convenience.

To upgrade with a script, run `upgrade_spinedb_api.bat` on Windows or 
`upgrade_spinedb_api.py` on Linux and Mac OS X. The scripts are located in the
`bin` directory.

To upgrade manually, run

    pip install --upgrade git+https://github.com/Spine-project/Spine-Database-API.git

#### Upgrading [spine_engine](https://github.com/Spine-project/spine-engine)

Package `spine_engine` is required for running Spine Toolbox. The application 
may request you to upgrade this package. You can either do this manually or by 
running an upgrade script, which has been added for convenience.

To upgrade with a script, run `upgrade_spine_engine.bat` on Windows or `upgrade_spinedb_api.py` 
on Linux and Mac OS X. The scripts are located in the `bin` directory.

To upgrade `spine_engine` manually, run

    pip install --upgrade git+https://github.com/Spine-project/spine-engine.git#egg=spine_engine

**Note:** You don't need to clone or download the `spinedb_api` nor the 
`spine_engine` source codes. *pip* takes care of installing the latest 
version from GitHub to your system automatically.


## Building the User Guide

Source files for the User Guide can be found in `docs/source` directory. In order to 
build the HTML docs, you need to install the *optional requirements* (see section 
'Installing requirements' above). This installs Sphinx (among other things), which 
is required in building the documentation. When Sphinx is installed, you can build the 
HTML pages from the user guide source files by using the `bin/build_doc.bat` script on 
Windows or the `bin/build_doc.sh` script on Linux and Mac. After running the script, the 
index page can be found in `docs/build/html/index.html`. The User Guide can also 
be opened from Spine Toolbox menu Help->User Guide (F2).

## Troubleshooting

### Installation fails

Please make sure you are using Python 3.6 or Python 3.7 to install the requirements.

### Installation fails on Linux
If Python runs into errors while installing on Linux systems, running the 
following commands in a terminal may help:
```shell
sudo apt install libpq-dev
sudo apt-get install unixodbc-dev
```

### Problems in starting the application

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

**Note**: Spine Toolbox does not support PySide2 5.12 version (yet).

## Contribution Guide

All are welcome to contribute!

See detailed instructions for contribution in [Spine Toolbox User Guide](https://spine-toolbox.readthedocs.io/en/latest/contribution_guide.html).

Below are the bare minimum things you need to know.

### Setting up development environment

1. Install the developer requirements.
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
