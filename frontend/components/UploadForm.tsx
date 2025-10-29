"use client";

import { useState } from "react";
import { submitSnap } from "../lib/api";

export function UploadForm() {
  const [files, setFiles] = useState<File[]>([]);
  const [status, setStatus] = useState<string>();
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!files.length) {
      setStatus("Please add at least one photo.");
      return;
    }
    setIsSubmitting(true);
    setStatus("Uploading...");
    try {
      const encoded = await Promise.all(files.map(encodeFile));
      const response = await submitSnap({ photos: encoded });
      setStatus(`Snap job queued. ID: ${response.job_id}`);
      setFiles([]);
    } catch (error) {
      if (error instanceof Error) {
        setStatus(error.message);
      } else {
        setStatus("Failed to submit snap.");
      }
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="flex flex-col gap-4 rounded-lg border border-dashed border-brand/40 bg-white p-6 shadow-sm"
    >
      <div>
        <h3 className="text-lg font-semibold text-slate-900">
          Upload photos to create a listing
        </h3>
        <p className="text-sm text-slate-500">
          Deal Scout will detect the item, clean your photos, suggest pricing, and prep cross-posting.
        </p>
      </div>
      <input
        type="file"
        accept="image/*"
        multiple
        onChange={(event) => {
          const target = event.target;
          if (!target.files) return;
          setFiles(Array.from(target.files));
        }}
        className="rounded border border-slate-200 px-3 py-2 text-sm"
      />
      <button
        type="submit"
        disabled={isSubmitting}
        className="inline-flex w-fit items-center justify-center rounded bg-brand px-4 py-2 font-medium text-white shadow hover:bg-brand-dark disabled:cursor-not-allowed disabled:opacity-60"
      >
        {isSubmitting ? "Processing..." : "Start Snap"}
      </button>
      {status && <p className="text-sm text-slate-600">{status}</p>}
    </form>
  );
}

async function encodeFile(file: File): Promise<string> {
  const arrayBuffer = await file.arrayBuffer();
  const bytes = new Uint8Array(arrayBuffer);
  let binary = "";
  for (let i = 0; i < bytes.byteLength; i += 1) {
    binary += String.fromCharCode(bytes[i]);
  }
  return btoa(binary);
}
