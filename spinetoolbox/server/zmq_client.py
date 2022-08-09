######################################################################################################################
# Copyright (C) 2017-2021 Spine project consortium
# This file is part of Spine Toolbox.
# Spine Engine is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""
ZMQ client for exchanging messages between the toolbox client and the remote server.
:author: P. Pääkkönen (VTT)
:date:   02.09.2021
"""

import os
import zmq
import zmq.auth
import time
import random
from enum import unique, Enum
from spine_engine.server.util.server_message import ServerMessage
from spine_engine.server.util.server_message_parser import ServerMessageParser
from spine_engine.server.util.event_data_converter import EventDataConverter
from spine_engine.exception import RemoteEngineFailed


class ClientSecurityModel(Enum):
    NONE = 0  # Nope
    STONEHOUSE = 1  # ZMQ stonehouse security model


@unique
class ZMQClientConnectionState(Enum):
    CONNECTED = 0
    DISCONNECTED = 1


class ZMQClient:
    def __init__(self, protocol, host, port, sec_model, sec_folder, ping=True):
        """
        Args:
            protocol (string): Zero-MQ protocol
            host: location of the remote spine server
            port(int): port of the remote spine server
            sec_model: see: ClientSecurityModel
            sec_folder: folder, where security files have been stored.
            ping (bool): True checks connection before sending the request
        """
        self.ping = ping
        self._context = zmq.Context()
        self._socket = self._context.socket(zmq.REQ)
        self._socket.setsockopt(zmq.LINGER, 1)
        if sec_model == ClientSecurityModel.STONEHOUSE:
            # Security configs
            # implementation below based on https://github.com/zeromq/pyzmq/blob/main/examples/security/stonehouse.py
            # prepare folders
            base_dir = sec_folder
            secret_keys_dir = os.path.join(base_dir, 'private_keys')
            keys_dir = os.path.join(base_dir, 'certificates')
            public_keys_dir = os.path.join(base_dir, 'public_keys')
            # We need two certificates, one for the client and one for
            # the server. The client must know the server's public key
            # to make a CURVE connection.
            client_secret_file = os.path.join(secret_keys_dir, "client.key_secret")
            client_public, client_secret = zmq.auth.load_certificate(client_secret_file)
            self._socket.curve_secretkey = client_secret
            self._socket.curve_publickey = client_public
            # The client must know the server's public key to make a CURVE connection.
            server_public_file = os.path.join(public_keys_dir, "server.key")
            server_public, _ = zmq.auth.load_certificate(server_public_file)
            self._socket.curve_serverkey = server_public
        ret = self._socket.connect(protocol + "://" + host + ":" + str(port))
        # Ping server
        self._connection_state = ZMQClientConnectionState.DISCONNECTED
        if self.ping:
            try:
                self._check_connectivity(1000)
            except RemoteEngineFailed:
                raise
        self._connection_state = ZMQClientConnectionState.CONNECTED

    def get_connection_state(self):
        """Returns client connection state.

        Returns:
            int: ZMQClientConnectionState
        """
        return self._connection_state

    def send(self, engine_data, file_path, filename):
        """Sends the project and the execution request to the server, waits for the response and acts accordingly.

        Args:
            engine_data (str): Input for SpineEngine as JSON str. Includes most of project.json, settings, etc.
            file_path (string): Path to project zip-file
            filename (string): Name of the binary file to be transmitted

        Returns:
            list or str: List of tuples containing events+data, or an error message string if something went wrong
            in initializing the execution at server.
        """
        zip_path = os.path.join(file_path, filename)
        print(f"zip_path in send():{zip_path}")
        if not os.path.exists(zip_path):
            raise ValueError(f"Zipped project file {filename} not found in {file_path}")
        print(f"Zip-file size:{os.path.getsize(zip_path)}")
        with open(zip_path, "rb") as f:
            file_data = f.read()  # Read file into bytes string
        # Create request content
        random_id = random.randrange(10000000)  # Request ID
        list_files = [filename]
        msg = ServerMessage("execute", str(random_id), engine_data, list_files)
        print(f"ZMQClient(): msg to be sent: {msg.toJSON()} + {len(file_data)} of data in bytes (zip-file)")
        self._socket.send_multipart([msg.to_bytes(), file_data])  # Send request
        response = self._socket.recv()  # Blocks until a response is received
        response_str = response.decode("utf-8")  # Decode received bytes to get (JSON) string
        response_msg = ServerMessageParser.parse(response_str)  # Parse received JSON string into a ServerMessage
        data = response_msg.getData()  # Get events+data in a dictionary
        # If something went wrong, data is an error string instead of a dictionary
        if type(data) == str:
            return data
        else:
            # Convert dictionary into a list of tuples and the base64 stuff to sane text
            data_events = EventDataConverter.convertJSON(data, True)
            return data_events

    def close(self):
        """Closes ZMQ client socket, context and thread."""
        if not self._socket.closed:
            self._socket.close()
        if not self._context.closed:
            self._context.term()

    def _check_connectivity(self, timeout):
        """Pings server, waits for the response, and acts accordingly.

        Args:
            timeout (int): Time to wait before giving up [ms]

        Returns:
            void

        Raises:
            RemoteEngineFailed if the server is not responding.
        """
        start_time_ms = round(time.time() * 1000.0)
        random_id = random.randrange(10000000)
        ping_request = ServerMessage("ping", str(random_id), "", None)
        self._socket.send_multipart([ping_request.to_bytes()], flags=zmq.NOBLOCK)
        event = self._socket.poll(timeout=timeout)
        if event == 0:
            raise RemoteEngineFailed("Timeout expired. Pinging the server failed.")
        else:
            msg = self._socket.recv()
            msg_str = msg.decode("utf-8")
            response = ServerMessageParser.parse(msg_str)
            # Check that request ID matches the response ID
            response_id = int(response.getId())
            if not response_id == random_id:
                raise RemoteEngineFailed(f"Ping failed. Request Id '{random_id}' does not match "
                                         f"reply Id '{response_id}'")
            stop_time_ms = round(time.time() * 1000.0)  # debugging
            print("Ping message received, RTT: %d ms" % (stop_time_ms - start_time_ms))
        return
