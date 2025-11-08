import "./globals.css";
import type { Metadata, Viewport } from "next";
import { clsx } from "clsx";
import type { ReactNode } from "react";
import { DemoToggle } from "../components/DemoToggle";
import { ToastProvider } from "../components/Toast";
import FirstRunChecklist from "../components/FirstRunChecklist";
import PwaInstall from "../components/PwaInstall";

export const metadata: Metadata = {
  title: "Deal Scout - Cross-Post to Multiple Marketplaces",
  description: "Upload a photo and cross-post your items to eBay, Facebook Marketplace, and OfferUp instantly.",
  manifest: "/manifest.webmanifest",
  icons: {
    icon: [
      { url: "/icons/icon-192.png", sizes: "192x192", type: "image/png" },
      { url: "/icons/icon-512.png", sizes: "512x512", type: "image/png" },
    ],
    apple: [{ url: "/icons/icon-192.png" }],
    other: [{ rel: "mask-icon", url: "/icons/maskable-512.png", color: "#36013f" }],
  },
  appleWebApp: {
    capable: true,
    statusBarStyle: "black-translucent",
    title: "Deal Scout",
  },
};

export const viewport: Viewport = {
  themeColor: "#36013f",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body
        className={clsx(
          "min-h-screen bg-slate-50 text-slate-900 antialiased",
          "flex flex-col"
        )}
      >
        <ToastProvider>
          <header className="border-b border-slate-200 bg-white">
            <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-4 px-6 py-4">
              <div className="flex items-center gap-3">
                <span className="rounded bg-brand px-2 py-1 text-sm font-semibold text-white">
                  Deal Scout
                </span>
                <span className="text-sm text-slate-500">
                  San Jose, CA - within 50 miles
                </span>
              </div>
              <div className="flex flex-1 flex-wrap items-center justify-end gap-4">
                <nav className="flex items-center gap-4 text-sm font-medium text-slate-700">
                  <a href="/" className="hover:text-brand">
                    Home
                  </a>
                  <a href="/seller" className="hover:text-brand">
                    Sell an Item
                  </a>
                </nav>
                <PwaInstall />
              </div>
            </div>
          </header>
          <FirstRunChecklist />
          <main className="mx-auto w-full max-w-6xl flex-1 px-6 py-8">{children}</main>
          <footer className="border-t border-slate-200 bg-white">
            <div className="mx-auto max-w-6xl px-6 py-4 text-sm text-slate-500">
              Deal Scout - Powered by FastAPI, Celery, and Next.js
            </div>
          </footer>
        </ToastProvider>
      </body>
    </html>
  );
}
