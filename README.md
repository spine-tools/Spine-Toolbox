# Spine Toolbox
Link to the documentation: [https://spine-toolbox.readthedocs.io/en/latest/?badge=latest](https://spine-toolbox.readthedocs.io/en/latest/?badge=latest)

[![Python](https://img.shields.io/badge/python-3.11%20|%203.12%20|%203.13%20|%203.14-blue.svg)](https://www.python.org/downloads/release/python-3120/)
[![Documentation Status](https://readthedocs.org/projects/spine-toolbox/badge/?version=latest)](https://spine-toolbox.readthedocs.io/en/latest/?badge=latest)
[![Test suite](https://github.com/spine-tools/Spine-Toolbox/actions/workflows/test_runner.yml/badge.svg)](https://github.com/spine-tools/Spine-Toolbox/actions/workflows/test_runner.yml)
[![codecov](https://codecov.io/gh/spine-tools/Spine-Toolbox/branch/master/graph/badge.svg)](https://codecov.io/gh/spine-tools/Spine-Toolbox)
[![PyPI version](https://badge.fury.io/py/spinetoolbox.svg)](https://badge.fury.io/py/spinetoolbox)
[![Join the chat at https://gitter.im/spine-tools/Spine-Toolbox](https://badges.gitter.im/spine-tools/Spine-Toolbox.svg)](https://gitter.im/spine-tools/Spine-Toolbox?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)

Spine Toolbox is an open source Python package to manage data, scenarios and workflows for modelling and simulation. 
You can have your local workflow, but work as a team through version control and SQL databases.

<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="./fig/spinetoolbox_logo.svg" width="50%">
    <img alt="Spine Toolbox" src="./fig/spinetoolbox_on_wht.svg" width="50%">
  </picture>
</p>

## License

Spine Toolbox is released under the GNU Lesser General Public License (LGPL) license. 
All accompanying documentation, original graphics and other material are released under the 
[Creative Commons BY-SA 4.0 license](https://creativecommons.org/licenses/by-sa/4.0/).
Licenses of all packages used by Spine Toolbox are listed in the Spine Toolbox User 
Guide.

## Attribution

If you use Spine Toolbox in a published work, please cite the following publication (Chicago/Turabian Style).

Kiviluoma Juha, Pallonetto Fabiano, Marin Manuel, Savolainen Pekka T., Soininen Antti, Vennström Per, Rinne Erkka, 
Huang Jiangyi, Kouveliotis-Lysikatos Iasonas, Ihlemann Maren, Delarue Erik, O’Dwyer Ciara, O’Donnel Terence, 
Amelin Mikael, Söder Lennart, and Dillon Joseph. 2022. "Spine Toolbox: A flexible open-source workflow management 
system with scenario and data management" SoftwareX, Vol. 17, 100967, https://doi.org/10.1016/j.softx.2021.100967.

## Installation

We provide multiple options for installing Spine Toolbox.

- [Windows executable as .zip bundle](https://spine-tools.github.io/Downloads/) Requires only unzipping the downloaded .zip file.
  Use the bundle if you are on Windows and want to get started with Spine Toolbox quickly.
- [Python/pipx](#installation-with-python-and-pipx) Requires Python installation.
  Use this option if you are on Linux or your tools need specific Python environments to run.
- [MacOS from source files using Homebrew](#macos-installation-from-sources-with-homebrew)
  Use this option if you are on Mac.

### Installation with Python and pipx

This installation methods is for users on Linux systems
or if you want to run Python scripts and tools which require specific Python environments in Spine Toolbox.

1. If you don't have Python installed, please install it e.g. from 
[Python.org](https://www.python.org/downloads/).
Please note that we support Python versions from 3.11 to 3.15.

2. Install [pipx](https://pypa.github.io/pipx/). pipx creates an isolated environment for Spine 
Toolbox to avoid package conflicts. Open a terminal and run

        python -m pip install --user pipx

    After pipx has been installed, run

        python -m pipx ensurepath

3. **Restart the terminal** or re-login for the changes of the latest command to take effect.

4. Install latest Spine Toolbox using 

        python -m pipx install spinetoolbox

That’s it! To launch Spine Toolbox, open a terminal and run

    spinetoolbox

If for some reason the command is not found, the executable can be found under `~/.local/bin` 
(`%USERPROFILE%\.local\bin` on Windows).

### Upgrade when using pipx

To upgrade Spine Toolbox to the latest release, open a terminal and run

    python -m pipx upgrade spinetoolbox

### MacOS installation from sources with Homebrew

1. Open Terminal.
2. Install [Homebrew](https://brew.sh).
3. Install Python with

        brew install python

4. Restart Terminal. Ensure your Python is the one from Homebrew by checking that the following command gives `/opt/homebrew/bin/python3`

        which python3

5. Clone this repository with

        git clone https://github.com/spine-tools/Spine-Toolbox.git

6. Use the `cd` command to go to `Spine-Toolbox` directory that was just created

        cd Spine-Toolbox

7. Create a Python virtual environment

        python3 -m venv venv

8. Activate the virtual environment (yes, the next command starts with a `.` and a space)

        . venv/bin/activate

9. Install Spine Toolbox along with its dependencies with

        python -m pip install -r requirements.txt

10. Once the installation has finished, you can now launch Spine Toolbox using

        spinetoolbox

Successfully installed Spine Toolbox can be launched from Terminal with

    cd Spine-Toolbox
    . venv/bin/activate
    spinetoolbox

### Upgrading MacOS installation

To upgrade, pull the latest changes from the Spine Toolbox repository

    cd Spine-Toolbox
    git pull
    git fetch --tags origin

then upgrade the other Spine Toolbox packages by running

    python -m pip install -U -r requirements.txt

**NOTE:** The version number of Spine packages are automatically
generated from Git tags during the `python -m pip install ...` step. 
This makes it important to fetch new tags from GitHub before running the 
`python -m pip install ...` when upgrading.

#### Additional comments for developers

If you are alternating between multiple branches, you should repeat
the `pip install -e .` step after switching a branch.  This ensures
the version number is updated correctly.  On the other hand if you do
not need the version number to be precise, it is okay to skip the
step.

To illustrate with an example, consider there are two feature branches
`P` and `Q` that you are working on. Both are based on `master` after
the release `0.6.18`.

```
 0.6.18
---o----o--o--o  P
    \
     o--o--o--o  Q
```

Then the versions are:
- `P`: `0.7.0.dev3+g<commit-hash-P>.d<commit-date-P>`,
- `Q`: `0.7.0.dev4+g<commit-hash-Q>.d<commit-date-Q>`.

The version should be available inside Python as:
```python
from spinetoolbox.version import version_tuple

print(version_tuple)
# P: (0, 7, 0, 'dev3', 'g<commit-hash-P>.d<commit-date-P>')
# Q: (0, 7, 0, 'dev4', 'g<commit-hash-Q>.d<commit-date-Q>')
```

So if your code uses any of the components of the `version_tuple` that
might change, you should re-run `pip install`, otherwise this can be 
ignored safely.

### About requirements

Python 3.11 or later is required (check above for supported Python versions).

See the files `pyproject.toml` and `requirements.txt` for packages required to run Spine Toolbox.
(Additional packages needed for development are listed in `dev-requirements.txt`.)

The requirements include three Spine packages ([`spinedb_api`](https://github.com/spine-tools/Spine-Database-API),
[`spine_engine`](https://github.com/spine-tools/spine-engine), and 
[`spine_items`](https://github.com/spine-tools/spine-items)).

### Building the User Guide

You can find the latest documentation on [readthedocs](https://spine-toolbox.readthedocs.io/en/latest/index.html).
If you want to build the documentation yourself,
source files for the User Guide can be found in `docs/source` directory. In order to 
build the HTML docs, you need to install the *development requirements* (see section 
'About requirements' above). This installs Sphinx (among other things), which 
is required in building the documentation. When Sphinx is installed, you can build the 
HTML pages from the user guide source files by using the `bin/build_doc.bat` script on 
Windows or the `bin/build_doc.py` script on Linux and Mac. After running the script, the 
index page can be found in `docs/build/html/index.html`. The User Guide can also 
be opened from Spine Toolbox menu Help->User Guide (F1).

### Troubleshooting

#### Obscure crashes that may produce a traceback related to PySide6's model classes

The first thing is to make sure that you are not using Anaconda. Only Miniconda is supported. Anaconda's base 
environment includes Qt related packages and we suspect that they leak some shared Qt libraries into environments,
even when specifically requesting that base environment packages should not be linked to environment packages. See
also [Problems in starting the application](#problems-in-starting-the-application) below.

#### Installation fails

Please make sure you are using Python 3.11 or later to install the requirements (check above for supported Python versions).

#### 'No Python' error when installing with pipx

If you see the following error when running the command `python -m pipx install spinetoolbox`

```
No Python at 'c:\python38\python.exe'
Fatal error from pip prevented installation. Full pip output in file:
```

Where c:\python38\python.exe may be some other path. To fix this, delete the folder 
`C:\Users\<user name>\.local\pipx\shared` and run the `python -m pipx install spinetoolbox` command again.

#### Installation fails on Linux
If Python runs into errors while installing on Linux systems, running the 
following command in a terminal may help:

```shell
$ sudo apt install libpq-dev
```

#### Problems in starting the application

If there are problems in starting Spine Toolbox, the chances are that the required 
packages were not installed successfully. In case this happens, the first thing you 
should check is that you don't have `Qt`, `PyQt4`, `PyQt5`, `PySide`, `PySide2`, and 
`PySide6` packages installed in the same environment. These do not play nice together 
and may introduce conflicts. In addition, make sure that you do not have multiple versions 
of these `Qt` related packages installed in the same environment. The easiest way 
to solve this problem is to create a blank (e.g. venv virtual environment) Python 
environment just for `PySide6` applications and installing the requirements again.

**Warning: Using the *conda-forge* channel for installing the requirements is not 
recommended.**

The required `qtconsole` package from the ***conda-forge*** channel also
installs `qt` and `PyQt` packages. Since this is a `PySide6` application, those 
are not needed and there is a chance of conflicts between the packages.

#### Problems in running the application

Creating arrows may fail on Fedora Linux, as described in [issue #3286](https://github.com/spine-tools/Spine-Toolbox/issues/3286).
A workaround is to install a separate Python and use that to install Spine Toolbox.

## Webinars showing the use of Spine Tools

Check out our [webinar series](https://github.com/spine-tools#community-speech_balloon) (recordings available) to see Spine Toolbox in action!

## Contribution Guide

All are welcome to contribute!

See detailed instructions for contribution in 
[Spine Toolbox User Guide](https://spine-toolbox.readthedocs.io/en/latest/contribution_guide.html).

Below are the bare minimum things you need to know.

### Setting up development environment

1. Install the developer requirements:

        python -m pip install -r dev-requirements.txt

2. It is also recommended to run `pre-commit install` in the respective root directories of spine-toolbox, spinedb_api,
   spine-engine and spine-items. This sets up git hooks for auto-formatting the files before committing.

### Coding style

- [Black](https://github.com/python/black) is used for Python code formatting.
  The project's GitHub page includes instructions on how to integrate Black in IDEs.
- [isort](https://pycqa.github.io/isort/) is used for formatting the Python import statements.
- Google style docstrings

Running the following line in the project root will take care of sorting the imports:

    isort .

### Linting

It is advisable to run [`pylint`](https://pylint.readthedocs.io/en/latest/) 
regularly on files that have been changed.
The project root includes a configuration file for `pylint`.
`pylint`'s user guide includes instructions on how to 
[integrate the tool in IDEs](https://pylint.readthedocs.io/en/latest/user_guide/ide-integration.html#pylint-in-pycharm).

### Unit tests

Unit tests are located in the `tests` directory while execution tests are in `execution_tests`.
You can run the entire test suite from project root by

    python -m pytest

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
The developers of Spine Toolbox are happy to hear feature requests or ideas for improving 
existing functionality. The format for requesting new features is free. Just fill 
out the required fields on the issue tracker and give a description of the new feature. 
A picture accompanying the description is a good way to get your idea into development
faster. But before you make a new issue, please check that there isn't a related idea 
already open in the issue tracker.

&nbsp;
<hr>
<table width=500px frame="none">
<tr>
<td valign="middle" width=100px>
<img src=fig/eu-emblem-low-res.jpg alt="EU emblem" width=100%></td>
<td valign="middle">This work has been partially supported by EU project Mopo (2023-2026), which has received funding 
from European Climate, Infrastructure and Environment Executive Agency under the European Union’s HORIZON Research and 
Innovation Actions under grant agreement N°101095998.</td>
<tr>
<td valign="middle" width=100px>
<img src=fig/eu-emblem-low-res.jpg alt="EU emblem" width=100%></td>
<td valign="middle">This work has been partially supported by EU project Spine (2017-2021), which has received funding 
from the European Union’s Horizon 2020 research and innovation programme under grant agreement No 774629.</td>
</table>
