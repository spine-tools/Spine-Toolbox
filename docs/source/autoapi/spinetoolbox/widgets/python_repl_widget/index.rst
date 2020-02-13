:mod:`spinetoolbox.widgets.python_repl_widget`
==============================================

.. py:module:: spinetoolbox.widgets.python_repl_widget

.. autoapi-nested-parse::

   Class for a custom SpineConsoleWidget to use as Python REPL.

   :author: P. Savolainen (VTT)
   :date:   14.3.2019



Module Contents
---------------

.. py:class:: PythonReplWidget(toolbox)

   Bases: :class:`spinetoolbox.widgets.spine_console_widget.SpineConsoleWidget`

   Python Repl Widget class.

   .. attribute:: toolbox

      App main window (QMainWindow) instance

      :type: ToolboxUI

   Class constructor.

   .. attribute:: name
      :annotation: = Python Console

      

   .. method:: connect_signals(self)


      Connect signals.


   .. method:: disconnect_signals(self)


      Disconnect signals. Needed before
      switching to another Python kernel.


   .. method:: python_kernel_name(self)


      Returns the name of the Python kernel specification
      and its display name according to the selected Python
      environment in Settings. Returns None if Python version
      cannot be determined.


   .. method:: setup_python_kernel(self)


      Context menu Start action handler.


   .. method:: launch_kernel(self, k_name, k_display_name)


      Check if selected kernel exists or if it needs to be set up before launching.


   .. method:: check_and_install_requirements(self)


      Prompts user to install IPython and ipykernel if they are missing.
      After installing the required packages, installs kernelspecs for the
      selected Python if they are missing.

      :returns: Boolean value depending on whether or not the user chooses to proceed.


   .. method:: is_package_installed(self, package_name)


      Checks if given package is installed to selected Python environment.

      :param package_name: Package name
      :type package_name: str

      :returns: True if installed, False if not
      :rtype: (bool)


   .. method:: start_package_install_process(self, package_name)


      Starts installing the given package using pip.

      :param package_name: Package name to install using pip
      :type package_name: str


   .. method:: handle_package_install_process_finished(self, retval)


      Handles installing package finished.

      :param retval: Process return value. 0: success, !0: failure
      :type retval: int


   .. method:: start_kernelspec_install_process(self)


      Install kernel specifications for the selected Python environment.


   .. method:: handle_kernelspec_install_process_finished(self, retval)


      Handles installing package finished.

      :param retval: Process return value. 0: success, !0: failure
      :type retval: int


   .. method:: start_python_kernel(self)


      Starts kernel manager and client and attaches
      the client to the Python Console.


   .. method:: wake_up(self)


      See base class.


   .. method:: handle_executing(self, code)


      Slot for handling the 'executing' signal. Signal is emitted
      when a user visible 'execute_request' has been submitted to the
      kernel from the FrontendWidget.

      :param code: Code to be executed (actually not 'str' but 'object')
      :type code: str


   .. method:: handle_executed(self, msg)


      Slot for handling the 'executed' signal. Signal is emitted
      when a user-visible 'execute_reply' has been received from the
      kernel and processed by the FrontendWidget.

      :param msg: Response message (actually not 'dict' but 'object')
      :type msg: dict


   .. method:: receive_iopub_msg(self, msg)


      Message received from the IOPUB channel.
      Note: We are only monitoring when the kernel has started
      successfully and ready for action here. Alternatively, this
      could be done in the Slot for the 'executed' signal. However,
      this Slot could come in handy at some point. See 'Messaging in
      Jupyter' for details:
      https://jupyter-client.readthedocs.io/en/latest/messaging.html

      :param msg: Received message from IOPUB channel
      :type msg: dict


   .. method:: shutdown_kernel(self, hush=False)


      Shut down Python kernel.


   .. method:: push_vars(self, var_name, var_value)


      Push a variable to Python Console session.
      Simply executes command 'var_name=var_value'.

      :param var_name: Variable name
      :type var_name: str
      :param var_value: Variable value
      :type var_value: object

      :returns: True if succeeded, False otherwise
      :rtype: (bool)


   .. method:: test_push_vars(self)


      QAction slot to test pushing variables to Python Console.


   .. method:: _context_menu_make(self, pos)


      Reimplemented to add custom actions.


   .. method:: dragEnterEvent(self, e)


      Don't accept project item drops.


   .. method:: _is_complete(self, source, interactive)
      :abstractmethod:


      See base class.



