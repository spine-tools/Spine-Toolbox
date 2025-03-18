"""
This script benchmarks SpineDBManager.get_item().
"""

import os
import sys

if sys.platform == "win32" and "HOMEPATH" not in os.environ:
    import pathlib

    os.environ["HOMEPATH"] = str(pathlib.Path(sys.executable).parent)

import time
from typing import Optional, Sequence
import pyperf
from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication
from benchmarks.utils import StdOutLogger
from spinedb_api import DatabaseMapping
from spinedb_api.temp_id import TempId
from spinetoolbox.spine_db_manager import SpineDBManager


def db_mngr_get_value(
    loops: int, db_mngr: SpineDBManager, db_map: DatabaseMapping, item_type, ids: Sequence[TempId]
) -> float:
    duration = 0.0
    for _ in range(loops):
        for id_ in ids:
            start = time.perf_counter()
            db_mngr.get_item(db_map, item_type, id_)
            duration += time.perf_counter() - start
    return duration


def run_benchmark(output_file: Optional[str]):
    if not QApplication.instance():
        QApplication()
    db_mngr = SpineDBManager(QSettings(), parent=None)
    logger = StdOutLogger()
    db_map = db_mngr.get_db_map("sqlite://", logger, create=True)
    with db_map:
        inner_loops = 10
        ids = []
        for i in range(inner_loops):
            item, error = db_map.add_entity_class_item(name=str(i))
            assert error is None
            ids.append(item["id"])
    runner = pyperf.Runner()
    benchmark = runner.bench_time_func(
        "SpineDBManager.get_value[parameter_value, DisplayRole]",
        db_mngr_get_value,
        db_mngr,
        db_map,
        "entity_class",
        ids,
        inner_loops=inner_loops,
    )
    if output_file:
        pyperf.add_runs(output_file, benchmark)
    db_mngr.close_all_sessions()
    db_mngr.deleteLater()


if __name__ == "__main__":
    run_benchmark(output_file="")
