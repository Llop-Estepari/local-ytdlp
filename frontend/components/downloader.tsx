"use client";

import { ListIcon } from "lucide-animated";
import { useCallback, useEffect, useRef, useState } from "react";

import { Button } from "@/components/ui/button";
import { DependencyFooter } from "@/components/dependency-footer";
import { DependencyWarning } from "@/components/dependency-warning";
import { DownloadOptionsDialog } from "@/components/download-options-dialog";
import { DownloadToast } from "@/components/download-toast";
import { ErrorPanel } from "@/components/error-panel";
import { FolderDialog } from "@/components/folder-dialog";
import { useI18n } from "@/components/i18n-provider";
import { Logo } from "@/components/logo";
import { PlaylistPanel } from "@/components/playlist-panel";
import { QueueDialog } from "@/components/queue-dialog";
import { ThemeToggle } from "@/components/theme-toggle";
import { UrlForm } from "@/components/url-form";
import { useDownloadProgress } from "@/hooks/use-download-progress";
import { api } from "@/lib/api";
import { translateApiText } from "@/lib/api-messages";
import { errorHint, errorMessage } from "@/lib/errors";
import {
  formatDuration,
  pickDefaultFormat,
  pickDefaultPlaylistFormat,
  validateUrlInput,
} from "@/lib/format";
import { formatLabel, qualityLabel } from "@/lib/labels";
import type {
  AnalyzeResult,
  ConfigResponse,
  DependenciesResponse,
  DownloadFormat,
  DownloadState,
  MediaInfo,
  PlaylistEntry,
  PlaylistInfo,
} from "@/types/api";
import type { QueueItem } from "@/types/queue";

type Phase = "idle" | "analyzing" | "ready" | "error";

interface ErrorState {
  title: string;
  message: string;
  hint?: string | null;
  retryLabel?: string;
  retry: () => void;
  resetLabel?: string;
}

interface BootError {
  message: string;
  hint: string | null;
}

interface ActiveQueueItem extends QueueItem {
  downloadId: string;
  initial: DownloadState;
}

interface QueueResult {
  kind: "completed" | "error" | "cancelled";
  title: string;
  message: string;
  hint?: string | null;
  destination?: string | null;
}

type DownloadDialogState =
  | { kind: "playlist"; entry: PlaylistEntry; playlist: PlaylistInfo }
  | { kind: "media"; media: MediaInfo };

function joinMeta(parts: (string | null | undefined)[]): string {
  return parts.filter((part): part is string => Boolean(part)).join(" · ");
}

