import { Link } from "@tanstack/react-router";
import { BarChart3, BookOpen, LayoutDashboard, Leaf, Menu, Users } from "lucide-react";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetTrigger } from "@/components/ui/sheet";

const NAV = [
  { to: "/", label: "Overview", exact: true, icon: LayoutDashboard },
  { to: "/customers", label: "Customers", exact: false, icon: Users },
  { to: "/insights", label: "Business Insights", exact: false, icon: BarChart3 },
  { to: "/methodology", label: "Methodology", exact: false, icon: BookOpen },
] as const;

const linkBase = "rounded-md px-3 py-2 text-sm font-semibold transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-bank-ink";

export function BankHeader() {
  const [open, setOpen] = useState(false);
  return (
    <>
      <header className="nav-shell">
        <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-6 py-3">
          <Link to="/" className="group flex items-center gap-3.5" aria-label="Green Insights overview">
            <span className="nav-logo-chip"><Leaf className="h-6 w-6 text-bank-green" /></span>
            <span className="hidden sm:block h-9 w-px bg-bank-on-hero/20" aria-hidden="true" />
            <span className="hidden sm:block font-display text-base font-bold leading-none">Green <span className="page-serif !bg-none !p-0 text-bank-green">Insights</span><span className="nav-brand-sub mt-1 block text-[10px] font-medium uppercase tracking-[0.18em]">Customer intelligence</span></span>
          </Link>
          <nav className="nav-pill-track hidden md:flex" aria-label="Main navigation">
            {NAV.map((n) => (
              <Link key={n.to} to={n.to} activeOptions={{ exact: n.exact }} className="nav-pill" activeProps={{ "aria-current": "page" }}>
                <n.icon className="h-3.5 w-3.5" />{n.label}
              </Link>
            ))}
          </nav>
          <Sheet open={open} onOpenChange={setOpen}>
            <SheetTrigger asChild>
              <Button variant="ghost" size="icon" className="text-bank-on-hero hover:bg-bank-on-hero/10 md:hidden" aria-label="Open menu">
                <Menu className="h-6 w-6" />
              </Button>
            </SheetTrigger>
            <SheetContent side="right" className="w-64">
              <SheetHeader><SheetTitle>Green Insights</SheetTitle></SheetHeader>
              <nav className="mt-4 flex flex-col gap-1 px-4" aria-label="Mobile navigation">
                {NAV.map((n) => (
                  <Link
                    key={n.to}
                    to={n.to}
                    activeOptions={{ exact: n.exact }}
                    onClick={() => setOpen(false)}
                    className={`${linkBase} hover:bg-accent`}
                    activeProps={{ className: "bg-primary text-primary-foreground hover:bg-primary", "aria-current": "page" }}
                  >
                    <n.icon className="mr-2 inline h-4 w-4" />{n.label}
                  </Link>
                ))}
              </nav>
            </SheetContent>
          </Sheet>
        </div>
      </header>
    </>
  );
}
