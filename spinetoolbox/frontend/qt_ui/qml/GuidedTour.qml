import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// Dims the window, highlights one control at a time and explains it in a bubble.
// Each step is {target: Item or null, title: string, text: string}; a step without a target is centered.
Item {
    id: tour

    property var steps: []
    property int index: -1
    property rect spot: Qt.rect(0, 0, 0, 0)

    readonly property bool active: index >= 0
    readonly property var step: active ? steps[index] : null
    readonly property bool hasTarget: step !== null && !!step.target
    readonly property bool lastStep: index === steps.length - 1

    readonly property int spotPadding: 6
    readonly property int margin: 16
    readonly property color dimColor: "#99000000"

    signal finished()

    visible: active
    z: 1000
    focus: active

    function start(newSteps) {
        steps = newSteps
        index = 0
        updateSpot()
        forceActiveFocus()
    }

    function next() {
        if (lastStep)
            finish()
        else
            index += 1
    }

    function back() {
        if (index > 0)
            index -= 1
    }

    function finish() {
        index = -1
        finished()
    }

    function updateSpot() {
        // reads steps[index] because step and hasTarget may not be re-evaluated yet when index just changed
        var target = index >= 0 ? steps[index].target : null
        if (target) {
            var origin = target.mapToItem(tour, 0, 0)
            spot = Qt.rect(origin.x - spotPadding, origin.y - spotPadding,
                           target.width + 2 * spotPadding, target.height + 2 * spotPadding)
        } else {
            spot = Qt.rect(width / 2, height / 2, 0, 0)
        }
    }

    // position of the bubble: next to the spotlight, on the first side where it fits
    function bubblePosition() {
        var w = bubble.width
        var h = bubble.height

        if (!hasTarget)
            return Qt.point((width - w) / 2, (height - h) / 2)

        var gap = 14
        var centerX = Math.max(margin, Math.min(width - w - margin, spot.x + spot.width / 2 - w / 2))
        var centerY = Math.max(margin, Math.min(height - h - margin, spot.y + spot.height / 2 - h / 2))
        var candidates = {
            below: Qt.point(centerX, spot.y + spot.height + gap),
            above: Qt.point(centerX, spot.y - gap - h),
            right: Qt.point(spot.x + spot.width + gap, centerY),
            left: Qt.point(spot.x - gap - w, centerY)
        }
        var order = spot.x + spot.width / 2 < width * 0.2
            ? ["right", "below", "above", "left"]
            : ["below", "above", "right", "left"]

        for (var i = 0; i < order.length; i++) {
            var p = candidates[order[i]]
            if (p.x >= margin && p.y >= margin && p.x + w <= width - margin && p.y + h <= height - margin)
                return p
        }
        // no side has room (e.g. the target is most of the window): sit inside it, at the bottom
        return Qt.point(centerX, Math.max(margin, Math.min(height - h - margin, spot.y + spot.height - h - gap)))
    }

    onIndexChanged: updateSpot()
    onWidthChanged: updateSpot()
    onHeightChanged: updateSpot()

    Keys.onRightPressed: next()
    Keys.onReturnPressed: next()
    Keys.onEnterPressed: next()
    Keys.onLeftPressed: back()
    Keys.onEscapePressed: finish()

    // blocks the controls underneath while the tour is active
    MouseArea {
        anchors.fill: parent
        hoverEnabled: true
        acceptedButtons: Qt.AllButtons
        onWheel: function (wheel) { wheel.accepted = true }
    }

    Rectangle {
        x: 0
        y: 0
        width: tour.width
        height: Math.max(0, tour.spot.y)
        color: tour.dimColor
    }

    Rectangle {
        x: 0
        y: tour.spot.y
        width: Math.max(0, tour.spot.x)
        height: tour.spot.height
        color: tour.dimColor
    }

    Rectangle {
        x: tour.spot.x + tour.spot.width
        y: tour.spot.y
        width: Math.max(0, tour.width - x)
        height: tour.spot.height
        color: tour.dimColor
    }

    Rectangle {
        x: 0
        y: tour.spot.y + tour.spot.height
        width: tour.width
        height: Math.max(0, tour.height - y)
        color: tour.dimColor
    }

    Rectangle {
        visible: tour.hasTarget
        x: tour.spot.x
        y: tour.spot.y
        width: tour.spot.width
        height: tour.spot.height
        radius: 8
        color: "transparent"
        border.color: "#22c55e"
        border.width: 2
    }

    Rectangle {
        id: bubble

        width: Math.min(380, tour.width - 2 * tour.margin)
        height: content.implicitHeight + 32
        x: tour.bubblePosition().x
        y: tour.bubblePosition().y

        radius: 12
        color: "white"
        border.color: "#d1e7d8"

        Accessible.role: Accessible.Dialog
        Accessible.name: tour.step ? tour.step.title : ""

        // a Column with a fixed width, so the wrapped labels report their real height
        Column {
            id: content

            x: 16
            y: 16
            width: bubble.width - 32
            spacing: 8

            Label {
                width: parent.width
                text: qsTr("Step %1 of %2").arg(tour.index + 1).arg(tour.steps.length)
                color: "#64748b"
                font.pixelSize: 12
            }

            Label {
                width: parent.width
                text: tour.step ? tour.step.title : ""
                font.bold: true
                font.pixelSize: 16
                color: "#173d2b"
                wrapMode: Text.WordWrap
            }

            Label {
                width: parent.width
                text: tour.step ? tour.step.text : ""
                color: "#334155"
                wrapMode: Text.WordWrap
            }

            RowLayout {
                width: parent.width

                Item {
                    Layout.fillWidth: true
                }

                Button {
                    visible: !tour.lastStep
                    text: qsTr("Skip")
                    flat: true
                    focusPolicy: Qt.NoFocus
                    Accessible.name: qsTr("Skip the tour")
                    onClicked: tour.finish()
                }

                Button {
                    visible: tour.index > 0
                    text: qsTr("Back")
                    focusPolicy: Qt.NoFocus
                    Accessible.name: qsTr("Previous step")
                    onClicked: tour.back()
                }

                Button {
                    text: tour.lastStep ? qsTr("Done") : qsTr("Next")
                    highlighted: true
                    focusPolicy: Qt.NoFocus
                    Accessible.name: text
                    onClicked: tour.next()
                }
            }
        }
    }
}
