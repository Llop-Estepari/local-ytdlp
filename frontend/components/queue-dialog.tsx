"use client";

import { useEffect, useState } from "react";
import { AlertTriangle, Loader2, Trash2 } from "lucide-react";

import { useI18n } from "@/components/i18n-provider";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Progress } from "@/components/ui/progress";
import { formatPercent } from "@/lib/format";
import type { DownloadState } from "@/types/api";
import type { QueueItem } from "@/types/queue";

interface ActiveQueueRow {
  item: QueueItem;
  state: DownloadState | null;
}

interface QueueDialogProps {
  open: boolean;
  active: ActiveQueueRow | null;
  items: QueueItem[];
  cancelling: boolean;
  clearing: boolean;
  onOpenChange: (open: boolean) => void;
  onRemove: (key: string) => void;
  onCancelActive: () => void;
  onClear: () => void;
}

export function QueueDialog({
  open,
  active,
  items,
  cancelling,
  clearing,
  onOpenChange,
  onRemove,
  onCancelActive,
  onClear,
}: QueueDialogProps) {
  const { t } = useI18n();
  const [confirmingClear, setConfirmingClear] = useState(false);

  useEffect(() => {
    if (!open) {
      setConfirmingClear(false);
    }
  }, [open]);

  const total = items.length + (active ? 1 : 0);

  if (confirmingClear) {
    return (
      <Dialog open={open} onOpenChange={onOpenChange}>
        <DialogContent>
          <DialogHeader>
            <div className="mb-1 flex h-10 w-10 items-center justify-center rounded-full border border-destructive/25 text-destructive">
              <AlertTriangle className="h-5 w-5" strokeWidth={1.8} />
            </div>
            <DialogTitle>{t("queue.clearTitle")}</DialogTitle>
            <DialogDescription>
              {t(
                active ? "queue.clearMessageActive" : "queue.clearMessage",
                { count: total },
              )}
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => setConfirmingClear(false)}
              disabled={clearing}
            >
              {t("common.cancel")}
            </Button>
            <Button
              type="button"
              variant="destructive"
              onClick={onClear}
              disabled={clearing}
            >
              {clearing ? (
                <Loader2 className="h-4 w-4 animate-spin" strokeWidth={1.8} />
              ) : (
                <Trash2 className="h-4 w-4" strokeWidth={1.8} />
              )}
              {clearing ? t("queue.clearing") : t("queue.clearConfirm")}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    );
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="gap-3">
        <DialogHeader>
          <DialogTitle>{t("queue.title")}</DialogTitle>
          <DialogDescription>{t("queue.total", { count: total })}</DialogDescription>
        </DialogHeader>

        {total === 0 ? (
          <p className="py-8 text-center text-sm text-muted-foreground">
            {t("queue.empty")}
          </p>
        ) : (
          <div className="max-h-80 space-y-2 overflow-y-auto pr-1">
            {active ? (
              <div className="rounded-lg border border-border bg-secondary/40 p-3">
                <div className="flex items-start gap-2">
                  <div className="min-w-0 flex-1 space-y-1">
                    <p className="text-[11px] font-medium uppercase tracking-[0.12em] text-muted-foreground">
                      {t("queue.active")}
                    </p>
                    <p className="truncate text-sm font-medium" title={active.item.title}>
                      {active.item.title}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {active.item.formatText} · {active.item.qualityText}
                    </p>
                  </div>
                  <Button
                    type="button"
                    variant="ghost"
                    size="icon"
                    className="-mr-1 -mt-1 h-8 w-8 shrink-0 text-muted-foreground"
                    onClick={onCancelActive}
                    disabled={cancelling}
                    aria-label={t("queue.cancelActive")}
                    title={t("queue.cancelActive")}
                  >
                    {cancelling ? (
                      <Loader2
                        className="h-3.5 w-3.5 animate-spin"
                        strokeWidth={1.8}
                      />
                    ) : (
                      <Trash2 className="h-3.5 w-3.5" strokeWidth={1.8} />
                    )}
                  </Button>
                </div>
                <div className="mt-2 flex items-center gap-2">
                  <Progress value={active.state?.percent ?? null} />
                  <span className="w-9 shrink-0 text-right text-[11px] tabular-nums text-muted-foreground">
                    {formatPercent(active.state?.percent ?? null)}
                  </span>
                </div>
              </div>
            ) : null}

            {items.map((item) => (
              <div
                key={item.key}
                className="flex items-center gap-2 rounded-lg border border-border px-3 py-2"
              >
                <div className="min-w-0 flex-1 space-y-0.5">
                  <p className="truncate text-sm" title={item.title}>
                    {item.title}
                  </p>
                  <p className="text-[11px] text-muted-foreground">
                    {item.formatText} · {item.qualityText}
                  </p>
                </div>
                <Button
                  type="button"
                  variant="ghost"
                  size="icon"
                  className="-mr-1 h-8 w-8 shrink-0 text-muted-foreground"
                  onClick={() => onRemove(item.key)}
                  aria-label={t("queue.remove")}
                  title={t("queue.remove")}
                >
                  <Trash2 className="h-3.5 w-3.5" strokeWidth={1.8} />
                </Button>
              </div>
            ))}
          </div>
        )}

        <DialogFooter className="border-t pt-3">
          <Button
            type="button"
            variant="outline"
            className="w-full sm:w-auto"
            onClick={() => setConfirmingClear(true)}
            disabled={total === 0 || clearing}
          >
            <Trash2 className="h-4 w-4" strokeWidth={1.8} />
            {t("queue.clear")}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
