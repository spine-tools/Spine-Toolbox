"""Database reads and edits for the QML database editor."""

from collections import Counter
from collections.abc import Callable
import json
from typing import Any
from .db_session import DatabaseSession, DatabaseSessionError

_EDITABLE_ITEM_TYPES = {"entity_class", "entity", "alternative", "scenario"}


def _editable_type(item_type: str) -> str:
    if item_type not in _EDITABLE_ITEM_TYPES:
        raise DatabaseSessionError(f"{item_type} items cannot be edited")
    return item_type


def _cell_text(value: Any) -> tuple[str, bool]:
    """Returns a value's text for a pivot cell and whether it can be edited as text."""
    if isinstance(value, (bool, int, float, type(None))):
        return json.dumps(value), True
    if isinstance(value, str):
        try:
            json.loads(value)
        except ValueError:
            if value:
                return value, True
        return json.dumps(value), True
    return type(value).__name__, False


def _set_parameter_value(
    session: DatabaseSession, class_name: str, entity: str, parameter: str, alternative: str, text: str
) -> None:
    """Adds, updates or, for empty text, removes a parameter value."""
    existing = next(
        (
            value
            for value in session.items("parameter_value")
            if value["entity_class_name"] == class_name
            and "__".join(value["entity_byname"]) == entity
            and value["parameter_definition_name"] == parameter
            and value["alternative_name"] == alternative
        ),
        None,
    )
    if existing is not None and not isinstance(existing["parsed_value"], (bool, int, float, str, type(None))):
        raise DatabaseSessionError("Only plain numbers, text and booleans can be edited here")
    if not text.strip():
        if existing is not None:
            session.remove("parameter_value", existing["id"])
        return
    try:
        parsed_value = json.loads(text)
    except ValueError:
        parsed_value = text
    if existing is not None:
        session.update("parameter_value", existing["id"], parsed_value=parsed_value)
        return
    entity_item = next(
        (
            item
            for item in session.items("entity")
            if item["entity_class_name"] == class_name and "__".join(item["entity_byname"]) == entity
        ),
        None,
    )
    if entity_item is None:
        raise DatabaseSessionError(f"No entity {entity} in {class_name}")
    session.add(
        "parameter_value",
        entity_class_name=class_name,
        entity_byname=tuple(entity_item["entity_byname"]),
        parameter_definition_name=parameter,
        alternative_name=alternative,
        parsed_value=parsed_value,
    )


