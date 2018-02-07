# Spine Toolbox

An application to define, manage, and execute various energy system 
simulation models.

## Requirements

- Python 3.5+
- PySide2 for Qt 5.6+

### Installing PySide2 for Anaconda & Miniconda Python (3.5+)

PySide2 for Qt 5.6.2 is available on conda-forge channel. You need to 
add this channel to your `conda` like this,

    conda config --add channels conda-forge

Now you can install PySide2 with

    conda install pyside2

### Installing PySide2 on Python

Download wheel from http://hansch.info/PySide2/

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

If your PySide2 folder is in another path, modify Prefix and Binaries 
lines accordingly.

Spine Toolbox should now work and you are ready to develop the core 
application components. If you want to develop the Graphical User 
Interface (views, buttons, menus, etc.) you need the PySide2 GUI 
development tools.

### Installing PySide2 GUI Development Tools (Windows)

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
project from

https://code.qt.io/pyside/pyside-setup.git

Checkout branch `dev`

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

### Preparing and starting Spine Toolbox

Run 'build_ui.bat' from your Python/PySide2 enabled command window to generate
the code for the Spine Toolbox user interface.
After modifying the user interface ('.ui') files with 'designer.exe', re-run 
`build_ui.bat` to build the Spine Toolbox interface anew.

In the command prompt, run 'python spinetoolbox.py' in the SpineToolbox folder.
