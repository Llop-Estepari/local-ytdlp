import { translateApiText } from "@/lib/api-messages";
import { ApiError } from "@/lib/api";
import type { Locale } from "@/lib/i18n";

export function errorMessage(error: unknown, locale: Locale = "es"): string {
  if (error instanceof ApiError) {
    return translateApiText(error.message, locale);
  }
  if (error instanceof Error) {
    return translateApiText(error.message, locale);
  }
  return locale === "en"
    ? "An unexpected error occurred."
    : "Ha ocurrido un error inesperado.";
}

export function errorHint(error: unknown, locale: Locale = "es"): string | null {
  if (!(error instanceof ApiError) || !error.hint) {
    return null;
  }
  return translateApiText(error.hint, locale);
}
