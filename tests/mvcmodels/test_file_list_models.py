######################################################################################################################
# Copyright (C) 2017-2022 Spine project consortium
# Copyright Spine Toolbox contributors
# This file is part of Spine Items.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################
import json
from pathlib import Path
from PySide6.QtCore import QMimeData, QModelIndex, Qt
from PySide6.QtGui import QFont
import pytest
from spine_engine.project_item.project_item_resource import CmdLineArg, LabelArg, file_resource, file_resource_in_pack
from spinetoolbox.helpers import signal_waiter
from spinetoolbox.mvcmodels.file_list_models import FileListModel, JumpCommandLineArgsModel, NewCommandLineArgItem
from tests.mock_helpers import q_object


@pytest.fixture()
def file_list_model(application):
    with q_object(FileListModel()) as model:
        yield model


class TestFileListModel:
    def test_duplicate_files(self, file_list_model):
        dupe1 = file_resource("item name", str(Path.cwd() / "path" / "to" / "other" / "file" / "A1"), "file label")
        dupe2 = file_resource_in_pack("item name", "pack label", str(Path.cwd() / "path" / "to" / "pack_file"))
        single_resources = [
            dupe1,
            dupe1,
            file_resource("item name", str(Path.cwd() / "path" / "to" / "file" / "A1"), "file label"),
            file_resource("item name", str(Path.cwd() / "path" / "to" / "file" / "Worcestershire"), "file label"),
            file_resource("item name", str(Path.cwd() / "path" / "to" / "file" / "Sriracha"), "file label"),
            file_resource("some name", str(Path.cwd() / "path" / "to" / "other" / "file" / "B12"), "file label"),
            file_resource("item name", str(Path.cwd() / "path" / "to" / "other" / "file" / "Sriracha"), "some label"),
        ]
        pack_resources = [
            file_resource_in_pack("item name", "pack label", str(Path.cwd() / "path" / "to" / "other" / "pack_file")),
            file_resource_in_pack("item name", "pack label", str(Path.cwd() / "path" / "to" / "some" / "pack_file")),
            file_resource_in_pack("item name", "pack label", str(Path.cwd() / "path" / "to" / "pack_file2")),
            dupe2,
            file_resource_in_pack("some name", "pack label", str(Path.cwd() / "path" / "to" / "pack_file21")),
            file_resource_in_pack("item name", "pack label", str(Path.cwd() / "path" / "to" / "pack_file3")),
            dupe2,
        ]
        file_list_model.update(single_resources + pack_resources)
        results = file_list_model.duplicate_paths()
        expected = set()
        expected.add(str(dupe1.path))
        expected.add(str(dupe2.path))
        assert results == expected


_EMPTY_LINE_TEXT = "Type arg, or drag and drop from Available resources..."


