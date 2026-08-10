import importlib
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import torch
from aiohttp import web
from PIL import Image

sys.path.insert(0, str(Path(__file__).parents[3]))
from server import PromptServer


class PromptServerStub:
    routes = web.RouteTableDef()


PromptServer.instance = PromptServerStub()
sys.path.insert(0, str(Path(__file__).parents[2]))
folder_batch_nodes = importlib.import_module("ComfyUI-FolderBatch.nodes.folder_batch_nodes")


class QueueStateTests(unittest.TestCase):
    def test_text_queue_repeats_each_entry_before_finishing(self):
        with tempfile.TemporaryDirectory() as folder:
            Path(folder, "a.txt").write_text("a", encoding="utf-8")
            Path(folder, "b.txt").write_text("b", encoding="utf-8")
            queue = folder_batch_nodes.FB_FolderTextQueue()

            first = queue.run(folder=folder, repeat_count=2, repeat_index=0, auto_queue=False)
            repeated = queue.run(folder=folder, repeat_count=2, repeat_index=1, auto_queue=False)
            second = queue.run(folder=folder, start_at=1, repeat_count=2, repeat_index=0, auto_queue=False)

            self.assertEqual(os.path.basename(first["result"][0]), "a.txt")
            self.assertEqual(os.path.basename(repeated["result"][0]), "a.txt")
            self.assertEqual(os.path.basename(second["result"][0]), "b.txt")
            self.assertEqual(first["ui"]["progress"], (0.25,))
            self.assertEqual(repeated["ui"]["progress"], (0.5,))
            self.assertEqual(second["ui"]["progress"], (0.75,))

    def test_media_queues_refresh_when_folder_changes(self):
        queue_types = (
            folder_batch_nodes.FB_FolderVideoQueue,
            folder_batch_nodes.FB_FolderAudioQueue,
            folder_batch_nodes.FB_FolderImageQueue,
        )

        with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
            for name in ("a.dat", "b.dat"):
                Path(first, name).touch()
            Path(second, "c.dat").touch()

            for queue_type in queue_types:
                with self.subTest(queue_type=queue_type.__name__):
                    queue = queue_type()
                    first_result = queue.run(first, "*.dat", start_at=0, auto_queue=False)
                    second_result = queue.run(second, "*.dat", start_at=0, auto_queue=False)
                    self.assertEqual(os.path.basename(first_result["result"][0]), "a.dat")
                    self.assertEqual(os.path.basename(second_result["result"][0]), "c.dat")

    def test_sync_queue_refreshes_when_folder_changes(self):
        with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
            for name in ("a.png", "b.png"):
                Path(first, name).touch()
            Path(second, "c.png").touch()

            queue = folder_batch_nodes.FB_FolderSyncQueue()
            first_result = queue.run(first, use_image=True, start_at=0, auto_queue=False)
            second_result = queue.run(second, use_image=True, start_at=0, auto_queue=False)

            self.assertEqual(os.path.basename(first_result["result"][1]), "a.png")
            self.assertEqual(os.path.basename(second_result["result"][1]), "c.png")


class ImageLoaderTests(unittest.TestCase):
    def test_image_uses_intermediate_dtype_and_device(self):
        with tempfile.TemporaryDirectory() as folder:
            image_path = Path(folder, "image.png")
            Image.new("RGB", (4, 3), "white").save(image_path)

            with (
                mock.patch.object(folder_batch_nodes.comfy.model_management, "intermediate_dtype", return_value=torch.float16),
                mock.patch.object(folder_batch_nodes.comfy.model_management, "intermediate_device", return_value=torch.device("cpu")),
            ):
                image, mask = folder_batch_nodes.FB_LoadImageFile().load_image(str(image_path))

            self.assertEqual(image.dtype, torch.float16)
            self.assertEqual(mask.dtype, torch.float16)
            self.assertEqual(image.device.type, "cpu")
            self.assertEqual(mask.device.type, "cpu")


if __name__ == "__main__":
    unittest.main()
