import json
from pathlib import Path
from PySide6.QtCore import QCoreApplication
import pytest
from spinedb_api import DatabaseMapping
from spinetoolbox.frontend.qt_ui.project_bridge import ProjectBridge


@pytest.fixture(scope="module")
def application() -> QCoreApplication:
    return QCoreApplication.instance() or QCoreApplication([])


@pytest.fixture
def url(tmp_path: Path) -> str:
    url = f"sqlite:///{tmp_path / 'data.sqlite'}"
    with DatabaseMapping(url, create=True) as db_map:
        db_map.add_entity_class(name="Widget")
        db_map.add_entity(entity_class_name="Widget", name="knob")
        db_map.add_entity(entity_class_name="Widget", name="dial")
        db_map.add_parameter_definition(entity_class_name="Widget", name="weight")
        db_map.add_parameter_value(
            entity_class_name="Widget",
            entity_byname=("knob",),
            parameter_definition_name="weight",
            alternative_name="Base",
            parsed_value=2.5,
        )
        db_map.add_alternative(name="Heavy")
        db_map.add_scenario(name="Scenario")
        db_map.add_scenario_alternative(scenario_name="Scenario", alternative_name="Base", rank=1)
        db_map.commit_session("Set up")
    return url


@pytest.fixture
def bridge(tmp_path: Path, application: QCoreApplication):
    bridge = ProjectBridge(tmp_path)
    yield bridge
    bridge._close_sessions()


def _contents(bridge: ProjectBridge, url: str) -> dict:
    return json.loads(bridge.get_database_contents(url))


def _values(bridge: ProjectBridge, url: str) -> dict[tuple[str, str, str], str]:
    rows = json.loads(bridge.get_entity_class_values(url, "Widget"))
    return {(row["entity"], row["parameter"], row["alternative"]): row["value"] for row in rows}


def _committed_names(url: str, item_type: str) -> set[str]:
    with DatabaseMapping(url) as db_map:
        return {item["name"] for item in db_map.get_items(item_type)}


def test_added_alternative_is_listed_and_marks_session_dirty(bridge: ProjectBridge, url: str) -> None:
    state = json.loads(bridge.add_item(url, "alternative", json.dumps({"name": "Light"})))
    assert state == {"dirty": True, "can_undo": True, "can_redo": False}
    assert _contents(bridge, url)["alternatives"] == ["Base", "Heavy", "Light"]
    assert _committed_names(url, "alternative") == {"Base", "Heavy"}


def test_rejected_edit_reports_error_without_dirtying(bridge: ProjectBridge, url: str) -> None:
    state = json.loads(bridge.add_item(url, "alternative", json.dumps({"name": "Heavy"})))
    assert state["error"]
    assert not state["dirty"]


def test_other_item_types_cannot_be_edited(bridge: ProjectBridge, url: str) -> None:
    state = json.loads(bridge.add_item(url, "parameter_value", json.dumps({})))
    assert "cannot be edited" in state["error"]


def test_rename_and_remove_entity_class(bridge: ProjectBridge, url: str) -> None:
    bridge.update_item(url, "entity_class", json.dumps({"name": "Widget"}), json.dumps({"name": "Gadget"}))
    assert [c["name"] for c in _contents(bridge, url)["entity_classes"]] == ["Gadget"]
    bridge.remove_item(url, "entity_class", json.dumps({"name": "Gadget"}))
    assert _contents(bridge, url)["entity_classes"] == []


def test_remove_alternative_can_be_undone_with_its_scenario_membership(bridge: ProjectBridge, url: str) -> None:
    bridge.remove_item(url, "alternative", json.dumps({"name": "Base"}))
    assert _contents(bridge, url)["scenario_tree"][0]["alternatives"] == []
    assert _values(bridge, url) == {}
    bridge.undo_edit(url)
    assert [a["name"] for a in _contents(bridge, url)["scenario_tree"][0]["alternatives"]] == ["Base"]
    assert _values(bridge, url) == {("knob", "weight", "Base"): "2.5"}


def test_set_scenario_alternatives_reorders_in_one_undo_step(bridge: ProjectBridge, url: str) -> None:
    state = json.loads(bridge.set_scenario_alternatives(url, "Scenario", json.dumps(["Heavy", "Base"])))
    assert "error" not in state
    assert [a["name"] for a in _contents(bridge, url)["scenario_tree"][0]["alternatives"]] == ["Heavy", "Base"]
    state = json.loads(bridge.undo_edit(url))
    assert not state["dirty"]
    assert [a["name"] for a in _contents(bridge, url)["scenario_tree"][0]["alternatives"]] == ["Base"]
    bridge.redo_edit(url)
    assert [a["name"] for a in _contents(bridge, url)["scenario_tree"][0]["alternatives"]] == ["Heavy", "Base"]


def test_set_parameter_value_updates_adds_and_clears(bridge: ProjectBridge, url: str) -> None:
    bridge.set_parameter_value(url, "Widget", "knob", "weight", "Base", "4")
    bridge.set_parameter_value(url, "Widget", "dial", "weight", "Heavy", "heavy stuff")
    assert _values(bridge, url) == {
        ("knob", "weight", "Base"): "4.0",
        ("dial", "weight", "Heavy"): "heavy stuff",
    }
    bridge.set_parameter_value(url, "Widget", "knob", "weight", "Base", "")
    assert _values(bridge, url) == {("dial", "weight", "Heavy"): "heavy stuff"}
    bridge.undo_edit(url)
    assert _values(bridge, url)[("knob", "weight", "Base")] == "4.0"


