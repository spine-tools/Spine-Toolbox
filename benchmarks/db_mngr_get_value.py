"""
This script benchmarks SpineDatabaseManager.get_item().
"""
import os
import sys

if sys.platform == "win32" and "HOMEPATH" not in os.environ:
    import pathlib
    os.environ["HOMEPATH"] = str(pathlib.Path(sys.executable).parent)

import time
from typing import Optional, Sequence
import pyperf
from PySide6.QtCore import QSettings, Qt
from PySide6.QtWidgets import QApplication
from spinetoolbox.spine_db_manager import SpineDBManager
from spinedb_api import DatabaseMapping, to_database
from spinedb_api.temp_id import TempId
from benchmarks.utils import StdOutLogger


def db_mngr_get_value(
    loops: int, db_mngr: SpineDBManager, db_map: DatabaseMapping, ids: Sequence[TempId], role: Qt.ItemDataRole
) -> float:
    duration = 0.0
    for _ in range(loops):
        for id_ in ids:
            start = time.perf_counter()
            db_mngr.get_value(db_map, "parameter_value", id_, role)
            duration += time.perf_counter() - start
    return duration


def run_benchmark(output_file: Optional[str]):
    if not QApplication.instance():
        QApplication()
    db_mngr = SpineDBManager(QSettings(), parent=None)
    logger = StdOutLogger()
    db_map = db_mngr.get_db_map("sqlite://", logger, create=True)
    db_map.add_entity_class_item(name="Object")
    db_map.add_parameter_definition_item(name="x", entity_class_name="Object")
    db_map.add_entity_item(name="object", entity_class_name="Object")
    value_ids = []
    for i in range(100):
        alternative_name = str(i)
        db_map.add_alternative_item(name=str(i))
        value, value_type = to_database(i)
        item, error = db_map.add_parameter_value_item(
            entity_class_name="Object",
            parameter_definition_name="x",
            entity_byname=("object",),
            alternative_name=alternative_name,
            value=value,
            type=value_type,
        )
        assert error is None
        value_ids.append(item["id"])
    runner = pyperf.Runner()
    benchmark = runner.bench_time_func(
        "SpineDatabaseManager.get_value[parameter_value, DisplayRole]",
        db_mngr_get_value,
        db_mngr,
        db_map,
        value_ids,
        Qt.ItemDataRole.DisplayRole,
        inner_loops=len(value_ids),
    )
    if output_file:
        pyperf.add_runs(output_file, benchmark)
    db_mngr.close_all_sessions()
    db_mngr.deleteLater()


if __name__ == "__main__":
    run_benchmark(output_file="")
