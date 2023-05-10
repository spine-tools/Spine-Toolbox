######################################################################################################################
# Copyright (C) 2017-2022 Spine project consortium
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""
Unit tests for the JupyterConsoleWidget.
"""

import time
import unittest
from unittest import mock
from threading import Event
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Slot, QObject
from PySide6.QtGui import QIcon
from spinetoolbox.widgets.jupyter_console_widget import JupyterConsoleWidget
from spinetoolbox.widgets.console_window import ConsoleWindow
from spine_engine.execution_managers.kernel_execution_manager import _kernel_manager_factory
from jupyter_client.kernelspec import NATIVE_KERNEL_NAME
from jupyter_client.threaded import ThreadedKernelClient
from qtconsole.kernel_mixins import QtKernelClientMixin
from qtconsole.client import QtHBChannel, QtZMQSocketChannel
from traitlets import Type
from tests.mock_helpers import create_toolboxui, clean_up_toolbox


class CustomQtZMQSocketChannel(QtZMQSocketChannel):
    """Class."""
    last_msg = None

    def __init__(self, *args, **kwargs):
        self.msg_recv = Event()
        super().__init__(*args, **kwargs)

    def call_handlers(self, msg):
        super().call_handlers(msg)
        msg_type = msg["header"]["msg_type"]
        if msg_type == "status":
            execution_state = msg["content"]["execution_state"]
            print(f"status: execution_state:{execution_state}")
        elif msg_type == "kernel_info_reply":
            kernel_status = msg["content"]["status"]
            print(f"Kernel connected: {kernel_status}")
            self.last_msg = msg
            self.msg_recv.set()
        elif msg_type == "execute_reply":
            status = msg["content"]["status"]
            self.last_msg = msg
            self.msg_recv.set()
        # time.sleep(2)


class CustomThreadedKernelClient(ThreadedKernelClient):
    """Also Class."""
    iopub_channel_class = Type(CustomQtZMQSocketChannel)
    shell_channel_class = Type(CustomQtZMQSocketChannel)
    stdin_channel_class = Type(CustomQtZMQSocketChannel)


class CustomQtKernelClient(QtKernelClientMixin, CustomThreadedKernelClient):
    """ A CustomQtKernelClient where ThreadedKernelClient super class is replaced with a custom one."""
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
        jcw = JupyterConsoleWidget(self.toolbox, kernel_name="testkernel")
        self.assertIsInstance(jcw, JupyterConsoleWidget)
        self.assertIsInstance(jcw, QObject)

    def test_connect_jcw_to_kernel_manager_on_engine(self):
        jcw = JupyterConsoleWidget(self.toolbox, NATIVE_KERNEL_NAME)
        cw = ConsoleWindow(self.toolbox, jcw, QIcon())
        success = cw.console().request_start_kernel()
        self.assertTrue(success)
        self.assertEqual(1, _kernel_manager_factory.n_kernel_managers())
        # Replace QtKernelClient class with a custom one
        # Inspired by jupyter_client/tests/test_client.py
        with mock.patch("spinetoolbox.widgets.jupyter_console_widget.QtKernelClient", new=CustomQtKernelClient) as mtkc:
            jcw.connect_to_kernel()
            jcw.kernel_client.shell_channel.msg_recv.wait(timeout=10)
            reply = jcw.kernel_client.shell_channel.last_msg
            print(f"reply:{reply}")
            self.assertTrue(jcw.kernel_client.is_alive())
        jcw.kernel_client.execute("print('0')")
        jcw.kernel_client.shell_channel.msg_recv.wait(timeout=10)
        execute_reply = jcw.kernel_client.shell_channel.last_msg
        print(f"execute_reply:{execute_reply}")
        self.assertTrue(execute_reply["content"]["status"] == "ok")
        jcw.request_shutdown_kernel_manager()
        self.assertEqual(0, _kernel_manager_factory.n_kernel_managers())
        jcw.shutdown_kernel_client()
        self.assertIsNone(jcw.kernel_client)
