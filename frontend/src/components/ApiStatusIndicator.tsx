import React from "react";
import { HealthStatus } from "../types";
import { RefreshCw } from "lucide-react";

interface ApiStatusIndicatorProps {
  health: HealthStatus | null;
  loading: boolean;
  onRefresh: () => void;
}

export const ApiStatusIndicator: React.FC<ApiStatusIndicatorProps> = ({
  health,
  loading,
  onRefresh,
}) => {
  const isHealthy = health?.status === "healthy";
  const isOffline = !health || health.status === "offline";

  return (
    <div className="flex items-center gap-2 text-xs font-medium px-3 py-1.5 rounded-full border bg-white dark:bg-navy-900 border-slate-200 dark:border-slate-800 shadow-sm transition-all">
      {loading ? (
        <RefreshCw className="w-3.5 h-3.5 text-slate-400 animate-spin" />
      ) : isHealthy ? (
        <span className="relative flex h-2 w-2">
          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
          <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
        </span>
      ) : (
        <span className="relative flex h-2 w-2">
          <span className="relative inline-flex rounded-full h-2 w-2 bg-rose-500"></span>
        </span>
      )}

      <div className="flex items-center gap-1.5">
        <span className="text-slate-500 dark:text-slate-400">API:</span>
        {isHealthy ? (
          <span className="text-emerald-700 dark:text-emerald-400 font-semibold flex items-center gap-1">
            Connected
            <span className="text-[10px] text-slate-400 font-normal hidden sm:inline">
              ({health.database === "connected" ? "DB Active" : "DB Issue"})
            </span>
          </span>
        ) : isOffline ? (
          <span className="text-rose-600 dark:text-rose-400 font-semibold flex items-center gap-1">
            Offline
          </span>
        ) : (
          <span className="text-amber-600 dark:text-amber-400 font-semibold">
            Degraded
          </span>
        )}
      </div>

      <button
        onClick={onRefresh}
        disabled={loading}
        title="Check API health"
        className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 ml-1 transition-colors disabled:opacity-50"
      >
        <RefreshCw className={`w-3 h-3 ${loading ? "animate-spin" : ""}`} />
      </button>
    </div>
  );
};
