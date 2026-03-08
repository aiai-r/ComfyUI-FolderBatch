import { app } from "/scripts/app.js";
import { findWidgetByName, sleep } from "./modules/utils.js";

const API_BASE_URL = "/folderbatch/sync-queue/";

class FolderBatchSyncQueue {
    node;
    startAtWidget;
    itemCountWidget;
    autoQueueWidget;
    progressWidget;
    itemCount = 0;

    getParams() {
        const names = [
            "common_folder",
            "sync_mode",
            "missing_policy",
            "sort_by",
            "order_by",
            "use_image",
            "image_folder",
            "image_extension",
            "use_video",
            "video_folder",
            "video_extension",
            "use_text",
            "text_folder",
            "text_extension",
            "use_audio",
            "audio_folder",
            "audio_extension",
        ];

        const params = new URLSearchParams();
        for (const name of names) {
            const widget = findWidgetByName(this.node, name);
            const value = widget?.value ?? "";
            params.set(name, String(value));
        }
        return params.toString();
    }

    getItemCount() {
        return new Promise(async (resolve) => {
            const url = API_BASE_URL + `get_sync_count?${this.getParams()}`;
            const response = await fetch(url);
            const data = await response.json();
            this.itemCount = parseInt(data["item_count"]);
            resolve(this.itemCount);
        });
    }

    refreshItemCount() {
        if (this.itemCountWidget) {
            this.itemCountWidget.value = this.itemCount;
        }
    }

    refreshProgress(startAt) {
        if (this.progressWidget && this.itemCount > 0) {
            this.progressWidget.value = (startAt + 1) / this.itemCount;
        }
    }

    async onExecuted(itemCount, startAt) {
        if (startAt + 1 < itemCount) {
            this.startAtWidget.value = startAt + 1;
            this.refreshProgress(startAt);

            if (this.autoQueueWidget.value) {
                await sleep(200);
                app.queuePrompt(0, 1);
            }
        } else if (startAt + 1 >= itemCount) {
            this.startAtWidget.value = 0;
            if (this.progressWidget) {
                this.progressWidget.value = 0;
            }
        }
    }

    initWidget(node, startAtWidget, itemCountWidget, autoQueueWidget, progressWidget) {
        this.node = node;
        this.startAtWidget = startAtWidget;
        this.itemCountWidget = itemCountWidget;
        this.autoQueueWidget = autoQueueWidget;
        this.progressWidget = progressWidget;

        const watchedNames = [
            "common_folder",
            "sync_mode",
            "missing_policy",
            "sort_by",
            "order_by",
            "use_image",
            "image_folder",
            "image_extension",
            "use_video",
            "video_folder",
            "video_extension",
            "use_text",
            "text_folder",
            "text_extension",
            "use_audio",
            "audio_folder",
            "audio_extension",
        ];

        for (const name of watchedNames) {
            const widget = findWidgetByName(node, name);
            if (!widget) continue;
            widget.callback = async () => {
                await this.getItemCount();
                this.refreshItemCount();
            };
        }

        setTimeout(async () => {
            await this.getItemCount();
            this.refreshItemCount();
        }, 100);
    }
}

app.registerExtension({
    name: "Comfy.FolderBatch.FolderBatchSyncQueue",

    async beforeRegisterNodeDef(nodeType, nodeData) {
        if (nodeData.name !== "FolderBatch Sync Queue") return;

        const folderSyncQueue = new FolderBatchSyncQueue();

        const origOnNodeCreated = nodeType.prototype.onNodeCreated;
        nodeType.prototype.onNodeCreated = function () {
            const r = origOnNodeCreated ? origOnNodeCreated.apply(this) : undefined;

            const startAtWidget = findWidgetByName(this, "start_at");
            const autoQueueWidget = findWidgetByName(this, "auto_queue");
            const itemCountWidget = findWidgetByName(this, "item_count");
            const progressWidget = findWidgetByName(this, "progress");

            folderSyncQueue.initWidget(
                this,
                startAtWidget,
                itemCountWidget,
                autoQueueWidget,
                progressWidget
            );

            return r;
        };

        const onExecuted = nodeType.prototype.onExecuted;
        nodeType.prototype.onExecuted = async function (message) {
            onExecuted?.apply(this, arguments);

            const itemCount = message["item_count"][0];
            const startAt = message["start_at"][0];
            folderSyncQueue.onExecuted(itemCount, startAt);
        };
    },
});
