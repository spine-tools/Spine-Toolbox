from pathlib import Path
from PySide6.QtCore import QCoreApplication
import pytest
from spinetoolbox.config import PROJECT_CONFIG_DIR_NAME, PROJECT_FILENAME
from spinetoolbox.frontend.qt_ui import project_bridge
from spinetoolbox.frontend.qt_ui.project_bridge import ProjectBridge


@pytest.fixture(scope="module")
def application() -> QCoreApplication:
    return QCoreApplication.instance() or QCoreApplication([])


@pytest.fixture
def bridge(tmp_path: Path, application: QCoreApplication, monkeypatch: pytest.MonkeyPatch) -> ProjectBridge:
    monkeypatch.setattr(project_bridge, "update_recent_projects", lambda *args: None)
    return ProjectBridge(tmp_path / "current")


def _make_project(folder: Path) -> None:
    config_file = folder / PROJECT_CONFIG_DIR_NAME / PROJECT_FILENAME
    config_file.parent.mkdir(parents=True)
    config_file.write_text("{}", encoding="utf-8")


@pytest.mark.parametrize("nesting", [0, 1, 2])
def test_open_project_finds_project_up_to_two_levels_down(bridge: ProjectBridge, tmp_path: Path, nesting: int) -> None:
    chosen = tmp_path / "chosen"
    project = chosen.joinpath(*["nested"] * nesting)
    _make_project(project)
    assert bridge.open_project(str(chosen)) == project.name
    assert Path(bridge.project_dir) == project


def test_open_project_ignores_project_three_levels_down(bridge: ProjectBridge, tmp_path: Path) -> None:
    chosen = tmp_path / "chosen"
    _make_project(chosen / "a" / "b" / "c")
    messages = []
    bridge.setupStatusChanged.connect(lambda message, status: messages.append((message, status)))
    assert bridge.open_project(str(chosen)) == ""
    assert bridge.project_dir == ""
    assert len(messages) == 1
    assert messages[0][1] == "error"


def test_open_project_reports_folder_that_is_not_a_project(bridge: ProjectBridge, tmp_path: Path) -> None:
    messages = []
    bridge.setupStatusChanged.connect(lambda message, status: messages.append((message, status)))
    assert bridge.open_project(str(tmp_path)) == ""
    assert messages == [
        (
            f"{tmp_path} is not a Spine Toolbox project: no .spinetoolbox folder found in it "
            "or in the two folder levels below it",
            "error",
        )
    ]
