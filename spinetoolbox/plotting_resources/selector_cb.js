const indices = source.selected.indices;
if (indices.length === 0) {
    return;
}
const idx = indices[0];
var row = {};
for (const key in source.data) {
    row[key] = source.data[key][idx];
}

// NOTE: read column order from (future) order widget like the line below:
// const order = column_order.value;
// then pass `JSON.stringify(order)` to the bridge.

if (window.bridge) {
    window.bridge.refreshPlot(JSON.stringify(row));
} else {
    alert("QWebChannel bridge not available");
    console.error("QWebChannel bridge not available");
}
