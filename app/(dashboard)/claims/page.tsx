"use client";

import { useState } from "react";
import Link from "next/link";
import {
  Search,
  Filter,
  ChevronDown,
  ChevronUp,
  Eye,
  ArrowUpDown,
  Upload,
  FileText,
} from "lucide-react";
import { formatCurrency, getStatusColor, getRiskColor } from "@/lib/utils";

type SortField = "date" | "amount" | "risk";
type SortDir = "asc" | "desc";

const allClaims = [
  { id: "CLM-2024-0847", patient: "PAT-4521", patientName: "Maria Garcia", provider: "Metro General Hospital", amount: 12450, status: "investigating", risk: 82, date: "2024-07-08" },
  { id: "CLM-2024-0846", patient: "PAT-3891", patientName: "John Smith", provider: "HealthFirst Clinic", amount: 3200, status: "completed", risk: 15, date: "2024-07-07" },
  { id: "CLM-2024-0845", patient: "PAT-5201", patientName: "Sarah Johnson", provider: "Valley Medical Center", amount: 28900, status: "processing", risk: 67, date: "2024-07-07" },
  { id: "CLM-2024-0844", patient: "PAT-1923", patientName: "Robert Williams", provider: "Community Health Partners", amount: 8750, status: "completed", risk: 23, date: "2024-07-06" },
  { id: "CLM-2024-0843", patient: "PAT-6744", patientName: "Emily Brown", provider: "Premier Healthcare Group", amount: 45200, status: "investigating", risk: 91, date: "2024-07-06" },
  { id: "CLM-2024-0842", patient: "PAT-2108", patientName: "Michael Davis", provider: "City Health Services", amount: 5600, status: "completed", risk: 8, date: "2024-07-05" },
  { id: "CLM-2024-0841", patient: "PAT-4590", patientName: "Jessica Wilson", provider: "Metro General Hospital", amount: 19800, status: "investigating", risk: 74, date: "2024-07-05" },
  { id: "CLM-2024-0840", patient: "PAT-3312", patientName: "David Martinez", provider: "HealthFirst Clinic", amount: 2100, status: "completed", risk: 5, date: "2024-07-04" },
  { id: "CLM-2024-0839", patient: "PAT-5567", patientName: "Lisa Anderson", provider: "Valley Medical Center", amount: 34500, status: "processing", risk: 88, date: "2024-07-04" },
  { id: "CLM-2024-0838", patient: "PAT-1456", patientName: "James Taylor", provider: "Premier Healthcare Group", amount: 7800, status: "uploaded", risk: 42, date: "2024-07-03" },
];

