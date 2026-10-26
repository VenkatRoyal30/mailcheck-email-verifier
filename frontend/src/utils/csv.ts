import { EmailVerificationRecord } from "../types";

export function exportRecordsToCsv(records: EmailVerificationRecord[], batchId?: string): void {
  if (!records || records.length === 0) return;

  const headers = [
    "Email Address",
    "Classification Status",
    "Reason",
    "Normalized Address",
    "Syntax Valid",
    "Mail Exchange (MX) Host",
    "SMTP Probed",
    "Verified At",
    "Batch ID",
  ];

  const rows = records.map((r) => {
    let mxHost = "N/A";
    if (r.dns_diagnostic?.mx_records && r.dns_diagnostic.mx_records.length > 0) {
      mxHost = r.dns_diagnostic.mx_records[0].exchange;
    } else if (r.dns_diagnostic?.fallback_records && r.dns_diagnostic.fallback_records.length > 0) {
      mxHost = `Fallback:${r.dns_diagnostic.fallback_records[0].address}`;
    }

    return [
      `"${(r.original_email || "").replace(/"/g, '""')}"`,
      `"${(r.status || "").replace(/"/g, '""')}"`,
      `"${(r.reason || "").replace(/"/g, '""')}"`,
      `"${(r.normalized_email || "").replace(/"/g, '""')}"`,
      r.syntax_diagnostic?.valid ? "Yes" : "No",
      `"${mxHost.replace(/"/g, '""')}"`,
      r.smtp_skipped ? "No" : "Yes",
      `"${r.created_at || ""}"`,
      `"${batchId || r.batch_id || ""}"`,
    ].join(",");
  });

  const csvContent = "data:text/csv;charset=utf-8," + [headers.join(","), ...rows].join("\n");
  const encodedUri = encodeURI(csvContent);
  const link = document.createElement("a");
  link.setAttribute("href", encodedUri);
  link.setAttribute("download", `mailcheck_export_${batchId ? batchId.slice(0, 8) : "results"}_${Date.now()}.csv`);
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}
