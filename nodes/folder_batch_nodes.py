import os
import json
import glob
import random
import av
import numpy as np
import torch
from aiohttp import web
from PIL import Image, ImageOps, ImageSequence

import folder_paths
import node_helpers
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


def get_base_name(path):
    return os.path.splitext(os.path.basename(path))[0]


def resolve_folder(common_folder, specific_folder):
    if specific_folder is not None and str(specific_folder).strip() != "":
        return str(specific_folder).strip()
    if common_folder is not None and str(common_folder).strip() != "":
        return str(common_folder).strip()
    return ""


def build_media_configs(
    common_folder="",
    use_image=False,
    image_folder="",
    image_extension="*.png;*.jpg;*.jpeg;*.webp;*.bmp",
    use_video=False,
    video_folder="",
    video_extension="*.mp4",
    use_text=False,
    text_folder="",
    text_extension="*.txt",
    use_audio=False,
    audio_folder="",
    audio_extension="*.mp3;*.wav;*.flac;*.m4a;*.ogg;*.aac",
):
    configs = []

    if use_image:
        configs.append({
            "key": "image_path",
            "folder": resolve_folder(common_folder, image_folder),
            "extension": image_extension,
        })
    if use_video:
        configs.append({
            "key": "video_path",
            "folder": resolve_folder(common_folder, video_folder),
            "extension": video_extension,
        })
    if use_text:
        configs.append({
            "key": "text_path",
            "folder": resolve_folder(common_folder, text_folder),
            "extension": text_extension,
        })
    if use_audio:
        configs.append({
            "key": "audio_path",
            "folder": resolve_folder(common_folder, audio_folder),
            "extension": audio_extension,
        })

    return configs


def build_sync_entries(configs, sync_mode="By Name", sort_by="Name", order_by="A-Z", missing_policy="Skip"):
    if not configs:
        return []

    media_files = {}
    for config in configs:
        media_files[config["key"]] = get_files(config["folder"], config["extension"], sort_by, order_by)

    if sync_mode == "By Name":
        return build_sync_entries_by_name(media_files, missing_policy)

    return build_sync_entries_by_order(media_files, missing_policy)


def build_sync_entries_by_name(media_files, missing_policy):
    name_maps = {
        key: {get_base_name(path): path for path in paths}
        for key, paths in media_files.items()
    }

    all_names = sorted({name for mapping in name_maps.values() for name in mapping.keys()})
    if not all_names:
        return []

    if missing_policy == "Skip":
        candidate_names = [
            name for name in all_names
            if all(name in mapping for mapping in name_maps.values())
        ]
    else:
        candidate_names = all_names

    entries = []
    for name in candidate_names:
        entry = {"base_name": name}
        missing_keys = []
        for key, mapping in name_maps.items():
            value = mapping.get(name, "")
            entry[key] = value
            if value == "":
                missing_keys.append(key)

        if missing_policy == "Error" and missing_keys:
            missing_list = ", ".join(missing_keys)
            raise ValueError(f"Missing synchronized files for '{name}': {missing_list}")

        entries.append(entry)

    return entries


