# ComfyUI-FolderBatch

Inspired by https://github.com/da2el-ai/D2-nodes-ComfyUI/tree/main and its design ideas.

Folder-based batch queue helpers for ComfyUI. These nodes let you queue items
from a folder one-by-one and feed them into your workflow.

---

Japanese translation below (日本語は後半に記載).

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

Outputs
- text (STRING): File content.

### FolderBatch Audio Queue
Queue audio files from a folder, one per execution.

Inputs (required)
- folder (STRING): Folder path to scan.
- extension (STRING): Glob pattern(s), default `*.mp3;*.wav;*.flac;*.m4a;*.ogg;*.aac`.
- start_at (INT): Start index (0-based).
- auto_queue (BOOLEAN): If enabled, triggers next queue automatically.
- sort_by (Name|Date|Random): Sorting method.
- order_by (A-Z|Z-A): Sort order.

Inputs (optional)
- audio_count (INT): UI display only.
- progress (FLOAT): UI display only (0.0 - 1.0).

Outputs
- audio_path (STRING): Full path of the selected audio file.
- audio_count (INT): Total count of matching files.

### FolderBatch Load Audio
Load an audio file and output it as AUDIO.

Inputs (required)
- audio_path (STRING): Full path to the audio file.

Outputs
- audio (AUDIO): Loaded audio waveform and sample rate.

## Typical Usage

Video batch:
1) FolderBatch Video Queue -> video_path
2) FolderBatch Load Video Frames -> images
3) Connect images to your processing nodes

Text batch:
1) FolderBatch Text Queue -> text_path
2) FolderBatch Load Text -> text
3) Connect text to prompt/conditioning nodes

Audio batch:
1) FolderBatch Audio Queue -> audio_path
2) FolderBatch Load Audio -> audio
3) Connect audio to your processing nodes

---

# ComfyUI-FolderBatch (日本語)

https://github.com/da2el-ai/D2-nodes-ComfyUI/tree/main の構想と設計を参考にしています。

ComfyUIでフォルダ内のファイルを1つずつキューに流し込むためのノード集です。

## ノード

### FolderBatch Video Queue
フォルダ内の動画を1本ずつキューに流します。

入力（必須）
- folder (STRING): 対象フォルダのパス
- extension (STRING): 拡張子のグロブ（例: `*.mp4`）
- start_at (INT): 開始インデックス（0始まり）
- auto_queue (BOOLEAN): 有効なら自動で次をキュー
- sort_by (Name|Date|Random): 並び順の基準
- order_by (A-Z|Z-A): 並び順の向き

入力（任意）
- video_count (INT): UI表示用
- progress (FLOAT): UI表示用（0.0 - 1.0）

出力
- video_path (STRING): 選択された動画のフルパス
- video_count (INT): 対象ファイルの総数

### FolderBatch Load Video Frames
動画を読み込み、フレームをIMAGEバッチで出力します。

入力（必須）
- video_path (STRING): 動画ファイルのフルパス

出力
- images (IMAGE): フレームのバッチ

### FolderBatch Text Queue
フォルダ内のtxtを1つずつキューに流します。

入力（必須）
- folder (STRING): 対象フォルダのパス
- extension (STRING): 拡張子のグロブ（例: `*.txt`）
- start_at (INT): 開始インデックス（0始まり）
- auto_queue (BOOLEAN): 有効なら自動で次をキュー
- sort_by (Name|Date|Random): 並び順の基準
- order_by (A-Z|Z-A): 並び順の向き

入力（任意）
- text_count (INT): UI表示用
- progress (FLOAT): UI表示用（0.0 - 1.0）

出力
- text_path (STRING): 選択されたテキストのフルパス
- text_count (INT): 対象ファイルの総数

### FolderBatch Load Text
テキストファイルを読み込み、内容をSTRINGで出力します。

入力（必須）
- text_path (STRING): テキストファイルのフルパス

出力
- text (STRING): ファイル内容

### FolderBatch Audio Queue
フォルダ内の音声を1つずつキューに流します。

入力（必須）
- folder (STRING): 対象フォルダのパス
- extension (STRING): 拡張子グロブ。複数指定可。既定値 `*.mp3;*.wav;*.flac;*.m4a;*.ogg;*.aac`
- start_at (INT): 開始インデックス（0始まり）
- auto_queue (BOOLEAN): 有効なら自動で次をキュー
- sort_by (Name|Date|Random): 並び順の基準
- order_by (A-Z|Z-A): 並び順の向き

入力（任意）
- audio_count (INT): UI表示用
- progress (FLOAT): UI表示用（0.0 - 1.0）

出力
- audio_path (STRING): 選択された音声のフルパス
- audio_count (INT): 対象ファイルの総数

### FolderBatch Load Audio
音声ファイルを読み込み、AUDIOで出力します。

入力（必須）
- audio_path (STRING): 音声ファイルのフルパス

出力
- audio (AUDIO): 読み込んだ音声データ

## 典型的な使い方

動画バッチ:
1) FolderBatch Video Queue -> video_path
2) FolderBatch Load Video Frames -> images
3) 画像処理ノードに接続

テキストバッチ:
1) FolderBatch Text Queue -> text_path
2) FolderBatch Load Text -> text
3) プロンプト/条件ノードに接続

音声バッチ:
1) FolderBatch Audio Queue -> audio_path
2) FolderBatch Load Audio -> audio
3) 音声処理ノードに接続
