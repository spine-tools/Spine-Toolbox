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
Class for a custom SpineConsoleWidget to use as Python REPL.

:author: P. Savolainen (VTT)
:date:   14.3.2019
"""

import os.path
import subprocess
from PySide2.QtCore import Qt, Slot
from PySide2.QtWidgets import QAction, QMessageBox
from qtconsole.manager import QtKernelManager
from jupyter_client.kernelspec import find_kernel_specs, get_kernel_spec, NoSuchKernel
from .toolbars import DraggableWidget
from ..helpers import busy_effect
from ..config import PYTHON_EXECUTABLE
from ..execution_managers import QProcessExecutionManager
from .spine_console_widget import SpineConsoleWidget


class PythonReplWidget(SpineConsoleWidget):
    """Python Repl Widget class.

    Attributes:
        toolbox (ToolboxUI): App main window (QMainWindow) instance
    """

    name = "Python Console"

    def __init__(self, toolbox):
        """Class constructor."""
        super().__init__(toolbox)
        self._kernel_starting = False  # Warning: Do not use self._starting (protected class variable in JupyterWidget)
        self.kernel_name = None
        self.kernel_display_name = ""
        self.kernel_manager = None
        self.kernel_client = None
        self.python_cmd = None  # Contains the path to selected python executable (i.e. pythondir/python.exe on Win.)
        self.install_proc_exec_mngr = None  # QSubProcess instance for installing required packages
        self.may_need_restart = True  # Has the user changed the Python environment in Settings
        self.normal_cursor = self._control.viewport().cursor()
        # QActions
        self.start_action = QAction("Start", self)
        self.start_action.triggered.connect(lambda checked: self.setup_python_kernel())
        self.restart_action = QAction("Restart", self)
        self.restart_action.triggered.connect(lambda a: self.restart_kernel("Do you want to restart the kernel?"))

    def connect_signals(self):
        """Connect signals."""
        self.executing.connect(self.handle_executing)  # Signal defined in FrontEndWidget class
        self.executed.connect(self.handle_executed)  # Signal defined in FrontEndWidget class
        self.kernel_client.iopub_channel.message_received.connect(self.receive_iopub_msg)

    def disconnect_signals(self):
        """Disconnect signals. Needed before
        switching to another Python kernel."""
        self.executing.disconnect(self.handle_executing)
        self.executed.disconnect(self.handle_executed)
        self.kernel_client.iopub_channel.message_received.disconnect(self.receive_iopub_msg)

    @busy_effect
    def python_kernel_name(self):
        """Returns the name of the Python kernel specification
        and its display name according to the selected Python
        environment in Settings. Returns None if Python version
        cannot be determined."""
        if not self.may_need_restart:
            return self.kernel_name, self.kernel_display_name
        python_path = self._toolbox.qsettings().value("appSettings/pythonPath", defaultValue="")
        if python_path:
            self.python_cmd = python_path
        else:
            self.python_cmd = PYTHON_EXECUTABLE
        program = str(self.python_cmd)
        args = list()
        args.append("-V")
        proc_exec_mngr = QProcessExecutionManager(self._toolbox, program, args, silent=True)
        proc_exec_mngr.start_execution()
        if not proc_exec_mngr.wait_for_process_finished(msecs=5000):
            self._toolbox.msg_error.emit(
                "Couldn't determine Python version. Please check " "the <b>Python interpreter</b> option in Settings."
            )
            return None
        python_version_str = proc_exec_mngr.process_output
        if not python_version_str:
            # The version str might be in stderr instead of stdout (happens at least with Python 2.7.14)
            python_version_str = proc_exec_mngr.error_output
        p_v_list = python_version_str.split()
        ver = p_v_list[1]  # version e.g. 3.7.1
        kernel_name = "python-" + ver[:3]
        kernel_display_name = "Python-" + ver
        self.may_need_restart = False
        return kernel_name, kernel_display_name

    @Slot()
    def setup_python_kernel(self):
        """Context menu Start action handler."""
        k_tuple = self.python_kernel_name()
        if not k_tuple:
            return
        self.launch_kernel(k_tuple[0], k_tuple[1])

    def launch_kernel(self, k_name, k_display_name):
        """Check if selected kernel exists or if it needs to be set up before launching."""
        if self.kernel_manager:
            if self.kernel_name == k_name:
                # Happens when context-menu 'Start' item is clicked while the kernel is already running
                self._toolbox.msg.emit("Kernel {0} already running in Python Console".format(self.kernel_name))
                return
            self._toolbox.msg.emit("*** Restarting Python Console ***")
            self._toolbox.msg.emit("\tShutting down IPython kernel <b>{0}</b>".format(self.kernel_name))
            self.shutdown_kernel(hush=True)
        else:
            self._toolbox.msg.emit("*** Starting Python Console ***")
        self.kernel_name = k_name
        self.kernel_display_name = k_display_name
        self.check_and_install_requirements()

    def check_and_install_requirements(self):
        """Prompts user to install IPython and ipykernel if they are missing.
        After installing the required packages, installs kernelspecs for the
        selected Python if they are missing.

        Returns:
            Boolean value depending on whether or not the user chooses to proceed.
        """
        if not self.is_package_installed("ipykernel"):
            message = (
                "Python Console requires package <b>ipykernel</b>." "<p>Do you want to install the package now?</p>"
            )
            message_box = QMessageBox(
                QMessageBox.Question,
                "ipykernel Missing",
                message,
                QMessageBox.Ok | QMessageBox.Cancel,
                parent=self._toolbox,
            )
            message_box.button(QMessageBox.Ok).setText("Install ipykernel")
            answer = message_box.exec_()
            if answer == QMessageBox.Cancel:
                self._control.viewport().setCursor(self.normal_cursor)
                return False
            self._toolbox.msg.emit("*** Installing ipykernel ***")
            self.start_package_install_process("ipykernel")
            return True
        # Install kernelspecs for self.kernel_name if not already present
        kernel_specs = find_kernel_specs()
        spec_exists = self.kernel_name in kernel_specs
        executable_valid = False
        if spec_exists:
            spec = get_kernel_spec(self.kernel_name)
            executable_valid = os.path.exists(spec.argv[0])
        if not spec_exists or not executable_valid:
            message = (
                "IPython kernel specifications for the selected environment are missing. "
                "<p>Do you want to install kernel <b>{0}</b> specifications now?</p>".format(self.kernel_name)
            )
            message_box = QMessageBox(
                QMessageBox.Question,
                "Kernel Specs Missing",
                message,
                QMessageBox.Ok | QMessageBox.Cancel,
                parent=self._toolbox,
            )
            message_box.button(QMessageBox.Ok).setText("Install specifications")
            answer = message_box.exec_()
            if answer == QMessageBox.Cancel:
                self._control.viewport().setCursor(self.normal_cursor)
                return False
            self._toolbox.msg.emit("*** Installing IPython kernel <b>{0}</b> specs ***".format(self.kernel_name))
            self.start_kernelspec_install_process()
            # New specs installed, update the variable
            if self.install_proc_exec_mngr.wait_for_process_finished():
                kernel_specs = find_kernel_specs()
            else:
                self._toolbox.msg_error.emit("Failed to install IPython kernel specifications.")
                return False
        # Everything ready, start Python Console
        kernel_dir = kernel_specs[self.kernel_name]
        kernel_spec_anchor = "<a style='color:#99CCFF;' title='{0}' href='#'>{1}</a>".format(
            kernel_dir, self.kernel_name
        )
        self._toolbox.msg.emit("\tStarting IPython kernel {0}".format(kernel_spec_anchor))
        self.start_python_kernel()
        return True

    def is_package_installed(self, package_name):
        """Checks if given package is installed to selected Python environment.

        Args:
            package_name (str): Package name

        Returns:
            (bool): True if installed, False if not
        """
        response = subprocess.check_output([self.python_cmd, '-m', 'pip', 'freeze', '-q'])
        installed_packages = [r.decode().split('==')[0] for r in response.split()]
        if package_name in installed_packages:
            return True
        return False

    def start_package_install_process(self, package_name):
        """Starts installing the given package using pip.

        Args:
            package_name (str): Package name to install using pip
        """
        program = "{0}".format(self.python_cmd)  # selected python environment
        args = list()
        args.append("-m")
        args.append("pip")
        args.append("install")
        args.append(package_name)
        self.install_proc_exec_mngr = QProcessExecutionManager(self._toolbox, program, args, semisilent=True)
        self.install_proc_exec_mngr.execution_finished.connect(self.handle_package_install_process_finished)
        self.install_proc_exec_mngr.start_execution()

    @Slot(int)
    def handle_package_install_process_finished(self, retval):
        """Handles installing package finished.

        Args:
            retval (int): Process return value. 0: success, !0: failure
        """
        self.install_proc_exec_mngr.execution_finished.disconnect()
        self.install_proc_exec_mngr.deleteLater()
        self.install_proc_exec_mngr = None
        if retval != 0:
            self._toolbox.msg_error.emit("\tInstalling required package failed. Please install it manually.")
            return
        self._toolbox.msg_success.emit("\tInstalling package to environment {0} succeeded".format(self.python_cmd))
        self.check_and_install_requirements()  # Check reqs again

    def start_kernelspec_install_process(self):
        """Install kernel specifications for the selected Python environment."""
        # python -m ipykernel install --user --name python-3.4 --display-name Python3.4
        # Creates kernelspecs to
        # C:\Users\ttepsa\AppData\Roaming\jupyter\kernels\python-3.4
        program = "{0}".format(self.python_cmd)  # selected python environment
        args = list()
        args.append("-m")
        args.append("ipykernel")
        args.append("install")
        args.append("--user")
        args.append("--name")
        args.append(self.kernel_name)
        args.append("--display-name")
        args.append(self.kernel_display_name)
        self.install_proc_exec_mngr = QProcessExecutionManager(self._toolbox, program, args, semisilent=True)
        self.install_proc_exec_mngr.execution_finished.connect(self.handle_kernelspec_install_process_finished)
        self.install_proc_exec_mngr.start_execution()

    @Slot(int)
    def handle_kernelspec_install_process_finished(self, retval):
        """Handles installing package finished.

        Args:
            retval (int): Process return value. 0: success, !0: failure
        """
        self.install_proc_exec_mngr.execution_finished.disconnect()
        self.install_proc_exec_mngr.deleteLater()
        self.install_proc_exec_mngr = None
        if retval != 0:
            self._toolbox.msg_error.emit("\tInstalling kernel specs failed. Please install them manually.")
            return
        self._toolbox.msg_success.emit("\tKernel specs <b>{0}</b> installed".format(self.kernel_name))
        self.start_python_kernel()

    def start_python_kernel(self):
        """Starts kernel manager and client and attaches
        the client to the Python Console."""
        self._kernel_starting = True
        km = QtKernelManager(kernel_name=self.kernel_name)
        try:
            blackhole = open(os.devnull, 'w')
            km.start_kernel(stdout=blackhole, stderr=blackhole)
            kc = km.client()
            kc.start_channels()
            self.kernel_manager = km
            self.kernel_client = kc
            self.connect_signals()
            return True
        except FileNotFoundError:
            self._toolbox.msg_error.emit("\tCouldn't find the Python executable specified by the Jupyter kernel")
            self._kernel_starting = False
            return False
        except NoSuchKernel:  # kernelspecs for the selected kernel_name not available
            self._toolbox.msg_error.emit(
                "\tCouldn't find the specified IPython kernel specs [{0}]".format(self.kernel_name)
            )
            self._kernel_starting = False
            return False

    def wake_up(self):
        """See base class."""
        k_tuple = self.python_kernel_name()
        if not k_tuple:
            self.execution_failed.emit(-1)
            return
        # Check if this kernel is already running
        kernel_name, kernel_display_name = k_tuple
        if self.kernel_manager and self.kernel_name == kernel_name:
            self.ready_to_execute.emit()
        else:
            self.launch_kernel(kernel_name, kernel_display_name)

    @Slot(str)
    def handle_executing(self, code):
        """Slot for handling the 'executing' signal. Signal is emitted
        when a user visible 'execute_request' has been submitted to the
        kernel from the FrontendWidget.

        Args:
            code (str): Code to be executed (actually not 'str' but 'object')
        """
        self._control.viewport().setCursor(Qt.BusyCursor)

    @Slot(dict)
    def handle_executed(self, msg):
        """Slot for handling the 'executed' signal. Signal is emitted
        when a user-visible 'execute_reply' has been received from the
        kernel and processed by the FrontendWidget.

        Args:
            msg (dict): Response message (actually not 'dict' but 'object')
        """
        self._control.viewport().setCursor(self.normal_cursor)
        if msg['content']['status'] == 'ok':
            # TODO: If user Stops execution, it should be handled here
            self.ready_to_execute.emit()
        else:
            # TODO: if status='error' you can get the exception and more info from msg
            self.execution_failed.emit(-1)

    @Slot(dict)
    def receive_iopub_msg(self, msg):
        """Message received from the IOPUB channel.
        Note: We are only monitoring when the kernel has started
        successfully and ready for action here. Alternatively, this
        could be done in the Slot for the 'executed' signal. However,
        this Slot could come in handy at some point. See 'Messaging in
        Jupyter' for details:
        https://jupyter-client.readthedocs.io/en/latest/messaging.html

        Args:
            msg (dict): Received message from IOPUB channel
        """
        if msg["header"]["msg_type"] == "status":
            # When msg_type:'status, content has the kernel execution_state
            # When msg_type:'execute_input', content has the code to be executed
            # When msg_type:'stream', content has the stream name (e.g. stdout) and the text
            execution_state = msg['content']['execution_state']
            try:
                parent_msg_type = msg["parent_header"]["msg_type"]  # msg that the received msg is replying to
            except KeyError:
                # execution_state: 'starting' -> no parent_header
                parent_msg_type = "na"  # status msg has no parent header
                # self._toolbox.msg.emit(msg)
            if parent_msg_type == "kernel_info_request":
                # If kernel_state:'busy', kernel_info_request is being processed
                # If kernel_state:'idle', kernel_info_request is done
                pass
            elif parent_msg_type == "history_request":
                # If kernel_state:'busy', history_request is being processed
                # If kernel_state:'idle', history_request is done
                pass
            elif parent_msg_type == "execute_request":
                # If kernel_state:'busy', execute_request is being processed (i.e. execution or start-up in progress)
                # If kernel_state:'idle', execute_request is done
                if execution_state == "busy":
                    # kernel is busy starting up or executing
                    pass
                elif execution_state == "idle":
                    # Kernel is idle after execution
                    if self._kernel_starting:
                        # Kernel is idle after starting up -> execute pending command
                        self._kernel_starting = False
                        # Start executing the first command (if available) from the command buffer immediately
                    self.ready_to_execute.emit()
                else:
                    # This should probably happen when _kernel_state is 'starting' but it doesn't seem to show up
                    self._toolbox.msg_error.emit(
                        "Unhandled execution_state '{0}' after " "execute_request".format(execution_state)
                    )

    def shutdown_kernel(self, hush=False):
        """Shut down Python kernel."""
        if not self.kernel_client:
            return
        self.disconnect_signals()
        if not hush:
            self._toolbox.msg.emit("Shutting down Python Console...")
        self.kernel_client.stop_channels()
        self.kernel_manager.shutdown_kernel()

    def push_vars(self, var_name, var_value):
        """Push a variable to Python Console session.
        Simply executes command 'var_name=var_value'.

        Args:
            var_name (str): Variable name
            var_value (object): Variable value

        Returns:
            (bool): True if succeeded, False otherwise
        """
        if not self.kernel_manager:
            return False
        self.execute("{0}={1}".format(var_name, var_value))
        return True

    @Slot()
    def test_push_vars(self):
        """QAction slot to test pushing variables to Python Console."""
        a = dict()
        a["eka"] = 1
        a["toka"] = 2
        a["kolmas"] = 3
        if not self.push_vars("a", a):
            self._toolbox.msg_error.emit("Pushing variable to Python Console failed")
        else:
            self._toolbox.msg.emit("Variable 'a' is now in Python Console")

    def _context_menu_make(self, pos):
        """Reimplemented to add custom actions."""
        menu = super()._context_menu_make(pos)
        first_action = menu.actions()[0]
        menu.insertAction(first_action, self.start_action)
        menu.insertAction(first_action, self.restart_action)
        menu.insertSeparator(first_action)
        return menu

    def dragEnterEvent(self, e):
        """Don't accept project item drops."""
        source = e.source()
        if isinstance(source, DraggableWidget):
            e.ignore()
        else:
            super().dragEnterEvent(e)

    def _is_complete(self, source, interactive):
        """See base class."""
        raise NotImplementedError()
