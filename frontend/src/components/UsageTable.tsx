import type { UsageItem } from "../types";

interface UsageTableProps {
  items: UsageItem[];
}

function formatDate(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString();
}

function cacheLabel(cacheType: UsageItem["cache_type"]): string {
  if (cacheType === "exact") return "Exact";
  if (cacheType === "semantic") return "Semantic";
  if (cacheType === "miss") return "Miss";
  return "—";
}

export default function UsageTable({ items }: UsageTableProps) {
  return (
    <div className="overflow-hidden rounded-2xl border border-slate-800 bg-slate-900/80">
      <div className="overflow-x-auto">
        <table className="min-w-full text-left text-sm">
          <thead className="border-b border-slate-800 bg-slate-950/70">
            <tr>
              {[
                "Time",
                "Model",
                "Provider",
                "Status",
                "Cache",
                "Tokens",
                "Cost",
                "Latency",
                "Fallback",
              ].map((header) => (
                <th
                  key={header}
                  className="whitespace-nowrap px-4 py-3 font-medium text-slate-400"
                >
                  {header}
                </th>
              ))}
            </tr>
          </thead>

          <tbody>
            {items.map((item) => (
              <tr
                key={`${item.id}-${item.request_id ?? "request"}`}
                className="border-b border-slate-800/70 last:border-b-0"
              >
                <td className="whitespace-nowrap px-4 py-3 text-slate-300">
                  {formatDate(item.created_at)}
                </td>
                <td className="px-4 py-3 font-medium text-white">
                  {item.model ?? "—"}
                </td>
                <td className="px-4 py-3 text-slate-300">
                  {item.provider ?? "—"}
                </td>
                <td className="px-4 py-3">
                  <span
                    className={[
                      "rounded-full px-2.5 py-1 text-xs font-medium",
                      item.status === "success"
                        ? "bg-emerald-400/10 text-emerald-300"
                        : "bg-rose-400/10 text-rose-300",
                    ].join(" ")}
                  >
                    {item.status}
                  </span>
                </td>
                <td className="px-4 py-3 text-slate-300">
                  {cacheLabel(item.cache_type)}
                </td>
                <td className="px-4 py-3 text-slate-300">
                  {item.total_tokens ?? 0}
                </td>
                <td className="px-4 py-3 text-slate-300">
                  ${(item.cost ?? 0).toFixed(4)}
                </td>
                <td className="px-4 py-3 text-slate-300">
                  {item.latency_ms == null
                    ? "—"
                    : `${Math.round(item.latency_ms)} ms`}
                </td>
                <td className="px-4 py-3 text-slate-300">
                  {item.fallback_used ? "Yes" : "No"}
                </td>
              </tr>
            ))}

            {items.length === 0 ? (
              <tr>
                <td
                  colSpan={9}
                  className="px-4 py-10 text-center text-slate-500"
                >
                  No usage records found for this application.
                </td>
              </tr>
            ) : null}
          </tbody>
        </table>
      </div>
    </div>
  );
}
