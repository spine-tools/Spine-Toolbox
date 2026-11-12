// Text of the first-run tour. Steps whose target is missing (e.g. no filter badge in the project) are left out.
// instructions is a list of {name, text} written by the workflow author; each gets a step on its item's box.
function buildSteps(hasProject, targets, instructions, nodeItems) {
    var welcome = {
        target: null,
        title: qsTr("Welcome to User Mode"),
        text: hasProject
            ? qsTr("This tour shows the main controls of SpineToolBox and the workflow of this project. "
                   + "You can replay the tour from Help at any time.")
            : qsTr("This tour uses an example project to show the main controls of SpineToolBox. "
                   + "Open a project to get a tour of its own workflow.")
    }

    if (!hasProject) {
        return [
            welcome,
            {
                target: targets.canvas,
                title: qsTr("Your workflow"),
                text: qsTr("In an example project, boxes are items such as a Data Store, an Importer and a Tool. "
                           + "Lines show how data flows from one item to the next.")
            },
            {
                target: targets.runButton,
                title: qsTr("Run the project"),
                text: qsTr("Run the whole workflow, or select some items first to run only those.")
            },
            {
                target: targets.help,
                title: qsTr("Need this again?"),
                text: qsTr("Click Help to replay this tour. With a project open it explains that project's workflow.")
            }
        ].filter(function (step) { return step === welcome || !!step.target })
    }

    var targeted = [
        {
            target: targets.canvas,
            title: qsTr("Your workflow"),
            text: qsTr("Boxes are items of the project and lines show how data flows between them. "
                       + "Use the zoom buttons or mouse wheel to change the size.")
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
            text: qsTr("Run the whole workflow, or select some items first to run only those. "
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
