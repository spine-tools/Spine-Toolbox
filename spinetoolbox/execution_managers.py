######################################################################################################################
# Copyright (C) 2017-2022 Spine project consortium
# Copyright Spine Toolbox contributors
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""Classes to manage tool instance execution in various forms."""
import logging
from PySide6.QtCore import QObject, QProcess, Slot, Signal


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


class QProcessExecutionManager(ExecutionManager):
    """Class to manage tool instance execution using a PySide6 QProcess."""

    def __init__(self, logger, program="", args=None, silent=False, semisilent=False):
        """Class constructor.

        Args:
            logger (LoggerInterface): a logger instance
            program (str): Path to program to run in the subprocess (e.g. julia.exe)
            args (list, optional): List of argument for the program (e.g. path to script file)
            silent (bool): Whether or not to emit logger msg signals
            semisilent (bool): If True, show Process Log messages
        """
        super().__init__(logger)
        self._program = program
        self._args = args if args is not None else []
        self._silent = silent  # Do not show Event Log nor Process Log messages
        self._semisilent = semisilent  # Do not show Event Log messages but show Process Log messages
        self.process_failed = False
        self.process_failed_to_start = False
        self.user_stopped = False
        self._process = QProcess(self)
        self.process_output = None  # stdout when running silent
        self.process_error = None  # stderr when running silent
        self._out_chunks = []
        self._err_chunks = []

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
            workdir (str, optional): Work directory
        """
        if workdir is not None:
            self._process.setWorkingDirectory(workdir)
        self._process.started.connect(self.process_started)
        self._process.finished.connect(self.on_process_finished)
        if not self._silent and not self._semisilent:  # Loud
            self._process.readyReadStandardOutput.connect(self.on_ready_stdout)
            self._process.readyReadStandardError.connect(self.on_ready_stderr)
            self._process.errorOccurred.connect(self.on_process_error)
            self._process.stateChanged.connect(self.on_state_changed)
        elif self._semisilent:  # semi-silent
            self._process.readyReadStandardOutput.connect(self.on_ready_stdout)
            self._process.readyReadStandardError.connect(self.on_ready_stderr)
        self._process.start(self._program, self._args)
        if self._process is not None and not self._process.waitForStarted(msecs=10000):
            self.process_failed = True
            self.process_failed_to_start = True
            self._process.deleteLater()
            self._process = None
            self.execution_finished.emit(-9998)

    def wait_for_process_finished(self, msecs=30000):
        """Wait for subprocess to finish.

        Args:
            msecs (int): Timeout in milliseconds

        Return:
            True if process finished successfully, False otherwise
        """
        if self._process is None:
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

    @Slot(int)
    def on_state_changed(self, new_state):
        """Runs when QProcess state changes.

        Args:
            new_state (int): Process state number (``QProcess::ProcessState``)
        """
        if new_state == QProcess.Starting:
            self._logger.msg.emit("\tStarting program <b>{0}</b>".format(self._program))
            arg_str = " ".join(self._args)
            self._logger.msg.emit("\tArguments: <b>{0}</b>".format(arg_str))
        elif new_state == QProcess.Running:
            self._logger.msg_warning.emit("\tExecution in progress...")
        elif new_state == QProcess.NotRunning:
            # logging.debug("Process is not running")
            pass
        else:
            self._logger.msg_error.emit("Process is in an unspecified state")
            logging.error("QProcess unspecified state: %s", new_state)

    @Slot(int)
    def on_process_error(self, process_error):
        """Runs if there is an error in the running QProcess.

        Args:
            process_error (int): Process error number (``QProcess::ProcessError``)
        """
        if process_error == QProcess.FailedToStart:
            self.process_failed = True
            self.process_failed_to_start = True
            self._logger.msg_error.emit("Process failed to start")
        elif process_error == QProcess.Timedout:
            self.process_failed = True
            self._logger.msg_error.emit("Timed out")
        elif process_error == QProcess.Crashed:
            self.process_failed = True
            if not self.user_stopped:
                self._logger.msg_error.emit("Process crashed")
        elif process_error == QProcess.WriteError:
            self._logger.msg_error.emit("Process WriteError")
        elif process_error == QProcess.ReadError:
            self._logger.msg_error.emit("Process ReadError")
        elif process_error == QProcess.UnknownError:
            self._logger.msg_error.emit("Unknown error in process")
        else:
            self._logger.msg_error.emit("Unspecified error in process: {0}".format(process_error))
        self.teardown_process()

    def teardown_process(self):
        """Tears down the QProcess in case a QProcess.ProcessError occurred.
        Emits execution_finished signal."""
        if not self._process:
            pass
        else:
            out = str(self._process.readAllStandardOutput().data(), "utf-8", errors="replace")
            errout = str(self._process.readAllStandardError().data(), "utf-8", errors="replace")
            if out is not None:
                self._logger.msg_proc.emit(out.strip())
            if errout is not None:
                self._logger.msg_proc.emit(errout.strip())
            self._process.deleteLater()
            self._process = None
        self.execution_finished.emit(-9998)

    def stop_execution(self):
        """See base class."""
        self.user_stopped = True
        self.process_failed = True
        if not self._process:
            return
        try:
            self._process.kill()
            if not self._process.waitForFinished(5000):
                self._process.finished.emit(-1, -1)
                self._process.deleteLater()
        except Exception as ex:  # pylint: disable=broad-except
            self._logger.msg_error.emit("[{0}] exception when terminating process".format(ex))
            logging.exception("Exception in closing QProcess: %s", ex)
        finally:
            self._process = None

    @Slot(int, int)
    def on_process_finished(self, exit_code, exit_status):
        """Runs when subprocess has finished.

        Args:
            exit_code (int): Return code from external program (only valid for normal exits)
            exit_status (int): Crash or normal exit (``QProcess::ExitStatus``)
        """
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
        if exit_code != 0:
            self.process_failed = True
        if not self.user_stopped:
            out = str(self._process.readAllStandardOutput().data(), "utf-8", errors="replace")
            errout = str(self._process.readAllStandardError().data(), "utf-8", errors="replace")
            if out is not None:
                if not self._silent:
                    self._logger.msg_proc.emit(out.strip())
                else:
                    self.process_output = out.strip()
                    self.process_error = errout.strip()
        else:
            self._logger.msg.emit("*** Terminating process ***")
        # Delete QProcess
        self._process.deleteLater()
        self._process = None
        self.execution_finished.emit(exit_code)

    @Slot()
    def on_ready_stdout(self):
        """Emit data from stdout."""
        if not self._process:
            return
        self._process.setReadChannel(QProcess.StandardOutput)
        chunk = self._process.readLine().data()
        self._out_chunks.append(chunk)
        if not chunk.endswith(b"\n"):
            return
        line = b"".join(self._out_chunks)
        line = str(line, "utf-8", errors="replace").strip()
        self._logger.msg_proc.emit(line)
        self._out_chunks.clear()

    @Slot()
    def on_ready_stderr(self):
        """Emit data from stderr."""
        if not self._process:
            return
        self._process.setReadChannel(QProcess.StandardError)
        chunk = self._process.readLine().data()
        self._err_chunks.append(chunk)
        if not chunk.endswith(b"\n"):
            return
        line = b"".join(self._err_chunks)
        line = str(line, "utf-8", errors="replace").strip()
        self._logger.msg_proc_error.emit(line)
        self._err_chunks.clear()
