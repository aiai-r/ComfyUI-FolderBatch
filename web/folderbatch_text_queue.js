import { app } from "/scripts/app.js";
import { findWidgetByName, sleep } from "./modules/utils.js";

const API_BASE_URL = "/folderbatch/text-queue/";

class FolderBatchTextQueue {
    folderWidget;
    extensionWidget;
    startAtWidget;
    textCountWidget;
    autoQueueWidget;
    progressWidget;
    textCount = 0;

    getTextCount() {
        return new Promise(async (resolve) => {
            const folder = this.folderWidget.value;
            const extension = this.extensionWidget.value;
            const url = API_BASE_URL + `get_text_count?folder=${folder}&extension=${extension}`;

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

    initWidget(folderWidget, extensionWidget, startAtWidget, textCountWidget, autoQueueWidget, progressWidget) {
        this.folderWidget = folderWidget;
        this.extensionWidget = extensionWidget;
        this.startAtWidget = startAtWidget;
        this.textCountWidget = textCountWidget;
        this.autoQueueWidget = autoQueueWidget;
        this.progressWidget = progressWidget;

        folderWidget.callback = async () => {
            await this.getTextCount();
            this.refreshTextCount();
        };
        extensionWidget.callback = async () => {
            await this.getTextCount();
            this.refreshTextCount();
        };

        setTimeout(async () => {
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

            const folderWidget = findWidgetByName(this, "folder");
            const extensionWidget = findWidgetByName(this, "extension");
            const startAtWidget = findWidgetByName(this, "start_at");
            const autoQueueWidget = findWidgetByName(this, "auto_queue");
            const textCountWidget = findWidgetByName(this, "text_count");
            const progressWidget = findWidgetByName(this, "progress");

            folderTextQueue.initWidget(
                folderWidget,
                extensionWidget,
                startAtWidget,
                textCountWidget,
                autoQueueWidget,
                progressWidget
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
