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
    property bool showProperties: width >= 1150

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
                            text: "My Project"
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

                        contentWidth: Math.max(width, 1320 + 220 + 80)
                        contentHeight: Math.max(height, 190 + 140 + 80)

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
                                var controlOffset = Math.max(50, distance * 0.45)

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

                                drawConnection(ctx, inputCard, databaseCard)
                                drawConnection(ctx, databaseCard, modelCard)
                                drawConnection(ctx, modelCard, resultsDbCard)
                                drawConnection(ctx, resultsDbCard, resultCard)
                            }
                        }

                        // =================================================
                        // DESIGN CARDS
                        // =================================================

                        WorkflowCard {
                            id: inputCard

                            x: 80
                            y: 190

                            title: "Input data"
                            subtitle: "Source"
                            iconText: "↓"
                            accent: "#3b82f6"
                            status: "Connected"

                            onClicked: inputFileDialog.open()

                            // reflect the reference already stored in the project (e.g. set by the classic Qt UI)
                            Component.onCompleted: {
                                if (typeof projectBridge === "undefined")
                                    return

                                var existing = projectBridge.get_input_reference()

                                if (existing) {
                                    var parts = existing.split(/[\\/]/)

                                    inputCard.subtitle = parts[parts.length - 1]
                                    inputCard.status = "File selected"
                                }
                            }

                            FileDialog {
                                id: inputFileDialog

                                title: "Select input data file"

                                onAccepted: {
                                    // persisted to the project's Data Connection so the classic Qt UI sees the same file
                                    var displayName = projectBridge.set_input_reference(selectedFile.toString())

                                    inputCard.subtitle = displayName
                                    inputCard.status = "File selected"
                                }
                            }
                        }

                        WorkflowCard {
                            id: databaseCard

                            x: 390
                            y: 190

                            title: "Database"
                            subtitle: "Data"
                            iconText: "▤"
                            accent: "#14b8a6"
                            status: "Ready"
                        }

                        WorkflowCard {
                            id: modelCard

                            x: 700
                            y: 190

                            title: "Energy model"
                            subtitle: "Model"
                            iconText: "◇"
                            accent: "#8b5cf6"
                            status: "Ready"
                        }

                        WorkflowCard {
                            id: resultsDbCard

                            x: 1010
                            y: 190

                            title: "Results DB"
                            subtitle: "Database"
                            iconText: "▣"
                            accent: "#ec4899"
                            status: "Ready"
                        }

                        WorkflowCard {
                            id: resultCard

                            x: 1320
                            y: 190

                            title: "Results"
                            subtitle: "Output"
                            iconText: "✓"
                            accent: "#10b981"
                            status: "Ready"
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

                // =================================================
                // PROPERTIES PANEL
                // =================================================

                Rectangle {
                    Layout.preferredWidth: 300
                    Layout.fillHeight: true

                    visible: root.showProperties

                    color: "#ffffff"

                    border.color: "#e5e7eb"
                    border.width: 1

                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 20

                        spacing: 16

                        Label {
                            text: "Properties"
                            font.pixelSize: 16
                            font.bold: true
                        }

                        Rectangle {
                            Layout.fillWidth: true
                            height: 1
                            color: "#e5e7eb"
                        }

                        Label {
                            text: "Selected item"
                            opacity: 0.5
                            font.pixelSize: 11
                        }

                        Label {
                            text: "Energy model"
                            font.pixelSize: 15
                            font.bold: true
                        }

                        Label {
                            text: "Model"
                            opacity: 0.55
                        }

                        Item {
                            height: 8
                        }

                        Label {
                            text: "Name"
                            font.pixelSize: 11
                            opacity: 0.55
                        }

                        TextField {
                            Layout.fillWidth: true
                            text: "Energy model"
                        }

                        Label {
                            text: "Description"
                            font.pixelSize: 11
                            opacity: 0.55
                        }

                        TextArea {
                            Layout.fillWidth: true
                            Layout.preferredHeight: 100

                            placeholderText: "Add a description..."
                        }

                        Item {
                            Layout.fillHeight: true
                        }

                        Button {
                            Layout.fillWidth: true
                            text: "Open in Advanced Mode"
                        }
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

        width: 220
        height: 140

        radius: 12

        color: "#ffffff"

        border.color: hovered
                      ? accent
                      : "#e2e8f0"

        border.width: hovered ? 2 : 1

        property bool hovered: false

        signal clicked()

        scale: hovered ? 1.015 : 1

        Behavior on scale {
            NumberAnimation {
                duration: 120
            }
        }

        // Shadow-ish background
        Rectangle {
            anchors.fill: parent
            anchors.margins: 2

            z: -1

            radius: parent.radius

            color: "#000000"
            opacity: 0.04
        }

        MouseArea {
            anchors.fill: parent

            hoverEnabled: true
            cursorShape: Qt.PointingHandCursor

            onEntered: card.hovered = true
            onExited: card.hovered = false
            onClicked: card.clicked()
        }

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 16

            spacing: 8

            RowLayout {
                Layout.fillWidth: true

                Rectangle {
                    width: 34
                    height: 34

                    radius: 9

                    color: card.accent

                    Label {
                        anchors.centerIn: parent

                        text: card.iconText

                        color: "white"
                        font.pixelSize: 16
                        font.bold: true
                    }
                }

                Item {
                    Layout.fillWidth: true
                }

                Label {
                    text: "⋮"

                    opacity: 0.4
                    font.pixelSize: 18
                }
            }

            ColumnLayout {
                Layout.fillWidth: true
                spacing: 2

                Label {
                    text: card.title

                    font.pixelSize: 14
                    font.bold: true
                }

                Label {
                    text: card.subtitle

                    font.pixelSize: 11
                    opacity: 0.5
                }
            }

            RowLayout {
                Layout.fillWidth: true

                Rectangle {
                    width: 7
                    height: 7

                    radius: 4

                    color: "#22c55e"
                }

                Label {
                    text: card.status

                    font.pixelSize: 10
                    opacity: 0.6

                    Layout.fillWidth: true
                }
            }
        }
    }
}