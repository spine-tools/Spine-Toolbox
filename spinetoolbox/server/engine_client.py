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
Client for exchanging messages between the toolbox and the remote Spine Engine server.
:author: P. Pääkkönen (VTT), P. Savolainen (VTT)
:date:   02.09.2021
"""

import os
import zmq
import zmq.auth
import time
import random
import json
from enum import Enum
from spine_engine.server.util.server_message import ServerMessage
from spine_engine.server.util.server_message_parser import ServerMessageParser
from spine_engine.exception import RemoteEngineInitFailed


class ClientSecurityModel(Enum):
    NONE = 0  # Nope
    STONEHOUSE = 1  # ZMQ stonehouse security model


class EngineClient:
    def __init__(self, protocol, host, port, sec_model, sec_folder, ping=True):
        """
        Args:
            protocol (str): Zero-MQ protocol
            host (str): Location of the remote spine server
            port(int): Port of the remote spine server
            sec_model (Enum): see: ClientSecurityModel
            sec_folder (str): folder, where security files have been stored.
            ping (bool): True checks connection before sending the request
        """
        self.protocol = protocol
        self.host = host
        self.port = port  # Request socket port
        self.ping = ping
        self._context = zmq.Context()
        self._socket = self._context.socket(zmq.REQ)
        self._socket.setsockopt(zmq.LINGER, 1)
        self.sub_socket = self._context.socket(zmq.SUB)
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
        self._socket.connect(protocol + "://" + host + ":" + str(port))
        if self.ping:
            try:
                self._check_connectivity(1000)  # Ping server
            except RemoteEngineInitFailed:
                raise

    def start_execute(self, engine_data, job_id):
        """Sends the project and the execution request to the server, waits for the response and acts accordingly.

        Args:
            engine_data (str): Input for SpineEngine as JSON str. Includes most of project.json, settings, etc.
            job_id (str): Job Id on server

        Returns:
            tuple: Response tuple (event_type: data). Event_type is "server_init_failed",
            "remote_execution_init_failed" or "remote_execution_started.
        """
        msg = ServerMessage("execute", job_id, engine_data, None)
        self._socket.send_multipart([msg.to_bytes()])  # Send execute request
        response = self._socket.recv()  # Blocks until a response is received
        response_str = response.decode("utf-8")  # Decode received bytes to get (JSON) string
        response_msg = ServerMessageParser.parse(response_str)  # Parse received JSON string into a ServerMessage
        data = response_msg.getData()
        return data

    def connect_sub_socket(self, publish_port):
        """Connects and sets up a subscribe socket for receiving remote engine execution events.

        Args:
            publish_port (str): Port of the event publish socket on server
        """
        self.sub_socket.connect(self.protocol + "://" + self.host + ":" + publish_port)
        self.sub_socket.setsockopt(zmq.SUBSCRIBE, b"EVENTS")

    def close(self):
        """Closes client socket, context and thread."""
        if not self._socket.closed:
            self._socket.close()
            self.sub_socket.close()
        if not self._context.closed:
            self._context.term()

    def _check_connectivity(self, timeout):
        """Pings server, waits for the response, and acts accordingly.

        Args:
            timeout (int): Time to wait before giving up [ms]

        Returns:
            void

        Raises:
            RemoteEngineInitFailed if the server is not responding.
        """
        start_time_ms = round(time.time() * 1000.0)
        random_id = random.randrange(10000000)
        ping_request = ServerMessage("ping", str(random_id), "", None)
        self._socket.send_multipart([ping_request.to_bytes()], flags=zmq.NOBLOCK)
        event = self._socket.poll(timeout=timeout)
        if event == 0:
            raise RemoteEngineInitFailed("Timeout expired. Pinging the server failed.")
        else:
            msg = self._socket.recv()
            msg_str = msg.decode("utf-8")
            response = ServerMessageParser.parse(msg_str)
            # Check that request ID matches the response ID
            response_id = int(response.getId())
            if not response_id == random_id:
                raise RemoteEngineInitFailed(f"Ping failed. Request Id '{random_id}' does not "
                                             f"match reply Id '{response_id}'")
            stop_time_ms = round(time.time() * 1000.0)  # debugging
            print("Ping message received, RTT: %d ms" % (stop_time_ms - start_time_ms))
        return

    def send_project_file(self, project_dir, fpath):
        """Sends the zipped project file to server. Project zip file must be ready and the server available
        before calling this method.

        Args:
            project_dir (str): Absolute path to project directory
            fpath (str): Absolute path to zipped project file.

        Returns:
            str: Server project execution job Id
        """
        with open(fpath, "rb") as f:
            file_data = f.read()  # Read file into bytes string
        _, zip_filename = os.path.split(fpath)
        project_dir = project_dir.replace(os.sep, "/")
        req = ServerMessage("prepare_execution", "1", json.dumps(project_dir), [zip_filename])
        self._socket.send_multipart([req.to_bytes(), file_data])
        response = self._socket.recv()
        response_server_message = ServerMessageParser.parse(response.decode("utf-8"))
        print(f"Got response to cmd:{response_server_message.getCommand()}: id:{response_server_message.getId()}")
        return response_server_message.getId()
