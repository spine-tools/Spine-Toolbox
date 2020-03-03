######################################################################################################################
# Copyright (C) 2017-2020 Spine project consortium
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""
Classes to manage tool instance execution in various forms.

:author: P. Savolainen (VTT)
:date:   1.2.2018
"""

import logging
import json
from PySide2.QtCore import QObject, QProcess, Slot, Signal


class ExecutionManager(QObject):
    """Base class for all tool instance execution managers."""

    execution_finished = Signal(int)

    def __init__(self, logger):
        """Class constructor.

        Args:
            logger (LoggerInterface): a logger instance
        """
        super().__init__()
        self._logger = logger

    # noinspection PyUnresolvedReferences
    def start_execution(self, workdir=None):
        """Starts the execution.

        Args:
            workdir (str): Work directory
        """
        raise NotImplementedError()

    def stop_execution(self):
        """Stops the execution."""
        raise NotImplementedError()


class ConsoleExecutionManager(ExecutionManager):
    """Class to manage tool instance execution using a SpineConsoleWidget."""

    def __init__(self, console, commands, logger):
        """Class constructor.

        Args:
            console (SpineConsoleWidget): Console widget where execution happens
            commands (list): List of commands to execute in the console
            logger (LoggerInterface): a logger instance
        """
        super().__init__(logger)
        self._console = console
        self._commands = commands
        self._stopped = False

    def start_execution(self, workdir=None):
        """See base class."""
        self._console.ready_to_execute.connect(self._start_execution)
        self._console.execution_failed.connect(self.execution_finished)
        self._console.wake_up()

    @Slot()
    def _start_execution(self):
        """Starts execution."""
        self._logger.msg_warning.emit(f"\tExecution started. See <b>{self._console.name}</b> for messages.")
        self._console.ready_to_execute.disconnect(self._start_execution)
        self._console.ready_to_execute.connect(self._execute_next_command)
        self._execute_next_command()

    @Slot()
    def _execute_next_command(self):
        """Executes next command in the buffer."""
        if self._stopped:
            return
        try:
            command = self._commands.pop(0)
            self._console.execute(command)
        except IndexError:
            self.execution_finished.emit(0)

    def stop_execution(self):
        """See base class."""
        self._stopped = True
        self._console.interrupt()


class QProcessExecutionManager(ExecutionManager):
    """Class to manage tool instance execution using a PySide2 QProcess."""

    def __init__(self, logger, program=None, args=None, silent=False, semisilent=False):
        """Class constructor.

        Args:
            logger (LoggerInterface): a logger instance
            program (str): Path to program to run in the subprocess (e.g. julia.exe)
            args (list): List of argument for the program (e.g. path to script file)
            silent (bool): Whether or not to emit logger msg signals
        """
        super().__init__(logger)
        self._program = program
        self._args = args
        self._silent = silent  # Do not show Event Log nor Process Log messages
        self._semisilent = semisilent  # Do not show Event Log messages but show Process Log messages
        self.process_failed = False
        self.process_failed_to_start = False
        self._user_stopped = False
        self._process = QProcess(self)
        self.process_output = None  # stdout when running silent
        self.error_output = None  # stderr when running silent
        self.data_to_inject = None

    def program(self):
        """Program getter method."""
        return self._program

    def args(self):
        """Program argument getter method."""
        return self._args

    # noinspection PyUnresolvedReferences
    def start_execution(self, workdir=None):
        """Starts the execution of a command in a QProcess.

        Args:
            workdir (str): Work directory
        """
        if workdir is not None:
            self._process.setWorkingDirectory(workdir)
        self._process.started.connect(self.process_started)
        self._process.finished.connect(self.on_process_finished)
        if not self._silent and not self._semisilent:  # Loud
            self._process.readyReadStandardOutput.connect(self.on_ready_stdout)
            self._process.readyReadStandardError.connect(self.on_ready_stderr)
            self._process.error.connect(self.on_process_error)  # errorOccurred available in Qt 5.6
            self._process.stateChanged.connect(self.on_state_changed)
        elif self._semisilent:  # semi-silent
            self._process.readyReadStandardOutput.connect(self.on_ready_stdout)
            self._process.readyReadStandardError.connect(self.on_ready_stderr)
        self._process.start(self._program, self._args)
        if not self._process.waitForStarted(msecs=10000):  # This blocks until process starts or timeout happens
            self.process_failed = True
            self.process_failed_to_start = True
            self._process.deleteLater()
            self._process = None
            self.data_to_inject = None
            self.execution_finished.emit(-9998)
        if self.data_to_inject is not None:
            self.inject_data_to_write_channel()

    def inject_data_to_write_channel(self):
        """Writes data to process write channel and closes it afterwards."""
        self._process.write(json.dumps(self.data_to_inject).encode("utf-8"))
        self._process.write(b'\n')
        self._process.closeWriteChannel()

    def wait_for_process_finished(self, msecs=30000):
        """Wait for subprocess to finish.

        Return:
            True if process finished successfully, False otherwise
        """
        if not self._process:
            return False
        if self.process_failed or self.process_failed_to_start:
            return False
        if not self._process.waitForFinished(msecs):
            self.process_failed = True
            self._process.close()
            self._process = None
            return False
        return True

    @Slot()
    def process_started(self):
        """Run when subprocess has started."""

    @Slot("QProcess::ProcessState")
    def on_state_changed(self, new_state):
        """Runs when QProcess state changes.

        Args:
            new_state (QProcess::ProcessState): Process state number
        """
        if new_state == QProcess.Starting:
            self._logger.msg.emit("\tStarting program <b>{0}</b>".format(self._program))
            arg_str = " ".join(self._args)
            self._logger.msg.emit("\tArguments: <b>{0}</b>".format(arg_str))
        elif new_state == QProcess.Running:
            self._logger.msg_warning.emit("\tExecution is in progress. See Process Log for messages " "(stdout&stderr)")
        elif new_state == QProcess.NotRunning:
            # logging.debug("QProcess is not running")
            pass
        else:
            self._logger.msg_error.emit("Process is in an unspecified state")
            logging.error("QProcess unspecified state: %s", new_state)

    @Slot("QProcess::ProcessError")
    def on_process_error(self, process_error):
        """Run if there is an error in the running QProcess.

        Args:
            process_error (QProcess::ProcessError): Process error number
        """
        if process_error == QProcess.FailedToStart:
            self.process_failed = True
            self.process_failed_to_start = True
        elif process_error == QProcess.Timedout:
            self.process_failed = True
            self._logger.msg_error.emit("Timed out")
        elif process_error == QProcess.Crashed:
            self.process_failed = True
            if not self._user_stopped:
                self._logger.msg_error.emit("Process crashed")
        elif process_error == QProcess.WriteError:
            self._logger.msg_error.emit("Process WriteError")
        elif process_error == QProcess.ReadError:
            self._logger.msg_error.emit("Process ReadError")
        elif process_error == QProcess.UnknownError:
            self._logger.msg_error.emit("Unknown error in process")
        else:
            self._logger.msg_error.emit("Unspecified error in process: {0}".format(process_error))

    def stop_execution(self):
        """See base class."""
        self._logger.msg_error.emit("Terminating process")
        self._user_stopped = True
        self.process_failed = True
        if not self._process:
            return
        try:
            self._process.terminate()
        except Exception as ex:  # pylint: disable=broad-except
            self._logger.msg_error.emit("[{0}] exception when terminating process".format(ex))
            logging.exception("Exception in closing QProcess: %s", ex)
        finally:
            self._process.deleteLater()
            self._process = None
            self.data_to_inject = None

    @Slot(int, "QProcess::ExitStatus")
    def on_process_finished(self, exit_code, exit_status):
        """Runs when subprocess has finished.

        Args:
            exit_code (int): Return code from external program (only valid for normal exits)
        """
        # logging.debug("Error that occurred last: {0}".format(self._process.error()))
        if not self._process:
            return
        if exit_status == QProcess.CrashExit:
            if not self._silent:
                self._logger.msg_error.emit("\tProcess crashed")
            exit_code = -1
        elif exit_status == QProcess.NormalExit:
            pass
        else:
            if not self._silent:
                self._logger.msg_error.emit("Unknown QProcess exit status [{0}]".format(exit_status))
            exit_code = -1
        if not exit_code == 0:
            self.process_failed = True
        if not self._user_stopped:
            out = str(self._process.readAllStandardOutput().data(), "utf-8", errors="replace")
            errout = str(self._process.readAllStandardError().data(), "utf-8", errors="replace")
            if out is not None:
                if not self._silent:
                    self._logger.msg_proc.emit(out.strip())
                else:
                    self.process_output = out.strip()
                    self.error_output = errout.strip()
        else:
            self._logger.msg.emit("*** Terminating process ***")
        # Delete QProcess
        self._process.deleteLater()
        self._process = None
        self.data_to_inject = None
        self.execution_finished.emit(exit_code)

    @Slot()
    def on_ready_stdout(self):
        """Emit data from stdout."""
        if not self._process:
            return
        out = str(self._process.readAllStandardOutput().data(), "utf-8", errors="replace")
        self._logger.msg_proc.emit(out.strip())

    @Slot()
    def on_ready_stderr(self):
        """Emit data from stderr."""
        if not self._process:
            return
        err = str(self._process.readAllStandardError().data(), "utf-8", errors="replace")
        self._logger.msg_proc_error.emit(err.strip())
