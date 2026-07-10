"use client";

import { useState, useCallback, type DragEvent } from "react";
import {
  Upload,
  FileText,
  X,
  CheckCircle,
  Loader2,
  AlertCircle,
  File,
  FileSpreadsheet,
} from "lucide-react";
import { cn } from "@/lib/utils";

type UploadedFile = {
  file: File;
  id: string;
  status: "pending" | "uploading" | "complete" | "error";
  progress: number;
  error?: string;
};

type AnalysisResult = {
  provider_id: string;
  prediction: string;
  fraud_probability: number;
  confidence: number;
  risk_level: string;
  investigation_priority: string;
  requires_manual_review: boolean;
  review_reason: string;
  investigation_score: number;
};

type AnalysisResponse = {
  success: boolean;
  data?: {
    results: AnalysisResult[];
    total_providers: number;
    summary: Record<string, number>;
  };
  error?: string;
};

function getFileIcon(fileName: string) {
  const ext = fileName.split(".").pop()?.toLowerCase();
  if (ext === "pdf") return FileText;
  if (ext === "csv") return FileSpreadsheet;
  if (ext === "xlsx" || ext === "xls") return FileSpreadsheet;
  return File;
}

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function getRiskBadgeColor(level: string) {
  switch (level) {
    case "High":
      return "bg-error-light text-error";
    case "Medium":
      return "bg-warning-light text-warning";
    case "Low":
      return "bg-success-light text-success";
    default:
      return "bg-surface-secondary text-text-muted";
  }
}

