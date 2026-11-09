import type { Metadata, Viewport } from "next";
import type { ReactNode } from "react";

import { I18nProvider } from "@/components/i18n-provider";

import "./globals.css";

const themeScript = `
(function () {
  try {
    var stored = localStorage.getItem("theme");
    var dark = stored ? stored === "dark" : true;
    document.documentElement.classList.toggle("dark", dark);
  } catch (error) {
    document.documentElement.classList.add("dark");
  }
})();
`;

export const metadata: Metadata = {
  title: "Vidora",
  description: "Descarga contenido multimedia local con yt-dlp y FFmpeg.",
  applicationName: "Vidora",
  robots: { index: false, follow: false },
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  themeColor: [
    { media: "(prefers-color-scheme: dark)", color: "#0a0a0a" },
    { media: "(prefers-color-scheme: light)", color: "#ffffff" },
  ],
};

export default function RootLayout({
  children,
}: Readonly<{ children: ReactNode }>) {
  return (
    <html lang="es" className="dark" suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: themeScript }} />
      </head>
      <body>
        <I18nProvider>{children}</I18nProvider>
      </body>
    </html>
  );
}
