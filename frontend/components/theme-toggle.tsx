"use client";

import { MoonIcon, SunIcon } from "lucide-animated";

import { useI18n } from "@/components/i18n-provider";
import { Button } from "@/components/ui/button";

export function ThemeToggle() {
  const { t } = useI18n();

  return (
    <Button
      type="button"
      variant="ghost"
      size="icon"
      aria-label={t("theme.toggle")}
      className="text-muted-foreground hover:text-foreground"
      onClick={() => {
        const root = document.documentElement;
        const isDark = root.classList.toggle("dark");
        try {
          localStorage.setItem("theme", isDark ? "dark" : "light");
        } catch {
          // The visual change still works without persistence.
        }
      }}
    >
      <SunIcon size={16} className="hidden dark:inline-flex" />
      <MoonIcon size={16} className="inline-flex dark:hidden" />
    </Button>
  );
}
