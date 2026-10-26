import React from "react";
import { ShieldCheck, Database, Lock, Clock } from "lucide-react";

export const PrivacyNotice: React.FC = () => {
  return (
    <div className="mt-12 mb-8 pt-8 border-t border-slate-200 dark:border-slate-800">
      <div className="bg-slate-100/70 dark:bg-navy-900/60 border border-slate-200/80 dark:border-slate-800 rounded-2xl p-6 text-xs text-slate-600 dark:text-slate-400">
        <div className="flex items-center gap-2 mb-3">
          <ShieldCheck className="w-5 h-5 text-brand-600 dark:text-brand-400" />
          <h4 className="text-sm font-bold text-slate-900 dark:text-white">
            Privacy, Retention & Security Disclosures
          </h4>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-4 text-[12px] leading-relaxed">
          <div className="flex items-start gap-2.5">
            <Database className="w-4 h-4 text-brand-500 shrink-0 mt-0.5" />
            <div>
              <span className="font-semibold text-slate-800 dark:text-slate-200 block">
                Persistent Audit Storage
              </span>
              Submitted email addresses and their diagnostic results are stored in the local database to support history review, export, and verification audits.
            </div>
          </div>

          <div className="flex items-start gap-2.5">
            <Clock className="w-4 h-4 text-brand-500 shrink-0 mt-0.5" />
            <div>
              <span className="font-semibold text-slate-800 dark:text-slate-200 block">
                Configurable 30-Day Retention
              </span>
              Records are retained for a configurable 30-day lifecycle. Full user controls allow instant deletion of single records or complete batches.
            </div>
          </div>

          <div className="flex items-start gap-2.5">
            <Lock className="w-4 h-4 text-brand-500 shrink-0 mt-0.5" />
            <div>
              <span className="font-semibold text-slate-800 dark:text-slate-200 block">
                Zero Outbound Marketing
              </span>
              MailCheck never sends email messages to submitted recipients or stores passwords, mailbox credentials, or sensitive headers.
            </div>
          </div>
        </div>

        <div className="mt-4 pt-3 border-t border-slate-200/60 dark:border-slate-800 text-[11px] text-slate-400 flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <span>
            Notice: Single-user demonstration SaaS instance. Do not store sensitive production PII without role-based access control.
          </span>
          <span className="font-mono">
            RFC 5321 • RFC 5322 • RFC 7505 Compliant
          </span>
        </div>
      </div>
    </div>
  );
};
