import { Link } from "@tanstack/react-router";
import { ArrowUpRight, Leaf, ShieldCheck } from "lucide-react";
import { Button } from "@/components/ui/button";

export function BankHeader({ customer = false }: { customer?: boolean }) {
  return (
    <>
      <div className="bg-bank-ink text-bank-on-ink">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-2 text-[11px]">
          <span>Lloyds-inspired · Megathon prototype</span>
          <span className="flex items-center gap-1.5"><ShieldCheck className="h-3 w-3" /> Synthetic data only</span>
        </div>
      </div>
      <header className="bg-bank-green text-bank-ink">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-4 px-6 py-5">
          <Link to="/" className="flex items-center gap-2.5" aria-label="Green Insights dashboard">
            <Leaf className="h-8 w-8" strokeWidth={2.5} />
            <span className="font-display text-xl font-extrabold">GREEN INSIGHTS<span className="block text-[10px] font-medium uppercase tracking-widest">Customer intelligence</span></span>
          </Link>
          <nav className="flex items-center gap-1" aria-label="Main navigation">
            <Button asChild variant="ghost" className="text-bank-ink hover:bg-bank-ink/10"><Link to="/">Overview</Link></Button>
            {!customer && <Button asChild variant="ghost" className="text-bank-ink hover:bg-bank-ink/10"><a href="#customers">Customers <ArrowUpRight className="h-4 w-4" /></a></Button>}
          </nav>
        </div>
      </header>
    </>
  );
}