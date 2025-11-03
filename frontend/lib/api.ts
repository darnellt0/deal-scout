// Use the Next.js proxy route for browser requests
// Browser requests use /api/proxy which is a same-origin call
// Server-side requests (in the proxy) use http://backend:8000 (Docker internal)
const API_BASE = typeof window !== 'undefined' ? '/api/proxy' : (process.env.NEXT_PUBLIC_API_BASE_URL || 'http://backend:8000');

const FALLBACK_AUTH_TOKEN =
  process.env.NEXT_PUBLIC_AUTH_TOKEN ||
  process.env.NEXT_PUBLIC_DEMO_AUTH_TOKEN ||
  "";

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
  const response = await authenticatedFetch(`${API_BASE}/seller/snap`, {
    method: "POST",
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
  const response = await authenticatedFetch(`${API_BASE}/seller/snap`, {
    headers: { "Accept": "application/json" },
    cache: "no-store",
  });
  if (!response.ok) {
    throw new Error("Failed to fetch snap jobs");
  }
  return response.json();
}

export type PublishSnapJobRequest = {
  snap_job_id: number;
  platforms: string[];
  price?: number;
  notes?: string;
};

export type PublishSnapJobResponse = {
  cross_post_id: number;
  item_id: number;
  platforms: string[];
  status: string;
  created_at: string | null;
};

export type CrossPostItemSummary = {
  id: number;
  title: string;
  price: number;
  status: string;
};

export type CrossPostListing = {
  id: number;
  platform: string;
  status: string;
  listing_url?: string | null;
  created_at: string;
  metadata: Record<string, unknown>;
  notes?: string | null;
  snap_job_id?: number | null;
  item: CrossPostItemSummary;
};

// Phase 7: Deal Alerts API types and functions
export type DealAlertRule = {
  id: number;
  user_id: number;
  name: string;
  enabled: boolean;
  keywords: string[];
  exclude_keywords: string[];
  categories: string[];
  condition?: string;
  min_price?: number;
  max_price?: number;
  location?: string;
  radius_mi?: number;
  min_deal_score?: number;
  notification_channels: string[];
  created_at: string;
  updated_at: string;
  last_triggered_at?: string;
};

export type CreateDealAlertRuleRequest = {
  name: string;
  keywords?: string[];
  exclude_keywords?: string[];
  categories?: string[];
  condition?: string;
  min_price?: number;
  max_price?: number;
  location?: string;
  radius_mi?: number;
  min_deal_score?: number;
  notification_channels?: string[];
};

export type UpdateDealAlertRuleRequest = Partial<CreateDealAlertRuleRequest>;

export type NotificationPreferences = {
  id: number;
  user_id: number;
  channels: string[];
  frequency: string;
  digest_time: string;
  quiet_hours_enabled: boolean;
  quiet_hours_start?: string;
  quiet_hours_end?: string;
  category_filters: string[];
  max_per_day: number;
  phone_number?: string;
  phone_verified: boolean;
  discord_webhook_url?: string;
  enabled: boolean;
  created_at: string;
  updated_at: string;
};

// Get JWT token from localStorage
function getAuthToken(): string {
  if (typeof window === "undefined") {
    return FALLBACK_AUTH_TOKEN;
  }

  const stored =
    window.localStorage.getItem("auth_token") ||
    window.sessionStorage.getItem("auth_token");

  if (stored) {
    return stored;
  }

  if (FALLBACK_AUTH_TOKEN) {
    window.localStorage.setItem("auth_token", FALLBACK_AUTH_TOKEN);
    return FALLBACK_AUTH_TOKEN;
  }

  return "";
}

// Helper to make authenticated requests
async function authenticatedFetch(
  url: string,
  options: RequestInit = {}
): Promise<Response> {
  const token = getAuthToken();
  const headers = {
    "Content-Type": "application/json",
    ...options.headers,
  };

  if (token) {
    (headers as any)["Authorization"] = `Bearer ${token}`;
  }

  return fetch(url, { ...options, headers });
}

// Deal Alerts API functions
export async function fetchDealAlertRules(): Promise<DealAlertRule[]> {
  const response = await authenticatedFetch(`${API_BASE}/deal-alert-rules`, {
    cache: "no-store",
  });
  if (!response.ok) {
    throw new Error("Failed to fetch deal alert rules");
  }
  return response.json();
}

export async function fetchDealAlertRule(ruleId: number): Promise<DealAlertRule> {
  const response = await authenticatedFetch(
    `${API_BASE}/deal-alert-rules/${ruleId}`,
    { cache: "no-store" }
  );
  if (!response.ok) {
    throw new Error(`Failed to fetch deal alert rule ${ruleId}`);
  }
  return response.json();
}

export async function createDealAlertRule(
  data: CreateDealAlertRuleRequest
): Promise<DealAlertRule> {
  const response = await authenticatedFetch(`${API_BASE}/deal-alert-rules`, {
    method: "POST",
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    const detail = await response.json().catch(() => ({}));
    throw new Error(detail.detail || "Failed to create deal alert rule");
  }
  return response.json();
}

export async function updateDealAlertRule(
  ruleId: number,
  data: UpdateDealAlertRuleRequest
): Promise<DealAlertRule> {
  const response = await authenticatedFetch(
    `${API_BASE}/deal-alert-rules/${ruleId}`,
    {
      method: "PATCH",
      body: JSON.stringify(data),
    }
  );
  if (!response.ok) {
    const detail = await response.json().catch(() => ({}));
    throw new Error(detail.detail || "Failed to update deal alert rule");
  }
  return response.json();
}

export async function deleteDealAlertRule(ruleId: number): Promise<void> {
  const response = await authenticatedFetch(
    `${API_BASE}/deal-alert-rules/${ruleId}`,
    { method: "DELETE" }
  );
  if (!response.ok) {
    throw new Error("Failed to delete deal alert rule");
  }
}

export async function testDealAlertRule(
  ruleId: number
): Promise<Array<Deal>> {
  const response = await authenticatedFetch(
    `${API_BASE}/deal-alert-rules/${ruleId}/test`,
    { method: "POST" }
  );
  if (!response.ok) {
    throw new Error("Failed to test deal alert rule");
  }
  return response.json();
}

export async function pauseDealAlertRule(ruleId: number): Promise<DealAlertRule> {
  const response = await authenticatedFetch(
    `${API_BASE}/deal-alert-rules/${ruleId}/pause`,
    { method: "POST" }
  );
  if (!response.ok) {
    throw new Error("Failed to pause deal alert rule");
  }
  return response.json();
}

export async function resumeDealAlertRule(
  ruleId: number
): Promise<DealAlertRule> {
  const response = await authenticatedFetch(
    `${API_BASE}/deal-alert-rules/${ruleId}/resume`,
    { method: "POST" }
  );
  if (!response.ok) {
    throw new Error("Failed to resume deal alert rule");
  }
  return response.json();
}

// Notification Preferences API functions
export async function fetchNotificationPreferences(): Promise<NotificationPreferences> {
  const response = await authenticatedFetch(
    `${API_BASE}/notification-preferences`,
    { cache: "no-store" }
  );
  if (!response.ok) {
    throw new Error("Failed to fetch notification preferences");
  }
  return response.json();
}

export async function updateNotificationChannels(
  channels: string[]
): Promise<NotificationPreferences> {
  const response = await authenticatedFetch(
    `${API_BASE}/notification-preferences/channels`,
    {
      method: "PATCH",
      body: JSON.stringify({ channels }),
    }
  );
  if (!response.ok) {
    throw new Error("Failed to update notification channels");
  }
  return response.json();
}

export async function updateNotificationFrequency(
  frequency: string,
  digest_time?: string
): Promise<NotificationPreferences> {
  const response = await authenticatedFetch(
    `${API_BASE}/notification-preferences/frequency`,
    {
      method: "PATCH",
      body: JSON.stringify({ frequency, digest_time }),
    }
  );
  if (!response.ok) {
    throw new Error("Failed to update notification frequency");
  }
  return response.json();
}

export async function updateQuietHours(
  quiet_hours_enabled: boolean,
  quiet_hours_start?: string,
  quiet_hours_end?: string
): Promise<NotificationPreferences> {
  const response = await authenticatedFetch(
    `${API_BASE}/notification-preferences/quiet-hours`,
    {
      method: "PATCH",
      body: JSON.stringify({
        quiet_hours_enabled,
        quiet_hours_start,
        quiet_hours_end,
      }),
    }
  );
  if (!response.ok) {
    throw new Error("Failed to update quiet hours");
  }
  return response.json();
}

export async function updateCategoryFilters(
  category_filters: string[]
): Promise<NotificationPreferences> {
  const response = await authenticatedFetch(
    `${API_BASE}/notification-preferences/category-filters`,
    {
      method: "PATCH",
      body: JSON.stringify({ category_filters }),
    }
  );
  if (!response.ok) {
    throw new Error("Failed to update category filters");
  }
  return response.json();
}

export async function updateMaxNotificationsPerDay(
  max_per_day: number
): Promise<NotificationPreferences> {
  const response = await authenticatedFetch(
    `${API_BASE}/notification-preferences/max-per-day`,
    {
      method: "PATCH",
      body: JSON.stringify({ max_per_day }),
    }
  );
  if (!response.ok) {
    throw new Error("Failed to update max notifications per day");
  }
  return response.json();
}

export async function publishSnapJob(
  jobId: number,
  data: PublishSnapJobRequest
): Promise<PublishSnapJobResponse> {
  const response = await authenticatedFetch(
    `${API_BASE}/seller/snap/${jobId}/publish`,
    {
      method: "POST",
      body: JSON.stringify(data),
    }
  );
  if (!response.ok) {
    const detail = await response.json().catch(() => ({}));
    throw new Error(detail.detail || "Failed to publish snap job");
  }
  return response.json();
}

export async function fetchCrossPosts(
  status?: string
): Promise<CrossPostListing[]> {
  const url = new URL(`${API_BASE}/seller/cross-posts`);
  if (status) {
    url.searchParams.set("status", status);
  }
  const response = await authenticatedFetch(url.toString(), {
    headers: { Accept: "application/json" },
    cache: "no-store",
  });
  if (!response.ok) {
    throw new Error("Failed to fetch cross-post listings");
  }
  return response.json();
}

export async function addPhoneNumber(
  phone_number: string
): Promise<NotificationPreferences> {
  const response = await authenticatedFetch(
    `${API_BASE}/notification-preferences/phone/add`,
    {
      method: "POST",
      body: JSON.stringify({ phone_number }),
    }
  );
  if (!response.ok) {
    throw new Error("Failed to add phone number");
  }
  return response.json();
}

export async function deleteSnapJob(jobId: number): Promise<void> {
  const response = await authenticatedFetch(
    `${API_BASE}/seller/snap/${jobId}`,
    { method: "DELETE" }
  );
  if (!response.ok) {
    const detail = await response.json().catch(() => ({}));
    throw new Error(detail.detail || "Failed to delete snap job");
  }
}

export async function removePhoneNumber(): Promise<NotificationPreferences> {
  const response = await authenticatedFetch(
    `${API_BASE}/notification-preferences/phone`,
    { method: "DELETE" }
  );
  if (!response.ok) {
    throw new Error("Failed to remove phone number");
  }
  return response.json();
}

export async function addDiscordWebhook(
  discord_webhook_url: string
): Promise<NotificationPreferences> {
  const response = await authenticatedFetch(
    `${API_BASE}/notification-preferences/discord-webhook/add`,
    {
      method: "POST",
      body: JSON.stringify({ discord_webhook_url }),
    }
  );
  if (!response.ok) {
    throw new Error("Failed to add Discord webhook");
  }
  return response.json();
}

export async function removeDiscordWebhook(): Promise<NotificationPreferences> {
  const response = await authenticatedFetch(
    `${API_BASE}/notification-preferences/discord-webhook`,
    { method: "DELETE" }
  );
  if (!response.ok) {
    throw new Error("Failed to remove Discord webhook");
  }
  return response.json();
}

export async function testDiscordWebhook(): Promise<{ status: string }> {
  const response = await authenticatedFetch(
    `${API_BASE}/notification-preferences/discord-webhook/test`,
    { method: "POST" }
  );
  if (!response.ok) {
    throw new Error("Failed to test Discord webhook");
  }
  return response.json();
}
