:mod:`spinetoolbox.widgets.spine_console_widget`
================================================

.. py:module:: spinetoolbox.widgets.spine_console_widget

.. autoapi-nested-parse::

   Class for a custom RichJupyterWidget that can run tool instances.

   :authors: M. Marin (KTH)
   :date:   22.10.2019



Module Contents
---------------

.. py:class:: SpineConsoleWidget(toolbox)

   Bases: :class:`qtconsole.rich_jupyter_widget.RichJupyterWidget`

   Base class for all console widgets that can run tool instances.

   :param toolbox: QMainWindow instance
   :type toolbox: ToolboxUI

   .. attribute:: ready_to_execute
      

      

   .. attribute:: execution_failed
      

      

   .. attribute:: name
      :annotation: = Unnamed console

      

   .. method:: wake_up(self)
      :abstractmethod:


      Wakes up the console in preparation for execution.

      Subclasses need to emit either ready_to_execute or execution_failed as a consequence of calling
      this function.


   .. method:: interrupt(self)


      Sends interrupt signal to kernel.



