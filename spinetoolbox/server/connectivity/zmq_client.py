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
A Zero-MQ client for exchanging messages between the toolbox client and the remote server.
:author: P. Pääkkönen (VTT)
:date:   02.09.2021
"""

import os
import zmq
import zmq.auth
import json
import time
import random
from enum import unique, Enum
from spine_engine.server.util.server_message import ServerMessage
from spine_engine.server.util.server_message_parser import ServerMessageParser
from spine_engine.server.util.event_data_converter import EventDataConverter


@unique
class ZMQSecurityModelState(Enum):
    NONE = 0  # no security is used
    STONEHOUSE = 1  # stonehouse-security model of Zero-MQ


# used, when connectivity is tested during initialisation
@unique
class ZMQClientConnectionState(Enum):
    CONNECTED = 0
    DISCONNECTED = 1


class ZMQClient:
    def __init__(self, protocol, remoteHost, remotePort, secModel, secFolder):
        """
        Args:
            protocol (string): Zero-MQ protocol
            remoteHost: location of the remote spine server
            remotePort(int): port of the remote spine server
            secModel: see: ZMQSecurityModelState
            secFolder: folder, where security files have been stored.
        """
        self.connectivity_testing = True
        if secModel == ZMQSecurityModelState.NONE:
            self._context = zmq.Context()
            self._socket = self._context.socket(zmq.REQ)
            self._socket.setsockopt(zmq.LINGER, 1)
            ret = self._socket.connect(protocol + "://" + remoteHost + ":" + str(remotePort))
        elif secModel == ZMQSecurityModelState.STONEHOUSE:
            self._context = zmq.Context()
            self._socket = self._context.socket(zmq.REQ)
            self._socket.setsockopt(zmq.LINGER, 1)
            # Security configs
            # implementation below based on https://github.com/zeromq/pyzmq/blob/main/examples/security/stonehouse.py
            # prepare folders
            base_dir = secFolder
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
            ret = self._socket.connect(protocol + "://" + remoteHost + ":" + str(remotePort))
        # Ping server
        if self.connectivity_testing:
            connected = self._check_connectivity(1000)
            if connected:
                self._connection_state = ZMQClientConnectionState.CONNECTED
            else:
                self._connection_state = ZMQClientConnectionState.DISCONNECTED
        else:
            self._connection_state = ZMQClientConnectionState.CONNECTED
        self._closed = False  # for tracking multiple closing calls

    def get_connection_state(self):
        """Returns ZMQ client connection state.

        Returns:
            int: ZMQClientConnectionState
        """
        return self._connection_state

    def send(self, text, file_path, filename):
        """Sends the project and the execution request to the server, waits for the response and acts accordingly.

        Args:
            text (str): Input for SpineEngine as text. Includes most of project.json, settings, etc.
            file_path (string): Path to project zip-file
            filename (string): Name of the binary file to be transferred

        Returns:
            a list of tuples containing events+data
        """
        zip_path = os.path.join(file_path, os.pardir, filename)  # Note: zip-file is in parent dir of file_path now
        if not os.path.exists(zip_path):
            raise ValueError(f"Zipped project file {filename} not found in {file_path}")
        if not text:
            raise ValueError("Invalid input text")
        print(f"Zip-file size:{os.path.getsize(zip_path)}")
        with open(zip_path, "rb") as f:
            file_data = f.read()  # Read file into bytes string
        # Create request content
        random_id = random.randrange(10000000)  # Request ID
        list_files = [filename]
        msg = ServerMessage("execute", str(random_id), text, list_files)
        print(f"ZMQClient(): msg to be sent: {msg.toJSON()} + {len(file_data)} of data in bytes (zip-file)")
        self._socket.send_multipart([msg.to_bytes(), file_data])  # Send request
        response = self._socket.recv()  # Blocks until a response is received
        response_str = response.decode("utf-8")  # Decode received bytes to get (JSON) string
        response_msg = ServerMessageParser.parse(response_str)  # Parse (JSON) string into a ServerMessage
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
        if not self._closed:
            self._socket.close()
            self._context.term()
            print("ZMQClient(): Connection closed.")
            self._closed = True

    def _check_connectivity(self, timeout):
        """Pings server, waits for the response, and acts accordingly.

        Args:
            timeout (int): Time to wait before giving up [ms]

        Returns:
            bool: True if server is ready for action, False otherwise
        """
        start_time_ms = round(time.time() * 1000.0)
        random_id = random.randrange(10000000)
        ping_request = ServerMessage("ping", str(random_id), "", None)
        self._socket.send_multipart([ping_request.to_bytes()], flags=zmq.NOBLOCK)
        event = self._socket.poll(timeout=timeout)
        if event == 0:
            print("Timeout expired. Pinging the server failed.")
            return False
        else:
            msg = self._socket.recv()
            msg_str = msg.decode("utf-8")
            response = ServerMessageParser.parse(msg_str)
            # Check that request ID matches the response ID
            response_id = int(response.getId())
            if not response_id == random_id:
                print(f"Ping failed. Request ID '{random_id}' does not match response ID '{response_id}'")
                return False
            stop_time_ms = round(time.time() * 1000.0)  # debugging
            print("Ping message received, RTT: %d ms" % (stop_time_ms - start_time_ms))
            return True
