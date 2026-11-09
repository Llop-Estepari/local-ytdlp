import { BadgeAlertIcon } from "lucide-animated";

import { useI18n } from "@/components/i18n-provider";
import type { DependenciesResponse } from "@/types/api";

interface DependencyWarningProps {
  dependencies: DependenciesResponse | null;
}

export function DependencyWarning({ dependencies }: DependencyWarningProps) {
  const { t } = useI18n();
  if (!dependencies || dependencies.ok) {
    return null;
  }

  const missing: string[] = [];
  if (!dependencies.ytdlp.installed) {
    missing.push("yt-dlp");
  }
  if (!dependencies.ffmpeg.installed) {
    missing.push("FFmpeg");
  }

  return (
    <div className="flex animate-fade-in gap-3 rounded-xl border border-border bg-card/50 px-4 py-3">
      <BadgeAlertIcon
        size={16}
        className="mt-0.5 inline-flex shrink-0 text-muted-foreground"
      />
      <div className="space-y-0.5 text-[13px]">
        <p className="font-medium">
          {missing.length === 2
            ? t("dependency.missingBoth")
            : t("dependency.missingOne", { tool: missing[0] })}
        </p>
        <p className="text-muted-foreground">
          {[
            missing.includes("yt-dlp") ? t("dependency.ytdlpNeeded") : null,
            missing.includes("FFmpeg") ? t("dependency.ffmpegNeeded") : null,
            t("dependency.runInstaller"),
          ]
            .filter(Boolean)
            .join(" ")}
        </p>
      </div>
    </div>
  );
}
