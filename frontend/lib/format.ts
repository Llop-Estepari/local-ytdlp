import type { MessageKey } from "@/lib/i18n";
import type { FormatOption } from "@/types/api";

const UNITS = ["B", "KB", "MB", "GB", "TB"] as const;

export function formatBytes(value: number | null | undefined): string | null {
  if (value == null || !Number.isFinite(value) || value < 0) {
    return null;
  }
  if (value < 1024) {
    return `${Math.round(value)} B`;
  }

  let amount = value;
  let unit = 0;
  while (amount >= 1024 && unit < UNITS.length - 1) {
    amount /= 1024;
    unit += 1;
  }

  const digits = amount >= 100 ? 0 : amount >= 10 ? 1 : 2;
  return `${amount.toFixed(digits)} ${UNITS[unit]}`;
}

export function formatSpeed(value: number | null | undefined): string | null {
  const formatted = formatBytes(value);
  return formatted ? `${formatted}/s` : null;
}

export function formatDuration(value: number | null | undefined): string | null {
  if (value == null || !Number.isFinite(value) || value < 0) {
    return null;
  }
  const total = Math.round(value);
  const hours = Math.floor(total / 3600);
  const minutes = Math.floor((total % 3600) / 60);
  const seconds = total % 60;

  if (hours > 0) {
    return `${hours}:${String(minutes).padStart(2, "0")}:${String(seconds).padStart(2, "0")}`;
  }
  return `${minutes}:${String(seconds).padStart(2, "0")}`;
}

export function formatEta(value: number | null | undefined): string | null {
  return formatDuration(value);
}

export function formatPercent(value: number | null | undefined): string {
  if (value == null || !Number.isFinite(value)) {
    return "—";
  }
  return `${Math.round(value)}%`;
}

export function validateUrlInput(value: string): MessageKey | null {
  const url = value.trim();
  if (!url) {
    return "url.error.empty";
  }
  let parsed: URL;
  try {
    parsed = new URL(url);
  } catch {
    return "url.error.invalid";
  }
  if (parsed.protocol !== "http:" && parsed.protocol !== "https:") {
    return "url.error.protocol";
  }
  if (!parsed.hostname) {
    return "url.error.host";
  }
  return null;
}

export function pickDefaultFormat(formats: FormatOption[]): FormatOption {
  const preference = ["mp4", "webm", "best", "mp3", "m4a"];
  for (const id of preference) {
    const match = formats.find((format) => format.id === id);
    if (match) {
      return match;
    }
  }
  return formats[0];
}

export function pickDefaultPlaylistFormat(formats: FormatOption[]): FormatOption {
  const preference = ["mp3", "m4a", "mp4", "webm", "best"];
  for (const id of preference) {
    const match = formats.find((format) => format.id === id);
    if (match) {
      return match;
    }
  }
  return formats[0];
}

export function shortenPath(path: string, maxLength = 52): string {
  if (path.length <= maxLength) {
    return path;
  }
  const parts = path.split(/[\\/]/).filter(Boolean);
  if (parts.length <= 2) {
    return path;
  }
  const separator = path.includes("\\") ? "\\" : "/";
  return `…${separator}${parts.slice(-2).join(separator)}`;
}
