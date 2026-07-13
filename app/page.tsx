"use client";

import Image from "next/image";
import Link from "next/link";

const trustBadges = [
  "Explainable AI",
  "Multi-Agent Workflow",
  "Secure & Compliant",
];

const platformStats = [
  { value: "10k+", label: "Claims Analyzed", marker: "CL" },
  { value: "98.6%", label: "Detection Accuracy", marker: "DA" },
  { value: "75%", label: "Investigation Time Saved", marker: "TS" },
  { value: "24/7", label: "AI-Powered Monitoring", marker: "AM" },
];

export default function Home() {
  return (
    <main className="min-h-screen overflow-hidden bg-background text-text-primary">
      <header className="border-b border-border bg-surface">
        <nav className="mx-auto flex h-16 w-full max-w-[1440px] items-center justify-between px-6 lg:px-8">
          <Link href="/" className="flex items-center gap-3" aria-label="FraudShield home">
            <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary text-sm font-bold text-primary-foreground shadow-sm">
              FS
            </span>
            <span>
              <span className="block text-lg font-bold leading-tight text-text-primary">
                FraudShield
              </span>
              <span className="block text-xs font-medium text-text-secondary">
                Healthcare Fraud Detection
              </span>
            </span>
          </Link>

          <div className="flex items-center gap-3">
            <Link
              href="/login"
              className="hidden rounded-md border border-border bg-surface px-5 py-2 text-sm font-semibold text-primary shadow-sm transition-colors hover:bg-surface-secondary sm:inline-flex"
            >
              Log In
            </Link>
            <Link
              href="/signup"
              className="inline-flex rounded-md bg-primary px-5 py-2 text-sm font-semibold text-primary-foreground shadow-sm transition-colors hover:bg-primary-dark"
            >
              Get Started
            </Link>
          </div>
        </nav>
      </header>

      <section className="relative mx-auto grid min-h-[650px] w-full max-w-[1440px] items-center gap-10 px-6 py-16 lg:grid-cols-[0.82fr_1.18fr] lg:px-8 lg:py-0">
        <div className="pointer-events-none absolute left-[40%] top-16 hidden h-[520px] w-[520px] rounded-full bg-primary-light opacity-40 blur-3xl lg:block" />
        <div className="pointer-events-none absolute right-0 top-16 hidden h-[520px] w-[760px] landing-dot-pattern opacity-80 lg:block" />

        <div className="relative z-10 max-w-[560px]">
          <h1 className="text-[40px] font-bold leading-[1.08] text-text-primary sm:text-5xl lg:text-[52px]">
            AI-Powered Healthcare{" "}
            <span className="text-primary">Fraud Detection</span> Built for
            Investigators
          </h1>
          <p className="mt-6 max-w-[520px] text-lg leading-8 text-text-secondary">
            Detect suspicious patterns, automate investigations, and uncover
            healthcare fraud with explainable AI and intelligent multi-agent
            workflows.
          </p>

          <div className="mt-8 flex flex-wrap items-center gap-4">
            <Link
              href="/login"
              className="inline-flex items-center justify-center rounded-md bg-primary px-8 py-4 text-sm font-semibold text-primary-foreground shadow-md transition-colors hover:bg-primary-dark"
            >
              Start Investigating
              <span className="ml-2" aria-hidden="true">
                -&gt;
              </span>
            </Link>
          </div>

          <div className="mt-8 flex flex-wrap items-center gap-6">
            {trustBadges.map((badge) => (
              <div key={badge} className="flex items-center gap-2 text-sm font-medium text-text-secondary">
                <span className="flex h-6 w-6 items-center justify-center rounded-full bg-primary-light text-[10px] font-bold text-primary">
                  AI
                </span>
                {badge}
              </div>
            ))}
          </div>
        </div>

        <div className="relative z-10 lg:-mr-40">
          <div className="h-[460px] overflow-hidden rounded-xl border border-border bg-surface p-2 shadow-lg sm:h-[540px] lg:h-[590px]">
            <Image
              src="/images/dashboard.png"
              alt="FraudShield dashboard showing claim metrics, risk distribution, and recent activity"
              width={1280}
              height={832}
              priority
              className="h-full w-full rounded-lg object-cover object-top"
            />
          </div>
        </div>
      </section>

      <section className="border-t border-border bg-surface">
        <div className="mx-auto w-full max-w-[1440px] px-6 py-8 lg:px-8">
          <p className="text-center text-base font-medium text-text-secondary">
            Trusted by healthcare organizations and insurance providers
          </p>
          <div className="mt-6 grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
            {platformStats.map((stat) => (
              <div key={stat.label} className="flex items-center justify-center gap-4">
                <span className="flex h-12 w-12 items-center justify-center rounded-xl bg-primary-light text-xs font-bold text-primary shadow-sm">
                  {stat.marker}
                </span>
                <span>
                  <span className="block text-3xl font-bold leading-tight text-primary">
                    {stat.value}
                  </span>
                  <span className="block text-sm font-medium text-text-secondary">
                    {stat.label}
                  </span>
                </span>
              </div>
            ))}
          </div>
        </div>
      </section>
    </main>
  );
}
