"use client";

import { useState } from "react";
import {
  Brain,
  Loader2,
  CheckCircle,
  AlertTriangle,
  FileText,
  Shield,
  TrendingUp,
} from "lucide-react";
import { cn } from "@/lib/utils";

type AnalysisStep = {
  id: string;
  label: string;
  status: "pending" | "running" | "complete" | "error";
};

const defaultSteps: AnalysisStep[] = [
  { id: "upload", label: "Upload Claim", status: "pending" },
  { id: "extract", label: "Extract Data", status: "pending" },
  { id: "predict", label: "Fraud Prediction", status: "pending" },
  { id: "explain", label: "AI Explanation", status: "pending" },
  { id: "report", label: "Generate Report", status: "pending" },
];

const mockResult = {
  fraudProbability: 78,
  riskScore: 78,
  prediction: "Suspicious",
  confidence: 0.92,
  classification: "Medium-High Risk",
  reasoning: [
    "Unusual billing pattern detected for this provider",
    "Claim amount significantly exceeds regional average",
    "Patient has multiple recent claims with different providers",
    "Diagnosis codes are inconsistent with procedure codes",
  ],
  evidence: [
    "3 similar fraudulent claims found in historical data",
    "Provider flagged in 2 prior investigations",
    "Billing frequency exceeds expected pattern by 340%",
  ],
};

export default function AnalyzePage() {
  const [steps, setSteps] = useState<AnalysisStep[]>(defaultSteps);
  const [analyzing, setAnalyzing] = useState(false);
  const [complete, setComplete] = useState(false);

  const startAnalysis = () => {
    setAnalyzing(true);
    setComplete(false);

    let currentStep = 0;
    const runStep = () => {
      if (currentStep >= steps.length) {
        setAnalyzing(false);
        setComplete(true);
        return;
      }

      setSteps((prev) =>
        prev.map((s, i) =>
          i === currentStep
            ? { ...s, status: "running" }
            : i < currentStep
              ? { ...s, status: "complete" }
              : s,
        ),
      );

      setTimeout(() => {
        setSteps((prev) =>
          prev.map((s, i) =>
            i === currentStep ? { ...s, status: "complete" } : s,
          ),
        );
        currentStep++;
        runStep();
      }, 800 + Math.random() * 400);
    };

    setSteps(defaultSteps);
    runStep();
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-text-primary">
          Analyze Claims
        </h1>
        <p className="mt-1 text-sm text-text-secondary">
          Run fraud detection analysis on uploaded claims
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-[380px_1fr]">
        <div className="space-y-6">
          <div className="rounded-xl border border-border bg-surface p-6 shadow-sm">
            <h2 className="text-base font-semibold text-text-primary">
              Analysis Workflow
            </h2>
            <div className="mt-4 space-y-3">
              {steps.map((step, i) => (
                <div key={step.id} className="flex items-center gap-3">
                  <div
                    className={cn(
                      "flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-xs font-bold",
                      step.status === "complete"
                        ? "bg-success text-primary-foreground"
                        : step.status === "running"
                          ? "bg-primary text-primary-foreground"
                          : step.status === "error"
                            ? "bg-error text-primary-foreground"
                            : "bg-surface-secondary text-text-muted",
                    )}
                  >
                    {step.status === "complete" ? (
                      <CheckCircle className="h-4 w-4" />
                    ) : step.status === "running" ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      i + 1
                    )}
                  </div>
                  <span
                    className={cn(
                      "text-sm font-medium",
                      step.status === "complete"
                        ? "text-success"
                        : step.status === "running"
                          ? "text-primary"
                          : "text-text-secondary",
                    )}
                  >
                    {step.label}
                  </span>
                </div>
              ))}
            </div>

            <button
              onClick={startAnalysis}
              disabled={analyzing}
              className="mt-6 flex w-full items-center justify-center gap-2 rounded-md bg-primary px-4 py-2.5 text-sm font-semibold text-primary-foreground shadow-sm transition-colors hover:bg-primary-dark disabled:opacity-50"
            >
              {analyzing ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Analyzing...
                </>
              ) : (
                <>
                  <Brain className="h-4 w-4" />
                  Start Analysis
                </>
              )}
            </button>
          </div>
        </div>

        {complete && (
          <div className="space-y-6">
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              <div className="rounded-xl border border-border bg-surface p-5 shadow-sm">
                <div className="flex items-center gap-2 text-text-muted">
                  <TrendingUp className="h-4 w-4" />
                  <span className="text-xs font-medium uppercase tracking-wider">
                    Fraud Probability
                  </span>
                </div>
                <p className="mt-2 text-3xl font-bold text-error">
                  {mockResult.fraudProbability}%
                </p>
              </div>
              <div className="rounded-xl border border-border bg-surface p-5 shadow-sm">
                <div className="flex items-center gap-2 text-text-muted">
                  <Shield className="h-4 w-4" />
                  <span className="text-xs font-medium uppercase tracking-wider">
                    Risk Score
                  </span>
                </div>
                <p className="mt-2 text-3xl font-bold text-warning">
                  {mockResult.riskScore}
                </p>
              </div>
              <div className="rounded-xl border border-border bg-surface p-5 shadow-sm">
                <div className="flex items-center gap-2 text-text-muted">
                  <AlertTriangle className="h-4 w-4" />
                  <span className="text-xs font-medium uppercase tracking-wider">
                    Prediction
                  </span>
                </div>
                <p className="mt-2 text-lg font-bold text-warning">
                  {mockResult.prediction}
                </p>
              </div>
              <div className="rounded-xl border border-border bg-surface p-5 shadow-sm">
                <div className="flex items-center gap-2 text-text-muted">
                  <CheckCircle className="h-4 w-4" />
                  <span className="text-xs font-medium uppercase tracking-wider">
                    Confidence
                  </span>
                </div>
                <p className="mt-2 text-3xl font-bold text-success">
                  {(mockResult.confidence * 100).toFixed(0)}%
                </p>
              </div>
            </div>

            <div className="rounded-xl border border-border bg-surface p-6 shadow-sm">
              <h3 className="text-base font-semibold text-text-primary">
                AI Explainability
              </h3>
              <div className="mt-4 space-y-3">
                {mockResult.reasoning.map((reason, i) => (
                  <div key={i} className="flex items-start gap-3">
                    <span className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-warning-light text-[10px] font-bold text-warning-foreground">
                      {i + 1}
                    </span>
                    <p className="text-sm text-text-secondary">{reason}</p>
                  </div>
                ))}
              </div>
            </div>

            <div className="rounded-xl border border-border bg-surface p-6 shadow-sm">
              <h3 className="text-base font-semibold text-text-primary">
                Supporting Evidence
              </h3>
              <div className="mt-4 space-y-3">
                {mockResult.evidence.map((ev, i) => (
                  <div key={i} className="flex items-start gap-3">
                    <FileText className="mt-0.5 h-4 w-4 shrink-0 text-info" />
                    <p className="text-sm text-text-secondary">{ev}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {!complete && (
          <div className="flex items-center justify-center rounded-xl border border-dashed border-border bg-surface p-12">
            <div className="text-center">
              <Brain className="mx-auto h-12 w-12 text-text-muted" />
              <h3 className="mt-3 text-base font-semibold text-text-primary">
                Ready to Analyze
              </h3>
              <p className="mt-1 text-sm text-text-secondary">
                Upload claims and start the analysis workflow to see results
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
