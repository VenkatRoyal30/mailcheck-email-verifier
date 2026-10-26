import React, { useState } from "react";
import {
  X,
  CheckCircle2,
  XCircle,
  HelpCircle,
  Server,
  Code2,
  Mail,
  Copy,
  Check,
  ShieldCheck,
  AlertTriangle,
  Info,
  Layers,
} from "lucide-react";
import { EmailVerificationRecord } from "../types";

interface InspectModalProps {
  record: EmailVerificationRecord | null;
  onClose: () => void;
}

export const InspectModal: React.FC<InspectModalProps> = ({ record, onClose }) => {
  const [activeTab, setActiveTab] = useState<"diagnostics" | "raw">("diagnostics");
  const [copied, setCopied] = useState<boolean>(false);

  if (!record) return null;

  const handleCopyJson = () => {
    navigator.clipboard.writeText(JSON.stringify(record, null, 2));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "Likely to be delivered":
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-emerald-100 dark:bg-emerald-950/80 text-emerald-800 dark:text-emerald-300 border border-emerald-300 dark:border-emerald-800">
            <CheckCircle2 className="w-3.5 h-3.5" />
            Likely to be delivered
          </span>
        );
      case "Likely to bounce":
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-rose-100 dark:bg-rose-950/80 text-rose-800 dark:text-rose-300 border border-rose-300 dark:border-rose-800">
            <XCircle className="w-3.5 h-3.5" />
            Likely to bounce
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-amber-100 dark:bg-amber-950/80 text-amber-800 dark:text-amber-300 border border-amber-300 dark:border-amber-800">
            <HelpCircle className="w-3.5 h-3.5" />
            {status || "Unknown"}
          </span>
        );
    }
  };

  const syntax = record.syntax_diagnostic;
  const dns = record.dns_diagnostic;
  const smtp = record.smtp_diagnostic;

  const isSmtpTimeoutOrBlocked =
    smtp?.port_blocked ||
    (smtp?.message && smtp.message.toLowerCase().includes("timed out")) ||
    (record.reason && record.reason.toLowerCase().includes("timed out")) ||
    (record.reason && record.reason.toLowerCase().includes("could not be reached"));

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 bg-slate-900/60 backdrop-blur-sm animate-fade-in">
      <div className="bg-white dark:bg-navy-900 border border-slate-200 dark:border-slate-800 rounded-2xl max-w-3xl w-full max-h-[90vh] flex flex-col shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="px-5 py-4 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between bg-slate-50/50 dark:bg-navy-950/40">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-xl bg-brand-100 dark:bg-brand-950 text-brand-600 dark:text-brand-300">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-slate-900 dark:text-white flex items-center gap-2">
                <span>Verification Diagnostics</span>
              </h3>
              <p className="text-xs font-mono text-slate-500 dark:text-slate-400">
                {record.original_email}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {getStatusBadge(record.status)}
            <button
              onClick={onClose}
              className="p-1.5 rounded-lg text-slate-400 hover:text-slate-700 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-navy-800 transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Tab Toggle */}
        <div className="px-5 pt-3 pb-0 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <button
              onClick={() => setActiveTab("diagnostics")}
              className={`pb-2.5 text-xs font-semibold border-b-2 transition-all ${
                activeTab === "diagnostics"
                  ? "border-brand-600 text-brand-600 dark:text-brand-400"
                  : "border-transparent text-slate-500 hover:text-slate-800 dark:hover:text-slate-300"
              }`}
            >
              Multi-Stage Inspection
            </button>
            <button
              onClick={() => setActiveTab("raw")}
              className={`pb-2.5 text-xs font-semibold border-b-2 transition-all ${
                activeTab === "raw"
                  ? "border-brand-600 text-brand-600 dark:text-brand-400"
                  : "border-transparent text-slate-500 hover:text-slate-800 dark:hover:text-slate-300"
              }`}
            >
              Raw Payload JSON
            </button>
          </div>

          {activeTab === "raw" && (
            <button
              onClick={handleCopyJson}
              className="inline-flex items-center gap-1 text-[11px] font-semibold text-slate-600 dark:text-slate-300 bg-slate-100 hover:bg-slate-200 dark:bg-navy-800 dark:hover:bg-slate-800 px-2 py-1 rounded-md transition-colors"
            >
              {copied ? <Check className="w-3 h-3 text-emerald-500" /> : <Copy className="w-3 h-3" />}
              <span>{copied ? "Copied" : "Copy JSON"}</span>
            </button>
          )}
        </div>

        {/* Modal Body */}
        <div className="p-5 overflow-y-auto space-y-4">
          {activeTab === "raw" ? (
            <pre className="p-4 rounded-xl bg-slate-900 text-slate-100 font-mono text-xs overflow-x-auto leading-relaxed border border-slate-800">
              {JSON.stringify(record, null, 2)}
            </pre>
          ) : (
            <>
              {/* Separate Status Overview Cards Grid */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
                {/* 1. Overall Classification */}
                <div className="p-3 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-navy-950/60">
                  <div className="flex items-center gap-1.5 text-[11px] font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-1">
                    <Layers className="w-3.5 h-3.5 text-brand-500" />
                    <span>Overall</span>
                  </div>
                  <div className="text-xs font-bold text-slate-900 dark:text-white truncate">
                    {record.status}
                  </div>
                </div>

                {/* 2. Syntax Status */}
                <div className="p-3 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-navy-950/60">
                  <div className="flex items-center gap-1.5 text-[11px] font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-1">
                    <Code2 className="w-3.5 h-3.5 text-indigo-500" />
                    <span>Syntax</span>
                  </div>
                  <div className="text-xs font-bold text-slate-900 dark:text-white">
                    {syntax?.valid ? (
                      <span className="text-emerald-600 dark:text-emerald-400">PASS (RFC Valid)</span>
                    ) : (
                      <span className="text-rose-600 dark:text-rose-400">FAIL (Invalid)</span>
                    )}
                  </div>
                </div>

                {/* 3. DNS/MX Status */}
                <div className="p-3 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-navy-950/60">
                  <div className="flex items-center gap-1.5 text-[11px] font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-1">
                    <Server className="w-3.5 h-3.5 text-blue-500" />
                    <span>DNS / MX</span>
                  </div>
                  <div className="text-xs font-bold text-slate-900 dark:text-white truncate">
                    {dns?.status === "PASS" ? (
                      <span className="text-emerald-600 dark:text-emerald-400">PASS (Active)</span>
                    ) : dns?.status === "UNKNOWN" ? (
                      <span className="text-amber-600 dark:text-amber-400">UNKNOWN (Timeout)</span>
                    ) : (
                      <span className="text-rose-600 dark:text-rose-400">FAIL (No Route)</span>
                    )}
                  </div>
                </div>

                {/* 4. SMTP Status */}
                <div className="p-3 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-navy-950/60">
                  <div className="flex items-center gap-1.5 text-[11px] font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-1">
                    <Mail className="w-3.5 h-3.5 text-purple-500" />
                    <span>SMTP Probe</span>
                  </div>
                  <div className="text-xs font-bold text-slate-900 dark:text-white truncate">
                    {record.smtp_skipped ? (
                      <span className="text-slate-500">DISABLED (Skipped)</span>
                    ) : smtp?.status === "PASS" ? (
                      <span className="text-emerald-600 dark:text-emerald-400">
                        PASS {smtp.is_catch_all ? "(Catch-All)" : "(Accepted)"}
                      </span>
                    ) : smtp?.status === "FAIL" ? (
                      <span className="text-rose-600 dark:text-rose-400">FAIL (Rejected)</span>
                    ) : (
                      <span className="text-amber-600 dark:text-amber-400">
                        UNKNOWN {isSmtpTimeoutOrBlocked ? "(Timeout)" : ""}
                      </span>
                    )}
                  </div>
                </div>
              </div>

              {/* Primary Evidence & Rationale */}
              <div className="p-3.5 rounded-xl bg-slate-100/70 dark:bg-navy-950 border border-slate-200 dark:border-slate-800">
                <div className="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-1">
                  Primary Classification Evidence
                </div>
                <div className="text-xs sm:text-sm font-semibold text-slate-800 dark:text-slate-200 leading-relaxed">
                  {record.reason}
                </div>
                {record.normalized_email && record.normalized_email !== record.original_email && (
                  <div className="mt-2 text-xs text-slate-500 dark:text-slate-400 font-mono">
                    Normalized: {record.normalized_email}
                  </div>
                )}
              </div>

              {/* Educational Context for SMTP Timeout/Unknown */}
              {isSmtpTimeoutOrBlocked && record.status === "Unknown" && (
                <div className="p-3.5 rounded-xl bg-amber-50/80 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-800/60 text-xs text-amber-900 dark:text-amber-200 flex items-start gap-2.5 leading-relaxed">
                  <Info className="w-4 h-4 text-amber-600 dark:text-amber-400 shrink-0 mt-0.5" />
                  <div>
                    <span className="font-bold block mb-0.5">
                      Understanding SMTP Timeouts & Provider Protections
                    </span>
                    The domain’s mail exchange (MX) routing is active and syntax is valid. However, direct port 25 connections to mail servers (like Google’s <code>gmail-smtp-in.l.google.com</code>) frequently time out due to residential/cloud firewall blocks on outbound port 25 or provider anti-enumeration rate limiting. <strong>An SMTP timeout is never treated as proof that a mailbox is invalid.</strong> MailCheck reports this evidence-based classification as <strong>Unknown</strong>.
                  </div>
                </div>
              )}

              {/* Stage 1: Syntax Format Validation */}
              <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-navy-900">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <Code2 className="w-4 h-4 text-brand-600 dark:text-brand-400" />
                    <h4 className="text-xs font-bold uppercase tracking-wider text-slate-900 dark:text-white">
                      Stage 1: RFC Format & Syntax
                    </h4>
                  </div>
                  <span
                    className={`text-[11px] font-bold px-2 py-0.5 rounded-full ${
                      syntax?.valid
                        ? "bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300"
                        : "bg-rose-100 text-rose-800 dark:bg-rose-950 dark:text-rose-300"
                    }`}
                  >
                    {syntax?.valid ? "PASS" : "FAIL"}
                  </span>
                </div>

                <div className="grid grid-cols-2 gap-3 text-xs">
                  <div>
                    <span className="text-slate-400">Local Part:</span>
                    <p className="font-mono text-slate-800 dark:text-slate-200 truncate">
                      {syntax?.local_part || "N/A"}
                    </p>
                  </div>
                  <div>
                    <span className="text-slate-400">Domain Part:</span>
                    <p className="font-mono text-slate-800 dark:text-slate-200 truncate">
                      {syntax?.domain || "N/A"}
                    </p>
                  </div>
                </div>

                {syntax?.error_message && (
                  <div className="mt-2 text-xs text-rose-600 dark:text-rose-400 bg-rose-50 dark:bg-rose-950/60 p-2 rounded-lg border border-rose-200 dark:border-rose-900">
                    <span className="font-semibold">Error: </span>
                    {syntax.error_message}
                  </div>
                )}
              </div>

              {/* Stage 2: DNS & MX Mail Routing */}
              <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-navy-900">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <Server className="w-4 h-4 text-brand-600 dark:text-brand-400" />
                    <h4 className="text-xs font-bold uppercase tracking-wider text-slate-900 dark:text-white">
                      Stage 2: DNS MX Mail Routing
                    </h4>
                  </div>
                  <span
                    className={`text-[11px] font-bold px-2 py-0.5 rounded-full ${
                      dns?.status === "PASS"
                        ? "bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300"
                        : dns?.status === "UNKNOWN"
                        ? "bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300"
                        : "bg-rose-100 text-rose-800 dark:bg-rose-950 dark:text-rose-300"
                    }`}
                  >
                    {dns?.status || "SKIPPED"}
                  </span>
                </div>

                <div className="text-xs text-slate-600 dark:text-slate-300 mb-2">
                  {dns?.reason || "DNS lookup was not performed."}
                </div>

                {/* MX Records List */}
                {dns?.mx_records && dns.mx_records.length > 0 && (
                  <div className="mt-2 space-y-1.5">
                    <span className="text-[11px] font-semibold text-slate-400 uppercase">
                      Configured Mail Exchanges (Priority Sorted):
                    </span>
                    <div className="rounded-lg border border-slate-200 dark:border-slate-800 overflow-hidden divide-y divide-slate-100 dark:divide-slate-800 text-xs">
                      {dns.mx_records.map((mx, idx) => (
                        <div
                          key={idx}
                          className="px-3 py-1.5 flex items-center justify-between font-mono bg-slate-50/50 dark:bg-navy-950/40"
                        >
                          <span className="text-slate-800 dark:text-slate-200">
                            {mx.exchange}
                          </span>
                          <span className="text-slate-400 text-[11px]">
                            Pref: {mx.preference}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Fallback A/AAAA records */}
                {dns?.fallback_records && dns.fallback_records.length > 0 && (
                  <div className="mt-2 space-y-1.5">
                    <span className="text-[11px] font-semibold text-slate-400 uppercase">
                      RFC 5321 Fallback Address Records:
                    </span>
                    <div className="rounded-lg border border-slate-200 dark:border-slate-800 overflow-hidden divide-y divide-slate-100 dark:divide-slate-800 text-xs">
                      {dns.fallback_records.map((fb, idx) => (
                        <div
                          key={idx}
                          className="px-3 py-1.5 flex items-center justify-between font-mono bg-slate-50/50 dark:bg-navy-950/40"
                        >
                          <span className="text-slate-800 dark:text-slate-200">{fb.address}</span>
                          <span className="text-slate-400 text-[11px]">{fb.type} Record</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {/* Stage 3: SMTP Mailbox Probing */}
              <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-navy-900">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <Mail className="w-4 h-4 text-brand-600 dark:text-brand-400" />
                    <h4 className="text-xs font-bold uppercase tracking-wider text-slate-900 dark:text-white">
                      Stage 3: SMTP Mailbox Probe
                    </h4>
                  </div>
                  <span
                    className={`text-[11px] font-bold px-2 py-0.5 rounded-full ${
                      record.smtp_skipped
                        ? "bg-slate-100 text-slate-600 dark:bg-navy-800 dark:text-slate-400"
                        : smtp?.status === "PASS"
                        ? "bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300"
                        : smtp?.status === "FAIL"
                        ? "bg-rose-100 text-rose-800 dark:bg-rose-950 dark:text-rose-300"
                        : "bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300"
                    }`}
                  >
                    {record.smtp_skipped ? "DISABLED / SKIPPED" : smtp?.status || "UNKNOWN"}
                  </span>
                </div>

                <div className="text-xs text-slate-600 dark:text-slate-300">
                  {smtp?.message || "SMTP probe disabled by default."}
                </div>

                {smtp?.is_catch_all && (
                  <div className="mt-2 flex items-center gap-2 p-2 rounded-lg bg-amber-50 dark:bg-amber-950/60 border border-amber-200 dark:border-amber-800 text-amber-800 dark:text-amber-300 text-xs">
                    <AlertTriangle className="w-3.5 h-3.5 shrink-0" />
                    <span>
                      Catch-all domain detected: The recipient server accepts arbitrary addresses. Mailbox existence cannot be guaranteed.
                    </span>
                  </div>
                )}

                {smtp?.port_blocked && (
                  <div className="mt-2 flex items-center gap-2 p-2 rounded-lg bg-slate-100 dark:bg-navy-950 text-slate-700 dark:text-slate-300 text-xs border border-slate-200 dark:border-slate-800">
                    <Info className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                    <span>Outbound Port 25 connection blocked or throttled by network environment.</span>
                  </div>
                )}
              </div>
            </>
          )}
        </div>

        {/* Footer */}
        <div className="px-5 py-3 border-t border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-navy-950/40 flex items-center justify-between">
          <span className="text-[11px] text-slate-400 font-mono">
            Record ID: {record.id.slice(0, 13)}...
          </span>
          <button
            onClick={onClose}
            className="px-4 py-1.5 rounded-xl text-xs font-semibold text-slate-700 dark:text-slate-300 bg-white dark:bg-navy-900 border border-slate-200 dark:border-slate-700 hover:bg-slate-100 dark:hover:bg-navy-800 transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
