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

"""Contains SpineEngineWorker."""
import copy
from PySide6.QtCore import Signal, Slot, QObject, QThread
from spine_engine.exception import EngineInitFailed, RemoteEngineInitFailed
from spine_engine.spine_engine import ItemExecutionFinishState, SpineEngineState
from .widgets.options_dialog import OptionsDialog
from .spine_engine_manager import make_engine_manager, LocalSpineEngineManager


@Slot(list)
def _handle_dag_execution_started(project_items):
    for item in project_items:
        item.get_icon().execution_icon.mark_execution_waiting()


@Slot(list)
def _handle_node_execution_ignored(project_items):
    for item in project_items:
        item.get_icon().execution_icon.mark_execution_ignored()


@Slot(object, object)
def _handle_node_execution_started(item, direction):
    icon = item.get_icon()
    if direction == "FORWARD":
        icon.execution_icon.mark_execution_started()
        if hasattr(icon, "animation_signaller"):
            icon.animation_signaller.animation_started.emit()


@Slot(object, object, object, object)
def _handle_node_execution_finished(item, direction, item_state):
    icon = item.get_icon()
    if direction == "FORWARD":
        icon.execution_icon.mark_execution_finished(item_state)
        if hasattr(icon, "animation_signaller"):
            icon.animation_signaller.animation_stopped.emit()


@Slot(object, str, str)
def _handle_event_message_arrived(item, filter_id, msg_type, msg_text):
    item.add_event_message(filter_id, msg_type, msg_text)


@Slot(object, str, str)
def _handle_process_message_arrived(item, filter_id, msg_type, msg_text):
    item.add_process_message(filter_id, msg_type, msg_text)


@Slot(dict, object)
def _handle_prompt_arrived(prompt, engine_mngr, logger=None):
    prompter_id = prompt["prompter_id"]
    title, text, option_to_answer, notes, preferred = prompt["data"]
    answer = OptionsDialog.get_answer(logger, title, text, option_to_answer, notes=notes, preferred=preferred)
    engine_mngr.answer_prompt(prompter_id, answer)


@Slot(object)
def _handle_flash_arrived(connection):
    connection.graphics_item.run_execution_animation()


@Slot(list)
def _mark_all_items_failed(items):
    """Fails all project items.

    Args:
        items (list of ProjectItem): project items
    """
    for item in items:
        icon = item.get_icon()
        icon.execution_icon.mark_execution_finished(ItemExecutionFinishState.FAILURE)
        if hasattr(icon, "animation_signaller"):
            icon.animation_signaller.animation_stopped.emit()


