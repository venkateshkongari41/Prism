import type { SummaryResponse, UsageResponse } from "../types";

const API_BASE = "";

function authHeaders(apiKey: string): HeadersInit {
  return {
    Authorization: `Bearer ${apiKey}`,
    "Content-Type": "application/json",
  };
}

async function parseJson<T>(response: Response): Promise<T> {
  const body = await response.json().catch(() => ({}));

  if (!response.ok) {
    const detail =
      typeof body?.detail === "string"
        ? body.detail
        : `Request failed with status ${response.status}`;

    throw new Error(detail);
  }

  return body as T;
}

export async function fetchUsage(
  apiKey: string,
  limit = 100,
  hours?: number,
): Promise<UsageResponse> {
  const params = new URLSearchParams({
    limit: String(limit),
  });

  if (hours !== undefined) {
    params.set("hours", String(hours));
  }

  const response = await fetch(
    `${API_BASE}/v1/usage?${params.toString()}`,
    {
      headers: authHeaders(apiKey),
    },
  );

  return parseJson<UsageResponse>(response);
}

export async function fetchUsageSummary(
  apiKey: string,
  hours?: number,
): Promise<SummaryResponse> {
  const params = new URLSearchParams();

  if (hours !== undefined) {
    params.set("hours", String(hours));
  }

  const query = params.toString();

  const response = await fetch(
    `${API_BASE}/v1/usage/summary${query ? `?${query}` : ""}`,
    {
      headers: authHeaders(apiKey),
    },
  );

  return parseJson<SummaryResponse>(response);
}
