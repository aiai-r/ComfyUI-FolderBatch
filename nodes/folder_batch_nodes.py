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
        return {
            "required": {
                "video_path": ("STRING", {"default": "", "forceInput": True}),
            },
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("images",)
    FUNCTION = "load_video_frames"
    CATEGORY = "FolderBatch/Video"

    def load_video_frames(self, video_path):
        if video_path is not None and str(video_path).strip() != "":
            resolved_path = str(video_path).strip()
        else:
            raise ValueError("No video file selected.")

        video_input = VideoFromFile(resolved_path)
        components = video_input.get_components()
        return (components.images,)


class FB_FolderTextQueue:
    """
    Folder-based text queue. Emits one text file path per execution.
    """

    def __init__(self):
        self.is_finished = False
        self.files = []

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "folder": ("STRING", {"default": ""}),
                "extension": ("STRING", {"default": "*.txt"}),
                "start_at": ("INT", {"default": 0, "min": 0}),
                "auto_queue": ("BOOLEAN", {"default": True}),
                "sort_by": (["Name", "Date", "Random"], {"default": "Name"}),
                "order_by": (["A-Z", "Z-A"], {"default": "A-Z"}),
            },
            "optional": {
                "text_count": ("INT", {"default": 0, "min": 0}),
                "progress": ("FLOAT", {"default": 0.0, "min": 0.0, "max": 1.0, "step": 0.001}),
            },
        }

    RETURN_TYPES = ("STRING", "INT")
    RETURN_NAMES = ("text_path", "text_count")
    FUNCTION = "run"
    CATEGORY = "FolderBatch/Text"

    def run(
        self,
        folder="",
        extension="*.txt",
        start_at=0,
        auto_queue=True,
        sort_by="Name",
        order_by="A-Z",
        text_count=0,
        progress=0.0,
    ):
        if len(self.files) <= 0:
            self.files = get_files(folder, extension, sort_by, order_by)
            self.is_finished = False

        if len(self.files) == 0:
            return {
                "result": ("", 0),
                "ui": {
                    "text_count": (0,),
                    "start_at": (0,),
                    "progress": (0.0,),
                },
            }

        start_at = max(0, min(start_at, len(self.files) - 1))
        text_path = self.files[start_at]
        total = len(self.files)

        if len(self.files) <= start_at + 1:
            self.is_finished = True
            self.files = []

        progress_val = 0.0
        if total > 0:
            progress_val = (start_at + 1) / total

        return {
            "result": (text_path, total),
            "ui": {
                "text_count": (total,),
                "start_at": (start_at,),
                "progress": (progress_val,),
            },
        }


class FB_LoadTextFile:
    """
    Load text file content as STRING.
    """

    @classmethod
    def INPUT_TYPES(cls):
        input_dir = folder_paths.get_input_directory()
        search_pattern = os.path.join(input_dir, "*.txt")
        files = [os.path.basename(p) for p in glob.glob(search_pattern)]
        return {
            "required": {
                "text_path": ("STRING", {"default": "", "forceInput": True}),
            },
            "optional": {
                "text_file": (sorted(files),),
            },
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("text",)
    FUNCTION = "load_text"
    CATEGORY = "FolderBatch/Text"

    def load_text(self, text_path, text_file=None):
        if text_path is not None and str(text_path).strip() != "":
            resolved_path = str(text_path).strip()
        elif text_file is not None and str(text_file).strip() != "":
            resolved_path = os.path.join(folder_paths.get_input_directory(), text_file)
        else:
            raise ValueError("No text file selected.")

        with open(resolved_path, "r", encoding="utf-8", errors="replace") as f:
            text = f.read()

        return (text,)


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


@PromptServer.instance.routes.get("/folderbatch/text-queue/get_text_count")
async def route_folderbatch_text_get_text_count(request):
    try:
        folder = request.query.get("folder")
        extension = request.query.get("extension")
        files = get_files(folder, extension)
        text_count = len(files)
    except Exception:
        text_count = 0

    json_data = json.dumps({"text_count": text_count})
    return web.Response(text=json_data, content_type="application/json")


NODE_CLASS_MAPPINGS = {
    "FolderBatch Video Queue": FB_FolderVideoQueue,
    "FolderBatch Load Video Frames": FB_LoadVideoFrames,
    "FolderBatch Text Queue": FB_FolderTextQueue,
    "FolderBatch Load Text": FB_LoadTextFile,
}

NODE_DISPLAY_NAME_MAPPINGS = {}
