######################################################################################################################
# Copyright (C) 2017-2022 Spine project consortium
# Copyright Spine Toolbox contributors
# This file is part of Spine Toolbox.
# Spine Engine is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""Client for exchanging messages between the toolbox and the Spine Engine Server."""
import os
import time
import random
import json
from enum import Enum
import zmq
import zmq.auth
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
        self._context = zmq.Context()
        self.dealer_socket = self._context.socket(zmq.DEALER)
        self.dealer_socket.setsockopt(zmq.LINGER, 1)
        self.pull_socket = self._context.socket(zmq.PULL)
        self.poller = zmq.Poller()
        self.poller.register(self.dealer_socket, zmq.POLLIN)
        self.poller.register(self.pull_socket, zmq.POLLIN)
        self.client_project_dir = None
        self.start_time = 0
        if sec_model == ClientSecurityModel.STONEHOUSE:
            # Security configs
            # implementation below based on https://github.com/zeromq/pyzmq/blob/main/examples/security/stonehouse.py
            # prepare folders
            base_dir = sec_folder
            secret_keys_dir = os.path.join(base_dir, "private_keys")
            keys_dir = os.path.join(base_dir, "certificates")
            public_keys_dir = os.path.join(base_dir, "public_keys")
            # We need two certificates, one for the client and one for
            # the server. The client must know the server's public key
            # to make a CURVE connection.
            client_secret_file = os.path.join(secret_keys_dir, "client.key_secret")
            client_public, client_secret = zmq.auth.load_certificate(client_secret_file)
            self.dealer_socket.curve_secretkey = client_secret
            self.dealer_socket.curve_publickey = client_public
            # The client must know the server's public key to make a CURVE connection.
            server_public_file = os.path.join(public_keys_dir, "server.key")
            server_public, _ = zmq.auth.load_certificate(server_public_file)
            self.dealer_socket.curve_serverkey = server_public
        self.dealer_socket.connect(self.protocol + "://" + self.host + ":" + str(self.port))
        if ping:
            try:
                self._check_connectivity(1000)  # Ping server
            except RemoteEngineInitFailed:
                self.close()
                raise

    def connect_pull_socket(self, port):
        """Connects a PULL socket for receiving engine execution events and files from server.

        Args:
            port (str): Port of the PUSH socket on server
        """
        self.pull_socket.connect(self.protocol + "://" + self.host + ":" + port)

    def rcv_next(self, dealer_or_pull):
        """Polls all sockets and returns a new reply based on given socket 'name'.

        Args:
            dealer_or_pull (str): "dealer" to wait reply from DEALER socket, "pull" to wait reply from PULL socket
        """
        while True:
            sockets = dict(self.poller.poll())
            if sockets.get(self.pull_socket) == zmq.POLLIN:
                if dealer_or_pull == "pull":
                    return self.pull_socket.recv_multipart()
                continue
            if sockets.get(self.dealer_socket) == zmq.POLLIN:
                if dealer_or_pull == "dealer":
                    return self.dealer_socket.recv_multipart()
                continue

    def _check_connectivity(self, timeout):
        """Pings server, waits for the response, and acts accordingly.

        Args:
            timeout (int): Time to wait for a response before giving up [ms]

        Returns:
            void

        Raises:
            RemoteEngineInitFailed if the server is not responding.
        """
        self.set_start_time()
        random_id = random.randrange(10000000)
        ping_request = ServerMessage("ping", str(random_id), "")
        self.dealer_socket.send_multipart([ping_request.to_bytes()], flags=zmq.NOBLOCK)
        event = self.dealer_socket.poll(timeout=timeout)
        if event == 0:
            raise RemoteEngineInitFailed("Timeout expired. Pinging the server failed.")
        else:
            msg = self.dealer_socket.recv_multipart()
            response = ServerMessage.parse(msg[1])
            response_id = int(response.getId())  # Check that request ID matches the response ID
            if not response_id == random_id:
                raise RemoteEngineInitFailed(
                    f"Ping failed. Request Id '{random_id}' does not " f"match reply Id '{response_id}'"
                )
            stop_time_ms = round(time.time() * 1000.0)  # debugging
        return

    def set_start_time(self):
        """Sets a start time for an operation. Call get_elapsed_time() after
        an operation has finished to get the elapsed time string."""
        self.start_time = round(time.time() * 1000.0)

    def upload_project(self, project_dir_name, fpath):
        """Uploads the zipped project file to server. Project zip file must be ready and the server available
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
        self.dealer_socket.send_multipart([req.to_bytes(), file_data])
        response = self.dealer_socket.recv_multipart()
        response_server_message = ServerMessage.parse(response[1])
        return response_server_message.getId()

    def start_execution(self, engine_data, job_id):
        """Sends the start execution request along with job Id and engine (dag) data to the server.
        Response message data contains the push/pull socket port if execution starts successfully.

        Args:
            engine_data (str): Input for SpineEngine as JSON str. Includes most of project.json, settings, etc.
            job_id (str): Project execution job Id on server

        Returns:
            tuple: Response tuple (event_type, data). Event_type is "server_init_failed",
            "remote_execution_init_failed" or "remote_execution_started. data is an error
            message or the publish and push sockets ports concatenated with ':'.
        """
        self.start_time = round(time.time() * 1000.0)
        msg = ServerMessage("start_execution", job_id, engine_data)
        self.dealer_socket.send_multipart([msg.to_bytes()])  # Send request
        response = self.rcv_next("dealer")
        response_msg = ServerMessage.parse(response[1])  # Parse received bytes into a ServerMessage
        return response_msg.getData()

    def stop_execution(self, job_id):
        """Sends a request to stop executing the DAG that is managed by this client.

        Args:
            job_id (str): Job Id on server to stop
        """
        req = ServerMessage("stop_execution", job_id, "", None)
        self.dealer_socket.send_multipart([req.to_bytes()])
        response = self.rcv_next("dealer")
        response_server_message = ServerMessage.parse(response[1])
        return response_server_message.getData()

    def answer_prompt(self, job_id, prompter_id, answer):
        """Sends a request to answer a prompt from the DAG that is managed by this client.

        Args:
            job_id (str): Job Id on server to stop
            prompter_id (int)
            answer
        """
        req = ServerMessage("answer_prompt", job_id, json.dumps((prompter_id, answer)), None)
        self.socket.send_multipart([req.to_bytes()])

    def download_files(self, q):
        """Pulls files from server until b'END' is received."""
        i = 0
        while True:
            rcv = self.rcv_next("pull")
            if rcv[0] == b"END":
                if i > 0:
                    q.put(("server_status_msg", {"msg_type": "neutral", "text": f"Downloaded {i} files"}))
                break
            elif rcv[0] == b"incoming_file":
                q.put(
                    ("server_status_msg", {"msg_type": "warning", "text": "Downloading file " + rcv[1].decode("utf-8")})
                )
            else:
                success, txt = self.save_downloaded_file(rcv[0], rcv[1])
                q.put(("server_status_msg", {"msg_type": success, "text": txt}))
                i += 1

    def save_downloaded_file(self, b_rel_path, file_data):
        """Saves downloaded file to project directory.

        Args:
            b_rel_path (bytes): Relative path (to project dir) where the file should be saved
            file_data (bytes): File as bytes object
        """
        rel_path = b_rel_path.decode("utf-8")
        if not self.client_project_dir:
            return "fail", f"Project dir should be {self.client_project_dir} but it was not found"
        dst_fpath = os.path.abspath(os.path.join(self.client_project_dir, rel_path))
        rel_path_wo_fname, _ = os.path.split(rel_path)
        dst_dir, fname = os.path.split(dst_fpath)
        if not os.path.exists(dst_dir):
            try:
                os.makedirs(dst_dir)  # Create dst directory
            except OSError:
                return "fail", f"Creating destination dir {dst_dir} for file {fname} failed"
        try:
            with open(dst_fpath, "wb") as f:
                f.write(file_data)
        except Exception as e:
            return "fail", f"Saving the received file to '{dst_fpath}' failed. [{type(e).__name__}: {e}"
        return "neutral", f"<b>{fname}</b> saved to  <b>&#x227A;project_dir&#x227B;/{rel_path_wo_fname}</b>"

    def retrieve_project(self, job_id):
        """Retrieves a zipped project file from server.

        Args:
            job_id (str): Job Id for finding the project directory on server

        Returns:
            bytes: Zipped project file
        """
        req = ServerMessage("retrieve_project", job_id, "")
        self.dealer_socket.send_multipart([req.to_bytes()])
        response = self.dealer_socket.recv_multipart()
        return response[-1]

    def remove_project_from_server(self, job_id):
        """Sends a request to remove a project directory from server.

        Args:
            job_id (str): Job Id for finding the project directory on server

        Returns:
            str: Message from server
        """
        req = ServerMessage("remove_project", job_id, "")
        self.dealer_socket.send_multipart([req.to_bytes()])
        response = self.dealer_socket.recv_multipart()
        return response[-1]

    def send_is_complete(self, persistent_key, cmd):
        """Sends a request to process is_complete(cmd) in persistent manager on server and returns the response."""
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

    def send_kill_persistent(self, persistent_key):
        """Sends kill persistent cmd to persistent execution manager backend on server.

        Args:
            persistent_key (tuple): persistent manager identifier
        """
        data = persistent_key, "kill_persistent", ""
        return self.send_request_to_persistent(data)

    def send_request_to_persistent(self, data):
        """Sends given data containing persistent_key, command, cmd_to_persistent to
        Spine Engine Server to be processed by a persistent execution manager backend.
        Makes a request using REQ socket, parses the response into a ServerMessage, and
        returns the second part of the data field."""
        json_d = json.dumps(data)
        req = ServerMessage("execute_in_persistent", "1", json_d)
        self.dealer_socket.send_multipart([req.to_bytes()])
        response = self.dealer_socket.recv_multipart()
        response_msg = ServerMessage.parse(response[1])
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
        completed_msg = self.dealer_socket.recv_multipart()  # Get the final 'completed' msg

    def get_elapsed_time(self):
        """Returns the elapsed time between now and when self.start_time was set.

        Returns:
            str: Time string with unit(s)
        """
        t = round(time.time() * 1000.0) - self.start_time  # ms
        if t <= 1000:
            return str(t) + " ms"
        elif 1000 < t < 60000:  # 1 < t < 60 s
            return str(t / 1000) + " s"
        else:
            m = (t / 1000) / 60
            s = (t / 1000) % 60
            return str(m) + " min " + str(s) + " s"

    def close(self):
        """Closes client sockets, context and thread."""
        if not self.dealer_socket.closed:
            self.dealer_socket.close()
        if not self.pull_socket.closed:
            self.pull_socket.close()
        if not self._context.closed:
            self._context.term()
