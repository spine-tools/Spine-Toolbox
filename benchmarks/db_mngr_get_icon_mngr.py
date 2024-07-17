"""
This script benchmarks SpineDBManager.get_icon_mngr().
"""
import os
import sys

if sys.platform == "win32" and "HOMEPATH" not in os.environ:
    import pathlib
    os.environ["HOMEPATH"] = str(pathlib.Path(sys.executable).parent)

import time
from typing import Iterable, Optional
import pyperf
from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication
from spinedb_api import DatabaseMapping
from spinetoolbox.spine_db_icon_manager import SpineDBIconManager
from spinetoolbox.spine_db_manager import SpineDBManager


def db_mngr_get_icon_mngr(
    loops: int, db_mngr: SpineDBManager, db_maps: Iterable[DatabaseMapping]
) -> float:
    duration = 0.0
    for _ in range(loops):
        for db_map in db_maps:
            start = time.perf_counter()
            icon_mngr = db_mngr.get_icon_mngr(db_map)
            duration += time.perf_counter() - start
            assert isinstance(icon_mngr, SpineDBIconManager)
    return duration


def run_benchmark(output_file: Optional[str]):
    if not QApplication.instance():
        QApplication()
    db_mngr = SpineDBManager(QSettings(), parent=None)
    inner_loops = 10
    db_maps = [DatabaseMapping("sqlite://", create=True) for _ in range(inner_loops)]
    runner = pyperf.Runner()
    benchmark = runner.bench_time_func(
        "SpineDBManager.get_icon_mngr[always different db map]",
        db_mngr_get_icon_mngr,
        db_mngr,
        db_maps,
        inner_loops=inner_loops,
    )
    if output_file:
        pyperf.add_runs(output_file, benchmark)
    db_maps = inner_loops * [DatabaseMapping("sqlite://", create=True)]
    benchmark = runner.bench_time_func(
        "SpineDBManager.get_icon_mngr[always same db_map]",
        db_mngr_get_icon_mngr,
        db_mngr,
        db_maps,
        inner_loops=inner_loops,
    )
    if output_file:
        pyperf.add_runs(output_file, benchmark)
    db_mngr.close_all_sessions()
    db_mngr.deleteLater()


if __name__ == "__main__":
    run_benchmark(output_file="")
