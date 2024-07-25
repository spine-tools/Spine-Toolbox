"""
This script benchmarks CompoundModelBase.filter_accepts_model().
"""

import os
import sys
from PySide6.QtGui import QClipboard

if sys.platform == "win32" and "HOMEPATH" not in os.environ:
    import pathlib

    os.environ["HOMEPATH"] = str(pathlib.Path(sys.executable).parent)

import time
from typing import Optional, Union
from unittest.mock import patch
import pyperf
from PySide6.QtCore import QItemSelectionModel, QSettings
from PySide6.QtWidgets import QApplication
from benchmarks.utils import StdOutLogger
from spinetoolbox.spine_db_editor.widgets.spine_db_editor import SpineDBEditor
from spinetoolbox.spine_db_manager import SpineDBManager


def call_paste(loops: int, text: str) -> float:
    with patch("spinetoolbox.spine_db_editor.widgets.spine_db_editor.SpineDBEditor.restore_ui"), patch(
        "spinetoolbox.spine_db_editor.widgets.spine_db_editor.SpineDBEditor.show"
    ):
        db_mngr = SpineDBManager(QSettings(), parent=None)
        logger = StdOutLogger()
        db_map = db_mngr.get_db_map("sqlite://", logger, codename="perf", create=True)
        db_editor = SpineDBEditor(db_mngr, {"sqlite://": "perf"})
        QApplication.processEvents()
    entity_class, error = db_map.add_entity_class_item(name="A")
    assert error is None
    entity_class, error = db_map.add_entity_class_item(name="B")
    assert error is None
    table_view = db_editor.ui.tableView_entity_alternative
    model = db_editor.ui.tableView_entity_alternative.model()
    table_view.selectionModel().setCurrentIndex(model.index(0, 0), QItemSelectionModel.SelectionFlag.ClearAndSelect)

    with patch.object(QClipboard, "text", return_value=text), patch(
        "spinetoolbox.spine_db_editor.widgets.spine_db_editor.SpineDBEditor.show"
    ):
        start = time.perf_counter()
        table_view.paste()
        duration = time.perf_counter() - start
    db_mngr.close_all_sessions()
    while not db_map.closed:
        QApplication.processEvents()
    db_mngr.clean_up()
    db_editor.deleteLater()
    db_mngr.deleteLater()
    return duration


def load_and_format_file(filename: Union[bytes, str]) -> str:
    with open(filename, "r") as file:
        lines = file.readlines()
    formatted_string = "".join(lines).strip()
    return formatted_string


def run_benchmark(output_file: Optional[str]):
    """The idea would be to have the entities and entity alternatives form initial_data.txt already in
    the database and then measure the time it takes to also add the data.txt into the database."""
    if not QApplication.instance():
        QApplication()
    text = load_and_format_file(os.path.join("benchmarks", "resources", "table_paste_data.txt"))
    runner = pyperf.Runner(values=1, warmups=1)
    benchmark = runner.bench_time_func("CopyPasteTableView.paste[table_view, text]", call_paste, text)
    if output_file:
        pyperf.add_runs(output_file, benchmark)


if __name__ == "__main__":
    run_benchmark(output_file="")
