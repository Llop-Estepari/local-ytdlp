import type { DownloadFormat } from "@/types/api";

export interface QueueItem {
  key: string;
  url: string;
  title: string;
  format: DownloadFormat;
  quality: string;
  formatText: string;
  qualityText: string;
  destination: string;
  playlistItem: number | null;
  numbered: boolean;
}