class TestJumpCommandLineArgsModel:
    def test_empty_model(self, application):
        with q_object(JumpCommandLineArgsModel()) as model:
            assert model.rowCount() == 1
            assert model.columnCount() == 1
            empty_item = model.item(0, 0)
            assert model.data(empty_item.index()) == _EMPTY_LINE_TEXT
            assert (
                model.data(empty_item.index(), Qt.ItemDataRole.ForegroundRole)
                == NewCommandLineArgItem.text_color_hint()
            )
            assert model.data(empty_item.index(), Qt.ItemDataRole.FontRole) is None
            assert empty_item.flags() & Qt.ItemFlag.ItemIsDropEnabled == Qt.ItemFlag.NoItemFlags
            assert empty_item.flags() & Qt.ItemFlag.ItemIsEditable != Qt.ItemFlag.NoItemFlags
            assert empty_item.rowCount() == 0
            assert model.headerData(0, Qt.Orientation.Horizontal) == "Command line arguments"

    def test_reset_model_with_non_label_arg(self, application):
        with q_object(JumpCommandLineArgsModel()) as model:
            args = [CmdLineArg("--version")]
            model.reset_model(args)
            assert model.rowCount() == 2
            assert model.columnCount() == 1
            arg_item = model.item(0, 0)
            assert model.data(arg_item.index()) == "--version"
            assert model.data(arg_item.index(), Qt.ItemDataRole.ForegroundRole) is None
            assert (
                model.data(arg_item.index(), Qt.ItemDataRole.FontRole) == JumpCommandLineArgsModel.non_label_arg_font()
            )
            assert arg_item.flags() & Qt.ItemFlag.ItemIsDropEnabled == Qt.ItemFlag.NoItemFlags
            assert arg_item.flags() & Qt.ItemFlag.ItemIsEditable != Qt.ItemFlag.NoItemFlags
            assert arg_item.rowCount() == 0
            empty_item = model.item(1, 0)
            assert model.data(empty_item.index()) == _EMPTY_LINE_TEXT
            assert empty_item.rowCount() == 0

    def test_reset_model_with_label_arg(self, application):
        with q_object(JumpCommandLineArgsModel()) as model:
            args = [LabelArg("<label>")]
            model.reset_model(args)
            assert model.rowCount() == 2
            assert model.columnCount() == 1
            label_item = model.item(0, 0)
            assert model.data(label_item.index()) == "<label>"
            assert model.data(label_item.index(), Qt.ItemDataRole.ForegroundRole) is None
            assert model.data(label_item.index(), Qt.ItemDataRole.FontRole) == QFont()
            assert label_item.flags() & Qt.ItemFlag.ItemIsDropEnabled == Qt.ItemFlag.NoItemFlags
            assert label_item.flags() & Qt.ItemFlag.ItemIsEditable == Qt.ItemFlag.NoItemFlags
            assert label_item.rowCount() == 0
            empty_item = model.item(1, 0)
            assert model.data(empty_item.index()) == _EMPTY_LINE_TEXT
            assert empty_item.rowCount() == 0

    def test_missing_label_is_red(self, application):
        with q_object(JumpCommandLineArgsModel()) as model:
            label = LabelArg("<missing>")
            label.missing = True
            model.reset_model([label])
            assert model.rowCount() == 2
            assert model.columnCount() == 1
            label_item = model.item(0, 0)
            assert model.data(label_item.index()) == "<missing>"
            assert model.data(label_item.index(), Qt.ItemDataRole.ForegroundRole) == Qt.GlobalColor.red
            assert model.data(label_item.index(), Qt.ItemDataRole.FontRole) == QFont()
            assert label_item.rowCount() == 0
            empty_item = model.item(1, 0)
            assert model.data(empty_item.index()) == _EMPTY_LINE_TEXT
            assert empty_item.rowCount() == 0

    def test_add_row_with_reset_model(self, application):
        with q_object(JumpCommandLineArgsModel()) as model:
            args = [CmdLineArg("--verbose")]
            model.reset_model(args)
            assert model.rowCount() == 2
            args = [CmdLineArg("--verbose"), CmdLineArg("--dry-run")]
            model.reset_model(args)
            assert model.rowCount() == 3
            arg_item = model.item(0, 0)
            assert model.data(arg_item.index()) == "--verbose"
            assert model.data(arg_item.index(), Qt.ItemDataRole.ForegroundRole) is None
            assert (
                model.data(arg_item.index(), Qt.ItemDataRole.FontRole) == JumpCommandLineArgsModel.non_label_arg_font()
            )
            arg_item = model.item(1, 0)
            assert model.data(arg_item.index()) == "--dry-run"
            assert model.data(arg_item.index(), Qt.ItemDataRole.ForegroundRole) is None
            assert (
                model.data(arg_item.index(), Qt.ItemDataRole.FontRole) == JumpCommandLineArgsModel.non_label_arg_font()
            )

    def test_remove_row_with_reset_model(self, application):
        with q_object(JumpCommandLineArgsModel()) as model:
            args = [CmdLineArg("--arg=1"), CmdLineArg("--arg=2")]
            model.reset_model(args)
            assert model.rowCount() == 3
            args = [CmdLineArg("--arg=2")]
            model.reset_model(args)
            assert model.rowCount() == 2
            arg_item = model.item(0, 0)
            assert model.data(arg_item.index()) == "--arg=2"
            empty_item = model.item(1, 0)
            assert model.data(empty_item.index()) == _EMPTY_LINE_TEXT

    def test_insert_label_with_reset_model(self, application):
        with q_object(JumpCommandLineArgsModel()) as model:
            args = [CmdLineArg("--arg")]
            model.reset_model(args)
            assert model.rowCount() == 2
            args = [LabelArg("<inserted>"), CmdLineArg("--arg")]
            model.reset_model(args)
            assert model.rowCount() == 3
            label_item = model.item(0, 0)
            assert model.data(label_item.index()) == "<inserted>"
            assert model.data(label_item.index(), Qt.ItemDataRole.ForegroundRole) is None
            assert model.data(label_item.index(), Qt.ItemDataRole.FontRole) == QFont()
            arg_item = model.item(1, 0)
            assert model.data(arg_item.index()) == "--arg"
            assert model.data(arg_item.index(), Qt.ItemDataRole.ForegroundRole) is None
            assert (
                model.data(arg_item.index(), Qt.ItemDataRole.FontRole) == JumpCommandLineArgsModel.non_label_arg_font()
            )
            empty_item = model.item(2, 0)
            assert model.data(empty_item.index()) == _EMPTY_LINE_TEXT

    def test_append_arg_emits_args_updated(self, application):
        with q_object(JumpCommandLineArgsModel()) as model:
            new_arg = CmdLineArg("--action")
            with signal_waiter(model.args_updated) as waiter:
                model.append_arg(new_arg)
                waiter.wait()
            assert waiter.args == ([new_arg],)

    def test_replace_arg_emit_args_updated(self, application):
        with q_object(JumpCommandLineArgsModel()) as model:
            args = [CmdLineArg("--action")]
            model.reset_model(args)
            new_arg = CmdLineArg("--reaction")
            with signal_waiter(model.args_updated) as waiter:
                model.replace_arg(0, new_arg)
                waiter.wait()
            assert waiter.args == ([new_arg],)

    def test_drop_label_emits_args_updated(self, application):
        with q_object(JumpCommandLineArgsModel()) as model:
            data = json.dumps(["labels", "label1;;label2"])
            mime_data = QMimeData()
            mime_data.setText(data)
            with signal_waiter(model.args_updated) as waiter:
                assert model.dropMimeData(mime_data, Qt.DropAction.CopyAction, 0, 0, QModelIndex())
                waiter.wait()
            assert waiter.args == ([LabelArg("label1"), LabelArg("label2")],)

    def test_move_rows_by_dropping_emits_args_updated(self, application):
        with q_object(JumpCommandLineArgsModel()) as model:
            args = [CmdLineArg("--arg=1"), CmdLineArg("--arg=2"), CmdLineArg("--arg=3")]
            model.reset_model(args)
            data = json.dumps(["rows", "1;;2"])
            mime_data = QMimeData()
            mime_data.setText(data)
            with signal_waiter(model.args_updated) as waiter:
                assert model.dropMimeData(mime_data, Qt.DropAction.CopyAction, 0, 0, QModelIndex())
                waiter.wait()
            assert waiter.args == ([CmdLineArg("--arg=2"), CmdLineArg("--arg=3"), CmdLineArg("--arg=1")],)
