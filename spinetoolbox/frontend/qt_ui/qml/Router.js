.pragma library

// Orthogonal connector routing for the user mode canvas. All connections are routed in one pass over a
// shared grid (every card's padded outline plus every connector stub contributes grid lines), with
// obstacles precomputed once, so the per-connection search is a small A* over typed arrays.

var EPS = 0.01

// search state kept between calls so repeated routing (e.g. while dragging) doesn't reallocate
var capacity = 0
var cost = null
var previous = null
var seen = null
var closed = null
var generation = 0
var heapKeys = []
var heapStates = []
var heapSize = 0

var DX = [1, -1, 0, 0]  // right, left, down, up; direction ^ 1 is the opposite direction
var DY = [0, 0, 1, -1]

function heapPush(key, state) {
    var index = heapSize++
    while (index > 0) {
        var parent = (index - 1) >> 1
        if (heapKeys[parent] <= key)
            break
        heapKeys[index] = heapKeys[parent]
        heapStates[index] = heapStates[parent]
        index = parent
    }
    heapKeys[index] = key
    heapStates[index] = state
}

// removes the smallest entry; its key and state are left in heapTopKey/heapTopState
var heapTopKey = 0
var heapTopState = 0

function heapPop() {
    heapTopKey = heapKeys[0]
    heapTopState = heapStates[0]
    heapSize--
    if (heapSize === 0)
        return
    var key = heapKeys[heapSize]
    var state = heapStates[heapSize]
    var index = 0
    while (true) {
        var child = 2 * index + 1
        if (child >= heapSize)
            break
        if (child + 1 < heapSize && heapKeys[child + 1] < heapKeys[child])
            child++
        if (heapKeys[child] >= key)
            break
        heapKeys[index] = heapKeys[child]
        heapStates[index] = heapStates[child]
        index = child
    }
    heapKeys[index] = key
    heapStates[index] = state
}

function uniqueSorted(values) {
    values.sort(function(a, b) { return a - b })
    var result = []
    for (var i = 0; i < values.length; i++) {
        if (i === 0 || values[i] - result[result.length - 1] > EPS)
            result.push(values[i])
    }
    return result
}

function indexOfValue(sorted, value) {
    var low = 0
    var high = sorted.length - 1
    while (low <= high) {
        var mid = (low + high) >> 1
        if (Math.abs(sorted[mid] - value) <= EPS)
            return mid
        if (sorted[mid] < value)
            low = mid + 1
        else
            high = mid - 1
    }
    return -1
}

// point on a card's side at the given 0..1 fraction along it, plus the side's outward direction
function edgePoint(card, side, fraction) {
    switch (side) {
    case "left": return { x: card.x, y: card.y + card.height * fraction, dx: -1, dy: 0 }
    case "top": return { x: card.x + card.width * fraction, y: card.y, dx: 0, dy: -1 }
    case "bottom": return { x: card.x + card.width * fraction, y: card.y + card.height, dx: 0, dy: 1 }
    default: return { x: card.x + card.width, y: card.y + card.height * fraction, dx: 1, dy: 0 }
    }
}

function directionIndex(dx, dy) {
    return dx > 0 ? 0 : dx < 0 ? 1 : dy > 0 ? 2 : 3
}

// Attachment points: connections sharing a card side get evenly spread slots ordered by the other card's
// position along that side, so their lines don't cross.
function describeEndpoints(cards, connections) {
    var groups = {}
    var endpoints = []
    for (var i = 0; i < connections.length; i++) {
        var connection = connections[i]
        var fromCard = cards[connection.from]
        var toCard = cards[connection.to]
        if (!fromCard || !toCard) {
            endpoints.push(null)
            continue
        }
        var fromSide = connection.from_anchor || "right"
        var toSide = connection.to_anchor || "left"
        endpoints.push({ fromSide: fromSide, toSide: toSide, fromCard: fromCard, toCard: toCard,
                         fromFraction: 0.5, toFraction: 0.5 })
        var ends = [[connection.from, fromSide, toCard, 0], [connection.to, toSide, fromCard, 1]]
        for (var e = 0; e < 2; e++) {
            var vertical = ends[e][1] === "left" || ends[e][1] === "right"
            var other = ends[e][2]
            var key = ends[e][0] + "|" + ends[e][1]
            if (!groups[key])
                groups[key] = []
            groups[key].push({
                index: i, end: ends[e][3],
                position: vertical ? other.y + other.height / 2 : other.x + other.width / 2
            })
        }
    }
    for (var groupKey in groups) {
        var group = groups[groupKey]
        group.sort(function(a, b) { return a.position - b.position || a.index - b.index })
        for (var g = 0; g < group.length; g++) {
            var fraction = (g + 1) / (group.length + 1)
            if (group[g].end === 0)
                endpoints[group[g].index].fromFraction = fraction
            else
                endpoints[group[g].index].toFraction = fraction
        }
    }
    return endpoints
}

