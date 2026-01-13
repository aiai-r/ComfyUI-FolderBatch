import os
import json
import glob
import random
from aiohttp import web

import folder_paths
from server import PromptServer
from comfy_api.latest._input_impl.video_types import VideoFromFile


def get_files(folder, extension, sort_by="Name", order_by="A-Z"):
    if folder is None or str(folder).strip() == "":
        return []

    search_pattern = os.path.join(folder, extension)
    file_list = glob.glob(search_pattern)
    file_list = [os.path.abspath(file) for file in file_list]

    if sort_by == "Name":
        file_list = sorted(file_list, key=lambda x: os.path.basename(x))
    elif sort_by == "Date":
        file_list = sorted(file_list, key=lambda x: os.path.getmtime(x))
    elif sort_by == "Random":
        random.shuffle(file_list)

    if order_by == "Z-A" and sort_by != "Random":
        file_list.reverse()

    return file_list


class FB_FolderVideoQueue:
    """
    Folder-based video queue. Emits one video path per execution.
    """

    def __init__(self):
        self.is_finished = False
        self.files = []

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "folder": ("STRING", {"default": ""}),
                "extension": ("STRING", {"default": "*.mp4"}),
                "start_at": ("INT", {"default": 0, "min": 0}),
                "auto_queue": ("BOOLEAN", {"default": True}),
                "sort_by": (["Name", "Date", "Random"], {"default": "Name"}),
                "order_by": (["A-Z", "Z-A"], {"default": "A-Z"}),
            },
            "optional": {
                "video_count": ("INT", {"default": 0, "min": 0}),
                "progress": ("FLOAT", {"default": 0.0, "min": 0.0, "max": 1.0, "step": 0.001}),
            },
        }

    RETURN_TYPES = ("STRING", "INT")
    RETURN_NAMES = ("video_path", "video_count")
    FUNCTION = "run"
    CATEGORY = "FolderBatch/Video"

    def run(
        self,
        folder="",
        extension="*.mp4",
        start_at=0,
        auto_queue=True,
        sort_by="Name",
        order_by="A-Z",
        video_count=0,
        progress=0.0,
    ):
        if len(self.files) <= 0:
            self.files = get_files(folder, extension, sort_by, order_by)
            self.is_finished = False

        if len(self.files) == 0:
            return {
                "result": ("", 0),
                "ui": {
                    "video_count": (0,),
                    "start_at": (0,),
                    "progress": (0.0,),
                },
            }

        start_at = max(0, min(start_at, len(self.files) - 1))
        video_path = self.files[start_at]
        total = len(self.files)

        if len(self.files) <= start_at + 1:
            self.is_finished = True
            self.files = []

        progress_val = 0.0
        if total > 0:
            progress_val = (start_at + 1) / total

        return {
            "result": (video_path, total),
            "ui": {
                "video_count": (total,),
                "start_at": (start_at,),
                "progress": (progress_val,),
            },
        }


class FB_LoadVideoFrames:
    """
    Load video frames as IMAGE batch.
    """

    @classmethod
    def INPUT_TYPES(cls):
        input_dir = folder_paths.get_input_directory()
        files = [f for f in os.listdir(input_dir) if os.path.isfile(os.path.join(input_dir, f))]
        files = folder_paths.filter_files_content_types(files, ["video"])
        return {
            "required": {
                "video_path": ("STRING", {"default": "", "forceInput": True}),
            },
            "optional": {
                "video": (sorted(files), {"video_upload": True}),
            },
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("images",)
    FUNCTION = "load_video_frames"
    CATEGORY = "FolderBatch/Video"

    def load_video_frames(self, video_path, video=None):
        if video_path is not None and str(video_path).strip() != "":
            resolved_path = str(video_path).strip()
        elif video is not None and str(video).strip() != "":
            resolved_path = folder_paths.get_annotated_filepath(video)
        else:
            raise ValueError("No video file selected.")

        video_input = VideoFromFile(resolved_path)
        components = video_input.get_components()
        return (components.images,)


@PromptServer.instance.routes.get("/folderbatch/video-queue/get_video_count")
async def route_folderbatch_video_get_video_count(request):
    try:
        folder = request.query.get("folder")
        extension = request.query.get("extension")
        files = get_files(folder, extension)
        video_count = len(files)
    except Exception:
        video_count = 0

    json_data = json.dumps({"video_count": video_count})
    return web.Response(text=json_data, content_type="application/json")


NODE_CLASS_MAPPINGS = {
    "FolderBatch Video Queue": FB_FolderVideoQueue,
    "FolderBatch Load Video Frames": FB_LoadVideoFrames,
}

NODE_DISPLAY_NAME_MAPPINGS = {}
