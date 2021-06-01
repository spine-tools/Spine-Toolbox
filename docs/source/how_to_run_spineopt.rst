.. How to set up SpineOpt.jl documentation
   Created 26.5.2021

.. |execute| image:: ../../spinetoolbox/ui/resources/menu_icons/play-circle-solid.svg
             :width: 16

.. _How to set up SpineOpt.jl:

*************************
How to set up SpineOpt.jl
*************************

#. Install Julia (v1.2 or later) from `<https://julialang.org/downloads/>`_ if you don't have one.
   See latest Julia compatibility information `here <https://github.com/Spine-project/SpineOpt.jl#spineoptjl>`_.

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

Spine Toolbox and Julia are now correctly set up for running **SpineOpt.jl**. Next step is to
`Create a project workflow using SpineOpt.jl <https://spine-project.github.io/SpineOpt.jl/latest/getting_started/setup_workflow/>`_
(takes you to SpineOpt documentation). See also :ref:`Tutorials` for more advanced use cases. For more information
on how to select a specific Python or Julia version, see :ref:`Setting up External Tools`).

.. note:: The *SpineOpt Plugin Toolbar* contains two predefined Tools that make use of SpineOpt.jl. **The SpineOpt
   Plugin is not a requirement to run SpineOpt.jl**, they are provided just for convenience and as examples to get
   you started quickly.
