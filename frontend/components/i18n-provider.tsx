"use client";

import {
  createContext,
  useContext,
  useEffect,
  useLayoutEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

import {
  detectLocale,
  translate,
  type Locale,
  type TFunction,
} from "@/lib/i18n";

interface I18nValue {
  locale: Locale;
  t: TFunction;
}

const I18nContext = createContext<I18nValue | null>(null);

const useIsomorphicLayoutEffect =
  typeof window !== "undefined" ? useLayoutEffect : useEffect;

export function I18nProvider({ children }: { children: ReactNode }) {
  const [locale, setLocale] = useState<Locale>("es");

  useIsomorphicLayoutEffect(() => {
    const detected = detectLocale();
    setLocale(detected);
    document.documentElement.lang = detected;
    document.title = translate(detected, "app.title");
  }, []);

  const t = useMemo<TFunction>(
    () => (key, params) => translate(locale, key, params),
    [locale],
  );

  const value = useMemo<I18nValue>(() => ({ locale, t }), [locale, t]);

  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>;
}

export function useI18n(): I18nValue {
  const context = useContext(I18nContext);
  if (!context) {
    throw new Error("useI18n must be used within I18nProvider");
  }
  return context;
}
