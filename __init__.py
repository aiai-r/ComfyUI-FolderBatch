"""
@author: FolderBatch
@title: FolderBatch Nodes
@description: Folder-based batch queue helpers for ComfyUI
"""

from .nodes.folder_batch_nodes import NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS

WEB_DIRECTORY = "./web"

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]
