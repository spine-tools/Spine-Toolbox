import json
from pathlib import Path
import pytest
from PySide6.QtCore import QCoreApplication
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


def test_progress_markers_are_aggregated_per_stack_and_hidden_from_log(
    tmp_path: Path, application: QCoreApplication
) -> None:
    bridge = ProjectBridge(tmp_path)
    bridge._display_members = {"Group": ["Source", "Importer"], "Store": ["Store"]}
    states = []
    log = []
    bridge.itemRunStateChanged.connect(lambda name, state: states.append((name, state)))
    bridge.executionLogAppended.connect(lambda text, kind: log.append(text))
    for line in (
        f"{PROGRESS_MARKER} running Source",
        f"{PROGRESS_MARKER} done Source",
        "some output",
        f"{PROGRESS_MARKER} running Importer",
        f"{PROGRESS_MARKER} done Importer",
        f"{PROGRESS_MARKER} failed Store",
    ):
        bridge._handle_run_output(line, "stdout")
    while bridge._state_queue:
        bridge._emit_next_run_state()
    assert states == [
        ("Group", "running"),
        ("Group", "queued"),
        ("Group", "running"),
        ("Group", "done"),
        ("Store", "failed"),
    ]
    assert log == ["some output"]


def test_skipped_does_not_override_done_and_final_state_completes_stack(
    tmp_path: Path, application: QCoreApplication
) -> None:
    bridge = ProjectBridge(tmp_path)
    bridge._display_members = {"Group": ["A", "B"]}
    for line in (f"{PROGRESS_MARKER} done A", f"{PROGRESS_MARKER} skipped A"):
        bridge._handle_run_output(line, "stdout")
    assert bridge._display_state("Group", final=False) == "queued"
    assert bridge._display_state("Group", final=True) == "done"
