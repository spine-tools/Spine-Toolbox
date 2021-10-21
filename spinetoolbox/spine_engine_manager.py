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

import socket
import threading
import time
import json
import ast
import os
from enum import Enum
from spinetoolbox.server.util.FilePackager import FilePackager
from spinetoolbox.server.connectivity.ZMQClient import ZMQClient, ZMQSecurityModelState, ZMQClientConnectionState
from spine_engine.spine_engine import ItemExecutionFinishState
from spine_engine.exception import EngineInitFailed


class RemoteSpineEngineManagerState2(Enum):
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
            generator: stdio and stderr messages (dictionaries with two keys: type, and data)
        """
        raise NotImplementedError()

    def restart_persistent(self, persistent_key):
        """Restart a persistent process.

        Args:
            persistent_key (tuple): persistent identifier
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

    def answer_prompt(self, item_name, accepted):
        """See base class."""
        raise NotImplementedError()

    def restart_kernel(self, connection_file):
        """See base class."""
        self._send("restart_kernel", connection_file)

    def shutdown_kernel(self, connection_file):
        """See base class."""
        self._send("shutdown_kernel", connection_file)

    def issue_persistent_command(self, persistent_key, command):
        """See base class."""
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

    def restart_persistent(self, persistent_key):
        # pylint: disable=import-outside-toplevel
        from spine_engine.execution_managers.persistent_execution_manager import restart_persistent

        restart_persistent(persistent_key)

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


