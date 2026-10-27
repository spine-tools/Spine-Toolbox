import json
from pathlib import Path
from PySide6.QtCore import QCoreApplication
import pytest
from spinedb_api import DatabaseMapping
from spinetoolbox.config import PROGRESS_MARKER, PROJECT_CONFIG_DIR_NAME, PROJECT_FILENAME
from spinetoolbox.frontend.qt_ui.project_bridge import ProjectBridge


@pytest.fixture(scope="module")
def application() -> QCoreApplication:
    return QCoreApplication.instance() or QCoreApplication([])


def _item(item_type: str, x: float, y: float) -> dict:
    return {"type": item_type, "x": x, "y": y}


@pytest.fixture
def workflow(tmp_path: Path, application: QCoreApplication) -> dict:
    project = {
        "project": {
            "stacks": {"group": {"name": "Group", "items": ["Source", "Importer"]}},
            "connections": [
                {"from": ["Source", "right"], "to": ["Importer", "left"]},
                {"from": ["Importer", "bottom"], "to": ["Store", "top"]},
            ],
        },
        "items": {
            "Source": _item("Data Connection", 0.0, 0.0),
            "Importer": _item("Importer", 100.0, 40.0),
            "Store": _item("Data Store", 100.0, 200.0),
        },
    }
    config_file = tmp_path / PROJECT_CONFIG_DIR_NAME / PROJECT_FILENAME
    config_file.parent.mkdir()
    config_file.write_text(json.dumps(project), encoding="utf-8")
    return json.loads(ProjectBridge(tmp_path).get_workflow())


def test_stack_is_placed_at_member_connected_outside_the_stack(workflow: dict) -> None:
    stack = next(item for item in workflow["items"] if item["name"] == "Group")
    assert (stack["x"], stack["y"]) == (100.0, 40.0)


def test_connections_keep_design_view_anchors(workflow: dict) -> None:
    connection = workflow["connections"][0]
    assert (connection["from"], connection["to"]) == ("Group", "Store")
    assert (connection["from_anchor"], connection["to_anchor"]) == ("bottom", "top")


_SCENARIO_FILTER = {"filter_settings": {"enabled_filter_types": {"scenario_filter": True}}}


def _filter_types(tmp_path: Path, scenarios: list[str], items: dict, connection: dict) -> list[str | None]:
    project = {"project": {"scenarios": scenarios, "connections": [connection]}, "items": items}
    config_file = tmp_path / PROJECT_CONFIG_DIR_NAME / PROJECT_FILENAME
    config_file.parent.mkdir()
    config_file.write_text(json.dumps(project), encoding="utf-8")
    workflow = json.loads(ProjectBridge(tmp_path).get_workflow())
    return [connection["filter_type"] for connection in workflow["connections"]]


@pytest.mark.parametrize(
    ("scenarios", "source_type", "target_type", "expected"),
    [
        (["Base"], "Data Store", "Tool", "scenario"),
        ([], "Data Store", "Tool", None),
        (["Base"], "Importer", "Data Store", None),
        (["Base"], "Data Connection", "Importer", None),
    ],
)
def test_scenario_filter_is_shown_only_for_data_store_source_with_scenarios(
    tmp_path: Path,
    application: QCoreApplication,
    scenarios: list[str],
    source_type: str,
    target_type: str,
    expected: str | None,
) -> None:
    items = {"A": _item(source_type, 0.0, 0.0), "B": _item(target_type, 200.0, 0.0)}
    connection = {"from": ["A", "right"], "to": ["B", "left"], **_SCENARIO_FILTER}
    assert _filter_types(tmp_path, scenarios, items, connection) == [expected]


def test_link_leaving_stack_carries_filter_of_filterable_link_inside_stack(
    tmp_path: Path, application: QCoreApplication
) -> None:
    project = {
        "project": {
            "scenarios": ["Base"],
            "stacks": {"group": {"name": "Group", "items": ["Source", "Importer"]}},
            "connections": [
                {"from": ["Source", "right"], "to": ["Importer", "left"], **_SCENARIO_FILTER},
                {"from": ["Importer", "right"], "to": ["Store", "left"], **_SCENARIO_FILTER},
            ],
        },
        "items": {
            "Source": _item("Data Store", 0.0, 0.0),
            "Importer": _item("Importer", 100.0, 0.0),
            "Store": _item("Data Store", 200.0, 0.0),
        },
    }
    config_file = tmp_path / PROJECT_CONFIG_DIR_NAME / PROJECT_FILENAME
    config_file.parent.mkdir()
    config_file.write_text(json.dumps(project), encoding="utf-8")
    bridge = ProjectBridge(tmp_path)
    connection = json.loads(bridge.get_workflow())["connections"][0]
    assert (connection["from"], connection["to"], connection["filter_type"]) == ("Group", "Store", "scenario")
    assert json.loads(bridge.get_connection_filters("Group", "Store"))["items"] == [{"name": "Base", "enabled": True}]


