import Link from "next/link";

export default function HomePage() {
  return (
    <div className="flex flex-col gap-8">
      <section className="text-center">
        <h1 className="text-4xl font-bold text-slate-900">
          Deal Scout
        </h1>
        <p className="mt-3 text-lg text-slate-600">
          Cross-post your items to multiple marketplaces from one photo
        </p>
      </section>

      <section className="mx-auto max-w-3xl rounded-lg border border-slate-200 bg-white p-8 shadow-sm">
        <h2 className="text-2xl font-semibold text-slate-900">
          How It Works
        </h2>
        <ol className="mt-4 space-y-4 text-slate-700">
          <li className="flex gap-3">
            <span className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full bg-brand text-sm font-bold text-white">
              1
            </span>
            <div>
              <strong className="text-slate-900">Take a photo</strong>
              <p className="text-sm text-slate-600">
                Upload a picture of the item you want to sell
              </p>
            </div>
          </li>
          <li className="flex gap-3">
            <span className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full bg-brand text-sm font-bold text-white">
              2
            </span>
            <div>
              <strong className="text-slate-900">AI generates your listing</strong>
              <p className="text-sm text-slate-600">
                Get auto-detected titles, descriptions, categories, and pricing suggestions
              </p>
            </div>
          </li>
          <li className="flex gap-3">
            <span className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full bg-brand text-sm font-bold text-white">
              3
            </span>
            <div>
              <strong className="text-slate-900">Publish everywhere</strong>
              <p className="text-sm text-slate-600">
                Cross-post to eBay, Facebook Marketplace, and OfferUp with one click
              </p>
            </div>
          </li>
        </ol>

        <div className="mt-8 text-center">
          <Link
            href="/seller"
            className="inline-flex items-center justify-center rounded-lg bg-brand px-8 py-4 text-lg font-semibold text-white shadow-md hover:bg-brand-dark transition-colors"
          >
            Start Selling →
          </Link>
        </div>
      </section>

      <section className="mx-auto max-w-3xl">
        <h2 className="text-xl font-semibold text-slate-900">
          Supported Marketplaces
        </h2>
        <div className="mt-4 grid gap-4 md:grid-cols-3">
          <div className="rounded-lg border border-slate-200 bg-white p-4 text-center">
            <div className="text-2xl font-bold text-blue-600">eBay</div>
            <p className="mt-1 text-xs text-slate-500">
              Reach millions of buyers
            </p>
          </div>
          <div className="rounded-lg border border-slate-200 bg-white p-4 text-center">
            <div className="text-2xl font-bold text-blue-500">Facebook</div>
            <p className="mt-1 text-xs text-slate-500">
              Sell locally with ease
            </p>
          </div>
          <div className="rounded-lg border border-slate-200 bg-white p-4 text-center">
            <div className="text-2xl font-bold text-green-600">OfferUp</div>
            <p className="mt-1 text-xs text-slate-500">
              Connect with local buyers
            </p>
          </div>
        </div>
      </section>
    </div>
  );
}