export function Downloader() {
  const { locale, t } = useI18n();
  const [phase, setPhase] = useState<Phase>("idle");
  const [url, setUrl] = useState("");
  const [media, setMedia] = useState<AnalyzeResult | null>(null);
  const [formatId, setFormatId] = useState<DownloadFormat>("mp4");
  const [qualityId, setQualityId] = useState("best");
  const [destination, setDestination] = useState("");
  const [config, setConfig] = useState<ConfigResponse | null>(null);
  const [dependencies, setDependencies] = useState<DependenciesResponse | null>(null);
  const [bootError, setBootError] = useState<BootError | null>(null);
  const [inlineError, setInlineError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [errorState, setErrorState] = useState<ErrorState | null>(null);
  const [folderOpen, setFolderOpen] = useState(false);
  const [queue, setQueue] = useState<QueueItem[]>([]);
  const [activeQueueItem, setActiveQueueItem] =
    useState<ActiveQueueItem | null>(null);
  const [queueState, setQueueState] = useState<DownloadState | null>(null);
  const [queueResult, setQueueResult] = useState<QueueResult | null>(null);
  const [queueCancelling, setQueueCancelling] = useState(false);
  const [queueOpen, setQueueOpen] = useState(false);
  const [queueClearing, setQueueClearing] = useState(false);
  const [downloadDialog, setDownloadDialog] =
    useState<DownloadDialogState | null>(null);
  const analyzingRef = useRef(false);
  const analyzeTokenRef = useRef(0);
  const queueStartRef = useRef(false);

  const loadConfig = useCallback(async () => {
    setBootError(null);
    try {
      const [nextConfig, nextDependencies] = await Promise.all([
        api.getConfig(),
        api.getDependencies(),
      ]);
      setConfig(nextConfig);
      setDependencies(nextDependencies);
      setDestination((current) => current || nextConfig.default_destination);
    } catch (caught) {
      setBootError({
        message: errorMessage(caught, locale),
        hint: errorHint(caught, locale),
      });
    }
  }, [locale]);

  useEffect(() => {
    void loadConfig();
  }, [loadConfig]);

  const analyze = useCallback(async (rawUrl: string) => {
    if (analyzingRef.current) {
      return;
    }
    const cleanUrl = rawUrl.trim();
    const validation = validateUrlInput(cleanUrl);
    if (validation) {
      setInlineError(t(validation));
      return;
    }

    analyzingRef.current = true;
    const token = ++analyzeTokenRef.current;
    setPhase("analyzing");
    setInlineError(null);
    setNotice(null);
    setErrorState(null);

    try {
      const info = await api.analyze(cleanUrl);
      if (token !== analyzeTokenRef.current) {
        return;
      }
      const preferred =
        info.kind === "playlist"
          ? pickDefaultPlaylistFormat(info.formats)
          : pickDefaultFormat(info.formats);
      setUrl(cleanUrl);
      setFormatId(preferred.id);
      setQualityId(preferred.qualities[0]?.id ?? "best");
      if (info.kind === "playlist") {
        setMedia(info);
        setDownloadDialog(null);
        setPhase("ready");
      } else {
        setMedia(null);
        setDownloadDialog({ kind: "media", media: info });
        setPhase("idle");
      }
    } catch (caught) {
      if (token !== analyzeTokenRef.current) {
        return;
      }
      setErrorState({
        title: t("downloader.analyzeTitle"),
        message: errorMessage(caught, locale),
        hint: errorHint(caught, locale),
        retry: () => {
          void analyze(cleanUrl);
        },
        resetLabel: t("common.changeUrl"),
      });
      setPhase("error");
    } finally {
      if (token === analyzeTokenRef.current) {
        analyzingRef.current = false;
      }
    }
  }, [locale, t]);

  const { state: queueLiveState } = useDownloadProgress(
    activeQueueItem?.downloadId ?? null,
  );

  useEffect(() => {
    if (activeQueueItem || queueStartRef.current || queue.length === 0) {
      return;
    }
    const next = queue[0];
    queueStartRef.current = true;
    setQueueResult(null);

    void (async () => {
      try {
        const state = await api.startDownload({
          url: next.url,
          format: next.format,
          quality: next.quality,
          destination: next.destination,
          playlist: false,
          playlist_item: next.playlistItem,
          numbered: next.numbered,
        });
        setQueue((current) => current.filter((item) => item.key !== next.key));
        setActiveQueueItem({
          ...next,
          downloadId: state.id,
          initial: state,
        });
        setQueueState(state);
      } catch (caught) {
        setQueue((current) => current.filter((item) => item.key !== next.key));
        setQueueResult({
          kind: "error",
          title: next.title,
          message: errorMessage(caught, locale),
          hint: errorHint(caught, locale),
        });
      } finally {
        queueStartRef.current = false;
      }
    })();
  }, [queue, activeQueueItem, locale]);

  useEffect(() => {
    if (
      !activeQueueItem ||
      !queueLiveState ||
      queueLiveState.id !== activeQueueItem.downloadId
    ) {
      return;
    }
    setQueueState(queueLiveState);

    if (queueLiveState.status === "completed") {
      setQueueResult({
        kind: "completed",
        title: activeQueueItem.title,
        message: queueLiveState.filename ?? t("toast.fileFallback"),
        destination: activeQueueItem.destination,
      });
      setActiveQueueItem(null);
      setQueueState(null);
      return;
    }
    if (queueLiveState.status === "cancelled") {
      setQueueResult({
        kind: "cancelled",
        title: activeQueueItem.title,
        message: t("downloader.cancelledNotice"),
      });
      setActiveQueueItem(null);
      setQueueState(null);
      return;
    }
    if (queueLiveState.status === "error") {
      setQueueResult({
        kind: "error",
        title: activeQueueItem.title,
        message: queueLiveState.error
          ? translateApiText(queueLiveState.error, locale)
          : t("downloader.failedMessage"),
        hint: queueLiveState.error_hint
          ? translateApiText(queueLiveState.error_hint, locale)
          : null,
      });
      setActiveQueueItem(null);
      setQueueState(null);
    }
  }, [queueLiveState, activeQueueItem, locale, t]);

  useEffect(() => {
    if (!queueResult) {
      return;
    }
    const timer = setTimeout(() => setQueueResult(null), 7000);
    return () => clearTimeout(timer);
  }, [queueResult]);

  const enqueueItems = useCallback(
    (items: QueueItem[]) => {
      setQueue((current) => {
        const existing = new Set(current.map((item) => item.key));
        if (activeQueueItem) {
          existing.add(activeQueueItem.key);
        }
        const additions = items.filter((item) => !existing.has(item.key));
        return additions.length ? [...current, ...additions] : current;
      });
      setQueueResult(null);
    },
    [activeQueueItem],
  );

  const enqueueDownload = useCallback(
    (entryFormat: DownloadFormat, entryQuality: string) => {
      const dialog = downloadDialog;
      if (!dialog) {
        return;
      }
      const target = destination || config?.default_destination || "";
      if (!target) {
        return;
      }
      const isPlaylist = dialog.kind === "playlist";
      const formats = isPlaylist
        ? dialog.playlist.formats
        : dialog.media.formats;
      const formatOption =
        formats.find((format) => format.id === entryFormat) ?? formats[0];
      if (!formatOption) {
        return;
      }
      const item: QueueItem = {
        key: isPlaylist
          ? `playlist:${dialog.playlist.url}:${dialog.entry.index}`
          : `media:${dialog.media.url}`,
        url: isPlaylist ? dialog.playlist.url : dialog.media.url,
        title: isPlaylist ? dialog.entry.title : dialog.media.title,
        format: formatOption.id,
        quality: entryQuality,
        formatText: formatLabel(formatOption, t),
        qualityText: qualityLabel(formatOption.id, entryQuality, t),
        destination: target,
        playlistItem: isPlaylist ? dialog.entry.index : null,
        numbered: false,
      };
      enqueueItems([item]);
      setDownloadDialog(null);
      if (!isPlaylist) {
        setPhase("idle");
        setMedia(null);
        setUrl("");
      }
    },
    [downloadDialog, destination, config, t, enqueueItems],
  );

  const enqueuePlaylist = useCallback(() => {
    if (!media || media.kind !== "playlist") {
      return;
    }
    const target = destination || config?.default_destination || "";
    if (!target) {
      return;
    }
    const formatOption =
      media.formats.find((format) => format.id === formatId) ??
      media.formats[0];
    if (!formatOption) {
      return;
    }
    const formatText = formatLabel(formatOption, t);
    const qualityText = qualityLabel(formatOption.id, qualityId, t);
    const known = new Map(
      media.entries.map((entry) => [entry.index, entry.title]),
    );
    const items: QueueItem[] = [];
    for (let index = 1; index <= media.entry_count; index += 1) {
      items.push({
        key: `playlist:${media.url}:${index}`,
        url: media.url,
        title: known.get(index) ?? t("playlist.itemLabel", { index }),
        format: formatOption.id,
        quality: qualityId,
        formatText,
        qualityText,
        destination: target,
        playlistItem: index,
        numbered: true,
      });
    }
    enqueueItems(items);
  }, [
    media,
    destination,
    config,
    formatId,
    qualityId,
    t,
    enqueueItems,
  ]);

  const closeDownloadDialog = () => {
    if (downloadDialog?.kind === "media") {
      setMedia(null);
    }
    setDownloadDialog(null);
  };

  const cancelQueueItem = async () => {
    if (!activeQueueItem || queueCancelling) {
      return;
    }
    setQueueCancelling(true);
    try {
      const state = await api.cancelDownload(activeQueueItem.downloadId);
      if (state.status === "cancelled") {
        setQueueResult({
          kind: "cancelled",
          title: activeQueueItem.title,
          message: t("downloader.cancelledNotice"),
        });
        setActiveQueueItem(null);
        setQueueState(null);
      } else if (state.status === "completed") {
        setQueueResult({
          kind: "completed",
          title: activeQueueItem.title,
          message: state.filename ?? t("toast.fileFallback"),
          destination: activeQueueItem.destination,
        });
        setActiveQueueItem(null);
        setQueueState(null);
      } else if (state.status === "error") {
        setQueueResult({
          kind: "error",
          title: activeQueueItem.title,
          message: state.error
            ? translateApiText(state.error, locale)
            : t("downloader.failedMessage"),
          hint: state.error_hint
            ? translateApiText(state.error_hint, locale)
            : null,
        });
        setActiveQueueItem(null);
        setQueueState(null);
      }
    } catch (caught) {
      setQueueResult({
        kind: "error",
        title: activeQueueItem.title,
        message: errorMessage(caught, locale),
        hint: errorHint(caught, locale),
      });
    } finally {
      setQueueCancelling(false);
    }
  };

  const openQueueFolder = async () => {
    const path = queueResult?.destination ?? destination;
    if (!path) {
      return;
    }
    try {
      await api.openFolder(path);
    } catch (caught) {
      setQueueResult((current) =>
        current
          ? { ...current, hint: errorMessage(caught, locale) }
          : current,
      );
    }
  };

  const queueProgress = activeQueueItem
    ? queueLiveState && queueLiveState.id === activeQueueItem.downloadId
      ? queueLiveState
      : (queueState ?? activeQueueItem.initial)
    : null;

  const removeQueueItem = (key: string) => {
    setQueue((current) => current.filter((item) => item.key !== key));
  };

  const clearQueue = async () => {
    if (queueClearing) {
      return;
    }
    setQueueClearing(true);
    const currentActive = activeQueueItem;
    setQueue([]);
    setActiveQueueItem(null);
    setQueueState(null);
    setQueueResult(null);
    try {
      if (currentActive) {
        await api.cancelDownload(currentActive.downloadId);
      }
    } catch (caught) {
      setQueueResult({
        kind: "error",
        title: t("queue.title"),
        message: errorMessage(caught, locale),
        hint: errorHint(caught, locale),
      });
    } finally {
      setQueueClearing(false);
      setQueueOpen(false);
    }
  };

  const changeUrl = () => {
    analyzeTokenRef.current += 1;
    analyzingRef.current = false;
    setPhase("idle");
    setMedia(null);
    setNotice(null);
    setInlineError(null);
    setErrorState(null);
    setDownloadDialog(null);
  };

  const reset = () => {
    analyzeTokenRef.current += 1;
    analyzingRef.current = false;
    setPhase("idle");
    setUrl("");
    setMedia(null);
    setNotice(null);
    setInlineError(null);
    setErrorState(null);
    setDownloadDialog(null);
  };

  const changeFormat = (nextFormatId: string) => {
    const nextFormat = media?.formats.find((item) => item.id === nextFormatId);
    if (!nextFormat) {
      return;
    }
    setFormatId(nextFormat.id);
    setQualityId(nextFormat.qualities[0]?.id ?? "best");
  };

  const goHome = () => {
    analyzeTokenRef.current += 1;
    analyzingRef.current = false;
    setPhase("idle");
    setUrl("");
    setMedia(null);
    setNotice(null);
    setInlineError(null);
    setErrorState(null);
    setDownloadDialog(null);
    setFolderOpen(false);
    setQueueOpen(false);
  };

  const showBootError = phase === "idle" && Boolean(bootError) && !config;
  const queueTotal = queue.length + (activeQueueItem ? 1 : 0);

  return (
    <div className="relative flex min-h-dvh flex-col">
      <header className="flex items-center justify-between px-5 py-5 sm:px-8">
        <button
          type="button"
          onClick={goHome}
          aria-label={t("nav.home")}
          title={t("nav.home")}
          className="rounded-lg transition-opacity hover:opacity-80 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring/60"
        >
          <Logo />
        </button>
        <div className="flex items-center gap-1">
          <Button
            type="button"
            variant="ghost"
            size="icon"
            className="relative text-muted-foreground hover:text-foreground"
            onClick={() => setQueueOpen(true)}
            aria-label={t("queue.open", { count: queueTotal })}
            title={t("queue.title")}
          >
            <ListIcon size={16} />
            {queueTotal > 0 ? (
              <span className="absolute -right-0.5 -top-0.5 flex h-4 min-w-4 items-center justify-center rounded-full bg-primary px-1 text-[10px] font-medium leading-none text-primary-foreground">
                {queueTotal > 99 ? "99+" : queueTotal}
              </span>
            ) : null}
          </Button>
          <ThemeToggle />
        </div>
      </header>

      <main className="flex flex-1 items-center justify-center px-5 pb-12 pt-2 sm:px-8">
        <div className="w-full max-w-xl">
          {showBootError && bootError ? (
            <ErrorPanel
              title={t("downloader.bootTitle")}
              message={bootError.message}
              hint={bootError.hint}
              retryLabel={t("downloader.retryConnection")}
              onRetry={() => {
                void loadConfig();
              }}
            />
          ) : null}

          {!showBootError && (phase === "idle" || phase === "analyzing") ? (
            <div className="animate-fade-up space-y-4">
              <UrlForm
                url={url}
                analyzing={phase === "analyzing"}
                error={inlineError}
                onUrlChange={(value) => {
                  setUrl(value);
                  if (inlineError) {
                    setInlineError(null);
                  }
                }}
                onSubmit={() => {
                  void analyze(url);
                }}
              />
              <DependencyWarning dependencies={dependencies} />
            </div>
          ) : null}

          {phase === "ready" && media && media.kind === "playlist" ? (
            <PlaylistPanel
              playlist={media}
              formatId={formatId}
              qualityId={qualityId}
              destination={destination}
              notice={notice}
              onChangeUrl={changeUrl}
              onFormatChange={changeFormat}
              onQualityChange={setQualityId}
              onChooseDestination={() => setFolderOpen(true)}
              onDownload={enqueuePlaylist}
              onChooseEntry={(entry) => {
                setDownloadDialog({
                  kind: "playlist",
                  entry,
                  playlist: media,
                });
              }}
            />
          ) : null}

          {phase === "error" && errorState ? (
            <ErrorPanel
              title={errorState.title}
              message={errorState.message}
              hint={errorState.hint}
              retryLabel={errorState.retryLabel}
              onRetry={errorState.retry}
              onReset={reset}
              resetLabel={errorState.resetLabel}
            />
          ) : null}
        </div>
      </main>

      <DependencyFooter dependencies={dependencies} />

      <FolderDialog
        open={folderOpen}
        initialPath={destination}
        roots={config?.roots ?? []}
        onOpenChange={setFolderOpen}
        onSelect={setDestination}
      />

      {downloadDialog ? (
        <DownloadOptionsDialog
          open
          heading={
            downloadDialog.kind === "playlist"
              ? t("entry.title")
              : t("entry.mediaTitle")
          }
          description={
            downloadDialog.kind === "playlist"
              ? joinMeta([
                  downloadDialog.entry.title,
                  formatDuration(downloadDialog.entry.duration),
                  t("entry.trackOf", {
                    index: downloadDialog.entry.index,
                    count: downloadDialog.playlist.entry_count,
                  }),
                ])
              : joinMeta([
                  downloadDialog.media.title,
                  formatDuration(downloadDialog.media.duration),
                  downloadDialog.media.extractor,
                ])
          }
          formats={
            downloadDialog.kind === "playlist"
              ? downloadDialog.playlist.formats
              : downloadDialog.media.formats
          }
          initialFormatId={formatId}
          initialQualityId={qualityId}
          destination={destination}
          onOpenChange={(open) => {
            if (!open) {
              closeDownloadDialog();
            }
          }}
          onConfirm={enqueueDownload}
        />
      ) : null}

      <QueueDialog
        open={queueOpen}
        active={
          activeQueueItem
            ? { item: activeQueueItem, state: queueProgress }
            : null
        }
        items={queue}
        cancelling={queueCancelling}
        clearing={queueClearing}
        onOpenChange={setQueueOpen}
        onRemove={removeQueueItem}
        onCancelActive={() => {
          void cancelQueueItem();
        }}
        onClear={() => {
          void clearQueue();
        }}
      />

      <DownloadToast
        active={
          activeQueueItem && queueProgress
            ? {
                title: activeQueueItem.title,
                state: queueProgress,
                queueLength: queue.length,
                cancelling: queueCancelling,
              }
            : null
        }
        result={queueResult}
        onCancel={() => {
          void cancelQueueItem();
        }}
        onDismiss={() => setQueueResult(null)}
        onOpenFolder={() => {
          void openQueueFolder();
        }}
      />
    </div>
  );
}