@pytest.mark.parametrize(("options", "expected"), [({"require_scenario_filter": True}, True), ({}, False)])
def test_required_filter_is_read_from_connection_options(
    tmp_path: Path, application: QCoreApplication, options: dict, expected: bool
) -> None:
    project = {
        "project": {
            "scenarios": ["Base"],
            "connections": [{"from": ["A", "right"], "to": ["B", "left"], "options": options, **_SCENARIO_FILTER}],
        },
        "items": {"A": _item("Data Store", 0.0, 0.0), "B": _item("Tool", 200.0, 0.0)},
    }
    config_file = tmp_path / PROJECT_CONFIG_DIR_NAME / PROJECT_FILENAME
    config_file.parent.mkdir()
    config_file.write_text(json.dumps(project), encoding="utf-8")
    assert json.loads(ProjectBridge(tmp_path).get_connection_filters("A", "B"))["required"] is expected


def _states_after(bridge: ProjectBridge, lines: list[str]) -> list[tuple[str, str]]:
    states = []
    bridge.itemRunStateChanged.connect(lambda name, state: states.append((name, state)))
    for line in lines:
        bridge._handle_run_output(line, "stdout")
    return states


def test_run_states_follow_progress_markers_and_aggregate_per_stack(
    tmp_path: Path, application: QCoreApplication
) -> None:
    bridge = ProjectBridge(tmp_path)
    bridge._display_members = {"Group": ["Source", "Importer"], "Store": ["Store"]}
    bridge._member_states = {"Source": "waiting", "Importer": "waiting", "Store": "waiting"}
    bridge._display_states = {"Group": "waiting", "Store": "waiting"}
    log = []
    bridge.executionLogAppended.connect(lambda text, kind: log.append(text))
    states = _states_after(
        bridge,
        [
            f"{PROGRESS_MARKER} running Source",
            f"{PROGRESS_MARKER} done Source",
            "some output",
            f"{PROGRESS_MARKER} running Importer",
            f"{PROGRESS_MARKER} done Importer",
            f"{PROGRESS_MARKER} failed Store",
        ],
    )
    assert states == [
        ("Group", "running"),
        ("Group", "waiting"),
        ("Group", "running"),
        ("Group", "done"),
        ("Store", "failed"),
    ]
    assert log == ["some output"]


def test_included_items_are_those_connected_to_selected_items(tmp_path: Path, application: QCoreApplication) -> None:
    bridge = ProjectBridge(tmp_path)
    data = {"project": {"connections": [{"from": ["A", "right"], "to": ["B", "left"]}]}}
    assert bridge._included_items({"A"}, data) == {"A", "B"}
    assert bridge._included_items({"C"}, data) == {"C"}


@pytest.fixture
def database_url(tmp_path: Path) -> str:
    url = f"sqlite:///{tmp_path / 'data.sqlite'}"
    with DatabaseMapping(url, create=True) as db_map:
        db_map.add_entity_class(name="Widget")
        db_map.add_entity(entity_class_name="Widget", name="knob")
        db_map.add_parameter_definition(entity_class_name="Widget", name="weight")
        db_map.add_parameter_value(
            entity_class_name="Widget",
            entity_byname=("knob",),
            parameter_definition_name="weight",
            alternative_name="Base",
            parsed_value=2.5,
        )
        db_map.add_alternative(name="Heavy", description="Heavier")
        db_map.add_scenario(name="Scenario")
        db_map.add_scenario_alternative(scenario_name="Scenario", alternative_name="Heavy", rank=2)
        db_map.add_scenario_alternative(scenario_name="Scenario", alternative_name="Base", rank=1)
        db_map.commit_session("Set up")
    return url


def test_database_contents_list_scenario_alternatives_in_rank_order(
    tmp_path: Path, application: QCoreApplication, database_url: str
) -> None:
    bridge = ProjectBridge(tmp_path)
    contents = json.loads(bridge.get_database_contents(database_url))
    assert contents["entity_classes"] == [{"name": "Widget", "entity_count": 1}]
    assert contents["alternatives"] == ["Base", "Heavy"]
    (scenario,) = contents["scenario_tree"]
    assert scenario["name"] == "Scenario"
    assert scenario["alternatives"] == [
        {"name": "Base", "description": scenario["alternatives"][0]["description"]},
        {"name": "Heavy", "description": "Heavier"},
    ]


def test_entity_class_values_are_read_from_database(
    tmp_path: Path, application: QCoreApplication, database_url: str
) -> None:
    bridge = ProjectBridge(tmp_path)
    assert json.loads(bridge.get_entity_class_values(database_url, "Widget")) == [
        {"entity": "knob", "parameter": "weight", "alternative": "Base", "value": "2.5"}
    ]
