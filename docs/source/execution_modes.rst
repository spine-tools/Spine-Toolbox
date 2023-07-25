.. How to set up shell or Jupyter Console execution model.
   Created 4.6.2021

.. |browse| image:: ../../spinetoolbox/ui/resources/menu_icons/folder-open-solid.svg
            :width: 16
.. |play| image:: ../../spinetoolbox/ui/resources/menu_icons/play-circle-solid.svg
            :width: 16
.. |stop| image:: ../../spinetoolbox/ui/resources/menu_icons/stop-circle-regular.svg
            :width: 16

.. _Execution Modes:

***************
Execution Modes
***************

Python and Julia Tools can be executed in either an embedded basic console or a Jupyter Console. GAMS Tools
are only executed in the shell. Executable tools are a shell or by running the executable file straight.

Python
******

Under the **Tools** page in **File -> Settings...**, you can set the default console for new Python Tool specifications
as either a Basic Console or a Jupyter Console. In the Tool Specification Editor, Tool specification specific selections
can be made overriding the default settings.

Basic Console
-------------

If Basic Console is selected (it is by default) Tools are executed in the **Console** dock widget on a basic console.
You can set the default Python interpreter in the settings and item specific interpreters in the
Tool's specification editor.

Jupyter Console
---------------
Jupyter Console will also appear in the **Console** dock widget.
If you want to use a Jupyter Console as the default, check the *Jupyter Console* check box.
There is an extra step involved since
the Jupyter Console requires a couple of extra packages (*ipykernel* and its dependencies) to be
installed on the selected Python. In addition, kernel specifications for the selected Python needs to be
installed beforehand. **Spine Toolbox can install these for you**, from the **Python Kernel Specification Creator** widget that
you can open from the **Tools** page in **File -> Settings...** by clicking the **Make Python Kernel** button.

.. note::
   You can install Python kernel specifications manually and Spine Toolbox will find them. You can select the kernel
   spec used in the Jupyter Console from the drop-down menu *Select Python kernel...*.

.. 1. Go to `<https://www.python.org/downloads/>`_ and download the Python you want
   2. Run the Python installer and follow instructions
   3. Either let the installer put Python in your PATH or memorize the path where you installed it
      (e.g. `C:\\Python38`)
   4. Start Spine Toolbox
   5. Go to File -> Settings (or press F1) and click the Tools tab open
   6. If the installed Python is now in your PATH, you can leave the Python interpreter line edit blank.
      Or you can set the Python interpreter explicitly by setting it to e.g. `C:\\Python38\\python.exe`
      by using the |browse| button.
   7. Check the `Use embedded Python Console` check box
   8. Create a project with a Tool and a Python Tool specification (See :ref:`Getting Started`)
   9. Press play to execute the project (See :ref:`Executing Projects`)
   10. You will see a question box

.. .. image:: img/ipykernel_missing.png
      :align: center

.. When you click on the *Install ipykernel* button, you can see the progress of the
   operation in Process Log. The following packages will be installed on your selected Python.::

..    backcall, colorama, decorator, ipykernel, ipython, ipython-genutils, jedi, jupyter-client,
      jupyter-core, parso, pickleshare, prompt-toolkit, pygments, python-dateutil, pywin32, pyzmq, six,
      tornado, traitlets, wcwidth

.. When this operation finishes successfully, you will see another guestion box.

.. .. image:: img/kernel_specs_missing.png
      :align: center

.. Clicking on *Install specifications* button starts installing the kernel specs for the selected Python.
   On the tested system, this creates a new kernel into directory
   `C:\\Users\\ttepsa\\AppData\\Roaming\\jupyter\\kernels\\Python-3.8`, which contains the `kernel.json` file
   required by the embedded Python Console (which is actually a jupyter qtconsole)

.. 11. After the kernel specs have been installed, executing your Tool project item starts in the
      Python Console immediately. You can see the executed command and the Tool output in the Python
      Console.

.. .. note::
      If you want to set up your Python environment ready for Python Console manually, the following
      commands are executed by Spine Toolbox under the hood

..   This installs all required packages::