def build_sync_entries_by_order(media_files, missing_policy):
    lengths = [len(paths) for paths in media_files.values()]
    if not lengths or max(lengths) == 0:
        return []

    if missing_policy == "Error" and len(set(lengths)) > 1:
        raise ValueError(f"Mismatched item counts for order sync: {lengths}")

    total = min(lengths) if missing_policy == "Skip" else max(lengths)
    entries = []

    for index in range(total):
        entry = {"base_name": ""}
        missing_keys = []
        for key, paths in media_files.items():
            value = paths[index] if index < len(paths) else ""
            entry[key] = value
            if entry["base_name"] == "" and value != "":
                entry["base_name"] = get_base_name(value)
            if value == "":
                missing_keys.append(key)

        if missing_policy == "Error" and missing_keys:
            missing_list = ", ".join(missing_keys)
            raise ValueError(f"Missing synchronized files at index {index}: {missing_list}")

        entries.append(entry)

    return entries


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

        # Match manual prompt entry more closely by ignoring UTF-8 BOM
        # and removing only terminal line breaks commonly added by editors.
        with open(resolved_path, "r", encoding="utf-8-sig", errors="replace") as f:
            text = f.read()

        text = text.rstrip("\r\n")

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
    Load audio file content as AUDIO and durations.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "audio_path": ("STRING", {"default": "", "forceInput": True}),
            },
        }

    RETURN_TYPES = ("AUDIO", "FLOAT", "INT")
    RETURN_NAMES = ("audio", "duration_float", "duration_int")
    FUNCTION = "load_audio"
    CATEGORY = "FolderBatch/Audio"

    def load_audio(self, audio_path):
        if audio_path is not None and str(audio_path).strip() != "":
            resolved_path = str(audio_path).strip()
        else:
            raise ValueError("No audio file selected.")

        audio = load_audio_file(resolved_path)
        waveform = audio["waveform"]
        sample_rate = audio["sample_rate"]
        duration_float = 0.0 if sample_rate <= 0 else float(waveform.shape[-1]) / float(sample_rate)
        duration_int = int(round(duration_float))

        return (audio, duration_float, duration_int)


class FB_FolderImageQueue:
    """
    Folder-based image queue. Emits one image file path per execution.
    """

    def __init__(self):
        self.is_finished = False
        self.files = []

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "folder": ("STRING", {"default": ""}),
                "extension": ("STRING", {"default": "*.png;*.jpg;*.jpeg;*.webp;*.bmp"}),
                "start_at": ("INT", {"default": 0, "min": 0}),
                "auto_queue": ("BOOLEAN", {"default": True}),
                "sort_by": (["Name", "Date", "Random"], {"default": "Name"}),
                "order_by": (["A-Z", "Z-A"], {"default": "A-Z"}),
            },
            "optional": {
                "image_count": ("INT", {"default": 0, "min": 0}),
                "progress": ("FLOAT", {"default": 0.0, "min": 0.0, "max": 1.0, "step": 0.001}),
            },
        }

    RETURN_TYPES = ("STRING", "INT")
    RETURN_NAMES = ("image_path", "image_count")
    FUNCTION = "run"
    CATEGORY = "FolderBatch/Image"

    def run(
        self,
        folder="",
        extension="*.png;*.jpg;*.jpeg;*.webp;*.bmp",
        start_at=0,
        auto_queue=True,
        sort_by="Name",
        order_by="A-Z",
        image_count=0,
        progress=0.0,
    ):
        if len(self.files) <= 0:
            self.files = get_files(folder, extension, sort_by, order_by)
            self.is_finished = False

        if len(self.files) == 0:
            return {
                "result": ("", 0),
                "ui": {
                    "image_count": (0,),
                    "start_at": (0,),
                    "progress": (0.0,),
                },
            }

        start_at = max(0, min(start_at, len(self.files) - 1))
        image_path = self.files[start_at]
        total = len(self.files)

        if len(self.files) <= start_at + 1:
            self.is_finished = True
            self.files = []

        progress_val = 0.0
        if total > 0:
            progress_val = (start_at + 1) / total

        return {
            "result": (image_path, total),
            "ui": {
                "image_count": (total,),
                "start_at": (start_at,),
                "progress": (progress_val,),
            },
        }


