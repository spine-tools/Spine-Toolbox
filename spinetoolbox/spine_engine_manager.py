######################################################################################################################
# Copyright (C) 2017-2021 Spine project consortium
# This file is part of Spine Items.
# Spine Items is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""
Contains SpineEngineManagerBase.

:authors: M. Marin (KTH)
:date:   14.10.2020
"""

import socket
import json


class SpineEngineManagerBase:
    def run_engine(self, engine_data):
        """Runs an engine with given data.

        Args:
            engine_data (dict): The engine data.
        """
        raise NotImplementedError()

    def get_engine_event(self):
        """Gets next event from engine currently running.

        Returns:
            tuple(str,dict): two element tuple: event type identifier string, and event data dictionary
        """
        raise NotImplementedError()

    def stop_engine(self):
        """Stops engine currently running."""
        raise NotImplementedError()

    def restart_kernel(self, connection_file):
        """Restarts the jupyter kernel associated to given connection file.

        Args:
            connection_file (str): path of connection file
        """
        raise NotImplementedError()

    def shutdown_kernel(self, connection_file):
        """Shuts down the jupyter kernel associated to given connection file.

        Args:
            connection_file (str): path of connection file
        """
        raise NotImplementedError()


class RemoteSpineEngineManager(SpineEngineManagerBase):
    _ENCODING = "ascii"

    def __init__(self, engine_server_address):
        """
        Args:
            engine_server_address (str)
        """
        super().__init__()
        self._engine_server_address = engine_server_address
        self.request = None
        self._engine_id = None

    def run_engine(self, engine_data):
        """See base class."""
        self._engine_id = self._send("run_engine", engine_data)

    def get_engine_event(self):
        """See base class."""
        return self._send("get_engine_event", self._engine_id)

    def stop_engine(self):
        """See base class."""
        self._send("stop_engine", self._engine_id, receive=False)

    def restart_kernel(self, connection_file):
        """See base class."""
        self._send("restart_kernel", connection_file)

    def shutdown_kernel(self, connection_file):
        """See base class."""
        self._send("shutdown_kernel", connection_file)

    def _send(self, request, *args, receive=True):
        """
        Sends a request to the server with the given arguments.

        Args:
            request (str): One of the supported engine server requests
            args: Request arguments
            receive (bool, optional): If True (the default) also receives the response and returns it.

        Returns:
            str or NoneType: response, or None if receive is False
        """
        msg = json.dumps((request, args))
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as self.request:
            self.request.connect(self._engine_server_address)
            self.request.sendall(bytes(msg, "ascii"))
            if receive:
                response = self._recvall()
                return json.loads(response)

    def _recvall(self):
        """
        Receives and returns all data in the current request.

        Returns:
            str
        """
        BUFF_SIZE = 4096
        fragments = []
        while True:
            chunk = str(self.request.recv(BUFF_SIZE), self._ENCODING)
            fragments.append(chunk)
            if len(chunk) < BUFF_SIZE:
                break
        return "".join(fragments)


class LocalSpineEngineManager(SpineEngineManagerBase):
    def __init__(self):
        super().__init__()
        self._engine = None

    def run_engine(self, engine_data):
        from spine_engine.spine_engine import SpineEngine

        self._engine = SpineEngine(**engine_data)

    def get_engine_event(self):
        return self._engine.get_event()

    def stop_engine(self):
        self._engine.stop()

    def restart_kernel(self, connection_file):
        from spine_engine.execution_managers import get_kernel_manager

        get_kernel_manager(connection_file).restart_kernel(now=True)

    def shutdown_kernel(self, connection_file):
        from spine_engine.execution_managers import get_kernel_manager

        get_kernel_manager(connection_file).shutdown_kernel(now=True)


def make_engine_manager(engine_server_address):
    if not engine_server_address:
        return LocalSpineEngineManager()
    return RemoteSpineEngineManager(engine_server_address)
