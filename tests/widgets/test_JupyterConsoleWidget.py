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

"""Unit tests for the JupyterConsoleWidget."""
import unittest
from unittest import mock
from unittest.mock import MagicMock
from threading import Event
import queue
from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import QObject
from spinetoolbox.widgets.jupyter_console_widget import JupyterConsoleWidget
from spine_engine.execution_managers.kernel_execution_manager import _kernel_manager_factory
from jupyter_client.kernelspec import NATIVE_KERNEL_NAME
from jupyter_client.threaded import ThreadedKernelClient
from qtconsole.kernel_mixins import QtKernelClientMixin
from qtconsole.client import QtHBChannel, QtZMQSocketChannel
from traitlets import Type
from tests.mock_helpers import create_toolboxui, clean_up_toolbox


class CustomQtZMQSocketChannel(QtZMQSocketChannel):
    """Custom class for waiting for a correct channel message
    until kernel is connected or until execution has finished."""

    last_msg = None

    def __init__(self, *args, **kwargs):
        self.kernel_info_event = Event()
        self.execute_reply_event = Event()
        super().__init__(*args, **kwargs)

    def call_handlers(self, msg):
        super().call_handlers(msg)
        msg_type = msg["header"]["msg_type"]
        if msg_type == "status":
            pass  # you can get the msg["content"]["execution_state"], which is e.g. 'idle' or 'busy' here if needed
        elif msg_type == "kernel_info_reply":
            # When this appears after calling connect_to_kernel(), kernel client should be connected and ready to go
            self.last_msg = msg
            self.kernel_info_event.set()
        elif msg_type == "execute_reply":
            # These are replies to execute_request's, ['content']['status'] tells if execution succeeded
            self.last_msg = msg
            self.execute_reply_event.set()


class CustomThreadedKernelClient(ThreadedKernelClient):
    """Class where QtZMQSocketChannel is replaced with a custom implementation."""

    iopub_channel_class = Type(CustomQtZMQSocketChannel)
    shell_channel_class = Type(CustomQtZMQSocketChannel)
    stdin_channel_class = Type(CustomQtZMQSocketChannel)


class CustomQtKernelClient(QtKernelClientMixin, CustomThreadedKernelClient):
    """Custom class where ThreadedKernelClient super class is replaced with a custom one."""

    hb_channel_class = Type(QtHBChannel)


