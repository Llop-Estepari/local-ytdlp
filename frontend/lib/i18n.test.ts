import { describe, expect, it } from "vitest";

import { translateApiText } from "@/lib/api-messages";
import { translate, type TFunction } from "@/lib/i18n";
import { formatLabel, qualityLabel, rootLabel } from "@/lib/labels";
import type { FormatOption } from "@/types/api";

const en: TFunction = (key, params) => translate("en", key, params);
const es: TFunction = (key, params) => translate("es", key, params);

const format: FormatOption = {
  id: "mp4",
  label: "MP4 · Vídeo",
  kind: "video",
  qualities: [{ id: "1080", label: "1080p · Full HD" }],
};

describe("translate", () => {
  it("translates static and interpolated messages", () => {
    expect(translate("es", "url.analyze")).toBe("Analizar");
    expect(translate("en", "url.analyze")).toBe("Analyze");
    expect(translate("en", "download.itemOf", { index: 2, count: 5 })).toBe(
      "Item 2 of 5",
    );
    expect(translate("es", "download.itemOf", { index: 2, count: 5 })).toBe(
      "Elemento 2 de 5",
    );
  });

  it("handles plural forms", () => {
    expect(translate("en", "playlist.count", { count: 1 })).toBe("1 item");
    expect(translate("en", "playlist.count", { count: 3 })).toBe("3 items");
    expect(translate("es", "playlist.count", { count: 1 })).toBe("1 elemento");
    expect(translate("es", "playlist.count", { count: 3 })).toBe("3 elementos");
    expect(translate("en", "success.fileCount", { count: 1 })).toBe(
      "1 file downloaded",
    );
    expect(translate("en", "success.fileCount", { count: 2 })).toBe(
      "2 files downloaded",
    );
    expect(translate("en", "queue.total", { count: 1 })).toBe("1 song");
    expect(translate("en", "queue.total", { count: 3 })).toBe("3 songs");
    expect(translate("es", "playlist.addToQueue", { count: 4 })).toBe(
      "Añadir lista a la cola (4)",
    );
  });
});

describe("translateApiText", () => {
  it("translates known backend messages", () => {
    expect(
      translateApiText("No se permiten direcciones locales o privadas.", "en"),
    ).toBe("Local or private addresses are not allowed.");
    expect(
      translateApiText("Introduce el enlace público del contenido.", "en"),
    ).toBe("Enter the public link to the content.");
  });

  it("keeps Spanish messages and unknown details", () => {
    expect(
      translateApiText("No se permiten direcciones locales o privadas.", "es"),
    ).toBe("No se permiten direcciones locales o privadas.");
    expect(translateApiText("Detalle dinámico de yt-dlp", "en")).toBe(
      "Detalle dinámico de yt-dlp",
    );
  });

  it("translates partial playlist errors", () => {
    expect(
      translateApiText(
        "Prueba con otra calidad o formato. Se descargaron 2 archivo(s) antes del error.",
        "en",
      ),
    ).toBe(
      "Try another quality or format. 2 file(s) downloaded before the error.",
    );
  });
});

describe("labels", () => {
  it("builds localized format and quality labels", () => {
    expect(formatLabel(format, en)).toBe("MP4 · Video");
    expect(formatLabel(format, es)).toBe("MP4 · Vídeo");
    expect(qualityLabel("mp4", "1080", en)).toBe("1080p · Full HD");
    expect(qualityLabel("mp4", "best", en)).toBe("Best available");
    expect(qualityLabel("mp3", "320", en)).toBe("320 kbps");
  });

  it("localizes known roots", () => {
    expect(rootLabel("Descargas", en)).toBe("Downloads");
    expect(rootLabel("Música", en)).toBe("Music");
    expect(rootLabel("MiCarpeta", en)).toBe("MiCarpeta");
  });
});
