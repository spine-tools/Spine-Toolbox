######################################################################################################################
# Copyright (C) 2017-2020 Spine project consortium
# This file is part of Spine Items.
# Spine Items is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""
Contains SpineEngineClient.

:authors: M. Marin (KTH)
:date:   8.11.2020
"""

import socket
import json


class SpineEngineClient:
    _ENCODING = "ascii"

    def __init__(self, engine_server_address):
        self._engine_server_address = engine_server_address
        self.request = None

    def run_engine(self, data):
        """
        Sends a run_engine request to the server.

        Args:
            data (dict): The engine data.

        Returns:
            str: engine id, for further calls
        """
        return self._send("run_engine", data)

    def get_engine_event(self, engine_id):
        """
        Sends a get_engine_event request to the server.

        Args:
            engine_id (str): the engine id.

        Returns:
            tuple(str,dict): two element tuple: event type identifier string, and event data dictionary
        return self._send("run_engine", data)
        """
        return self._send("get_engine_event", engine_id)

    def stop_engine(self, engine_id):
        """
        Sends a stop_engine request to the server.

        Args:
            engine_id (str): the engine id.
        """
        self._send("stop_engine", engine_id)

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
