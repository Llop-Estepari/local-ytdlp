"use client";

import { Link2, Loader2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import { useI18n } from "@/components/i18n-provider";

interface UrlFormProps {
  url: string;
  analyzing: boolean;
  error: string | null;
  onUrlChange: (value: string) => void;
  onSubmit: () => void;
}

export function UrlForm({
  url,
  analyzing,
  error,
  onUrlChange,
  onSubmit,
}: UrlFormProps) {
  const { t } = useI18n();

  return (
    <form
      className="space-y-2.5"
      onSubmit={(event) => {
        event.preventDefault();
        onSubmit();
      }}
    >
      <div className="flex items-center gap-2 rounded-2xl border border-border bg-card/60 p-1.5 pl-4 transition-colors focus-within:border-foreground/20 focus-within:bg-card">
        <Link2
          className="h-4 w-4 shrink-0 text-muted-foreground"
          strokeWidth={1.7}
          aria-hidden="true"
        />
        <input
          value={url}
          onChange={(event) => onUrlChange(event.target.value)}
          type="text"
          inputMode="url"
          autoComplete="off"
          spellCheck={false}
          autoFocus
          placeholder={t("url.placeholder")}
          aria-label={t("url.label")}
          aria-invalid={error ? true : undefined}
          disabled={analyzing}
          className="h-10 min-w-0 flex-1 bg-transparent text-[15px] outline-none placeholder:text-muted-foreground/80 disabled:opacity-60"
        />
        <Button
          type="submit"
          size="sm"
          disabled={analyzing || !url.trim()}
          className="h-10 shrink-0 rounded-xl px-3.5"
        >
          {analyzing ? (
            <Loader2 className="h-4 w-4 animate-spin" strokeWidth={1.8} />
          ) : null}
          <span>
            {analyzing ? t("url.analyzing") : t("url.analyze")}
          </span>
        </Button>
      </div>
      {error ? (
        <p className="px-1 text-[13px] text-destructive" role="alert">
          {error}
        </p>
      ) : null}
    </form>
  );
}
