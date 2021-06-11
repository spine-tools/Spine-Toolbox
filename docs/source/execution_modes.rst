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

You can execute Python or Julia Tools in the Jupyter Console or as in the shell. Gams Tools are only executed as
in the shell.

Python
------

Shell execution (default)
_________________________

On `Tools` page in `File->Settings...`, check the *Run Python Tools in a subprocess* radiobutton (release-0.6)
or uncheck the *Jupyter Console* check box (master). This is the default execution mode for Python Tools.

.. #. Start Spine Toolbox
   #. Create a project with a Tool and a Python Tool specification (See :ref:`Getting Started`)
   #. Go to the `Tools` page in `File->Settings...`
   #. Uncheck the `Use embedded Python Console` check box
   #. Press |play| to execute the project (See :ref:`Executing Projects`)
   #. Executing your Tool project item starts. You can see the output (stdout and stderr) in the
      Process Log.

Jupyter Console / Python Console execution
__________________________________________

If you want to use the embedded Python Console (Jupyter Console). Check the *Run Python Tools in embedded console*
radiobutton (release-0.6) or check the *Jupyter Console* check box (master). There is an extra step involved since
the Jupyter Console requires a couple of extra packages (`ipykernel` and its dependencies) to be
installed on the selected Python. In addition, kernel specifications for the selected Python need to be
installed beforehand. **Spine Toolbox can install these for you**, from the **Kernel Spec Editor** widget that
you can open from the `Tools` page in `File->Settings..` by clicking the `Kernel Spec Editor` button. In the Kernel
Spec Editor, give the spec a name and click `Make kernel specification` button.

.. note::
   You can install Python kernel specifications manually and Spine Toolbox will find them. You can select the kernel
   spec used in the Jupyter Console from the drop-down menu *Select Python kernel spec...*.

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
-----

Shell execution (default)
_________________________
On `Tools` page in `File->Settings...`, check the *Run Julia Tools in a subprocess* radiobutton (release-0.6)
or uncheck the *Jupyter Console* check box (master). This is the default execution mode for Julia Tools.

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

Jupyter Console / Julia Console execution
_________________________________________

Like the Python Console, Julia Console requires some extra setting up. The Julia Console requires a couple of
additional packages (`IJulia`, etc.) to be installed and built. **Spine Toolbox can set this up for you
automatically**. Just click the **Kernel spec Editor** button, give the spec a name and click
`Make kernel specification` button.

.. note::
   You can install Julia kernel specifications manually and Spine Toolbox will find them. You can select the kernel
   spec used in the Jupyter Console from the drop-down menu *Select Julia kernel spec...*.

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
