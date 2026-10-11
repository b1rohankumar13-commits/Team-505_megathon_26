import { Link } from "@tanstack/react-router";
import { ArrowRight, ArrowUpRight, Leaf, ShieldCheck, Activity } from "lucide-react";
import { Button } from "@/components/ui/button";
import forest from "@/assets/emerald-forest.jpg";
import { fmtNum, fmtPct } from "@/lib/format";

export function EditorialHero({ co2eKg, digitalAdoption }: { co2eKg: number | null; digitalAdoption: number | null }) {
  const metrics = [
    { value: "Model-led", label: "Customer Propensity" },
    { value: co2eKg === null ? "Unavailable" : fmtNum(co2eKg / 1000, "t CO₂e", 1), label: "Avoided Emissions", note: "Potential · per year" },
    { value: "Evidence-led", label: "Reason Codes" },
    { value: fmtPct(digitalAdoption), label: "Digital Adoption" },
  ];
  return (
    <section className="editorial-hero" aria-label="Green Customer Insights Platform">
      <div className="editorial-grid mx-auto max-w-6xl px-6">
        <div className="editorial-copy">
          <div className="editorial-eyebrow inline-flex items-center gap-2.5 rounded-full border px-3 py-2 text-[10px] font-semibold sm:text-xs">
            <Leaf className="h-4 w-4 shrink-0 text-primary" />
            <span className="opacity-50">•</span>
            <span>Sustainability Engine</span>
          </div>
          <p className="mt-6 text-[11px] font-semibold uppercase tracking-widest text-primary">Green Customer Insights Platform</p>
          <h1 className="editorial-title mt-4">Every transaction<br className="hidden sm:block" /> tells a <em className="editorial-word">greener</em><br className="hidden sm:block" /> story.</h1>
          <p className="mt-6 max-w-md text-base leading-relaxed text-muted-foreground">Transform retail transaction signals into estimated sustainability impact and intelligent green banking opportunities.</p>
          <div className="mt-8 flex flex-wrap gap-3">
            <Button asChild size="lg" className="editorial-primary h-12 gap-3 px-5 text-xs font-semibold"><Link to="/customers">Explore Opportunities <ArrowRight className="h-4 w-4" /></Link></Button>
            <Button asChild variant="outline" size="lg" className="editorial-secondary h-12 gap-2 px-5 text-xs font-semibold"><Link to="/methodology">View Carbon Methodology <ArrowUpRight className="h-4 w-4" /></Link></Button>
          </div>
          <div className="editorial-metrics mt-10 grid grid-cols-2 gap-x-4 gap-y-6 border-t pt-6 sm:grid-cols-4">
            {metrics.map((metric) => <div key={metric.label} className="min-w-0"><p className="whitespace-nowrap text-lg font-semibold sm:text-sm">{metric.value}</p><p className="mt-1 text-[10px] text-muted-foreground">{metric.label}</p>{metric.note && <p className="mt-1 text-[9px] text-muted-foreground">{metric.note}</p>}</div>)}
          </div>
        </div>
        <div className="editorial-visual">
          <div className="editorial-arch"><img src={forest} alt="Aerial view of emerald pine trees with morning mist drifting through the forest" width={1024} height={1536} className="h-full w-full object-cover" /><div className="editorial-image-caption"><Leaf className="h-4 w-4" /><span>A greener future, rooted in insight.</span></div></div>
          <span className="editorial-image-index text-[9px] uppercase tracking-widest text-muted-foreground">01 / Nature meets intelligence</span>
        </div>
      </div>
    </section>
  );
}
