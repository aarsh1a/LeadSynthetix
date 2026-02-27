"use client";

import { useCallback, useState } from "react";
import { uploadPdf } from "@/lib/api";

export default function UploadSection() {
  const [dragging, setDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleFile = useCallback(
    async (file: File | null) => {
      if (!file || !file.name.toLowerCase().endsWith(".pdf")) {
        setError("PDF files only");
        return;
      }
      setError(null);
      setUploading(true);
      try {
        const result = await uploadPdf(file);
        console.log("Upload result:", result);
        window.dispatchEvent(new CustomEvent("upload-success", { detail: result }));
      } catch (e) {
        setError(e instanceof Error ? e.message : "Upload failed");
      } finally {
        setUploading(false);
      }
    },
    []
  );

  const onDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragging(false);
    handleFile(e.dataTransfer.files[0] ?? null);
  };

  const onDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setDragging(true);
  };

  const onDragLeave = () => setDragging(false);

  const onInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    handleFile(e.target.files?.[0] ?? null);
    e.target.value = "";
  };

  return (
    <section
      onDrop={onDrop}
      onDragOver={onDragOver}
      onDragLeave={onDragLeave}
      className={`
        relative rounded-xl border-2 border-dashed p-8 transition-all duration-300
        ${dragging
          ? "border-accent-teal/60 bg-accent-teal/5"
          : "border-surface-500/50 bg-surface-800/50 hover:border-surface-500 hover:bg-surface-800/70"}
      `}
    >
      <input
        type="file"
        accept=".pdf"
        onChange={onInputChange}
        disabled={uploading}
        className="absolute inset-0 cursor-pointer opacity-0"
      />
      <div className="flex flex-col items-center gap-3 text-center">
        <div
          className={`
            flex h-12 w-12 items-center justify-center rounded-lg
            ${dragging ? "bg-accent-teal/20" : "bg-surface-700"}
          `}
        >
          <svg
            className={`h-6 w-6 ${dragging ? "text-accent-teal" : "text-slate-400"}`}
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
            />
          </svg>
        </div>
        <p className="text-sm text-slate-300">
          {uploading ? (
            <span className="text-accent-teal">Processing PDF...</span>
          ) : dragging ? (
            "Drop PDF here"
          ) : (
            "Drag & drop PDF or click to upload"
          )}
        </p>
        <p className="text-xs text-slate-500">Financial statements, loan docs</p>
        {error && (
          <p className="text-xs text-accent-rose animate-fade-in">{error}</p>
        )}
      </div>
    </section>
  );
}
