import type { Locale } from "@/lib/i18n";

/**
 * The backend returns human-readable messages in Spanish. The UI is available
 * in English too, so known messages are translated here. Unknown dynamic
 * details fall back to the original text instead of showing a broken message.
 */
const EN: Record<string, string> = {
  // API client / generic
  "No se pudo conectar con el servicio local.":
    "Could not connect to the local service.",
  "Asegúrate de que la aplicación esté en ejecución.":
    "Make sure the application is running.",
  "Ha ocurrido un error inesperado.": "An unexpected error occurred.",
  "No se pudo conectar con el servidor.": "Could not connect to the server.",
  "No se pudo completar la operación.": "Could not complete the operation.",
  "La solicitud no es válida.": "The request is invalid.",
  "La operación tardó demasiado.": "The operation took too long.",
  "La descarga no existe.": "The download does not exist.",

  // URL validation
  "Introduce una URL.": "Enter a URL.",
  "La URL es demasiado larga.": "The URL is too long.",
  "El límite es de 2048 caracteres.": "The limit is 2048 characters.",
  "La URL contiene caracteres no válidos.":
    "The URL contains invalid characters.",
  "Solo se admiten enlaces HTTP o HTTPS.":
    "Only HTTP or HTTPS links are supported.",
  "Los enlaces locales (file://) no están permitidos.":
    "Local links (file://) are not allowed.",
  "La URL no contiene un dominio válido.":
    "The URL does not contain a valid domain.",
  "La URL no puede incluir credenciales.":
    "The URL cannot include credentials.",
  "El puerto de la URL no es válido.": "The URL port is invalid.",
  "No se permiten direcciones locales o privadas.":
    "Local or private addresses are not allowed.",
  "Introduce el enlace público del contenido.":
    "Enter the public link to the content.",
  "La URL no es válida.": "The URL is invalid.",
  "El dominio de la URL no es válido.": "The URL domain is invalid.",
  "No se pudo resolver el dominio.": "Could not resolve the domain.",
  "Comprueba la URL y tu conexión a Internet.":
    "Check the URL and your internet connection.",
  "La URL apunta a una dirección local o privada.":
    "The URL points to a local or private address.",

  // Security
  "Origen de la petición no permitido.": "Request origin not allowed.",
  "La aplicación solo acepta peticiones desde su propia interfaz local.":
    "The application only accepts requests from its own local interface.",
  "Petición entre sitios bloqueada.": "Cross-site request blocked.",
  "Abre la aplicación directamente en localhost.":
    "Open the application directly on localhost.",
  "Token local no válido.": "Invalid local token.",
  "Recarga la aplicación para obtener un token nuevo.":
    "Reload the application to get a new token.",
  "El token solo se entrega a clientes locales.":
    "The token is only issued to local clients.",
  "El acceso por red requiere configurar el token manualmente.":
    "Network access requires setting the token manually.",

  // Formats and selection
  "Formato de descarga no válido.": "Invalid download format.",
  "Calidad de vídeo no válida.": "Invalid video quality.",
  "Calidad de audio no válida.": "Invalid audio quality.",
  "Calidad no válida para este formato.":
    "Invalid quality for this format.",
  "No se encontraron formatos descargables.":
    "No downloadable formats found.",
  "Comprueba que el enlace sea de un vídeo o audio compatible con yt-dlp.":
    "Check that the link is a video or audio supported by yt-dlp.",
  "La lista de reproducción está vacía.": "The playlist is empty.",
  "Comprueba que el enlace apunte a una lista con contenido público.":
    "Check that the link points to a playlist with public content.",
  "No se pudieron detectar los formatos de la lista.":
    "Could not detect the playlist formats.",
  "Comprueba que sus elementos sean públicos y estén disponibles.":
    "Check that its items are public and available.",

  // File system
  "La ruta no es válida.": "The path is invalid.",
  "Elige una carpeta dentro de las ubicaciones permitidas.":
    "Choose a folder within the allowed locations.",
  "La carpeta está fuera de las ubicaciones permitidas.":
    "The folder is outside the allowed locations.",
  "Elige una carpeta dentro de Descargas, Vídeos, Música o Escritorio.":
    "Choose a folder inside Downloads, Videos, Music or Desktop.",
  "La carpeta de destino no existe.": "The destination folder does not exist.",
  "Elige otra carpeta.": "Choose another folder.",
  "La ruta de destino no es una carpeta.":
    "The destination path is not a folder.",
  "Elige una carpeta válida.": "Choose a valid folder.",
  "No hay permisos para escribir en la carpeta.":
    "No permission to write to the folder.",
  "Elige otra carpeta de destino.": "Choose another destination folder.",
  "No se pudo leer la carpeta.": "Could not read the folder.",
  "Comprueba los permisos de la carpeta.": "Check the folder permissions.",
  "El nombre de la carpeta no es válido.": "The folder name is invalid.",
  "El nombre de la carpeta es demasiado largo.":
    "The folder name is too long.",
  "El nombre de la carpeta contiene caracteres no válidos.":
    "The folder name contains invalid characters.",
  'Evita los caracteres < > : " / \\ | ? *.':
    'Avoid the characters < > : " / \\ | ? *.',
  "Ese nombre de carpeta está reservado por el sistema.":
    "That folder name is reserved by the system.",
  "El nombre de la carpeta no puede terminar en punto o espacio.":
    "The folder name cannot end with a dot or space.",
  "Ya existe una carpeta con ese nombre.":
    "A folder with that name already exists.",
  "No se pudo crear la carpeta.": "Could not create the folder.",
  "Comprueba los permisos de la carpeta de destino.":
    "Check the destination folder permissions.",
  "No se pudo abrir la carpeta.": "Could not open the folder.",
  "Ábrela manualmente desde tu explorador de archivos.":
    "Open it manually from your file manager.",

  // yt-dlp / downloads
  "yt-dlp no está instalado.": "yt-dlp is not installed.",
  "Ejecuta el instalador de la aplicación para instalar las dependencias.":
    "Run the application installer to install the dependencies.",
  "La URL no es compatible con yt-dlp.": "The URL is not supported by yt-dlp.",
  "Comprueba que el enlace apunte a un vídeo o audio.":
    "Check that the link points to a video or audio.",
  "El contenido es privado.": "The content is private.",
  "No se puede descargar sin autorización del propietario.":
    "It cannot be downloaded without the owner's permission.",
  "El contenido no está disponible.": "The content is not available.",
  "Puede haber sido eliminado o restringido.":
    "It may have been removed or restricted.",
  "La plataforma requiere verificación o inicio de sesión.":
    "The platform requires verification or sign-in.",
  "Prueba más tarde o utiliza otro enlace público.":
    "Try again later or use another public link.",
  "El contenido requiere iniciar sesión.": "The content requires sign-in.",
  "La aplicación solo admite contenido público.":
    "The application only supports public content.",
  "El contenido no existe (404).": "The content does not exist (404).",
  "Comprueba que el enlace sea correcto.": "Check that the link is correct.",
  "Acceso denegado (403).": "Access denied (403).",
  "La plataforma ha rechazado la petición.":
    "The platform rejected the request.",
  "El contenido no está disponible en tu región.":
    "The content is not available in your region.",
  "El formato seleccionado no está disponible.":
    "The selected format is not available.",
  "Prueba con otra calidad o formato.":
    "Try another quality or format.",
  "FFmpeg no está instalado.": "FFmpeg is not installed.",
  "Instala FFmpeg para combinar pistas y convertir audio.":
    "Install FFmpeg to merge streams and convert audio.",
  "No hay espacio suficiente en el disco.": "Not enough disk space.",
  "Libera espacio o elige otra carpeta de destino.":
    "Free up space or choose another destination folder.",
  "La conexión ha caducado.": "The connection timed out.",
  "Comprueba tu conexión a Internet e inténtalo de nuevo.":
    "Check your internet connection and try again.",
  "Error al procesar el archivo con FFmpeg.":
    "Error processing the file with FFmpeg.",
  "Comprueba que FFmpeg esté instalado correctamente.":
    "Check that FFmpeg is installed correctly.",
  "yt-dlp terminó con un error.": "yt-dlp finished with an error.",
  "yt-dlp devolvió una respuesta inesperada.":
    "yt-dlp returned an unexpected response.",
  "No se pudo interpretar la información del contenido.":
    "Could not interpret the content information.",
  "No se pudo localizar el archivo descargado.":
    "Could not locate the downloaded file.",
  "yt-dlp terminó correctamente pero el archivo no aparece en la carpeta de destino.":
    "yt-dlp finished successfully but the file does not appear in the destination folder.",
  "La descarga ha fallado de forma inesperada.":
    "The download failed unexpectedly.",

  // Update checks
  "No se pudo comprobar la última versión de yt-dlp.":
    "Could not check the latest yt-dlp version.",
  "No se pudo comprobar la última versión de FFmpeg.":
    "Could not check the latest FFmpeg version.",
  "Respuesta sin versión": "Response without version",
};

export function translateApiText(text: string, locale: Locale): string {
  if (locale === "es") {
    return text;
  }
  const partial = text.match(
    /Se descargaron (\d+) archivo\(s\) antes del error\./,
  );
  if (partial) {
    const base = text.replace(partial[0], "").trim();
    const translatedBase = base ? (EN[base] ?? base) : "";
    const files = partial[1];
    return [translatedBase, `${files} file(s) downloaded before the error.`]
      .filter(Boolean)
      .join(" ");
  }
  return EN[text] ?? text;
}
