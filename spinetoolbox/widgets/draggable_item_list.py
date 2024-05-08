from PySide6.QtGui import QStandardItemModel, QStandardItem, QIcon, QBrush, QColor
from PySide6.QtCore import Qt, Slot, QModelIndex


class GenericItemsModel(QStandardItemModel):
    def __init__(self, toolbox):
        super().__init__()
        self.toolbox = toolbox
        self.add_project_items()
        self.add_specs_title()
        self._spec_model = self.toolbox.specification_model
        self._spec_model.rowsInserted.connect(self._insert_specs)

    def add_project_items(self):
        title = QStandardItem(QIcon(":/icons/share.svg"), "Generic Items")
        title.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        # title.setFlags(~Qt.ItemFlag.ItemIsEditable)
        self.insertRow(0, title)
        for item_type, factory in self.toolbox.item_factories.items():
            if factory.is_deprecated():
                continue
            icon = QIcon(factory.icon())
            item = QStandardItem(icon, item_type)
            title.appendRow(item)

    def add_specs_title(self):
        spec_title = QStandardItem(QIcon(":/icons/share.svg"), "Specifications")
        spec_title.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.insertRow(1, spec_title)

    @Slot(QModelIndex, int, int)
    def _insert_specs(self, parent, first, last):
        for row in range(first, last + 1):
            self._add_spec(row)

    def _add_spec(self, row):
        spec = self._spec_model.specification(row)
        if spec.plugin:
            return
        next_row = row + 1
        while True:
            next_spec = self._spec_model.specification(next_row)
            if next_spec is None or not next_spec.plugin:
                break
            next_row += 1
        factory = self.toolbox.item_factories[spec.item_type]
        icon = QIcon(factory.icon())
        # icon = self._icon_from_factory(factory)
        print(f"spec name:{spec.name}")
        for row in range(self.rowCount()):
            item = self.itemFromIndex(self.index(row, 0, QModelIndex()))
            item_name = item.data(Qt.ItemDataRole.DisplayRole)
            print(f"item:{item.data(Qt.ItemDataRole.DisplayRole)}")
            if item_name == "Specifications":
                spec_item = QStandardItem(icon, spec.name)
                item.appendRow(spec_item)

    @Slot(QModelIndex)
    def collapse_or_expand_children(self, index):
        if not index.isValid():
            return
        item = self.itemFromIndex(index)
        if item.hasChildren():
            if self.toolbox.ui.treeView_items.isExpanded(index):
                self.toolbox.ui.treeView_items.setExpanded(index, False)
            else:
                self.toolbox.ui.treeView_items.setExpanded(index, True)


def make_icon_background(color):
    color0 = color.name()
    color1 = color.lighter(140).name()
    return f"qlineargradient(x1: 1, y1: 1, x2: 0, y2: 0, stop: 0 {color0}, stop: 1 {color1});"


def make_treeview_item_ss(color):
    icon_background = make_icon_background(color)
    return f"QTreeView::item{{background: {icon_background}}}"

def make_treeview_ss(color):
    treeview_item_ss = make_treeview_item_ss(color)
    return "QTreeView::item:has-children {padding:5px; background-color: yellow; color: black; border: 1px solid gray; border-radius: 2px;}" + treeview_item_ss

# treeview_items_stylesheet = (
# "QTreeView::item {background-color: rgb(235, 235, 235); color: #1c1c1c;}"
# "QTreeView::item:has-children {padding:5px; background-color: yellow; color: black; border: 1px solid gray; border-radius: 2px;}"
# )
