import json
from spinetoolbox.project_commands import SetItemInstructionCommand
from tests.mock_helpers import add_view


def test_instruction_is_empty_by_default(spine_toolbox_with_project) -> None:
    assert spine_toolbox_with_project.project().item_instruction("View") == ""


def test_empty_text_clears_instruction(spine_toolbox_with_project) -> None:
    project = spine_toolbox_with_project.project()
    project.set_item_instruction("View", "Check this first.")
    assert project.item_instruction("View") == "Check this first."
    project.set_item_instruction("View", "")
    assert project.item_instruction("View") == ""


def test_instructions_are_written_to_project_file(spine_toolbox_with_project) -> None:
    project = spine_toolbox_with_project.project()
    project.set_item_instruction("View", "Check this first.")
    project.save()
    with open(project.config_file) as project_file:
        saved = json.load(project_file)
    assert saved["project"]["instructions"] == {"items": {"View": "Check this first."}}


def test_instruction_follows_renamed_item(spine_toolbox_with_project) -> None:
    toolbox = spine_toolbox_with_project
    project = toolbox.project()
    add_view(project, toolbox.item_factories, "View")
    project.set_item_instruction("View", "Check this first.")
    assert project.rename_item("View", "Renamed", "")
    assert project.item_instruction("Renamed") == "Check this first."
    assert project.item_instruction("View") == ""


def test_set_instruction_command_can_be_undone_and_redone(spine_toolbox_with_project) -> None:
    project = spine_toolbox_with_project.project()
    project.set_item_instruction("View", "Old")
    command = SetItemInstructionCommand(project, "View", "New")
    command.redo()
    assert project.item_instruction("View") == "New"
    command.undo()
    assert project.item_instruction("View") == "Old"
