######################################################################################################################
# Copyright (C) 2017-2020 Spine project consortium
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""
Contains CustomFileSystemWatcher.

:author: M. Marin (KTH)
:date:   12.11.2020
"""

import os
from PySide2.QtCore import QFileSystemWatcher, Signal, Slot


class CustomFileSystemWatcher(QFileSystemWatcher):
    """A file system watcher that keeps track of renamed files.
    """

    file_renamed = Signal(str, str)
    file_removed = Signal(str)
    file_added = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._watched_files = {}
        self._watched_dirs = set()
        self._directory_snapshots = {}
        self.directoryChanged.connect(self._handle_dir_changed)

    @Slot(str)
    def _handle_dir_changed(self, dirname):
        is_watched_dir = dirname in self._watched_dirs
        watched_files = self._watched_files.get(dirname, set())
        if not is_watched_dir and not watched_files:
            return
        snapshot = self._directory_snapshots[dirname]
        new_snapshot = self._directory_snapshots[dirname] = self._take_snapshot(dirname)
        removed_filepath = next(iter(snapshot - new_snapshot), None)
        if not is_watched_dir and removed_filepath not in watched_files:
            return
        added_filepath = next(iter(new_snapshot - snapshot), None)
        try:
            watched_files.remove(removed_filepath)
            watched_files.add(added_filepath)
        except KeyError:
            pass
        if removed_filepath and added_filepath:
            self.file_renamed.emit(removed_filepath, added_filepath)
            return
        if removed_filepath:
            self.file_removed.emit(removed_filepath)
            return
        if is_watched_dir:
            self.file_added.emit(added_filepath)

    def add_persistent_file_path(self, path):
        if not os.path.isfile(path):
            return False
        dirname = os.path.dirname(path)
        self._watched_files.setdefault(dirname, set()).add(path)
        self._directory_snapshots.setdefault(dirname, self._take_snapshot(dirname))
        return self.addPath(dirname)

    def add_persistent_file_paths(self, paths):
        added_paths = []
        for path in paths:
            if self.add_persistent_file_path(path):
                added_paths.append(path)
        return added_paths

    def remove_persistent_file_path(self, path):
        if not os.path.isfile(path):
            return False
        dirname = os.path.dirname(path)
        watched_files = self._watched_files.get(dirname)
        if not watched_files:
            return
        watched_files.discard(path)
        if watched_files:
            return
        del self._watched_files[dirname]
        if path in self._watched_dirs:
            return
        del self._directory_snapshots[dirname]
        return self.removePath(path)

    def remove_persistent_file_paths(self, paths):
        removed_paths = []
        for path in paths:
            if self.remove_persistent_file_path(path):
                removed_paths.append(path)
        return removed_paths

    def add_persistent_dir_path(self, path):
        if not os.path.isdir(path):
            return False
        self._watched_dirs.add(path)
        self._directory_snapshots.setdefault(path, self._take_snapshot(path))
        return self.addPath(path)

    def remove_persistent_dir_path(self, path):
        if not os.path.isdir(path):
            return False
        self._watched_dirs.discard(path)
        if path in self._watched_files:
            return
        del self._directory_snapshots[path]
        return self.removePath(path)

    def tear_down(self):
        self.removePaths(self.directories())
        self.deleteLater()

    def _take_snapshot(self, dirname):
        return set(self._absfilepaths(dirname))

    @staticmethod
    def _absfilepaths(dirname):
        with os.scandir(dirname) as scan_iterator:
            for entry in scan_iterator:
                if entry.is_file():
                    yield entry.path
