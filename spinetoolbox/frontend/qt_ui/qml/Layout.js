.pragma library

// User Mode card layout: starts from the dev mode (Design View) positions, then straightens near-linear
// chains and shrinks links that are too long without changing the order of the cards.

var CARD_WIDTH = 150
var CARD_HEIGHT = 74
var DEV_SCALE = 1.5
var SEPARATION_X = CARD_WIDTH + 30
var SEPARATION_Y = CARD_HEIGHT + 30
var MAX_LINK_X = 1.5 * SEPARATION_X
var MAX_LINK_Y = 1.5 * SEPARATION_Y
var SNAP_TOLERANCE = 0.6 * CARD_HEIGHT
var PADDING = 60

// links whose cards are nearly level are put on one line; a group never spans more than the tolerance
function snapChains(count, links, positions) {
    var parent = []
    var low = []
    var high = []
    for (var i = 0; i < count; i++) {
        parent[i] = i
        low[i] = positions[i]
        high[i] = positions[i]
    }
    function find(index) {
        while (parent[index] !== index) {
            parent[index] = parent[parent[index]]
            index = parent[index]
        }
        return index
    }
    links.sort(function (a, b) {
        return Math.abs(positions[a[0]] - positions[a[1]]) - Math.abs(positions[b[0]] - positions[b[1]])
    })
    for (var l = 0; l < links.length; l++) {
        var first = find(links[l][0])
        var second = find(links[l][1])
        if (first === second)
            continue
        var newLow = Math.min(low[first], low[second])
        var newHigh = Math.max(high[first], high[second])
        if (newHigh - newLow > SNAP_TOLERANCE)
            continue
        parent[first] = second
        low[second] = newLow
        high[second] = newHigh
    }
    var sums = ({})
    var sizes = ({})
    for (var j = 0; j < count; j++) {
        var root = find(j)
        sums[root] = (sums[root] || 0) + positions[j]
        sizes[root] = (sizes[root] || 0) + 1
    }
    for (var k = 0; k < count; k++) {
        var group = find(k)
        positions[k] = sums[group] / sizes[group]
    }
}

// pushes overlapping cards apart along the axis needing the smaller move
function separateCards(x, y) {
    for (var pass = 0; pass < 50; pass++) {
        var moved = false
        for (var i = 0; i < x.length; i++) {
            for (var j = i + 1; j < x.length; j++) {
                var overlapX = SEPARATION_X - Math.abs(x[i] - x[j])
                var overlapY = SEPARATION_Y - Math.abs(y[i] - y[j])
                if (overlapX <= 0 || overlapY <= 0)
                    continue
                if (overlapX / SEPARATION_X < overlapY / SEPARATION_Y) {
                    if (x[j] >= x[i])
                        x[j] += overlapX
                    else
                        x[i] += overlapX
                } else if (y[j] >= y[i]) {
                    y[j] += overlapY
                } else {
                    y[i] += overlapY
                }
                moved = true
            }
        }
        if (!moved)
            break
    }
}

// Moves the cards after a cut along axis a towards the cards before it while a link across the cut is longer
// than maxDistance. Cards that share a row (closer than separationB on the other axis b) keep separationA.
function shrinkLongLinks(a, b, links, separationA, separationB, maxDistance) {
    var order = []
    for (var i = 0; i < a.length; i++)
        order.push(i)
    order.sort(function (p, q) { return a[p] - a[q] })
    var rank = []
    for (var r = 0; r < order.length; r++)
        rank[order[r]] = r

    for (var cut = 1; cut < order.length; cut++) {
        var gap = a[order[cut]] - a[order[cut - 1]]
        if (gap <= 0)
            continue
        var longest = 0
        for (var l = 0; l < links.length; l++) {
            if ((rank[links[l][0]] < cut) !== (rank[links[l][1]] < cut))
                longest = Math.max(longest, Math.abs(a[links[l][0]] - a[links[l][1]]))
        }
        var shift = Math.min(longest - maxDistance, gap)
        if (shift <= 0)
            continue
        for (var before = 0; before < cut; before++) {
            for (var after = cut; after < order.length; after++) {
                var p = order[before]
                var q = order[after]
                if (Math.abs(b[p] - b[q]) < separationB)
                    shift = Math.min(shift, a[q] - a[p] - separationA)
            }
        }
        if (shift <= 0)
            continue
        for (var moved = cut; moved < order.length; moved++)
            a[order[moved]] -= shift
    }
}

// A link leaving a card's bottom and entering a side of the target needs the target beside the source,
// as there is no top connection point to enter from above.
function keepSideEntry(sideLinks, x) {
    var minimum = 0.75 * CARD_WIDTH
    for (var i = 0; i < sideLinks.length; i++) {
        var source = sideLinks[i][0]
        var target = sideLinks[i][1]
        if (sideLinks[i][2] === "left")
            x[target] = Math.max(x[target], x[source] + minimum)
        else
            x[target] = Math.min(x[target], x[source] - minimum)
    }
}

// sets items[].px/py; items need dev mode x/y. compactRows allows shrinking vertical distances, which is
// only wanted when stacks or hidden items have left gaps. Returns the size of the laid out area.
function layoutWorkflow(items, connections, defaultSize, compactRows) {
    if (items.length === 0)
        return defaultSize

    var itemIndex = ({})
    var x = []
    var y = []
    for (var i = 0; i < items.length; i++) {
        itemIndex[items[i].name] = i
        x.push((items[i].x || 0) * DEV_SCALE)
        y.push((items[i].y || 0) * DEV_SCALE)
    }

    var rowLinks = []
    var sideLinks = []
    var allLinks = []
    for (var d = 0; d < connections.length; d++) {
        var link = connections[d]
        var source = itemIndex[link.from]
        var target = itemIndex[link.to]
        if (source === undefined || target === undefined || source === target)
            continue
        allLinks.push([source, target])
        var toSide = link.to_anchor || "left"
        if ((link.from_anchor || "right") === "bottom") {
            if (toSide === "left" || toSide === "right")
                sideLinks.push([source, target, toSide])
        } else if (toSide === "left") {
            rowLinks.push([source, target])
        }
    }
    snapChains(items.length, rowLinks, y)

    keepSideEntry(sideLinks, x)
    separateCards(x, y)
    keepSideEntry(sideLinks, x)
    shrinkLongLinks(x, y, allLinks, SEPARATION_X, SEPARATION_Y, MAX_LINK_X)
    if (compactRows)
        shrinkLongLinks(y, x, allLinks, SEPARATION_Y, SEPARATION_X, MAX_LINK_Y)
    // shrinking moves whole columns, which can pull a target back under its source
    keepSideEntry(sideLinks, x)
    separateCards(x, y)

    var left = Math.min.apply(null, x)
    var right = Math.max.apply(null, x)
    var top = Math.min.apply(null, y)
    var bottom = Math.max.apply(null, y)
    for (var k = 0; k < items.length; k++) {
        items[k].px = PADDING + x[k] - left
        items[k].py = PADDING + y[k] - top
    }
    return {
        width: PADDING * 2 + (right - left) + CARD_WIDTH,
        height: PADDING * 2 + (bottom - top) + CARD_HEIGHT
    }
}
