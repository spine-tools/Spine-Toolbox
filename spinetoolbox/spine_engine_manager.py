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

    def is_persistent_command_complete(self, persistent_key, command):
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


def make_engine_manager(engine_server_address):
    if not engine_server_address:
        return LocalSpineEngineManager()
    return RemoteSpineEngineManager(engine_server_address)