class DatabaseEditorBackend:
    """Provides database data and editing operations independently of the project workflow bridge."""

    def __init__(self) -> None:
        self._sessions: dict[str, DatabaseSession] = {}

    def get_databases(self, data: dict, project_dir: str, url_builder: Callable[[dict, str], str | None]) -> str:
        """Returns the project's Data Store items and their resolved URLs as JSON."""
        databases = []
        for name, item in data.get("items", {}).items():
            if item.get("type") != "Data Store":
                continue
            url = url_builder(item.get("url") or {}, project_dir)
            if url:
                databases.append({"name": name, "url": url})
        return json.dumps(databases)

    def get_database_contents(self, url: str) -> str:
        """Returns entity classes, alternatives and the scenario tree as JSON."""
        try:
            session = self._session(url)
            entity_counts = Counter(entity["entity_class_name"] for entity in session.items("entity"))
            entity_classes = [
                {"name": entity_class["name"], "entity_count": entity_counts[entity_class["name"]]}
                for entity_class in session.items("entity_class")
            ]
            alternative_items = session.items("alternative")
            descriptions = {alternative["name"]: alternative["description"] or "" for alternative in alternative_items}
            ranked_alternatives: dict[str, list[tuple[int, str]]] = {}
            for scenario_alternative in session.items("scenario_alternative"):
                ranked_alternatives.setdefault(scenario_alternative["scenario_name"], []).append(
                    (scenario_alternative["rank"], scenario_alternative["alternative_name"])
                )
            scenario_tree = [
                {
                    "name": scenario["name"],
                    "description": scenario["description"] or "",
                    "alternatives": [
                        {"name": name, "description": descriptions[name]}
                        for _, name in sorted(ranked_alternatives.get(scenario["name"], []))
                    ],
                }
                for scenario in session.items("scenario")
            ]
        except Exception as error:
            return json.dumps({"error": str(error)})
        return json.dumps(
            {
                "entity_classes": entity_classes,
                "alternatives": list(descriptions),
                "scenario_tree": scenario_tree,
            }
        )

    def get_entity_class_values(self, url: str, class_name: str) -> str:
        """Returns parameter values for one entity class as JSON."""
        try:
            rows = [
                {
                    "entity": "__".join(value["entity_byname"]),
                    "parameter": value["parameter_definition_name"],
                    "alternative": value["alternative_name"],
                    "value": str(value["parsed_value"]),
                }
                for value in self._session(url).items("parameter_value")
                if value["entity_class_name"] == class_name
            ]
        except Exception:
            return json.dumps([])
        return json.dumps(rows)

    def get_pivot(self, url: str, class_name: str, alternative: str) -> str:
        """Returns the selected alternative's parameter values as a pivot grid in JSON."""
        try:
            session = self._session(url)
            alternatives = [item["name"] for item in session.items("alternative")]
            if alternative not in alternatives:
                alternative = "Base" if "Base" in alternatives else next(iter(alternatives), "")
            parameters = [
                item["name"]
                for item in session.items("parameter_definition")
                if item["entity_class_name"] == class_name
            ]
            values = {
                ("__".join(item["entity_byname"]), item["parameter_definition_name"]): item["parsed_value"]
                for item in session.items("parameter_value")
                if item["entity_class_name"] == class_name and item["alternative_name"] == alternative
            }
            rows = []
            for item in session.items("entity"):
                if item["entity_class_name"] != class_name:
                    continue
                entity = "__".join(item["entity_byname"])
                cells = []
                for parameter in parameters:
                    if (entity, parameter) in values:
                        text, editable = _cell_text(values[(entity, parameter)])
                        cells.append({"text": text, "editable": editable, "empty": False})
                    else:
                        cells.append({"text": "", "editable": True, "empty": True})
                rows.append({"entity": entity, "cells": cells})
        except Exception as error:
            return json.dumps({"error": str(error)})
        return json.dumps(
            {"alternatives": alternatives, "alternative": alternative, "parameters": parameters, "rows": rows}
        )

    def _session(self, url: str) -> DatabaseSession:
        session = self._sessions.get(url)
        if session is None:
            session = self._sessions[url] = DatabaseSession(url)
        return session

    def close_sessions(self) -> None:
        for session in self._sessions.values():
            session.close()
        self._sessions.clear()

    def refresh_sessions(self) -> None:
        for session in self._sessions.values():
            session.refresh()

    def _edit(self, url: str, edit: Callable[[DatabaseSession], None]) -> str:
        """Runs an edit and returns the session state as JSON."""
        error = ""
        try:
            edit(self._session(url))
        except Exception as exception:
            error = str(exception)
        return self._session_state(url, error)

    def _session_state(self, url: str, error: str = "") -> str:
        session = self._sessions.get(url)
        state = {
            "dirty": session.is_dirty if session else False,
            "can_undo": session.can_undo if session else False,
            "can_redo": session.can_redo if session else False,
        }
        if error:
            state["error"] = error
        return json.dumps(state)

    def reload_database(self, url: str) -> str:
        return self._edit(url, lambda session: session.refresh())

    def get_session_state(self, url: str) -> str:
        return self._session_state(url)

    def add_item(self, url: str, item_type: str, fields_json: str) -> str:
        return self._edit(url, lambda session: session.add(_editable_type(item_type), **json.loads(fields_json)))

    def update_item(self, url: str, item_type: str, key_json: str, fields_json: str) -> str:
        def update(session: DatabaseSession) -> None:
            item = session.find(_editable_type(item_type), **json.loads(key_json))
            session.update(item_type, item["id"], **json.loads(fields_json))

        return self._edit(url, update)

    def remove_item(self, url: str, item_type: str, key_json: str) -> str:
        def remove(session: DatabaseSession) -> None:
            item = session.find(_editable_type(item_type), **json.loads(key_json))
            session.remove(item_type, item["id"])

        return self._edit(url, remove)

    def set_scenario_alternatives(self, url: str, scenario_name: str, alternative_names_json: str) -> str:
        def set_alternatives(session: DatabaseSession) -> None:
            session.find("scenario", name=scenario_name)
            names = json.loads(alternative_names_json)
            existing = {
                item["alternative_name"]: item
                for item in session.items("scenario_alternative")
                if item["scenario_name"] == scenario_name
            }
            with session.batch():
                for name, item in existing.items():
                    if name not in names:
                        session.remove("scenario_alternative", item["id"])
                moved = [(rank, existing[name]) for rank, name in enumerate(names, start=1) if name in existing]
                moved = [(rank, item) for rank, item in moved if item["rank"] != rank]
                temporary_rank = max([item["rank"] for item in existing.values()] + [len(names)]) + 1
                for offset, (_, item) in enumerate(moved):
                    session.update("scenario_alternative", item["id"], rank=temporary_rank + offset)
                for rank, item in moved:
                    session.update("scenario_alternative", item["id"], rank=rank)
                for rank, name in enumerate(names, start=1):
                    if name not in existing:
                        session.add(
                            "scenario_alternative", scenario_name=scenario_name, alternative_name=name, rank=rank
                        )

        return self._edit(url, set_alternatives)

    def set_parameter_value(
        self, url: str, class_name: str, entity: str, parameter: str, alternative: str, text: str
    ) -> str:
        return self._edit(
            url, lambda session: _set_parameter_value(session, class_name, entity, parameter, alternative, text)
        )

    def undo_edit(self, url: str) -> str:
        return self._edit(url, lambda session: session.undo())

    def redo_edit(self, url: str) -> str:
        return self._edit(url, lambda session: session.redo())

    def commit_edits(self, url: str, comment: str) -> str:
        return self._edit(url, lambda session: session.commit(comment))

    def discard_edits(self, url: str) -> str:
        return self._edit(url, lambda session: session.discard())
