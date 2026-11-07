"use client";

import { useEffect, useState } from "react";

import { api, getApiToken, getWebSocketUrl } from "@/lib/api";
import type { DownloadState } from "@/types/api";

const FINAL_STATUSES = new Set(["completed", "cancelled", "error"]);

export function useDownloadProgress(downloadId: string | null) {
  const [state, setState] = useState<DownloadState | null>(null);
  const [connectionError, setConnectionError] = useState(false);

  useEffect(() => {
    setState(null);
    setConnectionError(false);
    if (!downloadId) {
      return;
    }

    let cancelled = false;
    let final = false;
    let socket: WebSocket | null = null;
    let pollTimer: ReturnType<typeof setInterval> | null = null;
    let reconnectTimer: ReturnType<typeof setTimeout> | null = null;
    let attempts = 0;

    const stop = () => {
      if (pollTimer) {
        clearInterval(pollTimer);
        pollTimer = null;
      }
      if (reconnectTimer) {
        clearTimeout(reconnectTimer);
        reconnectTimer = null;
      }
      if (socket) {
        socket.onclose = null;
        socket.onerror = null;
        socket.onmessage = null;
        socket.close();
        socket = null;
      }
    };

    const apply = (next: DownloadState) => {
      if (cancelled) {
        return;
      }
      setState(next);
      setConnectionError(false);
      if (FINAL_STATUSES.has(next.status)) {
        final = true;
        stop();
      }
    };

    const poll = async () => {
      try {
        apply(await api.getDownload(downloadId));
      } catch {
        if (!cancelled) {
          setConnectionError(true);
        }
      }
    };

    const scheduleReconnect = () => {
      if (cancelled || final) {
        return;
      }
      attempts += 1;
      const delay = Math.min(1000 * 2 ** Math.min(attempts, 4), 10000);
      reconnectTimer = setTimeout(() => {
        void connect();
      }, delay);
    };

    const connect = async () => {
      try {
        const token = await getApiToken();
        if (cancelled || final) {
          return;
        }
        socket = new WebSocket(getWebSocketUrl(downloadId), [
          "local-ytdlp",
          token,
        ]);
        socket.onopen = () => {
          attempts = 0;
          setConnectionError(false);
        };
        socket.onmessage = (event) => {
          try {
            apply(JSON.parse(event.data as string) as DownloadState);
          } catch {
            // Ignore malformed messages and keep polling as a fallback.
          }
        };
        socket.onerror = () => {
          socket?.close();
        };
        socket.onclose = () => {
          if (!cancelled && !final) {
            scheduleReconnect();
          }
        };
      } catch {
        if (!cancelled) {
          setConnectionError(true);
          scheduleReconnect();
        }
      }
    };

    void poll();
    void connect();
    pollTimer = setInterval(() => {
      void poll();
    }, 1500);

    return () => {
      cancelled = true;
      stop();
    };
  }, [downloadId]);

  return { state, connectionError };
}
