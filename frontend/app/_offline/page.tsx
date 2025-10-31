export default function Offline() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center gap-4 bg-slate-50 px-6 py-12 text-center text-slate-800">
      <h1 className="text-3xl font-semibold text-brand">Offline</h1>
      <p className="max-w-md text-base text-slate-600">
        You&rsquo;re offline right now. Recently viewed pages and cached assets
        are still available. Reconnect to get the latest Deal Scout updates.
      </p>
    </main>
  );
}
