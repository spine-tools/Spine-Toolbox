import json
from pathlib import Path
from PySide6.QtCore import QCoreApplication
import pytest
from spinetoolbox.config import PROJECT_CONFIG_DIR_NAME, PROJECT_FILENAME
from spinetoolbox.frontend.qt_ui.project_bridge import ProjectBridge


@pytest.fixture(scope="module")
def application() -> QCoreApplication:
    return QCoreApplication.instance() or QCoreApplication([])


def _item(item_type: str, x: float) -> dict:
    return {"type": item_type, "x": x, "y": 0.0}


@pytest.fixture
def bridge(tmp_path: Path, application: QCoreApplication) -> ProjectBridge:
    project = {
        "project": {
            "stacks": {"group": {"name": "Group", "items": ["B", "D"]}},
            "chains": {
                "default": "first",
                "items": {
                    "first": {"name": "First", "entries": [{"item": "A"}, {"item": "C"}]},
                    "grouped": {"name": "Grouped", "entries": [{"item": "A"}, {"stack": "group"}]},
                    "member": {"name": "Member", "entries": [{"item": "B"}]},
                },
            },
            "connections": [
                {"from": ["A", "right"], "to": ["B", "left"]},
                {"from": ["B", "right"], "to": ["C", "left"]},
            ],
        },
        "items": {
            "A": _item("Tool", 0.0),
            "B": _item("Tool", 100.0),
            "C": _item("Tool", 200.0),
            "D": _item("Tool", 300.0),
        },
    }
    config_file = tmp_path / PROJECT_CONFIG_DIR_NAME / PROJECT_FILENAME
    config_file.parent.mkdir()
    config_file.write_text(json.dumps(project), encoding="utf-8")
    return ProjectBridge(tmp_path)


def _names(workflow: dict) -> set[str]:
    return {item["name"] for item in workflow["items"]}


def _links(workflow: dict) -> set[tuple[str, str]]:
    return {(connection["from"], connection["to"]) for connection in workflow["connections"]}


def test_chains_are_listed_with_the_default(bridge: ProjectBridge) -> None:
    chains = json.loads(bridge.get_chains())
    assert chains["default"] == "first"
    assert [chain["name"] for chain in chains["chains"]] == ["First", "Grouped", "Member"]


def test_chain_shows_only_its_items_and_bridges_links_through_the_others(bridge: ProjectBridge) -> None:
    workflow = json.loads(bridge.get_workflow("first"))
    assert _names(workflow) == {"A", "C"}
    assert _links(workflow) == {("A", "C")}


def test_stack_entry_shows_the_collapsed_stack(bridge: ProjectBridge) -> None:
    workflow = json.loads(bridge.get_workflow("grouped"))
    assert _names(workflow) == {"A", "Group"}


def test_item_entry_shows_a_stack_member_on_its_own(bridge: ProjectBridge) -> None:
    workflow = json.loads(bridge.get_workflow("member"))
    assert _names(workflow) == {"B"}


def test_no_chain_shows_the_whole_workflow(bridge: ProjectBridge) -> None:
    assert _names(json.loads(bridge.get_workflow())) == {"A", "Group", "C"}


def test_chain_members_cover_the_selected_chains_on_the_whole_workflow(bridge: ProjectBridge) -> None:
    assert set(json.loads(bridge.get_chain_members("first"))) == {"A", "C"}
    assert set(json.loads(bridge.get_chain_members("first\x1fmember"))) == {"A", "C", "Group"}


def test_hidden_items_stay_hidden_in_a_chain(tmp_path: Path, application: QCoreApplication) -> None:
    project = {
        "project": {
            "hidden_items": ["C"],
            "chains": {"default": None, "items": {"all": {"name": "All", "entries": [{"item": "A"}, {"item": "C"}]}}},
        },
        "items": {"A": _item("Tool", 0.0), "C": _item("Tool", 100.0)},
    }
    config_file = tmp_path / PROJECT_CONFIG_DIR_NAME / PROJECT_FILENAME
    config_file.parent.mkdir()
    config_file.write_text(json.dumps(project), encoding="utf-8")
    assert _names(json.loads(ProjectBridge(tmp_path).get_workflow("all"))) == {"A"}


def test_user_positions_are_saved_per_chain(bridge: ProjectBridge) -> None:
    bridge.set_user_positions("first", json.dumps({"A": {"x": 1, "y": 2}}))
    bridge.set_user_positions("", json.dumps({"A": {"x": 3, "y": 4}}))
    assert json.loads(bridge.get_user_positions("first")) == {"A": {"x": 1, "y": 2}}
    assert json.loads(bridge.get_user_positions("")) == {"A": {"x": 3, "y": 4}}
    bridge.reset_user_positions("first")
    assert json.loads(bridge.get_user_positions("first")) == {}
    assert json.loads(bridge.get_user_positions("")) == {"A": {"x": 3, "y": 4}}


def test_positions_saved_before_chains_belong_to_the_whole_workflow(bridge: ProjectBridge, tmp_path: Path) -> None:
    (tmp_path / PROJECT_CONFIG_DIR_NAME / "user_mode.json").write_text(
        json.dumps({"A": {"x": 5, "y": 6}}), encoding="utf-8"
    )
    assert json.loads(bridge.get_user_positions("")) == {"A": {"x": 5, "y": 6}}


@pytest.fixture
def store_bridge(tmp_path: Path, application: QCoreApplication) -> ProjectBridge:
    both = [{"item": "T"}, {"item": "S"}]
    project = {
        "project": {
            "chains": {"default": None, "items": {"a": {"name": "A", "entries": both}, "b": {"name": "B", "entries": both}}},
            "connections": [{"from": ["T", "right"], "to": ["S", "left"]}],
        },
        "items": {"T": _item("Tool", 0.0), "S": _item("Data Store", 100.0)},
    }
    config_file = tmp_path / PROJECT_CONFIG_DIR_NAME / PROJECT_FILENAME
    config_file.parent.mkdir()
    config_file.write_text(json.dumps(project), encoding="utf-8")
    return ProjectBridge(tmp_path)


def test_database_written_by_another_chain_is_warned_about(store_bridge: ProjectBridge) -> None:
    store_bridge._write_store_chains({"S": "a"})
    assert json.loads(store_bridge.get_store_warnings("b")) == {"S": "A"}
    assert json.loads(store_bridge.get_store_warnings("a")) == {}


def test_written_stores_leave_out_connections_that_purge_themselves(store_bridge: ProjectBridge) -> None:
    data = store_bridge._load()
    assert set(store_bridge._written_stores(data, {"T"})) == {"S"}
    data["project"]["connections"][0]["options"] = {"purge_before_writing": True}
    assert store_bridge._written_stores(data, {"T"}) == {}
