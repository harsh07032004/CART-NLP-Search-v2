/**
 * useKeepAlive — prevents Render free-tier backend from spinning down.
 *
 * Strategy:
 * 1. Ping /health every `intervalMs` (default 10 min) to keep the backend warm.
 * 2. If the ping fails (backend is sleeping / cold-starting), retry every 15 s
 *    and show a "Waking up server…" toast so the user knows to wait.
 * 3. When the backend comes back, auto-dismiss the toast and reload products.
 */
import { useEffect, useRef, useCallback } from "react";
import { toast } from "sonner";
import { api } from "@/lib/api";

const PING_INTERVAL_MS = 10 * 60 * 1000; // 10 minutes
const RETRY_INTERVAL_MS = 15 * 1000;     // 15 seconds when down

export function useKeepAlive(onBackendRestored) {
  const wakeToastId = useRef(null);
  const retryTimerRef = useRef(null);
  const pingTimerRef = useRef(null);
  const isDown = useRef(false);

  const clearRetry = () => {
    if (retryTimerRef.current) {
      clearInterval(retryTimerRef.current);
      retryTimerRef.current = null;
    }
  };

  const handleRestored = useCallback(() => {
    isDown.current = false;
    clearRetry();

    // Dismiss the "waking up" toast
    if (wakeToastId.current) {
      toast.dismiss(wakeToastId.current);
      wakeToastId.current = null;
    }

    toast.success("Server is back online!", { duration: 3000 });

    // Reload products so the user sees fresh data
    if (typeof onBackendRestored === "function") {
      onBackendRestored();
    }
  }, [onBackendRestored]);

  const handleDown = useCallback(() => {
    if (isDown.current) return; // already handling — don't show duplicate toasts
    isDown.current = true;

    wakeToastId.current = toast.loading(
      "Waking up server… this may take up to 60 seconds on first load.",
      { duration: Infinity }
    );

    // Retry every 15 s until the backend responds
    retryTimerRef.current = setInterval(async () => {
      try {
        await api.health();
        handleRestored();
      } catch {
        // Still down — keep retrying silently
      }
    }, RETRY_INTERVAL_MS);
  }, [handleRestored]);

  const ping = useCallback(async () => {
    try {
      await api.health();
      if (isDown.current) handleRestored();
    } catch {
      handleDown();
    }
  }, [handleDown, handleRestored]);

  useEffect(() => {
    // Immediate ping on mount
    ping();

    // Schedule regular pings thereafter
    pingTimerRef.current = setInterval(ping, PING_INTERVAL_MS);

    return () => {
      clearInterval(pingTimerRef.current);
      clearRetry();
    };
  }, [ping]);
}
