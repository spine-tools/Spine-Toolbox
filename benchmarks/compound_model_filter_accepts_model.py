"""
This script benchmarks CompoundModelBase.filter_accepts_model().
"""

import os
import sys

if sys.platform == "win32" and "HOMEPATH" not in os.environ:
    import pathlib

    os.environ["HOMEPATH"] = str(pathlib.Path(sys.executable).parent)

import time
from typing import Optional
import pyperf
from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication
from benchmarks.utils import StdOutLogger
from spinetoolbox.spine_db_editor.mvcmodels.compound_models import CompoundParameterValueModel, CompoundStackedModel
from spinetoolbox.spine_db_editor.mvcmodels.single_models import SingleModelBase
from spinetoolbox.spine_db_manager import SpineDBManager


def call_filter_accepts_model(loops: int, compound_model: CompoundStackedModel, single_model: SingleModelBase) -> float:
    duration = 0.0
    for _ in range(loops):
        start = time.perf_counter()
        compound_model.filter_accepts_model(single_model)
        duration += time.perf_counter() - start
    return duration


def run_benchmark(output_file: Optional[str]):
    if not QApplication.instance():
        QApplication()
    db_mngr = SpineDBManager(QSettings(), parent=None)
    logger = StdOutLogger()
    db_map = db_mngr.get_db_map("sqlite://", logger, create=True)
    with db_map:
        entity_class, error = db_map.add_entity_class_item(name="Object")
        assert error is None
        db_map.add_entity_class_item(name="Subject")
        relationship_class, error = db_map.add_entity_class_item(
            name="Object__Subject", dimension_name_list=("Object", "Subject")
        )
        assert error is None
    compound_model = CompoundParameterValueModel(None, db_mngr, db_map)
    compound_model.set_filter_class_ids({db_map: {entity_class["id"]}})
    single_model = SingleModelBase(compound_model, db_map, relationship_class["id"], committed=False)
    runner = pyperf.Runner()
    benchmark = runner.bench_time_func(
        "CompoundModelBase.filter_accepts_model[filter by class ids]",
        call_filter_accepts_model,
        compound_model,
        single_model,
    )
    if output_file:
        pyperf.add_runs(output_file, benchmark)
    db_mngr.close_all_sessions()
    db_mngr.deleteLater()


if __name__ == "__main__":
    run_benchmark(output_file="")
