import React, { useState, useEffect, useCallback } from "react";
import { Header } from "./components/Header";
import { Hero } from "./components/Hero";
import { EmailInputForm } from "./components/EmailInputForm";
import { SummaryCards } from "./components/SummaryCards";
import { ResultsTable } from "./components/ResultsTable";
import { InspectModal } from "./components/InspectModal";
import { HistoryView } from "./components/HistoryView";
import { PrivacyNotice } from "./components/PrivacyNotice";
import { ConfirmDialog } from "./components/ConfirmDialog";
import { apiClient } from "./api/client";
import {
  VerificationBatch,
  EmailVerificationRecord,
  HealthStatus,
  StatusFilter,
} from "./types";
import { AlertCircle, CheckCircle2 } from "lucide-react";

export const App: React.FC = () => {
  // Theme state
  const [darkMode, setDarkMode] = useState<boolean>(() => {
    const saved = localStorage.getItem("mailcheck_theme");
    return saved ? saved === "dark" : false;
  });

  // App Navigation
  const [activeTab, setActiveTab] = useState<"verifier" | "history">("verifier");

  // Health state
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [healthLoading, setHealthLoading] = useState<boolean>(false);

  // Active batch / results
  const [currentBatch, setCurrentBatch] = useState<VerificationBatch | null>(null);
  const [records, setRecords] = useState<EmailVerificationRecord[]>([]);
  const [activeFilter, setActiveFilter] = useState<StatusFilter>("ALL");

  // History list
  const [batchesHistory, setBatchesHistory] = useState<VerificationBatch[]>([]);
  const [historyLoading, setHistoryLoading] = useState<boolean>(false);

  // Verification processing state
  const [isVerifying, setIsVerifying] = useState<boolean>(false);
  const [verifyingStep, setVerifyingStep] = useState<string>("");

  // Inspect modal
  const [inspectingRecord, setInspectingRecord] = useState<EmailVerificationRecord | null>(null);

  // Error & Notification banner
  const [errorBanner, setErrorBanner] = useState<string | null>(null);
  const [successBanner, setSuccessBanner] = useState<string | null>(null);

  // Confirmation modal state
  const [confirmDialog, setConfirmDialog] = useState<{
    isOpen: boolean;
    title: string;
    message: string;
    onConfirm: () => void;
  }>({
    isOpen: false,
    title: "",
    message: "",
    onConfirm: () => {},
  });

  // Synchronize dark mode class to HTML element
  useEffect(() => {
    if (darkMode) {
      document.documentElement.classList.add("dark");
      localStorage.setItem("mailcheck_theme", "dark");
    } else {
      document.documentElement.classList.remove("dark");
      localStorage.setItem("mailcheck_theme", "light");
    }
  }, [darkMode]);

  // Load Health Status
  const fetchHealth = useCallback(async () => {
    setHealthLoading(true);
    try {
      const data = await apiClient.getHealth();
      setHealth(data);
      if (errorBanner?.includes("backend API")) {
        setErrorBanner(null);
      }
    } catch (err: any) {
      setHealth(null);
    } finally {
      setHealthLoading(false);
    }
  }, [errorBanner]);

  // Load Verification History
  const fetchHistory = useCallback(async () => {
    setHistoryLoading(true);
    try {
      const data = await apiClient.getHistory();
      setBatchesHistory(data.batches || []);
    } catch (err: any) {
      console.error("Failed to fetch verification history:", err);
    } finally {
      setHistoryLoading(false);
    }
  }, []);

  // Initial load
  useEffect(() => {
    fetchHealth();
    fetchHistory();
  }, [fetchHealth, fetchHistory]);

  // Handle Verify Action
  const handleVerify = async (emails: string[], enableSmtp: boolean) => {
    setErrorBanner(null);
    setSuccessBanner(null);
    setIsVerifying(true);
    setVerifyingStep("Stage 1/3: Validating syntax via RFC specs...");

    try {
      const stepTimer = setTimeout(() => {
        setVerifyingStep("Stage 2/3: Querying DNS MX & routing records...");
      }, 500);

      const batch = await apiClient.verifyEmails(emails, enableSmtp);
      clearTimeout(stepTimer);

      setVerifyingStep("Stage 3/3: Saving verification results...");
      setCurrentBatch(batch);
      setRecords(batch.records || []);
      setActiveFilter("ALL");

      // Refresh history list
      fetchHistory();

      setSuccessBanner(
        `Verification complete! Processed ${batch.total_count} address(es) (${batch.delivered_count} likely to be delivered, ${batch.bounce_count} likely to bounce, ${batch.unknown_count} unknown).`
      );
      setTimeout(() => setSuccessBanner(null), 5000);
    } catch (err: any) {
      console.error("Verification failed:", err);
      setErrorBanner(err.message || "Failed to process verification. Please verify the backend is running.");
    } finally {
      setIsVerifying(false);
      setVerifyingStep("");
    }
  };

  // Open saved batch
  const handleOpenBatch = async (batchId: string) => {
    setErrorBanner(null);
    try {
      const batch = await apiClient.getBatch(batchId);
      setCurrentBatch(batch);
      setRecords(batch.records || []);
      setActiveFilter("ALL");
      setActiveTab("verifier");
    } catch (err: any) {
      setErrorBanner(`Failed to load batch: ${err.message}`);
    }
  };

  // Delete batch with confirmation
  const handleDeleteBatch = (batchId: string) => {
    setConfirmDialog({
      isOpen: true,
      title: "Delete Verification Batch?",
      message: `Are you sure you want to permanently delete Batch ${batchId.slice(0, 8)}? All associated email verification records will be permanently removed.`,
      onConfirm: async () => {
        setConfirmDialog((prev) => ({ ...prev, isOpen: false }));
        try {
          await apiClient.deleteBatch(batchId);
          if (currentBatch?.id === batchId) {
            setCurrentBatch(null);
            setRecords([]);
          }
          fetchHistory();
        } catch (err: any) {
          setErrorBanner(`Failed to delete batch: ${err.message}`);
        }
      },
    });
  };

  // Delete individual record with count update
  const handleDeleteRecord = async (recordId: string) => {
    if (!currentBatch) return;

    try {
      const res = await apiClient.deleteRecord(currentBatch.id, recordId);
      setRecords((prev) => prev.filter((r) => r.id !== recordId));
      if (res.batch) {
        setCurrentBatch((prev) => (prev ? { ...prev, ...res.batch } : null));
      }
      fetchHistory();
    } catch (err: any) {
      setErrorBanner(`Failed to delete record: ${err.message}`);
    }
  };

  // Clear all history with confirmation
  const handleClearHistory = () => {
    setConfirmDialog({
      isOpen: true,
      title: "Clear Entire Verification History?",
      message:
        "This will permanently purge all verification batches and recorded email results from the database. This action cannot be undone.",
      onConfirm: async () => {
        setConfirmDialog((prev) => ({ ...prev, isOpen: false }));
        try {
          await apiClient.clearHistory();
          setBatchesHistory([]);
          setCurrentBatch(null);
          setRecords([]);
          setSuccessBanner("All verification history has been purged successfully.");
          setTimeout(() => setSuccessBanner(null), 4000);
        } catch (err: any) {
          setErrorBanner(`Failed to clear history: ${err.message}`);
        }
      },
    });
  };

  return (
    <div className="min-h-screen flex flex-col bg-slate-50 text-slate-900 dark:bg-navy-950 dark:text-slate-100 transition-colors">
      {/* Header */}
      <Header
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        historyCount={batchesHistory.length}
        health={health}
        healthLoading={healthLoading}
        onRefreshHealth={fetchHealth}
        darkMode={darkMode}
        setDarkMode={setDarkMode}
      />

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* Offline / Error Alert */}
        {errorBanner && (
          <div className="mb-6 p-4 rounded-2xl bg-rose-50 dark:bg-rose-950/70 border border-rose-200 dark:border-rose-900 text-rose-800 dark:text-rose-300 text-xs sm:text-sm flex items-start justify-between gap-3 shadow-sm animate-fade-in">
            <div className="flex items-start gap-2.5">
              <AlertCircle className="w-5 h-5 shrink-0 text-rose-600 dark:text-rose-400 mt-0.5" />
              <span>{errorBanner}</span>
            </div>
            <button
              onClick={() => setErrorBanner(null)}
              className="font-bold text-rose-600 hover:text-rose-800 dark:hover:text-rose-200"
            >
              ×
            </button>
          </div>
        )}

        {/* Success Alert */}
        {successBanner && (
          <div className="mb-6 p-4 rounded-2xl bg-emerald-50 dark:bg-emerald-950/70 border border-emerald-200 dark:border-emerald-900 text-emerald-800 dark:text-emerald-300 text-xs sm:text-sm flex items-start justify-between gap-3 shadow-sm animate-fade-in">
            <div className="flex items-start gap-2.5">
              <CheckCircle2 className="w-5 h-5 shrink-0 text-emerald-600 dark:text-emerald-400 mt-0.5" />
              <span>{successBanner}</span>
            </div>
            <button
              onClick={() => setSuccessBanner(null)}
              className="font-bold text-emerald-600 hover:text-emerald-800 dark:hover:text-emerald-200"
            >
              ×
            </button>
          </div>
        )}

        {activeTab === "verifier" ? (
          <div className="space-y-6">
            <Hero />

            {/* Email Input Form */}
            <EmailInputForm
              onVerify={handleVerify}
              isLoading={isVerifying}
              verifyingStep={verifyingStep}
            />

            {/* Summary Cards (Only displayed when currentBatch or records exist) */}
            {records.length > 0 && (
              <>
                <SummaryCards
                  total={currentBatch?.total_count ?? records.length}
                  delivered={
                    currentBatch?.delivered_count ??
                    records.filter((r) => r.status === "Likely to be delivered").length
                  }
                  bounce={
                    currentBatch?.bounce_count ??
                    records.filter((r) => r.status === "Likely to bounce").length
                  }
                  unknown={
                    currentBatch?.unknown_count ??
                    records.filter((r) => r.status === "Unknown").length
                  }
                  activeFilter={activeFilter}
                  onFilterChange={setActiveFilter}
                />

                {/* Searchable and Filterable Results Table */}
                <ResultsTable
                  records={records}
                  batchId={currentBatch?.id}
                  activeFilter={activeFilter}
                  onFilterChange={setActiveFilter}
                  onInspect={(record) => setInspectingRecord(record)}
                  onDeleteRecord={handleDeleteRecord}
                />
              </>
            )}

            {/* Privacy & Disclosures */}
            <PrivacyNotice />
          </div>
        ) : (
          <div className="space-y-6">
            <HistoryView
              batches={batchesHistory}
              loading={historyLoading}
              onOpenBatch={handleOpenBatch}
              onDeleteBatch={handleDeleteBatch}
              onClearHistory={handleClearHistory}
            />

            <PrivacyNotice />
          </div>
        )}
      </main>

      {/* Diagnostics Inspect Modal */}
      <InspectModal
        record={inspectingRecord}
        onClose={() => setInspectingRecord(null)}
      />

      {/* Confirmation Modal */}
      <ConfirmDialog
        isOpen={confirmDialog.isOpen}
        title={confirmDialog.title}
        message={confirmDialog.message}
        onConfirm={confirmDialog.onConfirm}
        onCancel={() => setConfirmDialog((prev) => ({ ...prev, isOpen: false }))}
      />
    </div>
  );
};

export default App;
