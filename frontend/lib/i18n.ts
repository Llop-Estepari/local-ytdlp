export type Locale = "es" | "en";

export type MessageParams = Record<string, string | number>;

type Message = string | ((params: MessageParams) => string);

const es = {
  "app.title": "Local YT-DLP",
  "theme.toggle": "Cambiar entre tema claro y oscuro",
  "nav.home": "Ir al inicio",
  "queue.open": ({ count }) => `Abrir cola (${count})`,
  "queue.title": "Cola de descargas",
  "queue.total": ({ count }) =>
    `${count} ${Number(count) === 1 ? "canción" : "canciones"}`,
  "queue.empty": "No hay canciones en cola.",
  "queue.active": "Descargando",
  "queue.pending": "En espera",
  "queue.remove": "Quitar de la cola",
  "queue.cancelActive": "Cancelar la descarga actual",
  "queue.clear": "Limpiar cola",
  "queue.clearing": "Vaciando…",
  "queue.clearTitle": "¿Vaciar toda la cola?",
  "queue.clearMessage": ({ count }) =>
    `Se quitarán ${count} ${Number(count) === 1 ? "canción" : "canciones"} de la cola.`,
  "queue.clearMessageActive": ({ count }) =>
    `Se cancelará la descarga en curso y se quitarán ${count} ${Number(count) === 1 ? "canción" : "canciones"}.`,
  "queue.clearConfirm": "Vaciar cola",

  "url.placeholder": "Pega una URL…",
  "url.label": "URL del contenido",
  "url.analyze": "Analizar",
  "url.analyzing": "Analizando",
  "url.error.empty": "Introduce una URL.",
  "url.error.invalid": "Introduce un enlace válido.",
  "url.error.protocol": "Solo se admiten enlaces HTTP o HTTPS.",
  "url.error.host": "El enlace no contiene un dominio válido.",

  "common.cancel": "Cancelar",
  "common.download": "Descargar",
  "common.starting": "Iniciando…",
  "common.selectFolder": "Selecciona una carpeta",
  "common.saveIn": "Guardar en",
  "common.format": "Formato",
  "common.quality": "Calidad",
  "common.changeLink": "Cambiar enlace",
  "common.changeUrl": "Cambiar URL",
  "common.retry": "Reintentar",
  "common.close": "Cerrar",
  "common.cancelDownload": "Cancelar descarga",
  "common.cancelling": "Cancelando…",
  "common.check": "Comprobar",
  "common.processing": "Procesando…",
  "common.processingFfmpeg": "Procesando con FFmpeg…",
  "common.eta": ({ eta }) => `Quedan ${eta}`,

  "format.mp4": "MP4 · Vídeo",
  "format.webm": "WebM · Vídeo",
  "format.mp3": "MP3 · Audio",
  "format.m4a": "M4A · Audio",
  "format.best": "Mejor formato",
  "quality.best": "Mejor disponible",
  "quality.2160": "2160p · 4K",
  "quality.1440": "1440p · 2K",
  "quality.1080": "1080p · Full HD",
  "quality.720": "720p · HD",
  "quality.480": "480p",
  "quality.360": "360p",

  "dependency.missingBoth": "Faltan yt-dlp y FFmpeg",
  "dependency.missingOne": ({ tool }) => `Falta ${tool}`,
  "dependency.ytdlpNeeded":
    "yt-dlp es necesario para analizar y descargar contenido.",
  "dependency.ffmpegNeeded":
    "FFmpeg es necesario para combinar pistas y convertir audio.",
  "dependency.runInstaller": "Ejecuta el instalador de la aplicación.",

  "footer.updateAvailable": ({ tools }) =>
    `Actualización disponible: ${tools}`,
  "footer.checkFailed": "No se pudo comprobar",
  "footer.upToDate": "Todo actualizado",
  "footer.notInstalled": ({ tool }) => `${tool} no instalado`,
  "footer.check": "Comprobar",

  "folder.title": "Elegir carpeta",
  "folder.location": "Ubicación",
  "folder.parent": "Carpeta anterior",
  "folder.empty": "No hay subcarpetas.",
  "folder.namePlaceholder": "Nombre de la carpeta",
  "folder.create": "Crear",
  "folder.new": "Nueva carpeta",
  "folder.select": "Seleccionar",

  "root.downloads": "Descargas",
  "root.videos": "Vídeos",
  "root.music": "Música",
  "root.desktop": "Escritorio",

  "playlist.count": ({ count }) =>
    `${count} ${Number(count) === 1 ? "elemento" : "elementos"}`,
  "playlist.more": ({ count }) =>
    `y ${count} ${Number(count) === 1 ? "elemento más" : "elementos más"}`,
  "playlist.itemLabel": ({ index }) => `Pista ${index}`,
  "playlist.download": ({ count }) => `Descargar lista (${count})`,
  "playlist.addToQueue": ({ count }) => `Añadir lista a la cola (${count})`,
  "playlist.queueHint":
    "Hay descargas en curso. Puedes seguir añadiendo canciones desde sus iconos.",
  "playlist.downloadSong": ({ title }) => `Descargar ${title}`,
  "playlist.downloadThisSong": "Descargar esta canción",

  "success.playlistTitle": "Lista completada",
  "success.downloadTitle": "Descarga completada",
  "success.fileCount": ({ count }) =>
    `${count} ${Number(count) === 1 ? "archivo descargado" : "archivos descargados"}`,
  "success.fileFallback": "Archivo descargado",
  "success.openFolder": "Abrir carpeta",
  "success.newDownload": "Nueva descarga",

  "download.status.starting": "Preparando",
  "download.status.downloading": "Descargando",
  "download.status.processing": "Procesando",
  "download.status.completed": "Completado",
  "download.status.cancelled": "Cancelado",
  "download.status.error": "Error",
  "download.playlistStatus": "Descargando lista",
  "download.itemOf": ({ index, count }) => `Elemento ${index} de ${count}`,
  "download.item": ({ index }) => `Elemento ${index}`,
  "download.ffmpeg": "Procesando con FFmpeg…",
  "download.eta": ({ eta }) => `Quedan ${eta}`,

  "toast.queueCount": ({ count }) =>
    `${count} ${Number(count) === 1 ? "en cola" : "en cola"}`,
  "toast.cancelAria": "Cancelar descarga en cola",
  "toast.cancelTitle": "Cancelar descarga",
  "toast.completed": "Descarga completada",
  "toast.cancelled": "Descarga cancelada",
  "toast.failed": "No se pudo descargar",
  "toast.dismissAria": "Cerrar aviso de descarga",
  "toast.closeTitle": "Cerrar",
  "toast.fileFallback": "Archivo descargado",
  "toast.errorFallback": "No se pudo completar la descarga.",

  "entry.title": "Descargar canción",
  "entry.mediaTitle": "Descargar contenido",
  "entry.trackOf": ({ index, count }) => `Pista ${index} de ${count}`,
  "entry.choose": "Elige el formato y la calidad.",
  "entry.formatAria": "Formato de descarga",
  "entry.qualityAria": "Calidad de descarga",
  "entry.queueNote":
    "Si ya hay una descarga en curso, se añadirá a la cola.",

  "downloader.analyzeTitle": "No se pudo analizar el enlace",
  "downloader.noDestinationTitle": "No hay carpeta de destino",
  "downloader.noDestinationMessage":
    "Selecciona una carpeta antes de descargar.",
  "downloader.startTitle": "No se pudo iniciar la descarga",
  "downloader.failedTitle": "La descarga ha fallado",
  "downloader.failedMessage": "No se pudo completar la descarga.",
  "downloader.cancelTitle": "No se pudo cancelar la descarga",
  "downloader.bootTitle": "Sin conexión con el servicio local",
  "downloader.retryConnection": "Reintentar conexión",
  "downloader.downloadFallback": "Descarga",
  "downloader.cancelledNotice": "Descarga cancelada.",
  "downloader.unexpectedError": "Ha ocurrido un error inesperado.",
} satisfies Record<string, Message>;

