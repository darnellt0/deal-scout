"use client";

import { useCallback, useState } from "react";
import useSWR from "swr";
import { AlertCard } from "../../components/AlertCard";
import {
  Deal,
  DemoNotification,
  fetchDeals,
  fetchNotifications,
  triggerScan,
} from "../../lib/api";

const dealsFetcher = async () => fetchDeals();
const notificationsFetcher = async () => fetchNotifications();
const STORAGE_KEY = "deal-scout-demo-mode";

export default function BuyerFeedPage() {
  const { data, isLoading, mutate } = useSWR<Deal[]>("deals", dealsFetcher, {
    refreshInterval: 60_000,
  });
  const { data: notifications } = useSWR<DemoNotification[]>(
    "notifications",
    notificationsFetcher,
    { refreshInterval: 60_000 }
  );
  const [status, setStatus] = useState<string>();
  const hasNotifications = (notifications?.length ?? 0) > 0;

  const handleScan = useCallback(async () => {
    const demoEnabled =
      typeof window !== "undefined"
        ? window.localStorage.getItem(STORAGE_KEY) !== "false"
        : true;
    const live = !demoEnabled;
    setStatus(live ? "Scanning live marketplaces…" : "Refreshing demo fixtures…");
    try {
      await triggerScan(live);
      await mutate();
      setStatus("Scan queued — refresh in a few seconds for results.");
    } catch (error) {
      if (error instanceof Error) {
        setStatus(error.message);
      } else {
        setStatus("Unable to trigger scan.");
      }
    }
  }, [mutate]);

  return (
    <div className="flex flex-col gap-6">
      <header className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900">
            Buyer Deal Feed
          </h1>
          <p className="text-sm text-slate-500">
            Auto-ranked couches and kitchen islands across major marketplaces.
          </p>
        </div>
        <div className="flex items-center gap-3">
          {hasNotifications && (
            <span className="rounded bg-brand/10 px-3 py-1 text-xs font-semibold text-brand-dark">
              New Alerts
            </span>
          )}
          <button
            onClick={handleScan}
            className="rounded bg-brand px-4 py-2 text-sm font-medium text-white shadow hover:bg-brand-dark"
          >
            Trigger Scan
          </button>
        </div>
      </header>

      {status && <p className="text-sm text-slate-600">{status}</p>}

      {hasNotifications && (
        <section className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
          <h2 className="text-sm font-semibold text-slate-800">
            Recent Demo Notifications
          </h2>
          <ul className="mt-3 space-y-2 text-sm">
            {notifications?.map((notification) => (
              <li
                key={notification.id}
                className="flex items-center justify-between rounded border border-slate-100 bg-slate-50 px-3 py-2"
              >
                <div>
                  <span className="font-medium text-slate-900">
                    {notification.payload.title}
                  </span>
                  <span className="ml-2 text-slate-500">
                    score {notification.payload.deal_score}
                  </span>
                </div>
                <span className="text-xs text-slate-500">
                  Auto message ready
                </span>
              </li>
            ))}
          </ul>
        </section>
      )}

      <section className="grid gap-4 md:grid-cols-2">
        {isLoading && (
          <div className="rounded-lg border border-slate-200 bg-white p-6 text-sm text-slate-500">
            Loading deals…
          </div>
        )}
        {data && data.length === 0 && !isLoading && (
          <div className="rounded-lg border border-slate-200 bg-white p-6 text-sm text-slate-500">
            No deals yet. Trigger another scan or adjust filters.
          </div>
        )}
        {data?.map((deal) => (
          <AlertCard key={deal.id} deal={deal} />
        ))}
      </section>
    </div>
  );
}
