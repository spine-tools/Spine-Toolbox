"""Editing session over one database, with undo/redo and explicit commit."""

from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any


class DatabaseSessionError(Exception):
    """Raised when the database rejects an operation."""


@dataclass
class _Command:
    undo: Callable[[], None]
    redo: Callable[[], None]


class DatabaseSession:
    """Keeps a database open so edits stay uncommitted until commit() is called."""

    def __init__(self, url: str) -> None:
        from spinedb_api import DatabaseMapping  # imported lazily, see ProjectBridge

        self.url = url
        self._db_map = DatabaseMapping(url)
        self._db_map.__enter__()
        self._undo_stack: list[_Command] = []
        self._redo_stack: list[_Command] = []
        self._fully_fetched = False

    @property
    def is_dirty(self) -> bool:
        return bool(self._undo_stack)

    @property
    def can_undo(self) -> bool:
        return bool(self._undo_stack)

    @property
    def can_redo(self) -> bool:
        return bool(self._redo_stack)

    def items(self, item_type: str) -> list[Any]:
        """Returns the items of given type, including uncommitted edits."""
        try:
            return self._db_map.get_items(item_type)
        finally:
            self._release()

    def find(self, item_type: str, **key: Any) -> Any:
        """Returns the item whose fields match key."""
        for item in self.items(item_type):
            if all(item[name] == value for name, value in key.items()):
                return item
        raise DatabaseSessionError(f"No {item_type} matching {key}")

    @contextmanager
    def batch(self) -> Iterator[None]:
        """Groups the edits made inside the block into one undo step."""
        outer_stack = self._undo_stack
        self._undo_stack = []
        try:
            yield
        finally:
            commands = self._undo_stack
            self._undo_stack = outer_stack
            if commands:

                def undo() -> None:
                    for command in reversed(commands):
                        command.undo()

                def redo() -> None:
                    for command in commands:
                        command.redo()

                self._push(_Command(undo, redo))

    def add(self, item_type: str, **fields: Any) -> Any:
        item, error = self._db_map.add_item(item_type, **fields)
        self._release()
        if error:
            raise DatabaseSessionError(error)
        id_ = item["id"]
        self._push(_Command(lambda: self._remove(item_type, id_), lambda: self._restore(item_type, id_)))
        return item

    def update(self, item_type: str, id_: Any, **fields: Any) -> None:
        previous = {name: self._find(item_type, id_)[name] for name in fields}
        self._update(item_type, id_, fields)
        self._push(
            _Command(lambda: self._update(item_type, id_, previous), lambda: self._update(item_type, id_, fields))
        )

    def remove(self, item_type: str, id_: Any) -> None:
        if not self._fully_fetched:
            # removal only cascades to dependents that are already loaded
            self._db_map.fetch_all()
            self._release()
            self._fully_fetched = True
        self._remove(item_type, id_)
        self._push(_Command(lambda: self._restore(item_type, id_), lambda: self._remove(item_type, id_)))

    def undo(self) -> None:
        command = self._undo_stack.pop()
        command.undo()
        self._redo_stack.append(command)

    def redo(self) -> None:
        command = self._redo_stack.pop()
        command.redo()
        self._undo_stack.append(command)

    def commit(self, comment: str) -> None:
        if not self.is_dirty:
            return
        from spinedb_api.exception import SpineDBAPIError

        try:
            self._db_map.commit_session(comment)
        except SpineDBAPIError as error:
            raise DatabaseSessionError(str(error)) from error
        finally:
            self._release()
        self._clear_history()

    def discard(self) -> None:
        if not self.is_dirty:
            return
        self._db_map.rollback_session()
        self._release()
        self._clear_history()

    def refresh(self) -> None:
        """Reloads from the database, unless there are uncommitted edits; redoable edits are dropped."""
        if not self.is_dirty:
            self._redo_stack.clear()
            self._db_map.refresh_session()
            self._fully_fetched = False

    def close(self) -> None:
        self._db_map.__exit__(None, None, None)
        self._db_map.close()

    def _push(self, command: _Command) -> None:
        self._undo_stack.append(command)
        self._redo_stack.clear()

    def _clear_history(self) -> None:
        self._undo_stack.clear()
        self._redo_stack.clear()

    def _find(self, item_type: str, id_: Any) -> Any:
        for item in self.items(item_type):
            if item["id"] == id_:
                return item
        raise DatabaseSessionError(f"No {item_type} with id {id_}")

    def _update(self, item_type: str, id_: Any, fields: dict[str, Any]) -> None:
        _, error = self._db_map.update_item(item_type, id=id_, **fields)
        self._release()
        if error:
            raise DatabaseSessionError(error)

    def _remove(self, item_type: str, id_: Any) -> None:
        _, error = self._db_map.remove_item(item_type, id_)
        self._release()
        if error:
            raise DatabaseSessionError(error)

    def _restore(self, item_type: str, id_: Any) -> None:
        _, error = self._db_map.restore_item(item_type, id_)
        self._release()
        if error:
            raise DatabaseSessionError(error)

    def _release(self) -> None:
        """Ends the read transaction so that other writers, e.g. a running workflow, are not blocked."""
        self._db_map._session.rollback()  # spinedb_api exposes no public way to do this
