"use client";
import React, { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard, Database, FileSearch, MapPin, Shield, Brain,
  Activity, ChevronLeft, ChevronRight, BarChart3,
  Upload, Radio, Search, Layers, Zap, Globe
} from "lucide-react";
import { ThemeToggle } from "@/components/ThemeToggle";

const NAV_SECTIONS = [
  {
    label: "Dataset Intelligence",
    badge: "DATASET",
    badgeColor: "bg-emerald-500/15 text-emerald-500 border-emerald-500/20",
    items: [
      { href: "/", label: "Overview", icon: LayoutDashboard },
      { href: "/awareness-gaps", label: "Awareness Gap Analysis", icon: Search },
      { href: "/geography", label: "Geographic Gap Analysis", icon: MapPin },
      { href: "/schemes", label: "Scheme Analysis", icon: Shield },
      { href: "/intents", label: "Intent & Gap Types", icon: Layers },
      { href: "/explorer", label: "Dataset Explorer", icon: Database },
      { href: "/upload", label: "Upload Dataset", icon: Upload },
    ],
  },
  {
    label: "Live Scraping Intelligence",
    badge: "LIVE",
    badgeColor: "bg-red-500/15 text-red-400 border-red-500/20",
    items: [
      { href: "/live", label: "Live Dashboard", icon: Radio },
      { href: "/live/sources", label: "Source Registry", icon: Globe },
      { href: "/live/stream", label: "Live Question Stream", icon: Zap },
      { href: "/live/campaigns", label: "Campaigns", icon: Activity },
    ],
  },
];

export default function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const [collapsed, setCollapsed] = useState(false);

  // Determine if we're in live or dataset workspace
  const isLive = pathname.startsWith("/live");

  return (
    <div className="flex h-screen overflow-hidden">
      {/* Sidebar */}
      <aside
        className={`${
          collapsed ? "w-16" : "w-64"
        } flex flex-col border-r border-border/40 bg-sidebar transition-all duration-200 ease-in-out shrink-0`}
      >
        {/* Logo */}
        <div className="flex items-center gap-3 px-4 h-14 border-b border-border/30">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-amber-500 to-orange-600 flex items-center justify-center shrink-0">
            <BarChart3 className="w-4 h-4 text-white" />
          </div>
          {!collapsed && (
            <div className="overflow-hidden">
              <h1 className="text-sm font-semibold text-foreground truncate leading-tight">
                Gap Miner
              </h1>
              <p className="text-[10px] text-muted-foreground truncate leading-tight">
                Welfare Scheme Analytics
              </p>
            </div>
          )}
        </div>

        {/* Navigation */}
        <nav className="flex-1 overflow-y-auto py-3 px-2 space-y-5">
          {NAV_SECTIONS.map((section) => (
            <div key={section.label}>
              {!collapsed && (
                <div className="flex items-center gap-2 px-2 mb-1.5">
                  <p className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground/60">
                    {section.label}
                  </p>
                  <span className={`text-[8px] font-bold px-1.5 py-0.5 rounded-full border ${section.badgeColor}`}>
                    {section.badge}
                  </span>
                </div>
              )}
              <ul className="space-y-0.5">
                {section.items.map((item) => {
                  const active = pathname === item.href;
                  const Icon = item.icon;
                  return (
                    <li key={item.href}>
                      <Link
                        href={item.href}
                        className={`flex items-center gap-2.5 px-2.5 py-2 rounded-lg text-sm transition-all duration-150 ${
                          active
                            ? "bg-amber-500/15 text-amber-500 font-medium"
                            : "text-muted-foreground hover:bg-sidebar-accent hover:text-foreground"
                        }`}
                        title={item.label}
                      >
                        <Icon className={`w-4 h-4 shrink-0 ${active ? "text-amber-500" : ""}`} />
                        {!collapsed && <span className="truncate">{item.label}</span>}
                      </Link>
                    </li>
                  );
                })}
              </ul>
            </div>
          ))}
        </nav>

        {/* Collapse + Theme */}
        <div className="border-t border-border/30 p-2 flex items-center justify-between gap-1">
          <button
            onClick={() => setCollapsed(!collapsed)}
            className="flex-1 flex items-center justify-center gap-2 px-2 py-2 rounded-lg text-muted-foreground hover:bg-sidebar-accent hover:text-foreground transition-colors text-xs"
          >
            {collapsed ? <ChevronRight className="w-4 h-4" /> : <><ChevronLeft className="w-4 h-4" /> <span>Collapse</span></>}
          </button>
          {!collapsed && <ThemeToggle />}
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-y-auto bg-background">
        {/* Workspace Indicator Bar */}
        <div className={`h-1 ${isLive ? "bg-gradient-to-r from-red-500 to-orange-500" : "bg-gradient-to-r from-emerald-500 to-teal-500"}`} />
        {children}
      </main>
    </div>
  );
}
