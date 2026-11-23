import json
import os
from pathlib import Path
from PySide6.QtCore import QCoreApplication, QUrl
import pytest
from spinedb_api import DatabaseMapping
from spinetoolbox.config import PROJECT_CONFIG_DIR_NAME, PROJECT_FILENAME
from spinetoolbox.frontend.qt_ui.project_bridge import ProjectBridge
from spinetoolbox.frontend.qt_ui.run_results import changed_scenarios, commit_mark, files_written_since
from spinetoolbox.frontend.qt_ui.saved_plots import SavedPlots


@pytest.fixture(scope="module")
def application() -> QCoreApplication:
    return QCoreApplication.instance() or QCoreApplication([])


def _plot(directory: Path, name: str) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / name
    path.write_bytes(b"png")
    return path


def test_saved_plot_is_replaced_when_saved_again(tmp_path: Path) -> None:
    saved = SavedPlots(tmp_path / "saved")
    source = _plot(tmp_path / "plots", "plot_1.png")
    saved.save(source, "a", "Chain A", 1000.0)
    saved.save(source, "a", "Chain A", 1000.0)
    assert [entry["name"] for entry in saved.entries(None, None, "")] == ["plot_1"]


def test_saved_plots_are_filtered_by_chain_run_and_name(tmp_path: Path) -> None:
    saved = SavedPlots(tmp_path / "saved")
    saved.save(_plot(tmp_path / "plots", "cost.png"), "a", "Chain A", 1000.0)
    saved.save(_plot(tmp_path / "plots", "flow.png"), "b", "Chain B", 2000.0)
    assert [entry["name"] for entry in saved.entries("a", None, "")] == ["cost"]
    assert [entry["name"] for entry in saved.entries(None, 2000.0, "")] == ["flow"]
    assert [entry["name"] for entry in saved.entries(None, None, "FLO")] == ["flow"]
    assert [entry["name"] for entry in saved.entries(None, None, "")] == ["flow", "cost"]
    filters = saved.filters()
    assert [chain["name"] for chain in filters["chains"]] == ["Chain A", "Chain B"]
    assert [run["started"] for run in filters["runs"]] == [2000.0, 1000.0]


def test_deleting_a_saved_plot_removes_the_image(tmp_path: Path) -> None:
    saved = SavedPlots(tmp_path / "saved")
    saved.save(_plot(tmp_path / "plots", "cost.png"), "a", "Chain A", 1000.0)
    file_name = saved.entries(None, None, "")[0]["file"]
    saved.delete(file_name)
    assert saved.entries(None, None, "") == []
    assert not (tmp_path / "saved" / file_name).exists()


def test_files_written_since_lists_only_new_files(tmp_path: Path) -> None:
    old = _plot(tmp_path, "old.xlsx")
    new = _plot(tmp_path / "sub", "new.xlsx")
    old.touch()
    started = old.stat().st_mtime + 10
    new.touch()
    os.utime(new, (started + 5, started + 5))
    assert files_written_since(tmp_path, started) == [str(new)]


def test_scenarios_changed_after_a_commit_mark(tmp_path: Path) -> None:
    url = "sqlite:///" + (tmp_path / "db.sqlite").as_posix()
    with DatabaseMapping(url, create=True) as db_map:
        db_map.add_item("scenario", name="old")
        db_map.commit_session("first")
    mark = commit_mark(url)
    assert changed_scenarios(url, mark) == []
    with DatabaseMapping(url) as db_map:
        db_map.add_item("scenario", name="new")
        db_map.commit_session("second")
    assert changed_scenarios(url, mark) == ["new"]


def test_scenario_is_changed_when_its_alternative_gets_values(tmp_path: Path) -> None:
    url = "sqlite:///" + (tmp_path / "db.sqlite").as_posix()
    with DatabaseMapping(url, create=True) as db_map:
        db_map.add_item("entity_class", name="node")
        db_map.add_item("parameter_definition", entity_class_name="node", name="flow")
        db_map.add_item("entity", entity_class_name="node", name="n1")
        db_map.add_item("alternative", name="a1")
        db_map.add_item("scenario", name="s1")
        db_map.add_item("scenario_alternative", scenario_name="s1", alternative_name="a1", rank=1)
        db_map.commit_session("setup")
    mark = commit_mark(url)
    with DatabaseMapping(url) as db_map:
        db_map.add_item(
            "parameter_value",
            entity_class_name="node",
            entity_byname=("n1",),
            parameter_definition_name="flow",
            alternative_name="a1",
            parsed_value=2.0,
        )
        db_map.commit_session("values")
    assert changed_scenarios(url, mark) == ["s1"]


def test_plot_of_latest_run_is_saved_with_its_chain(tmp_path: Path, application: QCoreApplication) -> None:
    config_file = tmp_path / PROJECT_CONFIG_DIR_NAME / PROJECT_FILENAME
    config_file.parent.mkdir()
    config_file.write_text(json.dumps({"project": {}, "items": {}}), encoding="utf-8")
    bridge = ProjectBridge(tmp_path)
    plots_dir = tmp_path / PROJECT_CONFIG_DIR_NAME / "user_mode_plots"
    plot = _plot(plots_dir, "plot_1.png")
    (plots_dir / "latest_run.json").write_text(
        json.dumps({"chain": "a", "chain_name": "Chain A", "started": 1000.0}), encoding="utf-8"
    )
    assert bridge.save_plot(QUrl.fromLocalFile(str(plot)).toString())
    saved = json.loads(bridge.get_saved_plots("*", "*", ""))
    assert [(plot["name"], plot["chain_name"]) for plot in saved] == [("plot_1", "Chain A")]
    bridge.delete_saved_plot(saved[0]["file"])
    assert json.loads(bridge.get_saved_plots("*", "*", "")) == []
