######################################################################################################################
# Copyright (C) 2017-2022 Spine project consortium
# Copyright Spine Toolbox contributors
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################
"""Contains utilities for validating parameter types."""
from dataclasses import dataclass
from multiprocessing import Process, Queue
import queue
from typing import Any, Iterable, Optional, Tuple
from PySide6.QtCore import QObject, QTimer, Signal, Slot
from spinedb_api.db_mapping_helpers import is_parameter_type_valid, type_check_args

CHUNK_SIZE = 100


@dataclass(frozen=True)
class ValidationKey:
    item_type: str
    db_map_id: int
    item_private_id: int


@dataclass(frozen=True)
class ValidatableValue:
    key: ValidationKey
    args: Tuple[Iterable[str], Optional[bytes], Optional[Any], Optional[str]]


class ParameterTypeValidator(QObject):
    """Handles parameter type validation in a concurrent process."""

    validated = Signal(list, list)

    def __init__(self, parent=None):
        """
        Args:
            parent (QObject, optional): parent object
        """
        super().__init__(parent)
        self._sender = Queue()
        self._receiver = Queue()
        self._process = Process(target=schedule, name="Type validation worker", args=(self._receiver, self._sender))
        self._timer = QTimer(self)
        self._timer.setInterval(100)
        self._timer.timeout.connect(self._communicate)
        self._task_queue = []
        self._sent_task_count = 0

    def set_interval(self, interval):
        """Sets the interval between communication attempts with the validation process.

        Args:
            interval (int): interval in milliseconds
        """
        self._timer.setInterval(interval)

    def start_validating(self, db_mngr, db_map, value_item_ids):
        """Initiates validation of given parameter definition/value items.

        Args:
            db_mngr (SpineDBManager): database manager
            db_map (DatabaseMapping): database mapping
            value_item_ids (Iterable of TempId): item ids to validate
        """
        if not self._process.is_alive():
            self._process.start()
        with db_mngr.get_lock(db_map):
            for item_id in value_item_ids:
                mapped_table = db_map.mapped_table(item_id.item_type)
                item = mapped_table.find_item_by_id(item_id)
                args = type_check_args(item)
                self._task_queue.append(
                    ValidatableValue(ValidationKey(item_id.item_type, id(db_map), item_id.private_id), args)
                )
        if not self._timer.isActive():
            chunk = self._task_queue[:CHUNK_SIZE]
            self._task_queue = self._task_queue[CHUNK_SIZE:]
            self._sender.put(chunk)
            self._sent_task_count += len(chunk)
            self._timer.start()

    @Slot()
    def _communicate(self):
        """Communicates with the validation process."""
        self._timer.stop()
        if not self._process.is_alive():
            return
        try:
            results = self._receiver.get_nowait()
        except queue.Empty:
            pass
        else:
            self.validated.emit(*results)
            self._sent_task_count -= len(results[0])
        if self._task_queue and self._sent_task_count < 3 * CHUNK_SIZE:
            chunk = self._task_queue[:CHUNK_SIZE]
            self._task_queue = self._task_queue[CHUNK_SIZE:]
            self._sender.put(chunk)
            self._sent_task_count += len(chunk)
        if not self._task_queue and self._sent_task_count == 0:
            return
        self._timer.start()

    def tear_down(self):
        """Cleans up the validation process."""
        self._timer.stop()
        if self._process.is_alive():
            self._sender.put("quit")
            finished = False
            while not finished:
                finished = self._receiver.get() == "finished"
            self._process.join()


def validate_chunk(validatable_values):
    """Validates given parameter definitions/values.

    Args:
        validatable_values (Iterable of ValidatableValue): values to validate

    Returns:
        dict: mapping from ValidationKey to boolean
    """
    results = {}
    for validatable_value in validatable_values:
        results[validatable_value.key] = is_parameter_type_valid(*validatable_value.args)
    return results


def schedule(sender, receiver):
    """Loops over incoming messages and sends responses back.

    Args:
        sender (Queue): Queue for sending validation results
        receiver (Queue): Queue for receiving tasks
    """
    validatable_values = []
    while True:
        if not receiver.empty() or not validatable_values:
            while True:
                task = receiver.get()
                if task == "quit":
                    sender.put("finished")
                    return
                validatable_values += task
                if receiver.empty():
                    break
        chunk = validatable_values[:CHUNK_SIZE]
        validatable_values = validatable_values[CHUNK_SIZE:]
        results = validate_chunk(chunk)
        sender.put((list(results.keys()), list(results.values())))
