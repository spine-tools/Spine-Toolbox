.. How to set up and run SpineOpt.jl documentation
   Created 26.5.2021

.. |execute| image:: ../../spinetoolbox/ui/resources/menu_icons/play-circle-solid.svg
             :width: 16

.. _How to set up and run SpineOpt.jl:

*********************************
How to set up and run SpineOpt.jl
*********************************

#. Install Julia from `<https://julialang.org/downloads/>`_ if you don't have one

#. Start Spine Toolbox

#. Create a new project (*File->New project...*)

#. Select `File->Settings` from the main menu and open the `Tools` page.

#. Set a path to a Julia executable to the appropriate line edit (e.g. *C:\\Julia-1.5.4\\bin\\julia.exe*).
   Your selections should look similar to this now.

   .. image:: img/settings_tools_filled_for_spineopt_github.png
      :align: center

#. Next, you need to install **SpineOpt.jl** package for the Julia you just selected for Spine Toolbox. You can do
   this manually by following the instructions `here <https://github.com/Spine-project/SpineOpt.jl#installation>`_
   **or** you can install **SpineOpt.jl** by clicking the `Add/Update SpineOpt` button. After clicking the button,
   an install/upgrade Spineopt wizard appears. Click `Next` twice and finally `Install SpineOpt`.
   **Wait until the process has finished** and you are greeted with this screen.

   .. image:: img/spineopt_install_wizard_successful.png
      :align: center

   Close the wizard.

#. Click Ok to close the `Settings` window
#. Back in the main window, select `PlugIns->Install plugin…` from the menu
#. Select `SpineOpt` and click Ok. After a short while, a red *SpineOpt Plugin Toolbar* appears on the main window.
#. SpineOpt.jl is ready for action

.. note:: The *SpineOpt Plugin Toolbar* contains two predefined Tools that make use of SpineOpt.jl. **The SpineOpt
   Plugin is not a requirement to run SpineOpt.jl**, they are provided just for convenience and as examples to get
   you started quickly.

How to run SpineOpt.jl
----------------------

After you have completed the set up phase, do the following to test **SpineOpt.jl** using the SpineOpt Plugin:

   .. note:: If you want to do something meaningful with SpineOpt.jl, please see e.g. section :ref:`Tutorials`.

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
