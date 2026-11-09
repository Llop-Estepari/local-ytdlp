export type DownloadFormat = "mp4" | "webm" | "mp3" | "m4a" | "best";

export type DownloadStatus =
  | "starting"
  | "downloading"
  | "processing"
  | "completed"
  | "cancelled"
  | "error";

export interface QualityOption {
  id: string;
  label: string;
}

export interface FormatOption {
  id: DownloadFormat;
  label: string;
  kind: "video" | "audio";
  qualities: QualityOption[];
}

export interface MediaInfo {
  kind: "media";
  url: string;
  title: string;
  duration: number | null;
  thumbnail: string | null;
  extractor: string | null;
  formats: FormatOption[];
}

export interface PlaylistEntry {
  index: number;
  title: string;
  duration: number | null;
  thumbnail: string | null;
}

export interface PlaylistInfo {
  kind: "playlist";
  url: string;
  title: string;
  entry_count: number;
  thumbnail: string | null;
  extractor: string | null;
  formats: FormatOption[];
  entries: PlaylistEntry[];
}

export type AnalyzeResult = MediaInfo | PlaylistInfo;

export interface DownloadState {
  id: string;
  url: string;
  format: DownloadFormat;
  quality: string;
  destination: string;
  status: DownloadStatus;
  percent: number | null;
  downloaded_bytes: number | null;
  total_bytes: number | null;
  speed: number | null;
  eta: number | null;
  filename: string | null;
  filepath: string | null;
  playlist: boolean;
  playlist_index: number | null;
  playlist_count: number | null;
  current_title: string | null;
  item_percent: number | null;
  file_count: number;
  error: string | null;
  error_hint: string | null;
  created_at: string;
  updated_at: string;
}

export interface RootEntry {
  path: string;
  label: string;
}

export interface ConfigResponse {
  app_version: string;
  default_destination: string;
  roots: RootEntry[];
  allow_network: boolean;
}

export interface ToolStatus {
  installed: boolean;
  version: string | null;
  path: string | null;
}

export interface DependenciesResponse {
  ok: boolean;
  ytdlp: ToolStatus;
  ffmpeg: ToolStatus;
}

export interface ToolUpdateStatus {
  installed: string | null;
  latest: string | null;
  update_available: boolean | null;
  error: string | null;
}

export interface UpdateCheckResponse {
  app: AppUpdateStatus;
  ytdlp: ToolUpdateStatus;
  ffmpeg: ToolUpdateStatus;
  checked_at: string;
}

export interface AppUpdateStatus {
  installed: string;
  latest: string | null;
  update_available: boolean | null;
  error: string | null;
}

export type ToolName = "ytdlp" | "ffmpeg";

export interface DependencyUpdateResponse {
  tool: ToolName;
  updated: boolean;
  version: string | null;
  error: string | null;
  hint: string | null;
  dependencies: DependenciesResponse;
  check: UpdateCheckResponse | null;
}

export interface DirectoryEntry {
  name: string;
  path: string;
}

export interface DirectoryListing {
  path: string;
  parent: string | null;
  directories: DirectoryEntry[];
  writable: boolean;
}

export interface StartDownloadInput {
  url: string;
  format: DownloadFormat;
  quality: string;
  destination: string;
  playlist?: boolean;
  playlist_count?: number | null;
  playlist_item?: number | null;
  numbered?: boolean;
}
