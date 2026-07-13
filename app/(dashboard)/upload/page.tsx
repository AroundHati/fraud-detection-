"use client";

import { useState, useEffect, useCallback, type DragEvent } from "react";
import Link from "next/link";
import {
  Upload,
  X,
  CheckCircle,
  Loader2,
  AlertCircle,
  FileSpreadsheet,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { PageHeader } from "@/components/ui/PageHeader";
import { SectionCard } from "@/components/ui/SectionCard";
import { StatusBadge, type BadgeVariant } from "@/components/ui/StatusBadge";
import { Button } from "@/components/ui/Button";
import { EmptyState } from "@/components/ui/EmptyState";
import type { AnalysisResponse, Investigation } from "@/lib/api";
import { listInvestigations } from "@/lib/api";

type UploadedFile = {
  file: File;
  id: string;
  status: "pending" | "uploading" | "complete" | "error";
  progress: number;
  error?: string;
  investigationId?: string;
};

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function getRiskBadgeVariant(level: string): BadgeVariant {
  switch (level) {
    case "High":
      return "error";
    case "Medium":
      return "warning";
    case "Low":
      return "success";
    default:
      return "default";
  }
}

export default function UploadPage() {
  const [files, setFiles] = useState<UploadedFile[]>([]);
  const [isDragging, setIsDragging] = useState(false);
  const [results, setResults] = useState<AnalysisResponse | null>(null);
  const [recentInvestigations, setRecentInvestigations] = useState<Investigation[]>([]);

  useEffect(() => {
    listInvestigations()
      .then((inv) => setRecentInvestigations(inv.slice(0, 5)))
      .catch(() => {});
  }, []);

  const addFiles = useCallback((newFiles: FileList | File[]) => {
    const fileArray = Array.from(newFiles);
    const uploaded: UploadedFile[] = fileArray.map((file) => ({
      file,
      id: `${Date.now()}-${Math.random().toString(36).slice(2, 9)}`,
      status: "pending" as const,
      progress: 0,
    }));
    setFiles((prev) => [...prev, ...uploaded]);
    setResults(null);
  }, []);

  const handleDragOver = (e: DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e: DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files.length > 0) {
      addFiles(e.dataTransfer.files);
    }
  };

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      addFiles(e.target.files);
    }
  };

  const removeFile = (id: string) => {
    setFiles((prev) => prev.filter((f) => f.id !== id));
  };

  const uploadAndAnalyze = async () => {
    setResults(null);
    const pendingFiles = files.filter((f) => f.status === "pending");
    if (pendingFiles.length === 0) return;

    setFiles((prev) =>
      prev.map((f) =>
        f.status === "pending" ? { ...f, status: "uploading" as const } : f,
      ),
    );

    for (const item of pendingFiles) {
      try {
        if (!item.file.name.toLowerCase().endsWith(".csv")) {
          throw new Error("Only CSV files are supported");
        }

        const formData = new FormData();
        formData.append("file", item.file);

        const response = await fetch("/api/ml/analyze", {
          method: "POST",
          body: formData,
        });

        const data: AnalysisResponse = await response.json();

        if (!response.ok || !data.success) {
          throw new Error(data.error || `Analysis failed (${response.status})`);
        }

        setResults(data);
        setFiles((prev) =>
          prev.map((f) =>
            f.id === item.id
              ? { ...f, status: "complete" as const, progress: 100, investigationId: data.investigation_id }
              : f,
          ),
        );
        // Refresh recent investigations
        listInvestigations()
          .then((inv) => setRecentInvestigations(inv.slice(0, 5)))
          .catch(() => {});
      } catch (err) {
        const message =
          err instanceof Error ? err.message : "Upload failed";
        setFiles((prev) =>
          prev.map((f) =>
            f.id === item.id
              ? { ...f, status: "error" as const, error: message }
              : f,
          ),
        );
      }
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Upload Claims"
        description="Upload a healthcare claims CSV to analyze potential fraud."
      />

      {/* Drop zone */}
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        className={cn(
          "rounded-xl border-2 border-dashed p-10 text-center transition-colors",
          isDragging
            ? "border-primary bg-primary-light"
            : "border-border bg-surface hover:border-border-light",
        )}
      >
        <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-surface-secondary">
          <Upload className="h-5 w-5 text-text-muted" />
        </div>
        <p className="mt-3 text-sm font-medium text-text-primary">
          Drag & drop a CSV file here
        </p>
        <p className="mt-1 text-xs text-text-muted">
          or click to browse
        </p>
        <label className="mt-4 inline-flex cursor-pointer items-center justify-center rounded-md border border-border bg-surface px-5 py-2 text-sm font-medium text-text-primary transition-colors hover:bg-surface-secondary">
          Browse Files
          <input
            type="file"
            accept=".csv"
            onChange={handleFileInput}
            className="hidden"
          />
        </label>
      </div>

      {/* File list */}
      {files.length > 0 && (
        <SectionCard
          title="Files"
          headerRight={
            <Button
              size="sm"
              onClick={uploadAndAnalyze}
              disabled={files.every((f) => f.status !== "pending")}
            >
              <Upload className="h-3.5 w-3.5" />
              Analyze Claims
            </Button>
          }
          noPadding
        >
          <div className="divide-y divide-border">
            {files.map((item) => (
              <div key={item.id} className="flex items-center gap-3 px-6 py-3">
                <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-surface-secondary">
                  <FileSpreadsheet className="h-4 w-4 text-text-muted" />
                </div>
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm font-medium text-text-primary">
                    {item.file.name}
                  </p>
                  <p className="text-xs text-text-muted">
                    {formatFileSize(item.file.size)}
                  </p>
                  {item.status === "uploading" && (
                    <div className="mt-1.5 h-1 overflow-hidden rounded-full bg-surface-secondary">
                      <div
                        className="h-full rounded-full bg-primary transition-all duration-300"
                        style={{ width: `${item.progress}%` }}
                      />
                    </div>
                  )}
                  {item.error && (
                    <p className="mt-1 text-xs text-error">{item.error}</p>
                  )}
                  {item.status === "complete" && item.investigationId && (
                    <Link
                      href={`/investigations/${item.investigationId}`}
                      className="mt-1 inline-block text-xs text-primary hover:underline"
                    >
                      View Investigation {item.investigationId}
                    </Link>
                  )}
                </div>
                <div className="shrink-0">
                  {item.status === "pending" && (
                    <button
                      onClick={() => removeFile(item.id)}
                      className="rounded p-1 text-text-muted hover:bg-surface-secondary hover:text-text-primary"
                    >
                      <X className="h-4 w-4" />
                    </button>
                  )}
                  {item.status === "uploading" && (
                    <Loader2 className="h-4 w-4 animate-spin text-primary" />
                  )}
                  {item.status === "complete" && (
                    <CheckCircle className="h-4 w-4 text-success" />
                  )}
                  {item.status === "error" && (
                    <AlertCircle className="h-4 w-4 text-error" />
                  )}
                </div>
              </div>
            ))}
          </div>
        </SectionCard>
      )}

      {/* Empty file list */}
      {files.length === 0 && (
        <SectionCard>
          <EmptyState
            title="No file selected"
            description="Choose a CSV file containing healthcare claim data to begin analysis."
          />
        </SectionCard>
      )}

      {/* Analysis results */}
      {results?.data && (
        <SectionCard
          title="Analysis Results"
          headerRight={
            results.investigation_id ? (
              <Link href={`/investigations/${results.investigation_id}`}>
                <Button variant="secondary" size="sm">
                  View Investigation
                </Button>
              </Link>
            ) : undefined
          }
          description={`${results.data.total_providers} provider(s) analyzed${results.investigation_id ? ` \u2022 ${results.investigation_id}` : ""}`}
        >
          <div className="space-y-4">
            {Object.entries(results.data.summary).length > 0 && (
              <div className="flex flex-wrap gap-2">
                {Object.entries(results.data.summary).map(([level, count]) => (
                  <StatusBadge
                    key={level}
                    label={`${count} ${level}`}
                    variant={getRiskBadgeVariant(level)}
                  />
                ))}
              </div>
            )}

            <div className="divide-y divide-border rounded-lg border border-border">
              {results.data.results.map((r) => (
                <div key={r.provider_id} className="px-4 py-3">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-text-primary">
                        Provider {r.provider_id}
                      </p>
                      <p className="text-xs text-text-muted">
                        {r.prediction} &middot; Confidence{" "}
                        {r.confidence.toFixed(1)}%
                      </p>
                    </div>
                    <div className="flex items-center gap-2">
                      <StatusBadge
                        label={r.risk_level}
                        variant={getRiskBadgeVariant(r.risk_level)}
                      />
                      <StatusBadge
                        label={r.investigation_priority}
                        variant="default"
                      />
                    </div>
                  </div>
                  {r.review_reason && (
                    <p className="mt-1 text-xs text-text-secondary">
                      {r.review_reason}
                    </p>
                  )}
                </div>
              ))}
            </div>
          </div>
        </SectionCard>
      )}

      {/* Recent investigations */}
      {recentInvestigations.length > 0 && (
        <SectionCard
          title="Recent Investigations"
          headerRight={
            <Link href="/investigations">
              <Button variant="secondary" size="sm">
                View All
              </Button>
            </Link>
          }
        >
          <div className="divide-y divide-border rounded-lg border border-border">
            {recentInvestigations.map((inv) => (
              <Link
                key={inv.investigation_id}
                href={`/investigations/${inv.investigation_id}`}
                className="flex items-center justify-between px-4 py-3 transition-colors hover:bg-surface-secondary"
              >
                <div>
                  <p className="text-sm font-medium text-primary">
                    {inv.investigation_id}
                  </p>
                  <p className="text-xs text-text-muted">
                    {inv.uploaded_filename || "Unknown file"} &middot;{" "}
                    {inv.provider_count} providers
                  </p>
                </div>
                <StatusBadge
                  label={inv.status}
                  variant={inv.status === "completed" ? "success" : "default"}
                  dot
                />
              </Link>
            ))}
          </div>
        </SectionCard>
      )}
    </div>
  );
}
