'use client';

import { useEffect, useState } from "react";

type BeforeInstallPromptEvent = Event & {
  prompt: () => Promise<void>;
  userChoice: Promise<{ outcome: "accepted" | "dismissed"; platform: string }>;
};

export default function PwaInstall() {
  const [promptEvent, setPromptEvent] = useState<BeforeInstallPromptEvent | null>(null);
  const [supported, setSupported] = useState(false);

  useEffect(() => {
    const handler = (event: Event) => {
      const prompt = event as BeforeInstallPromptEvent;
      prompt.preventDefault?.();
      setPromptEvent(prompt);
      setSupported(true);
    };

    window.addEventListener("beforeinstallprompt", handler);
    return () => window.removeEventListener("beforeinstallprompt", handler);
  }, []);

  const install = async () => {
    if (!promptEvent) return;

    await promptEvent.prompt();
    await promptEvent.userChoice;
    setPromptEvent(null);
  };

  if (!supported) return null;

  return (
    <button
      onClick={install}
      className="rounded border border-brand px-3 py-1 text-sm font-semibold text-brand transition hover:bg-brand hover:text-white"
    >
      Install Deal Scout
    </button>
  );
}
