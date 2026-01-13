export function findWidgetByName(node, name) {
    if (!node || !node.widgets) {
        return null;
    }
    return node.widgets.find((w) => w.name === name);
}

export function sleep(ms) {
    return new Promise((resolve) => setTimeout(resolve, ms));
}
