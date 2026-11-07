"use client";

import { useEffect, useState } from "react";
import { Folder } from "lucide-react";

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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { shortenPath } from "@/lib/format";
import { formatLabel, qualityLabel } from "@/lib/labels";
import type { DownloadFormat, FormatOption } from "@/types/api";

interface DownloadOptionsDialogProps {
  open: boolean;
  heading: string;
  description: string;
  formats: FormatOption[];
  initialFormatId: string;
  initialQualityId: string;
  destination: string;
  onOpenChange: (open: boolean) => void;
  onConfirm: (formatId: DownloadFormat, qualityId: string) => void;
}

function resolveFormat(
  formats: FormatOption[],
  formatId: string,
  qualityId: string,
): { format: FormatOption; quality: string } {
  const format =
    formats.find((item) => item.id === formatId) ?? formats[0];
  const quality = format.qualities.some((item) => item.id === qualityId)
    ? qualityId
    : (format.qualities[0]?.id ?? "best");
  return { format, quality };
}

export function DownloadOptionsDialog({
  open,
  heading,
  description,
  formats,
  initialFormatId,
  initialQualityId,
  destination,
  onOpenChange,
  onConfirm,
}: DownloadOptionsDialogProps) {
  const { t } = useI18n();
  const [formatId, setFormatId] = useState<DownloadFormat>(
    initialFormatId as DownloadFormat,
  );
  const [qualityId, setQualityId] = useState(initialQualityId);

  useEffect(() => {
    if (!open) {
      return;
    }
    const resolved = resolveFormat(formats, initialFormatId, initialQualityId);
    setFormatId(resolved.format.id);
    setQualityId(resolved.quality);
  }, [open, initialFormatId, initialQualityId, formats]);

  const current = resolveFormat(formats, formatId, qualityId);

  const changeFormat = (nextId: string) => {
    const next = formats.find((item) => item.id === nextId);
    if (!next) {
      return;
    }
    setFormatId(next.id);
    setQualityId(next.qualities[0]?.id ?? "best");
  };

  const confirm = () => {
    onConfirm(current.format.id, current.quality);
    onOpenChange(false);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{heading}</DialogTitle>
          <DialogDescription>{description}</DialogDescription>
        </DialogHeader>

        <div className="grid gap-3 sm:grid-cols-2">
          <div className="space-y-1.5">
            <label className="text-[11px] font-medium uppercase tracking-[0.12em] text-muted-foreground">
              {t("common.format")}
            </label>
            <Select value={formatId} onValueChange={changeFormat}>
              <SelectTrigger aria-label={t("entry.formatAria")}>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {formats.map((format) => (
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
            <Select value={current.quality} onValueChange={setQualityId}>
              <SelectTrigger aria-label={t("entry.qualityAria")}>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {current.format.qualities.map((quality) => (
                  <SelectItem key={quality.id} value={quality.id}>
                    {qualityLabel(current.format.id, quality.id, t)}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>

        <div className="flex items-center gap-2 rounded-lg border px-3 py-2 text-sm">
          <Folder
            className="h-4 w-4 shrink-0 text-muted-foreground"
            strokeWidth={1.7}
          />
          <span className="shrink-0 text-muted-foreground">
            {t("common.saveIn")}
          </span>
          <span className="truncate text-foreground/90" title={destination}>
            {destination ? shortenPath(destination) : t("common.selectFolder")}
          </span>
        </div>

        <p className="text-xs text-muted-foreground">{t("entry.queueNote")}</p>

        <DialogFooter>
          <Button
            type="button"
            variant="outline"
            onClick={() => onOpenChange(false)}
          >
            {t("common.cancel")}
          </Button>
          <Button type="button" onClick={confirm} disabled={!destination}>
            {t("common.download")}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
