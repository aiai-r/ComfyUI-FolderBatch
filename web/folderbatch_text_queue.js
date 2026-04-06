import { app } from "/scripts/app.js";
import { findWidgetByName, sleep } from "./modules/utils.js";

const API_BASE_URL = "/folderbatch/text-queue/";
const HIDDEN_TAG = "folderbatch_hidden";

function setWidgetHidden(widget, hidden) {
    if (!widget) {
        return;
    }

    if (!widget[HIDDEN_TAG]) {
        widget[HIDDEN_TAG] = {
            computeSize: widget.computeSize,
            type: widget.type,
        };
    }

    if (hidden) {
        widget.computeSize = () => [0, -4];
        widget.type = "hidden";
    } else {
        widget.computeSize = widget[HIDDEN_TAG].computeSize;
        widget.type = widget[HIDDEN_TAG].type;
    }
}

class FolderBatchTextQueue {
    sourceModeWidget;
    unitModeWidget;
    folderWidget;
    textPathWidget;
    extensionWidget;
    startAtWidget;
    textCountWidget;
    autoQueueWidget;
    progressWidget;
    skipEmptyLinesWidget;
    textCount = 0;

    normalizeModes() {
        if (this.sourceModeWidget.value === "file" && this.unitModeWidget.value !== "line") {
            this.unitModeWidget.value = "line";
        }
    }

    refreshWidgetVisibility(node) {
        const isFileMode = this.sourceModeWidget.value === "file";
        const isLineMode = this.unitModeWidget.value === "line";

        setWidgetHidden(this.folderWidget, isFileMode);
        setWidgetHidden(this.textPathWidget, !isFileMode);
        setWidgetHidden(this.extensionWidget, isFileMode);
        setWidgetHidden(this.skipEmptyLinesWidget, !isLineMode);

        if (this.unitModeWidget) {
            this.unitModeWidget.disabled = isFileMode;
        }

        if (node?.computeSize) {
            const size = node.computeSize();
            node.setSize([
                Math.max(size[0], node.size[0]),
                Math.max(size[1], node.size[1]),
            ]);
        }
    }

    getTextCount() {
        return new Promise(async (resolve) => {
            this.normalizeModes();
            const sourceMode = encodeURIComponent(this.sourceModeWidget.value ?? "folder");
            const unitMode = encodeURIComponent(this.unitModeWidget.value ?? "file");
            const folder = encodeURIComponent(this.folderWidget.value ?? "");
            const textPath = encodeURIComponent(this.textPathWidget.value ?? "");
            const extension = encodeURIComponent(this.extensionWidget.value ?? "");
            const skipEmptyLines = encodeURIComponent(this.skipEmptyLinesWidget.value ?? true);
            const url = API_BASE_URL
                + `get_text_count?source_mode=${sourceMode}&unit_mode=${unitMode}&folder=${folder}`
                + `&text_path=${textPath}&extension=${extension}&skip_empty_lines=${skipEmptyLines}`;

            const response = await fetch(url);
            const data = await response.json();
            this.textCount = parseInt(data["text_count"]);
            resolve(this.textCount);
        });
    }

    refreshTextCount() {
        if (this.textCountWidget) {
            this.textCountWidget.value = this.textCount;
        }
    }

    refreshProgress(startAt) {
        if (this.progressWidget && this.textCount > 0) {
            this.progressWidget.value = (startAt + 1) / this.textCount;
        }
    }

    async onExecuted(textCount, startAt) {
        if (startAt + 1 < textCount) {
            this.startAtWidget.value = startAt + 1;
            this.refreshProgress(startAt);

            if (this.autoQueueWidget.value) {
                await sleep(200);
                app.queuePrompt(0, 1);
            }
        } else if (startAt + 1 >= textCount) {
            this.startAtWidget.value = 0;
            if (this.progressWidget) {
                this.progressWidget.value = 0;
            }
        }
    }

    initWidget(node, sourceModeWidget, unitModeWidget, folderWidget, textPathWidget, extensionWidget, startAtWidget, textCountWidget, autoQueueWidget, progressWidget, skipEmptyLinesWidget) {
        this.sourceModeWidget = sourceModeWidget;
        this.unitModeWidget = unitModeWidget;
        this.folderWidget = folderWidget;
        this.textPathWidget = textPathWidget;
        this.extensionWidget = extensionWidget;
        this.startAtWidget = startAtWidget;
        this.textCountWidget = textCountWidget;
        this.autoQueueWidget = autoQueueWidget;
        this.progressWidget = progressWidget;
        this.skipEmptyLinesWidget = skipEmptyLinesWidget;

        sourceModeWidget.callback = async () => {
            this.normalizeModes();
            this.refreshWidgetVisibility(node);
            await this.getTextCount();
            this.refreshTextCount();
        };
        unitModeWidget.callback = async () => {
            this.normalizeModes();
            this.refreshWidgetVisibility(node);
            await this.getTextCount();
            this.refreshTextCount();
        };
        folderWidget.callback = async () => {
            await this.getTextCount();
            this.refreshTextCount();
        };
        textPathWidget.callback = async () => {
            await this.getTextCount();
            this.refreshTextCount();
        };
        extensionWidget.callback = async () => {
            await this.getTextCount();
            this.refreshTextCount();
        };
        skipEmptyLinesWidget.callback = async () => {
            await this.getTextCount();
            this.refreshTextCount();
        };

        setTimeout(async () => {
            this.normalizeModes();
            this.refreshWidgetVisibility(node);
            await this.getTextCount();
            this.refreshTextCount();
        }, 100);
    }
}

app.registerExtension({
    name: "Comfy.FolderBatch.FolderBatchTextQueue",

    async beforeRegisterNodeDef(nodeType, nodeData) {
        if (nodeData.name !== "FolderBatch Text Queue") return;

        const folderTextQueue = new FolderBatchTextQueue();

        const origOnNodeCreated = nodeType.prototype.onNodeCreated;
        nodeType.prototype.onNodeCreated = function () {
            const r = origOnNodeCreated ? origOnNodeCreated.apply(this) : undefined;

            const sourceModeWidget = findWidgetByName(this, "source_mode");
            const unitModeWidget = findWidgetByName(this, "unit_mode");
            const folderWidget = findWidgetByName(this, "folder");
            const textPathWidget = findWidgetByName(this, "text_path");
            const extensionWidget = findWidgetByName(this, "extension");
            const startAtWidget = findWidgetByName(this, "start_at");
            const autoQueueWidget = findWidgetByName(this, "auto_queue");
            const textCountWidget = findWidgetByName(this, "text_count");
            const progressWidget = findWidgetByName(this, "progress");
            const skipEmptyLinesWidget = findWidgetByName(this, "skip_empty_lines");

            folderTextQueue.initWidget(
                this,
                sourceModeWidget,
                unitModeWidget,
                folderWidget,
                textPathWidget,
                extensionWidget,
                startAtWidget,
                textCountWidget,
                autoQueueWidget,
                progressWidget,
                skipEmptyLinesWidget
            );

            return r;
        };

        const onExecuted = nodeType.prototype.onExecuted;
        nodeType.prototype.onExecuted = async function (message) {
            onExecuted?.apply(this, arguments);

            const textCount = message["text_count"][0];
            const startAt = message["start_at"][0];
            folderTextQueue.onExecuted(textCount, startAt);
        };
    },
});
