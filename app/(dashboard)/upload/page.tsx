"use client";

import { useState, useCallback, type DragEvent } from "react";
import {
  Upload,
  FileText,
  X,
  CheckCircle,
  Loader2,
  File,
  FileSpreadsheet,
} from "lucide-react";
import { cn } from "@/lib/utils";

type UploadedFile = {
  file: File;
  id: string;
  status: "pending" | "uploading" | "complete" | "error";
  progress: number;
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

export default function UploadPage() {
  const [files, setFiles] = useState<UploadedFile[]>([]);
  const [isDragging, setIsDragging] = useState(false);

  const addFiles = useCallback((newFiles: FileList | File[]) => {
    const fileArray = Array.from(newFiles);
    const uploaded: UploadedFile[] = fileArray.map((file) => ({
      file,
      id: `${Date.now()}-${Math.random().toString(36).slice(2, 9)}`,
      status: "pending" as const,
      progress: 0,
    }));
    setFiles((prev) => [...prev, ...uploaded]);
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

  const simulateUpload = () => {
    setFiles((prev) =>
      prev.map((f) =>
        f.status === "pending" ? { ...f, status: "uploading" as const } : f,
      ),
    );

    files.forEach((f, index) => {
      if (f.status === "pending") {
        let progress = 0;
        const interval = setInterval(() => {
          progress += Math.random() * 30;
          if (progress >= 100) {
            progress = 100;
            clearInterval(interval);
            setFiles((prev) =>
              prev.map((pf) =>
                pf.id === f.id
                  ? { ...pf, status: "complete" as const, progress: 100 }
                  : pf,
              ),
            );
          } else {
            setFiles((prev) =>
              prev.map((pf) =>
                pf.id === f.id ? { ...pf, progress } : pf,
              ),
            );
          }
        }, 300 + index * 200);
      }
    });
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
          Supports CSV, Excel (XLSX/XLS), and PDF files
        </p>
        <label className="mt-4 inline-flex cursor-pointer items-center justify-center rounded-md border border-border bg-surface px-6 py-2.5 text-sm font-semibold text-text-primary shadow-sm transition-colors hover:bg-surface-secondary">
          Browse Files
          <input
            type="file"
            multiple
            accept=".csv,.xlsx,.xls,.pdf"
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
              onClick={simulateUpload}
              disabled={files.every((f) => f.status !== "pending")}
              className="inline-flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground shadow-sm transition-colors hover:bg-primary-dark disabled:opacity-50"
            >
              <Upload className="h-4 w-4" />
              Upload All
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
    </div>
  );
}
