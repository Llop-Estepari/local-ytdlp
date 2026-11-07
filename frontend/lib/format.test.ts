import { describe, expect, it } from "vitest";

import {
  formatBytes,
  formatDuration,
  formatEta,
  formatPercent,
  formatSpeed,
  pickDefaultFormat,
  pickDefaultPlaylistFormat,
  shortenPath,
  validateUrlInput,
} from "@/lib/format";
import type { FormatOption } from "@/types/api";

const format = (
  id: FormatOption["id"],
  qualities: string[] = ["best"],
): FormatOption => ({
  id,
  label: id,
  kind: id === "mp3" || id === "m4a" ? "audio" : "video",
  qualities: qualities.map((quality) => ({ id: quality, label: quality })),
});

describe("formatBytes", () => {
  it("formats bytes and units", () => {
    expect(formatBytes(0)).toBe("0 B");
    expect(formatBytes(512)).toBe("512 B");
    expect(formatBytes(1024)).toBe("1.00 KB");
    expect(formatBytes(1024 * 1024 * 5)).toBe("5.00 MB");
    expect(formatBytes(1024 * 1024 * 1024 * 2.5)).toBe("2.50 GB");
  });

  it("returns null for invalid values", () => {
    expect(formatBytes(null)).toBeNull();
    expect(formatBytes(undefined)).toBeNull();
    expect(formatBytes(-1)).toBeNull();
    expect(formatBytes(Number.NaN)).toBeNull();
  });
});

describe("formatSpeed", () => {
  it("appends per second", () => {
    expect(formatSpeed(2048)).toBe("2.00 KB/s");
    expect(formatSpeed(null)).toBeNull();
  });
});

describe("formatDuration", () => {
  it("formats minutes and hours", () => {
    expect(formatDuration(0)).toBe("0:00");
    expect(formatDuration(65)).toBe("1:05");
    expect(formatDuration(3661)).toBe("1:01:01");
  });

  it("rejects invalid values", () => {
    expect(formatDuration(-1)).toBeNull();
    expect(formatDuration(null)).toBeNull();
  });
});

describe("formatEta", () => {
  it("reuses duration formatting", () => {
    expect(formatEta(90)).toBe("1:30");
    expect(formatEta(null)).toBeNull();
  });
});

describe("formatPercent", () => {
  it("rounds and falls back", () => {
    expect(formatPercent(0)).toBe("0%");
    expect(formatPercent(36.4)).toBe("36%");
    expect(formatPercent(100)).toBe("100%");
    expect(formatPercent(null)).toBe("—");
  });
});

describe("validateUrlInput", () => {
  it("accepts http and https", () => {
    expect(validateUrlInput("https://example.com/video")).toBeNull();
    expect(validateUrlInput("  http://example.com  ")).toBeNull();
  });

  it("rejects empty, malformed and non-http urls", () => {
    expect(validateUrlInput("")).toBe("url.error.empty");
    expect(validateUrlInput("no es una url")).toBe("url.error.invalid");
    expect(validateUrlInput("file:///etc/passwd")).toBe("url.error.protocol");
    expect(validateUrlInput("ftp://example.com/video")).toBe(
      "url.error.protocol",
    );
  });
});

describe("pickDefaultFormat", () => {
  it("prefers mp4, then webm and best", () => {
    expect(
      pickDefaultFormat([format("mp3"), format("webm"), format("mp4")]).id,
    ).toBe("mp4");
    expect(pickDefaultFormat([format("mp3"), format("webm")]).id).toBe("webm");
    expect(pickDefaultFormat([format("mp3"), format("best")]).id).toBe("best");
  });

  it("falls back through the preference order", () => {
    expect(pickDefaultFormat([format("m4a"), format("mp3")]).id).toBe("mp3");
    expect(pickDefaultFormat([format("m4a")]).id).toBe("m4a");
  });
});

describe("pickDefaultPlaylistFormat", () => {
  it("prefers audio formats for playlists", () => {
    expect(
      pickDefaultPlaylistFormat([format("mp4"), format("m4a"), format("mp3")]).id,
    ).toBe("mp3");
    expect(pickDefaultPlaylistFormat([format("mp4"), format("m4a")]).id).toBe(
      "m4a",
    );
  });

  it("falls back to video or the first format", () => {
    expect(pickDefaultPlaylistFormat([format("webm"), format("mp4")]).id).toBe(
      "mp4",
    );
    expect(pickDefaultPlaylistFormat([format("best")]).id).toBe("best");
  });
});

describe("shortenPath", () => {
  it("keeps short paths unchanged", () => {
    expect(shortenPath("/home/user/Downloads")).toBe("/home/user/Downloads");
  });

  it("shortens long paths to the last segments", () => {
    const long = "/home/user/aaaaaaaaaa/bbbbbbbbbb/cccccccccc/dddddddddd/Downloads";
    expect(shortenPath(long, 30)).toBe("…/dddddddddd/Downloads");
  });
});
