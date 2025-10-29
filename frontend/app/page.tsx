import Link from "next/link";
import { AlertCard } from "../components/AlertCard";
import { fetchDeals } from "../lib/api";

export default async function HomePage() {
  const deals = await fetchDeals().catch(() => []);

  return (
    <div className="flex flex-col gap-8">
      <section>
        <h1 className="text-2xl font-semibold text-slate-900">
          Marketplace Radar
        </h1>
        <p className="text-sm text-slate-500">
          Live scan of Craigslist, eBay, OfferUp, and Facebook Marketplace within 50 miles of San Jose, CA.
        </p>
      </section>

      <section className="grid gap-4 md:grid-cols-2">
        {deals.length ? (
          deals.slice(0, 4).map((deal) => <AlertCard key={deal.id} deal={deal} />)
        ) : (
          <div className="rounded-lg border border-slate-200 bg-white p-6 text-sm text-slate-500">
            No deals yet. Trigger a scan from the Buyer Feed to populate results.
          </div>
        )}
      </section>

      <section className="grid gap-4 md:grid-cols-2">
        <div className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-slate-900">
            Buyer Feed
          </h2>
          <p className="mt-2 text-sm text-slate-500">
            Review the fresh finds, copy ready-to-send outreach, and jump on zero-dollar couch or island pickups instantly.
          </p>
          <Link
            href="/buyer"
            className="mt-4 inline-flex items-center text-brand hover:text-brand-dark"
          >
            Open Buyer Feed →
          </Link>
        </div>
        <div className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-slate-900">
            Sell Instantly
          </h2>
          <p className="mt-2 text-sm text-slate-500">
            Snap photos, let Deal Scout detect the item, clean images, generate pricing, and prep one-click cross posts.
          </p>
          <Link
            href="/seller"
            className="mt-4 inline-flex items-center text-brand hover:text-brand-dark"
          >
            Launch Seller Assist →
          </Link>
        </div>
      </section>
    </div>
  );
}
