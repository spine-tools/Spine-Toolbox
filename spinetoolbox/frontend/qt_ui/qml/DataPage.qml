import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// Database browser and editor; edits stay in ProjectBridge's session until committed
Rectangle {
    id: page

    color: "#f2f8f4"

    property var databases: []
    property bool databasesLoaded: false
    property string selectedDatabaseUrl: ""
    property var databaseContents: ({ "entity_classes": [], "alternatives": [], "scenario_tree": [] })
    property string selectedEntityClass: ""
    property var pivot: ({ "alternatives": [], "alternative": "", "parameters": [], "rows": [] })
    property string pivotAlternative: ""
    // uncommitted edits of the selected database, and the last rejected edit's message
    property var sessionState: ({ "dirty": false, "can_undo": false, "can_redo": false })
    property string editError: ""

    readonly property var emptyContents: ({ "entity_classes": [], "alternatives": [], "scenario_tree": [] })
    readonly property var emptyPivot: ({ "alternatives": [], "alternative": "", "parameters": [], "rows": [] })

    // loads the project's databases the first time the page is shown
    function open() {
        if (!page.databasesLoaded)
            page.loadDatabases()
    }

    // forgets the current databases, e.g. when another project is opened
    function reset() {
        page.databasesLoaded = false
        page.databases = []
        page.selectedDatabaseUrl = ""
        page.refreshData()
    }

    function loadDatabases() {
        page.databasesLoaded = true

        if (typeof projectBridge === "undefined")
            return

        var raw = projectBridge.get_databases()
        page.databases = raw ? JSON.parse(raw) : []

        if (page.databases.length > 0)
            page.selectDatabase(page.databases[0].url)
    }

    function selectDatabase(url) {
        page.selectedDatabaseUrl = url
        page.selectedEntityClass = ""
        page.pivotAlternative = ""
        page.editError = ""

        if (typeof projectBridge !== "undefined" && url)
            projectBridge.reload_database(url)

        page.refreshData()
    }

    function selectEntityClass(name) {
        page.selectedEntityClass = name
        page.loadPivot()
    }

    // reloads everything the page shows from the open session, including uncommitted edits
    function refreshData() {
        var url = page.selectedDatabaseUrl

        if (typeof projectBridge === "undefined" || !url) {
            page.databaseContents = page.emptyContents
            page.sessionState = ({ "dirty": false, "can_undo": false, "can_redo": false })
            page.loadPivot()
            return
        }

        var raw = projectBridge.get_database_contents(url)
        page.databaseContents = raw ? JSON.parse(raw) : page.emptyContents
        page.sessionState = JSON.parse(projectBridge.get_session_state(url))

        var names = (page.databaseContents.entity_classes || []).map(function (entityClass) { return entityClass.name })
        if (names.indexOf(page.selectedEntityClass) < 0)
            page.selectedEntityClass = ""

        page.loadPivot()
    }

    function loadPivot() {
        if (typeof projectBridge === "undefined" || !page.selectedDatabaseUrl || !page.selectedEntityClass) {
            page.pivot = page.emptyPivot
            return
        }

        var parsed = JSON.parse(projectBridge.get_pivot(page.selectedDatabaseUrl, page.selectedEntityClass,
                                                        page.pivotAlternative))
        page.pivot = parsed.error ? page.emptyPivot : parsed
        page.pivotAlternative = page.pivot.alternative
    }

    // takes the JSON a ProjectBridge editing slot returned and shows its outcome
    function applyEdit(raw) {
        page.editError = JSON.parse(raw).error || ""
        page.refreshData()
    }

    function setCell(entity, parameter, text) {
        page.applyEdit(projectBridge.set_parameter_value(page.selectedDatabaseUrl, page.selectedEntityClass, entity,
                                                         parameter, page.pivotAlternative, text))
    }

    function addItem(itemType, fields) {
        page.applyEdit(projectBridge.add_item(page.selectedDatabaseUrl, itemType, JSON.stringify(fields)))
    }

    function renameItem(itemType, key, newName) {
        page.applyEdit(projectBridge.update_item(page.selectedDatabaseUrl, itemType, JSON.stringify(key),
                                                 JSON.stringify({ "name": newName })))
    }

    function removeItem(itemType, key) {
        page.applyEdit(projectBridge.remove_item(page.selectedDatabaseUrl, itemType, JSON.stringify(key)))
    }

    function scenarioAlternatives(scenario) {
        var tree = page.databaseContents.scenario_tree || []

        for (var i = 0; i < tree.length; i++) {
            if (tree[i].name === scenario)
                return tree[i].alternatives.map(function (alternative) { return alternative.name })
        }

        return []
    }

    function setScenarioAlternatives(scenario, names) {
        page.applyEdit(projectBridge.set_scenario_alternatives(page.selectedDatabaseUrl, scenario, JSON.stringify(names)))
    }

    function moveScenarioAlternative(scenario, index, step) {
        var names = page.scenarioAlternatives(scenario)
        var target = index + step

        if (target < 0 || target >= names.length)
            return

        var moved = names.splice(index, 1)[0]
        names.splice(target, 0, moved)
        page.setScenarioAlternatives(scenario, names)
    }

    function removeScenarioAlternative(scenario, index) {
        var names = page.scenarioAlternatives(scenario)
        names.splice(index, 1)
        page.setScenarioAlternatives(scenario, names)
    }

    function askName(title, initialText, onConfirmed, allowEmpty) {
        nameDialog.title = title
        nameDialog.confirmed = onConfirmed
        nameDialog.allowEmpty = allowEmpty === true
        nameField.text = initialText
        nameDialog.open()
        nameField.selectAll()
        nameField.forceActiveFocus()
    }

    function askAdd(title, itemType, extraFields) {
        page.askName(title, "", function (name) {
            var fields = Object.assign({ "name": name }, extraFields)
            page.addItem(itemType, fields)
        })
    }

    function askRename(itemType, key, currentName) {
        page.askName("Rename " + currentName, currentName, function (name) {
            if (name !== currentName)
                page.renameItem(itemType, key, name)
        })
    }

    function askRemove(itemType, key, label) {
        confirmDialog.message = "Remove " + label + " and everything that depends on it?"
        confirmDialog.confirmed = function () { page.removeItem(itemType, key) }
        confirmDialog.open()
    }

    function askCommit() {
        page.askName("Commit message", "Edited in User Mode", function (comment) {
            page.applyEdit(projectBridge.commit_edits(page.selectedDatabaseUrl, comment || "Edited in User Mode"))
        }, true)
    }

    // runs proceed once any uncommitted edits have been committed or discarded; cancelled runs if the user backs out
    function guardUnsaved(proceed, cancelled) {
        if (!page.sessionState.dirty) {
            proceed()
            return
        }

        unsavedDialog.proceed = proceed
        unsavedDialog.cancelled = cancelled || function () {}
        unsavedDialog.open()
    }

    // dialogs are parented to the overlay so they also work while the page is hidden
    // (guardUnsaved is called when a project is opened from another view)

    // single-line text prompt shared by every add/rename/commit action
    Dialog {
        id: nameDialog

        property var confirmed: function (name) {}
        property bool allowEmpty: false

        parent: Overlay.overlay
        anchors.centerIn: parent
        modal: true
        width: 340
        standardButtons: Dialog.Ok | Dialog.Cancel

        contentItem: TextField {
            id: nameField

            onAccepted: nameDialog.accept()
        }

        onAccepted: {
            var name = nameField.text.trim()

            if (name || allowEmpty)
                confirmed(name)
        }
    }

    Dialog {
        id: confirmDialog

        property string message: ""
        property var confirmed: function () {}

        parent: Overlay.overlay
        anchors.centerIn: parent
        modal: true
        width: 380
        title: "Please confirm"
        standardButtons: Dialog.Ok | Dialog.Cancel

        contentItem: Label {
            text: confirmDialog.message
            wrapMode: Text.WordWrap
            padding: 12
        }

        onAccepted: confirmed()
    }

    Dialog {
        id: unsavedDialog

        property var proceed: function () {}
        property var cancelled: function () {}

        parent: Overlay.overlay
        anchors.centerIn: parent
        modal: true
        width: 400
        title: "Uncommitted changes"
        standardButtons: Dialog.Save | Dialog.Discard | Dialog.Cancel

        contentItem: Label {
            text: "The database has changes that have not been committed."
            wrapMode: Text.WordWrap
            padding: 12
        }

        onAccepted: {
            page.applyEdit(projectBridge.commit_edits(page.selectedDatabaseUrl, "Edited in User Mode"))

            if (page.sessionState.dirty)
                cancelled()
            else
                proceed()
        }

        onDiscarded: {
            page.applyEdit(projectBridge.discard_edits(page.selectedDatabaseUrl))
            close()
            proceed()
        }

        onRejected: cancelled()
    }

    Dialog {
        id: addAlternativeDialog

        property string scenario: ""
        property var available: []

        parent: Overlay.overlay
        anchors.centerIn: parent
        modal: true
        width: 340
        title: "Add alternative to " + scenario
        standardButtons: Dialog.Ok | Dialog.Cancel

        function openFor(scenarioName) {
            var used = page.scenarioAlternatives(scenarioName)
            scenario = scenarioName
            available = (page.databaseContents.alternatives || []).filter(function (name) {
                return used.indexOf(name) < 0
            })
            open()
        }

        contentItem: ComboBox {
            id: availableAlternatives

            model: addAlternativeDialog.available
        }

        onAccepted: {
            if (availableAlternatives.currentText) {
                page.setScenarioAlternatives(
                    scenario, page.scenarioAlternatives(scenario).concat([availableAlternatives.currentText]))
            }
        }
    }

    component RowMenu: ToolButton {
        default property alias menuItems: menu.contentData

        text: "\u22ee"
        implicitWidth: 26
        implicitHeight: 26

        onClicked: menu.popup()

        Menu {
            id: menu
        }
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 20

        spacing: 12

        // -------------------------------------------------
        // TOP BAR: undo/redo/commit for the selected database
        // -------------------------------------------------

        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 52

            radius: 10
            color: "#ffffff"
            border.color: "#e2e8f0"

            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 14
                anchors.rightMargin: 14
                spacing: 6
                enabled: page.selectedDatabaseUrl !== ""

                Button {
                    text: "Undo"
                    enabled: page.sessionState.can_undo
                    onClicked: page.applyEdit(projectBridge.undo_edit(page.selectedDatabaseUrl))
                }

                Button {
                    text: "Redo"
                    enabled: page.sessionState.can_redo
                    onClicked: page.applyEdit(projectBridge.redo_edit(page.selectedDatabaseUrl))
                }

                Rectangle {
                    Layout.preferredWidth: 1
                    Layout.preferredHeight: 24
                    color: "#e2e8f0"
                }

                Button {
                    text: "Commit"
                    enabled: page.sessionState.dirty
                    highlighted: page.sessionState.dirty
                    onClicked: page.askCommit()
                }

                Button {
                    text: "Discard"
                    enabled: page.sessionState.dirty
                    onClicked: {
                        confirmDialog.message = "Discard all uncommitted changes?"
                        confirmDialog.confirmed = function () {
                            page.applyEdit(projectBridge.discard_edits(page.selectedDatabaseUrl))
                        }
                        confirmDialog.open()
                    }
                }

                Label {
                    visible: page.sessionState.dirty
                    text: "Uncommitted changes"
                    color: "#b45309"
                    font.bold: true
                    font.pixelSize: 12
                }

                Label {
                    Layout.fillWidth: true
                    visible: page.editError !== ""
                    text: page.editError
                    color: "#dc2626"
                    font.pixelSize: 12
                    elide: Text.ElideRight
                    horizontalAlignment: Text.AlignRight
                }

                Item {
                    Layout.fillWidth: page.editError === ""
                }
            }
        }

        RowLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true

            spacing: 16

            // -------------------------------------------------
            // LEFT: database picker + entity classes
            // -------------------------------------------------

            Rectangle {
                Layout.preferredWidth: 190
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

                        model: page.databases
                        textRole: "name"

                        onActivated: {
                            var url = page.databases[currentIndex].url
                            page.guardUnsaved(function () {
                                page.selectDatabase(url)
                            }, function () {
                                currentIndex = page.databases.findIndex(function (database) {
                                    return database.url === page.selectedDatabaseUrl
                                })
                            })
                        }
                    }

                    Label {
                        visible: page.databaseContents.error !== undefined
                        text: page.databaseContents.error || ""
                        color: "#dc2626"
                        font.pixelSize: 11
                        wrapMode: Text.WordWrap
                        Layout.fillWidth: true
                    }

                    RowLayout {
                        Layout.fillWidth: true

                        Label {
                            Layout.fillWidth: true
                            text: "Entity classes"
                            font.bold: true
                            font.pixelSize: 12
                            opacity: 0.6
                        }

                        ToolButton {
                            text: "+"
                            enabled: page.selectedDatabaseUrl !== ""

                            ToolTip.visible: hovered
                            ToolTip.text: "Add entity class"

                            onClicked: page.askAdd("New entity class", "entity_class", {})
                        }
                    }

                    ListView {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        Layout.preferredHeight: 300
                        clip: true
                        model: page.databaseContents.entity_classes || []

                        ScrollBar.vertical: ScrollBar {}

                        delegate: RowLayout {
                            width: ListView.view.width
                            spacing: 0

                            Button {
                                Layout.fillWidth: true
                                flat: true
                                highlighted: modelData.name === page.selectedEntityClass
                                text: modelData.name + " (" + modelData.entity_count + ")"

                                onClicked: page.selectEntityClass(modelData.name)
                            }

                            RowMenu {
                                MenuItem {
                                    text: "Rename\u2026"
                                    onTriggered: page.askRename("entity_class", { "name": modelData.name }, modelData.name)
                                }

                                MenuItem {
                                    text: "Remove"
                                    onTriggered: page.askRemove("entity_class", { "name": modelData.name },
                                                                "entity class " + modelData.name)
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

                    RowLayout {
                        Layout.fillWidth: true
                        visible: page.selectedEntityClass !== ""
                        spacing: 8

                        Label {
                            Layout.fillWidth: true
                            text: "Parameter values \u2013 " + page.selectedEntityClass
                            font.bold: true
                            font.pixelSize: 14
                        }

                        Label {
                            text: "Alternative"
                            opacity: 0.6
                            font.pixelSize: 12
                        }

                        ComboBox {
                            model: page.pivot.alternatives
                            currentIndex: page.pivot.alternatives.indexOf(page.pivotAlternative)

                            onActivated: {
                                page.pivotAlternative = currentText
                                page.loadPivot()
                            }
                        }

                        Button {
                            text: "+ Entity"

                            onClicked: page.askAdd("New " + page.selectedEntityClass, "entity",
                                                   { "entity_class_name": page.selectedEntityClass })
                        }
                    }

                    ColumnLayout {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        visible: page.selectedEntityClass === ""
                        spacing: 6

                        Label {
                            Layout.alignment: Qt.AlignHCenter
                            text: "\u2190"
                            font.pixelSize: 36
                            color: "#2f6b4a"
                        }

                        Label {
                            Layout.alignment: Qt.AlignHCenter
                            text: page.databases.length === 0 ? "No database in this project"
                                                              : "Select an entity class to get started"
                            font.pixelSize: 18
                            font.bold: true
                            color: "#2f6b4a"
                        }

                        Label {
                            Layout.alignment: Qt.AlignHCenter
                            visible: page.databases.length > 0
                            text: "Pick one from the list on the left to see and edit its parameter values."
                            font.pixelSize: 12
                            opacity: 0.6
                        }

                        Item {
                            Layout.fillHeight: true
                        }
                    }

                    ListView {
                        id: pivotView

                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        visible: page.selectedEntityClass !== ""
                        clip: true
                        model: page.pivot.rows

                        flickableDirection: Flickable.HorizontalAndVerticalFlick
                        boundsBehavior: Flickable.StopAtBounds
                        contentWidth: 200 + page.pivot.parameters.length * 130
                        headerPositioning: ListView.OverlayHeader

                        ScrollBar.vertical: ScrollBar {}
                        ScrollBar.horizontal: ScrollBar {}

                        header: Rectangle {
                            z: 2
                            width: pivotView.contentWidth
                            height: 30
                            color: "#f8fafc"

                            Row {
                                Label {
                                    width: 200
                                    height: 30
                                    text: "Entity"
                                    font.bold: true
                                    font.pixelSize: 11
                                    opacity: 0.6
                                    verticalAlignment: Text.AlignVCenter
                                }

                                Repeater {
                                    model: page.pivot.parameters

                                    Label {
                                        width: 130
                                        height: 30
                                        text: modelData
                                        font.bold: true
                                        font.pixelSize: 11
                                        opacity: 0.6
                                        elide: Text.ElideRight
                                        verticalAlignment: Text.AlignVCenter
                                    }
                                }
                            }
                        }

                        delegate: Row {
                            id: pivotRow

                            property var rowData: modelData

                            height: 32

                            RowLayout {
                                width: 200
                                height: 32
                                spacing: 0

                                Label {
                                    Layout.fillWidth: true
                                    text: pivotRow.rowData.entity
                                    font.pixelSize: 12
                                    elide: Text.ElideRight
                                }

                                RowMenu {
                                    MenuItem {
                                        text: "Rename\u2026"
                                        onTriggered: page.askRename(
                                            "entity",
                                            { "entity_class_name": page.selectedEntityClass, "name": pivotRow.rowData.entity },
                                            pivotRow.rowData.entity)
                                    }

                                    MenuItem {
                                        text: "Remove"
                                        onTriggered: page.askRemove(
                                            "entity",
                                            { "entity_class_name": page.selectedEntityClass, "name": pivotRow.rowData.entity },
                                            "entity " + pivotRow.rowData.entity)
                                    }
                                }
                            }

                            Repeater {
                                model: pivotRow.rowData.cells

                                TextField {
                                    id: cellField

                                    property var cell: modelData

                                    width: 130
                                    height: 32
                                    text: cell.text
                                    readOnly: !cell.editable
                                    selectByMouse: true
                                    font.pixelSize: 12

                                    background: Rectangle {
                                        color: !cellField.cell.editable ? "#f1f5f9"
                                               : cellField.cell.empty ? "#ffffff" : "#f0fdf4"
                                        border.color: cellField.activeFocus ? "#2563eb" : "#e2e8f0"
                                    }

                                    ToolTip.visible: readOnly && hovered
                                    ToolTip.text: "This kind of value can't be edited here"

                                    onEditingFinished: {
                                        if (text !== cell.text)
                                            page.setCell(pivotRow.rowData.entity, page.pivot.parameters[index], text)
                                    }

                                    Keys.onEscapePressed: {
                                        text = cell.text
                                        focus = false
                                    }
                                }
                            }
                        }
                    }
                }
            }

            // -------------------------------------------------
            // RIGHT: alternatives and scenario tree
            // -------------------------------------------------

            Rectangle {
                Layout.preferredWidth: 190
                Layout.fillHeight: true

                radius: 10
                color: "#ffffff"
                border.color: "#e2e8f0"

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 14

                    spacing: 8

                    RowLayout {
                        Layout.fillWidth: true

                        Label {
                            Layout.fillWidth: true
                            text: "Alternatives"
                            font.bold: true
                            font.pixelSize: 12
                            opacity: 0.6
                        }

                        ToolButton {
                            text: "+"
                            enabled: page.selectedDatabaseUrl !== ""

                            ToolTip.visible: hovered
                            ToolTip.text: "Add alternative"

                            onClicked: page.askAdd("New alternative", "alternative", {})
                        }
                    }

                    Rectangle {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        Layout.preferredHeight: 110
                        radius: 6
                        color: "#f8fafc"
                        border.color: "#e2e8f0"

                        ListView {
                            anchors.fill: parent
                            anchors.margins: 6
                            clip: true
                            model: page.databaseContents.alternatives || []

                            ScrollBar.vertical: ScrollBar {}

                            delegate: RowLayout {
                                width: ListView.view.width
                                spacing: 0

                                Label {
                                    Layout.fillWidth: true
                                    text: modelData
                                    font.pixelSize: 12
                                    elide: Text.ElideRight
                                }

                                RowMenu {
                                    MenuItem {
                                        text: "Rename\u2026"
                                        onTriggered: page.askRename("alternative", { "name": modelData }, modelData)
                                    }

                                    MenuItem {
                                        text: "Remove"
                                        onTriggered: page.askRemove("alternative", { "name": modelData },
                                                                    "alternative " + modelData)
                                    }
                                }
                            }
                        }
                    }

                    RowLayout {
                        Layout.fillWidth: true

                        Label {
                            Layout.fillWidth: true
                            text: "Scenario tree"
                            font.bold: true
                            font.pixelSize: 12
                            opacity: 0.6
                        }

                        ToolButton {
                            text: "+"
                            enabled: page.selectedDatabaseUrl !== ""

                            ToolTip.visible: hovered
                            ToolTip.text: "Add scenario"

                            onClicked: page.askAdd("New scenario", "scenario", {})
                        }
                    }

                    Rectangle {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        Layout.preferredHeight: 180
                        radius: 6
                        color: "#f8fafc"
                        border.color: "#e2e8f0"

                        ListView {
                            anchors.fill: parent
                            anchors.margins: 6
                            clip: true
                            model: page.databaseContents.scenario_tree || []

                            ScrollBar.vertical: ScrollBar {}

                            delegate: ColumnLayout {
                                id: scenarioNode

                                property bool expanded: true
                                property string scenarioName: modelData.name
                                property int alternativeCount: modelData.alternatives.length

                                width: ListView.view.width
                                spacing: 2

                                RowLayout {
                                    Layout.fillWidth: true
                                    spacing: 4

                                    Label {
                                        Layout.preferredWidth: 14
                                        horizontalAlignment: Text.AlignHCenter
                                        opacity: 0.6
                                        text: modelData.alternatives.length === 0 ? ""
                                              : scenarioNode.expanded ? "\u25be" : "\u25b8"

                                        MouseArea {
                                            anchors.fill: parent
                                            onClicked: scenarioNode.expanded = !scenarioNode.expanded
                                        }
                                    }

                                    Label {
                                        Layout.fillWidth: true
                                        text: modelData.name
                                        font.bold: true
                                        font.pixelSize: 12
                                        elide: Text.ElideRight

                                        ToolTip.visible: scenarioHover.hovered && modelData.description !== ""
                                        ToolTip.text: modelData.description

                                        HoverHandler {
                                            id: scenarioHover
                                        }
                                    }

                                    RowMenu {
                                        MenuItem {
                                            text: "Add alternative\u2026"
                                            onTriggered: addAlternativeDialog.openFor(scenarioNode.scenarioName)
                                        }

                                        MenuItem {
                                            text: "Rename\u2026"
                                            onTriggered: page.askRename("scenario", { "name": scenarioNode.scenarioName },
                                                                        scenarioNode.scenarioName)
                                        }

                                        MenuItem {
                                            text: "Remove"
                                            onTriggered: page.askRemove("scenario", { "name": scenarioNode.scenarioName },
                                                                        "scenario " + scenarioNode.scenarioName)
                                        }
                                    }
                                }

                                Repeater {
                                    model: scenarioNode.expanded ? modelData.alternatives : []

                                    RowLayout {
                                        Layout.fillWidth: true
                                        spacing: 0

                                        Label {
                                            Layout.fillWidth: true
                                            text: modelData.name
                                            font.pixelSize: 12
                                            leftPadding: 22
                                            elide: Text.ElideRight

                                            ToolTip.visible: alternativeHover.hovered && modelData.description !== ""
                                            ToolTip.text: modelData.description

                                            HoverHandler {
                                                id: alternativeHover
                                            }
                                        }

                                        RowMenu {
                                            MenuItem {
                                                text: "Move up"
                                                enabled: index > 0
                                                onTriggered: page.moveScenarioAlternative(scenarioNode.scenarioName, index, -1)
                                            }

                                            MenuItem {
                                                text: "Move down"
                                                enabled: index < scenarioNode.alternativeCount - 1
                                                onTriggered: page.moveScenarioAlternative(scenarioNode.scenarioName, index, 1)
                                            }

                                            MenuItem {
                                                text: "Remove from scenario"
                                                onTriggered: page.removeScenarioAlternative(scenarioNode.scenarioName, index)
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}
