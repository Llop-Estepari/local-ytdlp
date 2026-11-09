"use client";

import { useState } from "react";
import { RefreshCwIcon } from "lucide-animated";

import { useI18n } from "@/components/i18n-provider";
import { api } from "@/lib/api";
import { errorMessage } from "@/lib/errors";
import type { TFunction } from "@/lib/i18n";
import { cn } from "@/lib/utils";
import type { DependenciesResponse, UpdateCheckResponse } from "@/types/api";

interface DependencyFooterProps {
  dependencies: DependenciesResponse | null;
}

function updateLabel(result: UpdateCheckResponse, t: TFunction): string {
  const updates: string[] = [];
  if (result.ytdlp.update_available) {
    updates.push(`yt-dlp ${result.ytdlp.latest}`);
  }
  if (result.ffmpeg.update_available) {
    updates.push(`FFmpeg ${result.ffmpeg.latest}`);
  }
  if (updates.length > 0) {
    return t("footer.updateAvailable", { tools: updates.join(", ") });
  }
  if (result.ytdlp.error || result.ffmpeg.error) {
    return t("footer.checkFailed");
  }
  return t("footer.upToDate");
}

export function DependencyFooter({ dependencies }: DependencyFooterProps) {
  const { locale, t } = useI18n();
  const [checking, setChecking] = useState(false);
  const [result, setResult] = useState<UpdateCheckResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const check = async () => {
    if (checking) {
      return;
    }
    setChecking(true);
    setError(null);
    try {
      setResult(await api.checkUpdates());
    } catch (caught) {
      setError(errorMessage(caught, locale));
    } finally {
      setChecking(false);
    }
  };

  const ytdlp = dependencies
    ? dependencies.ytdlp.installed
      ? `yt-dlp ${dependencies.ytdlp.version ?? "—"}`
      : t("footer.notInstalled", { tool: "yt-dlp" })
    : "yt-dlp —";
  const ffmpeg = dependencies
    ? dependencies.ffmpeg.installed
      ? `FFmpeg ${dependencies.ffmpeg.version ?? "—"}`
      : t("footer.notInstalled", { tool: "FFmpeg" })
    : "FFmpeg —";

  return (
    <footer className="flex flex-wrap items-center justify-center gap-x-2.5 gap-y-1 px-5 pb-5 pt-2 text-[11px] text-muted-foreground/70">
      <span className={cn(!dependencies?.ytdlp.installed && dependencies && "text-destructive/80")}>
        {ytdlp}
      </span>
      <span aria-hidden="true">·</span>
      <span className={cn(!dependencies?.ffmpeg.installed && dependencies && "text-destructive/80")}>
        {ffmpeg}
      </span>
      <span aria-hidden="true">·</span>
      <button
        type="button"
        onClick={() => {
          void check();
        }}
        disabled={checking}
        className="inline-flex items-center gap-1 transition-colors hover:text-foreground disabled:opacity-50"
      >
        <RefreshCwIcon
          size={12}
          animateOnHover={!checking}
          className={cn("inline-flex", checking && "animate-spin")}
        />
        {t("footer.check")}
      </button>
      {result || error ? (
        <span aria-live="polite" className="basis-full text-center">
          {error ?? (result ? updateLabel(result, t) : null)}
        </span>
      ) : null}
    </footer>
  );
}
