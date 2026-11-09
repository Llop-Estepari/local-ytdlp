"use client";

import { BadgeAlertIcon, RotateCcwIcon } from "lucide-animated";

import { useI18n } from "@/components/i18n-provider";
import { Button } from "@/components/ui/button";

interface ErrorPanelProps {
  title: string;
  message: string;
  hint?: string | null;
  retryLabel?: string;
  onRetry: () => void;
  onReset?: () => void;
  resetLabel?: string;
}

export function ErrorPanel({
  title,
  message,
  hint,
  retryLabel,
  onRetry,
  onReset,
  resetLabel,
}: ErrorPanelProps) {
  const { t } = useI18n();
  const retryText = retryLabel ?? t("common.retry");
  const resetText = resetLabel ?? t("common.changeUrl");

  return (
    <div className="animate-fade-up space-y-6">
      <div className="flex h-11 w-11 items-center justify-center rounded-full border border-destructive/25 text-destructive">
        <BadgeAlertIcon size={20} />
      </div>

      <div className="space-y-1.5">
        <h2 className="text-lg font-medium tracking-tight">{title}</h2>
        <p className="text-sm text-muted-foreground">{message}</p>
        {hint ? (
          <p className="break-words pt-1 text-xs text-muted-foreground/80">
            {hint}
          </p>
        ) : null}
      </div>

      <div className="space-y-2">
        <Button type="button" className="w-full" onClick={onRetry}>
          <RotateCcwIcon size={16} />
          {retryText}
        </Button>
        {onReset ? (
          <Button
            type="button"
            variant="ghost"
            className="w-full"
            onClick={onReset}
          >
            {resetText}
          </Button>
        ) : null}
      </div>
    </div>
  );
}
