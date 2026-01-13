import { app } from "/scripts/app.js";
import { findWidgetByName, sleep } from "./modules/utils.js";

const API_BASE_URL = "/folderbatch/video-queue/";

class FolderBatchVideoQueue {
    folderWidget;
    extensionWidget;
    startAtWidget;
    videoCountWidget;
    autoQueueWidget;
    progressWidget;
    videoCount = 0;

    getVideoCount() {
        return new Promise(async (resolve) => {
            const folder = this.folderWidget.value;
            const extension = this.extensionWidget.value;
            const url = API_BASE_URL + `get_video_count?folder=${folder}&extension=${extension}`;

            const response = await fetch(url);
            const data = await response.json();
            this.videoCount = parseInt(data["video_count"]);
            resolve(this.videoCount);
        });
    }

    refreshVideoCount() {
        if (this.videoCountWidget) {
            this.videoCountWidget.value = this.videoCount;
        }
    }

    refreshProgress(startAt) {
        if (this.progressWidget && this.videoCount > 0) {
            this.progressWidget.value = (startAt + 1) / this.videoCount;
        }
    }

    async onExecuted(videoCount, startAt) {
        if (startAt + 1 < videoCount) {
            this.startAtWidget.value = startAt + 1;
            this.refreshProgress(startAt);

            if (this.autoQueueWidget.value) {
                await sleep(200);
                app.queuePrompt(0, 1);
            }
        } else if (startAt + 1 >= videoCount) {
            this.startAtWidget.value = 0;
            if (this.progressWidget) {
                this.progressWidget.value = 0;
            }
        }
    }

    initWidget(folderWidget, extensionWidget, startAtWidget, videoCountWidget, autoQueueWidget, progressWidget) {
        this.folderWidget = folderWidget;
        this.extensionWidget = extensionWidget;
        this.startAtWidget = startAtWidget;
        this.videoCountWidget = videoCountWidget;
        this.autoQueueWidget = autoQueueWidget;
        this.progressWidget = progressWidget;

        folderWidget.callback = async () => {
            await this.getVideoCount();
            this.refreshVideoCount();
        };
        extensionWidget.callback = async () => {
            await this.getVideoCount();
            this.refreshVideoCount();
        };

        setTimeout(async () => {
            await this.getVideoCount();
            this.refreshVideoCount();
        }, 100);
    }
}

app.registerExtension({
    name: "Comfy.FolderBatch.FolderBatchVideoQueue",

    async beforeRegisterNodeDef(nodeType, nodeData) {
        if (nodeData.name !== "FolderBatch Video Queue") return;

        const folderVideoQueue = new FolderBatchVideoQueue();

        const origOnNodeCreated = nodeType.prototype.onNodeCreated;
        nodeType.prototype.onNodeCreated = function () {
            const r = origOnNodeCreated ? origOnNodeCreated.apply(this) : undefined;

            const folderWidget = findWidgetByName(this, "folder");
            const extensionWidget = findWidgetByName(this, "extension");
            const startAtWidget = findWidgetByName(this, "start_at");
            const autoQueueWidget = findWidgetByName(this, "auto_queue");
            const videoCountWidget = findWidgetByName(this, "video_count");
            const progressWidget = findWidgetByName(this, "progress");

            folderVideoQueue.initWidget(
                folderWidget,
                extensionWidget,
                startAtWidget,
                videoCountWidget,
                autoQueueWidget,
                progressWidget
            );

            return r;
        };

        const onExecuted = nodeType.prototype.onExecuted;
        nodeType.prototype.onExecuted = async function (message) {
            onExecuted?.apply(this, arguments);

            const videoCount = message["video_count"][0];
            const startAt = message["start_at"][0];
            folderVideoQueue.onExecuted(videoCount, startAt);
        };
    },
});
