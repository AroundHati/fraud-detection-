"use client";

import { useState, useRef, useEffect } from "react";
import {
  Bot,
  Send,
  User,
  Sparkles,
  MessageSquare,
  ChevronRight,
} from "lucide-react";
import { cn } from "@/lib/utils";
import type {
  InvestigationDetail,
  InvestigationChatMessage,
} from "@/types";

const SUGGESTED_QUESTIONS = [
  "Why was this provider flagged?",
  "Which fraud indicators contributed most?",
  "What should an investigator review first?",
  "Is this likely billing abuse or provider abuse?",
  "Summarize this investigation.",
];

type Props = {
  detail: InvestigationDetail;
};

function createMessageId(): string {
  return `msg-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
}

function formatAnswer(content: string): string {
  return content;
}

export function AIInvestigationAssistant({ detail }: Props) {
  const [messages, setMessages] = useState<InvestigationChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSubmit = async (question: string) => {
    if (!question.trim() || isLoading) return;

    const userMessage: InvestigationChatMessage = {
      id: createMessageId(),
      role: "user",
      content: question.trim(),
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsLoading(true);

    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_ML_API_URL ?? "http://localhost:8000"}/api/ml/investigate`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            provider: {
              provider_id: detail.provider.provider_id,
              provider_name: detail.provider.provider_name,
              risk_score: detail.provider.risk_score,
              prediction: detail.provider.prediction,
              confidence: detail.provider.confidence,
              total_claims: detail.provider.total_claims,
              total_reimbursement: detail.provider.total_reimbursement,
              average_claim_amount: detail.provider.average_claim_amount,
              inpatient_claims: detail.provider.inpatient_claims,
              outpatient_claims: detail.provider.outpatient_claims,
              unique_beneficiaries: detail.provider.unique_beneficiaries,
              unique_physicians: detail.provider.unique_physicians,
              fraud_indicators: detail.fraud_indicators.map((ind) => ({
                label: ind.label,
                description: ind.description,
                severity: ind.severity,
                status: ind.status,
              })),
              recommendation: detail.recommendation,
            },
            question: question.trim(),
          }),
        },
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail ?? "Failed to get response");
      }

      const assistantMessage: InvestigationChatMessage = {
        id: createMessageId(),
        role: "assistant",
        content: data.data.answer,
        sources: data.data.sources,
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error) {
      const errorMessage: InvestigationChatMessage = {
        id: createMessageId(),
        role: "assistant",
        content:
          "I encountered an error processing your question. Please try again or rephrase your question.",
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
      inputRef.current?.focus();
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(input);
    }
  };

  const hasMessages = messages.length > 0;

  return (
    <div className="rounded-xl border border-border bg-surface shadow-sm">
      {/* Header */}
      <div className="flex items-center gap-3 border-b border-border px-6 py-4">
        <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary-light">
          <Bot className="h-5 w-5 text-primary" />
        </div>
        <div>
          <h3 className="text-base font-semibold text-text-primary">
            AI Investigation Assistant
          </h3>
          <p className="text-xs font-medium text-text-muted">
            Ask questions about this provider&apos;s investigation results
          </p>
        </div>
      </div>

      {/* Messages area */}
      <div className="flex h-[400px] flex-col overflow-y-auto">
        {hasMessages ? (
          <div className="flex-1 space-y-4 p-6">
            {messages.map((msg) => (
              <MessageBubble key={msg.id} message={msg} />
            ))}
            {isLoading && (
              <div className="flex items-start gap-3">
                <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-primary-light">
                  <Bot className="h-4 w-4 text-primary" />
                </div>
                <div className="rounded-lg border border-border bg-surface-secondary px-4 py-3">
                  <div className="flex items-center gap-1.5">
                    <div className="h-1.5 w-1.5 animate-pulse rounded-full bg-primary" />
                    <div className="h-1.5 w-1.5 animate-pulse rounded-full bg-primary [animation-delay:150ms]" />
                    <div className="h-1.5 w-1.5 animate-pulse rounded-full bg-primary [animation-delay:300ms]" />
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        ) : (
          <EmptyState onSelectQuestion={handleSubmit} />
        )}
      </div>

      {/* Input area */}
      <div className="border-t border-border px-6 py-4">
        <div className="flex items-center gap-3">
          <input
            ref={inputRef}
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask about this investigation..."
            disabled={isLoading}
            className="h-11 flex-1 rounded-md border border-border bg-surface px-4 text-sm text-text-primary placeholder:text-text-muted focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary disabled:opacity-50"
          />
          <button
            onClick={() => handleSubmit(input)}
            disabled={!input.trim() || isLoading}
            className={cn(
              "flex h-11 w-11 items-center justify-center rounded-md transition-colors",
              input.trim() && !isLoading
                ? "bg-primary text-primary-foreground hover:bg-primary-dark"
                : "bg-surface-secondary text-text-muted",
            )}
          >
            <Send className="h-4 w-4" />
          </button>
        </div>
      </div>
    </div>
  );
}

function MessageBubble({ message }: { message: InvestigationChatMessage }) {
  const isUser = message.role === "user";

  return (
    <div className={cn("flex items-start gap-3", isUser && "flex-row-reverse")}>
      <div
        className={cn(
          "flex h-8 w-8 shrink-0 items-center justify-center rounded-lg",
          isUser ? "bg-surface-secondary" : "bg-primary-light",
        )}
      >
        {isUser ? (
          <User className="h-4 w-4 text-text-secondary" />
        ) : (
          <Bot className="h-4 w-4 text-primary" />
        )}
      </div>

      <div
        className={cn(
          "max-w-[80%] space-y-2",
          isUser ? "text-right" : "text-left",
        )}
      >
        <div
          className={cn(
            "inline-block rounded-lg border border-border px-4 py-3 text-left text-sm leading-relaxed",
            isUser
              ? "bg-surface-secondary text-text-primary"
              : "bg-surface text-text-primary",
          )}
        >
          <div className="whitespace-pre-wrap">{formatAnswer(message.content)}</div>
        </div>

        {message.sources && message.sources.length > 0 && (
          <div className="flex flex-wrap gap-1.5">
            {message.sources.map((source: string) => (
              <span
                key={source}
                className="inline-flex items-center rounded-full bg-primary-light px-2 py-0.5 text-[10px] font-medium text-primary"
              >
                {source}
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function EmptyState({
  onSelectQuestion,
}: {
  onSelectQuestion: (q: string) => void;
}) {
  return (
    <div className="flex flex-1 flex-col items-center justify-center px-6 py-12">
      <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-primary-light">
        <Sparkles className="h-6 w-6 text-primary" />
      </div>

      <h4 className="mb-1 text-base font-semibold text-text-primary">
        Investigation Assistant
      </h4>
      <p className="mb-6 text-center text-sm text-text-secondary">
        Ask questions to understand this provider&apos;s fraud assessment
      </p>

      <div className="w-full max-w-md space-y-2">
        {SUGGESTED_QUESTIONS.map((question) => (
          <button
            key={question}
            onClick={() => onSelectQuestion(question)}
            className="group flex w-full items-center gap-3 rounded-lg border border-border bg-surface p-3 text-left transition-colors hover:border-primary/20 hover:bg-primary-light/30"
          >
            <MessageSquare className="h-4 w-4 shrink-0 text-text-muted transition-colors group-hover:text-primary" />
            <span className="flex-1 text-sm text-text-secondary transition-colors group-hover:text-text-primary">
              {question}
            </span>
            <ChevronRight className="h-4 w-4 shrink-0 text-text-muted opacity-0 transition-all group-hover:translate-x-0.5 group-hover:opacity-100 group-hover:text-primary" />
          </button>
        ))}
      </div>
    </div>
  );
}
