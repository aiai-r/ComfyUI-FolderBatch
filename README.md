# ComfyUI-FolderBatch

Inspired by https://github.com/da2el-ai/D2-nodes-ComfyUI/tree/main and its design ideas.

Folder-based batch queue helpers for ComfyUI. These nodes let you queue items
from a folder one-by-one and feed them into your workflow.

## Nodes

### FolderBatch Video Queue
Queue video files from a folder, one per execution.

Inputs (required)
- folder (STRING): Folder path to scan.
- extension (STRING): Glob pattern, default `*.mp4`.
- start_at (INT): Start index (0-based).
- auto_queue (BOOLEAN): If enabled, triggers next queue automatically.
- sort_by (Name|Date|Random): Sorting method.
- order_by (A-Z|Z-A): Sort order.

Inputs (optional)
- video_count (INT): UI display only.
- progress (FLOAT): UI display only (0.0 - 1.0).

Outputs
- video_path (STRING): Full path of the selected video.
- video_count (INT): Total count of matching files.

### FolderBatch Load Video Frames
Load a video and output frames as IMAGE batch.

Inputs (required)
- video_path (STRING): Full path to the video file.

Outputs
- images (IMAGE): Video frames as a batch.

### FolderBatch Text Queue
Queue text files from a folder, one per execution.

Inputs (required)
- folder (STRING): Folder path to scan.
- extension (STRING): Glob pattern, default `*.txt`.
- start_at (INT): Start index (0-based).
- auto_queue (BOOLEAN): If enabled, triggers next queue automatically.
- sort_by (Name|Date|Random): Sorting method.
- order_by (A-Z|Z-A): Sort order.

Inputs (optional)
- text_count (INT): UI display only.
- progress (FLOAT): UI display only (0.0 - 1.0).

Outputs
- text_path (STRING): Full path of the selected text file.
- text_count (INT): Total count of matching files.

### FolderBatch Load Text
Load a text file and output its content.

Inputs (required)
- text_path (STRING): Full path to the text file.

Inputs (optional)
- text_file (COMBO): Optional file picker from ComfyUI input directory.

Outputs
- text (STRING): File content.

## Typical Usage

Video batch:
1) FolderBatch Video Queue -> video_path
2) FolderBatch Load Video Frames -> images
3) Connect images to your processing nodes

Text batch:
1) FolderBatch Text Queue -> text_path
2) FolderBatch Load Text -> text
3) Connect text to prompt/conditioning nodes
