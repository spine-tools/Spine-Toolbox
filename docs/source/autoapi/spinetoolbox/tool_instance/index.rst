:mod:`spinetoolbox.tool_instance`
=================================

.. py:module:: spinetoolbox.tool_instance

.. autoapi-nested-parse::

   Contains ToolInstance class.

   :authors: P. Savolainen (VTT), E. Rinne (VTT)
   :date:   1.2.2018



Module Contents
---------------

.. py:class:: ToolInstance(tool_specification, basedir, settings, logger)

   Bases: :class:`PySide2.QtCore.QObject`

   Tool instance base class.

   :param tool_specification: the tool specification for this instance
   :type tool_specification: ToolSpecification
   :param basedir: the path to the directory where this instance should run
   :type basedir: str
   :param settings: Toolbox settings
   :type settings: QSettings
   :param logger: a logger instance
   :type logger: LoggerInterface

   .. attribute:: instance_finished
      

      Signal to emit when a Tool instance has finished processing


   .. method:: is_running(self)



   .. method:: terminate_instance(self)


      Terminates Tool instance execution.


   .. method:: remove(self)


      [Obsolete] Removes Tool instance files from work directory.


   .. method:: prepare(self, optional_input_files, input_database_urls, output_database_urls, tool_args)
      :abstractmethod:


      Prepares this instance for execution.

      Implement in subclasses to perform specific initialization.

      :param optional_input_files: list of tool's optional input files
      :type optional_input_files: list
      :param input_database_urls: a mapping from upstream Data Store name to database URL
      :type input_database_urls: dict
      :param output_database_urls: a mapping from downstream Data Store name to database URL
      :type output_database_urls: dict
      :param tool_args: Tool cmd line args
      :type tool_args: list


   .. method:: execute(self, **kwargs)
      :abstractmethod:


      Executes a prepared instance. Implement in subclasses.


   .. method:: handle_execution_finished(self, ret)
      :abstractmethod:


      Handles execution finished.

      :param ret:
      :type ret: int


   .. method:: append_cmdline_args(self, optional_input_files, input_database_urls, output_database_urls, tool_args)


      Appends Tool specification command line args into instance args list.

      :param optional_input_files: list of tool's optional input files
      :type optional_input_files: list
      :param input_database_urls: a mapping from upstream Data Store name to database URL
      :type input_database_urls: dict
      :param output_database_urls: a mapping from downstream Data Store name to database URL
      :type output_database_urls: dict
      :param tool_args: List of Tool cmd line args
      :type tool_args: list



.. py:class:: GAMSToolInstance

   Bases: :class:`spinetoolbox.tool_instance.ToolInstance`

   Class for GAMS Tool instances.

   .. method:: prepare(self, optional_input_files, input_database_urls, output_database_urls, tool_args)


      See base class.


   .. method:: execute(self, **kwargs)


      Executes a prepared instance.


   .. method:: handle_execution_finished(self, ret)


      Handles execution finished.

      :param ret:
      :type ret: int



.. py:class:: JuliaToolInstance(toolbox, tool_specification, basedir, settings, logger)

   Bases: :class:`spinetoolbox.tool_instance.ToolInstance`

   Class for Julia Tool instances.

   :param toolbox: QMainWindow instance
   :type toolbox: ToolboxUI
   :param tool_specification: the tool specification for this instance
   :type tool_specification: ToolSpecification
   :param basedir: the path to the directory where this instance should run
   :type basedir: str
   :param settings: Toolbox settings
   :type settings: QSettings
   :param logger: a logger instance
   :type logger: LoggerInterface

   .. method:: prepare(self, optional_input_files, input_database_urls, output_database_urls, tool_args)


      See base class.


   .. method:: execute(self, **kwargs)


      Executes a prepared instance.


   .. method:: handle_repl_execution_finished(self, ret)


      Handles repl-execution finished.

      :param ret: Tool specification process return value
      :type ret: int


   .. method:: handle_execution_finished(self, ret)


      Handles execution finished.

      :param ret: Tool specification process return value
      :type ret: int



.. py:class:: PythonToolInstance(toolbox, tool_specification, basedir, settings, logger)

   Bases: :class:`spinetoolbox.tool_instance.ToolInstance`

   Class for Python Tool instances.

   :param toolbox: QMainWindow instance
   :type toolbox: ToolboxUI
   :param tool_specification: the tool specification for this instance
   :type tool_specification: ToolSpecification
   :param basedir: the path to the directory where this instance should run
   :type basedir: str
   :param settings: Toolbox settings
   :type settings: QSettings
   :param logger: A logger instance
   :type logger: LoggerInterface

   .. method:: prepare(self, optional_input_files, input_database_urls, output_database_urls, tool_args)


      See base class.


   .. method:: execute(self, **kwargs)


      Executes a prepared instance.


   .. method:: handle_console_execution_finished(self, ret)


      Handles console-execution finished.

      :param ret: Tool specification process return value
      :type ret: int


   .. method:: handle_execution_finished(self, ret)


      Handles execution finished.

      :param ret: Tool specification process return value
      :type ret: int



.. py:class:: ExecutableToolInstance

   Bases: :class:`spinetoolbox.tool_instance.ToolInstance`

   Class for Executable Tool instances.

   .. method:: prepare(self, optional_input_files, input_database_urls, output_database_urls, tool_args)


      See base class.


   .. method:: execute(self, **kwargs)


      Executes a prepared instance.


   .. method:: handle_execution_finished(self, ret)


      Handles execution finished.

      :param ret: Tool specification process return value
      :type ret: int



