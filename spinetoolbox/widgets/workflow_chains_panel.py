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

"""Panel for defining the workflow chains that User Mode can show."""

import json
import typing
from PySide6.QtCore import QObject, Qt, Slot
from PySide6.QtWidgets import QInputDialog, QListWidgetItem, QMessageBox
from ..project_commands import SetChainsCommand
from ..project_item_icon import ProjectItemIcon

if typing.TYPE_CHECKING:
    from ..ui_main import ToolboxUI

_KEY_ROLE = Qt.ItemDataRole.UserRole


class WorkflowChainsPanel(QObject):
    """Lists the project's chains and creates, edits and removes them through the undo stack."""

    def __init__(self, toolbox: "ToolboxUI") -> None:
        super().__init__(toolbox)
        self._toolbox = toolbox
        ui = toolbox.ui
        self._list = ui.listWidget_chains
        self._list.setToolTip("Double-click a chain to select its items in Design View")
        self._list.itemDoubleClicked.connect(self._select_chain_items)
        self._list.itemSelectionChanged.connect(self._update_buttons)
        ui.pushButton_chain_new.clicked.connect(self._new_chain)
        ui.pushButton_chain_update.clicked.connect(self._update_chain)
        ui.pushButton_chain_rename.clicked.connect(self._rename_chain)
        ui.pushButton_chain_default.clicked.connect(self._toggle_default)
        ui.pushButton_chain_delete.clicked.connect(self._delete_chain)
        self.refresh()

    @Slot()
    def refresh(self) -> None:
        project = self._toolbox.project()
        current_key = self._current_key()
        self._list.clear()
        if project is not None:
            for key, chain in project.chains.items():
                label = chain["name"] + (" (default)" if key == project.default_chain else "")
                item = QListWidgetItem(label)
                item.setData(_KEY_ROLE, key)
                self._list.addItem(item)
                if key == current_key:
                    self._list.setCurrentItem(item)
        self._update_buttons()

    def _current_key(self) -> str | None:
        item = self._list.currentItem()
        return item.data(_KEY_ROLE) if item is not None and item.isSelected() else None

    def _update_buttons(self) -> None:
        ui = self._toolbox.ui
        has_project = self._toolbox.project() is not None
        has_chain = self._current_key() is not None
        ui.pushButton_chain_new.setEnabled(has_project)
        for button in (
            ui.pushButton_chain_update,
            ui.pushButton_chain_rename,
            ui.pushButton_chain_default,
            ui.pushButton_chain_delete,
        ):
            button.setEnabled(has_chain)

    def _selected_entries(self) -> list[dict]:
        """Returns the chain entries for the items selected in Design View: a stack when all its members are
        selected, otherwise each selected item on its own."""
        project = self._toolbox.project()
        scene = self._toolbox.ui.graphicsView.scene()
        names = {item.name() for item in scene.selectedItems() if isinstance(item, ProjectItemIcon)}
        entries = []
        for stack_key, stack in project.stacks.items():
            if names.issuperset(stack["items"]):
                entries.append({"stack": stack_key})
                names.difference_update(stack["items"])
        entries.extend({"item": name} for name in sorted(names))
        return entries

    def _push(self, chains: dict[str, dict], default_chain: str | None, text: str) -> None:
        project = self._toolbox.project()
        self._toolbox.undo_stack.push(SetChainsCommand(project, chains, default_chain, text))

    def _copy_chains(self) -> dict[str, dict]:
        return json.loads(json.dumps(self._toolbox.project().chains))

    def _ask_name(self, title: str, initial: str = "") -> str | None:
        project = self._toolbox.project()
        name, ok = QInputDialog.getText(self._toolbox, title, "Chain name:", text=initial)
        name = name.strip()
        if not ok or not name:
            return None
        if any(chain["name"] == name for chain in project.chains.values() if chain["name"] != initial):
            QMessageBox.warning(self._toolbox, "Cannot use name", f"A chain named <b>{name}</b> already exists.")
            return None
        return name

    @Slot(bool)
    def _new_chain(self, _checked: bool = False) -> None:
        entries = self._selected_entries()
        if not entries:
            QMessageBox.information(self._toolbox, "No items selected", "Select the chain's items in Design View first.")
            return
        name = self._ask_name("New chain")
        if name is None:
            return
        project = self._toolbox.project()
        chains = self._copy_chains()
        index = len(chains) + 1
        while f"chain_{index}" in chains:
            index += 1
        key = f"chain_{index}"
        chains[key] = {"name": name, "entries": entries}
        # the first chain becomes the default so User Mode has something to open on
        self._push(chains, project.default_chain or key, f"add chain '{name}'")

    @Slot(bool)
    def _update_chain(self, _checked: bool = False) -> None:
        key = self._current_key()
        entries = self._selected_entries()
        if not entries:
            QMessageBox.information(self._toolbox, "No items selected", "Select the chain's items in Design View first.")
            return
        chains = self._copy_chains()
        chains[key]["entries"] = entries
        self._push(chains, self._toolbox.project().default_chain, f"update chain '{chains[key]['name']}'")

    @Slot(bool)
    def _rename_chain(self, _checked: bool = False) -> None:
        key = self._current_key()
        chains = self._copy_chains()
        name = self._ask_name("Rename chain", chains[key]["name"])
        if name is None:
            return
        chains[key]["name"] = name
        self._push(chains, self._toolbox.project().default_chain, f"rename chain to '{name}'")

    @Slot(bool)
    def _toggle_default(self, _checked: bool = False) -> None:
        key = self._current_key()
        project = self._toolbox.project()
        default_chain = None if project.default_chain == key else key
        self._push(self._copy_chains(), default_chain, f"set default chain to '{project.chains[key]['name']}'")

    @Slot(bool)
    def _delete_chain(self, _checked: bool = False) -> None:
        key = self._current_key()
        project = self._toolbox.project()
        chains = self._copy_chains()
        name = chains.pop(key)["name"]
        default_chain = None if project.default_chain == key else project.default_chain
        self._push(chains, default_chain, f"delete chain '{name}'")

    @Slot(QListWidgetItem)
    def _select_chain_items(self, list_item: QListWidgetItem) -> None:
        project = self._toolbox.project()
        names = set()
        for entry in project.chains[list_item.data(_KEY_ROLE)]["entries"]:
            if "stack" in entry:
                names.update(project.stacks.get(entry["stack"], {}).get("items", []))
            else:
                names.add(entry["item"])
        scene = self._toolbox.ui.graphicsView.scene()
        scene.clearSelection()
        for name in names & set(project.all_item_names):
            project.get_item(name).get_icon().setSelected(True)
