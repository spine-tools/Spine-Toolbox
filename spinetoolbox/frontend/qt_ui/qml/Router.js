.pragma library

// Connector geometry for the user mode canvas: lines leave and enter a card straight out of its side, with a
// diagonal between, as in dev mode.

var STUB = 15

// outward direction of a card side
function sideDirection(side) {
    switch (side) {
    case "left": return { x: -1, y: 0 }
    case "bottom": return { x: 0, y: 1 }
    default: return { x: 1, y: 0 }
    }
}

// point in the middle of a card's side; all lines on a side share it
function edgePoint(card, side) {
    switch (side) {
    case "left": return { x: card.x, y: card.y + card.height / 2 }
    case "bottom": return { x: card.x + card.width / 2, y: card.y + card.height }
    default: return { x: card.x + card.width, y: card.y + card.height / 2 }
    }
}

// cards: name -> {x, y, width, height}; connections: [{from, to, from_anchor, to_anchor}].
// Returns "from|to" -> {path, anchor, line, arrow}: line/arrow are SVG path strings in the same coordinates.
function routeAll(cards, connections, scale) {
    var routes = {}
    for (var i = 0; i < connections.length; i++) {
        var fromCard = cards[connections[i].from]
        var toCard = cards[connections[i].to]
        if (!fromCard || !toCard)
            continue
        var fromSide = connections[i].from_anchor || "right"
        var toSide = connections[i].to_anchor || "left"
        var start = edgePoint(fromCard, fromSide)
        var end = edgePoint(toCard, toSide)
        var out = sideDirection(fromSide)
        var inward = sideDirection(toSide)
        // the same stub length on every line, so lines sharing a side run together up to the card
        var stub = STUB * scale
        var startOut = { x: start.x + out.x * stub, y: start.y + out.y * stub }
        var endOut = { x: end.x + inward.x * stub, y: end.y + inward.y * stub }
        routes[connections[i].from + "|" + connections[i].to] = {
            path: [start, startOut, endOut, end],
            anchor: { x: (startOut.x + endOut.x) / 2, y: (startOut.y + endOut.y) / 2 },
            line: "M " + start.x + " " + start.y + " L " + startOut.x + " " + startOut.y
                  + " L " + endOut.x + " " + endOut.y + " L " + end.x + " " + end.y,
            arrow: arrowSvg(endOut, end, 11 * scale)
        }
    }
    return routes
}

// triangle at the end of the line pointing along it
function arrowSvg(start, end, size) {
    var length = Math.hypot(end.x - start.x, end.y - start.y)
    if (length === 0)
        return ""
    var dx = (end.x - start.x) / length
    var dy = (end.y - start.y) / length
    return "M " + end.x + " " + end.y
            + " L " + (end.x - dx * size - dy * size / 2) + " " + (end.y - dy * size + dx * size / 2)
            + " L " + (end.x - dx * size + dy * size / 2) + " " + (end.y - dy * size - dx * size / 2) + " Z"
}
