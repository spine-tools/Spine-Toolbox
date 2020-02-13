:mod:`spinetoolbox.widgets.julia_repl_widget`
=============================================

.. py:module:: spinetoolbox.widgets.julia_repl_widget

.. autoapi-nested-parse::

   Class for a custom SpineConsoleWidget to use as julia REPL.

   :author: M. Marin (KTH)
   :date:   22.5.2018



Module Contents
---------------

.. py:class:: CustomQtKernelManager

   Bases: :class:`qtconsole.manager.QtKernelManager`

   A QtKernelManager with a custom restarter, and a means to override the --project argument.

   .. attribute:: kernel_left_dead
      

      

   .. attribute:: project_path
      

      

   .. method:: kernel_spec(self)
      :property:



   .. method:: override_project_arg(self)



   .. method:: start_restarter(self)


      Starts a restarter with custom time to dead and restart limit.


   .. method:: _handle_kernel_left_dead(self)




.. py:class:: JuliaREPLWidget(toolbox)

   Bases: :class:`spinetoolbox.widgets.spine_console_widget.SpineConsoleWidget`

   Class for a custom SpineConsoleWidget.


   :param toolbox: QMainWindow instance
   :type toolbox: ToolboxUI

   .. attribute:: name
      :annotation: = Julia Console

      

   .. method:: julia_kernel_name(self)


      Returns the name of the julia kernel specification according to the
      julia executable selected in settings. Returns None if julia version
      cannot be determined.

      :returns: str, NoneType


   .. method:: start_jupyter_kernel(self)


      Starts a Julia Jupyter kernel if available.


   .. method:: _do_start_jupyter_kernel(self, kernel_name=None)


      Starts a Jupyter kernel with the specified name.

      :param kernel_name:
      :type kernel_name: str, optional


   .. method:: handle_repl_failed_to_start(self)


      Tries using IJulia.

      :returns: True, False, or None if unable to determine.
      :rtype: (bool, NoneType)


   .. method:: _try_installing_ijulia(self)


      Prompts user to install IJulia.


   .. method:: _do_try_installing_ijulia(self)



   .. method:: _try_rebuilding_ijulia(self)



   .. method:: restart_jupyter_kernel(self)


      Restarts the julia jupyter kernel if it's already started.
      Starts a new kernel if none started or if the julia version has changed in Settings.


   .. method:: setup_client(self)



   .. method:: _handle_kernel_restarted(self, died=True)


      Called when the kernel is restarted, i.e., when time to dead has elapsed.


   .. method:: _handle_kernel_left_dead(self)


      Called when the kernel is finally declared dead, i.e., the restart limit has been reached.


   .. method:: handle_ijulia_installation_finished(self, ret)


      Runs when IJulia installation process finishes


   .. method:: handle_ijulia_rebuild_finished(self, ret)


      Runs when IJulia rebuild process finishes


   .. method:: handle_ijulia_process_finished(self, ret, process)


      Checks whether or not the IJulia process finished successfully.


   .. method:: _handle_execute_reply(self, msg)



   .. method:: _handle_status(self, msg)


      Handles status message.


   .. method:: _handle_error(self, msg)


      Handle error messages.


   .. method:: wake_up(self)


      See base class.


   .. method:: shutdown_jupyter_kernel(self)


      Shut down the jupyter kernel.


   .. method:: _context_menu_make(self, pos)


      Reimplemented to add an action for (re)start REPL action.


   .. method:: enterEvent(self, event)


      Set busy cursor during REPL (re)starts.


   .. method:: dragEnterEvent(self, e)


      Don't accept drops from Add Item Toolbar.


   .. method:: copy_input(self)


      Copy only input.


   .. method:: _is_complete(self, source, interactive)
      :abstractmethod:


      See base class.



