:mod:`spinetoolbox.execution_managers`
======================================

.. py:module:: spinetoolbox.execution_managers

.. autoapi-nested-parse::

   Classes to manage tool instance execution in various forms.

   :author: P. Savolainen (VTT)
   :date:   1.2.2018



Module Contents
---------------

.. py:class:: ExecutionManager(logger)

   Bases: :class:`PySide2.QtCore.QObject`

   Base class for all tool instance execution managers.

   Class constructor.

   :param logger: a logger instance
   :type logger: LoggerInterface

   .. attribute:: execution_finished
      

      

   .. method:: start_execution(self, workdir=None)
      :abstractmethod:


      Starts the execution.

      :param workdir: Work directory
      :type workdir: str


   .. method:: stop_execution(self)
      :abstractmethod:


      Stops the execution.



.. py:class:: ConsoleExecutionManager(console, commands, logger)

   Bases: :class:`spinetoolbox.execution_managers.ExecutionManager`

   Class to manage tool instance execution using a SpineConsoleWidget.

   Class constructor.

   :param console: Console widget where execution happens
   :type console: SpineConsoleWidget
   :param commands: List of commands to execute in the console
   :type commands: list
   :param logger: a logger instance
   :type logger: LoggerInterface

   .. method:: start_execution(self, workdir=None)


      See base class.


   .. method:: _start_execution(self)


      Starts execution.


   .. method:: _execute_next_command(self)


      Executes next command in the buffer.


   .. method:: stop_execution(self)


      See base class.



.. py:class:: QProcessExecutionManager(logger, program=None, args=None, silent=False, semisilent=False)

   Bases: :class:`spinetoolbox.execution_managers.ExecutionManager`

   Class to manage tool instance execution using a PySide2 QProcess.

   Class constructor.

   :param logger: a logger instance
   :type logger: LoggerInterface
   :param program: Path to program to run in the subprocess (e.g. julia.exe)
   :type program: str
   :param args: List of argument for the program (e.g. path to script file)
   :type args: list
   :param silent: Whether or not to emit logger msg signals
   :type silent: bool

   .. method:: program(self)


      Program getter method.


   .. method:: args(self)


      Program argument getter method.


   .. method:: start_execution(self, workdir=None)


      Starts the execution of a command in a QProcess.

      :param workdir: Work directory
      :type workdir: str


   .. method:: wait_for_process_finished(self, msecs=30000)


      Wait for subprocess to finish.

      :returns: True if process finished successfully, False otherwise


   .. method:: process_started(self)


      Run when subprocess has started.


   .. method:: on_state_changed(self, new_state)


      Runs when QProcess state changes.

      :param new_state: Process state number
      :type new_state: QProcess::ProcessState


   .. method:: on_process_error(self, process_error)


      Run if there is an error in the running QProcess.

      :param process_error: Process error number
      :type process_error: QProcess::ProcessError


   .. method:: stop_execution(self)


      See base class.


   .. method:: on_process_finished(self, exit_code)


      Runs when subprocess has finished.

      :param exit_code: Return code from external program (only valid for normal exits)
      :type exit_code: int


   .. method:: on_ready_stdout(self)


      Emit data from stdout.


   .. method:: on_ready_stderr(self)


      Emit data from stderr.



