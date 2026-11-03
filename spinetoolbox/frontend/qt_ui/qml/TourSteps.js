// Text of the first-run tour. Steps whose target is missing (e.g. no filter badge in the project) are left out.
// instructions is a list of {name, text} written by the workflow author; each gets a step on its item's box.
function buildSteps(targets, instructions, nodeItems) {
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
        }
    ]

    var authored = (instructions || []).map(function (instruction) {
        return {target: nodeItems[instruction.name], title: instruction.name, text: instruction.text}
    })

    var closing = [
        {
            target: targets.runButton,
            title: qsTr("Run the project"),
            text: qsTr("Run the whole workflow, or select some boxes first to run only those. "
                       + "While a run is in progress, the same button stops it.")
        },
        {
            target: targets.help,
            title: qsTr("Need this again?"),
            text: qsTr("Click Help to replay this tour.")
        }
    ]

    return [welcome].concat(targeted, authored, closing).filter(function (step) { return step === welcome || !!step.target })
}
