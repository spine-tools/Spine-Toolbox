import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Dialogs

ApplicationWindow {
    id: root

    visible: true
    width: 1400
    height: 850
    minimumWidth: 480
    minimumHeight: 560

    // responsive breakpoints
    property bool compactSidebar: width < 900

    // name of the project currently open in the shared .spinetoolbox project.json
    property string currentProjectName: ""

    // items/connections loaded from project.json, rendered by the design canvas below
    property var workflow: ({ "items": [], "connections": [] })
    property var nodeItems: ({})

    property real designContentWidth: 1400
    property real designContentHeight: 640

    function iconForType(kind) {
        switch (kind) {
        case "Stack": return "▦"
        case "Data Store": return "▤"
        case "Data Connection": return "↓"
        case "Tool": return "◇"
        case "Importer": return "⇥"
        case "Exporter": return "⇤"
        case "Merger": return "⇄"
        case "View": return "✓"
        default: return "●"
        }
    }

    function accentForType(kind) {
        switch (kind) {
        case "Stack": return "#8a6fd8"
        case "Data Store": return "#14b8a6"
        case "Data Connection": return "#3b82f6"
        case "Tool": return "#8b5cf6"
        case "Importer": return "#f59e0b"
        case "Exporter": return "#ec4899"
        case "Merger": return "#0ea5e9"
        case "View": return "#10b981"
        default: return "#64748b"
        }
    }

    // assigns each item a (rank, lane) grid slot: rank = column by dependency depth (from -> to),
    // lane = row, reused from a node's single predecessor so linear chains stay on the same row
    function layoutWorkflow(items, connections) {
        var incoming = ({})
        var rank = ({})

        for (var i = 0; i < items.length; i++) {
            incoming[items[i].name] = []
            rank[items[i].name] = 0
        }

        for (var c = 0; c < connections.length; c++) {
            var connection = connections[c]
            if (incoming[connection.to] !== undefined && incoming[connection.from] !== undefined)
                incoming[connection.to].push(connection.from)
        }

        // longest path from a source node, found by relaxing edges until nothing changes
        var changed = true
        var guard = 0

        while (changed && guard < items.length + 5) {
            changed = false
            guard++

            for (var j = 0; j < connections.length; j++) {
                var conn = connections[j]
                if (rank[conn.from] === undefined || rank[conn.to] === undefined)
                    continue
                if (rank[conn.from] + 1 > rank[conn.to]) {
                    rank[conn.to] = rank[conn.from] + 1
                    changed = true
                }
            }
        }

        var maxRank = 0
        for (var k = 0; k < items.length; k++)
            maxRank = Math.max(maxRank, rank[items[k].name])

        var laneUsedByRank = []
        for (var r = 0; r <= maxRank; r++)
            laneUsedByRank.push(({}))

        function claimLane(atRank, preferredLane) {
            var used = laneUsedByRank[atRank]
            var candidate = preferredLane

            while (used[candidate] !== undefined)
                candidate++

            used[candidate] = true
            return candidate
        }

        var lane = ({})
        var ordered = items.slice().sort(function (a, b) { return rank[a.name] - rank[b.name] })

        for (var o = 0; o < ordered.length; o++) {
            var item = ordered[o]
            var preds = incoming[item.name] || []
            var preferred = 0

            if (preds.length === 1 && lane[preds[0]] !== undefined) {
                preferred = lane[preds[0]]
            } else if (preds.length > 1) {
                var sum = 0
                var count = 0

                for (var p = 0; p < preds.length; p++) {
                    if (lane[preds[p]] !== undefined) {
                        sum += lane[preds[p]]
                        count++
                    }
                }

                preferred = count > 0 ? Math.round(sum / count) : 0
            }

            lane[item.name] = claimLane(rank[item.name], preferred)
        }

        var columnWidth = 190
        var rowHeight = 96
        var padding = 40
        var maxLane = 0

        for (var m = 0; m < items.length; m++) {
            items[m].px = padding + rank[items[m].name] * columnWidth
            items[m].py = padding + lane[items[m].name] * rowHeight
            maxLane = Math.max(maxLane, lane[items[m].name])
        }

        return {
            width: padding * 2 + (maxRank + 1) * columnWidth,
            height: padding * 2 + (maxLane + 1) * rowHeight
        }
    }

    // fetches project.json's items/connections and lays them out on a rank/lane grid
    function loadWorkflow() {
        if (typeof projectBridge === "undefined")
            return

        var raw = projectBridge.get_workflow()

        if (!raw)
            return

        var parsed = JSON.parse(raw)
        var items = parsed.items || []
        var connections = parsed.connections || []

        if (items.length > 0) {
            var size = layoutWorkflow(items, connections)

            root.designContentWidth = size.width + 110
            root.designContentHeight = size.height + 34
        }

        root.nodeItems = ({})
        root.workflow = parsed

        connectionsCanvas.requestPaint()
    }


    Component.onCompleted: {
        if (typeof projectBridge !== "undefined")
            currentProjectName = projectBridge.get_project_name()

        loadWorkflow()
    }

    // shrink workflow cards so they keep fitting without horizontal scrolling on narrow windows
    property real cardScale: Math.max(0.5, Math.min(1, designFlick.width / root.designContentWidth))

    title: "Spine Toolbox"

    color: "#f4f9f5"

    // ---------------------------------------------------------
    // Main application layout
    // ---------------------------------------------------------

    RowLayout {
        anchors.fill: parent
        spacing: 0

        // =====================================================
        // SIDEBAR
        // =====================================================

        Rectangle {
            id: sidebar

            Layout.preferredWidth: root.compactSidebar ? 68 : 240
            Layout.fillHeight: true

            color: "#173d2b"

            border.color: "#12301f"
            border.width: 1

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 16
                spacing: 8

                // -------------------------------------------------
                // Logo
                // -------------------------------------------------

                RowLayout {
                    Layout.fillWidth: true
                    Layout.bottomMargin: 20

                    Rectangle {
                        width: 34
                        height: 34
                        radius: 9

                        color: "#22c55e"

                        Label {
                            anchors.centerIn: parent

                            text: "S"
                            color: "white"
                            font.pixelSize: 18
                            font.bold: true
                        }
                    }

                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 0

                        visible: !root.compactSidebar

                        Label {
                            text: "Spine Toolbox"
                            color: "white"
                            font.pixelSize: 15
                            font.bold: true
                        }

                        Label {
                            text: "Easy Mode"
                            color: "#bbf7d0"
                            opacity: 0.7
                            font.pixelSize: 11
                        }
                    }
                }

                // -------------------------------------------------
                // Navigation
                // -------------------------------------------------

                Label {
                    text: "WORKSPACE"
                    color: "#86efac"
                    opacity: 0.6
                    font.pixelSize: 10
                    font.bold: true

                    visible: !root.compactSidebar

                    Layout.leftMargin: 10
                    Layout.bottomMargin: 4
                }

                SidebarButton {
                    text: "Home"
                    iconText: "⌂"
                    selected: false
                    compact: root.compactSidebar
                }

                SidebarButton {
                    text: "Projects"
                    iconText: "▣"
                    selected: true
                    compact: root.compactSidebar
                }

                SidebarButton {
                    text: "Data"
                    iconText: "◇"
                    compact: root.compactSidebar

                    onClicked: projectBridge.open_database_editor()
                }

                SidebarButton {
                    text: "Runs"
                    iconText: "▶"
                    compact: root.compactSidebar
                }

                Item {
                    Layout.fillHeight: true
                }

                Rectangle {
                    Layout.fillWidth: true
                    height: 1
                    color: "#2f5a41"
                }

                SidebarButton {
                    text: "Settings"
                    iconText: "⚙"
                    compact: root.compactSidebar
                }

                SidebarButton {
                    text: "Help"
                    iconText: "?"
                    compact: root.compactSidebar
                }

                // -------------------------------------------------
                // Mode switch
                // -------------------------------------------------

                Rectangle {
                    Layout.fillWidth: true
                    Layout.topMargin: 12

                    visible: !root.compactSidebar

                    height: 68
                    radius: 10

                    color: "#1f4d34"
                    border.color: "#2f6b4a"

                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 12
                        spacing: 2

                        Label {
                            text: "Interface"
                            color: "#bbf7d0"
                            font.pixelSize: 11
                            opacity: 0.7
                        }

                        RowLayout {
                            Layout.fillWidth: true

                            Label {
                                text: "Easy Mode"
                                color: "white"
                                font.bold: true

                                Layout.fillWidth: true
                            }

                            Switch {
                                checked: true
                            }
                        }
                    }
                }
            }
        }

        // =====================================================
        // MAIN AREA
        // =====================================================

        ColumnLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true

            spacing: 0

            // -------------------------------------------------
            // TOP BAR
            // -------------------------------------------------

            Rectangle {
                Layout.fillWidth: true
                height: 68

                color: "#ffffff"

                border.color: "#e5e7eb"
                border.width: 1

                RowLayout {
                    anchors.fill: parent
                    anchors.leftMargin: 28
                    anchors.rightMargin: 24

                    spacing: 16

                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 1

                        Label {
                            text: root.currentProjectName || "No project open"
                            font.pixelSize: 19
                            font.bold: true
                        }

                        Label {
                            text: "Project workspace"
                            opacity: 0.5
                            font.pixelSize: 12

                            visible: root.width >= 700
                        }
                    }

                    Button {
                        text: "Open project"

                        onClicked: openProjectDialog.open()

                        FolderDialog {
                            id: openProjectDialog

                            title: "Choose a project folder (must contain .spinetoolbox)"

                            onAccepted: {
                                var name = projectBridge.open_project(selectedFolder.toString())

                                if (name)
                                    root.currentProjectName = name

                                root.loadWorkflow()
                            }
                        }
                    }

                    Button {
                        id: runProjectButton
                        text: "Run project"

                        background: Rectangle {
                            radius: 8
                            color: runProjectButton.hovered ? "#15803d" : "#16a34a"
                        }

                        contentItem: Label {
                            text: runProjectButton.text
                            color: "white"
                            font.bold: true

                            horizontalAlignment: Text.AlignHCenter
                            verticalAlignment: Text.AlignVCenter

                            leftPadding: 12
                            rightPadding: 12
                        }
                    }

                    ToolButton {
                        text: "⋮"
                        font.pixelSize: 22
                    }

                    Rectangle {
                        width: 34
                        height: 34
                        radius: 17

                        visible: root.width >= 640

                        color: "#e0e7ff"

                        Label {
                            anchors.centerIn: parent
                            text: "JD"
                            font.pixelSize: 11
                            font.bold: true
                        }
                    }
                }
            }

            // -------------------------------------------------
            // WORKSPACE
            // -------------------------------------------------

            RowLayout {
                Layout.fillWidth: true
                Layout.fillHeight: true

                spacing: 0

                // =================================================
                // DESIGN CANVAS
                // =================================================

                Rectangle {
                    Layout.fillWidth: true
                    Layout.fillHeight: true

                    color: "#f2f8f4"

                    // subtle grid, scrollable so fixed-position cards stay reachable on narrow windows
                    Flickable {
                        id: designFlick

                        anchors.fill: parent

                        contentWidth: Math.max(width, root.designContentWidth * root.cardScale)
                        contentHeight: Math.max(height, root.designContentHeight * root.cardScale)

                        clip: true
                        boundsBehavior: Flickable.StopAtBounds

                        Canvas {
                            id: connectionsCanvas

                            anchors.fill: parent
                            z: 0

                            function drawConnection(ctx, fromItem, toItem) {
                                var from = fromItem.mapToItem(connectionsCanvas, 0, 0)
                                var to = toItem.mapToItem(connectionsCanvas, 0, 0)

                                var startX = from.x + fromItem.width
                                var startY = from.y + fromItem.height / 2

                                var endX = to.x
                                var endY = to.y + toItem.height / 2

                                // Horizontal distance used to create a smooth curve
                                var distance = endX - startX
                                var controlOffset = Math.max(50, Math.abs(distance) * 0.45)

                                ctx.beginPath()

                                ctx.moveTo(startX, startY)

                                ctx.bezierCurveTo(
                                    startX + controlOffset,
                                    startY,
                                    endX - controlOffset,
                                    endY,
                                    endX,
                                    endY
                                )

                                ctx.strokeStyle = "#7c9c88"
                                ctx.lineWidth = 2
                                ctx.stroke()

                                // Arrow head
                                var arrowSize = 7

                                ctx.beginPath()

                                ctx.moveTo(endX, endY)
                                ctx.lineTo(
                                    endX - arrowSize,
                                    endY - arrowSize / 2
                                )
                                ctx.lineTo(
                                    endX - arrowSize,
                                    endY + arrowSize / 2
                                )
                                ctx.closePath()

                                ctx.fillStyle = "#7c9c88"
                                ctx.fill()
                            }

                            onPaint: {
                                var ctx = getContext("2d")

                                ctx.clearRect(0, 0, width, height)

                                var connections = root.workflow.connections || []

                                for (var i = 0; i < connections.length; i++) {
                                    var connection = connections[i]
                                    var fromItem = root.nodeItems[connection.from]
                                    var toItem = root.nodeItems[connection.to]

                                    if (fromItem && toItem)
                                        drawConnection(ctx, fromItem, toItem)
                                }
                            }
                        }

                        // =================================================
                        // DESIGN CARDS (one per project.json item)
                        // =================================================

                        Repeater {
                            model: root.workflow.items

                            WorkflowCard {
                                designX: modelData.px || 0
                                designY: modelData.py || 0
                                sizeFactor: root.cardScale

                                title: modelData.name
                                subtitle: modelData.subtitle
                                iconText: root.iconForType(modelData.type)
                                accent: root.accentForType(modelData.type)
                                isStack: modelData.type === "Stack"

                                Component.onCompleted: {
                                    root.nodeItems[modelData.name] = this
                                    connectionsCanvas.requestPaint()
                                }
                            }
                        }
                    }

                    // -------------------------------------------------
                    // Canvas header (overlays the scrollable canvas)
                    // -------------------------------------------------

                    RowLayout {
                        anchors.top: parent.top
                        anchors.left: parent.left
                        anchors.right: parent.right

                        anchors.margins: 24

                        Label {
                            text: "Design"
                            font.pixelSize: 15
                            font.bold: true

                            Layout.fillWidth: true
                        }

                        ToolButton {
                            text: "−"
                        }

                        ToolButton {
                            text: "+"
                        }

                        ToolButton {
                            text: "Fit"
                        }
                    }

                    // -------------------------------------------------
                    // Floating add button
                    // -------------------------------------------------

                    RoundButton {
                        anchors.right: parent.right
                        anchors.bottom: parent.bottom

                        anchors.rightMargin: 28
                        anchors.bottomMargin: 28

                        text: "+"
                        font.pixelSize: 22

                        ToolTip.visible: hovered
                        ToolTip.text: "Add item"
                    }
                }
            }
        }
    }

    // =============================================================
    // COMPONENTS
    // =============================================================

    component SidebarButton: AbstractButton {
        id: sidebarButton

        property string iconText: ""
        property bool selected: false
        property bool compact: false

        Layout.fillWidth: true
        implicitHeight: 42

        ToolTip.visible: compact && hovered
        ToolTip.text: sidebarButton.text

        background: Rectangle {
            radius: 8

            color: sidebarButton.selected
                   ? "#2f6b4a"
                   : sidebarButton.hovered
                     ? "#1f4d34"
                     : "transparent"
        }

        contentItem: RowLayout {
            spacing: 12

            Label {
                text: sidebarButton.iconText

                Layout.preferredWidth: 22

                horizontalAlignment: Text.AlignHCenter

                color: "white"
                font.pixelSize: 16

                opacity: sidebarButton.selected ? 1 : 0.6
            }

            Label {
                text: sidebarButton.text

                Layout.fillWidth: true

                visible: !sidebarButton.compact

                color: "white"
                font.pixelSize: 13
                font.bold: sidebarButton.selected

                opacity: sidebarButton.selected ? 1 : 0.75
            }
        }
    }

    // =============================================================

    component WorkflowCard: Rectangle {
        id: card

        property string title: ""
        property string subtitle: ""
        property string iconText: ""
        property string accent: "#3b82f6"
        property string status: ""
        property bool isStack: false

        property real designX: 0
        property real designY: 0
        property real sizeFactor: 1

        // initial layout from project.json; dragging then takes over and owns x/y directly
        x: designX * sizeFactor
        y: designY * sizeFactor

        width: 150 * sizeFactor
        height: 74 * sizeFactor

        radius: 10 * sizeFactor

        color: "#ffffff"

        border.color: hovered
                      ? accent
                      : (isStack ? Qt.lighter(accent, 1.6) : "#e2e8f0")

        border.width: hovered ? 2 : (isStack ? 2 : 1)

        property bool hovered: false

        signal clicked()

        scale: hovered ? 1.015 : 1
        z: dragArea.drag.active ? 10 : 1

        Behavior on scale {
            NumberAnimation {
                duration: 120
            }
        }

        // redraw arrows as the card is dragged around
        onXChanged: connectionsCanvas.requestPaint()
        onYChanged: connectionsCanvas.requestPaint()

        // Shadow-ish background
        Rectangle {
            anchors.fill: parent
            anchors.margins: 2

            z: -1

            radius: parent.radius

            color: "#000000"
            opacity: 0.04
        }

        // extra offset layers behind the card give a collapsed stack a "deck of cards" look
        Rectangle {
            visible: card.isStack
            anchors.fill: parent
            anchors.topMargin: 6 * card.sizeFactor
            anchors.leftMargin: 6 * card.sizeFactor

            z: -2

            radius: parent.radius
            color: "#ffffff"
            border.color: "#e2e8f0"
            border.width: 1
        }

        Rectangle {
            visible: card.isStack
            anchors.fill: parent
            anchors.topMargin: 12 * card.sizeFactor
            anchors.leftMargin: 12 * card.sizeFactor

            z: -3

            radius: parent.radius
            color: "#ffffff"
            border.color: "#e2e8f0"
            border.width: 1
        }

        MouseArea {
            id: dragArea

            anchors.fill: parent

            hoverEnabled: true
            cursorShape: drag.active ? Qt.ClosedHandCursor : Qt.PointingHandCursor

            drag.target: card
            drag.axis: Drag.XAndYAxis

            onEntered: card.hovered = true
            onExited: card.hovered = false
            onClicked: card.clicked()
        }

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 11 * card.sizeFactor

            spacing: 6 * card.sizeFactor

            RowLayout {
                Layout.fillWidth: true

                Rectangle {
                    width: 28 * card.sizeFactor
                    height: 28 * card.sizeFactor

                    radius: 8 * card.sizeFactor

                    color: card.accent

                    Label {
                        anchors.centerIn: parent

                        text: card.iconText

                        color: "white"
                        font.pixelSize: 14 * card.sizeFactor
                        font.bold: true
                    }
                }

                Item {
                    Layout.fillWidth: true
                }

                Label {
                    text: "⋮"

                    opacity: 0.4
                    font.pixelSize: 13 * card.sizeFactor
                }
            }

            Label {
                text: card.title

                Layout.fillWidth: true

                font.pixelSize: 13 * card.sizeFactor
                font.bold: true

                elide: Text.ElideRight
            }

            Label {
                text: card.subtitle

                visible: card.subtitle.length > 0

                Layout.fillWidth: true

                font.pixelSize: 9 * card.sizeFactor
                opacity: 0.55

                elide: Text.ElideRight
            }

            Item {
                Layout.fillHeight: true
            }
        }
    }
}