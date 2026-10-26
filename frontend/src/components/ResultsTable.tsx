import React, { useState, useMemo } from "react";
import {
  Search,
  Download,
  Eye,
  Trash2,
  CheckCircle2,
  XCircle,
  HelpCircle,
  Filter,
  AlertTriangle,
  Server,
} from "lucide-react";
import { EmailVerificationRecord, StatusFilter, VerificationStatus } from "../types";
import { exportRecordsToCsv } from "../utils/csv";

interface ResultsTableProps {
  records: EmailVerificationRecord[];
  batchId?: string;
  activeFilter: StatusFilter;
  onFilterChange: (filter: StatusFilter) => void;
  onInspect: (record: EmailVerificationRecord) => void;
  onDeleteRecord: (recordId: string) => void;
}

export const ResultsTable: React.FC<ResultsTableProps> = ({
  records,
  batchId,
  activeFilter,
  onFilterChange,
  onInspect,
  onDeleteRecord,
}) => {
  const [searchTerm, setSearchTerm] = useState<string>("");

  // Filter & Search logic
  const filteredRecords = useMemo(() => {
    return records.filter((r) => {
      const matchesFilter =
        activeFilter === "ALL" || r.status === activeFilter;

      const term = searchTerm.toLowerCase().trim();
      const matchesSearch =
        !term ||
        r.original_email.toLowerCase().includes(term) ||
        (r.normalized_email && r.normalized_email.toLowerCase().includes(term)) ||
        r.reason.toLowerCase().includes(term);

      return matchesFilter && matchesSearch;
    });
  }, [records, activeFilter, searchTerm]);

  const handleExportCsv = () => {
    exportRecordsToCsv(filteredRecords, batchId);
  };

  const getStatusBadge = (status: VerificationStatus) => {
    switch (status) {
      case "Likely to be delivered":
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-50 dark:bg-emerald-950/60 text-emerald-700 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800">
            <CheckCircle2 className="w-3.5 h-3.5" />
            <span>Likely to be delivered</span>
          </span>
        );
      case "Likely to bounce":
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-rose-50 dark:bg-rose-950/60 text-rose-700 dark:text-rose-300 border border-rose-200 dark:border-rose-800">
            <XCircle className="w-3.5 h-3.5" />
            <span>Likely to bounce</span>
          </span>
        );
      case "Unknown":
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-amber-50 dark:bg-amber-950/60 text-amber-700 dark:text-amber-300 border border-amber-200 dark:border-amber-800">
            <HelpCircle className="w-3.5 h-3.5" />
            <span>Unknown</span>
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-amber-50 dark:bg-amber-950/60 text-amber-700 dark:text-amber-300 border border-amber-200 dark:border-amber-800">
            <HelpCircle className="w-3.5 h-3.5" />
            <span>{(status as string) || "Unknown"}</span>
          </span>
        );
    }
  };

  return (
    <div className="bg-white dark:bg-navy-900 border border-slate-200 dark:border-slate-800 rounded-2xl shadow-sm overflow-hidden transition-all">
      {/* Controls Header */}
      <div className="p-4 sm:p-5 border-b border-slate-200 dark:border-slate-800 flex flex-col md:flex-row md:items-center justify-between gap-3">
        {/* Search */}
        <div className="relative flex-1 max-w-md">
          <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search by address or reason..."
            className="w-full pl-9 pr-4 py-2 rounded-xl text-xs sm:text-sm bg-slate-50 dark:bg-navy-950/60 border border-slate-200 dark:border-slate-800 text-slate-900 dark:text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500 transition-all"
          />
        </div>

        {/* Filter Tabs & Export CSV */}
        <div className="flex items-center flex-wrap gap-2">
          {/* Quick Filter buttons */}
          <div className="flex items-center p-1 rounded-xl bg-slate-100 dark:bg-navy-950 border border-slate-200/80 dark:border-slate-800 text-xs">
            {(["ALL", "Likely to be delivered", "Likely to bounce", "Unknown"] as StatusFilter[]).map((f) => (
              <button
                key={f}
                onClick={() => onFilterChange(f)}
                className={`px-2.5 py-1 rounded-lg font-medium transition-all ${
                  activeFilter === f
                    ? "bg-white dark:bg-navy-800 text-brand-700 dark:text-brand-300 shadow-sm"
                    : "text-slate-500 hover:text-slate-900 dark:hover:text-white"
                }`}
              >
                {f === "ALL" ? "All" : f}
              </button>
            ))}
          </div>

          {/* Export CSV button */}
          <button
            onClick={handleExportCsv}
            disabled={filteredRecords.length === 0}
            className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-semibold text-slate-700 dark:text-slate-300 bg-white dark:bg-navy-800 hover:bg-slate-50 dark:hover:bg-slate-800 border border-slate-200 dark:border-slate-700 transition-all disabled:opacity-40"
            title="Export displayed verification records to CSV"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Export CSV</span>
          </button>
        </div>
      </div>

      {/* Results Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs sm:text-sm">
          <thead className="bg-slate-50/80 dark:bg-navy-950/80 text-slate-500 dark:text-slate-400 font-semibold uppercase text-[11px] tracking-wider border-b border-slate-200 dark:border-slate-800">
            <tr>
              <th className="py-3.5 px-4 sm:px-6">Status</th>
              <th className="py-3.5 px-4 sm:px-6">Email Address</th>
              <th className="py-3.5 px-4 sm:px-6">Analysis / Evidence</th>
              <th className="py-3.5 px-4 sm:px-6 hidden md:table-cell">Routing</th>
              <th className="py-3.5 px-4 sm:px-6 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 dark:divide-slate-800/80">
            {filteredRecords.length === 0 ? (
              <tr>
                <td colSpan={5} className="py-12 text-center text-slate-400">
                  <div className="max-w-xs mx-auto space-y-2">
                    <Filter className="w-8 h-8 mx-auto text-slate-300 dark:text-slate-600" />
                    <p className="text-sm font-medium text-slate-600 dark:text-slate-300">
                      No matching records found
                    </p>
                    <p className="text-xs text-slate-400">
                      Try adjusting your search terms or filter selection.
                    </p>
                  </div>
                </td>
              </tr>
            ) : (
              filteredRecords.map((r) => {
                const hasMx = r.dns_diagnostic?.has_mx;
                const hasFallback = r.dns_diagnostic?.has_fallback;

                return (
                  <tr
                    key={r.id}
                    className="hover:bg-slate-50/60 dark:hover:bg-navy-950/40 transition-colors"
                  >
                    {/* Status */}
                    <td className="py-3.5 px-4 sm:px-6 whitespace-nowrap">
                      {getStatusBadge(r.status)}
                    </td>

                    {/* Email */}
                    <td className="py-3.5 px-4 sm:px-6">
                      <div className="flex flex-col">
                        <span className="font-mono font-medium text-slate-900 dark:text-slate-100 break-all">
                          {r.original_email}
                        </span>
                        {r.normalized_email && r.normalized_email !== r.original_email && (
                          <span className="text-[10px] text-slate-400 font-mono mt-0.5">
                            Norm: {r.normalized_email}
                          </span>
                        )}
                        {r.is_duplicate && (
                          <span className="inline-flex items-center gap-1 text-[10px] text-amber-600 dark:text-amber-400 mt-0.5">
                            <AlertTriangle className="w-3 h-3" /> Duplicate entry in batch
                          </span>
                        )}
                      </div>
                    </td>

                    {/* Reason & Stage Tag */}
                    <td className="py-3.5 px-4 sm:px-6 text-slate-600 dark:text-slate-300 max-w-sm">
                      <div className="flex flex-col gap-1">
                        <div className="flex items-center gap-1.5">
                          <span
                            className={`inline-flex items-center text-[10px] font-semibold uppercase tracking-wider px-1.5 py-0.5 rounded border ${
                              r.smtp_skipped
                                ? !r.syntax_diagnostic?.valid
                                  ? "bg-slate-100 dark:bg-navy-800 text-slate-600 dark:text-slate-400 border-slate-200 dark:border-slate-700"
                                  : "bg-blue-50 dark:bg-blue-950/60 text-blue-700 dark:text-blue-300 border-blue-200 dark:border-blue-800"
                                : "bg-purple-50 dark:bg-purple-950/60 text-purple-700 dark:text-purple-300 border-purple-200 dark:border-purple-800"
                            }`}
                          >
                            {r.stage || (r.smtp_skipped ? (!r.syntax_diagnostic?.valid ? "Stage 1: Syntax" : "Stage 2: DNS Routing") : "Stage 3: SMTP Probe")}
                          </span>
                        </div>
                        <p className="line-clamp-2 text-xs leading-relaxed text-slate-700 dark:text-slate-300">
                          {r.reason}
                        </p>
                      </div>
                    </td>

                    {/* Routing Diagnostic Quick Tag */}
                    <td className="py-3.5 px-4 sm:px-6 hidden md:table-cell whitespace-nowrap">
                      {hasMx ? (
                        <span className="inline-flex items-center gap-1 text-[11px] font-mono text-slate-700 dark:text-slate-300 bg-slate-100 dark:bg-navy-800 px-2 py-0.5 rounded">
                          <Server className="w-3 h-3 text-brand-500" />
                          <span>{r.dns_diagnostic?.mx_records?.[0]?.exchange || "MX"}</span>
                        </span>
                      ) : hasFallback ? (
                        <span className="inline-flex items-center gap-1 text-[11px] font-mono text-slate-700 dark:text-slate-300 bg-slate-100 dark:bg-navy-800 px-2 py-0.5 rounded">
                          A/AAAA Fallback
                        </span>
                      ) : (
                        <span className="text-[11px] text-slate-400 font-mono">None</span>
                      )}
                    </td>

                    {/* Actions */}
                    <td className="py-3.5 px-4 sm:px-6 text-right whitespace-nowrap">
                      <div className="inline-flex items-center gap-1.5">
                        <button
                          onClick={() => onInspect(r)}
                          className="inline-flex items-center gap-1 px-2.5 py-1.5 rounded-lg text-xs font-semibold text-brand-600 dark:text-brand-400 bg-brand-50 hover:bg-brand-100 dark:bg-brand-950/60 dark:hover:bg-brand-900/60 transition-colors"
                          title="Inspect detailed syntax, DNS, and SMTP diagnostics"
                        >
                          <Eye className="w-3.5 h-3.5" />
                          <span>Inspect</span>
                        </button>
                        <button
                          onClick={() => onDeleteRecord(r.id)}
                          className="p-1.5 rounded-lg text-slate-400 hover:text-rose-600 dark:hover:text-rose-400 hover:bg-rose-50 dark:hover:bg-rose-950/50 transition-colors"
                          title="Delete this record from the database"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>

      {/* Table Footer with Count Info */}
      <div className="px-4 py-3 bg-slate-50/50 dark:bg-navy-950/50 border-t border-slate-200 dark:border-slate-800 flex items-center justify-between text-xs text-slate-500 dark:text-slate-400">
        <span>
          Showing {filteredRecords.length} of {records.length} record{records.length !== 1 ? "s" : ""}
        </span>
        {batchId && (
          <span className="font-mono text-[11px] text-slate-400 hidden sm:inline">
            Batch ID: {batchId}
          </span>
        )}
      </div>
    </div>
  );
};
