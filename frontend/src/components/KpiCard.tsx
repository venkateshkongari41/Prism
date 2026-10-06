interface KpiCardProps {
  label: string;
  value: string;
  helper?: string;
}

export default function KpiCard({ label, value, helper }: KpiCardProps) {
  return (
    <section className="rounded-2xl border border-slate-800 bg-slate-900/80 p-5 shadow-xl shadow-black/10">
      <p className="text-sm font-medium text-slate-400">{label}</p>
      <p className="mt-3 text-3xl font-semibold tracking-tight text-white">
        {value}
      </p>
      {helper ? (
        <p className="mt-2 text-xs text-slate-500">{helper}</p>
      ) : null}
    </section>
  );
}