class SpineEngineWorker(QObject):
    finished = Signal()
    _mark_items_ignored = Signal(list)
    _dag_execution_started = Signal(list)
    _node_execution_started = Signal(object, object)
    _node_execution_finished = Signal(object, object, object)
    _event_message_arrived = Signal(object, str, str, str)
    _process_message_arrived = Signal(object, str, str, str)
    _prompt_arrived = Signal(dict, object, object)
    _flash_arrived = Signal(object)
    _all_items_failed = Signal(list)

    def __init__(self, engine_data, dag, dag_identifier, project_items, connections, logger, job_id):
        """
        Args:
            engine_data (dict): engine data
            dag (DirectedGraphHandler):
            dag_identifier (str):
            project_items (dict): mapping from project item name to :class:`ProjectItem`
            connections (dict): mapping from jump name to :class:`LoggingConnection` or :class:`LoggingJump`
            logger (LoggerInterface): a logger
            job_id (str): Job id for remote execution
        """
        super().__init__()
        self._engine_data = engine_data
        exec_remotely = engine_data["settings"].get("engineSettings/remoteExecutionEnabled", "false") == "true"
        self._job_id = job_id
        self._engine_mngr = make_engine_manager(exec_remotely, job_id)
        self.dag = dag
        self.dag_identifier = dag_identifier
        self._engine_final_state = "UNKNOWN"
        self._executing_items = set()
        self._project_items = project_items
        self._connections = connections
        self._logger = logger
        self.event_messages = {}
        self.process_messages = {}
        self.successful_executions = []
        self._thread = QThread()
        self.moveToThread(self._thread)
        self._thread.started.connect(self.do_work)

    @property
    def job_id(self):
        return self._job_id

    @property
    def engine_data(self):
        """Engine data dictionary."""
        return self._engine_data

    def get_engine_data(self):
        """Returns the engine data. Together with ``self.set_engine_data()`` it can be used to modify
        the workflow after it's initially created. We use it at the moment for creating Julia sysimages.

        Returns:
            dict
        """
        return copy.deepcopy(self._engine_data)

    def set_engine_data(self, engine_data):
        """Sets the engine data.

        Args:
            engine_data (dict): New data
        """
        self._engine_data = engine_data

    @Slot(object, str, str)
    def _handle_event_message_arrived_silent(self, item, filter_id, msg_type, msg_text):
        self.event_messages.setdefault(msg_type, []).append(msg_text)

    @Slot(object, str, str)
    def _handle_process_message_arrived_silent(self, item, filter_id, msg_type, msg_text):
        self.process_messages.setdefault(msg_type, []).append(msg_text)

    def stop_engine(self):
        self._engine_mngr.stop_engine()

    def engine_final_state(self):
        return self._engine_final_state

    def thread(self):
        return self._thread

    def _connect_log_signals(self, silent):
        if silent:
            self._event_message_arrived.connect(self._handle_event_message_arrived_silent)
            self._process_message_arrived.connect(self._handle_process_message_arrived_silent)
            return
        self._mark_items_ignored.connect(_handle_node_execution_ignored)
        self._dag_execution_started.connect(_handle_dag_execution_started)
        self._node_execution_started.connect(_handle_node_execution_started)
        self._node_execution_finished.connect(_handle_node_execution_finished)
        self._event_message_arrived.connect(_handle_event_message_arrived)
        self._process_message_arrived.connect(_handle_process_message_arrived)
        self._prompt_arrived.connect(_handle_prompt_arrived)
        self._flash_arrived.connect(_handle_flash_arrived)

    def start(self, silent=False):
        """Connects log signals.

        Args:
            silent (bool, optional): If True, log messages are not forwarded to the loggers
                but saved in internal dicts.
        """
        self._connect_log_signals(silent)
        self._all_items_failed.connect(_mark_all_items_failed)
        included_items, ignored_items = self._included_and_ignored_items()
        self._dag_execution_started.emit(included_items)
        self._mark_items_ignored.emit(ignored_items)
        self._thread.start()

    def _included_and_ignored_items(self):
        """Returns two lists, where the first one contains project items that are about to be executed and the second
        one contains project items that are about to be ignored."""
        included = self._included_items(self.engine_data["execution_permits"], self.engine_data["connections"])
        included_items = [item_dict for name, item_dict in self._project_items.items() if name in included]
        ignored_items = [item_dict for name, item_dict in self._project_items.items() if name not in included]
        return included_items, ignored_items

    def _included_items(self, permitted_items, connections):
        """Collects a list of project item names that are going to be executed in this DAG
        based on execution permits and connections in the DAG.

        Args:
            permitted_items (dict): Mapping of item names to bool. True items have been selected by user for execution.
            connections (list): Serialized connections

        Returns:
            list: Project item names
        """
        selected_items = [name for name, item_dict in self._project_items.items() if permitted_items[name]]
        i_names = set()  # Names of items that are connected to permitted items
        for conn in connections:
            src_item = conn["from"][0]
            dst_item = conn["to"][0]
            if src_item in selected_items or dst_item in selected_items:
                i_names.add(src_item)
                i_names.add(dst_item)
        if not i_names:  # Single node DAG with no connections
            return selected_items
        return list(i_names)

    @Slot()
    def do_work(self):
        """Does the work and emits finished when done."""
        try:
            self._engine_mngr.run_engine(self._engine_data)
        except EngineInitFailed as error:
            self._logger.msg_error.emit(f"Failed to start engine: {error}")
            self._engine_final_state = str(SpineEngineState.FAILED)
            self._all_items_failed.emit(list(self._project_items.values()))
            self.finished.emit()
            return
        except RemoteEngineInitFailed as e:
            self._logger.msg_error.emit(
                f"Server is not responding. {e}. Check settings " f"in <b>File->Settings->Engine</b>."
            )
            self._engine_final_state = str(SpineEngineState.FAILED)
            self._all_items_failed.emit(list(self._project_items.values()))
            self.finished.emit()
            return
        while True:
            event_type, data = self._engine_mngr.get_engine_event()
            self._process_event(event_type, data)
            if event_type == "dag_exec_finished":
                self._engine_final_state = data
                break
            if event_type in ("remote_execution_init_failed", "server_init_failed"):
                self._logger.msg_error.emit(f"{data}")
                self._engine_final_state = str(SpineEngineState.FAILED)
                self._all_items_failed.emit(list(self._project_items.values()))
                break
        self.finished.emit()

    def _process_event(self, event_type, data):
        handler = {
            "exec_started": self._handle_node_execution_started,
            "exec_finished": self._handle_node_execution_finished,
            "event_msg": self._handle_event_msg,
            "process_msg": self._handle_process_msg,
            "standard_execution_msg": self._handle_standard_execution_msg,
            "persistent_execution_msg": self._handle_persistent_execution_msg,
            "kernel_execution_msg": self._handle_kernel_execution_msg,
            "prompt": self._handle_prompt,
            "flash": self._handle_flash,
            "server_status_msg": self._handle_server_status_msg,
        }.get(event_type)
        if handler is None:
            return
        handler(data)

    def _handle_prompt(self, prompt):
        self._prompt_arrived.emit(prompt, self._engine_mngr, self._logger)

    def _handle_flash(self, flash):
        connection = self._connections[flash["item_name"]]
        self._flash_arrived.emit(connection)

    def _handle_standard_execution_msg(self, msg):
        item = self._project_items[msg["item_name"]]
        if msg["type"] == "execution_failed_to_start":
            msg_text = f"Program <b>{msg['program']}</b> failed to start: {msg['error']}"
            self._event_message_arrived.emit(item, msg["filter_id"], "msg_error", msg_text)
        elif msg["type"] == "execution_started":
            self._event_message_arrived.emit(
                item, msg["filter_id"], "msg", f"\tStarting program <b>{msg['program']}</b>"
            )
            self._event_message_arrived.emit(item, msg["filter_id"], "msg", f"\tArguments: <b>{msg['args']}</b>")
            self._event_message_arrived.emit(
                item, msg["filter_id"], "msg_warning", "\tExecution is in progress. See messages below (stdout&stderr)"
            )

    def _handle_persistent_execution_msg(self, msg):
        item = self._project_items.get(msg["item_name"]) or self._connections.get(msg["item_name"])
        msg_type = msg["type"]
        if msg_type == "persistent_started":
            self._logger.persistent_console_requested.emit(item, msg["filter_id"], msg["key"], msg["language"])
        elif msg_type == "persistent_failed_to_start":
            msg_text = (
                f"Unable to start persistent process <b>{msg['args']}</b>: {msg['error']}."
                "Please go to Settings->Tools and check your setup."
            )
            self._event_message_arrived.emit(item, msg["filter_id"], "msg_error", msg_text)
        elif msg_type == "persistent_killed":
            self._logger.persistent_killed(item, msg["filter_id"])
        elif msg_type == "stdin":
            self._logger.add_persistent_stdin(item, msg["filter_id"], msg["data"])
        elif msg_type == "stdout":
            self._logger.add_persistent_stdout(item, msg["filter_id"], msg["data"])
        elif msg_type == "stderr":
            self._logger.add_persistent_stderr(item, msg["filter_id"], msg["data"])
        elif msg_type == "execution_started":
            self._event_message_arrived.emit(
                item, msg["filter_id"], "msg", f"*** Starting execution on persistent process <b>{msg['args']}</b> ***"
            )
            self._event_message_arrived.emit(item, msg["filter_id"], "msg_warning", "See Console for messages")
        else:
            raise RuntimeError(f"Logic error: unknown persistent execution msg_type '{msg_type}'")

    def _handle_kernel_execution_msg(self, msg):
        item = self._project_items[msg["item_name"]] or self._connections.get(msg["item_name"])
        if msg["type"] == "kernel_started":
            self._logger.jupyter_console_requested.emit(
                item,
                msg["filter_id"],
                msg["kernel_name"],
                msg["connection_file"],
                msg.get("connection_file_dict", dict()),
            )
        elif msg["type"] == "kernel_spec_not_found":
            msg_text = (
                f"Unable to find kernel spec <b>{msg['kernel_name']}</b>"
                "<br/>For Python Tools, select a kernel spec in the Tool specification editor."
                "<br/>For Julia Tools, select a kernel spec from File->Settings->Tools."
            )
            self._event_message_arrived.emit(item, msg["filter_id"], "msg_error", msg_text)
        elif msg["type"] == "conda_not_found":
            msg_text = (
                f"{msg['error']}<br/>Couldn't call Conda. Set up <b>Conda executable</b> "
                f"in <b>File->Settings->Tools</b>."
            )
            self._event_message_arrived.emit(item, msg["filter_id"], "msg_error", msg_text)
        elif msg["type"] == "execution_failed_to_start":
            msg_text = f"Execution on kernel <b>{msg['kernel_name']}</b> failed to start: {msg['error']}"
            self._event_message_arrived.emit(item, msg["filter_id"], "msg_error", msg_text)
        elif msg["type"] == "kernel_spec_exe_not_found":
            msg_text = (
                f"Invalid kernel spec ({msg['kernel_name']}). File <b>{msg['kernel_exe_path']}</b> " f"does not exist."
            )
            self._event_message_arrived.emit(item, msg["filter_id"], "msg_error", msg_text)
        elif msg["type"] == "execution_started":
            self._event_message_arrived.emit(
                item, msg["filter_id"], "msg", f"*** Starting execution on kernel spec <b>{msg['kernel_name']}</b> ***"
            )
            self._event_message_arrived.emit(item, msg["filter_id"], "msg_warning", "See Console for messages")
        elif msg["type"] == "kernel_shutdown":
            self._logger.kernel_shutdown.emit(item, msg["filter_id"])

    def _handle_process_msg(self, data):
        self._do_handle_process_msg(**data)

    def _do_handle_process_msg(self, item_name, filter_id, msg_type, msg_text):
        item = self._project_items.get(item_name) or self._connections.get(item_name)
        self._process_message_arrived.emit(item, filter_id, msg_type, msg_text)

    def _handle_event_msg(self, data):
        self._do_handle_event_msg(**data)

    def _do_handle_event_msg(self, item_name, filter_id, msg_type, msg_text):
        item = self._project_items.get(item_name) or self._connections.get(item_name)
        self._event_message_arrived.emit(item, filter_id, msg_type, msg_text)

    def _handle_node_execution_started(self, data):
        self._do_handle_node_execution_started(**data)

    def _do_handle_node_execution_started(self, item_name, direction):
        """Starts item icon animation when executing forward."""
        item = self._project_items[item_name]
        self._executing_items.add(item)
        self._node_execution_started.emit(item, direction)

    def _handle_node_execution_finished(self, data):
        self._do_handle_node_execution_finished(**data)

    def _do_handle_node_execution_finished(self, item_name, direction, state, item_state):
        item = self._project_items[item_name]
        if item_state == ItemExecutionFinishState.SUCCESS:
            self.successful_executions.append((item, direction, state))
        self._executing_items.discard(item)
        # NOTE: A single item may seemingly finish multiple times
        # when the execution is stopped by user during filtered execution.
        self._node_execution_finished.emit(item, direction, item_state)

    def _handle_server_status_msg(self, data):
        if data["msg_type"] == "success":
            self._logger.msg_success.emit(data["text"])
        elif data["msg_type"] == "neutral":
            self._logger.msg.emit(data["text"])
        elif data["msg_type"] == "fail":
            self._logger.msg_error.emit(data["text"])
        elif data["msg_type"] == "warning":
            self._logger.msg_warning.emit(data["text"])

    def clean_up(self):
        for item in self._executing_items:
            self._node_execution_finished.emit(item, None, None)
        if isinstance(self._engine_mngr, LocalSpineEngineManager):
            self._engine_mngr.stop_engine()
        else:
            self._engine_mngr.clean_up()
        self._thread.quit()
        self._thread.wait()
        self._thread.deleteLater()
        self.deleteLater()
