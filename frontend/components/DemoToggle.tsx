"use client";

import { useEffect, useState } from "react";

const STORAGE_KEY = "deal-scout-demo-mode";

export function DemoToggle() {
  const [enabled, setEnabled] = useState<boolean>(true);

  useEffect(() => {
    if (typeof window === "undefined") return;
    const stored = window.localStorage.getItem(STORAGE_KEY);
    if (stored !== null) {
      setEnabled(stored === "true");
    } else {
      window.localStorage.setItem(STORAGE_KEY, "true");
    }
  }, []);

  const toggle = () => {
    setEnabled((prev) => {
      const next = !prev;
      if (typeof window !== "undefined") {
        window.localStorage.setItem(STORAGE_KEY, String(next));
      }
      return next;
    });
  };

  return (
    <button
      type="button"
      onClick={toggle}
      className={`flex items-center gap-2 rounded-full border px-3 py-1 text-xs font-medium transition ${
        enabled
          ? "border-brand bg-brand/10 text-brand-dark"
          : "border-slate-300 bg-white text-slate-500"
      }`}
      aria-pressed={enabled}
    >
      <span
        className={`h-2.5 w-2.5 rounded-full ${
          enabled ? "bg-brand-dark" : "bg-slate-300"
        }`}
      />
      Demo Mode
    </button>
  );
}
