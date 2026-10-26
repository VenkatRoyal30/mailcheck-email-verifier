import React from "react";
import { CheckCircle2, XCircle, HelpCircle, Layers, Filter } from "lucide-react";
import { StatusFilter } from "../types";

interface SummaryCardsProps {
  total: number;
  delivered: number;
  bounce: number;
  unknown: number;
  activeFilter: StatusFilter;
  onFilterChange: (filter: StatusFilter) => void;
}

export const SummaryCards: React.FC<SummaryCardsProps> = ({
  total,
  delivered,
  bounce,
  unknown,
  activeFilter,
  onFilterChange,
}) => {
  const getPercentage = (count: number) => {
    if (!total || total === 0) return 0;
    return Math.round((count / total) * 100);
  };

  const cards = [
    {
      id: "ALL" as StatusFilter,
      label: "Total Processed",
      count: total,
      percentage: total > 0 ? 100 : 0,
      icon: Layers,
      color: "brand",
      bgLight: "bg-slate-50 dark:bg-navy-900",
      borderActive: "border-brand-500 ring-2 ring-brand-500/20",
      textColor: "text-slate-900 dark:text-white",
      badgeBg: "bg-slate-100 dark:bg-navy-800 text-slate-700 dark:text-slate-300",
    },
    {
      id: "Likely to be delivered" as StatusFilter,
      label: "Likely to be delivered",
      count: delivered,
      percentage: getPercentage(delivered),
      icon: CheckCircle2,
      color: "emerald",
      bgLight: "bg-emerald-50/40 dark:bg-emerald-950/20",
      borderActive: "border-emerald-500 ring-2 ring-emerald-500/20",
      textColor: "text-emerald-700 dark:text-emerald-400",
      badgeBg: "bg-emerald-100/70 dark:bg-emerald-950 text-emerald-800 dark:text-emerald-300",
    },
    {
      id: "Likely to bounce" as StatusFilter,
      label: "Likely to bounce",
      count: bounce,
      percentage: getPercentage(bounce),
      icon: XCircle,
      color: "rose",
      bgLight: "bg-rose-50/40 dark:bg-rose-950/20",
      borderActive: "border-rose-500 ring-2 ring-rose-500/20",
      textColor: "text-rose-700 dark:text-rose-400",
      badgeBg: "bg-rose-100/70 dark:bg-rose-950 text-rose-800 dark:text-rose-300",
    },
    {
      id: "Unknown" as StatusFilter,
      label: "Unknown",
      count: unknown,
      percentage: getPercentage(unknown),
      icon: HelpCircle,
      color: "amber",
      bgLight: "bg-amber-50/40 dark:bg-amber-950/20",
      borderActive: "border-amber-500 ring-2 ring-amber-500/20",
      textColor: "text-amber-700 dark:text-amber-400",
      badgeBg: "bg-amber-100/70 dark:bg-amber-950 text-amber-800 dark:text-amber-300",
    },
  ];

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4 my-6">
      {cards.map((card) => {
        const IconComponent = card.icon;
        const isSelected = activeFilter === card.id;

        return (
          <button
            key={card.id}
            type="button"
            onClick={() => onFilterChange(isSelected && card.id !== "ALL" ? "ALL" : card.id)}
            className={`text-left p-4 rounded-2xl border transition-all relative overflow-hidden group shadow-sm ${
              card.bgLight
            } ${
              isSelected
                ? `${card.borderActive} shadow-md`
                : "border-slate-200 dark:border-slate-800 hover:border-slate-300 dark:hover:border-slate-700"
            }`}
          >
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-slate-500 dark:text-slate-400">
                {card.label}
              </span>
              <div className={`p-1.5 rounded-lg ${card.badgeBg}`}>
                <IconComponent className="w-4 h-4" />
              </div>
            </div>

            <div className="mt-3 flex items-baseline justify-between">
              <span className={`text-2xl sm:text-3xl font-extrabold ${card.textColor}`}>
                {card.count}
              </span>
              <span className="text-xs font-semibold text-slate-400">
                {card.percentage}%
              </span>
            </div>

            {/* Click-to-filter indicator */}
            <div className="mt-2 flex items-center gap-1 text-[10px] font-medium text-slate-400 group-hover:text-slate-600 dark:group-hover:text-slate-300 transition-colors">
              <Filter className="w-2.5 h-2.5" />
              <span>{isSelected ? "Active filter (click to reset)" : "Click to filter"}</span>
            </div>
          </button>
        );
      })}
    </div>
  );
};
