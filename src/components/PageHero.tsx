import type { LucideIcon } from "lucide-react";
import type { ReactNode } from "react";

type Stat = { label: string; value: ReactNode };

export function PageHero({ icon: Icon, eyebrow, title, accent, subtitle, stats, narrow }: {
  icon: LucideIcon; eyebrow: string; title: string; accent: string; subtitle: string; stats?: Stat[]; narrow?: boolean;
}) {
  return (
    <section className="page-hero">
      <div className={`relative z-10 mx-auto px-6 py-12 ${narrow ? "max-w-3xl" : "max-w-6xl"}`}>
        <span className="page-eyebrow"><Icon className="h-3.5 w-3.5" />{eyebrow}</span>
        <h1 className="mt-5 font-display text-4xl font-bold tracking-tight sm:text-5xl">
          {title} <span className="page-serif">{accent}</span>
        </h1>
        <p className="mt-4 max-w-2xl text-sm text-muted-foreground sm:text-base">{subtitle}</p>
        {stats && stats.length > 0 && (
          <div className="mt-6 flex flex-wrap gap-3">
            {stats.map((s) => (
              <div key={s.label} className="page-stat">
                <div className="text-[11px] font-medium uppercase tracking-wider text-muted-foreground">{s.label}</div>
                <div className="mt-0.5 font-display text-lg font-semibold tabular-nums">{s.value}</div>
              </div>
            ))}
          </div>
        )}
      </div>
    </section>
  );
}
