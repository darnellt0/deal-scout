"use client";

import { useCallback, useState } from "react";
import useSWR from "swr";
import { UploadForm } from "../../components/UploadForm";
import { QuickListingModal } from "../../components/QuickListingModal";
import {
  deleteSnapJob,
  fetchSnapJobs,
  publishSnapJob,
  PublishSnapJobRequest,
  SnapJobSummary,
  fetchCrossPosts,
  CrossPostListing,
} from "../../lib/api";

export default function SellerPage() {
  const [isQuickListingOpen, setIsQuickListingOpen] = useState(false);
  const { data: snapJobs, mutate } = useSWR<SnapJobSummary[]>(
    "snap-jobs",
    fetchSnapJobs,
    { refreshInterval: 60_000 }
  );
  const { data: crossPosts, mutate: mutateCrossPosts } =
    useSWR<CrossPostListing[]>("cross-posts", fetchCrossPosts, {
      refreshInterval: 60_000,
    });
  const hasPrepared = (snapJobs?.length ?? 0) > 0;
  const crossPostList = crossPosts ?? [];
  const pendingCrossPosts = crossPostList.filter(
    (entry) => entry.status.toLowerCase() === "pending"
  );
  const completedCrossPosts = crossPostList.filter(
    (entry) => entry.status.toLowerCase() !== "pending"
  );

  const [publishJobId, setPublishJobId] = useState<number | null>(null);
  const [publishPrice, setPublishPrice] = useState<string>("");
  const [publishPlatforms, setPublishPlatforms] = useState<string[]>(["ebay"]);
  const [publishNotes, setPublishNotes] = useState<string>("");
  const [publishStatus, setPublishStatus] = useState<string>();
  const [publishError, setPublishError] = useState<string>();
  const [isPublishing, setIsPublishing] = useState(false);
  const [deletingJobId, setDeletingJobId] = useState<number | null>(null);

  const platformOptions = ["ebay", "facebook", "offerup"];
  const formatDateTime = useCallback(
    (value: string) =>
      new Date(value).toLocaleString(undefined, {
        dateStyle: "short",
        timeStyle: "short",
      }),
    []
  );
  const formatPrice = useCallback(
    (amount: number) =>
      Intl.NumberFormat(undefined, {
        style: "currency",
        currency: "USD",
        maximumFractionDigits: 2,
      }).format(amount),
    []
  );
  const formatPlatform = useCallback(
    (value: string) => value.charAt(0).toUpperCase() + value.slice(1),
    []
  );

  const openPublishForm = useCallback(
    (job: SnapJobSummary) => {
      setPublishJobId(job.job_id);
      const suggested =
        job.price_suggestion_cents != null
          ? (job.price_suggestion_cents / 100).toFixed(2)
          : job.suggested_price != null
            ? job.suggested_price.toFixed(2)
            : "";
      setPublishPrice(suggested);
      setPublishPlatforms(["ebay"]);
      setPublishNotes("");
      setPublishError(undefined);
      setPublishStatus(undefined);
    },
    [setPublishJobId]
  );

  const cancelPublish = useCallback(() => {
    setPublishJobId(null);
    setPublishError(undefined);
  }, []);

  const togglePlatform = useCallback((platform: string) => {
    setPublishPlatforms((prev) =>
      prev.includes(platform)
        ? prev.filter((p) => p !== platform)
        : [...prev, platform]
    );
  }, []);

  const submitPublish = useCallback(async () => {
    if (!publishJobId) return;
    if (!publishPlatforms.length) {
      setPublishError("Select at least one platform.");
      return;
    }

    const parsedPrice = publishPrice.trim()
      ? Number(publishPrice.trim())
      : undefined;

    if (parsedPrice !== undefined && Number.isNaN(parsedPrice)) {
      setPublishError("Enter a valid price (e.g., 199.99).");
      return;
    }

    const payload: PublishSnapJobRequest = {
      snap_job_id: publishJobId,
      platforms: publishPlatforms,
      price: parsedPrice,
      notes: publishNotes.trim() || undefined,
    };

    setIsPublishing(true);
    setPublishError(undefined);
    setPublishStatus("Publishing listing...");

    try {
      await publishSnapJob(publishJobId, payload);
      setPublishStatus("Listing sent to cross-post queue.");
      setPublishJobId(null);
      setPublishPrice("");
      setPublishNotes("");
      await mutate();
      await mutateCrossPosts();
      setTimeout(() => setPublishStatus(undefined), 3000);
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Failed to publish listing.";
      setPublishError(message);
      setPublishStatus(undefined);
    } finally {
      setIsPublishing(false);
    }
  }, [
    mutate,
    mutateCrossPosts,
    publishJobId,
    publishNotes,
    publishPlatforms,
    publishPrice,
  ]);

  const handleDelete = useCallback(
    async (job: SnapJobSummary) => {
      if (!window.confirm("Delete this draft?")) {
        return;
      }
      setDeletingJobId(job.job_id);
      setPublishError(undefined);
      setPublishStatus("Deleting draft...");
      try {
        await deleteSnapJob(job.job_id);
        if (publishJobId === job.job_id) {
          setPublishJobId(null);
        }
        await mutate();
        setPublishStatus("Draft removed.");
        setTimeout(() => setPublishStatus(undefined), 2500);
      } catch (err) {
        const message =
          err instanceof Error ? err.message : "Failed to delete draft.";
        setPublishError(message);
        setPublishStatus(undefined);
      } finally {
        setDeletingJobId(null);
      }
    },
    [mutate, publishJobId]
  );

  return (
    <div className="flex flex-col gap-6">
      <header className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900">
            Seller Snap Studio
          </h1>
          <p className="text-sm text-slate-500">
            Upload photos and Deal Scout will detect the item, clean images, draft listings,
            and prep one-click cross posts to eBay and other marketplaces.
          </p>
        </div>
        <button
          onClick={() => setIsQuickListingOpen(true)}
          className="inline-flex items-center justify-center rounded-lg bg-green-600 px-6 py-3 font-semibold text-white shadow hover:bg-green-700 transition-colors whitespace-nowrap"
        >
          <svg
            className="w-5 h-5 mr-2"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 4v16m8-8H4"
            />
          </svg>
          Quick List Item
        </button>
      </header>
      {publishStatus && (
        <div className="rounded-lg border border-green-200 bg-green-50 p-4 text-sm text-green-800">
          {publishStatus}
        </div>
      )}
      {publishError && (
        <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-800">
          {publishError}
        </div>
      )}
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
                  <div className="flex items-center gap-2">
                    <span className="rounded bg-brand/10 px-2 py-1 text-xs font-semibold text-brand-dark">
                      {job.status}
                    </span>
                    {job.status !== "published" && (
                      <button
                        onClick={() => handleDelete(job)}
                        disabled={deletingJobId === job.job_id}
                        className="rounded border border-red-200 px-3 py-1 text-xs font-medium text-red-700 hover:bg-red-50 disabled:cursor-not-allowed disabled:opacity-60"
                      >
                        {deletingJobId === job.job_id ? "Removing…" : "Delete"}
                      </button>
                    )}
                  </div>
                </div>
                {job.processed_images?.length ? (
                  <div className="mt-3 grid grid-cols-3 gap-2">
                    {job.processed_images.slice(0, 3).map((img, idx) => (
                      <img
                        key={idx}
                        src={`data:image/jpeg;base64,${img}`}
                        alt={`${job.title ?? "Draft"} preview ${idx + 1}`}
                        className="h-20 w-full rounded border border-slate-200 object-cover"
                      />
                    ))}
                  </div>
                ) : null}
                {job.status === "ready" ? (
                  publishJobId === job.job_id ? (
                    <div className="mt-3 space-y-3 rounded border border-slate-200 bg-white p-4 text-sm">
                      <div>
                        <label className="block text-sm font-medium text-slate-700">
                          Listing Price ($)
                        </label>
                        <input
                          type="number"
                          step="0.01"
                          value={publishPrice}
                          onChange={(e) => setPublishPrice(e.target.value)}
                          className="mt-1 w-full rounded border border-slate-300 px-3 py-2 text-sm focus:border-brand focus:outline-none"
                          placeholder="e.g. 199.99"
                        />
                      </div>
                      <div>
                        <span className="block text-sm font-medium text-slate-700">
                          Cross-post to
                        </span>
                        <div className="mt-2 flex flex-wrap gap-3">
                          {platformOptions.map((platform) => (
                            <label
                              key={platform}
                              className="flex items-center gap-2 text-sm text-slate-700"
                            >
                              <input
                                type="checkbox"
                                checked={publishPlatforms.includes(platform)}
                                onChange={() => togglePlatform(platform)}
                                className="rounded border-slate-300"
                              />
                              <span className="capitalize">{platform}</span>
                            </label>
                          ))}
                        </div>
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-slate-700">
                          Notes (optional)
                        </label>
                        <textarea
                          rows={2}
                          value={publishNotes}
                          onChange={(e) => setPublishNotes(e.target.value)}
                          className="mt-1 w-full rounded border border-slate-300 px-3 py-2 text-sm focus:border-brand focus:outline-none"
                          placeholder="Any special instructions for this listing?"
                        />
                      </div>
                      <div className="flex flex-wrap gap-3">
                        <button
                          onClick={submitPublish}
                          disabled={isPublishing}
                          className="rounded bg-green-600 px-4 py-2 text-sm font-medium text-white hover:bg-green-700 disabled:cursor-not-allowed disabled:opacity-60"
                        >
                          {isPublishing ? "Publishing..." : "Publish Listing"}
                        </button>
                        <button
                          type="button"
                          onClick={cancelPublish}
                          className="rounded border border-slate-300 px-4 py-2 text-sm font-medium text-slate-600 hover:bg-slate-100"
                        >
                          Cancel
                        </button>
                      </div>
                    </div>
                  ) : (
                    <button
                      onClick={() => openPublishForm(job)}
                      className="mt-3 rounded bg-indigo-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-indigo-700"
                    >
                      Publish Listing
                    </button>
                  )
                ) : null}
                {job.status === "published" && (
                  <p className="mt-3 text-sm text-green-700">
                    Published and pending cross-post confirmations.
                  </p>
                )}
              </li>
            ))}
          </ul>
        </section>
      )}
      <section className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
        <h2 className="text-sm font-semibold text-slate-800">
          Cross-Post Queue
        </h2>
        {crossPostList.length === 0 ? (
          <p className="mt-3 text-sm text-slate-600">
            No cross-post activity yet. Publish a Snap draft to populate this
            queue.
          </p>
        ) : (
          <div className="mt-3 space-y-4 text-sm">
            <div>
              <h3 className="font-semibold text-slate-700">Waiting to go live</h3>
              {pendingCrossPosts.length === 0 ? (
                <p className="mt-1 text-slate-500">
                  Nothing pending right now. Listings are either live or closed.
                </p>
              ) : (
                <ul className="mt-2 space-y-2">
                  {pendingCrossPosts.map((entry) => (
                    <li
                      key={entry.id}
                      className="rounded border border-indigo-100 bg-indigo-50 px-3 py-2"
                    >
                      <div className="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
                        <div>
                          <p className="font-medium text-slate-900">
                            {entry.item.title}
                          </p>
                          <p className="text-xs text-slate-500">
                            {formatPlatform(entry.platform)} ·{" "}
                            {formatPrice(entry.item.price)} · queued{" "}
                            {formatDateTime(entry.created_at)}
                          </p>
                          {entry.notes ? (
                            <p className="mt-1 text-xs text-slate-600">
                              Notes: {entry.notes}
                            </p>
                          ) : null}
                        </div>
                        <span className="self-start rounded bg-indigo-600/10 px-2 py-1 text-xs font-semibold text-indigo-700">
                          Pending
                        </span>
                      </div>
                    </li>
                  ))}
                </ul>
              )}
            </div>
            {completedCrossPosts.length > 0 && (
              <div>
                <h3 className="font-semibold text-slate-700">
                  Recent activity
                </h3>
                <ul className="mt-2 space-y-2">
                  {completedCrossPosts.slice(0, 8).map((entry) => (
                    <li
                      key={entry.id}
                      className="rounded border border-slate-200 bg-slate-50 px-3 py-2"
                    >
                      <div className="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
                        <div>
                          <p className="font-medium text-slate-900">
                            {entry.item.title}
                          </p>
                          <p className="text-xs text-slate-500">
                            {formatPlatform(entry.platform)} ·{" "}
                            {formatPrice(entry.item.price)} ·{" "}
                            {entry.status.toUpperCase()} ·{" "}
                            {formatDateTime(entry.created_at)}
                          </p>
                          {entry.listing_url ? (
                            <a
                              href={entry.listing_url}
                              target="_blank"
                              rel="noreferrer"
                              className="mt-1 inline-flex text-xs font-medium text-indigo-600 hover:text-indigo-700"
                            >
                              View marketplace listing
                            </a>
                          ) : null}
                        </div>
                        <span className="self-start rounded bg-slate-300/30 px-2 py-1 text-xs font-semibold text-slate-700">
                          {entry.status}
                        </span>
                      </div>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
      </section>
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

      {/* Quick Listing Modal */}
      <QuickListingModal
        isOpen={isQuickListingOpen}
        onClose={() => setIsQuickListingOpen(false)}
      />
    </div>
  );
}
