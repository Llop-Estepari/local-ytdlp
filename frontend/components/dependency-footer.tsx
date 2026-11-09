"use client";

import { useState } from "react";
import { RefreshCwIcon } from "lucide-animated";

import { useI18n } from "@/components/i18n-provider";
import { LoadingIcon } from "@/components/ui/loading-icon";
import { api } from "@/lib/api";
import { translateApiText } from "@/lib/api-messages";
import { errorHint, errorMessage } from "@/lib/errors";
import type { TFunction } from "@/lib/i18n";
import { cn } from "@/lib/utils";
import type {
  DependenciesResponse,
  ToolName,
  UpdateCheckResponse,
} from "@/types/api";

interface DependencyFooterProps {
  dependencies: DependenciesResponse | null;
  appVersion?: string | null;
  onDependenciesChange?: (dependencies: DependenciesResponse) => void;
}

interface UpdateNotice {
  kind: "success" | "error";
  message: string;
  hint?: string | null;
}

function toolLabel(tool: ToolName): string {
  return tool === "ytdlp" ? "yt-dlp" : "FFmpeg";
}

function updateLabel(result: UpdateCheckResponse, t: TFunction): string {
  const updates: string[] = [];
  if (result.app.update_available) {
    updates.push(`Vidora ${result.app.latest}`);
  }
  if (result.ytdlp.update_available) {
    updates.push(`yt-dlp ${result.ytdlp.latest}`);
  }
  if (result.ffmpeg.update_available) {
    updates.push(`FFmpeg ${result.ffmpeg.latest}`);
  }
  if (updates.length > 0) {
    return t("footer.updateAvailable", { tools: updates.join(", ") });
  }
  if (result.app.error || result.ytdlp.error || result.ffmpeg.error) {
    return t("footer.checkFailed");
  }
  return t("footer.upToDate");
}

export function DependencyFooter({
  dependencies,
  appVersion,
  onDependenciesChange,
}: DependencyFooterProps) {
  const { locale, t } = useI18n();
  const [checking, setChecking] = useState(false);
  const [updating, setUpdating] = useState<ToolName | null>(null);
  const [result, setResult] = useState<UpdateCheckResponse | null>(null);
  const [notice, setNotice] = useState<UpdateNotice | null>(null);
  const [error, setError] = useState<string | null>(null);

  const check = async () => {
    if (checking || updating) {
      return;
    }
    setChecking(true);
    setError(null);
    setNotice(null);
    try {
      setResult(await api.checkUpdates());
    } catch (caught) {
      setError(errorMessage(caught, locale));
    } finally {
      setChecking(false);
    }
  };

  const update = async (tool: ToolName) => {
    if (updating) {
      return;
    }
    setUpdating(tool);
    setError(null);
    setNotice(null);
    try {
      const response = await api.updateDependency(tool);
      onDependenciesChange?.(response.dependencies);
      if (response.check) {
        setResult(response.check);
      }
      if (response.updated) {
        setNotice({
          kind: "success",
          message: t("footer.updateDone", {
            tool: toolLabel(tool),
            version: response.version ?? "",
          }),
        });
      } else {
        const detail = response.hint ?? response.error;
        setNotice({
          kind: "error",
          message: t("footer.updateFailed", { tool: toolLabel(tool) }),
          hint: detail ? translateApiText(detail, locale) : null,
        });
      }
    } catch (caught) {
      setNotice({
        kind: "error",
        message: t("footer.updateFailed", { tool: toolLabel(tool) }),
        hint: errorHint(caught, locale) ?? errorMessage(caught, locale),
      });
    } finally {
      setUpdating(null);
    }
  };

  const available: ToolName[] = [];
  if (result?.ytdlp.update_available) {
    available.push("ytdlp");
  }
  if (result?.ffmpeg.update_available) {
    available.push("ffmpeg");
  }

  const app = `${t("app.title")} ${appVersion ?? "—"}`;
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
      <span className={cn(result?.app.update_available && "text-amber-500")}>
        {app}
      </span>
      <span aria-hidden="true">·</span>
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
        disabled={checking || updating !== null}
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
          {!error && available.length > 0 ? (
            <span className="ml-2 inline-flex flex-wrap items-center justify-center gap-1.5 align-middle">
              {available.map((tool) => (
                <button
                  key={tool}
                  type="button"
                  onClick={() => {
                    void update(tool);
                  }}
                  disabled={updating !== null}
                  className="inline-flex items-center gap-1 rounded-full border border-border/80 px-2 py-0.5 text-[10px] font-medium text-foreground/80 transition-colors hover:border-border hover:bg-accent hover:text-foreground disabled:opacity-50"
                >
                  {updating === tool ? <LoadingIcon size={10} /> : null}
                  {updating === tool
                    ? t("footer.updatingTool", { tool: toolLabel(tool) })
                    : t("footer.updateTool", { tool: toolLabel(tool) })}
                </button>
              ))}
            </span>
          ) : null}
        </span>
      ) : null}
      {notice ? (
        <span
          aria-live="polite"
          className={cn(
            "basis-full text-center",
            notice.kind === "error" ? "text-destructive" : "text-emerald-500",
          )}
        >
          {notice.message}
          {notice.hint ? (
            <span className="block text-muted-foreground/80">{notice.hint}</span>
          ) : null}
        </span>
      ) : null}
    </footer>
  );
}
