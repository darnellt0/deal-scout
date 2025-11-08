"use client";

import { useState, useCallback } from "react";
import { CreateDealAlertRuleRequest } from "../lib/api";

const CONDITIONS = ["poor", "fair", "good", "great", "excellent"];
const COMMON_CATEGORIES = [
  "Electronics",
  "Furniture",
  "Clothing",
  "Books",
  "Sports",
  "Toys",
  "Home & Garden",
  "Appliances",
];
const CHANNELS = ["email", "discord", "sms", "push"];

interface CreateAlertModalProps {
  onSubmit: (data: CreateDealAlertRuleRequest) => Promise<void>;
  onClose: () => void;
}

export default function CreateAlertModal({
  onSubmit,
  onClose,
}: CreateAlertModalProps) {
  const [name, setName] = useState("");
  const [keywords, setKeywords] = useState("");
  const [excludeKeywords, setExcludeKeywords] = useState("");
  const [categories, setCategories] = useState<string[]>([]);
  const [condition, setCondition] = useState<string>("");
  const [minPrice, setMinPrice] = useState<string>("");
  const [maxPrice, setMaxPrice] = useState<string>("");
  const [location, setLocation] = useState("");
  const [radiusMi, setRadiusMi] = useState<string>("");
  const [minDealScore, setMinDealScore] = useState<string>("");
  const [notificationChannels, setNotificationChannels] = useState<string[]>(["email"]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string>();

  const handleCategoryToggle = useCallback((cat: string) => {
    setCategories((prev) =>
      prev.includes(cat) ? prev.filter((c) => c !== cat) : [...prev, cat]
    );
  }, []);

  const handleChannelToggle = useCallback((channel: string) => {
    setNotificationChannels((prev) =>
      prev.includes(channel)
        ? prev.filter((c) => c !== channel)
        : [...prev, channel]
    );
  }, []);

  const handleSubmit = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();
      setError(undefined);

      if (!name.trim()) {
        setError("Rule name is required");
        return;
      }

      try {
        setIsSubmitting(true);
        const data: CreateDealAlertRuleRequest = {
          name: name.trim(),
          keywords: keywords
            .split(",")
            .map((k) => k.trim())
            .filter((k) => k),
          exclude_keywords: excludeKeywords
            .split(",")
            .map((k) => k.trim())
            .filter((k) => k),
          categories: categories.length > 0 ? categories : undefined,
          condition: condition || undefined,
          min_price: minPrice ? parseFloat(minPrice) : undefined,
          max_price: maxPrice ? parseFloat(maxPrice) : undefined,
          location: location || undefined,
          radius_mi: radiusMi ? parseInt(radiusMi) : undefined,
          min_deal_score: minDealScore ? parseFloat(minDealScore) : undefined,
          notification_channels: notificationChannels,
        };

        await onSubmit(data);
      } catch (err) {
        const msg = err instanceof Error ? err.message : "Failed to create rule";
        setError(msg);
      } finally {
        setIsSubmitting(false);
      }
    },
    [
      name,
      keywords,
      excludeKeywords,
      categories,
      condition,
      minPrice,
      maxPrice,
      location,
      radiusMi,
      minDealScore,
      notificationChannels,
      onSubmit,
    ]
  );

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="w-full max-w-2xl rounded-lg bg-white p-6 shadow-lg">
        <h2 className="mb-4 text-lg font-semibold text-slate-900">
          Create Deal Alert Rule
        </h2>

        {error && (
          <div className="mb-4 rounded border border-red-200 bg-red-50 p-3">
            <p className="text-sm text-red-800">{error}</p>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Rule Name */}
          <div>
            <label className="block text-sm font-medium text-slate-700">
              Rule Name *
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g., Gaming Laptops Under $800"
              className="mt-2 w-full rounded border border-slate-300 px-3 py-2 text-sm focus:border-brand focus:outline-none"
            />
          </div>

          {/* Keywords */}
          <div>
            <label className="block text-sm font-medium text-slate-700">
              Keywords (comma-separated)
            </label>
            <input
              type="text"
              value={keywords}
              onChange={(e) => setKeywords(e.target.value)}
              placeholder="e.g., gaming, laptop, RTX"
              className="mt-2 w-full rounded border border-slate-300 px-3 py-2 text-sm focus:border-brand focus:outline-none"
            />
            <p className="mt-1 text-xs text-slate-500">
              Matches if any keyword appears in title or description (OR logic)
            </p>
          </div>

          {/* Exclude Keywords */}
          <div>
            <label className="block text-sm font-medium text-slate-700">
              Exclude Keywords (comma-separated)
            </label>
            <input
              type="text"
              value={excludeKeywords}
              onChange={(e) => setExcludeKeywords(e.target.value)}
              placeholder="e.g., broken, damaged, parts"
              className="mt-2 w-full rounded border border-slate-300 px-3 py-2 text-sm focus:border-brand focus:outline-none"
            />
            <p className="mt-1 text-xs text-slate-500">
              Excludes any listing containing these keywords
            </p>
          </div>

          {/* Categories */}
          <div>
            <label className="block text-sm font-medium text-slate-700">
              Categories
            </label>
            <div className="mt-2 flex flex-wrap gap-2">
              {COMMON_CATEGORIES.map((cat) => (
                <button
                  key={cat}
                  type="button"
                  onClick={() => handleCategoryToggle(cat)}
                  className={`rounded-full px-3 py-1 text-xs font-medium transition-colors ${
                    categories.includes(cat)
                      ? "bg-brand text-white"
                      : "border border-slate-300 text-slate-700 hover:border-brand"
                  }`}
                >
                  {cat}
                </button>
              ))}
            </div>
          </div>

          {/* Price Range */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-slate-700">
                Min Price ($)
              </label>
              <input
                type="number"
                value={minPrice}
                onChange={(e) => setMinPrice(e.target.value)}
                placeholder="0"
                className="mt-2 w-full rounded border border-slate-300 px-3 py-2 text-sm focus:border-brand focus:outline-none"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700">
                Max Price ($)
              </label>
              <input
                type="number"
                value={maxPrice}
                onChange={(e) => setMaxPrice(e.target.value)}
                placeholder="9999"
                className="mt-2 w-full rounded border border-slate-300 px-3 py-2 text-sm focus:border-brand focus:outline-none"
              />
            </div>
          </div>

          {/* Condition */}
          <div>
            <label className="block text-sm font-medium text-slate-700">
              Minimum Condition
            </label>
            <select
              value={condition}
              onChange={(e) => setCondition(e.target.value)}
              className="mt-2 w-full rounded border border-slate-300 px-3 py-2 text-sm focus:border-brand focus:outline-none"
            >
              <option value="">Any condition</option>
              {CONDITIONS.map((c) => (
                <option key={c} value={c}>
                  {c.charAt(0).toUpperCase() + c.slice(1)}
                </option>
              ))}
            </select>
          </div>

          {/* Location */}
          <div className="grid grid-cols-3 gap-4">
            <div className="col-span-2">
              <label className="block text-sm font-medium text-slate-700">
                Location
              </label>
              <input
                type="text"
                value={location}
                onChange={(e) => setLocation(e.target.value)}
                placeholder="e.g., San Jose, CA"
                className="mt-2 w-full rounded border border-slate-300 px-3 py-2 text-sm focus:border-brand focus:outline-none"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700">
                Radius (mi)
              </label>
              <input
                type="number"
                value={radiusMi}
                onChange={(e) => setRadiusMi(e.target.value)}
                placeholder="50"
                className="mt-2 w-full rounded border border-slate-300 px-3 py-2 text-sm focus:border-brand focus:outline-none"
              />
            </div>
          </div>

          {/* Deal Score */}
          <div>
            <label className="block text-sm font-medium text-slate-700">
              Minimum Deal Score (0-1)
            </label>
            <input
              type="number"
              step="0.1"
              min="0"
              max="1"
              value={minDealScore}
              onChange={(e) => setMinDealScore(e.target.value)}
              placeholder="0.5"
              className="mt-2 w-full rounded border border-slate-300 px-3 py-2 text-sm focus:border-brand focus:outline-none"
            />
          </div>

          {/* Notification Channels */}
          <div>
            <label className="block text-sm font-medium text-slate-700">
              Notification Channels *
            </label>
            <div className="mt-2 space-y-2">
              {CHANNELS.map((channel) => (
                <label key={channel} className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={notificationChannels.includes(channel)}
                    onChange={() => handleChannelToggle(channel)}
                    className="rounded border-slate-300"
                  />
                  <span className="text-sm capitalize text-slate-700">
                    {channel}
                  </span>
                </label>
              ))}
            </div>
          </div>

          {/* Buttons */}
          <div className="flex gap-3">
            <button
              type="submit"
              disabled={isSubmitting}
              className="flex-1 rounded bg-brand px-4 py-2 text-sm font-medium text-white hover:bg-brand-dark disabled:opacity-50"
            >
              {isSubmitting ? "Creating..." : "Create Alert Rule"}
            </button>
            <button
              type="button"
              onClick={onClose}
              className="flex-1 rounded border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
