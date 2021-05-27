.. How to set up and run SpineOpt.jl documentation
   Created 26.5.2021

.. |execute| image:: ../../spinetoolbox/ui/resources/menu_icons/play-circle-solid.svg
             :width: 16

.. _How to set up and run SpineOpt.jl:

*********************************
How to set up and run SpineOpt.jl
*********************************

The instructions on how to set up and run `SpineOpt.jl <https://github.com/Spine-project/SpineOpt.jl>`_ in
Spine Toolbox depends on how you have installed Spine Toolbox. **The installation options are:**

1. Using a single-file *installation bundle* (**spine-toolbox-0.6.0-final.0-x64.exe**). You can find this
   file and the latest releases from
   `Spine Toolbox releases <https://github.com/Spine-project/Spine-Toolbox/releases>`_.
   The installation bundles are only available for Windows at the moment.
2. Cloning Spine Toolbox Git repository from `<https://github.com/Spine-project/Spine-Toolbox>`_. Checkout branch
   **release-0.6** and follow the installation instructions on **README.md**.

.. note:: Spine Toolbox **v0.6.0** is shipped with **spinedb_api v0.12.1**, **spine_engine v0.10.0**,
   and **spine_items v0.7.5** and is compatible with **SpineOpt.jl v0.5.9**.

Setting up SpineOpt.jl for Spine Toolbox installed using an installation bundle
-------------------------------------------------------------------------------

When you have successfully installed Spine Toolbox using **spine-toolbox-0.6.0-final.0-x64.exe**,
do the following:

#. Install Julia from `<https://julialang.org/downloads/>`_ if you don't have one

#. Start Spine Toolbox

#. Create a new project (*File->New project...*)

#. Select `File->Settings` from the main menu and open the `Tools` page.

#. Set a path to a Julia executable to the appropriate line edit (e.g. *C:\\Julia-1.5.4\\bin\\julia.exe*)

#. Set the Python interpreter to `<install_dir>\\Tools\\Python.exe` (if you installed Spine Toolbox to the default
   directory this is *C:\\Program Files\\Spine Toolbox\\tools\\Python.exe*). Your selections should look similar to
   this now.

   .. image:: img/settings_tools_filled_for_spineopt.png
      :align: center

   .. note:: If you already have a Python in your PATH, the Python interpreter line edit will show this Python in
      the line edit. **Change it to <install_dir>\\tools\\Python.exe**, because this 'embedded' Python has
      access to the `spinedb_api` package that is shipped with the application.

#. Click the `Add/Update SpineOpt` button and click `Next` twice and finally `Install SpineOpt`. This installs
   `SpineOpt.jl` package for the Julia you just selected. **Wait until the process has finished** and you are
   greeted with this screen.

   .. image:: img/spineopt_install_wizard_successful.png
      :align: center

   Close the wizard.

#. Click Ok to close the `Settings` window
#. Back in the main window, select `PlugIns->Install plugin…` from the menu
#. Select `SpineOpt` and click Ok. After a short while, a red *SpineOpt Plugin Toolbar* appears on the main window.

Setting up SpineOpt.jl for Spine Toolbox installed from GitHub
--------------------------------------------------------------

When you have successfully installed the application by following the instructions in **README.md**,
do the following:

#. Install Julia from `<https://julialang.org/downloads/>`_ if you don't have one

#. Start Spine Toolbox

#. Create a new project (*File->New project...*)

#. Select `File->Settings` from the main menu and open the `Tools` page.

#. Set a path to a Julia executable to the appropriate line edit (e.g. *C:\\Julia-1.5.4\\bin\\julia.exe*)

#. The default Python interpreter is the **Python that was used in launching the application** (i.e. *sys.executable*).
   This is shown as placeholder (gray) text in the line edit. Leave it as it is.

   .. image:: img/settings_tools_filled_for_spineopt_github.png
      :align: center

#. Click the `Add/Update SpineOpt` button and click `Next` twice and finally `Install SpineOpt`. This installs
   `SpineOpt.jl` package for the Julia you just selected. **Wait until the process has finished** and you are
   greeted with this screen.

   .. image:: img/spineopt_install_wizard_successful.png
      :align: center

   Close the wizard.

#. Click Ok to close the `Settings` window
#. Back in the main window, select `PlugIns->Install plugin…` from the menu
#. Select `SpineOpt` and click Ok. After a short while, a red *SpineOpt Plugin Toolbar* appears on the main window.

How to run SpineOpt.jl
----------------------

After you have completed the set up phase, do the following to test **SpineOpt.jl**:

#. Make sure you have either opened an existing project or created a new one in Spine Toolbox

#. Drag the `Load template` icon from the *SpineOpt Plugin Toolbar* to *Design View*. Remove * 1* from the
   suggested name to make it look cleaner and click Ok to accept the dialog.

#. Create a Data Store item by dragging its icon from the *Main Toolbar* to *Design View*. Name it *Spine Db* or
   something.

#. Drag the `Run SpineOpt` icon from the *SpineOpt Plugin Toolbar* to *Design View*. Again, remove * 1* from
   the suggested name and accept the dialog.

   .. tip:: You can rename project items from the context-menu (mouse right-click menu).

#. Select `Spine Db`. In *Data Store Properties* widget, set the dialect to *sqlite* and click *New Spine db* button.
   Accept the default filename and folder by clicking *Save*.

#. Create a workflow on *Design View* by connecting items `Load template` -> `Spine Db` -> `Run SpineOpt`.

#. Select `Load template` item on *Design View*. In *Tool Properties* widget, drag *db_url@Spine Db*
   item from *available resources* box and drop it onto *type new arg here...* text in the *Command line
   arguments* box. *Design View* and `Load template` properties should look like this now:

   .. image:: img/main_window_spineopt_load_template_ready.png
      :align: center

   .. tip:: The 'curved' links (yellow arrows) connecting project items are an option in `File->Settings`.

#. Do the same for `Run SpineOpt` item. Select `Run SpineOpt` item on *Design View*. In *Tool Properties* widget,
   drag *db_url@Spine Db* item from *available resources* box and drop it onto *type new arg here...* text in
   the *Command line arguments* box.

#. Save the project (`File->Save project` or `Ctrl-s`)

#. Press |execute| to execute the project

Congratulations! You have run **SpineOpt.jl** using Spine Toolbox.

For more information on how to select a specific Python or Julia version, see :ref:`Setting up External Tools`).
See also the :ref:`Getting Started` section for information on how to run a simple Python script using Spine Toolbox.