export default function ClaimsPage() {
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [riskFilter, setRiskFilter] = useState("all");
  const [sortField, setSortField] = useState<SortField>("date");
  const [sortDir, setSortDir] = useState<SortDir>("desc");
  const [showFilters, setShowFilters] = useState(false);

  const filteredClaims = allClaims
    .filter((claim) => {
      const matchSearch =
        claim.id.toLowerCase().includes(search.toLowerCase()) ||
        claim.patient.toLowerCase().includes(search.toLowerCase()) ||
        claim.patientName.toLowerCase().includes(search.toLowerCase()) ||
        claim.provider.toLowerCase().includes(search.toLowerCase());
      const matchStatus =
        statusFilter === "all" || claim.status === statusFilter;
      const matchRisk =
        riskFilter === "all" ||
        (riskFilter === "low" && claim.risk <= 30) ||
        (riskFilter === "medium" && claim.risk > 30 && claim.risk <= 70) ||
        (riskFilter === "high" && claim.risk > 70);
      return matchSearch && matchStatus && matchRisk;
    })
    .sort((a, b) => {
      const dir = sortDir === "asc" ? 1 : -1;
      if (sortField === "amount") return (a.amount - b.amount) * dir;
      if (sortField === "risk") return (a.risk - b.risk) * dir;
      return (new Date(a.date).getTime() - new Date(b.date).getTime()) * dir;
    });

  const toggleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDir(sortDir === "asc" ? "desc" : "asc");
    } else {
      setSortField(field);
      setSortDir("desc");
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-text-primary">Claims</h1>
          <p className="mt-1 text-sm text-text-secondary">
            Manage and review all uploaded healthcare claims
          </p>
        </div>
        <Link
          href="/upload"
          className="inline-flex items-center gap-2 rounded-md bg-primary px-4 py-2.5 text-sm font-semibold text-primary-foreground shadow-sm transition-colors hover:bg-primary-dark"
        >
          <Upload className="h-4 w-4" />
          Upload Claim
        </Link>
      </div>

      <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-text-muted" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search by Claim ID, Patient, or Provider..."
            className="h-10 w-full rounded-md border border-border bg-surface pl-9 pr-4 text-sm text-text-primary placeholder:text-text-muted focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
          />
        </div>
        <button
          onClick={() => setShowFilters(!showFilters)}
          className="inline-flex items-center gap-2 rounded-md border border-border bg-surface px-4 py-2 text-sm font-medium text-text-secondary transition-colors hover:bg-surface-secondary"
        >
          <Filter className="h-4 w-4" />
          Filters
          {showFilters ? (
            <ChevronUp className="h-3 w-3" />
          ) : (
            <ChevronDown className="h-3 w-3" />
          )}
        </button>
      </div>

      {showFilters && (
        <div className="flex flex-wrap gap-3 rounded-xl border border-border bg-surface p-4 shadow-sm">
          <div>
            <label className="mb-1 block text-xs font-medium text-text-muted">
              Status
            </label>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="h-9 rounded-md border border-border bg-surface px-3 text-sm text-text-primary focus:border-primary focus:outline-none"
            >
              <option value="all">All Statuses</option>
              <option value="uploaded">Uploaded</option>
              <option value="processing">Processing</option>
              <option value="investigating">Investigating</option>
              <option value="completed">Completed</option>
            </select>
          </div>
          <div>
            <label className="mb-1 block text-xs font-medium text-text-muted">
              Risk Level
            </label>
            <select
              value={riskFilter}
              onChange={(e) => setRiskFilter(e.target.value)}
              className="h-9 rounded-md border border-border bg-surface px-3 text-sm text-text-primary focus:border-primary focus:outline-none"
            >
              <option value="all">All Risk Levels</option>
              <option value="low">Low Risk (0-30)</option>
              <option value="medium">Medium Risk (31-70)</option>
              <option value="high">High Risk (71-100)</option>
            </select>
          </div>
        </div>
      )}

      <div className="rounded-xl border border-border bg-surface shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-border bg-surface-secondary">
                <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-text-muted">
                  Claim ID
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-text-muted">
                  Patient
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-text-muted">
                  Provider
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-text-muted">
                  <button
                    onClick={() => toggleSort("amount")}
                    className="inline-flex items-center gap-1"
                  >
                    Amount
                    <ArrowUpDown className="h-3 w-3" />
                  </button>
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-text-muted">
                  <button
                    onClick={() => toggleSort("date")}
                    className="inline-flex items-center gap-1"
                  >
                    Date
                    <ArrowUpDown className="h-3 w-3" />
                  </button>
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-text-muted">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-text-muted">
                  <button
                    onClick={() => toggleSort("risk")}
                    className="inline-flex items-center gap-1"
                  >
                    Risk
                    <ArrowUpDown className="h-3 w-3" />
                  </button>
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-text-muted">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {filteredClaims.map((claim) => {
                const statusColor = getStatusColor(claim.status);
                const riskColor = getRiskColor(claim.risk);
                return (
                  <tr
                    key={claim.id}
                    className="transition-colors hover:bg-background"
                  >
                    <td className="whitespace-nowrap px-6 py-4 text-sm font-medium text-primary">
                      {claim.id}
                    </td>
                    <td className="whitespace-nowrap px-6 py-4">
                      <div>
                        <p className="text-sm font-medium text-text-primary">
                          {claim.patientName}
                        </p>
                        <p className="text-xs text-text-muted">
                          {claim.patient}
                        </p>
                      </div>
                    </td>
                    <td className="whitespace-nowrap px-6 py-4 text-sm text-text-secondary">
                      {claim.provider}
                    </td>
                    <td className="whitespace-nowrap px-6 py-4 text-sm font-medium text-text-primary">
                      {formatCurrency(claim.amount)}
                    </td>
                    <td className="whitespace-nowrap px-6 py-4 text-sm text-text-secondary">
                      {claim.date}
                    </td>
                    <td className="whitespace-nowrap px-6 py-4">
                      <span
                        className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${statusColor.bg} ${statusColor.text}`}
                      >
                        {claim.status.charAt(0).toUpperCase() +
                          claim.status.slice(1)}
                      </span>
                    </td>
                    <td className="whitespace-nowrap px-6 py-4">
                      <span
                        className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${riskColor.bg} ${riskColor.text}`}
                      >
                        {claim.risk}%
                      </span>
                    </td>
                    <td className="whitespace-nowrap px-6 py-4">
                      <button className="rounded-md p-1.5 text-text-muted transition-colors hover:bg-surface-secondary hover:text-primary">
                        <Eye className="h-4 w-4" />
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
        {filteredClaims.length === 0 && (
          <div className="py-12 text-center">
            <FileText className="mx-auto h-12 w-12 text-text-muted" />
            <h3 className="mt-3 text-base font-semibold text-text-primary">
              No claims found
            </h3>
            <p className="mt-1 text-sm text-text-secondary">
              {search || statusFilter !== "all" || riskFilter !== "all"
                ? "Try adjusting your search or filters"
                : "Upload your first claim to get started"}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}