// midpoint of the longest straight stretch of a path, so a filter badge sits on a straight part
function pathAnchor(path) {
    var bestLength = -1
    var anchor = { x: 0, y: 0 }
    for (var j = 1; j < path.length; j++) {
        var length = Math.abs(path[j].x - path[j - 1].x) + Math.abs(path[j].y - path[j - 1].y)
        if (length > bestLength) {
            bestLength = length
            anchor = { x: (path[j].x + path[j - 1].x) / 2, y: (path[j].y + path[j - 1].y) / 2 }
        }
    }
    return anchor
}

// cards: name -> {x, y, width, height}; connections: [{from, to, from_anchor, to_anchor}].
// Returns "from|to" -> {path: [{x, y}, ...], anchor: {x, y}}.
function routeAll(cards, connections, scale) {
    var padding = 14 * scale
    var stub = 24 * scale
    var turnCost = 40 * scale
    var endpoints = describeEndpoints(cards, connections)

    var boxes = []
    var xValues = []
    var yValues = []
    for (var name in cards) {
        var card = cards[name]
        var box = { l: card.x - padding, r: card.x + card.width + padding,
                    t: card.y - padding, b: card.y + card.height + padding }
        boxes.push(box)
        xValues.push(box.l, box.r)
        yValues.push(box.t, box.b)
    }

    var plans = []
    for (var i = 0; i < connections.length; i++) {
        var info = endpoints[i]
        if (!info) {
            plans.push(null)
            continue
        }
        var start = edgePoint(info.fromCard, info.fromSide, info.fromFraction)
        var end = edgePoint(info.toCard, info.toSide, info.toFraction)
        var startOut = { x: start.x + start.dx * stub, y: start.y + start.dy * stub }
        var endOut = { x: end.x + end.dx * stub, y: end.y + end.dy * stub }
        xValues.push(startOut.x, endOut.x)
        yValues.push(startOut.y, endOut.y)
        plans.push({ start: start, end: end, startOut: startOut, endOut: endOut })
    }

    var xs = uniqueSorted(xValues)
    var ys = uniqueSorted(yValues)
    var width = xs.length
    var height = ys.length

    var nodeBlocked = new Uint8Array(width * height)
    var hBlocked = new Uint8Array(Math.max(1, (width - 1) * height))  // edge (x, y) -> (x + 1, y)
    var vBlocked = new Uint8Array(Math.max(1, width * (height - 1)))  // edge (x, y) -> (x, y + 1)
    for (var b = 0; b < boxes.length; b++) {
        var li = indexOfValue(xs, boxes[b].l)
        var ri = indexOfValue(xs, boxes[b].r)
        var ti = indexOfValue(ys, boxes[b].t)
        var bi = indexOfValue(ys, boxes[b].b)
        for (var yi = ti + 1; yi < bi; yi++) {
            for (var xi = li + 1; xi < ri; xi++)
                nodeBlocked[yi * width + xi] = 1
            for (var hx = li; hx < ri; hx++)
                hBlocked[yi * (width - 1) + hx] = 1
        }
        for (var vy = ti; vy < bi; vy++) {
            for (var vx = li + 1; vx < ri; vx++)
                vBlocked[vy * width + vx] = 1
        }
    }

    var stateCount = width * height * 4
    if (capacity < stateCount) {
        capacity = stateCount
        cost = new Float64Array(capacity)
        previous = new Int32Array(capacity)
        seen = new Int32Array(capacity)
        closed = new Int32Array(capacity)
    }

    var routes = {}
    for (var c = 0; c < connections.length; c++) {
        var plan = plans[c]
        if (!plan)
            continue
        var path = routeOne(plan, xs, ys, width, height, nodeBlocked, hBlocked, vBlocked, turnCost)
        routes[connections[c].from + "|" + connections[c].to] = { path: path, anchor: pathAnchor(path) }
    }
    return routes
}