class FB_LoadImageFile:
    """
    Load image file content as IMAGE and MASK.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image_path": ("STRING", {"default": "", "forceInput": True}),
            },
        }

    RETURN_TYPES = ("IMAGE", "MASK")
    RETURN_NAMES = ("image", "mask")
    FUNCTION = "load_image"
    CATEGORY = "FolderBatch/Image"

    def load_image(self, image_path):
        if image_path is not None and str(image_path).strip() != "":
            resolved_path = str(image_path).strip()
        else:
            raise ValueError("No image file selected.")

        img = node_helpers.pillow(Image.open, resolved_path)

        output_images = []
        output_masks = []
        width, height = None, None

        for frame in ImageSequence.Iterator(img):
            frame = node_helpers.pillow(ImageOps.exif_transpose, frame)

            if frame.mode == "I":
                frame = frame.point(lambda value: value * (1 / 255))
            image = frame.convert("RGB")

            if len(output_images) == 0:
                width, height = image.size

            if image.size[0] != width or image.size[1] != height:
                continue

            image = np.array(image).astype(np.float32) / 255.0
            image = torch.from_numpy(image)[None,]

            if "A" in frame.getbands():
                mask = np.array(frame.getchannel("A")).astype(np.float32) / 255.0
                mask = 1.0 - torch.from_numpy(mask)
            elif frame.mode == "P" and "transparency" in frame.info:
                mask = np.array(frame.convert("RGBA").getchannel("A")).astype(np.float32) / 255.0
                mask = 1.0 - torch.from_numpy(mask)
            else:
                mask = torch.zeros((64, 64), dtype=torch.float32, device="cpu")

            output_images.append(image)
            output_masks.append(mask.unsqueeze(0))

            if img.format == "MPO":
                break

        if not output_images:
            raise ValueError("No image frames decoded.")

        if len(output_images) > 1:
            output_image = torch.cat(output_images, dim=0)
            output_mask = torch.cat(output_masks, dim=0)
        else:
            output_image = output_images[0]
            output_mask = output_masks[0]

        return (output_image, output_mask)


class FB_FolderSyncQueue:
    """
    Folder-based synchronized queue for image, video, text, and audio.
    """

    def __init__(self):
        self.is_finished = False
        self.entries = []

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "common_folder": ("STRING", {"default": ""}),
                "sync_mode": (["By Name", "By Order"], {"default": "By Name"}),
                "missing_policy": (["Skip", "Error", "Empty"], {"default": "Skip"}),
                "start_at": ("INT", {"default": 0, "min": 0}),
                "auto_queue": ("BOOLEAN", {"default": True}),
                "sort_by": (["Name", "Date", "Random"], {"default": "Name"}),
                "order_by": (["A-Z", "Z-A"], {"default": "A-Z"}),
                "use_image": ("BOOLEAN", {"default": False}),
                "image_folder": ("STRING", {"default": ""}),
                "image_extension": ("STRING", {"default": "*.png;*.jpg;*.jpeg;*.webp;*.bmp"}),
                "use_video": ("BOOLEAN", {"default": False}),
                "video_folder": ("STRING", {"default": ""}),
                "video_extension": ("STRING", {"default": "*.mp4"}),
                "use_text": ("BOOLEAN", {"default": False}),
                "text_folder": ("STRING", {"default": ""}),
                "text_extension": ("STRING", {"default": "*.txt"}),
                "use_audio": ("BOOLEAN", {"default": False}),
                "audio_folder": ("STRING", {"default": ""}),
                "audio_extension": ("STRING", {"default": "*.mp3;*.wav;*.flac;*.m4a;*.ogg;*.aac"}),
            },
            "optional": {
                "item_count": ("INT", {"default": 0, "min": 0}),
                "progress": ("FLOAT", {"default": 0.0, "min": 0.0, "max": 1.0, "step": 0.001}),
            },
        }

    RETURN_TYPES = ("STRING", "STRING", "STRING", "STRING", "STRING", "INT")
    RETURN_NAMES = ("base_name", "image_path", "video_path", "text_path", "audio_path", "item_count")
    FUNCTION = "run"
    CATEGORY = "FolderBatch/Sync"

    def run(
        self,
        common_folder="",
        sync_mode="By Name",
        missing_policy="Skip",
        start_at=0,
        auto_queue=True,
        sort_by="Name",
        order_by="A-Z",
        use_image=False,
        image_folder="",
        image_extension="*.png;*.jpg;*.jpeg;*.webp;*.bmp",
        use_video=False,
        video_folder="",
        video_extension="*.mp4",
        use_text=False,
        text_folder="",
        text_extension="*.txt",
        use_audio=False,
        audio_folder="",
        audio_extension="*.mp3;*.wav;*.flac;*.m4a;*.ogg;*.aac",
        item_count=0,
        progress=0.0,
    ):
        if len(self.entries) <= 0:
            configs = build_media_configs(
                common_folder=common_folder,
                use_image=use_image,
                image_folder=image_folder,
                image_extension=image_extension,
                use_video=use_video,
                video_folder=video_folder,
                video_extension=video_extension,
                use_text=use_text,
                text_folder=text_folder,
                text_extension=text_extension,
                use_audio=use_audio,
                audio_folder=audio_folder,
                audio_extension=audio_extension,
            )
            self.entries = build_sync_entries(configs, sync_mode, sort_by, order_by, missing_policy)
            self.is_finished = False

        if len(self.entries) == 0:
            return {
                "result": ("", "", "", "", "", 0),
                "ui": {
                    "item_count": (0,),
                    "start_at": (0,),
                    "progress": (0.0,),
                },
            }

        start_at = max(0, min(start_at, len(self.entries) - 1))
        entry = self.entries[start_at]
        total = len(self.entries)

        if len(self.entries) <= start_at + 1:
            self.is_finished = True
            self.entries = []

        progress_val = 0.0
        if total > 0:
            progress_val = (start_at + 1) / total

        return {
            "result": (
                entry.get("base_name", ""),
                entry.get("image_path", ""),
                entry.get("video_path", ""),
                entry.get("text_path", ""),
                entry.get("audio_path", ""),
                total,
            ),
            "ui": {
                "item_count": (total,),
                "start_at": (start_at,),
                "progress": (progress_val,),
            },
        }


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


@PromptServer.instance.routes.get("/folderbatch/image-queue/get_image_count")
async def route_folderbatch_image_get_image_count(request):
    try:
        folder = request.query.get("folder")
        extension = request.query.get("extension")
        files = get_files(folder, extension)
        image_count = len(files)
    except Exception:
        image_count = 0

    json_data = json.dumps({"image_count": image_count})
    return web.Response(text=json_data, content_type="application/json")


@PromptServer.instance.routes.get("/folderbatch/sync-queue/get_sync_count")
async def route_folderbatch_sync_get_sync_count(request):
    try:
        configs = build_media_configs(
            common_folder=request.query.get("common_folder", ""),
            use_image=request.query.get("use_image", "false").lower() == "true",
            image_folder=request.query.get("image_folder", ""),
            image_extension=request.query.get("image_extension", "*.png;*.jpg;*.jpeg;*.webp;*.bmp"),
            use_video=request.query.get("use_video", "false").lower() == "true",
            video_folder=request.query.get("video_folder", ""),
            video_extension=request.query.get("video_extension", "*.mp4"),
            use_text=request.query.get("use_text", "false").lower() == "true",
            text_folder=request.query.get("text_folder", ""),
            text_extension=request.query.get("text_extension", "*.txt"),
            use_audio=request.query.get("use_audio", "false").lower() == "true",
            audio_folder=request.query.get("audio_folder", ""),
            audio_extension=request.query.get("audio_extension", "*.mp3;*.wav;*.flac;*.m4a;*.ogg;*.aac"),
        )
        entries = build_sync_entries(
            configs,
            request.query.get("sync_mode", "By Name"),
            request.query.get("sort_by", "Name"),
            request.query.get("order_by", "A-Z"),
            request.query.get("missing_policy", "Skip"),
        )
        item_count = len(entries)
    except Exception:
        item_count = 0

    json_data = json.dumps({"item_count": item_count})
    return web.Response(text=json_data, content_type="application/json")


NODE_CLASS_MAPPINGS = {
    "FolderBatch Video Queue": FB_FolderVideoQueue,
    "FolderBatch Load Video Frames": FB_LoadVideoFrames,
    "FolderBatch Text Queue": FB_FolderTextQueue,
    "FolderBatch Load Text": FB_LoadTextFile,
    "FolderBatch Audio Queue": FB_FolderAudioQueue,
    "FolderBatch Load Audio": FB_LoadAudioFile,
    "FolderBatch Image Queue": FB_FolderImageQueue,
    "FolderBatch Load Image": FB_LoadImageFile,
    "FolderBatch Sync Queue": FB_FolderSyncQueue,
}

NODE_DISPLAY_NAME_MAPPINGS = {}
