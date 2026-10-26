import {
  VerificationBatch,
  HealthStatus,
} from "../types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "/api";

export class ApiError extends Error {
  status?: number;
  details?: any;

  constructor(message: string, status?: number, details?: any) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.details = details;
  }
}

async function handleResponse<T>(response: Response): Promise<T> {
  const contentType = response.headers.get("content-type");
  let body: any = null;

  if (contentType && contentType.includes("application/json")) {
    body = await response.json();
  } else {
    body = await response.text();
  }

  if (!response.ok) {
    const errorMsg =
      body?.error || body?.details || body?.message || (typeof body === "string" ? body : "An unexpected server error occurred.");
    throw new ApiError(errorMsg, response.status, body);
  }

  return body as T;
}

export const apiClient = {
  async getHealth(): Promise<HealthStatus> {
    try {
      const res = await fetch(`${API_BASE_URL}/health`, {
        headers: { Accept: "application/json" },
      });
      return await handleResponse<HealthStatus>(res);
    } catch (err: any) {
      if (err instanceof ApiError) throw err;
      throw new ApiError("Unable to reach MailCheck backend API. Check if server is running.", 0, err);
    }
  },

  async verifyEmails(emails: string[], enableSmtp: boolean = false): Promise<VerificationBatch> {
    const res = await fetch(`${API_BASE_URL}/verify`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
      },
      body: JSON.stringify({
        emails,
        enable_smtp: enableSmtp,
      }),
    });
    return await handleResponse<VerificationBatch>(res);
  },

  async getHistory(): Promise<{ count: number; batches: VerificationBatch[] }> {
    const res = await fetch(`${API_BASE_URL}/history`, {
      headers: { Accept: "application/json" },
    });
    return await handleResponse<{ count: number; batches: VerificationBatch[] }>(res);
  },

  async getBatch(batchId: string): Promise<VerificationBatch> {
    const res = await fetch(`${API_BASE_URL}/history/${encodeURIComponent(batchId)}`, {
      headers: { Accept: "application/json" },
    });
    return await handleResponse<VerificationBatch>(res);
  },

  async deleteBatch(batchId: string): Promise<{ message: string }> {
    const res = await fetch(`${API_BASE_URL}/history/${encodeURIComponent(batchId)}`, {
      method: "DELETE",
      headers: { Accept: "application/json" },
    });
    return await handleResponse<{ message: string }>(res);
  },

  async deleteRecord(batchId: string, recordId: string): Promise<{ message: string; batch: VerificationBatch }> {
    const res = await fetch(
      `${API_BASE_URL}/history/${encodeURIComponent(batchId)}/records/${encodeURIComponent(recordId)}`,
      {
        method: "DELETE",
        headers: { Accept: "application/json" },
      }
    );
    return await handleResponse<{ message: string; batch: VerificationBatch }>(res);
  },

  async clearHistory(): Promise<{ message: string }> {
    const res = await fetch(`${API_BASE_URL}/history`, {
      method: "DELETE",
      headers: { Accept: "application/json" },
    });
    return await handleResponse<{ message: string }>(res);
  },

  getExportCsvUrl(batchId: string): string {
    return `${API_BASE_URL}/history/${encodeURIComponent(batchId)}/export`;
  },
};

