import type {
  AnalyzeResult,
  ConfigResponse,
  DependenciesResponse,
  DirectoryListing,
  DownloadState,
  RootEntry,
  StartDownloadInput,
  UpdateCheckResponse,
} from "@/types/api";

const DEV_API_BASE = "http://127.0.0.1:8765";

export const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE ??
  (process.env.NODE_ENV === "development" ? DEV_API_BASE : "");

const TOKEN_STORAGE_KEY = "local-ytdlp-token";

export class ApiError extends Error {
  readonly status: number;
  readonly hint: string | null;

  constructor(status: number, message: string, hint: string | null = null) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.hint = hint;
  }
}

let memoryToken: string | null = null;
let tokenPromise: Promise<string> | null = null;

function readHashToken(): string | null {
  if (typeof window === "undefined") {
    return null;
  }
  const hash = window.location.hash;
  if (!hash.startsWith("#token=")) {
    return null;
  }
  const token = decodeURIComponent(hash.slice("#token=".length)).trim();
  if (!token) {
    return null;
  }
  try {
    sessionStorage.setItem(TOKEN_STORAGE_KEY, token);
  } catch {
    // Session storage can be disabled; the in-memory token still works.
  }
  window.history.replaceState(
    null,
    "",
    window.location.pathname + window.location.search,
  );
  return token;
}

export async function getApiToken(): Promise<string> {
  if (memoryToken) {
    return memoryToken;
  }
  if (tokenPromise) {
    return tokenPromise;
  }

  tokenPromise = (async () => {
    const hashToken = readHashToken();
    if (hashToken) {
      memoryToken = hashToken;
      return hashToken;
    }

    if (typeof window !== "undefined") {
      try {
        const stored = sessionStorage.getItem(TOKEN_STORAGE_KEY);
        if (stored) {
          memoryToken = stored;
          return stored;
        }
      } catch {
        // Ignore unavailable session storage.
      }
    }

    let response: Response;
    try {
      response = await fetch(`${API_BASE}/api/session`, {
        credentials: "omit",
        cache: "no-store",
      });
    } catch {
      throw new ApiError(
        0,
        "No se pudo conectar con el servicio local.",
        "Asegúrate de que la aplicación esté en ejecución.",
      );
    }
    if (!response.ok) {
      throw await toApiError(response);
    }
    const payload = (await response.json()) as { token: string };
    memoryToken = payload.token;
    return payload.token;
  })().catch((error) => {
    tokenPromise = null;
    throw error;
  });

  return tokenPromise;
}

async function toApiError(response: Response): Promise<ApiError> {
  let message = `Error ${response.status}.`;
  let hint: string | null = null;
  try {
    const payload = (await response.json()) as {
      detail?: string | { message?: string; hint?: string | null };
    };
    if (typeof payload.detail === "string") {
      message = payload.detail;
    } else if (payload.detail && typeof payload.detail === "object") {
      message = payload.detail.message ?? message;
      hint = payload.detail.hint ?? null;
    }
  } catch {
    // Keep the generic message.
  }
  return new ApiError(response.status, message, hint);
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  let token = await getApiToken();

  const perform = async (apiToken: string): Promise<Response> => {
    const headers = new Headers(init.headers);
    headers.set("X-API-Token", apiToken);
    if (init.body && !headers.has("Content-Type")) {
      headers.set("Content-Type", "application/json");
    }
    try {
      return await fetch(`${API_BASE}${path}`, {
        ...init,
        headers,
        credentials: "omit",
        cache: "no-store",
      });
    } catch {
      throw new ApiError(
        0,
        "No se pudo conectar con el servicio local.",
        "Asegúrate de que la aplicación esté en ejecución.",
      );
    }
  };

  let response = await perform(token);
  if (response.status === 401) {
    memoryToken = null;
    tokenPromise = null;
    token = await getApiToken();
    response = await perform(token);
  }

  if (!response.ok) {
    throw await toApiError(response);
  }
  if (response.status === 204) {
    return undefined as T;
  }
  return (await response.json()) as T;
}

export const api = {
  getConfig: () => request<ConfigResponse>("/api/config"),
  getDependencies: () => request<DependenciesResponse>("/api/dependencies"),
  checkUpdates: () =>
    request<UpdateCheckResponse>("/api/dependencies/check-updates", {
      method: "POST",
    }),
  analyze: (url: string) =>
    request<AnalyzeResult>("/api/analyze", {
      method: "POST",
      body: JSON.stringify({ url }),
    }),
  startDownload: (input: StartDownloadInput) =>
    request<DownloadState>("/api/downloads", {
      method: "POST",
      body: JSON.stringify(input),
    }),
  getDownload: (id: string) =>
    request<DownloadState>(`/api/downloads/${encodeURIComponent(id)}`),
  cancelDownload: (id: string) =>
    request<DownloadState>(
      `/api/downloads/${encodeURIComponent(id)}/cancel`,
      { method: "POST" },
    ),
  listDirectory: (path: string) =>
    request<DirectoryListing>(`/api/fs/list?path=${encodeURIComponent(path)}`),
  createDirectory: (path: string, name: string) =>
    request<RootEntry>("/api/fs/mkdir", {
      method: "POST",
      body: JSON.stringify({ path, name }),
    }),
  openFolder: (path: string) =>
    request<{ ok: boolean }>("/api/open-folder", {
      method: "POST",
      body: JSON.stringify({ path }),
    }),
};

export function getWebSocketUrl(downloadId: string): string {
  const origin =
    API_BASE ||
    (typeof window !== "undefined" ? window.location.origin : "http://127.0.0.1");
  const url = new URL(origin);
  url.protocol = url.protocol === "https:" ? "wss:" : "ws:";
  url.pathname = `/ws/downloads/${encodeURIComponent(downloadId)}`;
  url.search = "";
  url.hash = "";
  return url.toString();
}
