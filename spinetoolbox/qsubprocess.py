#############################################################################
# Copyright (C) 2017 - 2018 VTT Technical Research Centre of Finland
#
# This file is part of Spine Toolbox.
#
# Spine Toolbox is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#############################################################################

"""
Module to handle running tools in a QProcess.

:author: Pekka Savolainen <pekka.t.savolainen@vtt.fi>
:date:   1.2.2018
"""

from PySide2.QtCore import QObject, QProcess, Slot, Signal
import logging


class QSubProcess(QObject):
    """Class to handle starting, running, and finishing PySide2 QProcesses."""

    subprocess_finished_signal = Signal(int, name="subprocess_finished_signal")

    def __init__(self, ui, tool):
        """Class constructor.

        Args:
            ui (ToolboxUI): Instance of Main UI class.
            tool (ToolTemplate): Tool to run in sub-process.
        """
        super().__init__()
        self._ui = ui
        self._running_tool = tool
        self.process_failed = False
        self.process_failed_to_start = False
        self._user_stopped = False
        self._process = QProcess(self)

    # noinspection PyUnresolvedReferences
    def start_process(self, command, workdir=None):
        """Start the execution of a tool in a QProcess.

        Args:
            command: Run command
            workdir (str): Path to work directory
        """
        if workdir is not None:
            self._process.setWorkingDirectory(workdir)
        self._ui.msg.emit("*** Starting Tool <b>{0}</b> ***".format(self._running_tool.name))
        self._ui.msg.emit("<i>{0}</i>".format(command))
        self._process.started.connect(self.process_started)
        self._process.readyReadStandardOutput.connect(self.on_ready_stdout)
        self._process.readyReadStandardError.connect(self.on_ready_stderr)
        self._process.finished.connect(self.process_finished)
        self._process.error.connect(self.on_process_error)  # errorOccurred available in Qt 5.6
        self._process.stateChanged.connect(self.on_state_changed)
        self._process.start(command)
        if not self._process.waitForStarted(msecs=10000):  # This blocks until process starts or timeout happens
            self.process_failed = True
            self._process.deleteLater()
            self._process = None
            self.subprocess_finished_signal.emit(0)  # TODO: Check that this works

    @Slot(name="process_started")
    def process_started(self):
        """Run when subprocess has started."""
        self._ui.msg.emit("Subprocess started...")

    @Slot("QProcess::ProcessState", name="on_state_changed")
    def on_state_changed(self, new_state):
        """Runs when QProcess state changes.

        Args:
            new_state (QProcess::ProcessState): Process state number
        """
        if new_state == QProcess.Starting:
            logging.debug("QProcess is starting")
        elif new_state == QProcess.Running:
            logging.debug("QProcess is running")
        elif new_state == QProcess.NotRunning:
            logging.debug("QProcess is not running")
        else:
            logging.debug("QProcess unspecified state: {0}".format(new_state))

    @Slot("QProcess::ProcessError", name="'on_process_error")
    def on_process_error(self, process_error):
        """Run if there is an error in the running QProcess.

        Args:
            process_error (QProcess::ProcessError): Process error number
        """
        if process_error == QProcess.FailedToStart:
            self.process_failed_to_start = True
        elif process_error == QProcess.Timedout:
            logging.debug("QProcess timed out")
        elif process_error == QProcess.Crashed:
            logging.debug("QProcess crashed")
        elif process_error == QProcess.WriteError:
            logging.debug("QProcess WriteError")
        elif process_error == QProcess.ReadError:
            logging.debug("QProcess ReadError")
        elif process_error == QProcess.UnknownError:
            logging.debug("QProcess unknown error")
        else:
            logging.debug("QProcess Unspecified error: {0}".format(process_error))

    def terminate_process(self):
        """Shutdown simulation in a QProcess."""
        # self._ui.msg.emit("<br/>Stopping process nr. {0}".format(self._process.processId()))
        logging.debug("Terminating QProcess nr.{0}. ProcessState:{1} and ProcessError:{2}"
                      .format(self._process.processId(), self._process.state(), self._process.error()))
        self._user_stopped = True
        self.process_failed = True
        try:
            self._process.close()
        except Exception as ex:
            logging.exception("Exception in closing QProcess: {}".format(ex))

    @Slot(int, name="process_finished")
    def process_finished(self, exit_code):
        """Run when subprocess has finished.

        Args:
            exit_code (int): Return code from external program (only valid for normal exits)
        """
        # logging.debug("Error that occurred last: {0}".format(self._process.error()))
        exit_status = self._process.exitStatus()  # Normal or crash exit
        if exit_status == QProcess.CrashExit:
            logging.error("QProcess CrashExit")
            self._ui.msg_error("Subprocess crashed")
            self.process_failed = True
        elif exit_status == QProcess.NormalExit:
            self._ui.msg.emit("Subprocess finished")
            logging.debug("QProcess NormalExit")
        else:
            logging.error("Unknown exit from QProcess '{0}'".format(exit_status))
        # TODO: exit_code is not valid if QProcess exit status is CrashExit.
        if not exit_code == 0:
            self.process_failed = True
        if not self._user_stopped:
            out = str(self._process.readAllStandardOutput().data(), "utf-8")
            if out is not None:
                self._ui.msg_proc.emit(out.strip())
        else:
            self._ui.msg.emit("*** Terminating subprocess ***")
        # Delete QProcess
        self._process.deleteLater()
        self._process = None
        self.subprocess_finished_signal.emit(exit_code)

    @Slot(name="on_ready_stdout")
    def on_ready_stdout(self):
        """Emit data from stdout."""
        out = str(self._process.readAllStandardOutput().data(), "utf-8")
        self._ui.msg_proc.emit(out.strip())

    @Slot(name="on_ready_stderr")
    def on_ready_stderr(self):
        """Emit data from stderr."""
        out = str(self._process.readAllStandardError().data(), "utf-8")
        self._ui.msg_proc_error.emit(out.strip())
