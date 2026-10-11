"use client";
import React, { useEffect, useState, useCallback } from "react";
import AppShell from "@/components/AppShell";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import {
  BarChart, Bar, XAxis, YAxis, Tooltip as RechartsTooltip, ResponsiveContainer,
  CartesianGrid, PieChart, Pie, Cell, Legend
} from "recharts";
import { api } from "@/lib/api";
import {
  Database, AlertTriangle, TrendingUp, MapPin, Shield, Search,
  RefreshCw, ChevronDown
} from "lucide-react";

const CHART_COLORS = [
  "#f59e0b", "#3b82f6", "#8b5cf6", "#10b981", "#ef4444",
  "#ec4899", "#06b6d4", "#f97316", "#84cc16", "#6366f1",
];

function KPICard({ title, value, subtitle, icon: Icon, color = "text-foreground", accent = "" }: any) {
  return (
    <Card className={`relative overflow-hidden border-border/30 bg-gradient-to-br ${accent}`}>
      <CardContent className="p-5">
        <div className="flex items-start justify-between">
          <div className="space-y-1">
            <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider">{title}</p>
            <p className={`text-2xl font-bold ${color}`}>{value}</p>
            {subtitle && <p className="text-xs text-muted-foreground">{subtitle}</p>}
          </div>
          <div className="w-10 h-10 rounded-xl bg-secondary dark:bg-white/5 flex items-center justify-center">
            <Icon className="w-5 h-5 text-muted-foreground" />
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

function ChartTooltip({ active, payload, label }: any) {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded-lg border border-border/50 bg-card px-3 py-2 shadow-xl">
      <p className="text-xs font-medium text-foreground mb-1">{label}</p>
      {payload.map((p: any, i: number) => (
        <p key={i} className="text-xs text-muted-foreground">
          <span style={{ color: p.color }} className="font-medium">{p.name}:</span> {p.value}
        </p>
      ))}
    </div>
  );
}

export default function DashboardPage() {
  const [overview, setOverview] = useState<any>(null);
  const [schemes, setSchemes] = useState<any[]>([]);
  const [gapTypes, setGapTypes] = useState<any[]>([]);
  const [issues, setIssues] = useState<any[]>([]);
  const [filters, setFilters] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeFilter, setActiveFilter] = useState<Record<string, string>>({});

  const loadData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params: Record<string, string> = {};
      Object.entries(activeFilter).forEach(([k, v]) => { if (v) params[k] = v; });

      const [ov, sch, gap, iss, flt] = await Promise.all([
        api.dashboardOverview(params),
        api.dashboardSchemes(params),
        api.dashboardGapTypes(params),
        api.dashboardRecurringIssues(params),
        !filters ? api.dashboardFilters() : Promise.resolve(filters),
      ]);
      setOverview(ov);
      setSchemes(sch);
      setGapTypes(gap);
      setIssues(iss);
      if (!filters) setFilters(flt);
    } catch (e: any) {
      setError(e.message || "Failed to load dashboard data");
    } finally {
      setLoading(false);
    }
  }, [activeFilter, filters]);

  useEffect(() => { loadData(); }, [loadData]);

  const setFilter = (key: string, value: string) => {
    setActiveFilter((prev) => {
      const next = { ...prev };
      if (value) next[key] = value;
      else delete next[key];
      return next;
    });
  };

  const nonGapCount = overview ? overview.total_records - overview.awareness_gap_signals : 0;
  const gapPieData = overview ? [
    { name: "Gap Signals", value: overview.awareness_gap_signals },
    { name: "No Gap", value: nonGapCount },
  ] : [];

  return (
    <AppShell>
      <div className="p-6 space-y-6 max-w-[1400px] mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-bold text-foreground">Dataset Intelligence</h1>
              <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-500/15 text-emerald-500 border border-emerald-500/20">
                ANALYZED DATASET
              </span>
            </div>
            <p className="text-sm text-muted-foreground mt-0.5">
              Awareness gaps, misconceptions &amp; information needs in government welfare schemes
            </p>
          </div>
          <button
            onClick={loadData}
            className="flex items-center gap-2 px-3 py-2 text-xs rounded-lg border border-border/40 bg-secondary hover:bg-secondary/80 transition-colors text-muted-foreground"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
            Refresh
          </button>
        </div>

        {/* Filter Bar */}
        {filters && (
          <div className="flex flex-wrap gap-2">
            {[
              { key: "scheme", label: "Scheme", options: filters.schemes },
              { key: "state", label: "State", options: filters.states },
              { key: "gap_type", label: "Gap Type", options: filters.gap_types },
            ].map(({ key, label, options }) => (
              <select
                key={key}
                value={activeFilter[key] || ""}
                onChange={(e) => setFilter(key, e.target.value)}
                className="text-xs px-3 py-1.5 rounded-lg border border-border/40 bg-card text-foreground appearance-none cursor-pointer min-w-[130px]"
              >
                <option value="">All {label}s</option>
                {options?.map((o: string) => <option key={o} value={o}>{o}</option>)}
              </select>
            ))}
            {Object.keys(activeFilter).length > 0 && (
              <button
                onClick={() => setActiveFilter({})}
                className="text-xs px-3 py-1.5 rounded-lg bg-amber-500/10 text-amber-500 hover:bg-amber-500/20 transition-colors"
              >
                Clear Filters
              </button>
            )}
          </div>
        )}

        {/* Error State */}
        {error && (
          <div className="p-4 rounded-lg border border-red-500/30 bg-red-500/5 text-red-400 text-sm">
            <AlertTriangle className="w-4 h-4 inline mr-2" />
            {error}. Make sure the backend is running on port 8000.
          </div>
        )}

        {/* KPI Cards - Project-focused */}
        {overview && (
          <div className="grid grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-3">
            <KPICard title="Analyzed Records" value={overview.total_records?.toLocaleString()} subtitle="Detected in analyzed dataset" icon={Database} accent="from-slate-100/50 to-slate-50/50 dark:from-slate-800/50 dark:to-slate-900/50" />
            <KPICard title="Gap Signals" value={overview.awareness_gap_signals} icon={AlertTriangle} color="text-amber-600 dark:text-amber-400" accent="from-amber-50/50 to-slate-50/50 dark:from-amber-950/30 dark:to-slate-900/50" />
            <KPICard title="Gap Rate" value={`${overview.gap_rate}%`} icon={TrendingUp} color="text-orange-600 dark:text-orange-400" accent="from-orange-50/50 to-slate-50/50 dark:from-orange-950/30 dark:to-slate-900/50" />
            <KPICard title="Schemes Analyzed" value={overview.schemes_analyzed} icon={Shield} accent="from-blue-50/50 to-slate-50/50 dark:from-blue-950/30 dark:to-slate-900/50" />
            <KPICard title="Regions with Gaps" value={overview.states_covered} subtitle={`${overview.districts_covered} districts`} icon={MapPin} accent="from-emerald-50/50 to-slate-50/50 dark:from-emerald-950/30 dark:to-slate-900/50" />
            <KPICard title="Top Gap Type" value={gapTypes[0]?.gap_type || "—"} subtitle={gapTypes[0] ? `${gapTypes[0].count} occurrences` : undefined} icon={Search} accent="from-purple-50/50 to-slate-50/50 dark:from-purple-950/30 dark:to-slate-900/50" />
          </div>
        )}

        {!loading && overview && (
          <>
            {/* Row: Gap vs Non-Gap + Gap Types */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              {/* Gap vs Non-Gap Pie */}
              <Card className="border-border/30 bg-card/50">
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-medium">Awareness Gap Detection</CardTitle>
                  <CardDescription className="text-xs">Gap vs non-gap signal distribution in analyzed dataset</CardDescription>
                </CardHeader>
                <CardContent className="h-72">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={gapPieData}
                        dataKey="value"
                        nameKey="name"
                        cx="50%" cy="50%"
                        innerRadius={55} outerRadius={90}
                        paddingAngle={3}
                        strokeWidth={0}
                      >
                        <Cell fill="#f59e0b" />
                        <Cell fill="var(--muted)" />
                      </Pie>
                      <RechartsTooltip content={<ChartTooltip />} />
                      <Legend iconType="circle" iconSize={8} wrapperStyle={{ fontSize: '11px', color: 'var(--muted-foreground)' }} />
                    </PieChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>

              {/* Gap Type Distribution */}
              <Card className="border-border/30 bg-card/50">
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-medium">Awareness Gap Types</CardTitle>
                  <CardDescription className="text-xs">Categories of awareness gaps detected in dataset</CardDescription>
                </CardHeader>
                <CardContent className="h-72">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={gapTypes} margin={{ left: 10, right: 20 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
                      <XAxis dataKey="gap_type" tick={{ fontSize: 10, fill: 'var(--muted-foreground)' }} axisLine={false} tickLine={false} />
                      <YAxis tick={{ fontSize: 11, fill: 'var(--muted-foreground)' }} axisLine={false} tickLine={false} />
                      <RechartsTooltip content={<ChartTooltip />} />
                      <Bar dataKey="count" fill="#8b5cf6" radius={[4, 4, 0, 0]} name="Count" />
                    </BarChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>
            </div>

            {/* Row: Scheme-wise Gaps + Recurring Issues */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              {/* Scheme Distribution */}
              <Card className="border-border/30 bg-card/50">
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-medium">Gap Signals by Scheme</CardTitle>
                  <CardDescription className="text-xs">Awareness gap detection rate per welfare scheme</CardDescription>
                </CardHeader>
                <CardContent className="h-72">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={schemes.slice(0, 10)} layout="vertical" margin={{ left: 10, right: 20 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" horizontal={false} />
                      <XAxis type="number" tick={{ fontSize: 11, fill: 'var(--muted-foreground)' }} axisLine={false} tickLine={false} />
                      <YAxis type="category" dataKey="scheme" tick={{ fontSize: 11, fill: 'var(--muted-foreground)' }} width={110} axisLine={false} tickLine={false} />
                      <RechartsTooltip content={<ChartTooltip />} />
                      <Bar dataKey="total_records" fill="var(--muted-foreground)" radius={[0, 3, 3, 0]} name="Total" />
                      <Bar dataKey="gap_signals" fill="#f59e0b" radius={[0, 3, 3, 0]} name="Gap Signals" />
                    </BarChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>

              {/* Recurring Awareness Issues */}
              <Card className="border-border/30 bg-card/50">
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-medium">Recurring Awareness Gaps</CardTitle>
                  <CardDescription className="text-xs">Most common misconceptions and information needs from analyzed data</CardDescription>
                </CardHeader>
                <CardContent className="space-y-2 max-h-72 overflow-y-auto">
                  {issues.length === 0 && (
                    <p className="text-xs text-muted-foreground py-4 text-center">No recurring issues found with current filters</p>
                  )}
                  {issues.slice(0, 6).map((issue: any, i: number) => (
                    <div key={i} className="p-3 rounded-lg bg-secondary/50 border border-border/20 hover:border-border/40 transition-colors">
                      <p className="text-xs text-foreground/90 line-clamp-2 leading-relaxed">&ldquo;{issue.text}&rdquo;</p>
                      <div className="flex gap-2 mt-2 flex-wrap">
                        {issue.scheme && (
                          <span className="text-[10px] px-2 py-0.5 rounded-full bg-amber-500/10 text-amber-500">{issue.scheme}</span>
                        )}
                        {issue.gap_type && (
                          <span className="text-[10px] px-2 py-0.5 rounded-full bg-purple-500/10 text-purple-400">{issue.gap_type}</span>
                        )}
                        {issue.states?.length > 0 && (
                          <span className="text-[10px] px-2 py-0.5 rounded-full bg-blue-500/10 text-blue-400">{issue.states[0]}</span>
                        )}
                      </div>
                    </div>
                  ))}
                </CardContent>
              </Card>
            </div>

            {/* Methodology */}
            <Card className="border-border/30 bg-card/50">
              <CardContent className="p-4">
                <div className="flex items-start gap-3">
                  <div className="w-8 h-8 rounded-lg bg-blue-500/10 flex items-center justify-center shrink-0 mt-0.5">
                    <AlertTriangle className="w-4 h-4 text-blue-400" />
                  </div>
                  <div>
                    <p className="text-xs font-medium text-foreground mb-1">Methodology &amp; Limitations</p>
                    <p className="text-[11px] text-muted-foreground leading-relaxed">
                      All metrics originate from the currently uploaded/processed dataset — no statistics are fabricated.
                      Awareness gap signals are detected using NLP classifiers (TF-IDF + Logistic Regression) 
                      trained on {overview.total_records} labeled records across {overview.schemes_analyzed} schemes.
                      Geographic coverage: {overview.states_covered} states, {overview.districts_covered} districts.
                      Gap rate = proportion of records flagged as containing awareness gap signals.
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </>
        )}

        {/* Loading State */}
        {loading && (
          <div className="grid grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-3">
            {Array.from({ length: 6 }).map((_, i) => (
              <Card key={i} className="border-border/30 bg-card/30 animate-pulse">
                <CardContent className="p-5 h-20" />
              </Card>
            ))}
          </div>
        )}
      </div>
    </AppShell>
  );
}
