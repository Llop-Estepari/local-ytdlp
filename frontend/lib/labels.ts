import type { TFunction } from "@/lib/i18n";
import type { FormatOption } from "@/types/api";

export function formatLabel(format: FormatOption, t: TFunction): string {
  switch (format.id) {
    case "mp4":
      return t("format.mp4");
    case "webm":
      return t("format.webm");
    case "mp3":
      return t("format.mp3");
    case "m4a":
      return t("format.m4a");
    case "best":
      return t("format.best");
    default:
      return format.label;
  }
}

export function qualityLabel(
  formatId: string,
  qualityId: string,
  t: TFunction,
): string {
  if (formatId === "mp3") {
    return `${qualityId} kbps`;
  }
  switch (qualityId) {
    case "best":
      return t("quality.best");
    case "2160":
      return t("quality.2160");
    case "1440":
      return t("quality.1440");
    case "1080":
      return t("quality.1080");
    case "720":
      return t("quality.720");
    case "480":
      return t("quality.480");
    case "360":
      return t("quality.360");
    default:
      return qualityId;
  }
}

const ROOT_LABELS: Record<string, Parameters<TFunction>[0]> = {
  downloads: "root.downloads",
  descargas: "root.downloads",
  videos: "root.videos",
  "vídeos": "root.videos",
  music: "root.music",
  "música": "root.music",
  desktop: "root.desktop",
  escritorio: "root.desktop",
};

export function rootLabel(label: string, t: TFunction): string {
  const key = ROOT_LABELS[label.trim().toLowerCase()];
  return key ? t(key) : label;
}
