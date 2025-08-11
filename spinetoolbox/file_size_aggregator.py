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
from collections.abc import Iterable
import multiprocessing
from multiprocessing import connection
import pathlib
from typing import Optional
from PySide6.QtCore import QObject, QTimer, Signal


class AggregatorProcess(QObject):
    aggregated = Signal(int)

    def __init__(self, parent: Optional[QObject]):
        super().__init__(parent)
        self._process: Optional[multiprocessing.Process] = None
        self._receiver, self._sender = multiprocessing.Pipe(duplex=False)
        self._timer = QTimer(self)
        self._timer.setInterval(100)
        self._timer.timeout.connect(self._check_process)

    def start_aggregating(self, paths: Iterable[str | pathlib.Path]) -> None:
        if self._process is not None:
            self._timer.stop()
            self._process.join()
        self._process = multiprocessing.Process(target=_aggregation_process, args=(paths, self._sender))
        self._process.start()
        self._timer.start()

    def _check_process(self) -> None:
        if self._receiver.poll():
            size = self._receiver.recv()
            self._process.join()
            self._process = None
            self.aggregated.emit(size)
        else:
            self._timer.start()

    def tear_down(self) -> None:
        self._timer.stop()
        if self._process is not None:
            self._process.join()


def _aggregation_process(paths: Iterable[str | pathlib.Path], sender: connection.Connection) -> None:
    size = sum(map(aggregate_file_sizes, paths))
    sender.send(size)


def aggregate_file_sizes(base_path: str | pathlib.Path) -> int:
    past_iterators = []
    base_path = pathlib.Path(base_path)
    if base_path.is_file():
        return base_path.stat().st_size
    dir_iterator = base_path.iterdir()
    total_size = 0
    while True:
        try:
            path = next(dir_iterator)
        except StopIteration:
            try:
                dir_iterator = past_iterators.pop()
            except IndexError:
                break
            else:
                continue
        if path.is_file():
            total_size += path.stat().st_size
        elif path.is_dir():
            past_iterators.append(dir_iterator)
            dir_iterator = path.iterdir()
    return total_size
