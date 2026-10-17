import { createFileRoute } from "@tanstack/react-router";
import { useSuspenseQuery } from "@tanstack/react-query";
import { BankHeader } from "@/components/BankHeader";
import { PageHero } from "@/components/PageHero";
import { BookOpen } from "lucide-react";
import { DemoBanner, LoadingState, RouteError } from "@/components/DataState";
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import { methodologyQuery } from "@/lib/api/client";

export const Route = createFileRoute("/methodology")({
  head: () => ({
    meta: [
      { title: "Methodology — Green Customer Insights" },
      { name: "description", content: "Data provenance, model splits, confidence, carbon formulas, LLM grounding, evaluation and responsible-AI approach." },
      { property: "og:title", content: "Methodology — Green Customer Insights" },
      { property: "og:description", content: "How green opportunities, confidence and impact estimates are produced." },
      { property: "og:type", content: "article" },
      { name: "twitter:card", content: "summary" },
    ],
  }),
  loader: ({ context }) => context.queryClient.ensureQueryData(methodologyQuery),
  pendingComponent: () => (<><BankHeader /><LoadingState label="Loading methodology…" /></>),
  errorComponent: ({ error }) => (<><BankHeader /><RouteError error={error as Error} /></>),
  component: MethodologyPage,
});

function MethodologyPage() {
  const { data: res } = useSuspenseQuery(methodologyQuery);
  return (
    <div className="min-h-screen bg-background">
      <BankHeader />
      <DemoBanner source={res.source} />
      <PageHero narrow icon={BookOpen} eyebrow="Transparent by default" title="How the engine" accent="thinks" subtitle="Results are shown only when supplied by evaluation reports or backend metadata. No scores are invented."
        stats={[{ label: "Sections", value: res.data.sections.length }, { label: "ML predicts", value: "Model" }, { label: "LLM", value: "Explains only" }]} />
      <main className="mx-auto max-w-3xl px-6 py-8">
        <Accordion type="multiple" defaultValue={[res.data.sections[0]?.id ?? ""]} className="lux-card px-5 pt-1">
          {res.data.sections.map((s) => (
            <AccordionItem key={s.id} value={s.id}>
              <AccordionTrigger className="text-sm font-semibold">{s.title}</AccordionTrigger>
              <AccordionContent>
                <ul className="list-disc space-y-1 pl-5 text-sm text-muted-foreground">{s.points.map((p) => <li key={p}>{p}</li>)}</ul>
                {s.metrics !== null && (
                  s.metrics.length === 0 ? (
                    <p className="mt-3 rounded-md border border-dashed p-3 text-xs text-muted-foreground">No evaluation metrics have been supplied yet.</p>
                  ) : (
                    <table className="mt-3 w-full text-sm">
                      <thead className="text-left text-xs text-muted-foreground"><tr><th className="pb-1 font-medium">Metric</th><th className="pb-1 font-medium">Model</th><th className="pb-1 font-medium">Baseline</th></tr></thead>
                      <tbody>{s.metrics.map((m) => <tr key={m.name} className="border-t"><td className="py-1.5">{m.name}</td><td className="py-1.5 tabular-nums">{m.value}</td><td className="py-1.5 tabular-nums">{m.baseline ?? "—"}</td></tr>)}</tbody>
                    </table>
                  )
                )}
              </AccordionContent>
            </AccordionItem>
          ))}
        </Accordion>
      </main>
    </div>
  );
}
