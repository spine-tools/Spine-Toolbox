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
import queue
import threading
import time
import json
import ast
import os
from enum import Enum
from spinetoolbox.server.util.file_packager import FilePackager
from spinetoolbox.server.connectivity.zmq_client import ZMQClient, ZMQSecurityModelState, ZMQClientConnectionState
from spine_engine.spine_engine import ItemExecutionFinishState
from spine_engine.exception import RemoteEngineFailed


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

    def get_persistent_history_item(self, persistent_key, index):
        """Returns an item from persistent history.

        Args:
            persistent_key (tuple): persistent identifier
            index (int): index of the history item, most recent first

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

    def get_persistent_history_item(self, persistent_key, index):
        # pylint: disable=import-outside-toplevel
        from spine_engine.execution_managers.persistent_execution_manager import get_persistent_history_item

        return get_persistent_history_item(persistent_key, index)


class RemoteSpineEngineManager(SpineEngineManagerBase):
    """Responsible for remote project execution."""

    ZipFileName = "project_package"  # ZIP-file name to be used

    def __init__(self):
        """Initializer."""
        super().__init__()
        self._runner = threading.Thread(name="RemoteSpineEngineManagerRunnerThread", target=self._run)
        self._requestPending = False
        self._inputData = None
        self._state = RemoteSpineEngineManagerState.IDLE
        self._outputData = None
        self._outputDataIteratorIndex = 0
        self.zmq_client = None
        self.engine_event_getter_thread = None

    def run_engine(self, engine_data):
        """Establishes a connection to server using a ZMQ client. Starts a thread, where
        the current DAG is packaged into a zip file and then sent to the server for
        execution.

        Args:
            engine_data (dict): The engine data.
        """
        if self._state == RemoteSpineEngineManagerState.IDLE and not self._requestPending:
            app_settings = engine_data["settings"]
            protocol = "tcp"  # Zero-MQ protocol. Hardcoded to tcp for now.
            host = app_settings.get("engineSettings/remoteHost", "")  # Host name
            port = app_settings.get("engineSettings/remotePort", "49152")  # Host port
            sec_model = app_settings.get("engineSettings/remoteSecurityModel", "")  # ZQM security model
            security = ZMQSecurityModelState.NONE if not sec_model else ZMQSecurityModelState.STONEHOUSE
            sec_folder = (
                ""
                if security == ZMQSecurityModelState.NONE
                else app_settings.get("engineSettings/remoteSecurityFolder", "")
            )
            if not host:
                raise RemoteEngineFailed("Engine server host name missing.")
            self.engine_event_getter_thread = RemoteEngineEventGetter(self._state)
            try:
                self.zmq_client = ZMQClient(protocol, host, port, security, sec_folder)
            except ValueError as e:
                raise RemoteEngineFailed(f"Initializing ZMQ client failed: {e}")
            if self.zmq_client.getConnectionState() == ZMQClientConnectionState.CONNECTED:
                self._requestPending = True
                self._inputData = engine_data
                self._runner.start()
            else:
                self._state = RemoteSpineEngineManagerState.CLOSED
                raise RemoteEngineFailed("Connecting to server failed. Check Remote "
                                         "Execution settings in File->Settings->Engine.")
        else:
            raise RemoteEngineFailed(f"Remote execution failed. state:{self._state}. "
                                     f"self._requestPending:{self._requestPending}")

    def stop_engine(self):
        """Stops engine currently running."""
        self._state = RemoteSpineEngineManagerState.CLOSED
        if self._runner.is_alive():
            self._runner.join()
        if self.zmq_client is not None:
            self.zmq_client.close()
        print("RemoteSpineEngineManager.stop_engine()")

    def close(self):
        """Closes zmq_client and _runner thread when execution has finished."""
        self._state = RemoteSpineEngineManagerState.CLOSED
        self.zmq_client.close()
        if self._runner.is_alive():
            self._runner.join()
        print(f"ZMQ client and {self._runner.name} have been closed")

    def _run(self):
        """Packs the project into a zip file, sends the zip file and settings
        to the server for execution and waits for the response. Parses the
        response message(s) and puts them into a queue for further processing.
        Deletes the zip file after execution."""
        while self._state != RemoteSpineEngineManagerState.CLOSED:
            # run request
            if self._requestPending and self._state == RemoteSpineEngineManagerState.IDLE:
                start_time = round(time.time() * 1000.0)
                self._state = RemoteSpineEngineManagerState.RUNNING  # Change state to RUNNING
                json_txt = json.dumps(self._inputData)  # Transform dict to JSON string
                # Make a zip file containing the project (or DAG) to be executed remotely
                FilePackager.package(
                    self._inputData['project_dir'],
                    self._inputData['project_dir'],
                    RemoteSpineEngineManager.ZipFileName,
                )
                # Send a request to remote server, and wait for a response
                data_events = self.zmq_client.send(
                    json_txt, self._inputData['project_dir'], RemoteSpineEngineManager.ZipFileName + ".zip"
                )
                self.engine_event_getter_thread.server_output_msg_q.put(data_events)
                # Delete the transmitted zip file
                FilePackager.deleteFile(
                    os.path.abspath(
                        os.path.join(self._inputData['project_dir'], RemoteSpineEngineManager.ZipFileName + ".zip")))
                stop_time = round(time.time() * 1000.0)
                print("RemoteSpineEngineManager.run() run time after execution %d ms" % (stop_time - start_time))
                self._state = RemoteSpineEngineManagerState.REPLY_RECEIVED  # Change state to REPLY_RECEIVED
                self.engine_event_getter_thread._state = RemoteSpineEngineManagerState.REPLY_RECEIVED
                self._requestPending = False
            else:
                time.sleep(0.01)
        print(f"Closing thread {self._runner.name}")

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
        # TODO: Implementing this needs a new ServerMessage type (with 'execute' and 'ping')
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


class RemoteEngineWorker(threading.Thread):
    def __init__(self):
        super().__init__()


class RemoteEngineEventGetter(threading.Thread):
    def __init__(self, start_state):
        super().__init__(name="RemoteEngineEventGetterThread")
        self._state = start_state
        self.server_output_msg_q = queue.Queue()  # Queue for messages from remote server
        self.output_iterator_index_q = 0
        self.q = queue.Queue()  # Queue for sending data forward to SpineEngineWorker
        self.start()

    def run(self):
        """Former get_engine_event(). Gets next event from engine currently running.

        Returns:
            tuple(str,dict): two element tuple: event type identifier string, and event data dictionary
        """
        while True:
            if self._state == RemoteSpineEngineManagerState.REPLY_RECEIVED:
                output_data = self.server_output_msg_q.get()
                output_data_iterator_index = 0
                print(f"REPLY_RECEIVED. output_data:{output_data}")
                if isinstance(output_data, str):
                    # Error happened on server
                    self.q.put(("remote_engine_failed", output_data))
                    self._state = RemoteSpineEngineManagerState.CLOSED
                    break
                for event in output_data:
                    # output_data is a list of tuples
                    # event is eg. ('exec_started', "{'item_name': 'DC', 'direction': 'BACKWARD'}")
                    try:
                        # handle execution state transformation, see returned data from SpineEngine._process_event()
                        if event[1].find('\'item_state\': <') != -1:
                            data_dict = self.transform_execution_state(event[1])
                        else:
                            data_dict = ast.literal_eval(event[1])
                        self.q.put((event[0], data_dict))
                    # this exception is needed due to status code return (not a dict string), see: SpineEngine._process_event()
                    except Exception as e:
                        if event[1].find('{') == -1:
                            print("RemoteEngineEventGetter.run() Handled exception in parsing, returning a status code.")
                            self.q.put((event[0], event[1]))
                        else:
                            print("RemoteEngineEventGetter.run() Failure in parsing,returning empty..")
                            self.q.put((None, None))
                self._state = RemoteSpineEngineManagerState.CLOSED
                break
            else:
                # print("get_engine_event(): returning empty tuple, reply has not been received yet.")
                time.sleep(0.01)
        print(f"thread {self.name} closed")

    def transform_execution_state(self, data):
        # first add quotes around execution state
        quotedStr = self._add_quotes_to_dict_string(data)
        tempDict = ast.literal_eval(quotedStr)
        stateStr = tempDict['item_state']
        state = None
        # transform string state into enum
        if stateStr == '<ItemExecutionFinishState.SUCCESS: 1>':
            state = ItemExecutionFinishState.SUCCESS
        elif stateStr == '<ItemExecutionFinishState.FAILURE: 2>':
            state = ItemExecutionFinishState.FAILURE
        elif stateStr == '<ItemExecutionFinishState.SKIPPED: 3>':
            state = ItemExecutionFinishState.SKIPPED
        elif stateStr == '<ItemExecutionFinishState.EXCLUDED: 4>':
            state = ItemExecutionFinishState.EXCLUDED
        elif stateStr == '<ItemExecutionFinishState.STOPPED: 5>':
            state = ItemExecutionFinishState.STOPPED
        elif stateStr == '<ItemExecutionFinishState.NEVER_FINISHED: 6>':
            state = ItemExecutionFinishState.NEVER_FINISHED
        if state is not None:
            tempDict['item_state'] = state
            return tempDict
        else:
            print("RemoteEngineEventGetter.transform_execution_state() Failure in parsing")
            return tempDict

    @staticmethod
    def _add_quotes_to_dict_string(s):
        new_str = s.replace('\': <', '\': \'<')
        ret_str = new_str.replace('}', '\'}')
        return ret_str


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
