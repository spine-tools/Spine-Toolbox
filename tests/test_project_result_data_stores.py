import json
from spinetoolbox.project_commands import SetResultDataStoreCommand
from tests.mock_helpers import add_ds


def test_data_store_is_not_a_result_database_by_default(spine_toolbox_with_project) -> None:
    assert not spine_toolbox_with_project.project().is_result_data_store("DS")


def test_result_marks_are_written_to_project_file(spine_toolbox_with_project) -> None:
    project = spine_toolbox_with_project.project()
    project.set_result_data_store("DS", True)
    project.save()
    with open(project.config_file) as project_file:
        saved = json.load(project_file)
    assert saved["project"]["result_data_stores"] == ["DS"]


def test_result_mark_follows_renamed_item(spine_toolbox_with_project) -> None:
    toolbox = spine_toolbox_with_project
    project = toolbox.project()
    add_ds(project, toolbox.item_factories, "DS")
    project.set_result_data_store("DS", True)
    assert project.rename_item("DS", "Renamed", "")
    assert project.is_result_data_store("Renamed")
    assert not project.is_result_data_store("DS")


def test_set_result_command_can_be_undone_and_redone(spine_toolbox_with_project) -> None:
    project = spine_toolbox_with_project.project()
    command = SetResultDataStoreCommand(project, "DS", True)
    command.redo()
    assert project.is_result_data_store("DS")
    command.undo()
    assert not project.is_result_data_store("DS")
