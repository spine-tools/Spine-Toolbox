// Text of the first-run tour. Steps whose target is missing (e.g. no filter badge in the project) are left out.
function buildSteps(targets) {
    var welcome = {
        target: null,
        title: qsTr("Welcome to User Mode"),
        text: qsTr("This tour shows the main controls and changes nothing. "
                   + "If no project is open, a bundled example is shown. You can replay the tour from Help at any time.")
    }

    var targeted = [
        {
            target: targets.openProject,
            title: qsTr("Open a project"),
            text: qsTr("Choose a folder that contains a .spinetoolbox project.")
        },
        {
            target: targets.canvas,
            title: qsTr("Your workflow"),
            text: qsTr("Boxes are the steps of the project and lines show how data flows between them. "
                       + "A stack is a group of steps shown as one box. Use the zoom buttons to change the size.")
        },
        {
            target: targets.filterBadge,
            title: qsTr("Choose scenarios"),
            text: qsTr("The S and A badges on a line choose which scenarios or alternatives are used. "
                       + "Click a badge to select them. A red ! means at least one must be selected before you run.")
        },
        {
            target: targets.runButton,
            title: qsTr("Run the project"),
            text: qsTr("Run the whole workflow, or select some boxes first to run only those. "
                       + "While a run is in progress, the same button stops it.")
        },
        {
            target: targets.runsNav,
            title: qsTr("Follow the run"),
            text: qsTr("The Runs page shows the log of the latest run.")
        },
        {
            target: targets.help,
            title: qsTr("Need this again?"),
            text: qsTr("Click Help to replay this tour.")
        }
    ]

    return [welcome].concat(targeted.filter(function (step) { return !!step.target }))
}
