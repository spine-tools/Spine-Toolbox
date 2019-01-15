.. Settings form documentation
   Created 14.1.2019

********
Settings
********

Spine Toolbox settings are categorized in the following way:

.. contents::
    :local:

Application settings
--------------------

You can open the application settings from the main window menu `File->Settings...`, or by pressing `F1`.

.. image:: img/settings_form.png
   :align: center

The settings on this form have been categorized into five categories. The *General*, *GAMS*, *Julia*, and
*Data Store views* settings are general application settings, which affect all projects. Settings in the
*Project* category only affect the current project. The general application settings are saved to file called
``settings.conf`` in your application directory. It is safe to delete this file if you want to go back to default
settings.

General settings
================

- **Open previous project at exit** If checked, application opens the project at startup that was open the last
  time the application was exited. If left unchecked, application starts without a project open.
- **Show confirm exit prompt** If checked, confirm exit prompt is shown. If unchecked, application exits
  without prompt.
- **Save project at exit** Unchecked: Does not save project and does not show message box. Partially checked:
  Shows message box (default). Checked: Saves project and does not show message box.
- **Show date and time in Event Log messages** If checked, date and time string is appended into every Event
  Log message.
- **Delete data when project item is removed from project** Check this box to delete project item's data when
  a project item is removed from project. This means, that the project item directory and its contents will be
  deleted from your HD.
- **Project directory** Directory where projects are saved. This is non-editable at the moment.

GAMS settings
=============
- **Path to GAMS executable** Path to directory where GAMS and GAMSIDE executables are found. GAMS in the
  selected directory is used to execute GAMS tools. You can leave this blank to use the system GAMS i.e. GAMS
  that you have set up in your system PATH variable.

Julia settings
==============
- **Run Julia scripts in REPL** Check this option to execute Julia tools in the built-in Julia REPL. If you leave
  this un-checked, Julia tools will be executed as in the shell. For example, on Windows this would be the
  equivalent as running command ``julia.exe example_script.jl`` in the command prompt. If using the Julia REPL,
  the ``example_script.jl`` is *included* into the built-in Julia REPL and executed there.
- **Path to Julia executable**. Path to Julia executable that you wish to use to execute Julia Tools. This is the
  Julia REPL that will be used if REPL execution is preferred and also the Julia executable used when executing
  Julia tools as in the shell. You can leave this blank, if you wish to use the system Julia.

Data Store views settings
=========================
- **Commit session at exit** This checkbox controls what happens when you close the tree view, graph view,
  or the tabular view when you have uncommitted changes. Unchecked: Does not commit session and does not show
  message box. Partially checked: Shows message box (default). Checked: Commits session and does not show
  message box.
- **Use smooth zoom in graph view** Controls if the zoom in/out in graph view is continuous or if there are
  discrete steps in zooming. On slower computers, it's recommended to not use smooth zooming.

Project settings
----------------
These settings affect only the project that is currently open.

- **Name** Current project name. If you want to change the name of the project, use menu option `File-Save as...`.
- **Description** Current project description. You can edit the description here.
- **Work directory** Directory where processing the Tool takes place. You can change this directory. Make sure to
  clean up the directory every now and then.

Project item settings / properties
----------------------------------
Each project item (Data Store, Data Connection, Tool, or View) has its own set of properties. These are saved
into the project save file. You can view and edit them in project item properties on the main window.

Application preferences
-----------------------
Spine Toolbox remembers the size, location, and placement of most of the application windows from the
previous session (i.e. when closing and restarting the app). These settings are saved to a location depending
on your operating system. E.g. on Windows you can find these settings in the registry key
``HKEY_CURRENT_USER\Software\SpineProject\Spine Toolbox``. Its safe to delete this key if you want to reset
the preferences to factory settings.
