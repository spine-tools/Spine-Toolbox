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

:authors: M. Marin (KTH), P. Pääkkönen (VTT), P. Savolainen (VTT)
:date:   14.10.2020
"""
import os
import queue
import threading
import time
import json
import ast
from enum import Enum
from spinetoolbox.server.engine_client import EngineClient, ClientSecurityModel, EngineClientConnectionState
from spinetoolbox.config import PROJECT_ZIP_FILENAME
from spine_engine.spine_engine import ItemExecutionFinishState
from spine_engine.exception import RemoteEngineFailed
from spine_engine.server.util.server_message import ServerMessage
from spine_engine.server.util.server_message_parser import ServerMessageParser
from spine_engine.server.util.event_data_converter import EventDataConverter


class RemoteSpineEngineManagerState(Enum):
    IDLE = 1  # no requests pending and events+data of an earlier request has been extracted with get_event()
    RUNNING = 2  # request is being processed with the remote server
    REPLY_RECEIVED = 3  # a reply has been received from the remote server
    CLOSED = 4  # the manager has been closed

    def __str__(self):
        return str(self.name)


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

    def answer_prompt(self, item_name, accepted):
        """Answers prompt.

        Args:
            item_name (str): The item that emitted the prompt
            accepted (bool): The user's decision.
        """
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

    def issue_persistent_command(self, persistent_key, command):
        """Issues a command to a persistent process.

        Args:
            persistent_key (tuple): persistent identifier
            command (str): command to issue

        Returns:
            generator: stdin, stdout, and stderr messages (dictionaries with two keys: type, and data)
        """
        raise NotImplementedError()

    def is_persistent_command_complete(self, persistent_key, command):
        """Checkes whether a command is complete.

        Args:
            key (tuple): persistent identifier
            cmd (str): command to issue

        Returns:
            bool
        """
        raise NotImplementedError()

    def restart_persistent(self, persistent_key):
        """Restart a persistent process.

        Args:
            persistent_key (tuple): persistent identifier

        Returns:
            generator: stdout and stderr messages (dictionaries with two keys: type, and data)
        """
        raise NotImplementedError()

    def interrupt_persistent(self, persistent_key):
        """Interrupts a persistent process.

        Args:
            persistent_key (tuple): persistent identifier
        """
        raise NotImplementedError()

    def get_persistent_completions(self, persistent_key, text):
        """Returns a list of auto-completion options from given text.

        Args:
            persistent_key (tuple): persistent identifier
            text (str): text to complete

        Returns:
            list of str
        """
        raise NotImplementedError()

    def get_persistent_history_item(self, persistent_key, text, prefix, backwards):
        """Returns an item from persistent history.

        Args:
            persistent_key (tuple): persistent identifier

        Returns:
            str: history item or empty string if none
        """
        raise NotImplementedError()


class LocalSpineEngineManager(SpineEngineManagerBase):
    def __init__(self):
        super().__init__()
        self._engine = None

    def run_engine(self, engine_data):
        from spine_engine.spine_engine import SpineEngine  # pylint: disable=import-outside-toplevel

        self._engine = SpineEngine(**engine_data)

    def get_engine_event(self):
        return self._engine.get_event()

    def stop_engine(self):
        self._engine.stop()

    def answer_prompt(self, item_name, accepted):
        self._engine.answer_prompt(item_name, accepted)

    def restart_kernel(self, connection_file):
        # pylint: disable=import-outside-toplevel
        from spine_engine.execution_managers.kernel_execution_manager import get_kernel_manager

        km = get_kernel_manager(connection_file)
        if km is not None:
            km.restart_kernel(now=True)

    def shutdown_kernel(self, connection_file):
        # pylint: disable=import-outside-toplevel
        from spine_engine.execution_managers.kernel_execution_manager import pop_kernel_manager

        km = pop_kernel_manager(connection_file)
        if km is not None:
            km.shutdown_kernel(now=True)

    def issue_persistent_command(self, persistent_key, command):
        # pylint: disable=import-outside-toplevel
        from spine_engine.execution_managers.persistent_execution_manager import issue_persistent_command

        yield from issue_persistent_command(persistent_key, command)

    def is_persistent_command_complete(self, persistent_key, command):
        # pylint: disable=import-outside-toplevel
        from spine_engine.execution_managers.persistent_execution_manager import is_persistent_command_complete

        return is_persistent_command_complete(persistent_key, command)

    def restart_persistent(self, persistent_key):
        # pylint: disable=import-outside-toplevel
        from spine_engine.execution_managers.persistent_execution_manager import restart_persistent

        yield from restart_persistent(persistent_key)

    def interrupt_persistent(self, persistent_key):
        # pylint: disable=import-outside-toplevel
        from spine_engine.execution_managers.persistent_execution_manager import interrupt_persistent

        interrupt_persistent(persistent_key)

    def get_persistent_completions(self, persistent_key, text):
        # pylint: disable=import-outside-toplevel
        from spine_engine.execution_managers.persistent_execution_manager import get_persistent_completions

        return get_persistent_completions(persistent_key, text)

    def get_persistent_history_item(self, persistent_key, text, prefix, backwards):
        # pylint: disable=import-outside-toplevel
        from spine_engine.execution_managers.persistent_execution_manager import get_persistent_history_item

        return get_persistent_history_item(persistent_key, text, prefix, backwards)


class RemoteSpineEngineManager(SpineEngineManagerBase):
    """Responsible for remote project execution."""
    def __init__(self):
        """Initializer."""
        super().__init__()
        self._runner = threading.Thread(name="RemoteSpineEngineManagerRunnerThread", target=self._run)
        self._engine_data = None
        self.engine_client = None
        self.q = queue.Queue()  # Queue for sending data forward to SpineEngineWorker

    def run_engine(self, engine_data):
        """Establishes a connection to server using a ZMQ client. Starts a thread, where
        the current DAG is packaged into a zip file and then sent to the server for
        execution.

        Args:
            engine_data (dict): The engine data.
        """
        app_settings = engine_data["settings"]
        protocol = "tcp"  # Zero-MQ protocol. Hardcoded to tcp for now.
        host = app_settings.get("engineSettings/remoteHost", "")  # Host name
        port = app_settings.get("engineSettings/remotePort", "49152")  # Host port
        sec_model = app_settings.get("engineSettings/remoteSecurityModel", "")  # ZQM security model
        security = ClientSecurityModel.NONE if not sec_model else ClientSecurityModel.STONEHOUSE
        sec_folder = (
            ""
            if security == ClientSecurityModel.NONE
            else app_settings.get("engineSettings/remoteSecurityFolder", "")
        )
        try:
            self.engine_client = EngineClient(protocol, host, port, security, sec_folder)
        except Exception as e:
            raise RemoteEngineFailed(f"Initializing ZMQ client failed: {e}")
        if self.engine_client.get_connection_state() == EngineClientConnectionState.CONNECTED:
            self._engine_data = engine_data
            self._runner.start()
        else:
            raise RemoteEngineFailed("Connecting to server failed. Check Remote "
                                     "Execution settings in File->Settings->Engine.")

    def stop_engine(self):
        """Stops EngineClient and _runner threads."""
        if self.engine_client is not None:
            self.engine_client.close()
        if self._runner.is_alive():
            self._runner.join()

    def close(self):
        """Closes client and thread."""
        self.stop_engine()

    def _run(self):
        """Sends the project zip file and settings to the server for
        execution and waits for a response. Parses the response
        message(s) and puts them into a queue for further processing.
        """
        start_time = round(time.time() * 1000.0)
        engine_data_json = json.dumps(self._engine_data)  # Transform dictionary to JSON string
        zip_fpath = os.path.abspath(
            os.path.join(self._engine_data["project_dir"], os.pardir, PROJECT_ZIP_FILENAME + ".zip")
        )
        # Send an execute request to remote server, and wait for an execution started response
        start_event = self.engine_client.send(engine_data_json, zip_fpath)
        if start_event[0] != "remote_execution_started":
            print(f"Unknown remote engine start response: {start_event}")
            print(f"Execution failed to start: {start_event}")
            self.q.put(start_event)
            return
        self.engine_client.connect_sub_socket(start_event[1])
        while True:
            # Receive events from a SUB socket
            rcv = self.engine_client.sub_socket.recv_multipart()
            event = json.loads(rcv[1])
            event = EventDataConverter.deconvert_single(event, True)
            try:
                # Handle execution state transformation, see returned data from SpineEngine._process_event()
                data_str = self._add_quotes_to_state_str(event[1])
                data_dict = ast.literal_eval(data_str)  # ast.literal_eval fails if input isn't a Python datatype
                if "item_state" in data_dict.keys():
                    data_dict["item_state"] = self.transform_execution_state(data_dict["item_state"])
                self.q.put((event[0], data_dict))
            except ValueError:
                # ast.literal_eval throws this if trying to turn a regular string like "COMPLETED" or "FAILED" to
                # a dict. See returned data from SpineEngine._process_event()
                self.q.put((event[0], event[1]))
            if event[0] == "dag_exec_finished":
                break
        stop_time = round(time.time() * 1000.0)
        print("RemoteSpineEngineManager.run() run time after execution %d ms" % (stop_time - start_time))

    @staticmethod
    def transform_execution_state(state):
        """Transforms state string into an ItemExecutionFinishState enum.

        Args:
            state (str): State as string

        Returns:
            ItemExecutionFinishState: Enum if given str is valid, None otherwise.
        """
        states = dict()
        states["<ItemExecutionFinishState.SUCCESS: 1>"] = ItemExecutionFinishState.SUCCESS
        states["<ItemExecutionFinishState.FAILURE: 1>"] = ItemExecutionFinishState.FAILURE
        states["<ItemExecutionFinishState.SKIPPED: 1>"] = ItemExecutionFinishState.SKIPPED
        states["<ItemExecutionFinishState.EXCLUDED: 1>"] = ItemExecutionFinishState.EXCLUDED
        states["<ItemExecutionFinishState.STOPPED: 1>"] = ItemExecutionFinishState.STOPPED
        states["<ItemExecutionFinishState.NEVER_FINISHED: 1>"] = ItemExecutionFinishState.NEVER_FINISHED
        return states.get(state, None)

    @staticmethod
    def _add_quotes_to_state_str(s):
        """Makes string ready for ast.literal_eval() by adding quotes around item_state value.
        The point of this method is to add quotes (') around item_state value. E.g.
        'item_state': <ItemExecutionFinishState.SUCCESS: 1> becomes
        'item_state': '<ItemExecutionFinishState.SUCCESS: 1>' because ast.literal_eval
        fails with a SyntaxError if the string contains invalid Python data types.
        Make sure that quotes (') are not added to other < > enclosed substrings, such as
        <b> or </b>. If there's no match for what we are looking for, this method returns
        the original string."""
        state = s.partition("'item_state': <")[2].partition(">")[0]
        new_s = s.replace("<" + state + ">", "\'<" + state + ">\'")
        return new_s

    def answer_prompt(self, item_name, accepted):
        """See base class."""
        raise NotImplementedError()

    def restart_kernel(self, connection_file):
        """See base class."""
        self._send("restart_kernel", connection_file)

    def shutdown_kernel(self, connection_file):
        """See base class."""
        self._send("shutdown_kernel", connection_file)

    def is_persistent_command_complete(self, persistent_key, command):
        # pylint: disable=import-outside-toplevel
        raise NotImplementedError()

    def issue_persistent_command(self, persistent_key, command):
        """See base class."""
        # TODO: Implementing this needs a new ServerMessage type
        raise NotImplementedError()

    def restart_persistent(self, persistent_key):
        """See base class."""
        raise NotImplementedError()

    def interrupt_persistent(self, persistent_key):
        """See base class."""
        raise NotImplementedError()

    def get_persistent_completions(self, persistent_key, text):
        """See base class."""
        raise NotImplementedError()

    def get_persistent_history_item(self, persistent_key, index):
        """Returns an item from persistent history.

        Args:
            persistent_key (tuple): persistent identifier
            index (int): index of the history item, most recent first

        Returns:
            str: history item or empty string if none
        """
        raise NotImplementedError()


def make_engine_manager(remote_execution_enabled=False):
    """Returns either a Local or a remote Spine Engine Manager based on settings.

    Args:
        remote_execution_enabled (bool): True returns a local Spine Engine Manager instance,
        False returns a remote Spine Engine Manager instance
    """
    if remote_execution_enabled:
        return RemoteSpineEngineManager()
    return LocalSpineEngineManager()


# TODO: This class is in master as the RemoteSpineEngineManager stub. See if _send() can be used.
# class RemoteSpineEngineManager(SpineEngineManagerBase):
#     _ENCODING = "ascii"
#
#     def __init__(self, engine_server_address):
#         """
#         Args:
#             engine_server_address (str)
#         """
#         super().__init__()
#         self._engine_server_address = engine_server_address
#         self.request = None
#         self._engine_id = None
#
#     def run_engine(self, engine_data):
#         """See base class."""
#         self._engine_id = self._send("run_engine", engine_data)
#
#     def get_engine_event(self):
#         """See base class."""
#         return self._send("get_engine_event", self._engine_id)
#
#     def stop_engine(self):
#         """See base class."""
#         self._send("stop_engine", self._engine_id, receive=False)
#
#     def answer_prompt(self, item_name, accepted):
#         """See base class."""
#         raise NotImplementedError()
#
#     def restart_kernel(self, connection_file):
#         """See base class."""
#         self._send("restart_kernel", connection_file)
#
#     def shutdown_kernel(self, connection_file):
#         """See base class."""
#         self._send("shutdown_kernel", connection_file)
#
#     def issue_persistent_command(self, persistent_key, command):
#         """See base class."""
#         raise NotImplementedError()
#
#     def is_persistent_command_complete(self, persistent_key, command):
#         """See base class."""
#         raise NotImplementedError()
#
#     def restart_persistent(self, persistent_key):
#         """See base class."""
#         raise NotImplementedError()
#
#     def interrupt_persistent(self, persistent_key):
#         """See base class."""
#         raise NotImplementedError()
#
#     def get_persistent_completions(self, persistent_key, text):
#         """See base class."""
#         raise NotImplementedError()
#
#     def _send(self, request, *args, receive=True):
#         """
#         Sends a request to the server with the given arguments.
#
#         Args:
#             request (str): One of the supported engine server requests
#             args: Request arguments
#             receive (bool, optional): If True (the default) also receives the response and returns it.
#
#         Returns:
#             str or NoneType: response, or None if receive is False
#         """
#         msg = json.dumps((request, args))
#         with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as self.request:
#             self.request.connect(self._engine_server_address)
#             self.request.sendall(bytes(msg, "ascii"))
#             if receive:
#                 response = self._recvall()
#                 return json.loads(response)
#
#     def _recvall(self):
#         """
#         Receives and returns all data in the current request.
#
#         Returns:
#             str
#         """
#         BUFF_SIZE = 4096
#         fragments = []
#         while True:
#             chunk = str(self.request.recv(BUFF_SIZE), self._ENCODING)
#             fragments.append(chunk)
#             if len(chunk) < BUFF_SIZE:
#                 break
#         return "".join(fragments)
