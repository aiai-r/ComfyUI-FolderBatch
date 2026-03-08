import os
import json
import glob
import random
import av
import torch
from aiohttp import web

import folder_paths
from server import PromptServer
from comfy_api.latest._input_impl.video_types import VideoFromFile


def get_search_patterns(extension):
    if extension is None:
        return []

    raw_patterns = str(extension).replace("\n", ";").replace(",", ";").split(";")
    patterns = [pattern.strip() for pattern in raw_patterns if pattern.strip()]
    return patterns or ["*"]


def get_files(folder, extension, sort_by="Name", order_by="A-Z"):
    if folder is None or str(folder).strip() == "":
        return []

    file_list = []
    for pattern in get_search_patterns(extension):
        search_pattern = os.path.join(folder, pattern)
        file_list.extend(glob.glob(search_pattern))

    file_list = sorted({os.path.abspath(file) for file in file_list})

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
        return {
            "required": {
                "text_path": ("STRING", {"default": "", "forceInput": True}),
            },
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("text",)
    FUNCTION = "load_text"
    CATEGORY = "FolderBatch/Text"

    def load_text(self, text_path):
        if text_path is not None and str(text_path).strip() != "":
            resolved_path = str(text_path).strip()
        else:
            raise ValueError("No text file selected.")

        with open(resolved_path, "r", encoding="utf-8", errors="replace") as f:
            text = f.read()

        return (text,)


def load_audio_file(filepath):
    with av.open(filepath) as audio_file:
        if not audio_file.streams.audio:
            raise ValueError("No audio stream found in the file.")

        stream = audio_file.streams.audio[0]
        sample_rate = stream.codec_context.sample_rate
        channels = stream.channels

        frames = []
        for frame in audio_file.decode(streams=stream.index):
            buffer = torch.from_numpy(frame.to_ndarray())
            if buffer.shape[0] != channels:
                buffer = buffer.view(-1, channels).t()
            frames.append(buffer)

        if not frames:
            raise ValueError("No audio frames decoded.")

        waveform = torch.cat(frames, dim=1)
        if waveform.dtype.is_floating_point:
            waveform = waveform.float()
        elif waveform.dtype == torch.int16:
            waveform = waveform.float() / (2 ** 15)
        elif waveform.dtype == torch.int32:
            waveform = waveform.float() / (2 ** 31)
        else:
            raise ValueError(f"Unsupported audio dtype: {waveform.dtype}")

        return {"waveform": waveform.unsqueeze(0), "sample_rate": sample_rate}


class FB_FolderAudioQueue:
    """
    Folder-based audio queue. Emits one audio file path per execution.
    """

    def __init__(self):
        self.is_finished = False
        self.files = []

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "folder": ("STRING", {"default": ""}),
                "extension": ("STRING", {"default": "*.mp3;*.wav;*.flac;*.m4a;*.ogg;*.aac"}),
                "start_at": ("INT", {"default": 0, "min": 0}),
                "auto_queue": ("BOOLEAN", {"default": True}),
                "sort_by": (["Name", "Date", "Random"], {"default": "Name"}),
                "order_by": (["A-Z", "Z-A"], {"default": "A-Z"}),
            },
            "optional": {
                "audio_count": ("INT", {"default": 0, "min": 0}),
                "progress": ("FLOAT", {"default": 0.0, "min": 0.0, "max": 1.0, "step": 0.001}),
            },
        }

    RETURN_TYPES = ("STRING", "INT")
    RETURN_NAMES = ("audio_path", "audio_count")
    FUNCTION = "run"
    CATEGORY = "FolderBatch/Audio"

    def run(
        self,
        folder="",
        extension="*.mp3;*.wav;*.flac;*.m4a;*.ogg;*.aac",
        start_at=0,
        auto_queue=True,
        sort_by="Name",
        order_by="A-Z",
        audio_count=0,
        progress=0.0,
    ):
        if len(self.files) <= 0:
            self.files = get_files(folder, extension, sort_by, order_by)
            self.is_finished = False

        if len(self.files) == 0:
            return {
                "result": ("", 0),
                "ui": {
                    "audio_count": (0,),
                    "start_at": (0,),
                    "progress": (0.0,),
                },
            }

        start_at = max(0, min(start_at, len(self.files) - 1))
        audio_path = self.files[start_at]
        total = len(self.files)

        if len(self.files) <= start_at + 1:
            self.is_finished = True
            self.files = []

        progress_val = 0.0
        if total > 0:
            progress_val = (start_at + 1) / total

        return {
            "result": (audio_path, total),
            "ui": {
                "audio_count": (total,),
                "start_at": (start_at,),
                "progress": (progress_val,),
            },
        }


class FB_LoadAudioFile:
    """
    Load audio file content as AUDIO.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "audio_path": ("STRING", {"default": "", "forceInput": True}),
            },
        }

    RETURN_TYPES = ("AUDIO",)
    RETURN_NAMES = ("audio",)
    FUNCTION = "load_audio"
    CATEGORY = "FolderBatch/Audio"

    def load_audio(self, audio_path):
        if audio_path is not None and str(audio_path).strip() != "":
            resolved_path = str(audio_path).strip()
        else:
            raise ValueError("No audio file selected.")

        return (load_audio_file(resolved_path),)


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


@PromptServer.instance.routes.get("/folderbatch/audio-queue/get_audio_count")
async def route_folderbatch_audio_get_audio_count(request):
    try:
        folder = request.query.get("folder")
        extension = request.query.get("extension")
        files = get_files(folder, extension)
        audio_count = len(files)
    except Exception:
        audio_count = 0

    json_data = json.dumps({"audio_count": audio_count})
    return web.Response(text=json_data, content_type="application/json")


NODE_CLASS_MAPPINGS = {
    "FolderBatch Video Queue": FB_FolderVideoQueue,
    "FolderBatch Load Video Frames": FB_LoadVideoFrames,
    "FolderBatch Text Queue": FB_FolderTextQueue,
    "FolderBatch Load Text": FB_LoadTextFile,
    "FolderBatch Audio Queue": FB_FolderAudioQueue,
    "FolderBatch Load Audio": FB_LoadAudioFile,
}

NODE_DISPLAY_NAME_MAPPINGS = {}
