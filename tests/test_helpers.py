######################################################################################################################
# Copyright (C) 2017-2022 Spine project consortium
# Copyright Spine Toolbox contributors
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""Unit tests for the helpers module."""
import json
from pathlib import Path
import re
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import MagicMock, patch
from PySide6.QtCore import QObject, QSettings, Signal
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import QLineEdit, QWidget
from spine_engine.load_project_items import load_item_specification_factories
from spinetoolbox.config import PROJECT_FILENAME, PROJECT_LOCAL_DATA_DIR_NAME, PROJECT_LOCAL_DATA_FILENAME
from spinetoolbox.helpers import (
    HTMLTagFilter,
    add_keyboard_shortcut_to_tool_tip,
    add_keyboard_shortcuts_to_action_tool_tips,
    copy_files,
    create_dir,
    dir_is_valid,
    disconnect,
    erase_dir,
    file_is_valid,
    first_non_null,
    format_log_message,
    format_string_list,
    get_datetime,
    home_dir,
    interpret_icon_id,
    list_to_rich_text,
    load_local_project_data,
    load_project_dict,
    load_specification_from_file,
    make_icon_id,
    merge_dicts,
    order_key,
    plain_to_rich,
    plain_to_tool_tip,
    recursive_overwrite,
    rename_dir,
    rows_to_row_count_tuples,
    select_julia_executable,
    select_julia_project,
    select_python_interpreter,
    signal_waiter,
    try_number_from_string,
    tuple_itemgetter,
    unique_name,
)
from tests.mock_helpers import TestCaseWithQApplication, q_object


class TestHelpers(TestCaseWithQApplication):

    def test_format_log_message(self):
        stamp_pattern = re.compile(r"\[\d\d-\d\d-\d\d\d\d \d\d:\d\d:\d\d]")
        message = "test msg"

        def test_correctness(message_type, expected_color):
            formatted = format_log_message(message_type, message)
            stamp_start = formatted.find("[")
            stamp_end = formatted.find("]")
            without_stamp = formatted[:stamp_start] + formatted[stamp_end + 1 :]
            stamp = formatted[stamp_start : stamp_end + 1]
            expected = f"<span style='color:{expected_color};white-space: pre-wrap;'> {message}</span>"
            self.assertEqual(without_stamp, expected)
            self.assertIsNotNone(stamp_pattern.match(stamp))

        test_correctness("msg", "white")
        test_correctness("msg_success", "#00ff00")
        test_correctness("msg_error", "#ff3333")
        test_correctness("msg_warning", "yellow")

    def test_make_icon_id(self):
        icon_id = make_icon_id(3, 7)
        self.assertEqual(icon_id, 3 + (7 << 16))

    def test_interpret_icon_id(self):
        icon_code, color_code = interpret_icon_id(None)
        self.assertEqual(icon_code, 0xF1B2)
        self.assertEqual(color_code, 0xFF000000)
        icon_code, color_code = interpret_icon_id(3 + (7 << 16))
        self.assertEqual(icon_code, 3)
        self.assertEqual(color_code, 7)

    def test_first_non_null(self):
        self.assertEqual(first_non_null([23]), 23)
        self.assertEqual(first_non_null([None, 23]), 23)

    def test_create_dir(self):
        with TemporaryDirectory() as temp_dir:
            base_dir = Path(temp_dir, "base")
            create_dir(str(base_dir))
            self.assertTrue(base_dir.exists())
            create_dir(str(base_dir), "sub-folder")
            self.assertTrue((base_dir / "sub-folder").exists())

    def test_rename_dir(self):
        with TemporaryDirectory() as temp_dir:
            old_dir = Path(temp_dir, "old directory")
            old_dir.mkdir()
            file_in_dir = Path(old_dir, "file.fff")
            file_in_dir.touch()
            new_dir = Path(temp_dir, "new directory")
            logger = MagicMock()
            self.assertTrue(rename_dir(str(old_dir), str(new_dir), logger, "box_title"))
            self.assertFalse(old_dir.exists())
            self.assertTrue(new_dir.exists())
            files_in_new_dir = list(new_dir.iterdir())
            self.assertEqual(files_in_new_dir, [Path(new_dir, "file.fff")])

    def test_rename_dir_prompts_user_if_target_exists(self):
        with TemporaryDirectory() as temp_dir:
            old_dir = Path(temp_dir, "old directory")
            old_dir.mkdir()
            new_dir = Path(temp_dir, "new directory")
            new_dir.mkdir()
            logger = MagicMock()
            with unittest.mock.patch("spinetoolbox.helpers.QMessageBox") as mock_msg_box:
                self.assertFalse(rename_dir(str(old_dir), str(new_dir), logger, "box_title"))
                mock_msg_box.assert_called_once()
            self.assertTrue(old_dir.exists())
            self.assertTrue(new_dir.exists())

    def test_get_datetime(self):
        self.assertEqual(get_datetime(False), "")
        self.assertIsNotNone(re.match(r"\[\d\d-\d\d-\d\d\d\d \d\d:\d\d:\d\d]", get_datetime(True)))
        self.assertIsNotNone(re.match(r"\[\d\d:\d\d:\d\d]", get_datetime(True, False)))

    def test_copy_files(self):
        with TemporaryDirectory() as temp_dir:
            source_dir = Path(temp_dir, "source")
            source_dir.mkdir()
            source_file = Path(source_dir, "file")
            source_file.touch()
            destination_dir = Path(temp_dir, "destination")
            destination_dir.mkdir()
            destination_file = Path(destination_dir, source_file.name)
            copy_count = copy_files(str(source_dir), str(destination_dir))
            self.assertEqual(copy_count, 1)
            self.assertTrue(destination_file.exists())

    def test_copy_files_with_includes(self):
        with TemporaryDirectory() as temp_dir:
            source_dir = Path(temp_dir, "source")
            source_dir.mkdir()
            included = Path(source_dir, "file.1")
            included.touch()
            excluded = Path(source_dir, "file.2")
            excluded.touch()
            destination_dir = Path(temp_dir, "destination")
            destination_dir.mkdir()
            destination_file = Path(destination_dir, included.name)
            copy_count = copy_files(str(source_dir), str(destination_dir), includes=["*.1"])
            self.assertEqual(copy_count, 1)
            self.assertTrue(destination_file.exists())

    def test_copy_files_with_excludes(self):
        with TemporaryDirectory() as temp_dir:
            source_dir = Path(temp_dir, "source")
            source_dir.mkdir()
            included = Path(source_dir, "file.1")
            included.touch()
            excluded = Path(source_dir, "file.2")
            excluded.touch()
            destination_dir = Path(temp_dir, "destination")
            destination_dir.mkdir()
            destination_file = Path(destination_dir, included.name)
            copy_count = copy_files(str(source_dir), str(destination_dir), excludes=["*.2"])
            self.assertEqual(copy_count, 1)
            self.assertTrue(destination_file.exists())

    def test_erase_dir(self):
        with TemporaryDirectory() as temp_dir:
            directory = Path(temp_dir, "dir")
            file = Path(directory, "file")
            directory.mkdir()
            file.touch()
            self.assertTrue(erase_dir(str(directory)))
            self.assertFalse(directory.exists())

    def test_recursive_overwrite(self):
        with TemporaryDirectory() as temp_dir:
            source_dir = Path(temp_dir, "source")
            source_dir.mkdir()
            sub_dir = Path("subdir")
            (source_dir / sub_dir).mkdir()
            file_name = Path("file")
            source_file_path = source_dir / sub_dir / file_name
            with open(source_file_path, "w") as out:
                out.write("source")
            destination_dir = Path(temp_dir, "destination")
            destination_dir.mkdir()
            (destination_dir / sub_dir).mkdir()
            overwritten_file = destination_dir / sub_dir / file_name
            overwritten_file.touch()
            logger = MagicMock()
            recursive_overwrite(logger, str(source_dir), str(destination_dir))
            with open(overwritten_file) as input_:
                self.assertEqual(input_.readline(), "source")

    def test_tuple_itemgetter(self):
        def first(t):
            return t[0]

        item_getter = tuple_itemgetter(first, 1)
        self.assertEqual(item_getter([3]), (3,))
        item_getter = tuple_itemgetter(first, 2)
        self.assertEqual(item_getter([3]), 3)

    def test_format_string_list(self):
        self.assertEqual(format_string_list(["a", "b", "c"]), "<ul><li>a</li><li>b</li><li>c</li></ul>")

    def test_row_to_row_count_tuples(self):
        self.assertEqual(rows_to_row_count_tuples([]), [])
        self.assertEqual(rows_to_row_count_tuples([1, 2, 3, 5, 6, 9]), [(1, 3), (5, 2), (9, 1)])

    def test_try_number_from_string(self):
        self.assertEqual(try_number_from_string("text"), "text")
        self.assertEqual(try_number_from_string("23"), 23)
        self.assertEqual(try_number_from_string("2.3"), 2.3)

    def test_select_julia_executable(self):
        with TemporaryDirectory() as temp_dir:
            executable = Path(temp_dir, "julia.exe")
            executable.touch()
            line_edit = QLineEdit()
            parent_widget = QWidget()
            if sys.platform == "win32":
                with patch("spinetoolbox.helpers.win32gui.GetOpenFileNameW") as mock_native_dialog:
                    mock_native_dialog.return_value = [str(executable)]
                    select_julia_executable(parent_widget, line_edit)
                    mock_native_dialog.assert_called()
            else:
                with patch("spinetoolbox.helpers.QFileDialog.getOpenFileName", lambda *args: [str(executable)]):
                    select_julia_executable(None, line_edit)
            self.assertEqual(line_edit.text(), str(executable))
            line_edit.deleteLater()
            parent_widget.deleteLater()

    def test_select_julia_project(self):
        with TemporaryDirectory() as temp_dir:
            project_dir = Path(temp_dir, "project")
            project_dir.mkdir()
            with patch("spinetoolbox.helpers.QFileDialog.getExistingDirectory", lambda *args: str(project_dir)):
                line_edit = QLineEdit()
                select_julia_project(None, line_edit)
                self.assertEqual(line_edit.text(), str(project_dir))
                line_edit.deleteLater()

    def test_select_python_interpreter(self):
        with TemporaryDirectory() as temp_dir:
            executable = Path(temp_dir, "python.exe")
            executable.touch()
            line_edit = QLineEdit()
            parent_widget = QWidget()
            if sys.platform == "win32":
                with patch("spinetoolbox.helpers.win32gui.GetOpenFileNameW") as mock_native_dialog:
                    mock_native_dialog.return_value = [str(executable)]
                    select_python_interpreter(parent_widget, line_edit)
                    mock_native_dialog.assert_called()
            else:
                with patch("spinetoolbox.helpers.QFileDialog.getOpenFileName", lambda *args: [str(executable)]):
                    select_python_interpreter(None, line_edit)
            self.assertEqual(line_edit.text(), str(executable))
            line_edit.deleteLater()
            parent_widget.deleteLater()

    def test_initial_dir_for_python_open_dialogs(self):
        with TemporaryDirectory() as temp_dir:
            executable = Path(temp_dir, "python.exe")
            executable.touch()
            line_edit = QLineEdit()
            line_edit.setText(str(executable))
            python_in_path = "some/legit/path/python.exe"
            line_edit.setPlaceholderText(python_in_path)
            parent_widget = QWidget()
            if sys.platform == "win32":
                with patch("spinetoolbox.helpers.win32gui.GetOpenFileNameW") as mock_native_dialog:
                    mock_native_dialog.return_value = [str(executable)]
                    select_python_interpreter(parent_widget, line_edit)
                    # initial dir should be according to the text in line edit
                    self.assertEqual(mock_native_dialog.call_args[1]["File"], str(executable))
                    self.assertEqual(mock_native_dialog.call_args[1]["InitialDir"], home_dir())
                    with (
                        patch("spinetoolbox.helpers.os.path.exists") as mock_exists,
                        patch("spinetoolbox.helpers.os.path.abspath") as mock_abspath,
                    ):
                        mock_exists.return_value = True
                        mock_abspath.return_value = python_in_path
                        line_edit.clear()
                        select_python_interpreter(parent_widget, line_edit)
                        mock_exists.assert_called()
                        mock_abspath.assert_called()
                        # initial dir should be according to the placeholder text in line edit
                        self.assertEqual(mock_native_dialog.call_args[1]["File"], python_in_path)
                        self.assertEqual(mock_native_dialog.call_args[1]["InitialDir"], home_dir())
                    line_edit.clear()
                    line_edit.setPlaceholderText("")
                    select_python_interpreter(parent_widget, line_edit)
                    # initial dir should be the home dir
                    self.assertEqual(mock_native_dialog.call_args[1]["File"], None)
                    self.assertEqual(mock_native_dialog.call_args[1]["InitialDir"], home_dir())
            else:  # Linux et al.
                with patch("spinetoolbox.helpers.QFileDialog.getOpenFileName") as mock_open_file_dialog:
                    mock_open_file_dialog.return_value = [str(executable)]
                    select_python_interpreter(None, line_edit)
                    # initial dir should be according to the text in line edit
                    mock_open_file_dialog.assert_called_with(None, "Select Python Interpreter", str(executable))
                    with (
                        patch("spinetoolbox.helpers.os.path.exists") as mock_exists,
                        patch("spinetoolbox.helpers.os.path.abspath") as mock_abspath,
                    ):
                        mock_exists.return_value = True
                        mock_abspath.return_value = python_in_path
                        line_edit.clear()
                        select_python_interpreter(None, line_edit)
                        mock_exists.assert_called()
                        mock_abspath.assert_called()
                        # initial dir should be according to the placeholder text in line edit
                        mock_open_file_dialog.assert_called_with(None, "Select Python Interpreter", python_in_path)
                    line_edit.clear()
                    line_edit.setPlaceholderText("")
                    select_python_interpreter(None, line_edit)
                    # initial dir should be the home dir
                    mock_open_file_dialog.assert_called_with(None, "Select Python Interpreter", home_dir())
            line_edit.deleteLater()
            parent_widget.deleteLater()

    def test_file_is_valid(self):
        with TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir, "file")
            file_path.touch()
            with patch("spinetoolbox.helpers.QMessageBox"):
                self.assertTrue(file_is_valid(None, str(file_path), "Message title"))

    def test_dir_is_valid(self):
        with TemporaryDirectory() as temp_dir:
            with patch("spinetoolbox.helpers.QMessageBox"):
                self.assertTrue(dir_is_valid(None, temp_dir, "Message title"))

    def test_unique_name(self):
        self.assertEqual(unique_name("Prefix", []), "Prefix (1)")
        self.assertEqual(unique_name("Prefix", ["aaa"]), "Prefix (1)")
        self.assertEqual(unique_name("Prefix", ["Prefix (1)"]), "Prefix (2)")
        self.assertEqual(unique_name("Prefix", ["Prefix (2)"]), "Prefix (1)")
        self.assertEqual(unique_name("Prefix (1)", []), "Prefix (2)")
        self.assertEqual(unique_name("Prefix (1)", ["Prefix"]), "Prefix (2)")
        self.assertEqual(unique_name("Prefix (1)", {"Prefix", "Prefix (1)", "Prefix (2)"}), "Prefix (3)")
        self.assertEqual(
            unique_name(
                "p (9)", {"p", "p (1)", "p (2)", "p (3)", "p (4)", "p (5)", "p (6)", "p (7)", "p (8)", "p (9)"}
            ),
            "p (10)",
        )
        self.assertEqual(
            unique_name(
                "p (9)",
                {"p", "p (1)", "p (2)", "p (3)", "p (4)", "p (5)", "p (6)", "p (7)", "p (8)", "p (9)", "p (10)"},
            ),
            "p (11)",
        )

    def test_load_tool_specification_from_file(self):
        """Tests creating a PythonTool (specification) instance from a valid tool specification file."""
        spec_path = Path(__file__).parent / "test_resources" / "test_tool_spec.json"
        specification_factories = load_item_specification_factories("spine_items")
        logger = MagicMock()
        app_settings = QSettings("SpineProject", "Spine Toolbox")
        tool_spec = load_specification_from_file(str(spec_path), {}, specification_factories, app_settings, logger)
        self.assertIsNotNone(tool_spec)
        self.assertEqual(tool_spec.name, "Python Tool Specification")
        app_settings.deleteLater()

    def test_load_project_dict(self):
        with TemporaryDirectory() as project_dir:
            project_file = Path(project_dir, PROJECT_FILENAME)
            with project_file.open("w") as fp:
                json.dump("don't panic this is a test", fp)
            logger = MagicMock()
            project_dict = load_project_dict(project_dir, logger)
            self.assertEqual(project_dict, "don't panic this is a test")

    def test_load_local_project_data(self):
        with TemporaryDirectory() as project_dir:
            local_data_path = Path(project_dir, PROJECT_LOCAL_DATA_DIR_NAME)
            local_data_path.mkdir()
            local_data_file = local_data_path / PROJECT_LOCAL_DATA_FILENAME
            with local_data_file.open("w") as fp:
                json.dump("don't panic this is a test", fp)
            logger = MagicMock()
            project_dict = load_local_project_data(project_dir, logger)
            self.assertEqual(project_dict, "don't panic this is a test")

    def test_merge_dicts_with_empty_source(self):
        target = {}
        merge_dicts({}, target)
        self.assertEqual(target, {})

    def test_merge_dicts(self):
        target = {"a": {"b": 1}}
        merge_dicts({"a": {"c": 2}}, target)
        self.assertEqual(target, {"a": {"b": 1, "c": 2}})

    def test_merge_dicts_when_source_contains_nested_dict_not_present_in_target(self):
        target = {"a": {"b": {"c": 2}}}
        merge_dicts({"a": {"d": 3}}, target)
        self.assertEqual(target, {"a": {"b": {"c": 2}, "d": 3}})

    def test_merge_dicts_when_source_overwrites_data_in_target(self):
        target = {"a": {"b": 1}}
        merge_dicts({"a": {"b": 2}}, target)
        self.assertEqual(target, {"a": {"b": 2}})

    def test_order_key(self):
        self.assertEqual(["Humphrey_Bogart"], order_key("Humphrey_Bogart"))
        self.assertEqual(["Wes_", "000000001969", "_Anderson"], order_key("Wes_1969_Anderson"))
        self.assertEqual(
            ["\U0010FFFF", "000000001899", "_Alfred-", "000000001980", "Hitchcock"],
            order_key("1899_Alfred-1980Hitchcock"),
        )
        self.assertEqual([], order_key(""))


class TestHTMLTagFilter(unittest.TestCase):
    def test_simple_log_line(self):
        tag_filter = HTMLTagFilter()
        tag_filter.feed("Very <b>important</b> notification!")
        self.assertEqual(tag_filter.drain(), "Very important notification!")

    def test_replaces_br_by_newline(self):
        tag_filter = HTMLTagFilter()
        tag_filter.feed("First line<br>second line")
        self.assertEqual(tag_filter.drain(), "First line\nsecond line")


class TestPlainToRich(unittest.TestCase):
    def test_final_string_is_rich_text(self):
        self.assertEqual(plain_to_rich(""), "<qt></qt>")
        self.assertEqual(
            plain_to_rich("Just a plain string making its way to rich."),
            "<qt>Just a plain string making its way to rich.</qt>",
        )


class TestListToRichText(unittest.TestCase):
    def test_makes_rich_text(self):
        self.assertEqual(list_to_rich_text([]), "<qt></qt>")
        self.assertEqual(list_to_rich_text(["single"]), "<qt>single</qt>")
        self.assertEqual(list_to_rich_text(["first", "second"]), "<qt>first<br>second</qt>")


class TestPlainToToolTip(unittest.TestCase):
    def test_makes_tool_tips(self):
        self.assertIsNone(plain_to_tool_tip(None))
        self.assertIsNone(plain_to_tool_tip(""))
        self.assertEqual(plain_to_tool_tip("Is not None."), plain_to_rich("Is not None."))


class TestAddKeyboardShortcutToToolTip(TestCaseWithQApplication):
    def test_tool_tip_remains_unchanged_without_shortcut(self):
        with q_object(QAction()) as action:
            text = "<html><head /><body><p>A useful action</p></body></html>"
            action.setToolTip(text)
            add_keyboard_shortcut_to_tool_tip(action)
            self.assertEqual(action.toolTip(), text)

    def test_shortcut_get_added_to_html_tool_tip(self):
        with q_object(QAction()) as action:
            text = "<html><head /><body><p>A useful action</p></body></html>"
            action.setToolTip(text)
            action.setShortcut(QKeySequence("g"))
            add_keyboard_shortcut_to_tool_tip(action)
            self.assertEqual(action.toolTip(), "<qt><p>A useful action</p><p><em>G</em></p></qt>")

    def test_shortcut_get_added_to_plain_text_tool_tip(self):
        with q_object(QAction()) as action:
            text = "A useful action"
            action.setToolTip(text)
            action.setShortcut(QKeySequence("g"))
            add_keyboard_shortcut_to_tool_tip(action)
            self.assertEqual(action.toolTip(), "<qt><p>A useful action</p><p><em>G</em></p></qt>")

    def test_html_formatting_within_tool_tip_is_preserved(self):
        with q_object(QAction()) as action:
            text = "<html><head /><body><p>A <b>useful</b> action</p></body></html>"
            action.setToolTip(text)
            action.setShortcut(QKeySequence("g"))
            add_keyboard_shortcut_to_tool_tip(action)
            self.assertEqual(action.toolTip(), "<qt><p>A <b>useful</b> action</p><p><em>G</em></p></qt>")


class TestAddKeyboardShortcutsToActionToolTips(TestCaseWithQApplication):
    def test_ui_without_actions_works(self):
        class Ui:
            no_action = object()

        ui = Ui()
        add_keyboard_shortcuts_to_action_tool_tips(ui)

    def test_ui_with_action_without_shortscuts_leaves_tool_tips_as_is(self):
        class Ui:
            no_action = object()
            action = None

        ui = Ui()
        with q_object(QAction()) as action:
            action.setToolTip("A highly useful thing")
            ui.action = action
            add_keyboard_shortcuts_to_action_tool_tips(ui)
            self.assertEqual(action.toolTip(), "A highly useful thing")

    def test_shortcut_gets_appended_to_tool_tip(self):
        class Ui:
            no_action = object()
            action = None

        ui = Ui()
        with q_object(QAction()) as action:
            action.setToolTip("A highly useful thing")
            action.setShortcut(QKeySequence("w"))
            ui.action = action
            add_keyboard_shortcuts_to_action_tool_tips(ui)
            self.assertEqual(action.toolTip(), "<qt><p>A highly useful thing</p><p><em>W</em></p></qt>")


class TestDisconnect(TestCaseWithQApplication):
    def test_disconnects_signal(self):
        class Signaller(QObject):
            trigger = Signal()

        with q_object(Signaller()) as signaller:
            with signal_waiter(signaller.trigger, timeout=1) as receiver:
                signaller.trigger.emit()
                receiver.wait()
                self.assertTrue(receiver.triggered)

        with q_object(Signaller()) as signaller:
            with signal_waiter(signaller.trigger, timeout=0.1) as receiver:
                with disconnect(signaller.trigger, receiver.trigger):
                    signaller.trigger.emit()
                    with self.assertRaisesRegex(RuntimeError, "timeout exceeded"):
                        receiver.wait()
                self.assertFalse(receiver.triggered)
                signaller.trigger.emit()
                receiver.wait()
                self.assertTrue(receiver.triggered)


if __name__ == "__main__":
    unittest.main()
