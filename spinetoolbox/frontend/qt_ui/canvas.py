from PySide6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsRectItem, QGraphicsPathItem, QGraphicsTextItem
from PySide6.QtGui import QBrush, QColor, QPen, QPainterPath, QPainter
from PySide6.QtCore import QRectF, QPointF, Qt


class NodeItem(QGraphicsRectItem):
    def __init__(self, x, y, w=140, h=90, label="Node", kind: str = "tool"):
        super().__init__(0, 0, w, h)
        self.setPos(x, y)
        # visual style by kind (try Fluent tokens first)
        kind = (kind or "tool").lower()
        try:
            from .fluent_integration import get_token_colors

            colours = get_token_colors()
        except Exception:
            colours = {
                "stack": ("#8a6fd8", "#f7f4ff"),
                "database": ("#50bf8c", "#f2fff8"),
                "tool": ("#dca557", "#fffaf1"),
                "results": ("#f1a053", "#fff9f3"),
                "input": ("#58b3ed", "#f7fcff"),
            }

        border_col, bg_col = colours.get(kind, ("#b8c9bd", "#ffffff"))
        self.setBrush(QBrush(QColor(bg_col)))
        self.setPen(QPen(QColor(border_col), 2))
        self.setFlags(
            QGraphicsRectItem.ItemIsMovable
            | QGraphicsRectItem.ItemIsSelectable
            | QGraphicsRectItem.ItemSendsGeometryChanges
        )
        self.label = QGraphicsTextItem(label, self)
        # try to pick a readable text color based on background
        try:
            bg = QColor(bg_col)
            # luminance
            lum = (0.299 * bg.redF() + 0.587 * bg.greenF() + 0.114 * bg.blueF())
            text_col = "#111111" if lum > 0.6 else "#ffffff"
        except Exception:
            text_col = "#30453a"
        self.label.setDefaultTextColor(QColor(text_col))
        self.label.setPos(8, 8)
        self._connections = []

    def add_connection(self, conn):
        if conn not in self._connections:
            self._connections.append(conn)

    def remove_connection(self, conn):
        if conn in self._connections:
            self._connections.remove(conn)

    def itemChange(self, change, value):
        if change == QGraphicsRectItem.ItemPositionHasChanged:
            for c in list(self._connections):
                c.update_path()
        return super().itemChange(change, value)


class ConnectionItem(QGraphicsPathItem):
    def __init__(self, src: NodeItem, dst: NodeItem):
        super().__init__()
        self.src = src
        self.dst = dst
        pen = QPen(QColor("#8fae9b"), 3)
        pen.setCapStyle(Qt.RoundCap)
        self.setPen(pen)
        self.setZValue(-1)
        src.add_connection(self)
        dst.add_connection(self)
        self.update_path()

    def update_path(self):
        # compute simple cubic bezier between centers
        s = self.src.sceneBoundingRect().center()
        d = self.dst.sceneBoundingRect().center()
        path = QPainterPath(s)
        dx = (d.x() - s.x()) * 0.5
        c1 = QPointF(s.x() + dx, s.y())
        c2 = QPointF(d.x() - dx, d.y())
        path.cubicTo(c1, c2, d)
        self.setPath(path)

    def remove(self):
        self.src.remove_connection(self)
        self.dst.remove_connection(self)
        if self.scene():
            self.scene().removeItem(self)


class CanvasView(QGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setRenderHint(QPainter.Antialiasing)
        self.setViewportUpdateMode(QGraphicsView.BoundingRectViewportUpdate)
        self.setDragMode(QGraphicsView.RubberBandDrag)
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.setBackgroundBrush(QColor("#f3f5f3"))
        self.nodes = []
        self.connections = []

    def add_node(self, x=0, y=0, label="Node", kind: str = "tool") -> NodeItem:
        node = NodeItem(x, y, label=label, kind=kind)
        self.scene.addItem(node)
        self.nodes.append(node)
        return node

    def connect_nodes(self, src: NodeItem, dst: NodeItem) -> ConnectionItem:
        conn = ConnectionItem(src, dst)
        self.scene.addItem(conn)
        self.connections.append(conn)
        return conn

    def clear(self):
        self.scene.clear()
        self.nodes.clear()
        self.connections.clear()
