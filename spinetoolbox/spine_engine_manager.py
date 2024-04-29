######################################################################################################################
# Copyright (C) 2017-2022 Spine project consortium
# Copyright Spine Toolbox contributors
# This file is part of Spine Items.
# Spine Items is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""Contains SpineEngineManagerBase."""
import queue
import threading
import json
from spine_engine.exception import RemoteEngineInitFailed
from spine_engine.server.util.event_data_converter import EventDataConverter
from spinetoolbox.server.engine_client import EngineClient, ClientSecurityModel


class SpineEngineManagerBase:
    def run_engine(self, engine_data):
        """Runs an engine with given data.

        Args:
            engine_data (dict): The engine data.
        """
        raise NotImplementedError()

    def get_engine_event(self):
        """Gets next event from a running engine.

        Returns:
            tuple(str,dict): two element tuple: event type identifier string, and event data dictionary
        """
        raise NotImplementedError()

    def stop_engine(self):
        """Stops a running engine."""
        raise NotImplementedError()

    def answer_prompt(self, prompter_id, answer):
        """Answers prompt.

        Args:
            prompter_id (int): The id of the prompter
            answer: The user's decision.
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
        """Checks whether a command is complete.

        Args:
            key (tuple): persistent identifier
            cmd (str): command to issue

        Returns:
            bool
        """
        raise NotImplementedError()

    def restart_persistent(self, persistent_key):
        """Restarts a persistent process.

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

    def kill_persistent(self, persistent_key):
        """Kills a persistent process.

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
        if self._engine is not None:
            self._engine.stop()

    def answer_prompt(self, prompter_id, answer):
        self._engine.answer_prompt(prompter_id, answer)

    def restart_kernel(self, connection_file):
        # pylint: disable=import-outside-toplevel
        from spine_engine.execution_managers.kernel_execution_manager import restart_kernel_manager

        return restart_kernel_manager(connection_file)

    def shutdown_kernel(self, connection_file):
        # pylint: disable=import-outside-toplevel
        from spine_engine.execution_managers.kernel_execution_manager import shutdown_kernel_manager

        return shutdown_kernel_manager(connection_file)

    def kernel_managers(self):
        # pylint: disable=import-outside-toplevel
        from spine_engine.execution_managers.kernel_execution_manager import n_kernel_managers

        return n_kernel_managers()

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

    def kill_persistent(self, persistent_key):
        # pylint: disable=import-outside-toplevel
        from spine_engine.execution_managers.persistent_execution_manager import kill_persistent

        kill_persistent(persistent_key)

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

    def __init__(self, job_id=""):
        """Initializer."""
        super().__init__()
        self._runner = threading.Thread(name="RemoteSpineEngineManagerRunnerThread", target=self._run)
        self._engine_data = None
        self.engine_client = None
        self.job_id = job_id  # Job Id of ProjectExtractionService for finding the extracted project on server
        self.exec_job_id = ""  # Job Id of RemoteExecutionService for stopping the execution
        self.q = queue.Queue()  # Queue for sending events forward to SpineEngineWorker

    def make_engine_client(self, host, port, security, sec_folder, ping=True):
        """Creates a client for connecting to Spine Engine Server."""
        try:
            self.engine_client = EngineClient(host, port, security, sec_folder, ping)
        except RemoteEngineInitFailed:
            raise
        except Exception:
            raise

    def run_engine(self, engine_data):
        """Makes an engine client for communicating with the engine server.
        Starts a thread for monitoring the DAG execution on server.

        Args:
            engine_data (dict): The engine data.
        """
        app_settings = engine_data["settings"]
        host = app_settings.get("engineSettings/remoteHost", "")  # Host name
        port = app_settings.get("engineSettings/remotePort", "49152")  # Host port
        sec_model = app_settings.get("engineSettings/remoteSecurityModel", "")  # ZQM security model
        security = ClientSecurityModel.NONE if not sec_model else ClientSecurityModel.STONEHOUSE
        sec_folder = (
            "" if security == ClientSecurityModel.NONE else app_settings.get("engineSettings/remoteSecurityFolder", "")
        )
        self.make_engine_client(host, port, security, sec_folder)
        self._engine_data = engine_data
        self._runner.start()

    def get_engine_event(self):
        """Returns the next engine execution event."""
        return self.q.get()

    def clean_up(self):
        """Closes EngineClient and joins _runner thread if still active."""
        self.engine_client.close()
        if self._runner.is_alive():
            self._runner.join()

    def stop_engine(self):
        """Sends a request to stop execution on Server then waits for _runner thread to end."""
        if self._runner.is_alive():
            self.engine_client.stop_execution(self.exec_job_id)
            self._runner.join()

    def _run(self):
        """Sends a start execution request to server with the job Id.
        Sets up a subscribe socket according to the publish port received from server.
        Passes received events to SpineEngineWorker for processing. After execution
        has finished, downloads new files from server.
        """
        self.engine_client.client_project_dir = self._engine_data["project_dir"]
        engine_data_json = json.dumps(self._engine_data)  # Transform dictionary to JSON string
        # Send request to server, and wait for an execution started response containing the publish port
        start_response_data = self.engine_client.start_execution(engine_data_json, self.job_id)
        if start_response_data[0] != "remote_execution_started":
            # Initializing the server for execution failed. 'remote_execution_init_failed' and 'server_init_failed'
            # are handled in SpineEngineWorker.
            self.q.put(
                (
                    "server_status_msg",
                    {
                        "msg_type": "fail",
                        "text": f"Server init failed: event_type:{start_response_data[0]} "
                        f"data:{start_response_data[1]}. Aborting.",
                    },
                )
            )
            self.q.put(start_response_data)
            return
        self.exec_job_id = start_response_data[2]  # Needed for stopping DAG execution on server
        self.engine_client.connect_pull_socket(start_response_data[1])
        while True:  # Pull events until dag_exec_finished event
            rcv = self.engine_client.rcv_next("pull")
            event = EventDataConverter.deconvert(*rcv)  # Unpack list
            if event[0] == "dag_exec_finished":
                # Download all files before sending 'dag_exec_finished' to SpineEngineWorker
                # because it will destroy this thread before the file transfers have finished.
                if event[1] == "COMPLETED":
                    self.engine_client.download_files(self.q)
                t = self.engine_client.get_elapsed_time()
                self.q.put(("server_status_msg", {"msg_type": "success", "text": f"Execution time: {t}"}))
                self.q.put(event)
                break
            elif event[0] == "server_execution_error":
                # spine engine raised an exception during execution
                self.q.put(("server_status_msg", {"msg_type": "fail", "text": f"{event[0]: {event[1]}}"}))
                break
            else:
                self.q.put(event)
        self.engine_client.close()

    def answer_prompt(self, prompter_id, answer):
        """See base class."""
        self.engine_client.answer_prompt(self.exec_job_id, prompter_id, answer)

    def restart_kernel(self, connection_file):
        """See base class."""
        # TODO: This does not restart the kernel, only replaces the client. Do kernel_manager.restart_kernel() on server
        pass

    def shutdown_kernel(self, connection_file):
        """See base class."""
        pass

    def is_persistent_command_complete(self, persistent_key, command):
        return self.engine_client.send_is_complete(persistent_key, command)

    def issue_persistent_command(self, persistent_key, command):
        return self.engine_client.send_issue_persistent_command(persistent_key, command)

    def restart_persistent(self, persistent_key):
        """See base class."""
        return self.engine_client.send_restart_persistent(persistent_key)

    def interrupt_persistent(self, persistent_key):
        """See base class."""
        return self.engine_client.send_interrupt_persistent(persistent_key)

    def kill_persistent(self, persistent_key):
        """See base class."""
        return self.engine_client.send_kill_persistent(persistent_key)

    def get_persistent_completions(self, persistent_key, text):
        """See base class."""
        return self.engine_client.send_get_persistent_completions(persistent_key, text)

    def get_persistent_history_item(self, persistent_key, text, prefix, backwards):
        """Returns an item from persistent history.

        Args:
            persistent_key (tuple): persistent identifier

        Returns:
            str: history item or empty string if none
        """
        return self.engine_client.send_get_persistent_history_item(persistent_key, text, prefix, backwards)


def make_engine_manager(remote_execution_enabled=False, job_id=""):
    """Returns either a Local or a remote Spine Engine Manager based on settings.

    Args:
        remote_execution_enabled (bool): True returns a local Spine Engine Manager instance,
        False returns a remote Spine Engine Manager instance
        job_id (str): Server execution job Id
    """
    if remote_execution_enabled:
        return RemoteSpineEngineManager(job_id)
    return LocalSpineEngineManager()
