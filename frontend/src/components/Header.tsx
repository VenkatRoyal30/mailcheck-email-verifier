import React from "react";
import { Mail, History, Sun, Moon, ShieldCheck } from "lucide-react";
import { ApiStatusIndicator } from "./ApiStatusIndicator";
import { HealthStatus } from "../types";

interface HeaderProps {
  activeTab: "verifier" | "history";
  setActiveTab: (tab: "verifier" | "history") => void;
  historyCount: number;
  health: HealthStatus | null;
  healthLoading: boolean;
  onRefreshHealth: () => void;
  darkMode: boolean;
  setDarkMode: (val: boolean) => void;
}

export const Header: React.FC<HeaderProps> = ({
  activeTab,
  setActiveTab,
  historyCount,
  health,
  healthLoading,
  onRefreshHealth,
  darkMode,
  setDarkMode,
}) => {
  return (
    <header className="sticky top-0 z-30 border-b border-slate-200 dark:border-slate-800 bg-white/95 dark:bg-navy-900/95 backdrop-blur-md transition-colors">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Brand Logo & Name */}
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-brand-700 via-brand-600 to-indigo-500 flex items-center justify-center text-white shadow-md shadow-brand-500/20">
            <ShieldCheck className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xl font-bold tracking-tight text-slate-900 dark:text-white">
                Mail<span className="text-brand-600 dark:text-brand-400">Check</span>
              </span>
              <span className="text-[10px] font-semibold tracking-wider uppercase px-2 py-0.5 rounded bg-brand-50 dark:bg-brand-950 text-brand-700 dark:text-brand-300 border border-brand-200 dark:border-brand-800/60">
                PRO SaaS
              </span>
            </div>
            <p className="text-[11px] text-slate-500 dark:text-slate-400 hidden sm:block">
              Evidence-based bulk email deliverability verification
            </p>
          </div>
        </div>

        {/* Center / Right Navigation & Actions */}
        <div className="flex items-center gap-3 sm:gap-4">
          {/* Navigation Tabs */}
          <nav className="flex items-center p-1 rounded-xl bg-slate-100 dark:bg-navy-800 border border-slate-200/80 dark:border-slate-700/60">
            <button
              onClick={() => setActiveTab("verifier")}
              className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-sm font-medium transition-all ${
                activeTab === "verifier"
                  ? "bg-white dark:bg-navy-900 text-brand-700 dark:text-brand-300 shadow-sm"
                  : "text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white"
              }`}
            >
              <Mail className="w-4 h-4" />
              <span>Verifier</span>
            </button>
            <button
              onClick={() => setActiveTab("history")}
              className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-sm font-medium transition-all ${
                activeTab === "history"
                  ? "bg-white dark:bg-navy-900 text-brand-700 dark:text-brand-300 shadow-sm"
                  : "text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white"
              }`}
            >
              <History className="w-4 h-4" />
              <span>History</span>
              {historyCount > 0 && (
                <span className="px-1.5 py-0.2 text-[10px] rounded-full bg-brand-100 dark:bg-brand-950 text-brand-800 dark:text-brand-300 font-bold">
                  {historyCount}
                </span>
              )}
            </button>
          </nav>

          {/* Genuine API Indicator */}
          <ApiStatusIndicator
            health={health}
            loading={healthLoading}
            onRefresh={onRefreshHealth}
          />

          {/* Theme Toggle Button */}
          <button
            onClick={() => setDarkMode(!darkMode)}
            className="p-2 rounded-xl text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-navy-800 border border-transparent hover:border-slate-200 dark:hover:border-slate-700 transition-all"
            title={darkMode ? "Switch to light theme" : "Switch to dark theme"}
            aria-label="Toggle theme"
          >
            {darkMode ? <Sun className="w-4 h-4 text-amber-400" /> : <Moon className="w-4 h-4 text-slate-600" />}
          </button>
        </div>
      </div>
    </header>
  );
};