function routeOne(plan, xs, ys, width, height, nodeBlocked, hBlocked, vBlocked, turnCost) {
    generation++
    var startDirection = directionIndex(plan.start.dx, plan.start.dy)
    // heading with which the line enters the target card
    var endDirection = directionIndex(-plan.end.dx, -plan.end.dy)
    var startNode = indexOfValue(ys, plan.startOut.y) * width + indexOfValue(xs, plan.startOut.x)
    var goalX = indexOfValue(xs, plan.endOut.x)
    var goalY = indexOfValue(ys, plan.endOut.y)
    var goalNode = goalY * width + goalX
    var goalXValue = xs[goalX]
    var goalYValue = ys[goalY]

    var startState = startNode * 4 + startDirection
    seen[startState] = generation
    cost[startState] = 0
    previous[startState] = -1
    heapSize = 0
    heapPush(Math.abs(xs[startNode % width] - goalXValue) + Math.abs(ys[(startNode / width) | 0] - goalYValue),
             startState)

    var best = -1
    var bestCost = Infinity
    while (heapSize > 0) {
        heapPop()
        var state = heapTopState
        if (heapTopKey >= bestCost)
            break
        if (closed[state] === generation)
            continue
        closed[state] = generation

        var spent = cost[state]
        var heading = state & 3
        var node = state >> 2
        if (node === goalNode) {
            var total = spent + (heading === endDirection ? 0 : turnCost)
            if (total < bestCost) {
                bestCost = total
                best = state
            }
            continue
        }

        var cy = (node / width) | 0
        var cx = node - cy * width
        for (var d = 0; d < 4; d++) {
            if (d === (heading ^ 1))
                continue
            var nx = cx + DX[d]
            var ny = cy + DY[d]
            if (nx < 0 || ny < 0 || nx >= width || ny >= height)
                continue
            if (d < 2) {
                if (hBlocked[cy * (width - 1) + (d === 0 ? cx : nx)] === 1)
                    continue
            } else if (vBlocked[(d === 2 ? cy : ny) * width + cx] === 1) {
                continue
            }
            var nextNode = ny * width + nx
            if (nodeBlocked[nextNode] === 1)
                continue
            var next = nextNode * 4 + d
            if (closed[next] === generation)
                continue
            var nextCost = spent + Math.abs(xs[nx] - xs[cx]) + Math.abs(ys[ny] - ys[cy]) + (d === heading ? 0 : turnCost)
            if (seen[next] !== generation || nextCost < cost[next]) {
                seen[next] = generation
                cost[next] = nextCost
                previous[next] = state
                heapPush(nextCost + Math.abs(xs[nx] - goalXValue) + Math.abs(ys[ny] - goalYValue), next)
            }
        }
    }

    var points = [{ x: plan.end.x, y: plan.end.y }]
    if (best < 0) {
        points.push({ x: plan.endOut.x, y: plan.endOut.y }, { x: plan.startOut.x, y: plan.endOut.y },
                    { x: plan.startOut.x, y: plan.startOut.y })
    } else {
        for (var step = best; step >= 0; step = previous[step]) {
            var stepNode = step >> 2
            var sy = (stepNode / width) | 0
            points.push({ x: xs[stepNode - sy * width], y: ys[sy] })
        }
    }
    points.push({ x: plan.start.x, y: plan.start.y })
    points.reverse()

    // drop points that don't change direction
    var path = [points[0]]
    for (var p = 1; p < points.length - 1; p++) {
        var before = path[path.length - 1]
        var after = points[p + 1]
        var straight = (Math.abs(before.x - points[p].x) < EPS && Math.abs(points[p].x - after.x) < EPS)
                || (Math.abs(before.y - points[p].y) < EPS && Math.abs(points[p].y - after.y) < EPS)
        if (!straight)
            path.push(points[p])
    }
    path.push(points[points.length - 1])
    return path
}
