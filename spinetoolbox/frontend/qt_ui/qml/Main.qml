import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Dialogs
import "Router.js" as Router

// root is a plain Item (Rectangle, for its color) rather than ApplicationWindow so this file can be
// embedded as a widget (see EasyModeWidget) as well as shown via QQuickView from qml_launcher.py
Rectangle {
    id: root

    width: 1400
    height: 850

    color: "#f4f9f5"

    // responsive breakpoints
    property bool compactSidebar: width < 900

    // name of the project currently open in the shared .spinetoolbox project.json
    property string currentProjectName: ""

    // transient banner shown while/after a project's setup script runs (see offerProjectSetup());
    // status is "info", "success" or "error"
    property string setupStatusMessage: ""
    property string setupStatusKind: "info"

    // transient banner shown while/after a workflow run; status is "info", "success" or "error"
    property string runStatusMessage: ""
    property string runStatusKind: "info"
    property bool executionRunning: false
    property ListModel executionLogModel: ListModel {}

    // surfaces projectBridge.has_unselected_scenarios() in the top bar, refreshed whenever the
    // workflow reloads or a scenario checkbox is toggled (see refreshScenarioWarning())
    property bool hasUnselectedScenarios: false

    // surfaces projectBridge.has_starved_scenarios(): true when some item has no scenarios enabled
    // and nothing else feeding the same downstream target does either, so it would run with no data
    property bool hasStarvedScenarios: false

    function refreshScenarioWarning() {
        if (typeof projectBridge === "undefined")
            return

        root.hasUnselectedScenarios = projectBridge.has_unselected_scenarios()
        root.hasStarvedScenarios = projectBridge.has_starved_scenarios()
    }

    // installs/runs a project's bundled setup script automatically, if it has one
    function offerProjectSetup() {
        if (typeof projectBridge === "undefined")
            return

        if (projectBridge.has_setup_script() && !projectBridge.is_project_setup_done())
            projectBridge.install_project_dependencies()
    }

    Connections {
        target: typeof projectBridge !== "undefined" ? projectBridge : null

        function onSetupStatusChanged(message, status) {
            root.setupStatusMessage = message
            root.setupStatusKind = status
            setupStatusTimer.restart()
        }

        function onRunStatusChanged(message, status) {
            root.runStatusMessage = message
            root.runStatusKind = status
            runStatusTimer.restart()
        }

        function onExecutionStateChanged(running) {
            root.executionRunning = running

            // a new run starts from a clean slate; the bridge sends the final state of every card when it ends
            if (running)
                root.itemRunStates = {}
        }

        function onItemRunStateChanged(name, state) {
            var states = Object.assign({}, root.itemRunStates)
            states[name] = state
            root.itemRunStates = states
        }

        function onPlotsChanged() {
            root.plotUrls = projectBridge.get_plots()

            if (root.plotUrls.length > 0)
                root.currentView = "results"
        }

        function onExecutionLogAppended(line, kind) {
            root.executionLogModel.append({ "text": line, "kind": kind })

            if (root.executionLogModel.count > 2000)
                root.executionLogModel.remove(0)
        }
    }

    Timer {
        id: setupStatusTimer
        interval: 6000
        onTriggered: root.setupStatusMessage = ""
    }

    Timer {
        id: runStatusTimer
        interval: 6000
        onTriggered: root.runStatusMessage = ""
    }

    // "workflow" (project canvas) or "database" (data browser), switched from the sidebar
    property string currentView: "workflow"

    // file URLs of the images produced by the latest run
    property var plotUrls: []

    // card name -> "running", "done" or "failed" for the current/latest run
    property var itemRunStates: ({})

    // Data page state: project.json's Data Stores, the selected one's contents, and the selected
    // entity class' parameter values, all fetched from ProjectBridge on demand
    property var databases: []
    property bool databasesLoaded: false
    property string selectedDatabaseUrl: ""
    property var databaseContents: ({ "entity_classes": [], "alternatives": [], "scenarios": [] })
    property string selectedEntityClass: ""
    property var entityClassValues: []

    function loadDatabases() {
        root.databasesLoaded = true

        if (typeof projectBridge === "undefined")
            return

        var raw = projectBridge.get_databases()
        root.databases = raw ? JSON.parse(raw) : []

        if (root.databases.length > 0)
            root.selectDatabase(root.databases[0].url)
    }

    function selectDatabase(url) {
        root.selectedDatabaseUrl = url
        root.selectedEntityClass = ""
        root.entityClassValues = []

        if (typeof projectBridge === "undefined" || !url) {
            root.databaseContents = ({ "entity_classes": [], "alternatives": [], "scenarios": [] })
            return
        }

        var raw = projectBridge.get_database_contents(url)
        root.databaseContents = raw ? JSON.parse(raw) : ({ "entity_classes": [], "alternatives": [], "scenarios": [] })
    }

    function selectEntityClass(name) {
        root.selectedEntityClass = name

        if (typeof projectBridge === "undefined" || !root.selectedDatabaseUrl) {
            root.entityClassValues = []
            return
        }

        var raw = projectBridge.get_entity_class_values(root.selectedDatabaseUrl, name)
        root.entityClassValues = raw ? JSON.parse(raw) : []
    }

    // items/connections loaded from project.json, rendered by the design canvas below
    property var workflow: ({ "items": [], "connections": [] })
    property var nodeItems: ({})
    // nodeItems is mutated in place (see WorkflowCard.onCompleted below), which doesn't emit a change
    // signal on its own; bindings that need to react to it becoming populated depend on this instead
    property int nodeItemsTick: 0

    // names of the currently selected cards, so a drag on any one of them moves the whole group
    property var selectedNames: ({})
    property rect rubberRect: Qt.rect(0, 0, 0, 0)
    property bool rubberActive: false

    function clearSelection() {
        root.selectedNames = ({})
    }

    function selectOnly(name) {
        var only = ({})
        only[name] = true
        root.selectedNames = only
    }

    function toggleSelection(name) {
        var copy = Object.assign({}, root.selectedNames)

        if (copy[name])
            delete copy[name]
        else
            copy[name] = true

        root.selectedNames = copy
    }

    function rectsIntersect(a, b) {
        return a.x < b.x + b.width && a.x + a.width > b.x
               && a.y < b.y + b.height && a.y + a.height > b.y
    }

    // selects every card whose bounds overlap the given rectangle, drawn while dragging on empty canvas
    function selectWithinRect(area, additive) {
        var selection = additive ? Object.assign({}, root.selectedNames) : ({})

        for (var name in root.nodeItems) {
            var nodeItem = root.nodeItems[name]

            if (nodeItem && root.rectsIntersect(area, Qt.rect(nodeItem.x, nodeItem.y, nodeItem.width, nodeItem.height)))
                selection[name] = true
        }

        root.selectedNames = selection
    }

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

    // groups items into ranks (rows by y, columns by x) using Design View as a hint for order and
    // which items share a row/column -- but then places ranks on a fixed, compact grid instead of
    // preserving Design View's often very spread out distances, so cards stay close together
    // (gaps only grow where the grid needs the extra room to avoid overlapping cards)
    function rankByCoordinate(items, getCoordinate, tolerance) {
        var order = []
        for (var i = 0; i < items.length; i++)
            order.push({ index: i, value: getCoordinate(items[i]) })
        order.sort(function (a, b) { return a.value - b.value })

        var rankOfItem = []
        var rankCount = 0
        var lastValue = 0
        for (var j = 0; j < order.length; j++) {
            var entry = order[j]
            if (rankCount === 0 || entry.value - lastValue >= tolerance) {
                lastValue = entry.value
                rankCount++
            }
            rankOfItem[entry.index] = rankCount - 1
        }
        return { rankOfItem: rankOfItem, rankCount: rankCount }
    }

    function layoutWorkflow(items, connections) {
        if (items.length === 0)
            return { width: root.designContentWidth, height: root.designContentHeight }

        var padding = 60
        var rowStep = 134   // vertical distance between adjacent rows (card height + a 60 gap, like colStep)
        var colStep = 210   // horizontal distance between adjacent columns (card width + a gap)

        var itemIndex = ({})
        for (var m = 0; m < items.length; m++)
            itemIndex[items[m].name] = m

        var rows = rankByCoordinate(items, function (item) { return item.y }, rowStep / 3)
        var rowForItem = rows.rankOfItem
        var rowCount = rows.rankCount

        var itemY = []
        for (var n = 0; n < items.length; n++)
            itemY[n] = rowForItem[n] * rowStep

        // columns are ranked independently within each row, so an unrelated item in a different row
        // never eats up a "phantom" column slot between two items that are actually adjacent
        var alignedX = []
        for (var rowIdx = 0; rowIdx < rowCount; rowIdx++) {
            var rowItems = []
            for (var ri = 0; ri < items.length; ri++) {
                if (rowForItem[ri] === rowIdx)
                    rowItems.push(items[ri])
            }
            var rowCols = rankByCoordinate(rowItems, function (item) { return item.x }, colStep / 4)
            var ri2 = 0
            for (var ri3 = 0; ri3 < items.length; ri3++) {
                if (rowForItem[ri3] === rowIdx) {
                    alignedX[ri3] = rowCols.rankOfItem[ri2] * colStep
                    ri2++
                }
            }
        }

        // feeders of one card (links entering its left/right side) are spread symmetrically around it,
        // one row step apart each, so their midpoint lines up with the card regardless of how far
        // apart (or close together) they originally were in Design View
        var feedersOf = ({})
        for (var f = 0; f < connections.length; f++) {
            var feed = connections[f]
            var feedTarget = itemIndex[feed.to]
            var feedSource = itemIndex[feed.from]
            var feedSide = feed.to_anchor || "left"
            if (feedTarget === undefined || feedSource === undefined || feedSource === feedTarget
                    || (feedSide !== "left" && feedSide !== "right"))
                continue
            if (!feedersOf[feedTarget])
                feedersOf[feedTarget] = []
            if (feedersOf[feedTarget].indexOf(feedSource) < 0)
                feedersOf[feedTarget].push(feedSource)
        }
        for (var targetKey in feedersOf) {
            var feeders = feedersOf[targetKey]
            if (feeders.length < 2)
                continue
            var targetY = itemY[targetKey]
            feeders.sort(function (a, b) { return itemY[a] - itemY[b] })
            for (var fs = 0; fs < feeders.length; fs++)
                itemY[feeders[fs]] = targetY + (fs - (feeders.length - 1) / 2) * rowStep
        }

        var minY = itemY[0], maxY = itemY[0]
        for (var yi = 1; yi < items.length; yi++) {
            minY = Math.min(minY, itemY[yi])
            maxY = Math.max(maxY, itemY[yi])
        }
        // the whole workflow starts lower so feeders spread above their target still fit in the view
        for (var py = 0; py < items.length; py++)
            items[py].py = padding + (itemY[py] - minY)

        // children hanging below a parent's bottom edge in Design View
        var belowChildren = []
        for (var c = 0; c < connections.length; c++) {
            var link = connections[c]
            var enteringBottom = link.from_anchor !== "bottom" && link.to_anchor === "bottom"
            var parentIndex = itemIndex[enteringBottom ? link.to : link.from]
            var childIndex = itemIndex[enteringBottom ? link.from : link.to]
            if ((link.from_anchor !== "bottom" && !enteringBottom) || parentIndex === undefined
                    || childIndex === undefined || rowForItem[childIndex] <= rowForItem[parentIndex])
                continue
            if (!belowChildren[parentIndex])
                belowChildren[parentIndex] = []
            belowChildren[parentIndex].push(childIndex)
        }

        // a single child goes straight below its parent; a parent with several children is centered
        // over them (or, if the parent's own x is already fixed, the children shift to be centered under it)
        var fixedX = []
        for (var downRow = 0; downRow < rowCount; downRow++) {
            for (var p = 0; p < items.length; p++) {
                var kids = belowChildren[p]
                if (rowForItem[p] !== downRow || !kids)
                    continue
                if (kids.length === 1) {
                    alignedX[kids[0]] = alignedX[p]
                    fixedX[kids[0]] = true
                    continue
                }
                var kidsCenter = 0
                for (var k = 0; k < kids.length; k++)
                    kidsCenter += alignedX[kids[k]]
                kidsCenter /= kids.length
                if (fixedX[p]) {
                    for (var s = 0; s < kids.length; s++)
                        alignedX[kids[s]] += alignedX[p] - kidsCenter
                } else {
                    alignedX[p] = kidsCenter
                }
            }
        }

        // cards sharing a row must not overlap
        var minSpacing = colStep
        for (var spreadRow = 0; spreadRow < rowCount; spreadRow++) {
            var inRow = []
            for (var q = 0; q < items.length; q++) {
                if (rowForItem[q] === spreadRow)
                    inRow.push(q)
            }
            inRow.sort(function(a, b) { return alignedX[a] - alignedX[b] })
            for (var t = 1; t < inRow.length; t++)
                alignedX[inRow[t]] = Math.max(alignedX[inRow[t]], alignedX[inRow[t - 1]] + minSpacing)
        }

        // a link leaving a card's bottom edge enters a card directly below it through the top edge, giving a
        // straight vertical line instead of a loop round to the target's side
        for (var vc = 0; vc < connections.length; vc++) {
            var down = connections[vc]
            var upper = itemIndex[down.from]
            var lower = itemIndex[down.to]
            if (down.from_anchor === "bottom" && upper !== undefined && lower !== undefined
                    && itemY[lower] > itemY[upper] && Math.abs(alignedX[lower] - alignedX[upper]) < colStep / 4)
                down.to_anchor = "top"

            // mirror case: a card below feeds the bottom edge of the card above, leaving through its top
            var above = itemIndex[down.to]
            var below = itemIndex[down.from]
            if (down.from_anchor !== "bottom" && down.to_anchor === "bottom" && above !== undefined
                    && below !== undefined && itemY[below] > itemY[above]
                    && Math.abs(alignedX[below] - alignedX[above]) < colStep / 4)
                down.from_anchor = "top"
        }

        var leftX = alignedX[0], rightX = alignedX[0]
        for (var u = 1; u < items.length; u++) {
            leftX = Math.min(leftX, alignedX[u])
            rightX = Math.max(rightX, alignedX[u])
        }
        for (var w = 0; w < items.length; w++)
            items[w].px = padding + (alignedX[w] - leftX)

        return {
            width: padding * 2 + (rightX - leftX) + 150,
            height: padding * 2 + (maxY - minY) + 74
        }
    }


    // routed paths and badge anchors per connection ("from|to"), recomputed in one go by rebuildRoutes()
    // instead of on every paint/binding evaluation since routing is the expensive part
    property var routes: ({})

    function rebuildRoutes() {
        var cards = ({})
        var names = Object.keys(root.nodeItems)
        for (var i = 0; i < names.length; i++) {
            var card = root.nodeItems[names[i]]
            cards[names[i]] = { x: card.x, y: card.y, width: card.width, height: card.height }
        }
        root.routes = Router.routeAll(cards, root.workflow.connections || [], root.cardScale)
        connectionsCanvas.requestPaint()
    }

    // coalesces the many x/y change signals of a layout or drag into a single rebuild
    function scheduleRoutes() {
        routeTimer.restart()
    }

    Timer {
        id: routeTimer
        interval: 0
        onTriggered: root.rebuildRoutes()
    }

    function connectionAnchor(fromName, toName) {
        var route = root.routes[fromName + "|" + toName]
        return route ? Qt.point(route.anchor.x, route.anchor.y) : Qt.point(0, 0)
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

        // don't clear nodeItems here: the Repeater reuses existing WorkflowCard delegates when the
        // new items array has the same length, so Component.onCompleted (the only place that
        // populates nodeItems) wouldn't refire and repopulate them, permanently losing valid
        // references and making every connection line and filter badge vanish
        root.workflow = parsed

        root.scheduleRoutes()
        root.refreshAllScenarioInfo()
    }

    // re-pulls each card's scenarioInfo; needed after any toggle since merge-group siblings can
    // flip between "disabled_ok" and "error" depending on each other's state, not just their own
    function refreshAllScenarioInfo() {
        if (typeof projectBridge === "undefined")
            return

        var statuses = JSON.parse(projectBridge.get_scenario_status())
        var names = Object.keys(root.nodeItems)
        for (var i = 0; i < names.length; i++)
            root.nodeItems[names[i]].applyScenarioStatuses(statuses)
    }

    Component.onCompleted: {
        if (typeof projectBridge !== "undefined")
            currentProjectName = projectBridge.get_project_name()

        loadWorkflow()
        offerProjectSetup()
    }

    // shrink workflow cards so they keep fitting without horizontal scrolling on narrow windows,
    // multiplied by a user-controlled zoom factor from the −/+/Fit buttons (or Ctrl+wheel)
    property real zoomLevel: 1.0

    onCardScaleChanged: root.scheduleRoutes()
    // floored so the two factors combined never shrink cards past where text/line rendering breaks down
    property real cardScale: Math.max(0.55, root.zoomLevel * Math.max(0.5, Math.min(1, designFlick.width / root.designContentWidth)))

    function zoomIn() {
        root.zoomLevel = Math.min(2.5, root.zoomLevel * 1.2)
    }

    function zoomOut() {
        root.zoomLevel = Math.max(0.55, root.zoomLevel / 1.2)
    }

    function zoomReset() {
        root.zoomLevel = 1.0
    }

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
                            text: "User Mode"
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
                    selected: root.currentView === "workflow"
                    compact: root.compactSidebar

                    onClicked: root.currentView = "workflow"
                }

                SidebarButton {
                    text: "Data"
                    iconText: "◇"
                    selected: root.currentView === "database"
                    compact: root.compactSidebar

                    onClicked: {
                        root.currentView = "database"

                        if (!root.databasesLoaded)
                            root.loadDatabases()
                    }
                }

                SidebarButton {
                    text: "Results"
                    iconText: "▤"
                    selected: root.currentView === "results"
                    compact: root.compactSidebar

                    onClicked: {
                        root.currentView = "results"
                        root.plotUrls = projectBridge.get_plots()
                    }
                }

                SidebarButton {
                    text: "Runs"
                    iconText: "▶"
                    selected: root.currentView === "runs"
                    compact: root.compactSidebar

                    onClicked: root.currentView = "runs"
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
                                text: "User Mode"
                                color: "white"
                                font.bold: true

                                Layout.fillWidth: true
                            }

                            Switch {
                                checked: true

                                // this UI *is* user mode, so unchecking it means "switch to developer mode"
                                onToggled: {
                                    if (!checked && typeof projectBridge !== "undefined")
                                        projectBridge.open_dev_mode()
                                }
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

                    Rectangle {
                        visible: root.hasUnselectedScenarios

                        Layout.preferredWidth: scenarioWarningRow.width + 20
                        Layout.preferredHeight: 30

                        radius: 15
                        color: "#fee2e2"
                        border.color: "#dc2626"
                        border.width: 1

                        RowLayout {
                            id: scenarioWarningRow
                            anchors.centerIn: parent
                            spacing: 6

                            Label {
                                text: "\u26A0"
                                color: "#dc2626"
                                font.bold: true
                            }

                            Label {
                                text: "Scenarios not selected"
                                color: "#991b1b"
                                font.pixelSize: 12
                                font.bold: true
                            }
                        }

                        ToolTip.visible: scenarioWarningHover.hovered
                        ToolTip.text: "Some items have scenarios unchecked; those scenarios will be skipped when you run the project."

                        HoverHandler {
                            id: scenarioWarningHover
                        }
                    }

                    Rectangle {
                        visible: root.hasStarvedScenarios

                        Layout.preferredWidth: starvedWarningRow.width + 20
                        Layout.preferredHeight: 30

                        radius: 15
                        color: "#dc2626"

                        RowLayout {
                            id: starvedWarningRow
                            anchors.centerIn: parent
                            spacing: 6

                            Label {
                                text: "\u26A0"
                                color: "white"
                                font.bold: true
                            }

                            Label {
                                text: "No scenarios selected to run"
                                color: "white"
                                font.pixelSize: 12
                                font.bold: true
                            }
                        }

                        ToolTip.visible: starvedWarningHover.hovered
                        ToolTip.text: {
                            if (typeof projectBridge === "undefined")
                                return ""

                            var statuses = JSON.parse(projectBridge.get_scenario_status())
                            var names = []
                            for (var i = 0; i < statuses.length; i++) {
                                if (statuses[i].state === "error")
                                    names.push(statuses[i].name)
                            }
                            return names.length > 0
                                    ? names.join(", ") + ": nothing will run for " + (names.length === 1 ? "this item" : "these items") + " \u2013 no other source supplies them either."
                                    : ""
                        }

                        HoverHandler {
                            id: starvedWarningHover
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
                                root.offerProjectSetup()
                            }
                        }
                    }

                    Button {
                        id: runProjectButton

                        property int selectedCount: Object.keys(root.selectedNames).length

                        text: root.executionRunning ? "Stop"
                            : selectedCount > 0 ? "Run selected (" + selectedCount + ")" : "Run project"

                        background: Rectangle {
                            radius: 8
                            color: root.executionRunning
                                ? (runProjectButton.hovered ? "#b91c1c" : "#dc2626")
                                : (runProjectButton.hovered ? "#15803d" : "#16a34a")
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

                        onClicked: {
                            if (typeof projectBridge === "undefined")
                                return

                            if (root.executionRunning)
                                projectBridge.stop_workflow()
                            else {
                                var selectedNames = Object.keys(root.selectedNames)
                                if (selectedNames.length === 0 && projectBridge.has_unselected_scenarios())
                                    unselectedScenariosDialog.open()
                                else
                                    projectBridge.run_workflow(selectedNames)
                            }
                        }
                    }

                    Dialog {
                        id: unselectedScenariosDialog

                        anchors.centerIn: parent
                        modal: true
                        width: 380
                        title: "Scenarios not selected"
                        standardButtons: Dialog.Ok | Dialog.Cancel

                        contentItem: Label {
                            text: "Some scenarios are unchecked. Run the whole workflow anyway?"
                            wrapMode: Text.WordWrap
                            padding: 12
                        }

                        onAccepted: projectBridge.run_workflow([])
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
            // SETUP STATUS BANNER (shown while/after a project's setup script runs)
            // -------------------------------------------------

            Rectangle {
                Layout.fillWidth: true
                height: 32

                visible: root.setupStatusMessage !== ""

                color: root.setupStatusKind === "error" ? "#fee2e2"
                     : root.setupStatusKind === "success" ? "#dcfce7" : "#e0e7ff"

                Label {
                    anchors.fill: parent
                    anchors.leftMargin: 28
                    anchors.rightMargin: 24
                    verticalAlignment: Text.AlignVCenter
                    elide: Text.ElideRight
                    text: root.setupStatusMessage
                    color: root.setupStatusKind === "error" ? "#991b1b"
                         : root.setupStatusKind === "success" ? "#166534" : "#3730a3"
                }
            }

            // -------------------------------------------------
            // RUN STATUS BANNER (shown while/after a workflow run)
            // -------------------------------------------------

            Rectangle {
                Layout.fillWidth: true
                height: 32

                visible: root.runStatusMessage !== ""

                color: root.runStatusKind === "error" ? "#fee2e2"
                     : root.runStatusKind === "success" ? "#dcfce7" : "#e0e7ff"

                Label {
                    anchors.fill: parent
                    anchors.leftMargin: 28
                    anchors.rightMargin: 24
                    verticalAlignment: Text.AlignVCenter
                    elide: Text.ElideRight
                    text: root.runStatusMessage
                    color: root.runStatusKind === "error" ? "#991b1b"
                         : root.runStatusKind === "success" ? "#166534" : "#3730a3"
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
                    id: designCanvas

                    Layout.fillWidth: true
                    Layout.fillHeight: true

                    visible: root.currentView === "workflow"
                    color: "#f2f8f4"

                    focus: true

                    // arrow keys nudge every selected card together, same grouping as dragging one of them
                    Keys.onPressed: function (event) {
                        var dx = event.key === Qt.Key_Left ? -1 : event.key === Qt.Key_Right ? 1 : 0
                        var dy = event.key === Qt.Key_Up ? -1 : event.key === Qt.Key_Down ? 1 : 0
                        if (dx === 0 && dy === 0)
                            return

                        var names = Object.keys(root.selectedNames)
                        if (names.length === 0)
                            return

                        var step = (event.modifiers & Qt.ShiftModifier) ? 10 : 1
                        for (var i = 0; i < names.length; i++) {
                            var nodeItem = root.nodeItems[names[i]]
                            if (nodeItem) {
                                nodeItem.x += dx * step
                                nodeItem.y += dy * step
                            }
                        }
                        event.accepted = true
                    }

                    // subtle grid, scrollable so fixed-position cards stay reachable on narrow windows
                    Flickable {
                        id: designFlick

                        anchors.fill: parent

                        contentWidth: Math.max(width, root.designContentWidth * root.cardScale)
                        contentHeight: Math.max(height, root.designContentHeight * root.cardScale)

                        // margins let the workflow be dragged freely, even when it fits in the window
                        leftMargin: width
                        rightMargin: width
                        topMargin: height
                        bottomMargin: height

                        Component.onCompleted: {
                            contentX = 0
                            contentY = 0
                        }

                        clip: true
                        // the Flickable's own mouse dragging would steal box selection; panning is done manually
                        interactive: false
                        boundsBehavior: Flickable.StopAtBounds

                        // the mouse wheel zooms; scroll bars and dragging pan
                        WheelHandler {
                            onWheel: function (event) {
                                if (event.angleDelta.y > 0)
                                    root.zoomIn()
                                else if (event.angleDelta.y < 0)
                                    root.zoomOut()
                            }
                        }

                        ScrollBar.vertical: ScrollBar {
                            policy: designFlick.contentHeight > designFlick.height ? ScrollBar.AlwaysOn : ScrollBar.AlwaysOff
                        }

                        ScrollBar.horizontal: ScrollBar {
                            policy: designFlick.contentWidth > designFlick.width ? ScrollBar.AlwaysOn : ScrollBar.AlwaysOff
                        }

                        Canvas {
                            id: connectionsCanvas

                            anchors.fill: parent
                            // above idle cards (z: 1) so arrows are never hidden behind them,
                            // but below a card actively being dragged (z: 10)
                            z: 5

                            function drawConnection(ctx, connection, state) {
                                var cached = root.routes[connection.from + "|" + connection.to]
                                var path = cached ? cached.path : []
                                if (path.length < 2)
                                    return

                                // bold + saturated for a line that will actually carry data when run, thin and
                                // pale when it's idle (another line covers the target), reddish when broken
                                var lineColor = state === "idle" ? "#c7d2d6" : state === "error" ? "#dc2626" : "#2f6b4a"
                                ctx.strokeStyle = lineColor
                                ctx.lineWidth = (state === "idle" ? 1.5 : 3) * root.cardScale

                                function segmentLength(a, b) {
                                    return Math.abs(a.x - b.x) + Math.abs(a.y - b.y)
                                }

                                ctx.beginPath()
                                ctx.moveTo(path[0].x, path[0].y)

                                for (var i = 1; i < path.length - 1; i++) {
                                    var radius = Math.min(12 * root.cardScale,
                                                          segmentLength(path[i - 1], path[i]) / 2,
                                                          segmentLength(path[i], path[i + 1]) / 2)
                                    ctx.arcTo(path[i].x, path[i].y, path[i + 1].x, path[i + 1].y, radius)
                                }

                                var tip = path[path.length - 1]
                                var tail = path[path.length - 2]
                                ctx.lineTo(tip.x, tip.y)

                                ctx.stroke()

                                // arrow head points along the final segment
                                var arrowSize = 7 * root.cardScale
                                var directionX = Math.sign(tip.x - tail.x)
                                var directionY = Math.sign(tip.y - tail.y)

                                ctx.beginPath()

                                ctx.moveTo(tip.x, tip.y)
                                ctx.lineTo(tip.x - directionX * arrowSize - directionY * arrowSize / 2,
                                           tip.y - directionY * arrowSize + directionX * arrowSize / 2)
                                ctx.lineTo(tip.x - directionX * arrowSize + directionY * arrowSize / 2,
                                           tip.y - directionY * arrowSize - directionX * arrowSize / 2)
                                ctx.closePath()

                                ctx.fillStyle = lineColor
                                ctx.fill()
                            }

                            onPaint: {
                                var ctx = getContext("2d")

                                ctx.clearRect(0, 0, width, height)

                                var connections = root.workflow.connections || []

                                for (var i = 0; i < connections.length; i++) {
                                    var connection = connections[i]
                                    if (root.nodeItems[connection.from] && root.nodeItems[connection.to]) {
                                        var state = connection.filter_type === null || connection.filter_state === "ok"
                                                ? "active"
                                                : connection.filter_state === "error" ? "error" : "idle"
                                        drawConnection(ctx, connection, state)
                                    }
                                }
                            }
                        }

                        // draws a selection box when dragging on empty canvas, and clears/starts selection
                        MouseArea {
                            id: selectionArea

                            x: -designFlick.leftMargin
                            y: -designFlick.topMargin
                            width: designFlick.contentWidth + designFlick.leftMargin + designFlick.rightMargin
                            height: designFlick.contentHeight + designFlick.topMargin + designFlick.bottomMargin

                            property point pressPoint
                            property point panStart
                            property point panOrigin
                            property bool panning: false

                            onPressed: function (mouse) {
                                designCanvas.forceActiveFocus()
                                pressPoint = Qt.point(mouse.x + selectionArea.x, mouse.y + selectionArea.y)
                                panning = (mouse.modifiers & Qt.ControlModifier) !== 0

                                if (panning) {
                                    panStart = selectionArea.mapToItem(designFlick, mouse.x, mouse.y)
                                    panOrigin = Qt.point(designFlick.contentX, designFlick.contentY)
                                } else {
                                    root.rubberActive = true
                                    root.rubberRect = Qt.rect(pressPoint.x, pressPoint.y, 0, 0)
                                }

                                if (!(mouse.modifiers & Qt.ControlModifier))
                                    root.clearSelection()
                            }

                            onPositionChanged: function (mouse) {
                                if (!pressed)
                                    return

                                if (panning) {
                                    var view = selectionArea.mapToItem(designFlick, mouse.x, mouse.y)
                                    designFlick.contentX = Math.max(-designFlick.leftMargin,
                                                                    Math.min(designFlick.contentWidth + designFlick.rightMargin - designFlick.width,
                                                                             panOrigin.x - (view.x - panStart.x)))
                                    designFlick.contentY = Math.max(-designFlick.topMargin,
                                                                    Math.min(designFlick.contentHeight + designFlick.bottomMargin - designFlick.height,
                                                                             panOrigin.y - (view.y - panStart.y)))
                                    return
                                }

                                var mouseX = mouse.x + selectionArea.x
                                var mouseY = mouse.y + selectionArea.y
                                var x = Math.min(pressPoint.x, mouseX)
                                var y = Math.min(pressPoint.y, mouseY)
                                var w = Math.abs(mouseX - pressPoint.x)
                                var h = Math.abs(mouseY - pressPoint.y)

                                root.rubberRect = Qt.rect(x, y, w, h)
                                root.selectWithinRect(root.rubberRect, (mouse.modifiers & Qt.ControlModifier) !== 0)
                            }

                            onReleased: {
                                root.rubberActive = false
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
                                nodeName: modelData.name
                                selected: root.selectedNames[modelData.name] === true

                                Component.onCompleted: {
                                    root.nodeItems[modelData.name] = this
                                    root.nodeItemsTick += 1
                                    refreshScenarioInfo()
                                    root.scheduleRoutes()
                                }
                            }
                        }

                        // =================================================
                        // FILTER BADGES (one per connection that has scenario/alternative filters,
                        // positioned at the connector's midpoint; red when a required filter has
                        // nothing checked, so missing selections are visible without opening anything)
                        // =================================================

                        Repeater {
                            model: root.workflow.connections

                            Rectangle {
                                // root.nodeItemsTick forces this binding to re-evaluate once cards finish
                                // registering themselves in root.nodeItems (see comment on nodeItemsTick)
                                visible: !!(root.nodeItemsTick >= 0 && modelData.filter_type
                                        && root.nodeItems[modelData.from] && root.nodeItems[modelData.to])

                                property point anchorPoint: visible
                                        ? root.connectionAnchor(modelData.from, modelData.to) : Qt.point(0, 0)

                                x: anchorPoint.x - width / 2
                                y: anchorPoint.y - height / 2
                                z: 6

                                width: 28 * root.cardScale
                                height: width
                                radius: width / 2

                                color: modelData.filter_state === "error" ? "#fee2e2" : "#ffffff"
                                border.color: modelData.filter_state === "error"
                                              ? "#dc2626"
                                              : modelData.filter_state === "disabled_ok"
                                                ? "#dbe3de"
                                                : "#2f6b4a"
                                border.width: (modelData.filter_state === "disabled_ok" ? 1 : 2) * root.cardScale
                                opacity: modelData.filter_state === "disabled_ok" ? 0.6 : 1.0

                                Label {
                                    anchors.centerIn: parent
                                    // "!" flags a required-but-unsatisfied filter without relying on the red color alone
                                    text: modelData.filter_state === "error"
                                          ? "!"
                                          : (modelData.filter_type === "scenario" ? "S" : "A")
                                    font.pixelSize: 13 * root.cardScale
                                    font.bold: modelData.filter_state !== "disabled_ok"
                                    color: modelData.filter_state === "error"
                                           ? "#dc2626"
                                           : modelData.filter_state === "disabled_ok"
                                             ? "#94a3b8"
                                             : "#2f6b4a"
                                }

                                MouseArea {
                                    anchors.fill: parent
                                    cursorShape: Qt.PointingHandCursor
                                    onClicked: linkFiltersDialog.openFor(modelData.from, modelData.to)
                                }

                                ToolTip.visible: hoverHandler.hovered
                                ToolTip.text: (modelData.filter_type === "scenario" ? "Scenario filter" : "Alternative filter")
                                        + (modelData.filter_state === "error"
                                           ? " – needs at least one selection"
                                           : modelData.filter_state === "disabled_ok"
                                             ? " – nothing selected here, but another line into the same target is"
                                             : "")

                                HoverHandler {
                                    id: hoverHandler
                                }
                            }
                        }

                        // visual feedback for the in-progress rubber-band selection
                        Rectangle {
                            visible: root.rubberActive

                            x: root.rubberRect.x
                            y: root.rubberRect.y
                            width: root.rubberRect.width
                            height: root.rubberRect.height

                            z: 20

                            color: "#3b82f61a"
                            border.color: "#3b82f6"
                            border.width: 1
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

                        Item {
                            Layout.fillWidth: true
                        }

                        ToolButton {
                            text: "−"

                            onClicked: root.zoomOut()
                        }

                        ToolButton {
                            text: "+"

                            onClicked: root.zoomIn()
                        }

                        ToolButton {
                            text: "Fit"

                            onClicked: root.zoomReset()
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

                    // -------------------------------------------------
                    // Scenario selection dialog (double-click on Tool/Stack items listed in
                    // project.json's "scenario_selectable_items")
                    // -------------------------------------------------

                    Dialog {
                        id: scenarioDialog

                        anchors.centerIn: parent
                        modal: true
                        width: 320

                        property string itemName: ""
                        property var scenarios: []

                        title: "Scenarios – " + scenarioDialog.itemName
                        standardButtons: Dialog.Close

                        function openFor(name) {
                            scenarioDialog.itemName = name
                            scenarioDialog.scenarios = []

                            if (typeof projectBridge === "undefined")
                                return

                            var raw = projectBridge.get_item_scenarios(name)
                            var parsed = raw ? JSON.parse(raw) : []

                            if (parsed.length === 0)
                                return

                            scenarioDialog.scenarios = parsed
                            scenarioDialog.open()
                        }

                        contentItem: ColumnLayout {
                            spacing: 4

                            Label {
                                text: "Select which scenarios " + scenarioDialog.itemName + " runs:"
                                wrapMode: Text.WordWrap
                                Layout.fillWidth: true
                                Layout.bottomMargin: 6
                                opacity: 0.7
                            }

                            Repeater {
                                model: scenarioDialog.scenarios

                                CheckBox {
                                    text: modelData.name
                                    checked: modelData.enabled

                                    onToggled: {
                                        if (typeof projectBridge !== "undefined") {
                                            projectBridge.set_item_scenario_enabled(
                                                scenarioDialog.itemName, modelData.name, checked)
                                            root.refreshScenarioWarning()
                                            root.refreshAllScenarioInfo()
                                        }
                                    }
                                }
                            }
                        }
                    }

                    // -------------------------------------------------
                    // Link filter dialog (click on a connection's filter badge): checklist of the
                    // scenarios/alternatives online for that link, with a notice when a required
                    // filter has nothing checked
                    // -------------------------------------------------

                    Dialog {
                        id: linkFiltersDialog

                        anchors.centerIn: parent
                        modal: true
                        width: 340

                        property string fromName: ""
                        property string toName: ""
                        property string filterType: ""
                        property bool required: false
                        property var items: []

                        readonly property bool nothingSelected: !items.some(function (item) { return item.enabled })

                        title: "Link filter – " + linkFiltersDialog.fromName + " → " + linkFiltersDialog.toName
                        standardButtons: Dialog.Close

                        function openFor(fromName, toName) {
                            linkFiltersDialog.fromName = fromName
                            linkFiltersDialog.toName = toName
                            linkFiltersDialog.filterType = ""
                            linkFiltersDialog.required = false
                            linkFiltersDialog.items = []

                            if (typeof projectBridge === "undefined")
                                return

                            var raw = projectBridge.get_connection_filters(fromName, toName)
                            var parsed = raw ? JSON.parse(raw) : {}

                            if (!parsed.filter_type)
                                return

                            linkFiltersDialog.filterType = parsed.filter_type
                            linkFiltersDialog.required = parsed.required
                            linkFiltersDialog.items = parsed.items
                            linkFiltersDialog.open()
                        }

                        function toggle(itemName, enabled) {
                            var updated = linkFiltersDialog.items.map(function (item) {
                                return item.name === itemName ? { "name": item.name, "enabled": enabled } : item
                            })
                            linkFiltersDialog.items = updated

                            if (typeof projectBridge !== "undefined")
                                projectBridge.set_connection_filter_enabled(
                                    linkFiltersDialog.fromName, linkFiltersDialog.toName,
                                    linkFiltersDialog.filterType, itemName, enabled)

                            root.loadWorkflow()
                        }

                        contentItem: ColumnLayout {
                            spacing: 4

                            Label {
                                text: (linkFiltersDialog.filterType === "scenario" ? "Scenario filter" : "Alternative filter")
                                        + ": select which " + linkFiltersDialog.filterType
                                        + "(s) may pass through this link."
                                wrapMode: Text.WordWrap
                                Layout.fillWidth: true
                                Layout.bottomMargin: 6
                                opacity: 0.7
                            }

                            Label {
                                visible: linkFiltersDialog.required && linkFiltersDialog.nothingSelected
                                text: "⚠ At least one " + linkFiltersDialog.filterType
                                        + " must be selected for this link to run."
                                wrapMode: Text.WordWrap
                                Layout.fillWidth: true
                                Layout.bottomMargin: 6
                                color: "#dc2626"
                                font.bold: true
                            }

                            // caps the checklist's height so dozens of scenarios scroll instead of
                            // stretching the dialog off the screen
                            ScrollView {
                                Layout.fillWidth: true
                                Layout.preferredHeight: Math.min(linkFiltersDialog.items.length * 32, 260)
                                clip: true

                                ColumnLayout {
                                    width: parent.width
                                    spacing: 0

                                    Repeater {
                                        model: linkFiltersDialog.items

                                        CheckBox {
                                            text: modelData.name
                                            checked: modelData.enabled

                                            onToggled: linkFiltersDialog.toggle(modelData.name, checked)
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            // =================================================
            // DATA PAGE (Entity/Alternative/Scenario browser, real spinedb_api reads)
            // =================================================

            Rectangle {
                Layout.fillWidth: true
                Layout.fillHeight: true

                visible: root.currentView === "database"
                color: "#f2f8f4"

                RowLayout {
                    anchors.fill: parent
                    anchors.margins: 20

                    spacing: 16

                    // -------------------------------------------------
                    // LEFT: database picker + entity/alternative/scenario lists
                    // -------------------------------------------------

                    Rectangle {
                        Layout.preferredWidth: 260
                        Layout.fillHeight: true

                        radius: 10
                        color: "#ffffff"
                        border.color: "#e2e8f0"

                        ColumnLayout {
                            anchors.fill: parent
                            anchors.margins: 14

                            spacing: 8

                            Label {
                                text: "Database"
                                font.bold: true
                                font.pixelSize: 12
                                opacity: 0.6
                            }

                            ComboBox {
                                Layout.fillWidth: true

                                model: root.databases
                                textRole: "name"

                                onActivated: root.selectDatabase(root.databases[currentIndex].url)
                            }

                            Label {
                                visible: root.databaseContents.error !== undefined
                                text: root.databaseContents.error || ""
                                color: "#dc2626"
                                font.pixelSize: 11
                                wrapMode: Text.WordWrap
                                Layout.fillWidth: true
                            }

                            // everything below scrolls as one column, so the panel never overflows
                            // its bounds regardless of window height or how many rows each list has
                            ScrollView {
                                Layout.fillWidth: true
                                Layout.fillHeight: true
                                clip: true

                                ColumnLayout {
                                    width: parent.width
                                    spacing: 8

                                    Label {
                                        text: "Entity classes"
                                        font.bold: true
                                        font.pixelSize: 12
                                        opacity: 0.6
                                    }

                                    Repeater {
                                        model: root.databaseContents.entity_classes || []

                                        Button {
                                            Layout.fillWidth: true
                                            flat: true
                                            highlighted: modelData.name === root.selectedEntityClass
                                            text: modelData.name + " (" + modelData.entity_count + ")"

                                            onClicked: root.selectEntityClass(modelData.name)
                                        }
                                    }

                                    Label {
                                        text: "Alternatives"
                                        font.bold: true
                                        font.pixelSize: 12
                                        opacity: 0.6
                                        Layout.topMargin: 6
                                    }

                                    Repeater {
                                        model: root.databaseContents.alternatives || []

                                        Label {
                                            text: modelData
                                            font.pixelSize: 12
                                            leftPadding: 4
                                        }
                                    }

                                    Label {
                                        text: "Scenarios"
                                        font.bold: true
                                        font.pixelSize: 12
                                        opacity: 0.6
                                        Layout.topMargin: 6
                                    }

                                    Repeater {
                                        model: root.databaseContents.scenarios || []

                                        Label {
                                            text: modelData
                                            font.pixelSize: 12
                                            leftPadding: 4
                                        }
                                    }
                                }
                            }
                        }
                    }

                    // -------------------------------------------------
                    // CENTER: parameter value table for the selected entity class
                    // -------------------------------------------------

                    Rectangle {
                        Layout.fillWidth: true
                        Layout.fillHeight: true

                        radius: 10
                        color: "#ffffff"
                        border.color: "#e2e8f0"

                        ColumnLayout {
                            anchors.fill: parent
                            anchors.margins: 14

                            spacing: 8

                            Label {
                                text: root.selectedEntityClass
                                      ? "Parameter values – " + root.selectedEntityClass
                                      : "Select an entity class"
                                font.bold: true
                                font.pixelSize: 14
                            }

                            RowLayout {
                                Layout.fillWidth: true
                                visible: root.entityClassValues.length > 0
                                spacing: 0

                                Label { Layout.preferredWidth: 160; text: "Entity"; font.bold: true; opacity: 0.6; font.pixelSize: 11 }
                                Label { Layout.preferredWidth: 160; text: "Parameter"; font.bold: true; opacity: 0.6; font.pixelSize: 11 }
                                Label { Layout.preferredWidth: 120; text: "Alternative"; font.bold: true; opacity: 0.6; font.pixelSize: 11 }
                                Label { Layout.fillWidth: true; text: "Value"; font.bold: true; opacity: 0.6; font.pixelSize: 11 }
                            }

                            Rectangle {
                                Layout.fillWidth: true
                                height: 1
                                color: "#e2e8f0"
                                visible: root.entityClassValues.length > 0
                            }

                            ScrollView {
                                Layout.fillWidth: true
                                Layout.fillHeight: true
                                clip: true

                                ColumnLayout {
                                    width: parent.width
                                    spacing: 0

                                    Repeater {
                                        model: root.entityClassValues

                                        RowLayout {
                                            Layout.fillWidth: true
                                            spacing: 0

                                            Label { Layout.preferredWidth: 160; text: modelData.entity; font.pixelSize: 12; elide: Text.ElideRight }
                                            Label { Layout.preferredWidth: 160; text: modelData.parameter; font.pixelSize: 12; elide: Text.ElideRight }
                                            Label { Layout.preferredWidth: 120; text: modelData.alternative; font.pixelSize: 12; elide: Text.ElideRight }
                                            Label { Layout.fillWidth: true; text: modelData.value; font.pixelSize: 12; elide: Text.ElideRight }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }

            // =================================================
            // RESULTS PAGE (plots produced by the latest run)
            // =================================================

            Rectangle {
                Layout.fillWidth: true
                Layout.fillHeight: true

                visible: root.currentView === "results"
                color: "#f2f8f4"

                Label {
                    anchors.centerIn: parent
                    visible: root.plotUrls.length === 0
                    text: "No plots yet. Run a workflow that creates plots."
                    color: "#475569"
                    font.pixelSize: 15
                }

                ScrollView {
                    anchors.fill: parent
                    anchors.margins: 20
                    clip: true
                    contentWidth: availableWidth

                    ColumnLayout {
                        width: parent.width
                        spacing: 16

                        Repeater {
                            model: root.plotUrls

                            Rectangle {
                                Layout.fillWidth: true
                                Layout.preferredHeight: plotImage.implicitWidth > 0
                                    ? (width - 20) * plotImage.implicitHeight / plotImage.implicitWidth + 20 : 0
                                radius: 10
                                color: "white"

                                Image {
                                    id: plotImage

                                    anchors.fill: parent
                                    anchors.margins: 10
                                    source: modelData
                                    fillMode: Image.PreserveAspectFit
                                    cache: false
                                }
                            }
                        }
                    }
                }
            }

            // =================================================
            // RUNS PAGE (streamed stdout/stderr from projectBridge.run_workflow())
            // =================================================

            Rectangle {
                Layout.fillWidth: true
                Layout.fillHeight: true

                visible: root.currentView === "runs"
                color: "#f2f8f4"

                Rectangle {
                    anchors.fill: parent
                    anchors.margins: 20

                    radius: 10
                    color: "#0f172a"

                    ListView {
                        id: runLogView

                        anchors.fill: parent
                        anchors.margins: 14
                        clip: true

                        model: root.executionLogModel

                        onCountChanged: positionViewAtEnd()

                        delegate: Label {
                            width: runLogView.width
                            text: model.text
                            wrapMode: Text.Wrap
                            font.family: "Consolas, monospace"
                            font.pixelSize: 12
                            color: model.kind === "stderr" ? "#f87171" : "#e2e8f0"
                        }
                    }
                }
            }
            // closes the Runs page Rectangle above; this next brace closes the WORKSPACE
            // RowLayout itself, so each page is a sibling of the design canvas
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
        property string nodeName: ""
        property bool selected: false

        property real designX: 0
        property real designY: 0
        property real sizeFactor: 1

        // {total, enabled, state}: this item's scenario selection, where state is "ok" (will run),
        // "disabled_ok" (none enabled, but a merge-group sibling covers it) or "error" (nothing
        // will reach whatever this feeds); refreshed via refreshScenarioInfo()
        property var scenarioInfo: ({ "total": 0, "enabled": 0, "state": "ok" })

        function refreshScenarioInfo() {
            if (typeof projectBridge === "undefined")
                return

            card.applyScenarioStatuses(JSON.parse(projectBridge.get_scenario_status()))
        }

        function applyScenarioStatuses(statuses) {
            for (var i = 0; i < statuses.length; i++) {
                if (statuses[i].name === card.nodeName) {
                    card.scenarioInfo = statuses[i]
                    return
                }
            }
            card.scenarioInfo = { "total": 0, "enabled": 0, "state": "ok" }
        }

        // initial layout from project.json; dragging then takes over and owns x/y directly
        x: designX * sizeFactor
        y: designY * sizeFactor

        width: 150 * sizeFactor
        height: 74 * sizeFactor

        radius: 10 * sizeFactor

        // true when every scenario/alternative-filtered link leaving this card has nothing chosen
        // (a stack's own selectable items surface only as filters on its outgoing links)
        property bool filtersUnchosen: {
            var connections = root.workflow.connections || []
            var filtered = 0
            for (var i = 0; i < connections.length; i++) {
                var connection = connections[i]
                if (connection.from !== nodeName || !connection.filter_type)
                    continue
                if (connection.filter_state === "ok")
                    return false
                filtered++
            }
            return filtered > 0
        }

        color: active ? "#ffffff" : "#e5e7eb"

        // a card that will actually run (scenarios selected) gets a bold green highlight so the active
        // path through a multi-branch workflow is traceable; one that's idle because a sibling covers
        // its target instead fades out; errors stay red regardless of selection
        opacity: scenarioInfo.state === "disabled_ok" ? 0.55 : 1.0

        // stacks and plain items share the same neutral default look; only active/error/selection state
        // (not item kind) should stand out, so the accent color here is type-coded only for hover/icons
        property bool active: scenarioInfo.state === "ok" && !filtersUnchosen

        border.color: scenarioInfo.state === "error"
                      ? "#dc2626"
                      : selected
                        ? "#2563eb"
                        : active
                          ? "#2f6b4a"
                          : (hovered ? accent : "#e2e8f0")

        border.width: (scenarioInfo.state === "error" || selected || active)
                      ? 3
                      : (hovered ? 2 : 1)

        property bool hovered: false

        property string runState: root.itemRunStates[nodeName] || ""

        // run progress badge: a swinging hammer while executing, then a check mark or a cross
        Label {
            id: runBadge

            visible: card.runState !== ""
            z: 5
            anchors.right: parent.right
            anchors.top: parent.top
            anchors.rightMargin: -8 * card.sizeFactor
            anchors.topMargin: -12 * card.sizeFactor
            transformOrigin: Item.BottomRight

            text: card.runState === "running" ? "⚒" : (card.runState === "done" ? "✔" : (card.runState === "queued" ? "…" : "✖"))
            color: card.runState === "done" ? "#16a34a" : (card.runState === "failed" ? "#dc2626" : (card.runState === "queued" ? "#6b7280" : "#b45309"))
            font.pixelSize: 20 * card.sizeFactor
            font.bold: true

            SequentialAnimation on rotation {
                running: card.runState === "running"
                loops: Animation.Infinite

                NumberAnimation { from: -25; to: 25; duration: 300; easing.type: Easing.InOutQuad }
                NumberAnimation { from: 25; to: -25; duration: 300; easing.type: Easing.InOutQuad }
            }
        }

        onRunStateChanged: {
            if (runState !== "running")
                runBadge.rotation = 0
        }

        signal clicked()

        scale: hovered ? 1.015 : 1
        z: dragArea.drag.active ? 10 : 1

        Behavior on scale {
            NumberAnimation {
                duration: 120
            }
        }

        // redraw arrows as the card is dragged around
        onXChanged: root.scheduleRoutes()
        onYChanged: root.scheduleRoutes()

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

        // marks whether this item/stack is set to run (green), harmlessly idle because a sibling
        // branch covers the same target (neutral), or starved with nothing else to cover it (red)
        Rectangle {
            visible: card.scenarioInfo.total > 0

            anchors.top: parent.top
            anchors.right: parent.right
            anchors.topMargin: -7 * card.sizeFactor
            anchors.rightMargin: -7 * card.sizeFactor

            z: 5

            width: scenarioBadgeLabel.implicitWidth + 12 * card.sizeFactor
            height: 18 * card.sizeFactor
            radius: height / 2

            color: card.scenarioInfo.state === "error"
                   ? "#fee2e2"
                   : card.scenarioInfo.state === "ok"
                     ? "#dcfce7"
                     : "#f1f5f9"
            border.color: card.scenarioInfo.state === "error"
                          ? "#dc2626"
                          : card.scenarioInfo.state === "ok"
                            ? "#15803d"
                            : "#cbd5e1"
            border.width: card.scenarioInfo.state === "disabled_ok" ? 1 : 2

            Label {
                id: scenarioBadgeLabel
                anchors.centerIn: parent
                text: (card.scenarioInfo.state === "error" ? "! " : card.scenarioInfo.state === "ok" ? "\u2713 " : "")
                        + card.scenarioInfo.enabled + "/" + card.scenarioInfo.total
                font.pixelSize: 10 * card.sizeFactor
                font.bold: card.scenarioInfo.state !== "disabled_ok"
                color: card.scenarioInfo.state === "error"
                       ? "#dc2626"
                       : card.scenarioInfo.state === "ok"
                         ? "#15803d"
                         : "#94a3b8"
            }

            ToolTip.visible: scenarioBadgeHover.hovered
            ToolTip.text: card.scenarioInfo.state === "error"
                    ? "No scenarios selected and no other source supplies data here; nothing will run for " + card.title + "."
                    : card.scenarioInfo.state === "disabled_ok"
                      ? "No scenarios selected for " + card.title + ", but another connected source still supplies data."
                      : card.scenarioInfo.enabled + " of " + card.scenarioInfo.total + " scenarios selected to run for " + card.title

            HoverHandler {
                id: scenarioBadgeHover
            }
        }

        MouseArea {
            id: dragArea

            anchors.fill: parent

            hoverEnabled: true
            cursorShape: drag.active ? Qt.ClosedHandCursor : Qt.PointingHandCursor

            drag.target: card
            drag.axis: Drag.XAndYAxis

            property real lastX: 0
            property real lastY: 0

            onEntered: card.hovered = true
            onExited: card.hovered = false

            onPressed: function (mouse) {
                designCanvas.forceActiveFocus()
                lastX = card.x
                lastY = card.y

                if (mouse.modifiers & Qt.ControlModifier)
                    root.toggleSelection(card.nodeName)
                else if (!card.selected)
                    root.selectOnly(card.nodeName)
            }

            // snap x/y to other unselected cards when within a few pixels
            function snapToNeighbours() {
                var threshold = 10 * card.sizeFactor
                var bestX = threshold
                var bestY = threshold
                var snapX = card.x
                var snapY = card.y

                for (var name in root.nodeItems) {
                    var other = root.nodeItems[name]

                    if (!other || other === card || root.selectedNames[name])
                        continue

                    if (Math.abs(other.x - card.x) < bestX) {
                        bestX = Math.abs(other.x - card.x)
                        snapX = other.x
                    }

                    if (Math.abs(other.y - card.y) < bestY) {
                        bestY = Math.abs(other.y - card.y)
                        snapY = other.y
                    }
                }

                card.x = snapX
                card.y = snapY
            }

            // while this card is dragged, move every other selected card by the same amount
            onPositionChanged: {
                if (!drag.active)
                    return

                snapToNeighbours()

                if (!card.selected)
                    return

                var dx = card.x - lastX
                var dy = card.y - lastY

                if (dx === 0 && dy === 0)
                    return

                lastX = card.x
                lastY = card.y

                var names = Object.keys(root.selectedNames)

                for (var i = 0; i < names.length; i++) {
                    if (names[i] === card.nodeName)
                        continue

                    var other = root.nodeItems[names[i]]

                    if (other) {
                        other.x += dx
                        other.y += dy
                    }
                }
            }

            onClicked: card.clicked()

            onDoubleClicked: {
                if (typeof projectBridge === "undefined")
                    return

                if (card.subtitle === "Data Connection") {
                    projectBridge.open_item_directory(card.nodeName)
                    return
                }

                if (card.subtitle === "Data Store") {
                    projectBridge.open_database(card.nodeName)
                    return
                }

                scenarioDialog.openFor(card.nodeName)
            }
        }

        ToolTip {
            visible: card.hovered
            text: {
                // item-specific guidance for double-click actions
                if (card.title === "Excel input")
                    return "Double-click to choose the Excel input file"
                if (card.subtitle === "Data Connection")
                    return "Double-click to open the data connection directory"
                if (card.subtitle === "Data Store")
                    return "Double-click to open in the database editor"
                if (typeof projectBridge !== "undefined") {
                    var raw = projectBridge.get_item_scenarios(card.title)
                    var parsed = raw ? JSON.parse(raw) : []
                    if (parsed.length > 0)
                        return "Double-click to choose scenarios to run"
                }
                return "Double-click to open"
            }
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

                Label {
                    text: card.subtitle

                    visible: card.subtitle.length > 0

                    font.pixelSize: 11 * card.sizeFactor
                    opacity: 0.6

                    elide: Text.ElideRight
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
                visible: card.scenarioInfo.state === "disabled_ok"
                text: "Scenarios not chosen"

                font.pixelSize: 10 * card.sizeFactor
                font.italic: true
                color: "#94a3b8"

                elide: Text.ElideRight
            }

            Item {
                Layout.fillHeight: true
            }
        }
    }
}