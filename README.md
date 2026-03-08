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
Load an audio file and output it as AUDIO plus durations.

Inputs (required)
- audio_path (STRING): Full path to the audio file.

Outputs
- audio (AUDIO): Loaded audio waveform and sample rate.
- duration_float (FLOAT): Audio duration in seconds.
- duration_int (INT): Rounded audio duration in seconds.

### FolderBatch Image Queue
Queue image files from a folder, one per execution.

Inputs (required)
- folder (STRING): Folder path to scan.
- extension (STRING): Glob pattern(s), default `*.png;*.jpg;*.jpeg;*.webp;*.bmp`.
- start_at (INT): Start index (0-based).
- auto_queue (BOOLEAN): If enabled, triggers next queue automatically.
- sort_by (Name|Date|Random): Sorting method.
- order_by (A-Z|Z-A): Sort order.

Inputs (optional)
- image_count (INT): UI display only.
- progress (FLOAT): UI display only (0.0 - 1.0).

Outputs
- image_path (STRING): Full path of the selected image file.
- image_count (INT): Total count of matching files.

### FolderBatch Load Image
Load an image file and output it as IMAGE and MASK.

Inputs (required)
- image_path (STRING): Full path to the image file.

Outputs
- image (IMAGE): Loaded image.
- mask (MASK): Alpha-derived mask if present, otherwise empty mask.

### FolderBatch Sync Queue
Queue synchronized items across image, video, text, and audio sources.

Inputs (required)
- common_folder (STRING): Shared folder used when a per-media folder is blank.
- sync_mode (By Name|By Order): Match by basename or by sorted index.
- missing_policy (Skip|Error|Empty): Skip incomplete sets, stop on mismatch, or output empty paths.
- start_at (INT): Start index (0-based).
- auto_queue (BOOLEAN): If enabled, triggers next queue automatically.
- sort_by (Name|Date|Random): Sorting method.
- order_by (A-Z|Z-A): Sort order.
- use_image / use_video / use_text / use_audio (BOOLEAN): Enable each media type.
- image_folder / video_folder / text_folder / audio_folder (STRING): Optional per-media folders.
- image_extension / video_extension / text_extension / audio_extension (STRING): Glob pattern(s) per media.

Inputs (optional)
- item_count (INT): UI display only.
- progress (FLOAT): UI display only (0.0 - 1.0).

Outputs
- base_name (STRING): Matched basename or first available basename in order mode.
- image_path (STRING): Selected image path or empty string.
- video_path (STRING): Selected video path or empty string.
- text_path (STRING): Selected text path or empty string.
- audio_path (STRING): Selected audio path or empty string.
- item_count (INT): Total synchronized item count.

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

Image batch:
1) FolderBatch Image Queue -> image_path
2) FolderBatch Load Image -> image, mask
3) Connect image to your processing nodes

Sync batch:
1) FolderBatch Sync Queue -> base_name, image_path, video_path, text_path, audio_path
2) Connect the paths you need into FolderBatch Load Image / Load Video Frames / Load Text / Load Audio
3) Process each synchronized item set

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
音声ファイルを読み込み、AUDIOと長さを出力します。

入力（必須）
- audio_path (STRING): 音声ファイルのフルパス

出力
- audio (AUDIO): 読み込んだ音声データ
- duration_float (FLOAT): 音声の長さ（秒）
- duration_int (INT): 四捨五入した音声の長さ（秒）

### FolderBatch Image Queue
フォルダ内の画像を1つずつキューに流します。

入力（必須）
- folder (STRING): 対象フォルダのパス
- extension (STRING): 拡張子グロブ。複数指定可。既定値 `*.png;*.jpg;*.jpeg;*.webp;*.bmp`
- start_at (INT): 開始インデックス（0始まり）
- auto_queue (BOOLEAN): 有効なら自動で次をキュー
- sort_by (Name|Date|Random): 並び順の基準
- order_by (A-Z|Z-A): 並び順の向き

入力（任意）
- image_count (INT): UI表示用
- progress (FLOAT): UI表示用（0.0 - 1.0）

出力
- image_path (STRING): 選択された画像のフルパス
- image_count (INT): 対象ファイルの総数

### FolderBatch Load Image
画像ファイルを読み込み、IMAGEとMASKで出力します。

入力（必須）
- image_path (STRING): 画像ファイルのフルパス

出力
- image (IMAGE): 読み込んだ画像
- mask (MASK): アルファ由来のマスク。なければ空マスク

### FolderBatch Sync Queue
画像・動画・テキスト・音声を同期してキューに流します。

入力（必須）
- common_folder (STRING): 個別フォルダが空のときに使う共通フォルダ
- sync_mode (By Name|By Order): ベース名一致か、ソート順一致か
- missing_policy (Skip|Error|Empty): 欠損セットをスキップ、エラー停止、空パス出力
- start_at (INT): 開始インデックス（0始まり）
- auto_queue (BOOLEAN): 有効なら自動で次をキュー
- sort_by (Name|Date|Random): 並び順の基準
- order_by (A-Z|Z-A): 並び順の向き
- use_image / use_video / use_text / use_audio (BOOLEAN): 媒体ごとの使用有無
- image_folder / video_folder / text_folder / audio_folder (STRING): 媒体ごとの個別フォルダ
- image_extension / video_extension / text_extension / audio_extension (STRING): 媒体ごとの拡張子グロブ

入力（任意）
- item_count (INT): UI表示用
- progress (FLOAT): UI表示用（0.0 - 1.0）

出力
- base_name (STRING): 一致したベース名。順番同期では最初に見つかった名前
- image_path (STRING): 対応画像のパス。なければ空文字
- video_path (STRING): 対応動画のパス。なければ空文字
- text_path (STRING): 対応テキストのパス。なければ空文字
- audio_path (STRING): 対応音声のパス。なければ空文字
- item_count (INT): 同期対象の総数

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

画像バッチ:
1) FolderBatch Image Queue -> image_path
2) FolderBatch Load Image -> image, mask
3) 画像処理ノードに接続

同期バッチ:
1) FolderBatch Sync Queue -> base_name, image_path, video_path, text_path, audio_path
2) 必要な path だけ FolderBatch Load Image / Load Video Frames / Load Text / Load Audio に接続
3) 同期された1件ずつを処理
