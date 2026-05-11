"use client";

import { useEffect } from "react";

export function usePolling(callback: () => void, intervalMs = 30000) {
  useEffect(() => {
    const interval = window.setInterval(callback, intervalMs);

    return () => {
      window.clearInterval(interval);
    };
  }, [callback, intervalMs]);
}