export default function UploadPage() {
  const [files, setFiles] = useState<UploadedFile[]>([]);
  const [isDragging, setIsDragging] = useState(false);
  const [results, setResults] = useState<AnalysisResponse | null>(null);

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

    // Mark all pending files as uploading.
    setFiles((prev) =>
      prev.map((f) =>
        f.status === "pending" ? { ...f, status: "uploading" as const } : f,
      ),
    );

    // Upload and analyse each CSV file sequentially.
    for (const item of pendingFiles) {
      try {
        // Validate file type on the client side.
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
              ? { ...f, status: "complete" as const, progress: 100 }
              : f,
          ),
        );
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
      <div>
        <h1 className="text-2xl font-bold text-text-primary">Upload Claim</h1>
        <p className="mt-1 text-sm text-text-secondary">
          Upload healthcare claim documents for fraud analysis
        </p>
      </div>

      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        className={cn(
          "rounded-xl border-2 border-dashed p-12 text-center transition-colors",
          isDragging
            ? "border-primary bg-primary-light"
            : "border-border bg-surface hover:border-border-light",
        )}
      >
        <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-surface-secondary">
          <Upload className="h-7 w-7 text-text-muted" />
        </div>
        <h3 className="mt-4 text-base font-semibold text-text-primary">
          Drag & drop files here
        </h3>
        <p className="mt-1 text-sm text-text-secondary">
          or click to browse your files
        </p>
        <p className="mt-2 text-xs text-text-muted">
          Supports CSV files with claim data
        </p>
        <label className="mt-4 inline-flex cursor-pointer items-center justify-center rounded-md border border-border bg-surface px-6 py-2.5 text-sm font-semibold text-text-primary shadow-sm transition-colors hover:bg-surface-secondary">
          Browse Files
          <input
            type="file"
            multiple
            accept=".csv"
            onChange={handleFileInput}
            className="hidden"
          />
        </label>
      </div>

      {files.length > 0 && (
        <div className="rounded-xl border border-border bg-surface shadow-sm">
          <div className="flex items-center justify-between border-b border-border px-6 py-4">
            <h2 className="text-base font-semibold text-text-primary">
              Uploaded Files ({files.length})
            </h2>
            <button
              onClick={uploadAndAnalyze}
              disabled={files.every((f) => f.status !== "pending")}
              className="inline-flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground shadow-sm transition-colors hover:bg-primary-dark disabled:opacity-50"
            >
              <Upload className="h-4 w-4" />
              Upload & Analyse
            </button>
          </div>
          <div className="divide-y divide-border">
            {files.map((item) => {
              const Icon = getFileIcon(item.file.name);
              return (
                <div key={item.id} className="flex items-center gap-4 px-6 py-4">
                  <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-surface-secondary">
                    <Icon className="h-5 w-5 text-text-muted" />
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-sm font-medium text-text-primary">
                      {item.file.name}
                    </p>
                    <p className="text-xs text-text-muted">
                      {formatFileSize(item.file.size)}
                    </p>
                    {item.status === "uploading" && (
                      <div className="mt-1.5 h-1.5 overflow-hidden rounded-full bg-surface-secondary">
                        <div
                          className="h-full rounded-full bg-primary transition-all duration-300"
                          style={{ width: `${item.progress}%` }}
                        />
                      </div>
                    )}
                    {item.error && (
                      <p className="mt-1 text-xs text-error">{item.error}</p>
                    )}
                  </div>
                  <div className="shrink-0">
                    {item.status === "pending" && (
                      <button
                        onClick={() => removeFile(item.id)}
                        className="rounded-md p-1.5 text-text-muted hover:bg-surface-secondary hover:text-text-primary"
                      >
                        <X className="h-4 w-4" />
                      </button>
                    )}
                    {item.status === "uploading" && (
                      <Loader2 className="h-5 w-5 animate-spin text-primary" />
                    )}
                    {item.status === "complete" && (
                      <CheckCircle className="h-5 w-5 text-success" />
                    )}
                    {item.status === "error" && (
                      <AlertCircle className="h-5 w-5 text-error" />
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {files.length === 0 && (
        <div className="rounded-xl border border-border bg-surface p-8 shadow-sm">
          <div className="text-center">
            <FileText className="mx-auto h-12 w-12 text-text-muted" />
            <h3 className="mt-3 text-base font-semibold text-text-primary">
              No files uploaded yet
            </h3>
            <p className="mt-1 text-sm text-text-secondary">
              Upload healthcare claim documents to begin fraud analysis
            </p>
          </div>
        </div>
      )}

      {/* Analysis Results */}
      {results?.data && (
        <div className="rounded-xl border border-border bg-surface shadow-sm">
          <div className="border-b border-border px-6 py-4">
            <h2 className="text-base font-semibold text-text-primary">
              Analysis Results
            </h2>
            <p className="mt-0.5 text-xs text-text-muted">
              {results.data.total_providers} provider(s) analysed
            </p>
          </div>

          {/* Summary */}
          <div className="grid grid-cols-3 gap-4 border-b border-border px-6 py-4">
            {Object.entries(results.data.summary).map(([level, count]) => (
              <div key={level} className="text-center">
                <span
                  className={cn(
                    "inline-block rounded-full px-3 py-1 text-xs font-semibold",
                    getRiskBadgeColor(level),
                  )}
                >
                  {count} {level}
                </span>
              </div>
            ))}
          </div>

          {/* Per-provider results */}
          <div className="divide-y divide-border">
            {results.data.results.map((r) => (
              <div key={r.provider_id} className="px-6 py-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-semibold text-text-primary">
                      Provider {r.provider_id}
                    </p>
                    <p className="text-xs text-text-muted">
                      Prediction: {r.prediction} &middot; Confidence:{" "}
                      {r.confidence.toFixed(1)}%
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <span
                      className={cn(
                        "rounded-full px-2.5 py-0.5 text-xs font-semibold",
                        getRiskBadgeColor(r.risk_level),
                      )}
                    >
                      {r.risk_level}
                    </span>
                    <span className="rounded-full bg-surface-secondary px-2.5 py-0.5 text-xs font-semibold text-text-secondary">
                      {r.investigation_priority}
                    </span>
                  </div>
                </div>
                <p className="mt-1 text-xs text-text-secondary">
                  {r.review_reason}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
