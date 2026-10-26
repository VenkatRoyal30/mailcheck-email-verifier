export type VerificationStatus =
  | "Likely to be delivered"
  | "Likely to bounce"
  | "Unknown";

export interface SyntaxDiagnostic {
  valid: boolean;
  original: string;
  normalized: string | null;
  local_part: string | null;
  domain: string | null;
  error_message: string | null;
  details?: Record<string, any>;
}

export interface MxRecord {
  preference: number;
  exchange: string;
}

export interface FallbackRecord {
  type: string;
  address: string;
}

export interface DnsDiagnostic {
  status: string;
  reason: string;
  has_mx?: boolean;
  is_null_mx?: boolean;
  has_fallback?: boolean;
  mx_records?: MxRecord[];
  fallback_records?: FallbackRecord[];
  ttl?: number | null;
  dns_error_type?: string | null;
}

export interface SmtpDiagnostic {
  probed: boolean;
  status: string;
  message: string;
  code?: number | null;
  is_catch_all?: boolean;
  port_blocked?: boolean;
  failure_type?: string | null;
}

export interface EmailVerificationRecord {
  id: string;
  batch_id: string;
  original_email: string;
  normalized_email: string | null;
  status: VerificationStatus;
  reason: string;
  syntax_diagnostic: SyntaxDiagnostic;
  dns_diagnostic: DnsDiagnostic;
  smtp_diagnostic: SmtpDiagnostic;
  smtp_skipped: boolean;
  created_at: string;
  is_duplicate?: boolean;
}

export interface VerificationBatch {
  id: string;
  created_at: string;
  total_count: number;
  delivered_count: number;
  bounce_count: number;
  unknown_count: number;
  smtp_enabled: boolean;
  records?: EmailVerificationRecord[];
}

export interface HealthStatus {
  status: "healthy" | "degraded" | "offline";
  service: string;
  version: string;
  database: string;
  timestamp: string;
}

export type StatusFilter = "ALL" | VerificationStatus;

