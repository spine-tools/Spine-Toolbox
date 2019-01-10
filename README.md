# Spine Toolbox

An application to define, manage, and execute various energy system simulation models.

## License

Spine Toolbox is released under the GNU Lesser General Public License (LGPL) license. All accompanying
documentation, original graphics, and manual are released under the Creative Commons BY-SA 4.0 license.
Licenses of all packages used by Spine Toolbox are listed in the Spine Toolbox User 
Guide.

## Running Spine Toolbox

### Releases

Release versions of Spine Toolbox can be found 
[here](https://drive.google.com/drive/folders/1t-AIIwRMl3HiYgka4ex5bCccI2gpbspK).
(only available for 64-bit Windows for now). Download the latest version, install and
run `spinetoolbox.exe`.

### Getting the latest development version

The `master` branch contains the latest release version of the application. The 
development happens on the `dev` branch. To get the latest features 
and bug fixes you need to 
[clone](https://help.github.com/articles/cloning-a-repository/) or download the latest 
version of the source code to your computer.

Step-by-step instructions:

1. Clone either the `master` or `dev` branch onto your computer
2. Install Python (3.5->)
3. Install requirements (see below)
4. Go to directory `\spinetoolbox` and run 

        python spinetoolbox.py

Remember to update your clone occasionally with the 
[git pull](https://www.atlassian.com/git/tutorials/syncing/git-pull) command.

## Requirements

Python 3.5 or higher is required.

See file `requirements.txt` for must have packages and file `optional-requirements.txt`
for optional ones. The optional requirements contain the SQL dialect API packages 
(can also be installed at runtime), packages for building the User Guide (Sphinx), 
and a package for deploying the application (cx_Freeze).
 
### Installing requirements

After cloning or downloading the repository, open terminal (e.g. command prompt 
on Windows). Change directory to Spine Toolbox root directory (the one that contains 
requirements.txt)  

Run

    pip install -r requirements.txt

If everything goes smoothly, you can now run Spine Toolbox.

To install optional requirements run

    pip install -r optional-requirements.txt

### Installing requirements for Anaconda & Miniconda Python

The recommended way to install dependencies using Anaconda or Miniconda is:

1. Open Anaconda prompt

2. Create a new environment by typing

        conda create -n spinetoolbox python=3.7

3. Activate the new environment

        conda activate spinetoolbox

4. cd to Spine Toolbox root directory (the one with requirements.txt)

5. Install requirements using **pip**

        pip install -r requirements.txt

6. And finally to install optional requirements run

        pip install -r optional-requirements.txt

### Upgrading spinedatabase_api

The package `spinedatabase_api` is required for running Spine Toolbox. It is being 
actively developed in 
[Spine-Database-API](https://github.com/Spine-project/Spine-Database-API) GitHub 
project by the Spine project consortium. Starting the application may require 
upgrading this package to the latest version. You can either upgrade the package 
manually or run an upgrade script, which has been added for convenience.  

To upgrade `spinedatabase_api` manually, run

    pip install --upgrade git+https://github.com/Spine-project/Spine-Database-API.git

Or run `upgrade_spinedatabase_api.bat` on Windows or `upgrade_spinedatabase_api.sh` 
on Linux and Mac OS X. The scripts are located in the `/bin` directory.

**Note:** You don't need to clone or download the `spinedatabase_api` source code. 
*pip* takes care of installing the latest version from GitHub to your system 
automatically.

### Upgrading all dependencies

You can upgrade all required packages for Spine Toolbox to the newest available 
version with a single command

    pip install --upgrade -r requirements.txt

You may want to do this occasionally if it has been a long time (i.e. several months) 
since you first installed the requirements.

## Building the User Guide

Source files for the User Guide can be found in `/docs/source` directory. In order to 
build the HTML docs, you need to first follow the above 'Upgrading all dependencies'
(among other things this installs Sphinx, which is the documentation builder).
After that, you can build HTML pages from the source files by using `/bin/build_doc.bat` 
(Windows) or `/bin/build_doc.sh` (Linux) scripts. After running the script, the 
index page can be found in `/docs/build/html/index.html`. The User Guide can also 
be opened from Spine Toolbox menu Help->User Guide (F2).

## Troubleshooting

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

### Feature Requests
The developers of Spine Toolbox are happy to hear new ideas for features or improvements 
to existing functionality. The format for requesting new features is free. Just fill 
out the required fields on the issue tracker and give a description of the new feature. 
A picture accompanying the description is a good way to get your idea into development
faster. But before you make a new issue, please check that there isn't a related idea 
already open in the issue tracker.
