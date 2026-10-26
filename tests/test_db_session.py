from pathlib import Path
import pytest
from spinedb_api import DatabaseMapping
from spinetoolbox.frontend.qt_ui.db_session import DatabaseSession, DatabaseSessionError


@pytest.fixture
def url(tmp_path: Path) -> str:
    url = f"sqlite:///{tmp_path / 'db.sqlite'}"
    with DatabaseMapping(url, create=True) as db_map:
        db_map.add_entity_class(name="Widget")
        db_map.add_entity(entity_class_name="Widget", name="knob")
        db_map.commit_session("Set up")
    return url


@pytest.fixture
def session(url: str):
    session = DatabaseSession(url)
    yield session
    session.close()


def _names(session: DatabaseSession, item_type: str) -> set[str]:
    return {item["name"] for item in session.items(item_type)}


def _committed_names(url: str, item_type: str) -> set[str]:
    with DatabaseMapping(url) as db_map:
        return {item["name"] for item in db_map.get_items(item_type)}


def test_reads_committed_data(session: DatabaseSession) -> None:
    assert _names(session, "entity") == {"knob"}
    assert not session.is_dirty


def test_add_is_visible_but_not_committed(session: DatabaseSession, url: str) -> None:
    session.add("entity", entity_class_name="Widget", name="lever")
    assert _names(session, "entity") == {"knob", "lever"}
    assert session.is_dirty
    assert _committed_names(url, "entity") == {"knob"}


def test_add_error_raises(session: DatabaseSession) -> None:
    with pytest.raises(DatabaseSessionError):
        session.add("entity", entity_class_name="Widget", name="knob")
    assert not session.is_dirty


def test_undo_redo_add(session: DatabaseSession) -> None:
    session.add("entity", entity_class_name="Widget", name="lever")
    session.undo()
    assert _names(session, "entity") == {"knob"}
    assert not session.is_dirty
    assert session.can_redo
    session.redo()
    assert _names(session, "entity") == {"knob", "lever"}
    assert session.is_dirty


def test_undo_redo_update(session: DatabaseSession) -> None:
    knob = session.items("entity")[0]
    session.update("entity", knob["id"], name="dial")
    assert _names(session, "entity") == {"dial"}
    session.undo()
    assert _names(session, "entity") == {"knob"}
    session.redo()
    assert _names(session, "entity") == {"dial"}


def test_undo_redo_remove(session: DatabaseSession) -> None:
    knob = session.items("entity")[0]
    session.remove("entity", knob["id"])
    assert _names(session, "entity") == set()
    session.undo()
    assert _names(session, "entity") == {"knob"}
    session.redo()
    assert _names(session, "entity") == set()


def test_new_edit_clears_redo(session: DatabaseSession) -> None:
    session.add("entity", entity_class_name="Widget", name="lever")
    session.undo()
    session.add("entity", entity_class_name="Widget", name="dial")
    assert not session.can_redo


def test_commit_writes_to_database_and_clears_history(session: DatabaseSession, url: str) -> None:
    session.add("entity", entity_class_name="Widget", name="lever")
    session.commit("Add lever")
    assert _committed_names(url, "entity") == {"knob", "lever"}
    assert not session.is_dirty
    assert not session.can_undo


def test_discard_drops_uncommitted_edits(session: DatabaseSession, url: str) -> None:
    session.add("entity", entity_class_name="Widget", name="lever")
    session.discard()
    assert _names(session, "entity") == {"knob"}
    assert not session.is_dirty
    assert _committed_names(url, "entity") == {"knob"}


def test_other_writers_are_not_blocked_while_session_is_open(session: DatabaseSession, url: str) -> None:
    session.items("entity")
    with DatabaseMapping(url) as db_map:
        db_map.add_entity(entity_class_name="Widget", name="lever")
        db_map.commit_session("From elsewhere")
    session.refresh()
    assert _names(session, "entity") == {"knob", "lever"}


def test_refresh_keeps_uncommitted_edits(session: DatabaseSession) -> None:
    session.add("entity", entity_class_name="Widget", name="lever")
    session.refresh()
    assert _names(session, "entity") == {"knob", "lever"}
