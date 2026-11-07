"use client";

import { AlertCircle, Check, FolderOpen, Loader2, X } from "lucide-react";

import { useI18n } from "@/components/i18n-provider";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import {
  formatBytes,
  formatEta,
  formatPercent,
  formatSpeed,
} from "@/lib/format";
import type { DownloadState } from "@/types/api";

interface ActiveToast {
  title: string;
  state: DownloadState;
  queueLength: number;
  cancelling: boolean;
}

interface ResultToast {
  kind: "completed" | "error" | "cancelled";
  title: string;
  message: string;
  hint?: string | null;
}

interface DownloadToastProps {
  active: ActiveToast | null;
  result: ResultToast | null;
  onCancel: () => void;
  onDismiss: () => void;
  onOpenFolder: () => void;
}

const STATUS_KEYS = {
  starting: "download.status.starting",
  downloading: "download.status.downloading",
  processing: "download.status.processing",
  completed: "download.status.completed",
  cancelled: "download.status.cancelled",
  error: "download.status.error",
} as const;

export function DownloadToast({
  active,
  result,
  onCancel,
  onDismiss,
  onOpenFolder,
}: DownloadToastProps) {
  if (!active && !result) {
    return null;
  }

  return (
    <div className="pointer-events-none fixed inset-x-0 top-4 z-[60] flex justify-center px-4">
      <div
        className="pointer-events-auto w-full max-w-md animate-toast-in rounded-xl border bg-card p-4 shadow-2xl"
        role="status"
        aria-live="polite"
      >
        {active ? (
          <ActiveProgress
            active={active}
            onCancel={onCancel}
          />
        ) : result ? (
          <ResultMessage
            result={result}
            onDismiss={onDismiss}
            onOpenFolder={onOpenFolder}
          />
        ) : null}
      </div>
    </div>
  );
}

function ActiveProgress({
  active,
  onCancel,
}: {
  active: ActiveToast;
  onCancel: () => void;
}) {
  const { t } = useI18n();
  const { state } = active;
  const speed = formatSpeed(state.speed);
  const downloaded = formatBytes(state.downloaded_bytes);
  const total = formatBytes(state.total_bytes);
  const eta = formatEta(state.eta);
  const bytesLabel = downloaded
    ? total
      ? `${downloaded} / ${total}`
      : downloaded
    : null;
  const statusLabel =
    state.status === "processing"
      ? t("common.processingFfmpeg")
      : t(STATUS_KEYS[state.status]);

  return (
    <div className="space-y-3">
      <div className="flex items-start gap-3">
        <Loader2
          className="mt-0.5 h-4 w-4 shrink-0 animate-spin text-muted-foreground"
          strokeWidth={1.8}
        />
        <div className="min-w-0 flex-1 space-y-0.5">
          <p className="text-[11px] font-medium uppercase tracking-[0.12em] text-muted-foreground">
            {statusLabel}
            {active.queueLength > 0
              ? ` · ${t("toast.queueCount", { count: active.queueLength })}`
              : ""}
          </p>
          <p className="truncate text-sm font-medium" title={active.title}>
            {active.title}
          </p>
        </div>
        <span className="shrink-0 text-lg font-medium tabular-nums tracking-tight">
          {formatPercent(state.percent)}
        </span>
        <Button
          type="button"
          variant="ghost"
          size="icon"
          className="-mr-2 -mt-1 h-8 w-8 shrink-0 text-muted-foreground"
          onClick={onCancel}
          disabled={active.cancelling}
          aria-label={t("toast.cancelAria")}
          title={t("toast.cancelTitle")}
        >
          {active.cancelling ? (
            <Loader2 className="h-3.5 w-3.5 animate-spin" strokeWidth={1.8} />
          ) : (
            <X className="h-3.5 w-3.5" strokeWidth={1.8} />
          )}
        </Button>
      </div>

      <Progress value={state.percent} />

      <div className="flex flex-wrap items-center justify-between gap-x-4 gap-y-1 text-[11px] tabular-nums text-muted-foreground">
        <span>{speed ?? "—"}</span>
        <span>{bytesLabel ?? "—"}</span>
        <span>
          {state.status === "processing"
            ? t("common.processing")
            : eta
              ? t("common.eta", { eta })
              : "—"}
        </span>
      </div>
    </div>
  );
}

function ResultMessage({
  result,
  onDismiss,
  onOpenFolder,
}: {
  result: ResultToast;
  onDismiss: () => void;
  onOpenFolder: () => void;
}) {
  const { t } = useI18n();
  const completed = result.kind === "completed";
  const cancelled = result.kind === "cancelled";
  const title =
    result.kind === "completed"
      ? t("toast.completed")
      : result.kind === "cancelled"
        ? t("toast.cancelled")
        : t("toast.failed");

  return (
    <div className="flex items-start gap-3">
      <span
        className={
          completed || cancelled
            ? "mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-full border border-border"
            : "mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-full border border-border text-destructive"
        }
      >
        {completed ? (
          <Check className="h-3.5 w-3.5" strokeWidth={2} />
        ) : cancelled ? (
          <X className="h-3.5 w-3.5" strokeWidth={2} />
        ) : (
          <AlertCircle className="h-3.5 w-3.5" strokeWidth={2} />
        )}
      </span>
      <div className="min-w-0 flex-1 space-y-0.5">
        <p className="text-sm font-medium">{title}</p>
        <p className="truncate text-xs text-muted-foreground" title={result.title}>
          {result.title}
        </p>
        <p className="break-all text-xs text-muted-foreground/90">
          {result.message}
        </p>
        {result.hint ? (
          <p className="text-xs text-destructive">{result.hint}</p>
        ) : null}
        {completed ? (
          <Button
            type="button"
            variant="outline"
            size="sm"
            className="mt-2 h-7 px-2.5 text-xs"
            onClick={onOpenFolder}
          >
            <FolderOpen className="h-3 w-3" strokeWidth={1.8} />
            {t("success.openFolder")}
          </Button>
        ) : null}
      </div>
      <Button
        type="button"
        variant="ghost"
        size="icon"
        className="-mr-2 -mt-1 h-8 w-8 shrink-0 text-muted-foreground"
        onClick={onDismiss}
        aria-label={t("toast.dismissAria")}
        title={t("toast.closeTitle")}
      >
        <X className="h-3.5 w-3.5" strokeWidth={1.8} />
      </Button>
    </div>
  );
}