def test_set_parameter_value_for_unknown_entity_fails(bridge: ProjectBridge, url: str) -> None:
    state = json.loads(bridge.set_parameter_value(url, "Widget", "nope", "weight", "Base", "1"))
    assert "No entity" in state["error"]


def test_reload_picks_up_changes_made_elsewhere(bridge: ProjectBridge, url: str) -> None:
    assert _contents(bridge, url)["alternatives"] == ["Base", "Heavy"]
    with DatabaseMapping(url) as db_map:
        db_map.update_alternative(name="Heavy", description="Changed")
        db_map.commit_session("From elsewhere")
    bridge.reload_database(url)
    scenario = bridge.set_scenario_alternatives(url, "Scenario", json.dumps(["Heavy"]))
    assert "error" not in json.loads(scenario)
    (tree,) = _contents(bridge, url)["scenario_tree"]
    assert tree["alternatives"] == [{"name": "Heavy", "description": "Changed"}]


def test_reload_keeps_uncommitted_edits(bridge: ProjectBridge, url: str) -> None:
    bridge.add_item(url, "alternative", json.dumps({"name": "Dark"}))
    bridge.reload_database(url)
    assert "Dark" in _contents(bridge, url)["alternatives"]
    assert json.loads(bridge.get_session_state(url))["dirty"]


def test_pivot_has_entities_as_rows_and_parameters_as_columns(bridge: ProjectBridge, url: str) -> None:
    pivot = json.loads(bridge.get_pivot(url, "Widget", "Base"))
    assert pivot["alternatives"] == ["Base", "Heavy"]
    assert pivot["alternative"] == "Base"
    assert pivot["parameters"] == ["weight"]
    assert pivot["rows"] == [
        {"entity": "knob", "cells": [{"text": "2.5", "editable": True, "empty": False}]},
        {"entity": "dial", "cells": [{"text": "", "editable": True, "empty": True}]},
    ]


def test_pivot_shows_only_values_of_selected_alternative(bridge: ProjectBridge, url: str) -> None:
    pivot = json.loads(bridge.get_pivot(url, "Widget", "Heavy"))
    assert pivot["alternative"] == "Heavy"
    assert all(row["cells"][0]["empty"] for row in pivot["rows"])


def test_pivot_falls_back_to_base_for_unknown_alternative(bridge: ProjectBridge, url: str) -> None:
    assert json.loads(bridge.get_pivot(url, "Widget", ""))["alternative"] == "Base"


def test_pivot_shows_uncommitted_edits(bridge: ProjectBridge, url: str) -> None:
    bridge.set_parameter_value(url, "Widget", "dial", "weight", "Base", "heavy")
    cell = json.loads(bridge.get_pivot(url, "Widget", "Base"))["rows"][1]["cells"][0]
    assert cell == {"text": "heavy", "editable": True, "empty": False}


@pytest.mark.parametrize(
    ("value", "text"), [("abc", "abc"), ("123", '"123"'), ("", '""'), (True, "true"), (None, "null"), (2, "2")]
)
def test_pivot_cell_text_round_trips_through_set_parameter_value(
    bridge: ProjectBridge, url: str, value: object, text: str
) -> None:
    from spinetoolbox.frontend.qt_ui.database_editor_backend import _cell_text

    assert _cell_text(value) == (text, True)
    bridge.set_parameter_value(url, "Widget", "dial", "weight", "Base", text)
    shown = json.loads(bridge.get_pivot(url, "Widget", "Base"))["rows"][1]["cells"][0]
    assert shown["text"] == text


def test_pivot_marks_complex_values_read_only(bridge: ProjectBridge, url: str) -> None:
    from spinedb_api import Map

    with DatabaseMapping(url) as db_map:
        db_map.add_parameter_value(
            entity_class_name="Widget",
            entity_byname=("dial",),
            parameter_definition_name="weight",
            alternative_name="Base",
            parsed_value=Map(["a"], [1.0]),
        )
        db_map.commit_session("Add map")
    cell = json.loads(bridge.get_pivot(url, "Widget", "Base"))["rows"][1]["cells"][0]
    assert cell == {"text": "Map", "editable": False, "empty": False}
    assert "Only plain" in json.loads(bridge.set_parameter_value(url, "Widget", "dial", "weight", "Base", "1"))["error"]


def test_commit_persists_edits_and_discard_drops_them(bridge: ProjectBridge, url: str) -> None:
    bridge.add_item(url, "alternative", json.dumps({"name": "Light"}))
    state = json.loads(bridge.commit_edits(url, "Add Light"))
    assert state == {"dirty": False, "can_undo": False, "can_redo": False}
    assert _committed_names(url, "alternative") == {"Base", "Heavy", "Light"}
    bridge.add_item(url, "alternative", json.dumps({"name": "Dark"}))
    bridge.discard_edits(url)
    assert _contents(bridge, url)["alternatives"] == ["Base", "Heavy", "Light"]
