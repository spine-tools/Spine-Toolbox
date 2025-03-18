"""
This script benchmarks SpineDBManager.get_value().
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
from benchmarks.utils import StdOutLogger
from spinedb_api import DatabaseMapping, to_database
from spinedb_api.db_mapping_base import PublicItem
from spinetoolbox.spine_db_manager import SpineDBManager


def db_mngr_get_value(
    loops: int, db_mngr: SpineDBManager, db_map: DatabaseMapping, items: Sequence[PublicItem], role: Qt.ItemDataRole
) -> float:
    duration = 0.0
    for _ in range(loops):
        for item in items:
            start = time.perf_counter()
            db_mngr.get_value(db_map, item, role)
            duration += time.perf_counter() - start
    return duration


def run_benchmark(output_file: Optional[str]):
    if not QApplication.instance():
        QApplication()
    db_mngr = SpineDBManager(QSettings(), parent=None)
    logger = StdOutLogger()
    db_map = db_mngr.get_db_map("sqlite://", logger, create=True)
    with db_map:
        db_map.add_entity_class_item(name="Object")
        db_map.add_parameter_definition_item(name="x", entity_class_name="Object")
        db_map.add_entity_item(name="object", entity_class_name="Object")
        value_items = []
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
            value_items.append(item)
    runner = pyperf.Runner()
    benchmark = runner.bench_time_func(
        "SpineDBManager.get_value[parameter_value, DisplayRole]",
        db_mngr_get_value,
        db_mngr,
        db_map,
        value_items,
        Qt.ItemDataRole.DisplayRole,
        inner_loops=len(value_items),
    )
    if output_file:
        pyperf.add_runs(output_file, benchmark)
    db_mngr.close_all_sessions()
    db_mngr.deleteLater()


if __name__ == "__main__":
    run_benchmark(output_file="")
