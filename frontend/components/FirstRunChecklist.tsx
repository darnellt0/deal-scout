"use client";

import { useEffect, useState, useCallback } from "react";
import { useToast } from "./Toast";

type Check = {
  id: string;
  label: string;
  status: "ok" | "warn" | "fail";
  details: string;
};

type StatusResponse = {
  ok: boolean;
  checks: Check[];
  progress: number;
  timestamp: string;
};

const STATUS_POLL_INTERVAL = 15000; // 15 seconds
const INITIAL_POLL_DURATION = 120000; // 2 minutes

export default function FirstRunChecklist() {
  const { push } = useToast();
  const [status, setStatus] = useState<StatusResponse | null>(null);
  const [dismissed, setDismissed] = useState(false);
  const [loading, setLoading] = useState(true);
  const [scanning, setScanning] = useState(false);
  const [pollingActive, setPollingActive] = useState(true);

  // Fetch status from backend
  const fetchStatus = useCallback(async () => {
    try {
      const res = await fetch("/setup/status");
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data: StatusResponse = await res.json();
      setStatus(data);
      setLoading(false);
      return data;
    } catch (err) {
      console.error("Failed to fetch setup status:", err);
      setLoading(false);
      return null;
    }
  }, []);

  // Check if dismissed
  const checkDismissed = useCallback(async () => {
    try {
      const res = await fetch("/setup/is-dismissed");
      if (!res.ok) return;
      const data = await res.json();
      setDismissed(data.dismissed);
      // Also check localStorage for client-side dismissed flag
      const localDismissed = localStorage.getItem("firstRunDismissed") === "true";
      if (localDismissed) {
        setDismissed(true);
      }
    } catch (err) {
      console.error("Failed to check dismissed status:", err);
    }
  }, []);

  // Initial load
  useEffect(() => {
    checkDismissed();
    fetchStatus();
  }, [checkDismissed, fetchStatus]);

  // Polling: active for first 2 minutes, then stop
  useEffect(() => {
    if (!pollingActive || dismissed) {
      return;
    }

    const pollStartTime = Date.now();
    const interval = setInterval(async () => {
      const data = await fetchStatus();

      // Stop polling if all checks ok or 2 minutes elapsed
      if (data?.ok || Date.now() - pollStartTime > INITIAL_POLL_DURATION) {
        setPollingActive(false);
      }
    }, STATUS_POLL_INTERVAL);

    return () => clearInterval(interval);
  }, [pollingActive, dismissed, fetchStatus]);

  // Handle run live scan
  const handleRunLiveScan = useCallback(async () => {
    if (scanning) return;

    try {
      setScanning(true);

      // Flip Demo Mode off
      localStorage.setItem("demoMode", "off");

      // Call blocking live scan
      const res = await fetch("/scan/run?live=1&blocking=1", {
        method: "POST",
      });

      if (!res.ok) {
        throw new Error(`Scan failed: HTTP ${res.status}`);
      }

      const data = await res.json();
      const total = data.total ?? 0;
      const added = data.new ?? 0;
      const updated = data.updated ?? 0;

      push(
        `Live scan complete: ${added} new, ${updated} updated, ${total} total.`,
        "success"
      );

      // Refetch status to update checklist
      await fetchStatus();

      // Trigger a window event so other components can refresh if needed
      window.dispatchEvent(new CustomEvent("liveScalComplete"));
    } catch (err: any) {
      push(
        `Scan failed: ${err?.message ?? "unknown error"}`,
        "error"
      );
    } finally {
      setScanning(false);
    }
  }, [scanning, push, fetchStatus]);

  // Handle dismiss
  const handleDismiss = useCallback(async () => {
    try {
      await fetch("/setup/dismiss", { method: "POST" });
    } catch (err) {
      console.error("Failed to dismiss:", err);
    }
    localStorage.setItem("firstRunDismissed", "true");
    setDismissed(true);
  }, []);

  // Auto-hide conditions
  const shouldShow =
    !dismissed && !loading && status && !status.ok && status.progress < 0.95;

  if (!shouldShow) {
    return null;
  }

  const percentComplete = Math.round(status!.progress * 100);
  const okCount = status!.checks.filter((c) => c.status === "ok").length;
  const totalCount = status!.checks.length;

  return (
    <div className="sticky top-0 z-40 bg-gradient-to-r from-blue-50 to-indigo-50 border-b border-blue-200 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 md:px-6 py-5">
        {/* Header */}
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-lg font-semibold text-gray-900">
              Let's finish setup
            </h2>
            <p className="text-sm text-gray-600">
              {okCount} of {totalCount} checks complete
            </p>
          </div>
          <button
            onClick={handleDismiss}
            className="text-gray-400 hover:text-gray-600 transition"
            title="Dismiss banner"
          >
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
              <path
                fillRule="evenodd"
                d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
                clipRule="evenodd"
              />
            </svg>
          </button>
        </div>

        {/* Progress bar */}
        <div className="mb-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-medium text-gray-700">Progress</span>
            <span className="text-xs font-semibold text-indigo-600">
              {percentComplete}%
            </span>
          </div>
          <div className="w-full h-2 bg-gray-200 rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-blue-500 to-indigo-600 transition-all duration-500"
              style={{ width: `${percentComplete}%` }}
            />
          </div>
        </div>

        {/* Checks grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mb-4">
          {status!.checks.map((check) => (
            <div
              key={check.id}
              className="flex items-center gap-3 p-3 bg-white/60 rounded-lg"
            >
              <div className="flex-shrink-0">
                {check.status === "ok" ? (
                  <span className="inline-flex items-center justify-center w-5 h-5 rounded-full bg-green-100 text-green-600 font-bold text-sm">
                    ✓
                  </span>
                ) : check.status === "warn" ? (
                  <span className="inline-flex items-center justify-center w-5 h-5 rounded-full bg-amber-100 text-amber-600 font-bold text-sm">
                    !
                  </span>
                ) : (
                  <span className="inline-flex items-center justify-center w-5 h-5 rounded-full bg-red-100 text-red-600 font-bold text-sm">
                    ✕
                  </span>
                )}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-900">
                  {check.label}
                </p>
                {check.details && (
                  <p className="text-xs text-gray-600 truncate">
                    {check.details}
                  </p>
                )}
              </div>
            </div>
          ))}
        </div>

        {/* Action buttons */}
        <div className="flex flex-wrap items-center gap-3">
          <button
            onClick={handleRunLiveScan}
            disabled={scanning}
            className="px-4 py-2 rounded-lg bg-teal-600 text-white font-medium hover:bg-teal-700 disabled:opacity-60 disabled:cursor-not-allowed transition"
          >
            {scanning ? "Scanning..." : "Run live scan now"}
          </button>
          <a
            href="/ebay/authorize"
            target="_blank"
            rel="noopener noreferrer"
            className="px-4 py-2 rounded-lg bg-blue-600 text-white font-medium hover:bg-blue-700 transition"
          >
            Connect eBay
          </a>
          <a
            href="http://localhost:8025"
            target="_blank"
            rel="noopener noreferrer"
            className="px-4 py-2 rounded-lg bg-gray-600 text-white font-medium hover:bg-gray-700 transition"
          >
            Open MailHog
          </a>
        </div>
      </div>
    </div>
  );
}
