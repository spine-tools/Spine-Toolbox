"""Finds what a workflow run produced: scenarios written to a database and files written to a folder."""

import os
from pathlib import Path
from spinedb_api import DatabaseMapping


def commit_mark(url: str) -> int:
    """Returns the id of the newest commit of the database at url, or 0 if it can't be read."""
    try:
        with DatabaseMapping(url) as db_map:
            return max((row.id for row in db_map.query(db_map.commit_sq)), default=0)
    except Exception:
        return 0


def changed_scenarios(url: str, mark: int) -> list[str]:
    """Returns the names of scenarios that were created, or whose alternatives got values, after commit mark."""
    try:
        with DatabaseMapping(url) as db_map:
            value_sq = db_map.parameter_value_sq
            written_alternatives = {
                row.alternative_id
                for row in db_map.query(value_sq.c.alternative_id).filter(value_sq.c.commit_id > mark).distinct()
            }
            alternatives_of_scenario: dict[int, set[int]] = {}
            for row in db_map.query(db_map.scenario_alternative_sq):
                alternatives_of_scenario.setdefault(row.scenario_id, set()).add(row.alternative_id)
            return sorted(
                row.name
                for row in db_map.query(db_map.scenario_sq)
                if row.commit_id > mark or alternatives_of_scenario.get(row.id, set()) & written_alternatives
            )
    except Exception:
        return []


def files_written_since(directory: Path, started: float) -> list[str]:
    """Returns the files under directory modified at or after started."""
    found = []
    for folder, _dirs, names in os.walk(directory):
        for name in names:
            path = Path(folder, name)
            if path.stat().st_mtime >= started:
                found.append(str(path))
    return sorted(found)
