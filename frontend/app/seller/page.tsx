"use client";

import useSWR from "swr";
import { UploadForm } from "../../components/UploadForm";
import { fetchSnapJobs, SnapJobSummary } from "../../lib/api";

export default function SellerPage() {
  const { data: snapJobs } = useSWR<SnapJobSummary[]>(
    "snap-jobs",
    fetchSnapJobs,
    { refreshInterval: 60_000 }
  );
  const hasPrepared = (snapJobs?.length ?? 0) > 0;

  return (
    <div className="flex flex-col gap-6">
      <header>
        <h1 className="text-2xl font-semibold text-slate-900">
          Seller Snap Studio
        </h1>
        <p className="text-sm text-slate-500">
          Upload photos and Deal Scout will detect the item, clean images, draft listings,
          and prep one-click cross posts to eBay and other marketplaces.
        </p>
      </header>
      {!hasPrepared && (
        <div className="rounded-lg border border-dashed border-brand px-6 py-4 text-sm text-slate-600">
          No prepared snap jobs yet. Run: <code>python scripts/seed_snap_items.py</code>{" "}
          to load demo-ready items.
        </div>
      )}
      {hasPrepared && (
        <section className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
          <h2 className="text-sm font-semibold text-slate-800">
            Prepared Snap-to-Sell Drafts
          </h2>
          <ul className="mt-3 space-y-3 text-sm">
            {snapJobs?.map((job) => (
              <li
                key={job.job_id}
                className="rounded border border-slate-100 bg-slate-50 px-4 py-3"
              >
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-semibold text-slate-900">
                      {job.title ?? "Draft in progress"}
                    </p>
                    <p className="text-xs text-slate-500">
                      {job.condition_guess ?? "condition tbd"} · Suggested $
                      {(job.price_suggestion_cents ?? 0) / 100}
                    </p>
                  </div>
                  <span className="rounded bg-brand/10 px-2 py-1 text-xs font-semibold text-brand-dark">
                    {job.status}
                  </span>
                </div>
              </li>
            ))}
          </ul>
        </section>
      )}
      <UploadForm />
      <section className="rounded-lg border border-slate-200 bg-white p-6 text-sm text-slate-600">
        <h2 className="text-lg font-semibold text-slate-900">
          What happens next?
        </h2>
        <ol className="mt-3 list-decimal space-y-2 pl-5">
          <li>Vision pipeline identifies category, attributes, and condition.</li>
          <li>Images are cleaned, brightened, and background removed (when enabled).</li>
          <li>
            Pricing engine pulls comps and suggests competitive pricing for San
            Jose, CA.
          </li>
          <li>
            Auto copywriter drafts your title, description, and cross-post metadata.
          </li>
          <li>Ready-to-publish drafts appear in the Seller Dashboard.</li>
        </ol>
      </section>
    </div>
  );
}
