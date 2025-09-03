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

"""This module contains functionality to manage database display names."""
from collections.abc import Iterable, Iterator
import hashlib
import pathlib
from PySide6.QtCore import QObject, Signal, Slot
from sqlalchemy.engine.url import URL, make_url
from spinedb_api import DatabaseMapping
from spinetoolbox.helpers import normcase_database_url_path


class NameRegistry(QObject):
    display_name_changed = Signal(str, str)
    """Emitted when the display name of a database changes."""

    def __init__(self, parent: QObject | None = None):
        """
        Args:
            parent: parent object
        """
        super().__init__(parent)
        self._names_by_url: dict[str, set[str]] = {}

    @Slot(str, str)
    def register(self, db_url: URL | str, name: str) -> None:
        """Registers a new name for given database URL.

        Args:
            db_url: database URL
            name: name to register
        """
        url = normcase_database_url_path(str(db_url))
        if url in self._names_by_url and name in self._names_by_url[url]:
            return
        self._names_by_url.setdefault(url, set()).add(name)
        self.display_name_changed.emit(url, self.display_name(db_url))

    @Slot(str, str)
    def unregister(self, db_url: URL | str, name: str) -> None:
        """Removes a name from the registry.

        Args:
            db_url: database URL
            name: name to remove
        """
        url = normcase_database_url_path(str(db_url))
        names = self._names_by_url[url]
        old_name = self.display_name(url) if 0 < len(names) < 3 else None
        names.remove(name)
        if old_name is not None:
            new_name = self.display_name(url)
            self.display_name_changed.emit(url, new_name)

    def display_name(self, db_url: URL | str) -> str:
        """Makes display name for a database.

        Args:
            db_url: database URL

        Returns:
            display name
        """
        try:
            registered_names = self._names_by_url[normcase_database_url_path(str(db_url))]
        except KeyError:
            return suggest_display_name(db_url)
        else:
            if len(registered_names) == 1:
                return next(iter(registered_names))
            return suggest_display_name(db_url)

    def display_name_iter(self, db_maps: Iterable[DatabaseMapping]) -> Iterator[str]:
        """Yields database mapping display names.

        Args:
            db_maps: database mappings

        Yields:
            display name
        """
        yield from (self.display_name(db_map.sa_url) for db_map in db_maps)

    def map_display_names_to_db_maps(self, db_maps: Iterable[DatabaseMapping]) -> dict[str, DatabaseMapping]:
        """Returns a dictionary that maps display names to database mappings.

        Args:
            db_maps: database mappings

        Returns:
            database mappings keyed by display names
        """
        return {self.display_name(db_map.sa_url): db_map for db_map in db_maps}


def suggest_display_name(db_url: URL | str) -> str:
    """Returns a short name for the database mapping.

    Args:
        db_url: database URL

    Returns:
        suggested name for the database for display purposes.
    """
    if not isinstance(db_url, URL):
        db_url = make_url(db_url)
    if not db_url.drivername.startswith("sqlite"):
        return db_url.database
    if db_url.database is not None:
        return pathlib.Path(db_url.database).stem
    hashing = hashlib.sha1()
    hashing.update(bytes(str(id(db_url)), "utf-8"))
    return hashing.hexdigest()
