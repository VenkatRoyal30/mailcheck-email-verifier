import React, { useState, useMemo } from "react";
import { Play, RotateCcw, FileText, AlertCircle, Info, Loader2 } from "lucide-react";

interface EmailInputFormProps {
  onVerify: (emails: string[], enableSmtp: boolean) => void;
  isLoading: boolean;
  verifyingStep: string;
}

// Educational and safe sample addresses covering diverse outcomes
const SAMPLE_EMAILS = [
  "alex.developer@gmail.com",
  "contact@github.com",
  "support@stripe.com",
  "sales@microsoft.com",
  "user+newsletter@subdomain.example.org",
  "bad-email-without-domain@",
  "missing-at-symbol-example.com",
  "two@@at-signs.com",
  "spaces in address@domain.com",
  "contact@this-domain-does-not-exist-987654321.xyz",
  "alex.developer@gmail.com", // Intentional duplicate
];

export const EmailInputForm: React.FC<EmailInputFormProps> = ({
  onVerify,
  isLoading,
  verifyingStep,
}) => {
  const [text, setText] = useState<string>("");
  const [enableSmtp, setEnableSmtp] = useState<boolean>(false);

  // Parse lines
  const parsedEmails = useMemo(() => {
    return text
      .split("\n")
      .map((line) => line.trim())
      .filter((line) => line.length > 0);
  }, [text]);

  // Duplicate analysis
  const duplicateStats = useMemo(() => {
    const seen = new Set<string>();
    let duplicates = 0;
    parsedEmails.forEach((email) => {
      const lower = email.toLowerCase();
      if (seen.has(lower)) {
        duplicates++;
      } else {
        seen.add(lower);
      }
    });
    return {
      total: parsedEmails.length,
      unique: seen.size,
      duplicates,
    };
  }, [parsedEmails]);

  const isOverLimit = duplicateStats.total > 100;
  const canSubmit = duplicateStats.total > 0 && !isOverLimit && !isLoading;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!canSubmit) return;
    onVerify(parsedEmails, enableSmtp);
  };

  const handleLoadSample = () => {
    setText(SAMPLE_EMAILS.join("\n"));
    setEnableSmtp(false);
  };

  const handleClear = () => {
    setText("");
    setEnableSmtp(false);
  };

  return (
    <div className="bg-white dark:bg-navy-900 border border-slate-200 dark:border-slate-800 rounded-2xl shadow-sm p-4 sm:p-6 transition-all">
      <form onSubmit={handleSubmit}>
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-3">
          <div>
            <label
              htmlFor="email-batch-input"
              className="text-sm font-bold text-slate-900 dark:text-white flex items-center gap-2"
            >
              <span>Email Addresses to Verify</span>
              <span className="text-xs font-normal text-slate-500 dark:text-slate-400">
                (One address per line)
              </span>
            </label>
          </div>

          {/* Real-time Address Counter & Duplicate Warning */}
          <div className="flex items-center gap-2 text-xs">
            <span
              className={`font-mono font-semibold px-2 py-0.5 rounded-md border ${
                isOverLimit
                  ? "bg-rose-50 dark:bg-rose-950 text-rose-700 dark:text-rose-300 border-rose-300 dark:border-rose-800"
                  : duplicateStats.total > 0
                  ? "bg-brand-50 dark:bg-brand-950 text-brand-700 dark:text-brand-300 border-brand-200 dark:border-brand-800"
                  : "bg-slate-100 dark:bg-navy-800 text-slate-500 dark:text-slate-400 border-slate-200 dark:border-slate-700"
              }`}
            >
              {duplicateStats.total} / 100 max
            </span>

            {duplicateStats.duplicates > 0 && (
              <span
                className="inline-flex items-center gap-1 text-[11px] font-medium text-amber-700 dark:text-amber-400 bg-amber-50 dark:bg-amber-950/70 border border-amber-200 dark:border-amber-800/80 px-2 py-0.5 rounded-md"
                title={`${duplicateStats.duplicates} duplicate address(es) detected in input`}
              >
                <AlertCircle className="w-3 h-3" />
                {duplicateStats.duplicates} duplicate{duplicateStats.duplicates > 1 ? "s" : ""}
              </span>
            )}
          </div>
        </div>

        {/* Text Area */}
        <div className="relative">
          <textarea
            id="email-batch-input"
            rows={7}
            disabled={isLoading}
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder="paste emails here, e.g.:&#10;user@example.com&#10;team@domain.org&#10;info@company.co"
            className={`w-full font-mono text-sm p-3.5 rounded-xl border bg-slate-50/50 dark:bg-navy-950/50 text-slate-900 dark:text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-2 transition-all ${
              isOverLimit
                ? "border-rose-500 focus:ring-rose-500/30"
                : "border-slate-200 dark:border-slate-800 focus:border-brand-500 focus:ring-brand-500/20"
            } disabled:opacity-60`}
          />
        </div>

        {/* Optional SMTP Probing Toggle & Disclosures */}
        <div
          className={`mt-3 p-3 rounded-xl border transition-all text-xs ${
            enableSmtp
              ? "bg-amber-50/80 dark:bg-amber-950/40 border-amber-300 dark:border-amber-800"
              : "bg-slate-50 dark:bg-navy-950/70 border-slate-200/80 dark:border-slate-800"
          }`}
        >
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <label className="flex items-center gap-2 cursor-pointer select-none">
              <input
                type="checkbox"
                checked={enableSmtp}
                disabled={isLoading}
                onChange={(e) => setEnableSmtp(e.target.checked)}
                className="w-4 h-4 text-brand-600 rounded border-slate-300 dark:border-slate-700 focus:ring-brand-500 disabled:opacity-50"
              />
              <span className="font-semibold text-slate-800 dark:text-slate-200">
                Enable SMTP Mailbox Probing
              </span>
              <span className="text-[10px] text-amber-700 dark:text-amber-400 font-medium px-1.5 py-0.5 rounded bg-amber-100 dark:bg-amber-950 border border-amber-300 dark:border-amber-800">
                Optional / Experimental
              </span>
            </label>

            <p className="text-[11px] text-slate-500 dark:text-slate-400 flex items-center gap-1">
              <Info className="w-3.5 h-3.5 text-slate-400 shrink-0" />
              <span>
                {enableSmtp
                  ? "SMTP active: connects to port 25 with retries (takes longer)."
                  : "Disabled by default (recommended): fast Syntax & DNS MX verification without port 25 timeouts."}
              </span>
            </p>
          </div>

          {enableSmtp && (
            <div className="mt-2.5 pt-2.5 border-t border-amber-200 dark:border-amber-800/60 text-[11px] text-amber-900 dark:text-amber-200 flex items-start gap-1.5 leading-relaxed">
              <AlertCircle className="w-3.5 h-3.5 text-amber-600 dark:text-amber-400 shrink-0 mt-0.5" />
              <span>
                <strong>Cloud Port 25 Notice:</strong> Hosting platforms (including Render) block outbound TCP port 25. Enabling this probe will cause connections to time out and report <strong>Unknown</strong>. Uncheck this box if you want fast verification based on syntax and active DNS mail routing (which classifies valid MX domains as <em>Likely to be delivered</em>).
              </span>
            </div>
          )}
        </div>

        {/* Action Buttons & Progress Feedback */}
        <div className="mt-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={handleLoadSample}
              disabled={isLoading}
              className="inline-flex items-center gap-1.5 px-3 py-2 rounded-xl text-xs font-semibold text-slate-700 dark:text-slate-300 bg-slate-100 hover:bg-slate-200 dark:bg-navy-800 dark:hover:bg-slate-800 border border-slate-200 dark:border-slate-700 transition-colors disabled:opacity-50"
            >
              <FileText className="w-3.5 h-3.5" />
              <span>Load Sample Data</span>
            </button>
            <button
              type="button"
              onClick={handleClear}
              disabled={isLoading || !text}
              className="inline-flex items-center gap-1.5 px-3 py-2 rounded-xl text-xs font-semibold text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-navy-800 border border-transparent hover:border-slate-200 dark:hover:border-slate-700 transition-colors disabled:opacity-40"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              <span>Clear</span>
            </button>
          </div>

          <div className="flex items-center gap-3">
            {isLoading && (
              <div className="flex items-center gap-2 text-xs font-medium text-brand-600 dark:text-brand-400 animate-pulse">
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>{verifyingStep || "Processing verification pipeline..."}</span>
              </div>
            )}

            <button
              type="submit"
              disabled={!canSubmit}
              className="inline-flex items-center justify-center gap-2 px-5 py-2.5 rounded-xl text-sm font-bold text-white bg-gradient-to-r from-brand-600 via-brand-700 to-indigo-700 hover:from-brand-500 hover:to-indigo-600 active:scale-[0.98] shadow-md shadow-brand-500/20 disabled:opacity-50 disabled:pointer-events-none transition-all"
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Verifying...</span>
                </>
              ) : (
                <>
                  <Play className="w-4 h-4 fill-current" />
                  <span>Verify {duplicateStats.total > 0 ? `(${duplicateStats.total})` : ""} Addresses</span>
                </>
              )}
            </button>
          </div>
        </div>
      </form>
    </div>
  );
};
