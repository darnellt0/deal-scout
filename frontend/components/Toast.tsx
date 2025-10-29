"use client";

import { createContext, useContext, useState, ReactNode, useCallback } from "react";

type Toast = {
  id: number;
  text: string;
  type?: "success" | "error" | "info";
};

type ToastContextType = {
  push: (text: string, type?: "success" | "error" | "info") => void;
};

const ToastCtx = createContext<ToastContextType>({
  push: () => {},
});

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const push = useCallback(
    (text: string, type: "success" | "error" | "info" = "info") => {
      const id = Date.now();
      setToasts((t) => [...t, { id, text, type }]);
      setTimeout(() => setToasts((t) => t.filter((x) => x.id !== id)), 4000);
    },
    []
  );

  return (
    <ToastCtx.Provider value={{ push }}>
      {children}
      <div className="fixed bottom-4 right-4 space-y-2 z-50 pointer-events-none">
        {toasts.map((t) => {
          const bgColor =
            t.type === "success"
              ? "bg-green-600"
              : t.type === "error"
              ? "bg-red-600"
              : "bg-slate-800";

          return (
            <div
              key={t.id}
              className={`${bgColor} text-white px-4 py-3 rounded-lg shadow-lg pointer-events-auto`}
            >
              {t.text}
            </div>
          );
        })}
      </div>
    </ToastCtx.Provider>
  );
}

export const useToast = () => {
  const context = useContext(ToastCtx);
  if (!context) {
    throw new Error("useToast must be used within ToastProvider");
  }
  return context;
};
