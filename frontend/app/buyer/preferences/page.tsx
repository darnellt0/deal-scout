"use client";

import { useCallback, useState, useEffect } from "react";
import useSWR from "swr";
import {
  NotificationPreferences,
  fetchNotificationPreferences,
  updateNotificationChannels,
  updateNotificationFrequency,
  updateQuietHours,
  updateMaxNotificationsPerDay,
  addDiscordWebhook,
  removeDiscordWebhook,
  testDiscordWebhook,
} from "../../../lib/api";

export default function NotificationPreferencesPage() {
  const { data: prefs, isLoading, mutate } = useSWR<NotificationPreferences>(
    "notification-preferences",
    fetchNotificationPreferences,
    { refreshInterval: 30_000 }
  );

  const [status, setStatus] = useState<string>();
  const [error, setError] = useState<string>();

  // Channel management
  const [selectedChannels, setSelectedChannels] = useState<string[]>([]);
  const [discordUrl, setDiscordUrl] = useState("");
  const [showDiscordInput, setShowDiscordInput] = useState(false);

  // Frequency management
  const [frequency, setFrequency] = useState("immediate");
  const [digestTime, setDigestTime] = useState("09:00");

  // Quiet hours
  const [quietHoursEnabled, setQuietHoursEnabled] = useState(false);
  const [quietStart, setQuietStart] = useState("22:00");
  const [quietEnd, setQuietEnd] = useState("08:00");

  // Rate limiting
  const [maxPerDay, setMaxPerDay] = useState(10);

  // Initialize from preferences when loaded
  useEffect(() => {
    if (prefs) {
      setSelectedChannels(prefs.channels);
      setFrequency(prefs.frequency);
      setDigestTime(prefs.digest_time);
      setQuietHoursEnabled(prefs.quiet_hours_enabled);
      setQuietStart(prefs.quiet_hours_start || "22:00");
      setQuietEnd(prefs.quiet_hours_end || "08:00");
      setMaxPerDay(prefs.max_per_day);
    }
  }, [prefs]);

  // Update channels
  const handleUpdateChannels = useCallback(
    async (channels: string[]) => {
      try {
        setError(undefined);
        setStatus("Updating notification channels...");
        await updateNotificationChannels(channels);
        setSelectedChannels(channels);
        await mutate();
        setStatus("Channels updated successfully");
        setTimeout(() => setStatus(undefined), 3000);
      } catch (err) {
        const msg = err instanceof Error ? err.message : "Failed to update channels";
        setError(msg);
      }
    },
    [mutate]
  );

  // Update frequency
  const handleUpdateFrequency = useCallback(async () => {
    try {
      setError(undefined);
      setStatus("Updating notification frequency...");
      await updateNotificationFrequency(frequency, digestTime);
      await mutate();
      setStatus("Frequency updated successfully");
      setTimeout(() => setStatus(undefined), 3000);
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Failed to update frequency";
      setError(msg);
    }
  }, [frequency, digestTime, mutate]);

  // Update quiet hours
  const handleUpdateQuietHours = useCallback(async () => {
    try {
      setError(undefined);
      setStatus("Updating quiet hours...");
      await updateQuietHours(quietHoursEnabled, quietStart, quietEnd);
      await mutate();
      setStatus("Quiet hours updated successfully");
      setTimeout(() => setStatus(undefined), 3000);
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Failed to update quiet hours";
      setError(msg);
    }
  }, [quietHoursEnabled, quietStart, quietEnd, mutate]);

  // Update max per day
  const handleUpdateMaxPerDay = useCallback(async () => {
    try {
      setError(undefined);
      setStatus("Updating rate limit...");
      await updateMaxNotificationsPerDay(maxPerDay);
      await mutate();
      setStatus("Rate limit updated successfully");
      setTimeout(() => setStatus(undefined), 3000);
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Failed to update rate limit";
      setError(msg);
    }
  }, [maxPerDay, mutate]);

  // Add Discord webhook
  const handleAddDiscord = useCallback(async () => {
    if (!discordUrl.trim()) {
      setError("Discord webhook URL is required");
      return;
    }

    try {
      setError(undefined);
      setStatus("Adding Discord webhook...");
      await addDiscordWebhook(discordUrl);
      setDiscordUrl("");
      setShowDiscordInput(false);
      await mutate();
      setStatus("Discord webhook added successfully");
      setTimeout(() => setStatus(undefined), 3000);
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Failed to add Discord webhook";
      setError(msg);
    }
  }, [discordUrl, mutate]);

  // Remove Discord webhook
  const handleRemoveDiscord = useCallback(async () => {
    try {
      setError(undefined);
      setStatus("Removing Discord webhook...");
      await removeDiscordWebhook();
      await mutate();
      setStatus("Discord webhook removed");
      setTimeout(() => setStatus(undefined), 3000);
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Failed to remove Discord webhook";
      setError(msg);
    }
  }, [mutate]);

  // Test Discord webhook
  const handleTestDiscord = useCallback(async () => {
    try {
      setError(undefined);
      setStatus("Testing Discord webhook...");
      await testDiscordWebhook();
      setStatus("Test message sent to Discord!");
      setTimeout(() => setStatus(undefined), 3000);
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Failed to test Discord webhook";
      setError(msg);
    }
  }, []);

  if (isLoading || !prefs) {
    return (
      <div className="text-center py-12">
        <p className="text-slate-500">Loading notification preferences...</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-6 max-w-4xl">
      <header>
        <h1 className="text-2xl font-semibold text-slate-900">
          Notification Preferences
        </h1>
        <p className="mt-2 text-sm text-slate-500">
          Customize how and when you receive deal alerts.
        </p>
      </header>

      {status && (
        <div className="rounded-lg border border-green-200 bg-green-50 p-4">
          <p className="text-sm text-green-800">{status}</p>
        </div>
      )}

      {error && (
        <div className="rounded-lg border border-red-200 bg-red-50 p-4">
          <p className="text-sm text-red-800">{error}</p>
        </div>
      )}

      {/* Notification Channels */}
      <section className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
        <h2 className="mb-4 text-lg font-semibold text-slate-900">
          Notification Channels
        </h2>

        <div className="space-y-3">
          {["email", "discord", "sms", "push"].map((channel) => (
            <label key={channel} className="flex items-center gap-3">
              <input
                type="checkbox"
                checked={selectedChannels.includes(channel)}
                onChange={(e) => {
                  const newChannels = e.target.checked
                    ? [...selectedChannels, channel]
                    : selectedChannels.filter((c) => c !== channel);
                  handleUpdateChannels(newChannels);
                }}
                className="rounded border-slate-300"
              />
              <span className="capitalize text-slate-700 font-medium">{channel}</span>
            </label>
          ))}
        </div>
      </section>

      {/* Discord Configuration */}
      {selectedChannels.includes("discord") && (
        <section className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="mb-4 text-lg font-semibold text-slate-900">
            Discord Webhook Configuration
          </h2>

          {prefs.discord_webhook_url ? (
            <div className="space-y-4">
              <div className="rounded bg-green-50 p-3 border border-green-200">
                <p className="text-sm text-green-800 font-medium">
                  ✓ Discord webhook configured
                </p>
              </div>

              <div className="flex gap-3">
                <button
                  onClick={handleTestDiscord}
                  className="rounded bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
                >
                  Test Webhook
                </button>
                <button
                  onClick={handleRemoveDiscord}
                  className="rounded bg-red-100 px-4 py-2 text-sm font-medium text-red-800 hover:bg-red-200"
                >
                  Remove Webhook
                </button>
              </div>
            </div>
          ) : showDiscordInput ? (
            <div className="space-y-3">
              <input
                type="url"
                value={discordUrl}
                onChange={(e) => setDiscordUrl(e.target.value)}
                placeholder="https://discordapp.com/api/webhooks/..."
                className="w-full rounded border border-slate-300 px-3 py-2 text-sm focus:border-brand focus:outline-none"
              />
              <div className="flex gap-3">
                <button
                  onClick={handleAddDiscord}
                  className="rounded bg-brand px-4 py-2 text-sm font-medium text-white hover:bg-brand-dark"
                >
                  Add Webhook
                </button>
                <button
                  onClick={() => setShowDiscordInput(false)}
                  className="rounded border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
                >
                  Cancel
                </button>
              </div>
            </div>
          ) : (
            <button
              onClick={() => setShowDiscordInput(true)}
              className="rounded bg-slate-200 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-300"
            >
              Add Discord Webhook
            </button>
          )}
        </section>
      )}

      {/* Notification Frequency */}
      <section className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
        <h2 className="mb-4 text-lg font-semibold text-slate-900">
          Notification Frequency
        </h2>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-700">
              Delivery Mode
            </label>
            <select
              value={frequency}
              onChange={(e) => setFrequency(e.target.value)}
              className="mt-2 w-full rounded border border-slate-300 px-3 py-2 text-sm focus:border-brand focus:outline-none"
            >
              <option value="immediate">Immediate (as soon as match found)</option>
              <option value="daily">Daily Digest</option>
              <option value="weekly">Weekly Digest</option>
            </select>
          </div>

          {frequency !== "immediate" && (
            <div>
              <label className="block text-sm font-medium text-slate-700">
                Digest Time
              </label>
              <input
                type="time"
                value={digestTime}
                onChange={(e) => setDigestTime(e.target.value)}
                className="mt-2 rounded border border-slate-300 px-3 py-2 text-sm focus:border-brand focus:outline-none"
              />
            </div>
          )}

          <button
            onClick={handleUpdateFrequency}
            className="rounded bg-brand px-4 py-2 text-sm font-medium text-white hover:bg-brand-dark"
          >
            Save Frequency Settings
          </button>
        </div>
      </section>

      {/* Quiet Hours */}
      <section className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
        <h2 className="mb-4 text-lg font-semibold text-slate-900">Quiet Hours</h2>

        <div className="space-y-4">
          <label className="flex items-center gap-3">
            <input
              type="checkbox"
              checked={quietHoursEnabled}
              onChange={(e) => setQuietHoursEnabled(e.target.checked)}
              className="rounded border-slate-300"
            />
            <span className="font-medium text-slate-700">
              Enable quiet hours (no notifications during this time)
            </span>
          </label>

          {quietHoursEnabled && (
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-slate-700">
                  Start Time
                </label>
                <input
                  type="time"
                  value={quietStart}
                  onChange={(e) => setQuietStart(e.target.value)}
                  className="mt-2 w-full rounded border border-slate-300 px-3 py-2 text-sm focus:border-brand focus:outline-none"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700">
                  End Time
                </label>
                <input
                  type="time"
                  value={quietEnd}
                  onChange={(e) => setQuietEnd(e.target.value)}
                  className="mt-2 w-full rounded border border-slate-300 px-3 py-2 text-sm focus:border-brand focus:outline-none"
                />
              </div>
            </div>
          )}

          <button
            onClick={handleUpdateQuietHours}
            className="rounded bg-brand px-4 py-2 text-sm font-medium text-white hover:bg-brand-dark"
          >
            Save Quiet Hours
          </button>
        </div>
      </section>

      {/* Rate Limiting */}
      <section className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
        <h2 className="mb-4 text-lg font-semibold text-slate-900">
          Rate Limiting
        </h2>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-700">
              Maximum Notifications Per Day
            </label>
            <input
              type="number"
              min="1"
              max="100"
              value={maxPerDay}
              onChange={(e) => setMaxPerDay(parseInt(e.target.value))}
              className="mt-2 w-full max-w-xs rounded border border-slate-300 px-3 py-2 text-sm focus:border-brand focus:outline-none"
            />
            <p className="mt-2 text-xs text-slate-500">
              Prevents notification overload by limiting daily alerts
            </p>
          </div>

          <button
            onClick={handleUpdateMaxPerDay}
            className="rounded bg-brand px-4 py-2 text-sm font-medium text-white hover:bg-brand-dark"
          >
            Save Rate Limit
          </button>
        </div>
      </section>

      {/* Info Section */}
      <section className="rounded-lg border border-blue-200 bg-blue-50 p-4">
        <h3 className="font-semibold text-blue-900">💡 Tips</h3>
        <ul className="mt-2 space-y-1 text-sm text-blue-800">
          <li>
            • Enable multiple channels to get alerts via email, Discord, and SMS
          </li>
          <li>
            • Use quiet hours to avoid notifications during sleep or work
          </li>
          <li>
            • Set a daily max to prevent too many alerts from reaching you
          </li>
          <li>
            • Test your Discord webhook to make sure it&apos;s working correctly
          </li>
        </ul>
      </section>
    </div>
  );
}
