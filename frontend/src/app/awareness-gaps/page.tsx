"use client";
import React, { useEffect, useState } from "react";
import AppShell from "@/components/AppShell";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  CartesianGrid, PieChart, Pie, Cell, Legend
} from "recharts";
import { api } from "@/lib/api";
import { AlertTriangle, TrendingUp, Search } from "lucide-react";

const COLORS = ["#f59e0b", "#8b5cf6", "#3b82f6", "#10b981", "#ef4444", "#ec4899", "#06b6d4", "#f97316"];

export default function AwarenessGapsPage() {
  const [overview, setOverview] = useState<any>(null);
  const [gapTypes, setGapTypes] = useState<any[]>([]);
  const [intents, setIntents] = useState<any[]>([]);
  const [schemes, setSchemes] = useState<any[]>([]);
  const [issues, setIssues] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      api.dashboardOverview(),
      api.dashboardGapTypes(),
      api.dashboardIntents(),
      api.dashboardSchemes(),
      api.dashboardRecurringIssues({ limit: "20" } as any),
    ])
      .then(([ov, gt, int, sch, iss]) => {
        setOverview(ov);
        setGapTypes(gt);
        setIntents(int);
        setSchemes(sch);
        setIssues(iss);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const gapPieData = overview ? [
    { name: "Gap Detected", value: overview.awareness_gap_signals },
    { name: "No Gap", value: overview.total_records - overview.awareness_gap_signals },
  ] : [];

  return (
    <AppShell>
      <div className="p-6 space-y-6 max-w-[1400px] mx-auto">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold">Awareness Gap Analysis</h1>
            <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-500/15 text-emerald-500 border border-emerald-500/20">ANALYZED DATASET</span>
          </div>
          <p className="text-sm text-muted-foreground mt-0.5">
            Detailed breakdown of detected awareness gaps, misconceptions and information needs
          </p>
        </div>

        {loading ? (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {Array.from({ length: 4 }).map((_, i) => (
              <Card key={i} className="h-80 animate-pulse border-border/30" />
            ))}
          </div>
        ) : (
          <>
            {/* Summary Strip */}
            {overview && (
              <div className="grid grid-cols-3 gap-3">
                <Card className="border-border/30 bg-card/50">
                  <CardContent className="p-4 text-center">
                    <p className="text-2xl font-bold text-amber-500">{overview.awareness_gap_signals}</p>
                    <p className="text-xs text-muted-foreground">Awareness Gap Signals</p>
                  </CardContent>
                </Card>
                <Card className="border-border/30 bg-card/50">
                  <CardContent className="p-4 text-center">
                    <p className="text-2xl font-bold text-orange-500">{overview.gap_rate}%</p>
                    <p className="text-xs text-muted-foreground">Gap Rate</p>
                  </CardContent>
                </Card>
                <Card className="border-border/30 bg-card/50">
                  <CardContent className="p-4 text-center">
                    <p className="text-2xl font-bold">{gapTypes.length}</p>
                    <p className="text-xs text-muted-foreground">Gap Type Categories</p>
                  </CardContent>
                </Card>
              </div>
            )}

            {/* Gap/Non-Gap + Gap Types side by side */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              <Card className="border-border/30 bg-card/50">
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm">Gap vs Non-Gap</CardTitle>
                  <CardDescription className="text-xs">What proportion of analyzed records contain awareness gap signals?</CardDescription>
                </CardHeader>
                <CardContent className="h-72">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie data={gapPieData} dataKey="value" nameKey="name" cx="50%" cy="50%" innerRadius={55} outerRadius={90} paddingAngle={3} strokeWidth={0}>
                        <Cell fill="#f59e0b" />
                        <Cell fill="var(--muted)" />
                      </Pie>
                      <Tooltip />
                      <Legend iconType="circle" iconSize={8} wrapperStyle={{ fontSize: '11px', color: 'var(--muted-foreground)' }} />
                    </PieChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>

              <Card className="border-border/30 bg-card/50">
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm">Gap Type Breakdown</CardTitle>
                  <CardDescription className="text-xs">What kinds of awareness gaps are most prevalent?</CardDescription>
                </CardHeader>
                <CardContent className="h-72">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={gapTypes} margin={{ left: 10, right: 20 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
                      <XAxis dataKey="gap_type" tick={{ fontSize: 10, fill: 'var(--muted-foreground)' }} axisLine={false} tickLine={false} />
                      <YAxis tick={{ fontSize: 11, fill: 'var(--muted-foreground)' }} axisLine={false} tickLine={false} />
                      <Tooltip />
                      <Bar dataKey="count" fill="#8b5cf6" radius={[4, 4, 0, 0]} name="Count" />
                    </BarChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>
            </div>

            {/* Scheme-wise Gaps + Intent Distribution */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              <Card className="border-border/30 bg-card/50">
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm">Scheme-wise Gap Distribution</CardTitle>
                  <CardDescription className="text-xs">Which welfare schemes have the most awareness gaps?</CardDescription>
                </CardHeader>
                <CardContent className="h-72">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={schemes.slice(0, 8)} layout="vertical" margin={{ left: 10, right: 20 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" horizontal={false} />
                      <XAxis type="number" tick={{ fontSize: 11, fill: 'var(--muted-foreground)' }} axisLine={false} tickLine={false} />
                      <YAxis type="category" dataKey="scheme" tick={{ fontSize: 10, fill: 'var(--muted-foreground)' }} width={110} axisLine={false} tickLine={false} />
                      <Tooltip />
                      <Bar dataKey="gap_signals" fill="#f59e0b" radius={[0, 3, 3, 0]} name="Gap Signals" />
                    </BarChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>

              <Card className="border-border/30 bg-card/50">
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm">Intent Distribution</CardTitle>
                  <CardDescription className="text-xs">What are people asking about government schemes?</CardDescription>
                </CardHeader>
                <CardContent className="h-72">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie data={intents} dataKey="count" nameKey="intent" cx="50%" cy="50%" innerRadius={50} outerRadius={90} paddingAngle={2} strokeWidth={0}>
                        {intents.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                      </Pie>
                      <Tooltip />
                      <Legend iconType="circle" iconSize={8} wrapperStyle={{ fontSize: '11px', color: 'var(--muted-foreground)' }} />
                    </PieChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>
            </div>

            {/* Recurring Awareness Gaps */}
            <Card className="border-border/30 bg-card/50">
              <CardHeader className="pb-2">
                <CardTitle className="text-sm">Recurring Awareness Gaps &amp; Misconceptions</CardTitle>
                <CardDescription className="text-xs">
                  Actual questions/records from the dataset that indicate awareness gaps
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-2 max-h-[500px] overflow-y-auto">
                {issues.length === 0 && (
                  <p className="text-xs text-muted-foreground py-8 text-center">No awareness gap signals found in the current dataset</p>
                )}
                {issues.map((issue: any, i: number) => (
                  <div key={i} className="p-3 rounded-lg bg-secondary/50 border border-border/20 hover:border-border/40 transition-colors">
                    <p className="text-xs text-foreground/90 leading-relaxed">&ldquo;{issue.text}&rdquo;</p>
                    <div className="flex gap-2 mt-2 flex-wrap">
                      {issue.scheme && <span className="text-[10px] px-2 py-0.5 rounded-full bg-amber-500/10 text-amber-500">{issue.scheme}</span>}
                      {issue.gap_type && <span className="text-[10px] px-2 py-0.5 rounded-full bg-purple-500/10 text-purple-400">{issue.gap_type}</span>}
                      {issue.intent && <span className="text-[10px] px-2 py-0.5 rounded-full bg-blue-500/10 text-blue-400">{issue.intent}</span>}
                      {issue.states?.length > 0 && <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400">{issue.states[0]}</span>}
                    </div>
                  </div>
                ))}
              </CardContent>
            </Card>
          </>
        )}
      </div>
    </AppShell>
  );
}