class TestJupyterConsoleWidget(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not QApplication.instance():
            QApplication()

    def setUp(self):
        """Set up toolbox."""
        self.toolbox = create_toolboxui()

    def tearDown(self):
        """Clean up."""
        clean_up_toolbox(self.toolbox)

    def test_make_jupyter_console_widget(self):
        self.assertEqual(0, _kernel_manager_factory.n_kernel_managers())
        jcw = JupyterConsoleWidget(self.toolbox, kernel_name="testkernel")
        self.assertIsInstance(jcw, JupyterConsoleWidget)
        self.assertIsInstance(jcw, QObject)
        jcw.close()
        self.assertEqual(0, _kernel_manager_factory.n_kernel_managers())

    def test_connect_jcw_to_kernel_manager_on_engine(self):
        QApplication.clipboard().clear()
        self.assertEqual(0, _kernel_manager_factory.n_kernel_managers())
        jcw = JupyterConsoleWidget(self.toolbox, NATIVE_KERNEL_NAME)
        connection_file = jcw.request_start_kernel()
        self.assertIsNotNone(connection_file)
        jcw.set_connection_file(connection_file)
        self.assertEqual(1, _kernel_manager_factory.n_kernel_managers())
        # Replace QtKernelClient class with a custom one
        # Inspired by jupyter_client/tests/test_client.py
        with mock.patch("spinetoolbox.widgets.jupyter_console_widget.QtKernelClient", new=CustomQtKernelClient) as mtkc:
            jcw.connect_to_kernel()
        jcw.kernel_client.shell_channel.kernel_info_event.wait(timeout=10)  # Wait until we get a kernel_info_reply
        kernel_info_reply = jcw.kernel_client.shell_channel.last_msg
        self.assertTrue(kernel_info_reply["content"]["status"] == "ok")  # If status == "ok" -> assume we're connected
        self.assertTrue(jcw.kernel_client.is_alive())
        jcw.kernel_client.execute("print('hi')")
        jcw.kernel_client.shell_channel.execute_reply_event.wait(timeout=10)  # Wait until an execute_reply is received
        execute_reply = jcw.kernel_client.shell_channel.last_msg
        self.assertTrue(execute_reply["content"]["status"] == "ok")  # Check that command was executed successfully
        # Check Toolbox and Engine kernel managers are the same
        self.assertEqual(
            jcw._execution_manager._kernel_manager, _kernel_manager_factory.get_kernel_manager(jcw._connection_file)
        )

        def fake_focus():
            return True

        jcw._control.hasFocus = fake_focus
        jcw._control.selectAll()
        jcw.copy_input()  # To increase coverage
        jcw.request_shutdown_kernel_manager()
        # This prevents a traceback in upcoming tests by letting the JupyterWidget finalize the shutdown process
        QApplication.processEvents()
        self.assertEqual(0, _kernel_manager_factory.n_kernel_managers())
        jcw.shutdown_kernel_client()
        self.assertIsNone(jcw.kernel_client)

    def test_restart_when_kernel_manager_is_running(self):
        self.assertEqual(0, _kernel_manager_factory.n_kernel_managers())
        jcw = JupyterConsoleWidget(self.toolbox, NATIVE_KERNEL_NAME)
        connection_file = jcw.request_start_kernel()
        self.assertIsNotNone(connection_file)
        jcw.set_connection_file(connection_file)
        self.assertEqual(1, _kernel_manager_factory.n_kernel_managers())
        # Replace QtKernelClient class with a custom one
        # Inspired by jupyter_client/tests/test_client.py
        with mock.patch("spinetoolbox.widgets.jupyter_console_widget.QtKernelClient", new=CustomQtKernelClient) as mtkc:
            jcw.connect_to_kernel()
        jcw.kernel_client.shell_channel.kernel_info_event.wait(timeout=10)  # Wait until we get a kernel_info_reply
        kernel_info_reply = jcw.kernel_client.shell_channel.last_msg
        self.assertTrue(kernel_info_reply["content"]["status"] == "ok")  # If status == "ok" -> assume we're connected
        self.assertTrue(jcw.kernel_client.is_alive())
        jcw.kernel_client.execute("print('hi')")
        jcw.kernel_client.shell_channel.execute_reply_event.wait(timeout=10)  # Wait until an execute_reply is received
        execute_reply = jcw.kernel_client.shell_channel.last_msg
        self.assertTrue(execute_reply["content"]["status"] == "ok")  # Check that command was executed successfully
        # Check Toolbox and Engine kernel managers are the same
        self.assertEqual(
            jcw._execution_manager._kernel_manager, _kernel_manager_factory.get_kernel_manager(jcw._connection_file)
        )
        # Restart kernel manager
        jcw.kernel_client.shell_channel.kernel_info_event.clear()
        with mock.patch("spinetoolbox.widgets.jupyter_console_widget.QtKernelClient", new=CustomQtKernelClient) as mtkc:
            jcw.request_restart_kernel_manager()
        jcw.kernel_client.shell_channel.kernel_info_event.wait(timeout=10)
        kernel_info_reply = jcw.kernel_client.shell_channel.last_msg
        self.assertTrue(kernel_info_reply["content"]["status"] == "ok")  # If status == "ok" -> assume we're connected
        self.assertTrue(jcw.kernel_client.is_alive())
        jcw.request_shutdown_kernel_manager()
        # This prevents a traceback in upcoming tests by letting the JupyterWidget finalize the shutdown process
        QApplication.processEvents()
        self.assertEqual(0, _kernel_manager_factory.n_kernel_managers())
        jcw.shutdown_kernel_client()
        self.assertIsNone(jcw.kernel_client)

    def test_restart_when_kernel_manager_is_not_running(self):
        self.assertEqual(0, _kernel_manager_factory.n_kernel_managers())
        jcw = JupyterConsoleWidget(self.toolbox, NATIVE_KERNEL_NAME)
        connection_file = jcw.request_start_kernel()
        self.assertIsNotNone(connection_file)
        jcw.set_connection_file(connection_file)
        self.assertEqual(1, _kernel_manager_factory.n_kernel_managers())
        # Replace QtKernelClient class with a custom one
        # Inspired by jupyter_client/tests/test_client.py
        with mock.patch("spinetoolbox.widgets.jupyter_console_widget.QtKernelClient", new=CustomQtKernelClient) as mtkc:
            jcw.connect_to_kernel()
        jcw.kernel_client.shell_channel.kernel_info_event.wait(timeout=10)  # Wait until we get a kernel_info_reply
        kernel_info_reply = jcw.kernel_client.shell_channel.last_msg
        self.assertTrue(kernel_info_reply["content"]["status"] == "ok")  # If status == "ok" -> assume we're connected
        self.assertTrue(jcw.kernel_client.is_alive())
        jcw.kernel_client.execute("print('hi')")
        jcw.kernel_client.shell_channel.execute_reply_event.wait(timeout=10)  # Wait until an execute_reply is received
        execute_reply = jcw.kernel_client.shell_channel.last_msg
        self.assertTrue(execute_reply["content"]["status"] == "ok")  # Check that command was executed successfully
        # Check Toolbox and Engine kernel managers are the same
        self.assertEqual(
            jcw._execution_manager._kernel_manager, _kernel_manager_factory.get_kernel_manager(jcw._connection_file)
        )
        # Shutdown kernel manager, simulates situation when 'kill consoles at end of execution' has been selected
        jcw.request_shutdown_kernel_manager()
        # This prevents a traceback in upcoming tests by letting the JupyterWidget finalize the shutdown process
        QApplication.processEvents()
        self.assertEqual(0, _kernel_manager_factory.n_kernel_managers())
        jcw.shutdown_kernel_client()
        self.assertIsNone(jcw.kernel_client)
        # Restart kernel manager
        # jcw.kernel_client.shell_channel.kernel_info_event.clear()
        with mock.patch("spinetoolbox.widgets.jupyter_console_widget.QtKernelClient", new=CustomQtKernelClient) as mtkc:
            jcw.request_restart_kernel_manager()
        jcw.kernel_client.shell_channel.kernel_info_event.wait(timeout=10)
        kernel_info_reply = jcw.kernel_client.shell_channel.last_msg
        self.assertTrue(kernel_info_reply["content"]["status"] == "ok")  # If status == "ok" -> assume we're connected
        self.assertTrue(jcw.kernel_client.is_alive())
        jcw.request_shutdown_kernel_manager()
        # This prevents a traceback in upcoming tests by letting the JupyterWidget finalize the shutdown process
        QApplication.processEvents()
        self.assertEqual(0, _kernel_manager_factory.n_kernel_managers())
        jcw.shutdown_kernel_client()
        self.assertIsNone(jcw.kernel_client)

    def test_close_console_by_typing_exit(self):
        self.assertEqual(0, _kernel_manager_factory.n_kernel_managers())
        jcw = JupyterConsoleWidget(self.toolbox, NATIVE_KERNEL_NAME)
        connection_file = jcw.request_start_kernel()
        self.assertIsNotNone(connection_file)
        jcw.set_connection_file(connection_file)
        self.assertEqual(1, _kernel_manager_factory.n_kernel_managers())
        # Replace QtKernelClient class with a custom one
        # Inspired by jupyter_client/tests/test_client.py
        with mock.patch("spinetoolbox.widgets.jupyter_console_widget.QtKernelClient", new=CustomQtKernelClient) as mtkc:
            jcw.connect_to_kernel()
        jcw.kernel_client.shell_channel.kernel_info_event.wait(timeout=10)  # Wait until we get a kernel_info_reply
        kernel_info_reply = jcw.kernel_client.shell_channel.last_msg
        self.assertTrue(kernel_info_reply["content"]["status"] == "ok")  # If status == "ok" -> assume we're connected
        self.assertTrue(jcw.kernel_client.is_alive())
        with mock.patch("PySide6.QtWidgets.QMessageBox.exec") as mock_msgbox_exec:
            mock_msgbox_exec.return_value = QMessageBox.StandardButton.Ok
            jcw._execute("exit", False)
        self.assertEqual(0, _kernel_manager_factory.n_kernel_managers())
        self.assertIsNone(jcw.kernel_client)

    def test_context_menu(self):
        self.assertEqual(0, _kernel_manager_factory.n_kernel_managers())
        jcw = JupyterConsoleWidget(self.toolbox, kernel_name="testkernel")
        jcw.kernel_client = MagicMock()
        jcw._context_menu_make(jcw.pos())
        jcw.close()
        self.assertEqual(0, _kernel_manager_factory.n_kernel_managers())

    def test_start_kernel_manager_fails_with_timeout(self):
        self.assertEqual(0, _kernel_manager_factory.n_kernel_managers())
        jcw = JupyterConsoleWidget(self.toolbox, kernel_name="testkernel")
        jcw._q = MagicMock()

        def raise_empty(timeout):
            raise queue.Empty

        jcw._q.get = raise_empty  # Calling multiprocessing.queue.get() raises queue.Empty
        conn_file = jcw.request_start_kernel()
        self.assertIsNone(conn_file)
        jcw.close()
        self.assertEqual(0, _kernel_manager_factory.n_kernel_managers())

    def test_start_kernel_receives_unexpected_msg(self):
        self.assertEqual(0, _kernel_manager_factory.n_kernel_managers())
        jcw = JupyterConsoleWidget(self.toolbox, kernel_name="testkernel")
        jcw._q = MagicMock()

        def return_unexpected_msg(timeout):
            return "unexpected_msg_type", {"item": "testitem"}

        jcw._q.get = return_unexpected_msg
        conn_file = jcw.request_start_kernel()
        self.assertIsNone(conn_file)
        jcw.close()
        self.assertEqual(0, _kernel_manager_factory.n_kernel_managers())

    def test_connect_to_unknown_kernel_fails(self):
        self.assertEqual(0, _kernel_manager_factory.n_kernel_managers())
        jcw = JupyterConsoleWidget(self.toolbox, "nonexistent_kernel")
        connection_file = jcw.request_start_kernel()
        self.assertIsNone(connection_file)
        jcw.close()
        self.assertEqual(0, _kernel_manager_factory.n_kernel_managers())

    def test_connect_to_unknown_conda_fails(self):
        self.assertEqual(0, _kernel_manager_factory.n_kernel_managers())
        jcw = JupyterConsoleWidget(self.toolbox, "nonexistent_conda_kernel")
        connection_file = jcw.request_start_kernel(conda=True)
        self.assertIsNone(connection_file)
        jcw.close()
        self.assertEqual(0, _kernel_manager_factory.n_kernel_managers())

    def test_connect_to_conda_kernel_when_conda_is_not_found(self):
        self.assertEqual(0, _kernel_manager_factory.n_kernel_managers())
        jcw = JupyterConsoleWidget(self.toolbox, "nonexistent_conda_kernel")
        with mock.patch("spinetoolbox.widgets.jupyter_console_widget.resolve_conda_executable") as mock_resolve_conda:
            mock_resolve_conda.return_value = "conda_that_does_not_exist.bat"
            connection_file = jcw.request_start_kernel(conda=True)
            mock_resolve_conda.assert_called()
        self.assertIsNone(connection_file)
        jcw.close()
        self.assertEqual(0, _kernel_manager_factory.n_kernel_managers())
