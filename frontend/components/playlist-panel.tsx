"use client";

import {
  ArrowLeftIcon,
  ChevronDownIcon,
  DownloadIcon,
  FolderOpenIcon,
} from "lucide-animated";

import { useI18n } from "@/components/i18n-provider";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { formatDuration, shortenPath } from "@/lib/format";
import { formatLabel, qualityLabel } from "@/lib/labels";
import type { FormatOption, PlaylistEntry, PlaylistInfo } from "@/types/api";

interface PlaylistPanelProps {
  playlist: PlaylistInfo;
  formatId: string;
  qualityId: string;
  destination: string;
  notice: string | null;
  onChangeUrl: () => void;
  onFormatChange: (formatId: string) => void;
  onQualityChange: (qualityId: string) => void;
  onChooseDestination: () => void;
  onDownload: () => void;
  onChooseEntry: (entry: PlaylistEntry) => void;
}

export function PlaylistPanel({
  playlist,
  formatId,
  qualityId,
  destination,
  notice,
  onChangeUrl,
  onFormatChange,
  onQualityChange,
  onChooseDestination,
  onDownload,
  onChooseEntry,
}: PlaylistPanelProps) {
  const { t } = useI18n();
  const currentFormat: FormatOption =
    playlist.formats.find((format) => format.id === formatId) ??
    playlist.formats[0];
  const countLabel = t("playlist.count", {
    count: playlist.entry_count,
  });
  const meta = [countLabel, playlist.extractor].filter(Boolean).join(" · ");
  const previewEntries = playlist.entries.slice(0, 50);
  const hiddenCount = playlist.entry_count - previewEntries.length;

  return (
    <div className="animate-fade-up space-y-5">
      {playlist.thumbnail ? (
        // eslint-disable-next-line @next/next/no-img-element
        <img
          src={playlist.thumbnail}
          alt=""
          loading="lazy"
          referrerPolicy="no-referrer"
          className="max-h-52 w-full rounded-xl border object-cover"
        />
      ) : null}

      <div className="flex items-start gap-3">
        <div className="min-w-0 flex-1 space-y-1">
          <h2 className="line-clamp-2 text-lg font-medium leading-snug tracking-tight">
            {playlist.title}
          </h2>
          <p className="text-xs text-muted-foreground">{meta}</p>
        </div>
        <Button
          type="button"
          variant="ghost"
          size="icon"
          onClick={onChangeUrl}
          aria-label={t("common.changeLink")}
          title={t("common.changeLink")}
          className="-mr-2 h-8 w-8 shrink-0 text-muted-foreground"
        >
          <ArrowLeftIcon size={16} />
        </Button>
      </div>

      <div className="overflow-hidden rounded-xl border">
        <div className="max-h-44 divide-y divide-border overflow-y-auto">
          {previewEntries.map((entry) => {
            const duration = formatDuration(entry.duration);
            return (
              <div
                key={entry.index}
                className="flex items-center gap-3 px-3 py-2 text-sm"
              >
                <span className="w-6 shrink-0 text-right text-xs tabular-nums text-muted-foreground">
                  {entry.index}
                </span>
                <span className="min-w-0 flex-1 truncate">{entry.title}</span>
                {duration ? (
                  <span className="shrink-0 text-xs tabular-nums text-muted-foreground">
                    {duration}
                  </span>
                ) : null}
                <Button
                  type="button"
                  variant="ghost"
                  size="icon"
                  className="-mr-1 h-7 w-7 shrink-0 text-muted-foreground"
                  onClick={() => onChooseEntry(entry)}
                  aria-label={t("playlist.downloadSong", { title: entry.title })}
                  title={t("playlist.downloadThisSong")}
                >
                  <DownloadIcon size={14} />
                </Button>
              </div>
            );
          })}
        </div>
        {hiddenCount > 0 ? (
          <p className="border-t px-3 py-2 text-xs text-muted-foreground">
            {t("playlist.more", { count: hiddenCount })}
          </p>
        ) : null}
      </div>

      <div className="grid gap-3 sm:grid-cols-2">
        <div className="space-y-1.5">
          <label className="text-[11px] font-medium uppercase tracking-[0.12em] text-muted-foreground">
            {t("common.format")}
          </label>
          <Select value={formatId} onValueChange={onFormatChange}>
            <SelectTrigger aria-label={t("common.format")}>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {playlist.formats.map((format) => (
                <SelectItem key={format.id} value={format.id}>
                  {formatLabel(format, t)}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div className="space-y-1.5">
          <label className="text-[11px] font-medium uppercase tracking-[0.12em] text-muted-foreground">
            {t("common.quality")}
          </label>
          <Select value={qualityId} onValueChange={onQualityChange}>
            <SelectTrigger aria-label={t("common.quality")}>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {currentFormat.qualities.map((quality) => (
                <SelectItem key={quality.id} value={quality.id}>
                  {qualityLabel(currentFormat.id, quality.id, t)}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      <button
        type="button"
        onClick={onChooseDestination}
        className="flex w-full items-center gap-2 rounded-lg border border-border px-3 py-2.5 text-left text-sm transition-colors hover:bg-accent"
      >
        <FolderOpenIcon
          size={16}
          className="shrink-0 text-muted-foreground"
        />
        <span className="shrink-0 text-muted-foreground">
          {t("common.saveIn")}
        </span>
        <span className="truncate text-foreground/90" title={destination}>
          {destination ? shortenPath(destination) : t("common.selectFolder")}
        </span>
        <ChevronDownIcon
          size={16}
          className="ml-auto shrink-0 text-muted-foreground"
        />
      </button>

      {notice ? (
        <p className="text-[13px] text-muted-foreground" role="status">
          {notice}
        </p>
      ) : null}

      <Button
        type="button"
        size="lg"
        className="w-full"
        onClick={onDownload}
        disabled={!destination}
      >
        {t("playlist.addToQueue", { count: playlist.entry_count })}
      </Button>
    </div>
  );
}
