"use client";

import { Moon, Sun } from "lucide-react";

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
      <Sun className="hidden h-4 w-4 dark:block" strokeWidth={1.7} />
      <Moon className="block h-4 w-4 dark:hidden" strokeWidth={1.7} />
    </Button>
  );
}
