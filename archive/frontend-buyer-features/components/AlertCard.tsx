"use client";

import Image from "next/image";
import { Deal } from "../lib/api";
import { getDemoBadge } from "../dev/demo-badges";

type AlertCardProps = {
  deal: Deal;
};

export function AlertCard({ deal }: AlertCardProps) {
  const demoBadge =
    process.env.NODE_ENV !== "production" ? getDemoBadge(deal) : null;

  return (
    <article className="flex flex-col gap-3 rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
      <div className="flex items-start justify-between">
        <div>
          <h3 className="text-lg font-semibold text-slate-900">{deal.title}</h3>
          <p className="text-sm text-slate-500">
            ${deal.price.toFixed(0)} · {deal.condition} · score {deal.deal_score}
          </p>
        </div>
        <div className="flex flex-col items-end gap-2">
          <span className="rounded bg-brand/10 px-2 py-1 text-xs font-semibold text-brand-dark">
            {deal.deal_score >= 85 ? "Hot Deal" : "Watch"}
          </span>
          {demoBadge && (
            <span className="rounded border border-brand px-2 py-1 text-xs font-semibold text-brand-dark">
              {demoBadge}
            </span>
          )}
        </div>
      </div>
      {deal.thumbnail_url && (
        <div className="relative h-48 w-full overflow-hidden rounded-md bg-slate-100">
          <Image
            src={deal.thumbnail_url}
            alt={deal.title}
            fill
            className="object-cover"
          />
        </div>
      )}
      <div className="flex items-center gap-3 text-sm">
        <button
          className="rounded bg-brand px-3 py-2 font-medium text-white shadow hover:bg-brand-dark"
          onClick={() => {
            navigator.clipboard.writeText(deal.auto_message);
          }}
        >
          Copy Message
        </button>
        <a
          href={deal.url}
          target="_blank"
          className="text-brand hover:text-brand-dark"
          rel="noreferrer"
        >
          Open Listing
        </a>
      </div>
    </article>
  );
}
