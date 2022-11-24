# Spine Toolbox
Link to the documentation: [https://spine-toolbox.readthedocs.io/en/latest/?badge=latest](https://spine-toolbox.readthedocs.io/en/latest/?badge=latest)

[![Python](https://img.shields.io/badge/python-3.7%20|%203.8%20|%203.9%20|%203.10-blue.svg)](https://www.python.org/downloads/release/python-379/)
[![Documentation Status](https://readthedocs.org/projects/spine-toolbox/badge/?version=latest)](https://spine-toolbox.readthedocs.io/en/latest/?badge=latest)
[![Test suite](https://github.com/Spine-project/Spine-Toolbox/actions/workflows/test_runner.yml/badge.svg)](https://github.com/Spine-project/Spine-Toolbox/actions/workflows/test_runner.yml)
[![codecov](https://codecov.io/gh/Spine-project/Spine-Toolbox/branch/master/graph/badge.svg)](https://codecov.io/gh/Spine-project/Spine-Toolbox)
[![PyPI version](https://badge.fury.io/py/spinetoolbox.svg)](https://badge.fury.io/py/spinetoolbox)

Spine Toolbox is an open source Python package to manage data, scenarios and workflows for modelling and simulation. You can have your local workflow, but work as a team through version control and SQL databases.

## Programming language

- Python 3.7
- Python 3.8
- Python 3.9
- Python 3.10 (requires Microsoft Visual C++ 14.0 or greater on Windows)

Python 3.8.0 is not supported (use Python 3.8.1 or later).

## License

Spine Toolbox is released under the GNU Lesser General Public License (LGPL) license. 
All accompanying documentation, original graphics and other material are released under the 
[Creative Commons BY-SA 4.0 license](https://creativecommons.org/licenses/by-sa/4.0/).
Licenses of all packages used by Spine Toolbox are listed in the Spine Toolbox User 
Guide.

## Attribution

If you use Spine Toolbox in a published work, please cite the following publication (Chicago/Turabian Style).

Kiviluoma Juha, Pallonetto Fabiano, Marin Manuel, Savolainen Pekka T., Soininen Antti, Vennström Per, Rinne Erkka, Huang Jiangyi, Kouveliotis-Lysikatos Iasonas, Ihlemann Maren, Delarue Erik, O’Dwyer Ciara, O’Donnel Terence, Amelin Mikael, Söder Lennart, and Dillon Joseph. 2022. "Spine Toolbox: A flexible open-source workflow management system with scenario and data management" SoftwareX, Vol. 17, 100967, https://doi.org/10.1016/j.softx.2021.100967.

## Installation

We provide three options for installing Spine Toolbox: 
[Python/pipx](#installation-with-python-and-pipx), 
[Windows installation package](#windows-64-bit-installer-package) (these are quite old - not recommended)
and [from source files](#installation-from-sources-using-git).

### Installation with Python and pipx

This works best for users that want to just use Spine Toolbox but also keep it 
updated with new releases.

1. If you don't yet have Python installed, the recommended version is the latest **Python 3.9** release
   from [Python.org](https://www.python.org/downloads/release/python-3913/).

2. Python 3.10 support is in experimental stage. If you want to try it out, please
   install **Microsoft Visual C++ 14.0 or greater** on Windows. Get it with *Microsoft C++ 
   Build Tools*: https://visualstudio.microsoft.com/visual-cpp-build-tools/.

3. Open a terminal (e.g., Command Prompt on Windows).

4. Get the latest version of `pip` (pip is a package manager for Python)

        python -m pip install --upgrade pip

5. Install [pipx](https://pypa.github.io/pipx/) (pipx allows to create an isolated 
   environment for Spine Toolbox to avoid package conflicts with other Python tools)

        python -m pip install --user pipx
        python -m pipx ensurepath

6. Restart the terminal or re-login for the changes of the latest command to take effect.

7. Choose which Toolbox version to install. Latest *release* version is installed using

        python -m pipx install spinetoolbox

   or get the latest *development* version using

        python -m pipx install git+https://github.com/Spine-project/spinetoolbox-dev

That’s it! To launch Spine Toolbox, open a terminal and run

    spinetoolbox

If for some reason the command is not found, the executable can be found under 
`~/.local/bin` (`%USERPROFILE%\.local\bin` on Windows).

To update Spine Toolbox to the latest available release, open a terminal and run

    python -m pipx upgrade spinetoolbox

Here, replace `spinetoolbox` with `spinetoolbox-dev` if you installed the latest
development version.


### Windows 64-bit installer package

There are old Windows installer packages available for a quick install, but they are
at this point (3.11.2022) quite obsolete and cannot be recommended for anything but 
a quick look at how Spine Toolbox looks and feels (although even that has changed).
Download the installer package from 
[here](https://github.com/Spine-project/Spine-Toolbox/releases),
run it, and follow the instructions to install Spine Toolbox.


### Installation from sources using Git

This option is for developers and other contributors who want to debug or 
edit Spine Toolbox source code. First, follow the instructions above to 
install Python and get the latest version of pip.

1. Clone or download the source code from this repository.
   
2. Browse to the folder and create a virtual environment using

        python -m venv .venv

    or a new [conda](https://docs.conda.io/projects/conda/) environment using 

        conda create -n spinetoolbox python=3.9
    
3. Activate the environment using `.venv\Scripts\activate.bat` (Windows cmd.exe) 
   or `source .venv/bin/activate` (bash, zsh) or `conda activate spinetoolbox`. 

4. Make sure that the terminal prompt indicates the active environment
   and get the latest version of `pip` (pip is a package manager for Python)

        python -m pip install --upgrade pip

5. Install Spine Toolbox along with its dependencies with

        python -m pip install -r requirements.txt
    
6. (Optional) Install additional development packages with

        python -m pip install -r dev-requirements.txt

You can now launch Spine Toolbox by calling `spinetoolbox` when the environment 
is active. 

**To upgrade**, pull or copy the latest changes from the repository and run

    python -m pip install -U -r requirements.txt


### About requirements

Python 3.7, 3.8, 3.9, or 3.10 is required. Python 3.8.0 is not supported due to problems in DLL loading on Windows.

See file `setup.cfg` and `requirements.txt` for packages required to run Spine Toolbox.
(Additional packages needed for development are listed in `dev-requirements.txt`.)

The requirements include three packages ([`spinedb_api`](https://github.com/Spine-project/Spine-Database-API),
[`spine_engine`](https://github.com/Spine-project/spine-engine), and [`spine_items`](https://github.com/Spine-project/spine-items)),
developed by the Spine project consortium.

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

Please make sure you are using Python 3.7, 3.8, 3.9, or 3.10 to install the requirements.

If you are on **Python 3.10**, please install **Microsoft Visual C++ 14.0 or greater** on Windows. 
Get it with *Microsoft C++ Build Tools*: https://visualstudio.microsoft.com/visual-cpp-build-tools/.

#### Installation fails on Linux
If Python runs into errors while installing on Linux systems, running the 
following commands in a terminal may help:

```shell
$ sudo apt install libpq-dev
$ sudo apt-get install unixodbc-dev
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
installs `qt` and `PyQt` packages. Since this is a `PySide2` application, those 
are not needed and there is a chance of conflicts between the packages.

**Note**: Python 3.8.0 is not supported. Use Python 3.8.1 or later.

## Contribution Guide

All are welcome to contribute!

See detailed instructions for contribution in 
[Spine Toolbox User Guide](https://spine-toolbox.readthedocs.io/en/latest/contribution_guide.html).

Below are the bare minimum things you need to know.

### Setting up development environment

1. Install the developer requirements:

        python -m pip install -r dev-requirements.txt

2. Optionally, run `pre-commit install` in project's root directory. This sets up some git hooks.

### Coding style

- [Black](https://github.com/python/black) is used for Python code formatting.
  The project's GitHub page includes instructions on how to integrate Black in IDEs.
- Google style docstrings

### Linting

It is advisable to run [`pylint`](https://pylint.readthedocs.io/en/latest/) 
regularly on files that have been changed.
The project root includes a configuration file for `pylint`.
`pylint`'s user guide includes instructions on how to 
[integrate the tool in IDEs](https://pylint.readthedocs.io/en/latest/user_guide/ide-integration.html#pylint-in-pycharm).

### Unit tests

Unit tests are located in the `tests` directory.
You can run the entire test suite from project root by

    python -m unittest

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
<center>
<table width=500px frame="none">
<tr>
<td valign="middle" width=100px>
<img src=https://europa.eu/european-union/sites/europaeu/files/docs/body/flag_yellow_low.jpg alt="EU emblem" width=100%></td>
<td valign="middle">This project has received funding from the European Union’s Horizon 2020 research and innovation programme under grant agreement No 774629.</td>
</table>
</center>