..      python -m pip install ipykernel

..   And this installs the kernel specifications::

..      python -m ipykernel install --user --name python-3.8 --display-name Python3.8


Julia
*****

As with Python, default console type can be selected in the settings and Julia kernels can also be created by pressing
**Make Julia Kernel** -button. In addition a default project can be selected for Julia Tool specifications.

Basic Console
-------------
On **Tools** page in **File -> Settings...**, check the **Basic Console** radiobutton.
This is the default execution mode for Julia Tools.

.. 1. Go to `<https://julialang.org/downloads/>`_ and download the Julia you want
   2. Run the Julia installer and follow instructions
   3. Either let the installer put Julia in your PATH or memorize the path where you installed it
      (e.g. `C:\\Julia-1.2.0`)
   4. Start Spine Toolbox
   5. Go to File -> Settings (or press F1) and click the Tools tab open
   6. If the installed Julia is now in your PATH, you can leave the Julia executable line edit blank.
      Or you can set the Julia executable explicitly by setting it to e.g. `C:\\Julia.1.2.0\\bin\\julia.exe`
      by using the |browse| button.
   7. Uncheck the `Use embedded Julia Console` check box
   8. Create a project with a Tool and a Julia Tool specification (See :ref:`Getting Started`)
   9. Press |play| to execute the project (See :ref:`Executing Projects`)
   10. Executing your Tool project item starts. You can see the output (stdout and stderr) in the
      Process Log.

Jupyter Console
---------------

Like the Python Console, the Jupyter Console with Julia requires some extra setting up. A couple of
additional packages (`IJulia`, etc.) are required to be installed and built. **Spine Toolbox can set this up for you
automatically**. Just click the **Make Julia Kernel** button after selecting the **Jupyter Console** -radiobutton.

.. note::
   You can install Julia kernel specifications manually and Spine Toolbox will find them. You can select the kernel
   spec used in the Jupyter Console from the drop-down menu *Select Julia kernel...*.

.. 1. Go to `<https://julialang.org/downloads/>`_ and download the Julia you want
   2. Run the Julia installer and follow instructions
   3. Either let the installer put Julia in your PATH or memorize the path where you installed it
      (e.g. `C:\\Julia-1.2.0`)
   4. Start Spine Toolbox
   5. Go to File -> Settings (or press F1) and click the Tools tab open
   6. If the installed Julia is now in your PATH, you can leave the Julia executable line edit blank.
      Or you can set the Julia executable explicitly by setting it to e.g. `C:\\Julia.1.2.0\\bin\\julia.exe`
      by using the |browse| button.
   7. Check the `Use embedded Julia Console` check box
   8. Create a project with a Tool and a Julia Tool specification (See :ref:`Getting Started`)
   9. Press |play| to execute the project (See :ref:`Executing Projects`)
   10. You will see a question box

.. .. image:: img/ijulia_missing.png
      :align: center

.. When you click on the *Allow* button, installing IJulia starts and you can see the progress of the
   operation in Process Log. **This may take a few minutes**.

.. When you see the these messages in the Event Log, the Julia Console is ready to be used.::

..    IJulia installation successful.
      *** Starting Julia Console ***

.. 11. After the installation has finished, executing your Julia Tool project item starts in the
      Julia Console immediately. You can see the executed command and the Tool output in the Julia
      Console. If nothing seems to be happening in the Julia Console. Just click |Stop| button and
      then try executing the project again by clicking the |play| button.

Executable
**********

With executable Tool types there are two ways to run the executable file: using a shell or without one.

Using a shell
-------------

To run an executable with a shell you need to select a shell out of the three available options that is
appropriate for the operating system you are running Spine Toolbox on. Then you can write a command that
runs the executable with the arguments that it needs into the *Command* textbox just like you would on a
normal shell.

Without a shell
---------------

To run an executable file without a shell you can either select the executable file as the main program
file of the Tool and write the possible arguments into *Command line arguments* or select *no shell* and
write the filepath of the executable file followed by it's arguments into the *Command* textbox.
Either way the file is executed independent of a shell and with the provided arguments.
