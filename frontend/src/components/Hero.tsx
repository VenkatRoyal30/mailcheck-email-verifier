import React from "react";
import { CheckCircle2, XCircle, HelpCircle, Sparkles } from "lucide-react";

export const Hero: React.FC = () => {
  return (
    <div className="relative pt-6 pb-4 sm:pt-8 sm:pb-6 text-center max-w-4xl mx-auto px-4">
      {/* Decorative gradient glow */}
      <div className="absolute inset-x-0 -top-10 -z-10 transform-gpu overflow-hidden blur-3xl" aria-hidden="true">
        <div className="relative left-[calc(50%-11rem)] aspect-[1155/678] w-[36.125rem] -translate-x-1/2 rotate-[30deg] bg-gradient-to-tr from-brand-400 to-indigo-600 opacity-20 sm:left-[calc(50%-30rem)] sm:w-[72.1875rem]"></div>
      </div>

      {/* Pill Badge */}
      <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold bg-brand-50 dark:bg-brand-950/70 text-brand-700 dark:text-brand-300 border border-brand-200 dark:border-brand-800/60 mb-4 shadow-sm">
        <Sparkles className="w-3.5 h-3.5 text-brand-500" />
        <span>Evidence-Based Deliverability Engine</span>
        <span className="text-slate-300 dark:text-slate-700">•</span>
        <span className="text-slate-500 dark:text-slate-400 font-normal">Not Delivery Guarantees</span>
      </div>

      <h1 className="text-3xl sm:text-4xl lg:text-5xl font-extrabold tracking-tight text-slate-900 dark:text-white">
        High-Confidence <span className="text-transparent bg-clip-text bg-gradient-to-r from-brand-600 via-indigo-600 to-violet-600 dark:from-brand-400 dark:via-indigo-300 dark:to-violet-400">Bulk Email Verification</span>
      </h1>
      
      <p className="mt-3 text-sm sm:text-base text-slate-600 dark:text-slate-300 max-w-2xl mx-auto leading-relaxed">
        Validate format compliance against RFC specifications, probe live DNS Mail Exchange (MX) and fallback A/AAAA records, and identify delivery risks before launching campaigns.
      </p>

      {/* The 3 Official Classifications */}
      <div className="mt-6 grid grid-cols-1 sm:grid-cols-3 gap-3 max-w-3xl mx-auto text-left">
        <div className="flex items-start gap-3 p-3 rounded-xl bg-white dark:bg-navy-900 border border-emerald-200/80 dark:border-emerald-900/50 shadow-sm">
          <div className="p-1.5 rounded-lg bg-emerald-50 dark:bg-emerald-950/80 text-emerald-600 dark:text-emerald-400 shrink-0">
            <CheckCircle2 className="w-4 h-4" />
          </div>
          <div>
            <div className="text-xs font-bold text-emerald-800 dark:text-emerald-300">Likely to be delivered</div>
            <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-0.5 leading-snug">
              Syntax passes RFC rules and verified mail-routing MX servers accept traffic.
            </p>
          </div>
        </div>

        <div className="flex items-start gap-3 p-3 rounded-xl bg-white dark:bg-navy-900 border border-rose-200/80 dark:border-rose-900/50 shadow-sm">
          <div className="p-1.5 rounded-lg bg-rose-50 dark:bg-rose-950/80 text-rose-600 dark:text-rose-400 shrink-0">
            <XCircle className="w-4 h-4" />
          </div>
          <div>
            <div className="text-xs font-bold text-rose-800 dark:text-rose-300">Likely to bounce</div>
            <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-0.5 leading-snug">
              Invalid syntax, nonexistent domain (NXDOMAIN), or confirmed absence of mail routes.
            </p>
          </div>
        </div>

        <div className="flex items-start gap-3 p-3 rounded-xl bg-white dark:bg-navy-900 border border-amber-200/80 dark:border-amber-900/50 shadow-sm">
          <div className="p-1.5 rounded-lg bg-amber-50 dark:bg-amber-950/80 text-amber-600 dark:text-amber-400 shrink-0">
            <HelpCircle className="w-4 h-4" />
          </div>
          <div>
            <div className="text-xs font-bold text-amber-800 dark:text-amber-300">Unknown</div>
            <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-0.5 leading-snug">
              DNS timeout, SERVFAIL, temporary resolver failure, or inconclusive mail probe.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
