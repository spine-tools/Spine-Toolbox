import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Dialogs
import QtQuick.Shapes
import "Layout.js" as CardLayout
import "Router.js" as Router
import "TourSteps.js" as TourSteps

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
    property bool setupRunning: false

    // transient banner shown while/after a workflow run; status is "info", "success" or "error"
    property string runStatusMessage: ""
    property string runStatusKind: "info"
    property bool executionRunning: false
    property ListModel executionLogModel: ListModel {}

    // true when a link's scenario/alternative filter has nothing chosen and no sibling link covers it
    property bool hasUnselectedScenarios: {
        var connections = root.workflow.connections || []
        return connections.some(function (connection) { return connection.filter_state === "error" })
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
            // progress lines stay up until the final success/error message, which then lingers
            if (status === "info")
                setupStatusTimer.stop()
            else
                setupStatusTimer.restart()
        }

        function onSetupRunningChanged(running) {
            root.setupRunning = running
        }

        function onRunStatusChanged(message, status) {
            root.runStatusMessage = message
            root.runStatusKind = status
            runStatusTimer.restart()
        }

        function onExecutionStateChanged(running) {
            root.executionRunning = running

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
        }

        function onDataViewRequested() {
            root.currentView = "database"
        }

        function onStoreWarningsChanged() {
            root.loadStoreWarnings()
        }

        function onRunResultsChanged() {
            root.loadRunResults()

            if (runResultsTab.visible)
                projectBridge.open_run_results(root.currentChain)
        }

        function onExecutionLogAppended(line, kind) {
            root.executionLogModel.append({ "text": line, "kind": kind })

            if (root.executionLogModel.count > 2000)
                root.executionLogModel.remove(0)
        }
    }

    Timer {
        id: setupStatusTimer
        interval: root.setupStatusKind === "error" ? 20000 : 8000
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
    // plots the user has saved, shown instead of the latest run's plots when showSavedPlots is set
    property bool showSavedPlots: false
    property var savedPlots: []
    property var savedPlotFilters: ({ "chains": [], "runs": [] })
    property string savedPlotChain: "*"
    property string savedPlotRun: "*"
    property string savedPlotQuery: ""
    // what the latest run of the current chain produced, see ProjectBridge.get_run_results
    property var runResults: ({})

    function loadSavedPlots() {
        if (typeof projectBridge === "undefined")
            return
        root.savedPlotFilters = JSON.parse(projectBridge.get_saved_plot_filters())
        root.savedPlots = JSON.parse(projectBridge.get_saved_plots(root.savedPlotChain, root.savedPlotRun,
                                                                    root.savedPlotQuery))
    }

    function loadRunResults() {
        if (typeof projectBridge !== "undefined")
            root.runResults = JSON.parse(projectBridge.get_run_results(root.currentChain))
    }

    function runResultsSummary() {
        var run = root.runResults
        if (!run.stores)
            return "This chain has not been run yet."
        var scenarios = []
        for (var store in run.stores)
            scenarios = scenarios.concat(run.stores[store])
        return run.chain_name + " - run " + run.started_label + (scenarios.length > 0
            ? " - scenarios: " + scenarios.join(", ")
            : " - no new scenarios found, showing the whole database")
    }

    onCurrentChainChanged: loadRunResults()
    property var dataStores: []
    property var resultDataStores: []
    property string currentDataStore: ""

    // card name -> "waiting", "running", "done", "failed", "skipped" or "excluded" for the latest run
    property var itemRunStates: ({})

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

    function layoutWorkflow(items, connections, compactRows) {
        return CardLayout.layoutWorkflow(
            items, connections, { width: root.designContentWidth, height: root.designContentHeight }, compactRows)
    }


    // routed paths and badge anchors per connection ("from|to") in unscaled design units, recomputed in one go
    // by rebuildRoutes() since routing is the expensive part; connectionsLayer scales them with cardScale
    property var routes: ({})

    // card moves for Ctrl+Z, each entry holds the design positions the moved cards had before
    property var moveUndoStack: []
    property var moveRedoStack: []
    property var moveSnapshot: ({})
    // name -> {x, y} design position of every card the user has moved, kept in the project's user mode file
    property var savedPositions: ({})

    // chains highlighted on the canvas, none means the whole workflow; chainList holds {key, name} of the defined chains
    property var selectedChains: []
    // the selected chain keys as one key for the bridge
    readonly property string currentChain: root.selectedChains.join("\u001f")
    // name -> true for the cards the selected chains cover, null while no chain is selected
    property var chainMembers: null
    // Data Store name -> name of the chain whose run last filled it, for stores shown in the current chain
    property var storeWarnings: ({})

    function loadStoreWarnings() {
        if (typeof projectBridge !== "undefined")
            root.storeWarnings = JSON.parse(projectBridge.get_store_warnings(root.currentChain))
    }

    function loadChainMembers() {
        if (!root.currentChain || typeof projectBridge === "undefined") {
            root.chainMembers = null
            return
        }
        var members = ({})
        JSON.parse(projectBridge.get_chain_members(root.currentChain)).forEach(function (name) { members[name] = true })
        root.chainMembers = members
    }

    function isDimmed(name) {
        return root.chainMembers !== null && root.chainMembers[name] !== true
    }

    property string defaultChain: ""
    property var chainList: []

    function loadChains(useDefault) {
        if (typeof projectBridge === "undefined")
            return
        var info = JSON.parse(projectBridge.get_chains())
        root.chainList = info.chains
        root.defaultChain = info.default || ""
        if (useDefault)
            root.selectedChains = root.defaultChain ? [root.defaultChain] : []
        else
            root.selectedChains = root.selectedChains.filter(function (key) {
                return info.chains.some(function (chain) { return chain.key === key })
            })
    }

    function savePositions() {
        if (typeof projectBridge !== "undefined")
            projectBridge.set_user_positions("", JSON.stringify(root.savedPositions))
    }

    // adds the chain to the highlighted ones or removes it; "" clears the selection
    function toggleChain(key) {
        if (!key)
            root.selectedChains = []
        else if (root.selectedChains.indexOf(key) >= 0)
            root.selectedChains = root.selectedChains.filter(function (selected) { return selected !== key })
        else
            root.selectedChains = root.selectedChains.concat([key])
        root.loadChainMembers()
        root.loadStoreWarnings()
    }

    // a card moved by hand keeps its place unless its design position changed, so put every card back
    function snapCardsToDesign() {
        for (var name in root.nodeItems) {
            var card = root.nodeItems[name]
            if (card) {
                card.x = card.designX * card.sizeFactor
                card.y = card.designY * card.sizeFactor
            }
        }
    }

    Timer {
        id: savePositionsTimer
        interval: 400
        onTriggered: root.savePositions()
    }

    function cardPositions() {
        var positions = ({})
        for (var name in root.nodeItems) {
            var card = root.nodeItems[name]
            if (card)
                positions[name] = { x: card.x / card.sizeFactor, y: card.y / card.sizeFactor }
        }
        return positions
    }

    function recordMove(before) {
        var after = root.cardPositions()
        var changed = ({})
        var any = false
        for (var name in before) {
            if (after[name] && (Math.abs(before[name].x - after[name].x) > 0.01
                                || Math.abs(before[name].y - after[name].y) > 0.01)) {
                changed[name] = { x: before[name].x, y: before[name].y, wasSaved: !!root.savedPositions[name] }
                root.savedPositions[name] = after[name]
                any = true
            }
        }
        if (any) {
            root.moveUndoStack = root.moveUndoStack.slice(-99).concat([changed])
            root.moveRedoStack = []
            savePositionsTimer.restart()
        }
    }

    // puts the cards in entry back as it describes and returns the entry that reverses that
    function applyMoveEntry(entry) {
        var inverse = ({})
        for (var name in entry) {
            var card = root.nodeItems[name]
            if (!card)
                continue
            inverse[name] = { x: card.x / card.sizeFactor, y: card.y / card.sizeFactor,
                              wasSaved: !!root.savedPositions[name] }
            card.x = entry[name].x * card.sizeFactor
            card.y = entry[name].y * card.sizeFactor
            if (entry[name].wasSaved)
                root.savedPositions[name] = { x: entry[name].x, y: entry[name].y }
            else
                delete root.savedPositions[name]
        }
        savePositionsTimer.restart()
        return inverse
    }

    function undoMove() {
        if (root.moveUndoStack.length === 0)
            return
        var entry = root.moveUndoStack[root.moveUndoStack.length - 1]
        root.moveUndoStack = root.moveUndoStack.slice(0, -1)
        root.moveRedoStack = root.moveRedoStack.concat([root.applyMoveEntry(entry)])
    }

    function redoMove() {
        if (root.moveRedoStack.length === 0)
            return
        var entry = root.moveRedoStack[root.moveRedoStack.length - 1]
        root.moveRedoStack = root.moveRedoStack.slice(0, -1)
        root.moveUndoStack = root.moveUndoStack.concat([root.applyMoveEntry(entry)])
    }

    function resetLayout() {
        if (typeof projectBridge === "undefined")
            return
        projectBridge.reset_user_positions("")
        root.loadWorkflow()
        root.snapCardsToDesign()
    }

    Shortcut {
        sequences: [StandardKey.Undo]
        enabled: root.currentView === "workflow"
        onActivated: root.undoMove()
    }

    Shortcut {
        sequences: [StandardKey.Redo, "Ctrl+Shift+Z"]
        enabled: root.currentView === "workflow"
        onActivated: root.redoMove()
    }

    function rebuildRoutes() {
        var cards = ({})
        var names = Object.keys(root.nodeItems)
        for (var i = 0; i < names.length; i++) {
            var card = root.nodeItems[names[i]]
            var s = card.sizeFactor
            cards[names[i]] = { x: card.x / s, y: card.y / s, width: card.width / s, height: card.height / s }
        }
        root.routes = Router.routeAll(cards, root.workflow.connections || [], 1)
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

        var raw = projectBridge.get_workflow("")

        if (!raw)
            return

        var parsed = JSON.parse(raw)
        var items = parsed.items || []
        var connections = parsed.connections || []

        if (items.length > 0) {
            var size = layoutWorkflow(items, connections, !!parsed.compact_rows)

            // cards the user has moved keep their saved place; names that no longer exist are ignored
            try {
                root.savedPositions = JSON.parse(projectBridge.get_user_positions(""))
            } catch (error) {
                root.savedPositions = ({})
            }
            var placed = items.map(function (item) { return { x: item.px, y: item.py } })
            for (var i = 0; i < items.length; i++) {
                var saved = root.savedPositions[items[i].name]
                if (saved) {
                    items[i].px = saved.x
                    items[i].py = saved.y
                }
            }
            // a saved place that now lies on top of another card is stale, so the card goes back to the layout
            for (var a = 0; a < items.length; a++) {
                var overlaps = root.savedPositions[items[a].name] && items.some(function (other, b) {
                    return b !== a && Math.abs(other.px - items[a].px) < 150 && Math.abs(other.py - items[a].py) < 74
                })
                if (overlaps) {
                    delete root.savedPositions[items[a].name]
                    items[a].px = placed[a].x
                    items[a].py = placed[a].y
                }
            }
            for (var c = 0; c < items.length; c++) {
                size.width = Math.max(size.width, items[c].px + 160)
                size.height = Math.max(size.height, items[c].py + 160)
            }

            root.designContentWidth = size.width + 110
            root.designContentHeight = size.height + 34
        }

        // don't clear nodeItems here: the Repeater reuses existing WorkflowCard delegates when the
        // new items array has the same length, so Component.onCompleted (the only place that
        // populates nodeItems) wouldn't refire and repopulate them, permanently losing valid
        // references and making every connection line and filter badge vanish
        root.workflow = parsed
        root.moveUndoStack = []
        root.moveRedoStack = []
        root.loadChainMembers()
        root.loadStoreWarnings()
        root.scheduleRoutes()
    }

    // starts the first-run tour; the delay lets the layout and the routes settle before targets are measured
    function startTour() {
        root.currentView = "workflow"
        tourStartTimer.restart()
    }

    Timer {
        id: tourStartTimer
        interval: 300
        onTriggered: root.beginTour()
    }

    // first filter badge that is fully inside the visible part of the canvas, or null
    function visibleFilterBadge() {
        for (var i = 0; i < filterBadges.count; i++) {
            var badge = filterBadges.itemAt(i)
            if (!badge || !badge.visible)
                continue

            var position = badge.mapToItem(designFlick, 0, 0)
            if (position.x >= 0 && position.y >= 0
                    && position.x + badge.width <= designFlick.width
                    && position.y + badge.height <= designFlick.height)
                return badge
        }
        return null
    }

    function beginTour() {
        var instructions = typeof projectBridge !== "undefined" ? JSON.parse(projectBridge.get_instructions()) : []
        tour.start(TourSteps.buildSteps(!!root.currentProjectName, {
            canvas: designCanvas,
            filterBadge: root.visibleFilterBadge(),
            runButton: runProjectButton,
            help: helpNavButton
        }, instructions, root.nodeItems))
    }

    Component.onCompleted: {
        if (typeof projectBridge !== "undefined")
            currentProjectName = projectBridge.get_project_name()

        loadChains(true)
        loadWorkflow()
        loadRunResults()
        offerProjectSetup()

        if (typeof projectBridge !== "undefined" && root.currentProjectName && !projectBridge.is_tour_seen())
            root.startTour()
    }

    // shrink workflow cards so they keep fitting without horizontal scrolling on narrow windows,
    // multiplied by a user-controlled zoom factor from the −/+/Fit buttons or the mouse wheel
    property real zoomLevel: 1.0

    // floored so the two factors combined never shrink cards past where text/line rendering breaks down
    property real cardScale: Math.max(0.35, root.zoomLevel * Math.max(0.35, Math.min(1, designFlick.width / root.designContentWidth)))

    function zoomIn() {
        root.zoomLevel = Math.min(2.5, root.zoomLevel * 1.2)
    }

    function zoomOut() {
        root.zoomLevel = Math.max(0.35, root.zoomLevel / 1.2)
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

                    onClicked: root.currentView = "database"
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
                    id: runsNavButton

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
                    id: helpNavButton

                    text: "Help"
                    iconText: "?"
                    compact: root.compactSidebar

                    onClicked: root.startTour()
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

                    Button {
                        id: openProjectButton

                        text: "Open project"

                        onClicked: openProjectDialog.open()

                        FolderDialog {
                            id: openProjectDialog

                            title: "Choose a project folder (must contain .spinetoolbox)"

                            onAccepted: {
                                var name = projectBridge.open_project(selectedFolder.toString())

                                if (name) {
                                    root.currentProjectName = name
                                    root.dataStores = JSON.parse(projectBridge.get_data_stores("data"))
                                    root.currentDataStore = ""
                                    root.resultDataStores = JSON.parse(projectBridge.get_data_stores("results"))

                                    if (resultsDataArea.visible)
                                        projectBridge.open_result_databases()

                                    root.loadChains(true)
                                    root.loadWorkflow()
                                    root.offerProjectSetup()
                                }
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
                                if (selectedNames.length === 0 && root.hasUnselectedScenarios)
                                    unselectedScenariosDialog.open()
                                else
                                    projectBridge.run_workflow(selectedNames, root.currentChain)
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

                        onAccepted: projectBridge.run_workflow([], root.currentChain)
                    }
                }
            }

            // -------------------------------------------------
            // SETUP STATUS BANNER (shown while/after a project's setup script runs)
            // -------------------------------------------------

            Rectangle {
                Layout.fillWidth: true
                height: 32

                visible: root.setupStatusMessage !== "" && !root.setupRunning

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
                        var before = root.cardPositions()
                        for (var i = 0; i < names.length; i++) {
                            var nodeItem = root.nodeItems[names[i]]
                            if (nodeItem) {
                                nodeItem.x += dx * step
                                nodeItem.y += dy * step
                            }
                        }
                        root.recordMove(before)
                        event.accepted = true
                    }

                    Label {
                        anchors.centerIn: parent
                        width: Math.min(parent.width - 48, 420)
                        visible: !root.currentProjectName
                        z: 1
                        horizontalAlignment: Text.AlignHCenter
                        wrapMode: Text.WordWrap
                        color: "#4b5563"
                        font.pixelSize: 16
                        text: qsTr("No project open.\nClick \"Open project\" and choose a folder that contains a .spinetoolbox project. "
                                   + "Click Help for a tour with an example project.")
                    }

                    // scrollable so fixed-position cards stay reachable on narrow windows
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

                        // lines are routed in design units and scaled with the cards, so they follow a window
                        // resize or zoom in the same frame without being re-routed
                        Item {
                            id: connectionsLayer

                            scale: root.cardScale
                            transformOrigin: Item.TopLeft
                            // above idle cards (z: 1) so arrows are never hidden behind them,
                            // but below a card actively being dragged (z: 10)
                            z: 5

                            Repeater {
                                model: root.workflow.connections || []

                                Shape {
                                    id: connectionShape

                                    // bold + saturated for a line that will actually carry data when run, thin and
                                    // pale when it's idle (another line covers the target), reddish when broken
                                    readonly property string lineState: modelData.filter_type === null
                                            || modelData.filter_state === "ok"
                                            ? "active" : modelData.filter_state === "error" ? "error" : "idle"
                                    readonly property color lineColor: lineState === "idle" ? "#c7d2d6"
                                            : lineState === "error" ? "#dc2626" : "#2f6b4a"
                                    readonly property var route: root.nodeItemsTick >= 0
                                            && root.nodeItems[modelData.from] && root.nodeItems[modelData.to]
                                            ? root.routes[modelData.from + "|" + modelData.to] : undefined

                                    visible: !!route
                                    opacity: root.isDimmed(modelData.from) || root.isDimmed(modelData.to) ? 0.2 : 1
                                    preferredRendererType: Shape.CurveRenderer

                                    ShapePath {
                                        strokeColor: connectionShape.lineColor
                                        strokeWidth: connectionShape.lineState === "idle" ? 3 : 5
                                        fillColor: "transparent"
                                        capStyle: ShapePath.FlatCap

                                        PathSvg {
                                            path: connectionShape.route ? connectionShape.route.line : ""
                                        }
                                    }

                                    ShapePath {
                                        strokeColor: "transparent"
                                        fillColor: connectionShape.lineColor

                                        PathSvg {
                                            path: connectionShape.route ? connectionShape.route.arrow : ""
                                        }
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
                                opacity: root.isDimmed(modelData.name) ? 0.35 : 1
                                Component.onCompleted: {
                                    root.nodeItems[modelData.name] = this
                                    root.nodeItemsTick += 1
                                    root.scheduleRoutes()
                                }

                                Component.onDestruction: {
                                    if (root.nodeItems[nodeName] === this)
                                        delete root.nodeItems[nodeName]
                                }
                            }
                        }

                        // =================================================
                        // FILTER BADGES (one per connection that has scenario/alternative filters,
                        // positioned at the connector's midpoint; red when a required filter has
                        // nothing checked, so missing selections are visible without opening anything)
                        // =================================================

                        Repeater {
                            id: filterBadges

                            model: root.workflow.connections

                            Rectangle {
                                // root.nodeItemsTick forces this binding to re-evaluate once cards finish
                                // registering themselves in root.nodeItems (see comment on nodeItemsTick)
                                visible: !!(root.nodeItemsTick >= 0 && modelData.filter_type
                                        && root.nodeItems[modelData.from] && root.nodeItems[modelData.to])

                                property point anchorPoint: visible
                                        ? root.connectionAnchor(modelData.from, modelData.to) : Qt.point(0, 0)

                                x: anchorPoint.x * root.cardScale - width / 2
                                y: anchorPoint.y * root.cardScale - height / 2
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
                                opacity: root.isDimmed(modelData.from) || root.isDimmed(modelData.to)
                                         ? 0.2 : modelData.filter_state === "disabled_ok" ? 0.6 : 1.0

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

                        Button {
                            id: chainBox

                            visible: root.chainList.length > 0
                            implicitWidth: 220

                            ToolTip.visible: hovered
                            ToolTip.text: "Chains highlighted on the canvas; Run runs the highlighted chains"

                            text: {
                                if (root.selectedChains.length === 0)
                                    return "All items"
                                if (root.selectedChains.length > 1)
                                    return root.selectedChains.length + " chains"
                                var chain = root.chainList.find(function (c) { return c.key === root.selectedChains[0] })
                                return chain ? chain.name : root.selectedChains[0]
                            }

                            onClicked: chainMenu.popup(chainBox, 0, chainBox.height)

                            Menu {
                                id: chainMenu

                                MenuItem {
                                    text: "All items"
                                    checkable: true
                                    checked: root.selectedChains.length === 0
                                    onTriggered: root.toggleChain("")
                                }

                                Repeater {
                                    model: root.chainList

                                    MenuItem {
                                        text: modelData.key === root.defaultChain ? modelData.name + " (default)"
                                                                                  : modelData.name
                                        checkable: true
                                        checked: root.selectedChains.indexOf(modelData.key) >= 0
                                        onTriggered: root.toggleChain(modelData.key)
                                    }
                                }
                            }
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

                        ToolButton {
                            text: "Reset layout"

                            ToolTip.visible: hovered
                            ToolTip.text: "Forget the card positions you have moved"

                            onClicked: root.resetLayout()
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
            // DATA PAGE (the classic DB editor widget is shown over this area, see ProjectBridge.set_data_area)
            // =================================================

            ColumnLayout {
                id: dataPage

                Layout.fillWidth: true
                Layout.fillHeight: true

                spacing: 0
                visible: root.currentView === "database"

                onVisibleChanged: {
                    if (visible)
                        root.dataStores = JSON.parse(projectBridge.get_data_stores("data"))
                }

                RowLayout {
                    Layout.fillWidth: true
                    Layout.margins: 8

                    Label {
                        text: "Database"
                    }

                    ComboBox {
                        id: dataStoreCombo

                        Layout.preferredWidth: 260

                        model: root.dataStores
                        currentIndex: root.dataStores.indexOf(root.currentDataStore)
                        displayText: root.currentDataStore || "Choose database..."

                        onActivated: function (index) {
                            root.currentDataStore = root.dataStores[index]
                            projectBridge.open_database(root.currentDataStore)
                        }
                    }

                    Button {
                        text: "Purge..."
                        enabled: root.currentDataStore !== ""

                        ToolTip.visible: hovered
                        ToolTip.text: "Remove data from this database"

                        onClicked: projectBridge.purge_data_store(root.currentDataStore)
                    }

                    Item {
                        Layout.fillWidth: true
                    }
                }

                Item {
                    id: dataArea

                    Layout.fillWidth: true
                    Layout.fillHeight: true

                    // the editor is a widget drawn above all QML, so it is hidden while the dropdown is open
                    function report() {
                        var origin = dataArea.mapToItem(null, 0, 0)
                        projectBridge.set_data_area("data", origin.x, origin.y, dataArea.width, dataArea.height,
                                                    dataArea.visible && !dataStoreCombo.popup.visible)
                    }

                    onXChanged: Qt.callLater(report)
                    onYChanged: Qt.callLater(report)
                    onWidthChanged: Qt.callLater(report)
                    onHeightChanged: Qt.callLater(report)
                    onVisibleChanged: Qt.callLater(report)

                    Connections {
                        target: dataStoreCombo.popup

                        function onVisibleChanged() { Qt.callLater(dataArea.report) }
                    }

                    Connections {
                        target: root

                        function onWidthChanged() { Qt.callLater(dataArea.report) }
                        function onHeightChanged() { Qt.callLater(dataArea.report) }
                    }
                }
            }

            // =================================================
            // RESULTS PAGE (Plottings: plots produced by the latest run; Data: result databases)
            // =================================================

            ColumnLayout {
                id: resultsPage

                Layout.fillWidth: true
                Layout.fillHeight: true

                spacing: 0
                visible: root.currentView === "results"

                TabBar {
                    id: resultsTabBar

                    Layout.fillWidth: true

                    TabButton { text: "Plots" }
                    TabButton { text: "Results" }
                    TabButton { text: "Files" }
                    TabButton { text: "All databases" }
                }

            Rectangle {
                id: plotsTab

                Layout.fillWidth: true
                Layout.fillHeight: true

                visible: resultsTabBar.currentIndex === 0
                color: "#f2f8f4"

                // the plots of the latest run, or the ones the user has saved
                readonly property var plotItems: root.showSavedPlots
                    ? root.savedPlots.map(function (plot) {
                        return { "url": plot.url, "name": plot.name, "file": plot.file, "label": plot.run_label }
                    })
                    : root.plotUrls.map(function (url) {
                        return { "url": url, "name": decodeURIComponent(url.split("/").pop()), "file": "", "label": "" }
                    })

                onVisibleChanged: {
                    if (visible && root.showSavedPlots)
                        root.loadSavedPlots()
                }

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 20
                    spacing: 12

                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 8

                        Button {
                            text: "Latest run"
                            checkable: true
                            checked: !root.showSavedPlots
                            onClicked: root.showSavedPlots = false
                        }

                        Button {
                            text: "Saved"
                            checkable: true
                            checked: root.showSavedPlots
                            onClicked: {
                                root.showSavedPlots = true
                                root.loadSavedPlots()
                            }
                        }

                        ComboBox {
                            visible: root.showSavedPlots
                            implicitWidth: 200
                            textRole: "name"
                            valueRole: "key"
                            model: [{ "key": "*", "name": "All chains" }].concat(root.savedPlotFilters.chains)
                            currentIndex: {
                                for (var i = 0; i < model.length; i++) {
                                    if (model[i].key === root.savedPlotChain)
                                        return i
                                }
                                return 0
                            }
                            onActivated: {
                                root.savedPlotChain = currentValue
                                root.loadSavedPlots()
                            }
                        }

                        ComboBox {
                            visible: root.showSavedPlots
                            implicitWidth: 260
                            textRole: "label"
                            valueRole: "started"
                            model: [{ "started": "*", "label": "All runs" }].concat(root.savedPlotFilters.runs)
                            currentIndex: {
                                for (var i = 0; i < model.length; i++) {
                                    if (String(model[i].started) === root.savedPlotRun)
                                        return i
                                }
                                return 0
                            }
                            onActivated: {
                                root.savedPlotRun = String(currentValue)
                                root.loadSavedPlots()
                            }
                        }

                        TextField {
                            visible: root.showSavedPlots
                            Layout.fillWidth: true
                            placeholderText: "Search by name"
                            text: root.savedPlotQuery
                            onTextEdited: {
                                root.savedPlotQuery = text
                                root.loadSavedPlots()
                            }
                        }

                        Item {
                            visible: !root.showSavedPlots
                            Layout.fillWidth: true
                        }
                    }

                    Label {
                        visible: plotsTab.plotItems.length === 0
                        Layout.alignment: Qt.AlignHCenter
                        text: root.showSavedPlots ? "No saved plots match. Save plots from the latest run to keep them."
                                                  : "No plots yet. Run a workflow that creates plots."
                        color: "#475569"
                        font.pixelSize: 15
                    }

                    ScrollView {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        clip: true
                        contentWidth: availableWidth

                        ColumnLayout {
                            width: parent.width
                            spacing: 16

                            Repeater {
                                model: plotsTab.plotItems

                                Rectangle {
                                    id: plotCard

                                    property bool justSaved: false

                                    Layout.fillWidth: true
                                    Layout.preferredHeight: plotImage.implicitWidth > 0
                                        ? (width - 20) * plotImage.implicitHeight / plotImage.implicitWidth + 20 : 0
                                    radius: 10
                                    color: "white"

                                    Image {
                                        id: plotImage

                                        anchors.fill: parent
                                        anchors.margins: 10
                                        source: modelData.url
                                        fillMode: Image.PreserveAspectFit
                                        cache: false
                                    }

                                    Timer {
                                        id: savedMessageTimer
                                        interval: 2000
                                        onTriggered: plotCard.justSaved = false
                                    }

                                    RowLayout {
                                        anchors.top: parent.top
                                        anchors.right: parent.right
                                        anchors.margins: 12
                                        spacing: 6

                                        Label {
                                            visible: modelData.label !== ""
                                            text: modelData.label
                                            color: "#475569"
                                            font.pixelSize: 12
                                        }

                                        Button {
                                            visible: !root.showSavedPlots
                                            text: plotCard.justSaved ? "Saved" : "Save"
                                            onClicked: {
                                                if (projectBridge.save_plot(modelData.url)) {
                                                    plotCard.justSaved = true
                                                    savedMessageTimer.restart()
                                                }
                                            }
                                        }

                                        Button {
                                            text: "Save as..."
                                            onClicked: projectBridge.save_plot_as(modelData.url)
                                        }

                                        Button {
                                            visible: root.showSavedPlots
                                            text: "Delete"
                                            onClicked: {
                                                confirmDeletePlotDialog.plotFile = modelData.file
                                                confirmDeletePlotDialog.open()
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }

                Dialog {
                    id: confirmDeletePlotDialog

                    property string plotFile: ""

                    anchors.centerIn: parent
                    implicitWidth: 320
                    modal: true
                    title: "Delete saved plot"
                    standardButtons: Dialog.Ok | Dialog.Cancel

                    contentItem: Label {
                        text: "Delete this saved plot?"
                        padding: 12
                    }

                    onAccepted: {
                        projectBridge.delete_saved_plot(plotFile)
                        root.loadSavedPlots()
                    }
                }
            }

            ColumnLayout {
                id: runResultsTab

                Layout.fillWidth: true
                Layout.fillHeight: true

                spacing: 0
                visible: resultsTabBar.currentIndex === 1

                onVisibleChanged: {
                    if (visible)
                        projectBridge.open_run_results(root.currentChain)
                }

                Connections {
                    target: root

                    function onCurrentChainChanged() {
                        if (runResultsTab.visible)
                            projectBridge.open_run_results(root.currentChain)
                    }
                }

                Label {
                    Layout.fillWidth: true
                    Layout.margins: 8
                    wrapMode: Text.WordWrap
                    text: root.runResultsSummary()
                    color: "#334155"
                }

                Item {
                    id: resultsRunArea

                    Layout.fillWidth: true
                    Layout.fillHeight: true

                    function report() {
                        var origin = resultsRunArea.mapToItem(null, 0, 0)
                        projectBridge.set_data_area("run", origin.x, origin.y, resultsRunArea.width,
                                                    resultsRunArea.height, resultsRunArea.visible)
                    }

                    onXChanged: Qt.callLater(report)
                    onYChanged: Qt.callLater(report)
                    onWidthChanged: Qt.callLater(report)
                    onHeightChanged: Qt.callLater(report)
                    onVisibleChanged: Qt.callLater(report)

                    Label {
                        anchors.centerIn: parent
                        visible: !root.runResults.stores || Object.keys(root.runResults.stores).length === 0
                        text: "Run a chain that writes to a result database to see its results here."
                        color: "#475569"
                        font.pixelSize: 15
                    }

                    Connections {
                        target: root

                        function onWidthChanged() { Qt.callLater(resultsRunArea.report) }
                        function onHeightChanged() { Qt.callLater(resultsRunArea.report) }
                    }
                }
            }

            Rectangle {
                Layout.fillWidth: true
                Layout.fillHeight: true

                visible: resultsTabBar.currentIndex === 2
                color: "#f2f8f4"

                Label {
                    anchors.centerIn: parent
                    visible: !root.runResults.files || root.runResults.files.length === 0
                    text: "No exported files from the latest run of this chain."
                    color: "#475569"
                    font.pixelSize: 15
                }

                ListView {
                    anchors.fill: parent
                    anchors.margins: 20
                    clip: true
                    spacing: 8
                    model: root.runResults.files || []

                    delegate: Rectangle {
                        width: ListView.view.width
                        height: 48
                        radius: 8
                        color: "white"

                        RowLayout {
                            anchors.fill: parent
                            anchors.leftMargin: 12
                            anchors.rightMargin: 12
                            spacing: 8

                            Label {
                                Layout.fillWidth: true
                                text: modelData.split("\\").pop().split("/").pop()
                                elide: Text.ElideMiddle

                                ToolTip.visible: fileHover.hovered
                                ToolTip.text: modelData

                                HoverHandler {
                                    id: fileHover
                                }
                            }

                            Button {
                                text: "Open file"
                                onClicked: projectBridge.open_file(modelData)
                            }

                            Button {
                                text: "Open folder"
                                onClicked: projectBridge.open_folder(modelData)
                            }
                        }
                    }
                }
            }

            Item {
                id: resultsDataArea

                Layout.fillWidth: true
                Layout.fillHeight: true

                visible: resultsTabBar.currentIndex === 3

                function report() {
                    var origin = resultsDataArea.mapToItem(null, 0, 0)
                    projectBridge.set_data_area("results", origin.x, origin.y, resultsDataArea.width,
                                                resultsDataArea.height, resultsDataArea.visible)
                }

                onXChanged: Qt.callLater(report)
                onYChanged: Qt.callLater(report)
                onWidthChanged: Qt.callLater(report)
                onHeightChanged: Qt.callLater(report)

                onVisibleChanged: {
                    if (visible) {
                        root.resultDataStores = JSON.parse(projectBridge.get_data_stores("results"))
                        projectBridge.open_result_databases()
                    }

                    Qt.callLater(report)
                }

                Label {
                    anchors.centerIn: parent
                    visible: root.resultDataStores.length === 0
                    text: "No result databases. Mark a Data Store as a result database in the classic UI."
                    color: "#475569"
                    font.pixelSize: 15
                }

                Connections {
                    target: root

                    function onWidthChanged() { Qt.callLater(resultsDataArea.report) }
                    function onHeightChanged() { Qt.callLater(resultsDataArea.report) }
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
            }
        }
    }

    GuidedTour {
        id: tour

        anchors.fill: parent

        onFinished: {
            if (typeof projectBridge !== "undefined")
                projectBridge.mark_tour_seen()
        }
    }

    // blocks the whole UI while the project's dependencies are being installed
    Rectangle {
        anchors.fill: parent
        z: 10000
        visible: root.setupRunning
        color: "#99000000"
        focus: visible

        Keys.onPressed: function (event) { event.accepted = true }

        MouseArea {
            anchors.fill: parent
            hoverEnabled: true
            preventStealing: true
            onWheel: function (wheel) { wheel.accepted = true }
        }

        Rectangle {
            anchors.centerIn: parent
            width: Math.min(480, parent.width - 48)
            height: setupColumn.implicitHeight + 48
            radius: 12
            color: "#ffffff"

            ColumnLayout {
                id: setupColumn
                anchors.fill: parent
                anchors.margins: 24
                spacing: 12

                BusyIndicator {
                    Layout.alignment: Qt.AlignHCenter
                    running: root.setupRunning
                }

                Label {
                    Layout.fillWidth: true
                    horizontalAlignment: Text.AlignHCenter
                    text: "Installing dependencies of the project"
                    font.pixelSize: 17
                    font.bold: true
                }

                Label {
                    Layout.fillWidth: true
                    horizontalAlignment: Text.AlignHCenter
                    elide: Text.ElideRight
                    opacity: 0.6
                    text: root.setupStatusMessage
                }

                Label {
                    Layout.fillWidth: true
                    horizontalAlignment: Text.AlignHCenter
                    wrapMode: Text.WordWrap
                    opacity: 0.6
                    font.pixelSize: 12
                    text: "This can take several minutes. Please wait until it finishes; the full log is in Runs."
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
        property bool isStack: false
        property string nodeName: ""
        property bool selected: false

        property real designX: 0
        property real designY: 0
        property real sizeFactor: 1

        // x/y are set imperatively (dragging owns them), so zooming rescales them explicitly
        property real previousSizeFactor: 1
        property bool rescaling: false

        onSizeFactorChanged: {
            rescaling = true
            x = x * sizeFactor / previousSizeFactor
            y = y * sizeFactor / previousSizeFactor
            rescaling = false
            previousSizeFactor = sizeFactor
        }

        onDesignXChanged: x = designX * sizeFactor
        onDesignYChanged: y = designY * sizeFactor

        Component.onCompleted: {
            x = designX * sizeFactor
            y = designY * sizeFactor
        }

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

        // a card that will actually run (filters chosen) gets a bold green highlight so the active
        // path through a multi-branch workflow is traceable

        // stacks and plain items share the same neutral default look; only active/selection state
        // (not item kind) should stand out, so the accent color here is type-coded only for hover/icons
        property bool active: !filtersUnchosen

        border.color: selected
                      ? "#2563eb"
                      : active
                        ? "#2f6b4a"
                        : (hovered ? accent : "#e2e8f0")

        border.width: (selected || active)
                      ? 3
                      : (hovered ? 2 : 1)

        property bool hovered: false

        property string runState: root.itemRunStates[nodeName] || ""

        // same glyphs and colors as the classic UI's ExecutionIcon
        readonly property color runColor: runState === "done" ? "green"
                                        : runState === "failed" ? "red"
                                        : runState === "skipped" ? "chocolate" : "orange"
        readonly property string runSymbol: runState === "waiting" || runState === "running" ? "\u2026"
                                          : runState === "failed" ? "\u2716"
                                          : runState === "skipped" ? "\u00bb" : "\u2714"

        Rectangle {
            id: runBadge

            visible: ["waiting", "running", "done", "failed", "skipped"].indexOf(card.runState) >= 0
            z: 5
            anchors.right: parent.right
            anchors.bottom: parent.bottom
            anchors.rightMargin: -6 * card.sizeFactor
            anchors.bottomMargin: -6 * card.sizeFactor

            width: 20 * card.sizeFactor
            height: width
            radius: width / 2

            color: "#ffffff"
            border.color: card.runColor
            border.width: 2 * card.sizeFactor

            Label {
                anchors.centerIn: parent
                text: card.runSymbol
                color: card.runColor
                font.pixelSize: 11 * card.sizeFactor
                font.bold: true
            }

            ToolTip.visible: runBadgeHover.hovered
            ToolTip.text: "Execution " + (card.runState === "waiting" || card.runState === "running"
                                          ? "waiting for dependencies"
                                          : card.runState === "done" ? "completed" : card.runState)

            HoverHandler {
                id: runBadgeHover
            }
        }

        Rectangle {
            id: storeBadge

            visible: card.nodeName in root.storeWarnings
            z: 5
            anchors.left: parent.left
            anchors.bottom: parent.bottom
            anchors.leftMargin: -6 * card.sizeFactor
            anchors.bottomMargin: -6 * card.sizeFactor

            width: 20 * card.sizeFactor
            height: width
            radius: width / 2

            color: "#fef3c7"
            border.color: "#d97706"
            border.width: 2 * card.sizeFactor

            Label {
                anchors.centerIn: parent
                text: "!"
                color: "#b45309"
                font.pixelSize: 12 * card.sizeFactor
                font.bold: true
            }

            ToolTip.visible: storeBadgeHover.hovered
            ToolTip.text: "Holds data from chain \"" + root.storeWarnings[card.nodeName]
                          + "\". Purge it before running this chain if the old data should not be used."

            HoverHandler {
                id: storeBadgeHover
            }
        }

        scale: hovered ? 1.015 : 1
        z: dragArea.drag.active ? 10 : 1

        Behavior on scale {
            NumberAnimation {
                duration: 120
            }
        }

        // redraw arrows as the card is dragged around; rescaling moves cards but not in design units
        onXChanged: if (!rescaling) root.scheduleRoutes()
        onYChanged: if (!rescaling) root.scheduleRoutes()

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

            property real lastX: 0
            property real lastY: 0
            property bool wasSelectedOnPress: false

            onEntered: card.hovered = true
            onExited: card.hovered = false

            onPressed: function (mouse) {
                designCanvas.forceActiveFocus()
                root.moveSnapshot = root.cardPositions()
                lastX = card.x
                lastY = card.y
                wasSelectedOnPress = card.selected

                if (mouse.modifiers & Qt.ControlModifier)
                    root.toggleSelection(card.nodeName)
                else if (!card.selected)
                    root.selectOnly(card.nodeName)
            }

            onReleased: root.recordMove(root.moveSnapshot)

            // a plain click (no drag) on a card that was already selected deselects it
            onClicked: function (mouse) {
                if (wasSelectedOnPress && !(mouse.modifiers & Qt.ControlModifier))
                    root.toggleSelection(card.nodeName)
            }

            // snaps the moving group (every selected card, or just this one) to unselected cards within a few pixels
            function snapToNeighbours() {
                var threshold = 10 * card.sizeFactor
                var bestX = threshold
                var bestY = threshold
                var shiftX = 0
                var shiftY = 0
                var rawDx = card.selected ? card.x - lastX : 0
                var rawDy = card.selected ? card.y - lastY : 0
                var movers = card.selected ? Object.keys(root.selectedNames) : [card.nodeName]

                for (var i = 0; i < movers.length; i++) {
                    var mover = root.nodeItems[movers[i]]

                    if (!mover)
                        continue

                    var moverX = mover === card ? mover.x : mover.x + rawDx
                    var moverY = mover === card ? mover.y : mover.y + rawDy

                    for (var name in root.nodeItems) {
                        var other = root.nodeItems[name]

                        if (!other || root.selectedNames[name] || other === card)
                            continue

                        if (Math.abs(other.x - moverX) < bestX) {
                            bestX = Math.abs(other.x - moverX)
                            shiftX = other.x - moverX
                        }

                        if (Math.abs(other.y - moverY) < bestY) {
                            bestY = Math.abs(other.y - moverY)
                            shiftY = other.y - moverY
                        }
                    }
                }

                card.x += shiftX
                card.y += shiftY
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

            onDoubleClicked: {
                wasSelectedOnPress = false

                if (typeof projectBridge === "undefined")
                    return

                if (card.subtitle === "Data Connection") {
                    projectBridge.open_item_directory(card.nodeName)
                    return
                }

                if (card.subtitle === "Data Store") {
                    projectBridge.open_database(card.nodeName)
                }
            }
        }

        TapHandler {
            acceptedButtons: Qt.RightButton
            enabled: card.subtitle === "Data Store"
            onTapped: cardMenu.popup()
        }

        Menu {
            id: cardMenu

            MenuItem {
                text: "Purge database..."
                onTriggered: projectBridge.purge_data_store(card.nodeName)
            }
        }

        ToolTip {
            visible: card.hovered && text !== ""
            text: {
                // item-specific guidance for double-click actions
                if (card.title === "Excel input")
                    return "Double-click to choose the Excel input file"
                if (card.subtitle === "Data Connection")
                    return "Double-click to open the data connection directory"
                if (card.subtitle === "Data Store")
                    return "Double-click to open in the database editor"
                return ""
            }
        }


        Item {
            width: 150
            height: 74

            scale: card.sizeFactor
            transformOrigin: Item.TopLeft

            RowLayout {
                anchors.top: parent.top
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.margins: 11

                Rectangle {
                    Layout.preferredWidth: 28
                    Layout.preferredHeight: 28

                    radius: 8

                    color: card.accent

                    Label {
                        anchors.centerIn: parent

                        text: card.iconText

                        color: "white"
                        font.pixelSize: 14
                        font.bold: true
                    }
                }

                Label {
                    text: card.subtitle

                    visible: card.subtitle.length > 0

                    font.pixelSize: 11
                    opacity: 0.6

                    elide: Text.ElideRight
                }

                Item {
                    Layout.fillWidth: true
                }

                Label {
                    text: "⋮"

                    opacity: 0.4
                    font.pixelSize: 13
                }
            }

            ColumnLayout {
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.bottom: parent.bottom
                anchors.margins: 11

                spacing: 0

                Label {
                    text: card.title

                    Layout.fillWidth: true

                    font.pixelSize: 13
                    font.bold: true

                    elide: Text.ElideRight
                }
            }
        }
    }
}
