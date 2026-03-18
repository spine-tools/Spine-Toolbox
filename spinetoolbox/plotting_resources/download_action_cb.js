var visibleKeys = [];
if (typeof legend !== 'undefined' && legend != null) {
    for (var i = 0; i < legend.items.length; i++) {
        var item = legend.items[i];
        if (item.renderers[0].visible) {
            visibleKeys.push(item.label.value);
        }
    }
} else {
    visibleKeys.push("ALL");
}
if (window.bridge) {
    window.bridge.downloadFilteredCsv(JSON.stringify(visibleKeys));
} else {
    alert("QWebChannel bridge not available");
    console.error("QWebChannel bridge not available");
}
