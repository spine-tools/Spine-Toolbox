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

"""Qt-based thread pool executor."""
import os
from PySide6.QtCore import QMutex, QSemaphore, QThread


class TimeOutError(Exception):
    """An exception to raise when a timeouts expire"""


class _CustomQSemaphore(QSemaphore):
    def tryAcquire(self, n, timeout=None):
        if timeout is None:
            timeout = -1
        timeout *= 1000
        return super().tryAcquire(n, timeout)


class QtBasedQueue:
    """A Qt-based clone of queue.Queue."""

    def __init__(self):
        self._items = []
        self._mutex = QMutex()
        self._semafore = _CustomQSemaphore()

    def put(self, item):
        self._mutex.lock()
        self._items.append(item)
        self._mutex.unlock()
        self._semafore.release()

    def get(self, timeout=None):
        if not self._semafore.tryAcquire(1, timeout):
            raise TimeOutError()
        self._mutex.lock()
        item = self._items.pop(0)
        self._mutex.unlock()
        return item


class QtBasedFuture:
    """A Qt-based clone of concurrent.futures.Future."""

    def __init__(self):
        self._semafore = _CustomQSemaphore()
        self._done = False
        self._result = None
        self._exception = None
        self._done_callbacks = []

    def set_result(self, result):
        self._result = result
        self._done = True
        self._semafore.release()
        for callback in self._done_callbacks:
            callback(self)
        self._done_callbacks = []

    def set_exception(self, exc):
        self._exception = exc
        self._done = True
        self._semafore.release()

    def result(self, timeout=None):
        if not self._done and not self._semafore.tryAcquire(1, timeout):
            raise TimeOutError()
        if self._exception is not None:
            raise self._exception
        return self._result

    def exception(self, timeout=None):
        if not self._done and not self._semafore.tryAcquire(1, timeout):
            raise TimeOutError()
        return self._exception

    def add_done_callback(self, callback):
        if self._done:
            callback(self)
            return
        self._done_callbacks.append(callback)


class QtBasedThread(QThread):
    """A Qt-based clone of threading.Thread."""

    def __init__(self, target=None, args=()):
        super().__init__()
        self._target = target
        self._args = args

    def run(self):
        return self._target(*self._args)


class QtBasedThreadPoolExecutor:
    """A Qt-based clone of concurrent.futures.ThreadPoolExecutor"""

    def __init__(self, max_workers=None):
        if max_workers is None:
            max_workers = min(32, os.cpu_count() + 4)
        self._max_workers = max_workers
        self._threads = set()
        self._requests = QtBasedQueue()
        self._semafore = QSemaphore()
        self._shutdown = False

    def submit(self, fn, *args, **kwargs):
        future = QtBasedFuture()
        self._requests.put((future, fn, args, kwargs))
        self._spawn_thread()
        return future

    def _spawn_thread(self):
        if self._semafore.tryAcquire():
            # No need to spawn a new thread
            return
        if len(self._threads) == self._max_workers:
            # Not possible to spawn a new thread
            return
        thread = QtBasedThread(target=self._do_work)
        self._threads.add(thread)
        thread.start()

    def _do_work(self):
        while True:
            request = self._requests.get()
            if self._shutdown:
                break
            future, fn, args, kwargs = request
            _set_future_result_and_exc(future, fn, *args, **kwargs)
            self._semafore.release()

    def shutdown(self):
        self._shutdown = True
        for _ in self._threads:
            self._requests.put(None)
        while self._threads:
            thread = self._threads.pop()
            thread.wait()
            thread.deleteLater()


class SynchronousExecutor:
    def submit(self, fn, *args, **kwargs):
        future = QtBasedFuture()
        _set_future_result_and_exc(future, fn, *args, **kwargs)
        return future

    def shutdown(self):
        pass


def _set_future_result_and_exc(future, fn, *args, **kwargs):
    try:
        result = fn(*args, **kwargs)
        future.set_result(result)
    except Exception as exc:  # pylint: disable=broad-except
        future.set_exception(exc)
