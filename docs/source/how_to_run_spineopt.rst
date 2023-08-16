.. How to Set up SpineOpt.jl documentation

.. |execute| image:: ../../spinetoolbox/ui/resources/menu_icons/play-circle-solid.svg
             :width: 16

.. _How to Set up SpineOpt.jl:

*************************
How to Set up SpineOpt.jl
*************************

#. Install Julia (v1.6 or later) from `<https://julialang.org/downloads/>`_ if you don't have one.
   See latest **SpineOpt.jl** Julia compatibility information `here <https://github.com/spine-tools/SpineOpt.jl#spineoptjl>`_.

#. Start Spine Toolbox

#. Create a new project (**File -> New project...**)

#. Select **File -> Settings** from the main menu and open the *Tools* page.

#. Set a path to a Julia executable to the appropriate line edit (e.g. `C:/Julia-1.6.0/bin/julia.exe`).
   Your selections should look similar to this now.

   .. image:: img/settings_tools_default.png
      :align: center

#. *[Optional]* If you want to install and run SpineOpt in a specific Julia project environment (the place for
   `Project.toml` and `Manifest.toml`), you can set the path to the environment folder to the line edit just below the
   Julia executable (the one that says *Using Julia default project*).

#. Next, you need to install **SpineOpt.jl** package for the Julia you just selected for Spine Toolbox. You can do
   this manually by `following the instructions <https://github.com/spine-tools/SpineOpt.jl#installation>`_
   **or** you can install **SpineOpt.jl** by clicking the **Add/Update SpineOpt** button. After clicking the button,
   an install/upgrade Spineopt wizard appears. Click **Next** twice and finally **Install SpineOpt**.
   **Wait until the process has finished** and you are greeted with this screen.

   .. image:: img/spineopt_install_wizard_successful.png
      :align: center

   Close the wizard.

#. Click **Ok** to close the **Settings** window
#. Back in the main window, select **Plugins -> Install plugin…** from the menu
#. Select `SpineOpt` and click **Ok**. After a short while, a red **SpineOpt Plugin Toolbar** will appear in the main
   window.

Spine Toolbox and Julia are now correctly set up for running **SpineOpt.jl**. Next step is to
`Create a project workflow using SpineOpt.jl <https://spine-tools.github.io/SpineOpt.jl/latest/getting_started/setup_workflow/>`_
(takes you to SpineOpt documentation). See also `Tutorials
<https://spine-tools.github.io/SpineOpt.jl/latest/tutorial/simple_system/>`_ in SpineOpt documentation for more advanced
use cases. For more information on how to select a specific Python or Julia version, see :ref:`Setting up Consoles and External Tools`).

.. note:: The **SpineOpt Plugin Toolbar** contains an exporter specification as well as three predefined Tools that make
   use of SpineOpt.jl. **The SpineOpt Plugin is not a requirement to run SpineOpt.jl**, they are provided just for
   convenience and as examples to get you started quickly.
