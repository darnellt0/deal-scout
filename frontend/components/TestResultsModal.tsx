"use client";

import { Deal } from "../lib/api";

interface TestResultsModalProps {
  results: Deal[];
  onClose: () => void;
}

export default function TestResultsModal({
  results,
  onClose,
}: TestResultsModalProps) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="w-full max-w-4xl rounded-lg bg-white p-6 shadow-lg">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-slate-900">
            Test Results ({results.length} matches)
          </h2>
          <button
            onClick={onClose}
            className="text-slate-500 hover:text-slate-700"
          >
            ✕
          </button>
        </div>

        {results.length === 0 ? (
          <div className="rounded-lg border border-dashed border-slate-300 p-8 text-center">
            <p className="text-slate-600">No listings match this rule.</p>
          </div>
        ) : (
          <div className="max-h-96 overflow-y-auto space-y-3">
            {results.map((deal) => (
              <div
                key={deal.id}
                className="flex items-start gap-4 rounded-lg border border-slate-200 p-3 hover:bg-slate-50"
              >
                {deal.thumbnail_url && (
                  <img
                    src={deal.thumbnail_url}
                    alt={deal.title}
                    className="h-16 w-16 rounded object-cover"
                  />
                )}

                <div className="flex-1 min-w-0">
                  <h3 className="font-medium text-slate-900 truncate">
                    {deal.title}
                  </h3>
                  <div className="mt-1 flex flex-wrap gap-3 text-sm text-slate-600">
                    <span className="font-semibold text-green-600">
                      ${deal.price}
                    </span>
                    {deal.condition && (
                      <span className="capitalize">{deal.condition}</span>
                    )}
                    {deal.deal_score && (
                      <span>
                        Score:{" "}
                        <span className="font-medium">
                          {(deal.deal_score * 100).toFixed(0)}%
                        </span>
                      </span>
                    )}
                  </div>

                  {deal.url && (
                    <a
                      href={deal.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="mt-2 inline-block text-xs text-brand hover:underline"
                    >
                      View Listing →
                    </a>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}

        <div className="mt-6 flex justify-end">
          <button
            onClick={onClose}
            className="rounded bg-brand px-4 py-2 text-sm font-medium text-white hover:bg-brand-dark"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
