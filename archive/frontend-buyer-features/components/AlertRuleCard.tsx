"use client";

import { DealAlertRule } from "../lib/api";
import { formatDistanceToNow } from "date-fns";

interface AlertRuleCardProps {
  rule: DealAlertRule;
  onTest: (ruleId: number) => Promise<void>;
  onToggle: (rule: DealAlertRule) => Promise<void>;
  onDelete: (ruleId: number) => Promise<void>;
  isTesting: boolean;
}

export default function AlertRuleCard({
  rule,
  onTest,
  onToggle,
  onDelete,
  isTesting,
}: AlertRuleCardProps) {
  const getChannelIcon = (channel: string) => {
    switch (channel) {
      case "email":
        return "📧";
      case "discord":
        return "🎮";
      case "sms":
        return "📱";
      case "push":
        return "🔔";
      default:
        return "📬";
    }
  };

  const lastTriggeredAt = rule.last_triggered_at
    ? new Date(rule.last_triggered_at)
    : null;

  return (
    <div
      className={`rounded-lg border-2 p-4 ${
        rule.enabled
          ? "border-brand/30 bg-brand/5"
          : "border-slate-200 bg-slate-50"
      }`}
    >
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1">
          <div className="flex items-center gap-3">
            <h3 className="text-lg font-semibold text-slate-900">{rule.name}</h3>
            <span
              className={`rounded-full px-2 py-1 text-xs font-medium ${
                rule.enabled
                  ? "bg-green-100 text-green-800"
                  : "bg-slate-100 text-slate-800"
              }`}
            >
              {rule.enabled ? "Active" : "Paused"}
            </span>
          </div>

          {/* Rule Criteria */}
          <div className="mt-3 grid grid-cols-1 gap-3 md:grid-cols-2">
            {rule.keywords.length > 0 && (
              <div>
                <p className="text-xs font-medium text-slate-600">Keywords</p>
                <div className="mt-1 flex flex-wrap gap-1">
                  {rule.keywords.map((kw) => (
                    <span
                      key={kw}
                      className="rounded bg-slate-200 px-2 py-1 text-xs text-slate-700"
                    >
                      {kw}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {rule.exclude_keywords.length > 0 && (
              <div>
                <p className="text-xs font-medium text-slate-600">Exclude</p>
                <div className="mt-1 flex flex-wrap gap-1">
                  {rule.exclude_keywords.map((kw) => (
                    <span
                      key={kw}
                      className="rounded bg-red-100 px-2 py-1 text-xs text-red-700"
                    >
                      NOT {kw}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {(rule.min_price || rule.max_price) && (
              <div>
                <p className="text-xs font-medium text-slate-600">Price Range</p>
                <p className="mt-1 text-sm text-slate-700">
                  ${rule.min_price ?? 0} - ${rule.max_price ?? "∞"}
                </p>
              </div>
            )}

            {rule.categories.length > 0 && (
              <div>
                <p className="text-xs font-medium text-slate-600">Categories</p>
                <div className="mt-1 flex flex-wrap gap-1">
                  {rule.categories.map((cat) => (
                    <span
                      key={cat}
                      className="rounded bg-blue-100 px-2 py-1 text-xs text-blue-700"
                    >
                      {cat}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {rule.condition && (
              <div>
                <p className="text-xs font-medium text-slate-600">Condition</p>
                <p className="mt-1 text-sm text-slate-700 capitalize">
                  {rule.condition}+
                </p>
              </div>
            )}

            {rule.location && (
              <div>
                <p className="text-xs font-medium text-slate-600">Location</p>
                <p className="mt-1 text-sm text-slate-700">
                  {rule.location}
                  {rule.radius_mi && ` (${rule.radius_mi} mi radius)`}
                </p>
              </div>
            )}

            {rule.min_deal_score && (
              <div>
                <p className="text-xs font-medium text-slate-600">Min Deal Score</p>
                <p className="mt-1 text-sm text-slate-700">{rule.min_deal_score}</p>
              </div>
            )}
          </div>

          {/* Notifications & Last Triggered */}
          <div className="mt-3 flex flex-wrap items-center gap-4">
            <div className="flex items-center gap-2">
              <p className="text-xs font-medium text-slate-600">Notifications:</p>
              <div className="flex gap-1">
                {rule.notification_channels.map((channel) => (
                  <span key={channel} title={channel}>
                    {getChannelIcon(channel)}
                  </span>
                ))}
              </div>
            </div>

            {lastTriggeredAt && (
              <p className="text-xs text-slate-600">
                Last triggered:{" "}
                <span className="font-medium">
                  {formatDistanceToNow(lastTriggeredAt, { addSuffix: true })}
                </span>
              </p>
            )}
          </div>
        </div>

        {/* Actions */}
        <div className="flex flex-col gap-2">
          <button
            onClick={() => onTest(rule.id)}
            disabled={isTesting}
            className="whitespace-nowrap rounded bg-slate-200 px-3 py-1 text-xs font-medium text-slate-700 hover:bg-slate-300 disabled:opacity-50"
          >
            {isTesting ? "Testing..." : "Test Rule"}
          </button>

          <button
            onClick={() => onToggle(rule)}
            className={`whitespace-nowrap rounded px-3 py-1 text-xs font-medium ${
              rule.enabled
                ? "bg-yellow-100 text-yellow-800 hover:bg-yellow-200"
                : "bg-green-100 text-green-800 hover:bg-green-200"
            }`}
          >
            {rule.enabled ? "Pause" : "Resume"}
          </button>

          <button
            onClick={() => onDelete(rule.id)}
            className="whitespace-nowrap rounded bg-red-100 px-3 py-1 text-xs font-medium text-red-800 hover:bg-red-200"
          >
            Delete
          </button>
        </div>
      </div>
    </div>
  );
}
