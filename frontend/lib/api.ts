const API_BASE =
  process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

export type Deal = {
  id: number;
  title: string;
  price: number;
  condition: string;
  url: string;
  thumbnail_url?: string | null;
  deal_score: number;
  auto_message: string;
  price_cents?: number;
};

export type SnapRequest = {
  photos: string[];
  notes?: string;
  source?: string;
};

export type DemoNotification = {
  id: number;
  channel: string;
  status: string;
  payload: {
    title: string;
    price: number;
    deal_score: number;
    distance_mi?: number;
    thumbnail_url?: string | null;
    url: string;
    auto_message: string;
    source: string;
  };
  created_at: string;
  sent_at?: string | null;
};

export async function fetchDeals(): Promise<Deal[]> {
  const response = await fetch(`${API_BASE}/buyer/deals`, {
    headers: { "Accept": "application/json" },
    cache: "no-store",
  });
  if (!response.ok) {
    throw new Error("Failed to fetch deals");
  }
  return response.json();
}

export async function triggerScan(live: boolean): Promise<void> {
  const endpoint = `/scan/run?live=${live ? 1 : 0}`;
  const response = await fetch(`${API_BASE}${endpoint}`, {
    method: "POST",
  });
  if (!response.ok) {
    throw new Error("Failed to trigger scan");
  }
}

export async function submitSnap(payload: SnapRequest) {
  const response = await fetch(`${API_BASE}/seller/snap`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    const detail = await response.json().catch(() => ({}));
    throw new Error(detail.detail || "Failed to create snap job");
  }
  return response.json();
}

export async function fetchNotifications(): Promise<DemoNotification[]> {
  const response = await fetch(`${API_BASE}/buyer/notifications`, {
    headers: { "Accept": "application/json" },
    cache: "no-store",
  });
  if (!response.ok) {
    throw new Error("Failed to fetch notifications");
  }
  return response.json();
}

export type SnapJobSummary = {
  job_id: number;
  status: string;
  title?: string | null;
  description?: string | null;
  suggested_price?: number | null;
  price_suggestion_cents?: number | null;
  condition_guess?: string | null;
  processed_images: string[];
  images: string[];
};

export async function fetchSnapJobs(): Promise<SnapJobSummary[]> {
  const response = await fetch(`${API_BASE}/seller/snap`, {
    headers: { "Accept": "application/json" },
    cache: "no-store",
  });
  if (!response.ok) {
    throw new Error("Failed to fetch snap jobs");
  }
  return response.json();
}