export type MessageKey = keyof typeof es;

const en: Record<MessageKey, Message> = {
  "app.title": "Local YT-DLP",
  "theme.toggle": "Toggle light and dark theme",
  "nav.home": "Back to home",
  "queue.open": ({ count }) => `Open queue (${count})`,
  "queue.title": "Download queue",
  "queue.total": ({ count }) =>
    `${count} ${Number(count) === 1 ? "song" : "songs"}`,
  "queue.empty": "No songs in the queue.",
  "queue.active": "Downloading",
  "queue.pending": "Waiting",
  "queue.remove": "Remove from queue",
  "queue.cancelActive": "Cancel the active download",
  "queue.clear": "Clear queue",
  "queue.clearing": "Clearing…",
  "queue.clearTitle": "Clear the entire queue?",
  "queue.clearMessage": ({ count }) =>
    `${count} ${Number(count) === 1 ? "song" : "songs"} will be removed from the queue.`,
  "queue.clearMessageActive": ({ count }) =>
    `The active download will be cancelled and ${count} ${Number(count) === 1 ? "song" : "songs"} will be removed.`,
  "queue.clearConfirm": "Clear queue",

  "url.placeholder": "Paste a URL…",
  "url.label": "Content URL",
  "url.analyze": "Analyze",
  "url.analyzing": "Analyzing",
  "url.error.empty": "Enter a URL.",
  "url.error.invalid": "Enter a valid link.",
  "url.error.protocol": "Only HTTP or HTTPS links are supported.",
  "url.error.host": "The link does not contain a valid domain.",

  "common.cancel": "Cancel",
  "common.download": "Download",
  "common.starting": "Starting…",
  "common.selectFolder": "Select a folder",
  "common.saveIn": "Save to",
  "common.format": "Format",
  "common.quality": "Quality",
  "common.changeLink": "Change link",
  "common.changeUrl": "Change URL",
  "common.retry": "Retry",
  "common.close": "Close",
  "common.cancelDownload": "Cancel download",
  "common.cancelling": "Cancelling…",
  "common.check": "Check",
  "common.processing": "Processing…",
  "common.processingFfmpeg": "Processing with FFmpeg…",
  "common.eta": ({ eta }) => `${eta} left`,

  "format.mp4": "MP4 · Video",
  "format.webm": "WebM · Video",
  "format.mp3": "MP3 · Audio",
  "format.m4a": "M4A · Audio",
  "format.best": "Best format",
  "quality.best": "Best available",
  "quality.2160": "2160p · 4K",
  "quality.1440": "1440p · 2K",
  "quality.1080": "1080p · Full HD",
  "quality.720": "720p · HD",
  "quality.480": "480p",
  "quality.360": "360p",

  "dependency.missingBoth": "yt-dlp and FFmpeg are missing",
  "dependency.missingOne": ({ tool }) => `${tool} is missing`,
  "dependency.ytdlpNeeded":
    "yt-dlp is required to analyze and download content.",
  "dependency.ffmpegNeeded":
    "FFmpeg is required to merge streams and convert audio.",
  "dependency.runInstaller": "Run the application installer.",

  "footer.updateAvailable": ({ tools }) => `Update available: ${tools}`,
  "footer.checkFailed": "Could not check",
  "footer.upToDate": "Everything up to date",
  "footer.notInstalled": ({ tool }) => `${tool} not installed`,
  "footer.check": "Check",

  "folder.title": "Choose folder",
  "folder.location": "Location",
  "folder.parent": "Parent folder",
  "folder.empty": "No subfolders.",
  "folder.namePlaceholder": "Folder name",
  "folder.create": "Create",
  "folder.new": "New folder",
  "folder.select": "Select",

  "root.downloads": "Downloads",
  "root.videos": "Videos",
  "root.music": "Music",
  "root.desktop": "Desktop",

  "playlist.count": ({ count }) =>
    `${count} ${Number(count) === 1 ? "item" : "items"}`,
  "playlist.more": ({ count }) =>
    `and ${count} more ${Number(count) === 1 ? "item" : "items"}`,
  "playlist.itemLabel": ({ index }) => `Track ${index}`,
  "playlist.download": ({ count }) => `Download playlist (${count})`,
  "playlist.addToQueue": ({ count }) => `Add playlist to queue (${count})`,
  "playlist.queueHint":
    "Downloads are in progress. You can keep adding songs from their icons.",
  "playlist.downloadSong": ({ title }) => `Download ${title}`,
  "playlist.downloadThisSong": "Download this song",

  "success.playlistTitle": "Playlist completed",
  "success.downloadTitle": "Download completed",
  "success.fileCount": ({ count }) =>
    `${count} ${Number(count) === 1 ? "file downloaded" : "files downloaded"}`,
  "success.fileFallback": "File downloaded",
  "success.openFolder": "Open folder",
  "success.newDownload": "New download",

  "download.status.starting": "Preparing",
  "download.status.downloading": "Downloading",
  "download.status.processing": "Processing",
  "download.status.completed": "Completed",
  "download.status.cancelled": "Cancelled",
  "download.status.error": "Error",
  "download.playlistStatus": "Downloading playlist",
  "download.itemOf": ({ index, count }) => `Item ${index} of ${count}`,
  "download.item": ({ index }) => `Item ${index}`,
  "download.ffmpeg": "Processing with FFmpeg…",
  "download.eta": ({ eta }) => `${eta} left`,

  "toast.queueCount": ({ count }) => `${count} in queue`,
  "toast.cancelAria": "Cancel queued download",
  "toast.cancelTitle": "Cancel download",
  "toast.completed": "Download completed",
  "toast.cancelled": "Download cancelled",
  "toast.failed": "Download failed",
  "toast.dismissAria": "Dismiss download notification",
  "toast.closeTitle": "Close",
  "toast.fileFallback": "File downloaded",
  "toast.errorFallback": "Could not complete the download.",

  "entry.title": "Download song",
  "entry.mediaTitle": "Download content",
  "entry.trackOf": ({ index, count }) => `Track ${index} of ${count}`,
  "entry.choose": "Choose the format and quality.",
  "entry.formatAria": "Download format",
  "entry.qualityAria": "Download quality",
  "entry.queueNote":
    "If a download is already in progress, it will be added to the queue.",

  "downloader.analyzeTitle": "Could not analyze the link",
  "downloader.noDestinationTitle": "No destination folder",
  "downloader.noDestinationMessage":
    "Select a folder before downloading.",
  "downloader.startTitle": "Could not start the download",
  "downloader.failedTitle": "The download failed",
  "downloader.failedMessage": "Could not complete the download.",
  "downloader.cancelTitle": "Could not cancel the download",
  "downloader.bootTitle": "No connection to the local service",
  "downloader.retryConnection": "Retry connection",
  "downloader.downloadFallback": "Download",
  "downloader.cancelledNotice": "Download cancelled.",
  "downloader.unexpectedError": "An unexpected error occurred.",
};

export const messages: Record<Locale, Record<MessageKey, Message>> = {
  es,
  en,
};

export type TFunction = (
  key: MessageKey,
  params?: MessageParams,
) => string;

export function translate(
  locale: Locale,
  key: MessageKey,
  params: MessageParams = {},
): string {
  const message = messages[locale][key] ?? messages.es[key];
  if (typeof message === "function") {
    return message(params);
  }
  return message.replace(/\{(\w+)\}/g, (_, name: string) =>
    params[name] === undefined ? `{${name}}` : String(params[name]),
  );
}

export function detectLocale(): Locale {
  if (typeof navigator === "undefined") {
    return "es";
  }
  const languages =
    navigator.languages && navigator.languages.length > 0
      ? navigator.languages
      : [navigator.language];
  for (const language of languages) {
    const normalized = (language || "").toLowerCase();
    if (normalized.startsWith("es")) {
      return "es";
    }
    if (normalized.startsWith("en")) {
      return "en";
    }
  }
  return "en";
}
