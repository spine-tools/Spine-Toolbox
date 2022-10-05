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
Client for exchanging messages between the toolbox and the Spine Engine Server.
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
from spine_engine.exception import RemoteEngineInitFailed


class ClientSecurityModel(Enum):
    NONE = 0  # Nope
    STONEHOUSE = 1  # ZMQ stonehouse security model


class EngineClient:
    def __init__(self, host, port, sec_model, sec_folder, ping=True):
        """
        Args:
            host (str): IP address of the Spine Engine Server
            port(int): Port of the client facing (frontend) socket on Spine Engine Server
            sec_model (ClientSecurityModel): Client security scheme
            sec_folder (str): Path to security file directory
            ping (bool): Whether to check connectivity at instance creation
        """
        self.protocol = "tcp"  # Hard-coded to tcp for now
        self.host = host
        self.port = port  # Request socket port
        self.ping = ping
        self._context = zmq.Context()
        self._req_socket = self._context.socket(zmq.REQ)
        self._req_socket.setsockopt(zmq.LINGER, 1)
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
            self._req_socket.curve_secretkey = client_secret
            self._req_socket.curve_publickey = client_public
            # The client must know the server's public key to make a CURVE connection.
            server_public_file = os.path.join(public_keys_dir, "server.key")
            server_public, _ = zmq.auth.load_certificate(server_public_file)
            self._req_socket.curve_serverkey = server_public
        self._req_socket.connect(self.protocol + "://" + host + ":" + str(port))
        if self.ping:
            try:
                self._check_connectivity(1000)  # Ping server
            except RemoteEngineInitFailed:
                self.close()
                raise

    def start_execute(self, engine_data, job_id):
        """Sends the start execution request along with job Id and engine (dag) data to the server.
        Response message data contains the publish socket port if execution starts successfully.

        Args:
            engine_data (str): Input for SpineEngine as JSON str. Includes most of project.json, settings, etc.
            job_id (str): Project execution job Id on server

        Returns:
            tuple: Response tuple (event_type: data). Event_type is "server_init_failed",
            "remote_execution_init_failed" or "remote_execution_started. data is an error
            message or the publish socket port
        """
        msg = ServerMessage("start_execution", job_id, engine_data)
        self._req_socket.send_multipart([msg.to_bytes()])  # Send execute request
        response = self._req_socket.recv()  # Blocks until a response is received
        response_msg = ServerMessage.parse(response)  # Parse received bytes into a ServerMessage
        data = response_msg.getData()
        return data

    def connect_sub_socket(self, publish_port, filt):
        """Connects and sets up a subscribe socket for receiving engine execution events from server.

        Args:
            publish_port (str): Port of the event publisher socket on server
            filt (bytes): Filter for messages, b"" subscribes to all messages
        """
        self.sub_socket.connect(self.protocol + "://" + self.host + ":" + publish_port)
        self.sub_socket.setsockopt(zmq.SUBSCRIBE, filt)

    def rcv_next_event(self):
        """Waits until the subscribe socket receives a new event from server."""
        return self.sub_socket.recv_multipart()

    def close(self):
        """Closes client socket, context and thread."""
        if not self._req_socket.closed:
            self._req_socket.close()
        if not self.sub_socket.closed:
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
        ping_request = ServerMessage("ping", str(random_id), "")
        self._req_socket.send_multipart([ping_request.to_bytes()], flags=zmq.NOBLOCK)
        event = self._req_socket.poll(timeout=timeout)
        if event == 0:
            raise RemoteEngineInitFailed("Timeout expired. Pinging the server failed.")
        else:
            msg = self._req_socket.recv()
            response = ServerMessage.parse(msg)
            response_id = int(response.getId())  # Check that request ID matches the response ID
            if not response_id == random_id:
                raise RemoteEngineInitFailed(f"Ping failed. Request Id '{random_id}' does not "
                                             f"match reply Id '{response_id}'")
            stop_time_ms = round(time.time() * 1000.0)  # debugging
        return

    def send_project_file(self, project_dir_name, fpath):
        """Sends the zipped project file to server. Project zip file must be ready and the server available
        before calling this method.

        Args:
            project_dir_name (str): Project directory name
            fpath (str): Absolute path to zipped project file.

        Returns:
            str: Project execution job Id
        """
        with open(fpath, "rb") as f:
            file_data = f.read()  # Read file into bytes string
        _, zip_filename = os.path.split(fpath)
        req = ServerMessage("prepare_execution", "1", json.dumps(project_dir_name), [zip_filename])
        self._req_socket.send_multipart([req.to_bytes(), file_data])
        response = self._req_socket.recv()
        response_server_message = ServerMessage.parse(response)
        return response_server_message.getId()

    def retrieve_project(self, job_id):
        """Retrieves a zipped project file from server.

        Args:
            job_id (str): Job Id for finding the project directory on server

        Returns:
            bytes: Zipped project file
        """
        req = ServerMessage("retrieve_project", job_id, "")
        self._req_socket.send_multipart([req.to_bytes()])
        response = self._req_socket.recv_multipart()
        return response[-1]

    def send_is_complete(self, persistent_key, cmd):
        """Sends a request to process is_complete(cmd) on server and returns the response."""
        data = persistent_key, "is_complete", cmd
        return self.send_request_to_persistent(data)

    def send_issue_persistent_command(self, persistent_key, cmd):
        """Sends a request to process given command in persistent manager identified by given key.
        Yields the response string(s) as they arrive from server."""
        data = persistent_key, "issue_persistent_command", cmd
        yield from self.send_request_to_persistent_generator(data)

    def send_get_persistent_completions(self, persistent_key, text):
        """Requests completions to given text from persistent execution backend."""
        data = persistent_key, "get_completions", text
        return self.send_request_to_persistent(data)

    def send_get_persistent_history_item(self, persistent_key, text, prefix, backwards):
        """Requests the former or latter history item from persistent execution backend."""
        data = persistent_key, "get_history_item", [text, prefix, backwards]
        return self.send_request_to_persistent(data)

    def send_restart_persistent(self, persistent_key):
        """Sends restart persistent cmd to persistent execution manager backend on server.
        Yields the messages resulting from this operation to persistent console client."""
        data = persistent_key, "restart_persistent", ""
        yield from self.send_request_to_persistent_generator(data)

    def send_interrupt_persistent(self, persistent_key):
        """Sends interrupt persistent cmd to persistent execution manager backend on server."""
        data = persistent_key, "interrupt_persistent", ""
        return self.send_request_to_persistent(data)

    def send_request_to_persistent(self, data):
        """Sends given data containing persistent_key, command, cmd_to_persistent to
        Spine Engine Server to be processed by a persistent execution manager backend.
        Makes a request using REQ socket, parses the response into a ServerMessage, and
        returns the second part of the data field."""
        json_d = json.dumps(data)
        req = ServerMessage("execute_in_persistent", "1", json_d)
        self._req_socket.send_multipart([req.to_bytes()])
        response = self._req_socket.recv()
        response_msg = ServerMessage.parse(response)
        return response_msg.getData()[1]

    def send_request_to_persistent_generator(self, data):
        """Pulls all messages from server, that were the result of sending given data to Spine Engine Server."""
        pull_socket = self._context.socket(zmq.PULL)
        pull_port = self.send_request_to_persistent(data)
        pull_socket.connect(self.protocol + "://" + self.host + ":" + pull_port)
        while True:
            rcv = pull_socket.recv_multipart()
            if rcv == [b"END"]:
                break
            yield json.loads(rcv[0].decode("utf-8"))
        pull_socket.close()
