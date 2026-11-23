"""Plots the user chose to keep in the project."""

from datetime import datetime
import json
from pathlib import Path
import shutil


class SavedPlots:
    """A folder of plot images with an index of the chain and run each came from."""

    def __init__(self, directory: Path) -> None:
        self._directory = directory
        self._index_file = directory / "index.json"

    def _read(self) -> list[dict]:
        try:
            entries = json.loads(self._index_file.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return []
        return entries if isinstance(entries, list) else []

    def save(self, source: Path, chain_key: str, chain_name: str, started: float) -> None:
        """Copies source into the folder; saving the same plot of the same run again replaces it."""
        self._directory.mkdir(parents=True, exist_ok=True)
        file_name = f"{int(started)}_{chain_key or 'all'}_{source.name}"
        shutil.copy2(source, self._directory / file_name)
        entries = [entry for entry in self._read() if entry["file"] != file_name]
        entries.append(
            {"file": file_name, "name": source.stem, "chain": chain_key, "chain_name": chain_name, "started": started}
        )
        self._index_file.write_text(json.dumps(entries), encoding="utf-8")

    def delete(self, file_name: str) -> None:
        entries = self._read()
        kept = [entry for entry in entries if entry["file"] != file_name]
        if len(kept) == len(entries):
            return
        (self._directory / file_name).unlink(missing_ok=True)
        self._index_file.write_text(json.dumps(kept), encoding="utf-8")

    def entries(self, chain_key: str | None, started: float | None, query: str) -> list[dict]:
        """Returns the saved plots, newest first, limited to a chain and run if given and to names holding query."""
        matches = [
            {**entry, "path": str(self._directory / entry["file"]), "run_label": _run_label(entry)}
            for entry in self._read()
            if (chain_key is None or entry["chain"] == chain_key)
            and (started is None or entry["started"] == started)
            and query.lower() in entry["name"].lower()
        ]
        return sorted(matches, key=lambda entry: entry["started"], reverse=True)

    def filters(self) -> dict:
        """Returns the chains and runs that have saved plots."""
        entries = self._read()
        chains = {entry["chain"]: entry["chain_name"] for entry in entries}
        runs = {entry["started"]: _run_label(entry) for entry in entries}
        return {
            "chains": [{"key": key, "name": name} for key, name in sorted(chains.items(), key=lambda pair: pair[1])],
            "runs": [{"started": started, "label": label} for started, label in sorted(runs.items(), reverse=True)],
        }


def _run_label(entry: dict) -> str:
    return f"{datetime.fromtimestamp(entry['started']).strftime('%d.%m.%Y %H:%M')} - {entry['chain_name']}"
