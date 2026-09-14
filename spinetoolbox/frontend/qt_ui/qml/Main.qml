import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

ApplicationWindow {
    id: root

    visible: true
    width: 1400
    height: 850
    minimumWidth: 1100
    minimumHeight: 650

    title: "Spine Toolbox"

    color: "#f7f8fa"

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

            Layout.preferredWidth: 240
            Layout.fillHeight: true

            color: "#ffffff"

            border.color: "#e5e7eb"
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

                        color: "#2563eb"

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

                        Label {
                            text: "Spine Toolbox"
                            font.pixelSize: 15
                            font.bold: true
                        }

                        Label {
                            text: "Easy Mode"
                            opacity: 0.55
                            font.pixelSize: 11
                        }
                    }
                }

                // -------------------------------------------------
                // Navigation
                // -------------------------------------------------

                Label {
                    text: "WORKSPACE"
                    opacity: 0.45
                    font.pixelSize: 10
                    font.bold: true

                    Layout.leftMargin: 10
                    Layout.bottomMargin: 4
                }

                SidebarButton {
                    text: "Home"
                    iconText: "⌂"
                    selected: false
                }

                SidebarButton {
                    text: "Projects"
                    iconText: "▣"
                    selected: true
                }

                SidebarButton {
                    text: "Data"
                    iconText: "◇"
                }

                SidebarButton {
                    text: "Runs"
                    iconText: "▶"
                }

                Item {
                    Layout.fillHeight: true
                }

                Rectangle {
                    Layout.fillWidth: true
                    height: 1
                    color: "#e5e7eb"
                }

                SidebarButton {
                    text: "Settings"
                    iconText: "⚙"
                }

                SidebarButton {
                    text: "Help"
                    iconText: "?"
                }

                // -------------------------------------------------
                // Mode switch
                // -------------------------------------------------

                Rectangle {
                    Layout.fillWidth: true
                    Layout.topMargin: 12

                    height: 68
                    radius: 10

                    color: "#f5f6f8"
                    border.color: "#e5e7eb"

                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 12
                        spacing: 2

                        Label {
                            text: "Interface"
                            font.pixelSize: 11
                            opacity: 0.5
                        }

                        RowLayout {
                            Layout.fillWidth: true

                            Label {
                                text: "Easy Mode"
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
                        }
                    }

                    Button {
                        text: "Run project"
                    }

                    ToolButton {
                        text: "⋮"
                        font.pixelSize: 22
                    }

                    Rectangle {
                        width: 34
                        height: 34
                        radius: 17

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

                    color: "#f7f8fa"

                    // subtle grid
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

                            ctx.strokeStyle = "#94a3b8"
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

                            ctx.fillStyle = "#94a3b8"
                            ctx.fill()
                        }

                        onPaint: {
                            var ctx = getContext("2d")

                            ctx.clearRect(0, 0, width, height)

                            drawConnection(ctx, inputCard, modelCard)
                            drawConnection(ctx, modelCard, databaseCard)
                            drawConnection(ctx, databaseCard, resultCard)
                        }
                    }

                    // -------------------------------------------------
                    // Canvas header
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
                    }

                    WorkflowCard {
                        id: modelCard

                        x: 390
                        y: 190

                        title: "Energy model"
                        subtitle: "Model"
                        iconText: "◇"
                        accent: "#8b5cf6"
                        status: "Ready"
                    }

                    WorkflowCard {
                        id: databaseCard

                        x: 700
                        y: 190

                        title: "Results DB"
                        subtitle: "Database"
                        iconText: "▣"
                        accent: "#ec4899"
                        status: "Ready"
                    }

                    WorkflowCard {
                        id: resultCard

                        x: 1010
                        y: 190

                        title: "Results"
                        subtitle: "Output"
                        iconText: "✓"
                        accent: "#10b981"
                        status: "Ready"
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

        Layout.fillWidth: true
        implicitHeight: 42

        background: Rectangle {
            radius: 8

            color: sidebarButton.selected
                   ? "#eef2ff"
                   : sidebarButton.hovered
                     ? "#f5f6f8"
                     : "transparent"
        }

        contentItem: RowLayout {
            spacing: 12

            Label {
                text: sidebarButton.iconText

                Layout.preferredWidth: 22

                horizontalAlignment: Text.AlignHCenter

                font.pixelSize: 16

                opacity: sidebarButton.selected ? 1 : 0.6
            }

            Label {
                text: sidebarButton.text

                Layout.fillWidth: true

                font.pixelSize: 13
                font.bold: sidebarButton.selected
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

            onEntered: card.hovered = true
            onExited: card.hovered = false
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