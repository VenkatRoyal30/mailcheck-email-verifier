import React from "react";
import {
  History,
  Trash2,
  Download,
  FolderOpen,
  Calendar,
  CheckCircle2,
  XCircle,
  HelpCircle,
  Layers,
  ShieldAlert,
  Loader2
} from "lucide-react";
import { VerificationBatch } from "../types";
import { apiClient } from "../api/client";

interface HistoryViewProps {
  batches: VerificationBatch[];
  loading: boolean;
  onOpenBatch: (batchId: string) => void;
  onDeleteBatch: (batchId: string) => void;
  onClearHistory: () => void;
}

export const HistoryView: React.FC<HistoryViewProps> = ({
  batches,
  loading,
  onOpenBatch,
  onDeleteBatch,
  onClearHistory,
}) => {

  const formatDate = (isoString: string) => {
    try {
      const date = new Date(isoString);
      return {
        formatted: date.toLocaleDateString(undefined, {
          year: "numeric",
          month: "short",
          day: "numeric",
        }),
        time: date.toLocaleTimeString(undefined, {
          hour: "2-digit",
          minute: "2-digit",
          second: "2-digit",
        }),
      };
    } catch {
      return { formatted: isoString, time: "" };
    }
  };

  const handleDownloadCsv = (batchId: string) => {
    const url = apiClient.getExportCsvUrl(batchId);
    window.open(url, "_blank");
  };

  return (
    <div className="space-y-6">
      {/* Retention Policy & Private Demo Notice */}
      <div className="p-4 rounded-2xl bg-brand-50/60 dark:bg-brand-950/40 border border-brand-200 dark:border-brand-900/60 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs">
        <div className="flex items-start sm:items-center gap-3">
          <div className="p-2 rounded-xl bg-brand-100 dark:bg-brand-900 text-brand-700 dark:text-brand-300 shrink-0">
            <ShieldAlert className="w-4 h-4" />
          </div>
          <div>
            <div className="font-bold text-slate-900 dark:text-white">
              Persistent Local Storage & 30-Day Retention Policy
            </div>
            <p className="text-slate-600 dark:text-slate-300 mt-0.5">
              Verification batches are persistently recorded in the SQLite/PostgreSQL database for auditing. You can delete individual records or purge complete batches at any time.
            </p>
          </div>
        </div>

        {batches.length > 0 && (
          <button
            onClick={onClearHistory}
            className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-semibold text-rose-700 dark:text-rose-300 bg-rose-50 hover:bg-rose-100 dark:bg-rose-950 dark:hover:bg-rose-900 border border-rose-200 dark:border-rose-900 transition-colors shrink-0"
          >
            <Trash2 className="w-3.5 h-3.5" />
            <span>Clear All History</span>
          </button>
        )}
      </div>

      {/* Batch List */}
      <div className="bg-white dark:bg-navy-900 border border-slate-200 dark:border-slate-800 rounded-2xl shadow-sm overflow-hidden">
        <div className="p-4 sm:p-5 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <History className="w-5 h-5 text-brand-600 dark:text-brand-400" />
            <h3 className="font-bold text-base text-slate-900 dark:text-white">
              Previous Verification Batches
            </h3>
            <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-slate-100 dark:bg-navy-800 text-slate-600 dark:text-slate-400">
              {batches.length}
            </span>
          </div>
        </div>

        {loading ? (
          <div className="py-16 text-center text-slate-400 flex flex-col items-center justify-center gap-2">
            <Loader2 className="w-6 h-6 animate-spin text-brand-600" />
            <span className="text-xs">Loading verification history...</span>
          </div>
        ) : batches.length === 0 ? (
          <div className="py-16 text-center text-slate-400">
            <Layers className="w-10 h-10 mx-auto text-slate-300 dark:text-slate-700 mb-2" />
            <p className="text-sm font-semibold text-slate-700 dark:text-slate-300">
              No verification history recorded yet
            </p>
            <p className="text-xs text-slate-400 mt-1 max-w-sm mx-auto">
              Run your first batch in the Verifier tab to see your persistent history and exportable audit records here.
            </p>
          </div>
        ) : (
          <div className="divide-y divide-slate-100 dark:divide-slate-800">
            {batches.map((batch) => {
              const { formatted, time } = formatDate(batch.created_at);

              return (
                <div
                  key={batch.id}
                  className="p-4 sm:p-5 flex flex-col md:flex-row md:items-center justify-between gap-4 hover:bg-slate-50/60 dark:hover:bg-navy-950/40 transition-colors"
                >
                  {/* Left: Batch Info & Timestamp */}
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-xs font-bold text-slate-900 dark:text-white">
                        Batch {batch.id.slice(0, 8)}
                      </span>
                      {batch.smtp_enabled && (
                        <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-brand-50 dark:bg-brand-950 text-brand-700 dark:text-brand-300 border border-brand-200 dark:border-brand-800">
                          SMTP Probed
                        </span>
                      )}
                    </div>

                    <div className="flex items-center gap-2 text-xs text-slate-400">
                      <Calendar className="w-3.5 h-3.5" />
                      <span>{formatted}</span>
                      <span>•</span>
                      <span>{time}</span>
                    </div>
                  </div>

                  {/* Middle: Count Badges */}
                  <div className="flex items-center flex-wrap gap-2 text-xs">
                    <span className="px-2.5 py-1 rounded-lg bg-slate-100 dark:bg-navy-800 text-slate-700 dark:text-slate-300 font-semibold" title={`Total addresses: ${batch.total_count}`}>
                      Total: {batch.total_count}
                    </span>
                    <span title={`Likely to be delivered: ${batch.delivered_count}`} className="px-2.5 py-1 rounded-lg bg-emerald-50 dark:bg-emerald-950/70 text-emerald-700 dark:text-emerald-400 font-semibold border border-emerald-200 dark:border-emerald-800/80 flex items-center gap-1">
                      <CheckCircle2 className="w-3 h-3" /> {batch.delivered_count}
                    </span>
                    <span title={`Likely to bounce: ${batch.bounce_count}`} className="px-2.5 py-1 rounded-lg bg-rose-50 dark:bg-rose-950/70 text-rose-700 dark:text-rose-400 font-semibold border border-rose-200 dark:border-rose-800/80 flex items-center gap-1">
                      <XCircle className="w-3 h-3" /> {batch.bounce_count}
                    </span>
                    <span title={`Unknown: ${batch.unknown_count}`} className="px-2.5 py-1 rounded-lg bg-amber-50 dark:bg-amber-950/70 text-amber-700 dark:text-amber-400 font-semibold border border-amber-200 dark:border-amber-800/80 flex items-center gap-1">
                      <HelpCircle className="w-3 h-3" /> {batch.unknown_count}
                    </span>
                  </div>

                  {/* Right: Actions */}
                  <div className="flex items-center gap-2 shrink-0">
                    <button
                      onClick={() => onOpenBatch(batch.id)}
                      className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold text-brand-700 dark:text-brand-300 bg-brand-50 hover:bg-brand-100 dark:bg-brand-950/70 dark:hover:bg-brand-900 border border-brand-200 dark:border-brand-800 transition-colors"
                      title="Load batch into main verification results table"
                    >
                      <FolderOpen className="w-3.5 h-3.5" />
                      <span>View Results</span>
                    </button>

                    <button
                      onClick={() => handleDownloadCsv(batch.id)}
                      className="p-1.5 rounded-lg text-slate-500 hover:text-slate-800 dark:text-slate-400 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-navy-800 transition-colors"
                      title="Download batch CSV"
                    >
                      <Download className="w-4 h-4" />
                    </button>

                    <button
                      onClick={() => onDeleteBatch(batch.id)}
                      className="p-1.5 rounded-lg text-slate-400 hover:text-rose-600 dark:hover:text-rose-400 hover:bg-rose-50 dark:hover:bg-rose-950/50 transition-colors"
                      title="Delete this batch from database"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};