class RemoteSpineEngineManager2(SpineEngineManagerBase, threading.Thread):
    """Responsible for remote project execution."""

    ZipFileName = "project_package"  # ZIP-file name to be used

    def __init__(self, app_settings):
        """Initializer.

        Args:
            app_settings (dict): Application settings
        """
        protocol = "tcp"  # Zero-MQ protocol
        host = app_settings.get("appSettings/remoteHost", "")  # Host name
        port = app_settings.get("appSettings/remotePort", "49152")  # Host port
        sec_model = app_settings.get("appSettings/remoteSecurityModel", "")  # ZOM security model
        security = ZMQSecurityModelState.NONE if not sec_model else ZMQSecurityModelState.STONEHOUSE
        sec_folder = "" if security == ZMQSecurityModelState.NONE else \
            app_settings.get("appSettings/remoteSecurityDirectory", "")
        if not host:
            raise ValueError("Engine server host name missing in RemoteSpineEngineManager2.")
        threading.Thread.__init__(self)
        self.zmq_client = ZMQClient(protocol, host, port, security, sec_folder)

        if self.zmq_client.getConnectionState()==ZMQClientConnectionState.CONNECTED:
            self._state = RemoteSpineEngineManagerState2.IDLE
            self._requestPending = False
            self._inputData = None
            self._outputData = None
            self._outputDataIteratorIndex = 0
            self.start()
        else:
            self._state = RemoteSpineEngineManagerState2.CLOSED
            print("RemoteSpineEngineManager2.__init__(): Client is disconnected from the server, check Remote "
                  "execution configuration (File->Settings->Remote execution)!")

    def run_engine(self, engine_data):
        """Runs an engine with given data.

        Args:
            engine_data (dict): The engine data.
        """
        if self._state == RemoteSpineEngineManagerState2.IDLE and not self._requestPending:
            self._inputData = engine_data
            self._requestPending = True
            # print("RemoteSpineEngineManager2.run_engine(): Pending request execution..")
        else:
            # print("RemoteSpineEngineManager2.run_engine(): Cannot execute due to pending request or state: %s"%str(self._state))
            raise EngineInitFailed()

    def get_engine_event(self):
        """Gets next event from engine currently running.

        Returns:
            tuple(str,dict): two element tuple: event type identifier string, and event data dictionary
        """
        if self._state == RemoteSpineEngineManagerState2.REPLY_RECEIVED:
            eventData = self._outputData[self._outputDataIteratorIndex]
            self._outputDataIteratorIndex += 1
            if self._outputDataIteratorIndex == len(self._outputData):
                # print("get_engine_event() all events+data has been received, returning to CLOSED")
                self._state = RemoteSpineEngineManagerState2.CLOSED
            try:
                dataDict = dict()
                # print("get_engine_event() transforming data: %s"%eventData[1])
                # handle execution state transformation, see returned data from SpineEngine._process_event()
                if eventData[1].find('\'item_state\': <') != -1:
                    dataDict = self._transformExecutionState(eventData[1])
                else:
                    dataDict = ast.literal_eval(eventData[1])
                # dataDict=json.loads(eventData[1])
                # print(type(dataDict))
                # print("get_engine_event() returning: event: %s, data: %s"%(eventData[0],dataDict))
                return (eventData[0], dataDict)
            # this exception is needed due to status code return (not a dict string), see: SpineEngine._process_event()
            except Exception as e:
                if eventData[1].find('{') == -1:
                    # print("get_engine_event() Handled exception in parsing, returning a status code.")
                    return (eventData[0], eventData[1])
                else:  
                    # print(e)
                    # print("event data: %s;%s"%(eventData[0], eventData[1]))
                    print("get_engine_event() Failure in parsing,returning empty..")
                    return (None, None)
        else:
            # print("get_engine_event(): returning empty tuple, reply has not been received yet.")
            return (None, None)

    def stop_engine(self):
        """Stops engine currently running."""
        self._state=RemoteSpineEngineManagerState2.CLOSED
        self.zmq_client.close()
        print("RemoteSpineEngineManager2.stop_engine()")

    def run(self):
        while self._state != RemoteSpineEngineManagerState2.CLOSED:
            # run request
            if self._requestPending and self._state == RemoteSpineEngineManagerState2.IDLE:
                # debugging
                runStartTimeMs = round(time.time()*1000.0)
                # change state
                # print("RemoteSpineEngineManager2.run() Started running..")
                self._state = RemoteSpineEngineManagerState2.RUNNING
                # transform dict to JSON string
                jsonTxt = json.dumps(self._inputData)
                # print("RemoteSpineEngineManager2.run() Sending data: %s"%jsonTxt)
                runStartTimeMs = round(time.time()*1000.0)
                # Debugging
                runStopTimeMs = round(time.time()*1000.0)
                print("RemoteSpineEngineManager2.run() run time after JSON encoding %d ms"%(runStopTimeMs-runStartTimeMs))
                runStartTimeMs = round(time.time()*1000.0)
                # get folder from input data, and package it
                print("RemoteSpineEngineManager2.run() Packaging folder %s.."%self._inputData['project_dir'])
                FilePackager.package(
                    self._inputData['project_dir'],
                    self._inputData['project_dir'],
                    RemoteSpineEngineManager2.ZipFileName
                )
                # Debugging
                runStopTimeMs = round(time.time()*1000.0)
                print("RemoteSpineEngineManager2.run() run time after packaging %d ms"%(runStopTimeMs-runStartTimeMs))
                runStartTimeMs = round(time.time()*1000.0)
                # send request to the remote client, and listen for a response
                dataEvents = self.zmq_client.send(
                    jsonTxt,
                    self._inputData['project_dir'],
                    RemoteSpineEngineManager2.ZipFileName + ".zip"
                )
                # print("RemoteSpineEngineManager2.run() received a response:")
                # print(dataEvents)
                # print("RemoteSpineEngineManager2.run() %d of event+data items received."%len(dataEvents))
                self._outputData = dataEvents
                self._outputDataIteratorIndex = 0
                # remove the transferred ZIP-file
                FilePackager.deleteFile(
                    os.path.join(self._inputData['project_dir'], RemoteSpineEngineManager2.ZipFileName + ".zip")
                )
                # debugging
                runStopTimeMs = round(time.time()*1000.0)
                print("RemoteSpineEngineManager2.run() duration of transfer %d ms"%(runStopTimeMs-runStartTimeMs))
                # change state to REPLY_RECEIVED
                self._state = RemoteSpineEngineManagerState2.REPLY_RECEIVED
                self._requestPending = False
            else:
                time.sleep(0.01)
        self.zmq_client.close()

    def _transformExecutionState(self, data):
        # first add quotes around execution state
        # print("RemoteSpineEngineManager2._transformExecutionState() with data %s"%data)
        quotedStr = self._add_quotes_to_dict_string(data)
        # print("RemoteSpineEngineManager2._transformExecutionState() Quoted str: %s"%quotedStr)
        tempDict = ast.literal_eval(quotedStr)
        stateStr = tempDict['item_state']
        # print("RemoteSpineEngineManager2._transformExecutionState() state str: %s"%stateStr)
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
            # print("RemoteSpineEngineManager2._transformExecutionState() Returning transformed dict:")
            # print(tempDict)
            return tempDict
        else:
            print("RemoteSpineEngineManager2._transformExecutionState() Failure in parsing")
            return tempDict

    @staticmethod
    def _add_quotes_to_dict_string(s):
        new_str = s.replace('\': <', '\': \'<')
        ret_str = new_str.replace('}', '\'}')
        return ret_str


def make_engine_manager(app_settings):
    """Returns either a Local or a remote Spine Engine Manager based on settings.

    Args:
        app_settings (dict): Application settings
    """
    if app_settings.get("appSettings/remoteExecutionEnabled", "false") == "false":
        return LocalSpineEngineManager()
    return RemoteSpineEngineManager2(app_settings)
