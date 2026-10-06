import { useCallback, useEffect, useMemo, useState } from "react";
import KpiCard from "./components/KpiCard";
import UsageTable from "./components/UsageTable";
import { fetchUsage, fetchUsageSummary } from "./lib/api";
import type { UsageResponse, UsageSummary } from "./types";

const STORAGE_KEY = "prism.ops.apiKey";

function formatCurrency(value: number): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: 4,
    maximumFractionDigits: 4,
  }).format(value);
}

function formatPercent(value: number): string {
  return `${(value * 100).toFixed(1)}%`;
}

export default function App() {
  const [apiKey, setApiKey] = useState(
    () => localStorage.getItem(STORAGE_KEY) ?? "",
  );
  const [draftKey, setDraftKey] = useState(apiKey);
  const [hours, setHours] = useState(24);
  const [summary, setSummary] = useState<UsageSummary | null>(null);
  const [applicationName, setApplicationName] = useState("—");
  const [usage, setUsage] = useState<UsageResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const loadDashboard = useCallback(async () => {
    if (!apiKey.trim()) {
      setSummary(null);
      setUsage(null);
      setError("Enter a Prism virtual API key to load the dashboard.");
      return;
    }

    setLoading(true);
    setError("");

    try {
      const [summaryResponse, usageResponse] = await Promise.all([
        fetchUsageSummary(apiKey.trim(), hours),
        fetchUsage(apiKey.trim(), 100, hours),
      ]);

      setSummary(summaryResponse.summary);
      setApplicationName(summaryResponse.application);
      setUsage(usageResponse);
      localStorage.setItem(STORAGE_KEY, apiKey.trim());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load dashboard.");
      setSummary(null);
      setUsage(null);
    } finally {
      setLoading(false);
    }
  }, [apiKey, hours]);

  useEffect(() => {
    if (apiKey) {
      void loadDashboard();
    }
  }, [apiKey, loadDashboard]);

  const displayApplicationName = applicationName !== "—" ? applicationName : usage?.application ?? "—";
  const items = usage?.items ?? [];

  const successfulRate = useMemo(() => {
    if (!summary || summary.total_requests === 0) return 0;
    return summary.successful_requests / summary.total_requests;
  }, [summary]);

  function connect(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const nextKey = draftKey.trim();

    if (!nextKey) {
      setError("Enter an API key first.");
      return;
    }

    setApiKey(nextKey);
  }

  function clearKey() {
    localStorage.removeItem(STORAGE_KEY);
    setApiKey("");
    setDraftKey("");
    setSummary(null);
    setUsage(null);
    setApplicationName("—");
    setError("");
  }

  return (
    <div className="min-h-screen text-slate-100">
      <header className="border-b border-slate-800/80 bg-slate-950/80 backdrop-blur">
        <div className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-6 py-5">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.22em] text-sky-400">
              Prism
            </p>
            <h1 className="mt-1 text-xl font-semibold text-white">
              Operations Console
            </h1>
          </div>

          <div className="hidden items-center gap-2 text-xs text-slate-500 md:flex">
            <span className="h-2 w-2 rounded-full bg-emerald-400" />
            Gateway dashboard
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-7xl px-6 py-8">
        <section className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5 shadow-xl shadow-black/10">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
            <form
              onSubmit={connect}
              className="flex w-full flex-col gap-3 lg:max-w-3xl lg:flex-row"
            >
              <div className="flex-1">
                <label
                  htmlFor="api-key"
                  className="mb-2 block text-sm font-medium text-slate-300"
                >
                  Prism virtual API key
                </label>
                <input
                  id="api-key"
                  type="password"
                  value={draftKey}
                  onChange={(event) => setDraftKey(event.target.value)}
                  placeholder="Enter the seeded/demo key"
                  className="w-full rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 text-sm text-white outline-none transition focus:border-sky-500"
                />
              </div>

              <button
                type="submit"
                className="rounded-xl bg-sky-500 px-5 py-3 text-sm font-semibold text-slate-950 transition hover:bg-sky-400 lg:self-end"
              >
                {loading ? "Loading..." : "Load dashboard"}
              </button>

              {apiKey ? (
                <button
                  type="button"
                  onClick={clearKey}
                  className="rounded-xl border border-slate-700 px-5 py-3 text-sm font-medium text-slate-300 transition hover:border-slate-500 hover:text-white lg:self-end"
                >
                  Clear
                </button>
              ) : null}
            </form>

            <div className="flex items-center gap-2">
              <label
                htmlFor="range"
                className="text-sm text-slate-400"
              >
                Window
              </label>
              <select
                id="range"
                value={hours}
                onChange={(event) => setHours(Number(event.target.value))}
                className="rounded-xl border border-slate-700 bg-slate-950 px-3 py-3 text-sm text-slate-200 outline-none"
              >
                <option value={1}>Last hour</option>
                <option value={24}>Last 24 hours</option>
                <option value={168}>Last 7 days</option>
                <option value={720}>Last 30 days</option>
              </select>
            </div>
          </div>

          {error ? (
            <div className="mt-4 rounded-xl border border-rose-900/60 bg-rose-950/40 px-4 py-3 text-sm text-rose-300">
              {error}
            </div>
          ) : null}
        </section>

        <div className="mt-6 flex flex-col gap-1">
          <p className="text-sm text-slate-500">Application</p>
          <p className="text-lg font-semibold text-white">{displayApplicationName}</p>
        </div>

        {summary ? (
          <>
            <section className="mt-5 grid gap-4 sm:grid-cols-2 xl:grid-cols-5">
              <KpiCard
                label="Requests"
                value={summary.total_requests.toLocaleString()}
                helper={`${summary.successful_requests} successful`}
              />
              <KpiCard
                label="Total cost"
                value={formatCurrency(summary.total_cost)}
                helper={`${summary.total_tokens.toLocaleString()} tokens`}
              />
              <KpiCard
                label="Cache hit rate"
                value={formatPercent(summary.cache_hit_rate)}
                helper={`${summary.cache_hits} hits / ${summary.cache_misses} misses`}
              />
              <KpiCard
                label="Fallbacks"
                value={summary.fallback_requests.toLocaleString()}
                helper="Provider fallback requests"
              />
              <KpiCard
                label="Avg latency"
                value={`${Math.round(summary.average_latency_ms)} ms`}
                helper={`${formatPercent(successfulRate)} success rate`}
              />
            </section>

            <section className="mt-6 grid gap-6 lg:grid-cols-[1.35fr_1fr]">
              <div>
                <div className="mb-3 flex items-center justify-between">
                  <div>
                    <h2 className="text-lg font-semibold text-white">
                      Recent requests
                    </h2>
                    <p className="text-sm text-slate-500">
                      Latest 100 request-level usage records
                    </p>
                  </div>
                  <button
                    type="button"
                    onClick={() => void loadDashboard()}
                    className="rounded-lg border border-slate-700 px-3 py-2 text-xs font-medium text-slate-300 hover:border-slate-500 hover:text-white"
                  >
                    Refresh
                  </button>
                </div>
                <UsageTable items={items} />
              </div>

              <aside className="h-fit rounded-2xl border border-slate-800 bg-slate-900/80 p-5">
                <h2 className="text-lg font-semibold text-white">
                  Cache & routing
                </h2>
                <div className="mt-5 space-y-4">
                  <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-4">
                    <p className="text-xs uppercase tracking-wide text-slate-500">
                      Exact cache hits
                    </p>
                    <p className="mt-1 text-2xl font-semibold text-white">
                      {summary.cache_hits}
                    </p>
                  </div>
                  <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-4">
                    <p className="text-xs uppercase tracking-wide text-slate-500">
                      Semantic + exact hit rate
                    </p>
                    <p className="mt-1 text-2xl font-semibold text-white">
                      {formatPercent(summary.cache_hit_rate)}
                    </p>
                  </div>
                  <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-4">
                    <p className="text-xs uppercase tracking-wide text-slate-500">
                      Completion tokens
                    </p>
                    <p className="mt-1 text-2xl font-semibold text-white">
                      {summary.total_completion_tokens.toLocaleString()}
                    </p>
                  </div>
                </div>
              </aside>
            </section>
          </>
        ) : (
          <section className="mt-6 rounded-2xl border border-dashed border-slate-800 bg-slate-900/40 px-6 py-16 text-center">
            <p className="text-lg font-semibold text-white">
              Connect the dashboard
            </p>
            <p className="mx-auto mt-2 max-w-xl text-sm leading-6 text-slate-500">
              Enter a Prism virtual API key above. The console reads only the
              usage records associated with that authenticated application.
            </p>
          </section>
        )}
      </main>
    </div>
  );
}
