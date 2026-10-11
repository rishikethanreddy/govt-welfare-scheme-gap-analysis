"use client";
import React, { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import AppShell from "@/components/AppShell";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { api } from "@/lib/api";
import { ArrowLeft, AlertTriangle } from "lucide-react";
import Link from "next/link";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from "recharts";

export default function SchemeDetailPage() {
  const params = useParams();
  const schemeId = decodeURIComponent(params.id as string);
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.schemeIntelligence(schemeId)
      .then(setData)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [schemeId]);

  return (
    <AppShell>
      <div className="p-6 space-y-6 max-w-[1200px] mx-auto">
        <Link href="/schemes" className="flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground transition-colors">
          <ArrowLeft className="w-4 h-4" /> Back to Schemes
        </Link>

        {loading && <div className="animate-pulse space-y-4">{Array.from({ length: 3 }).map((_, i) => <Card key={i} className="h-32 border-border/30" />)}</div>}
        {error && <div className="p-4 rounded-lg border border-red-500/30 bg-red-500/5 text-red-400 text-sm">{error}</div>}

        {data && (
          <>
            <div>
              <h1 className="text-2xl font-bold">{data.scheme?.name || schemeId}</h1>
              <p className="text-sm text-muted-foreground mt-0.5">{data.scheme?.short_name} — Scheme Intelligence Report</p>
            </div>

            <div className="grid grid-cols-3 gap-3">
              <Card className="border-border/30 bg-card/50">
                <CardContent className="p-4 text-center">
                  <p className="text-2xl font-bold">{data.total_records}</p>
                  <p className="text-xs text-muted-foreground">Total Records</p>
                </CardContent>
              </Card>
              <Card className="border-border/30 bg-card/50">
                <CardContent className="p-4 text-center">
                  <p className="text-2xl font-bold text-amber-400">{data.awareness_gap_signals}</p>
                  <p className="text-xs text-muted-foreground">Gap Signals</p>
                </CardContent>
              </Card>
              <Card className="border-border/30 bg-card/50">
                <CardContent className="p-4 text-center">
                  <p className="text-2xl font-bold text-orange-400">{data.gap_rate}%</p>
                  <p className="text-xs text-muted-foreground">Gap Rate</p>
                </CardContent>
              </Card>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              {/* Top Intents */}
              <Card className="border-border/30 bg-card/50">
                <CardHeader><CardTitle className="text-sm">Top Intents</CardTitle></CardHeader>
                <CardContent className="h-48">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={data.top_intents} layout="vertical">
                      <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" horizontal={false} />
                      <XAxis type="number" tick={{ fontSize: 10, fill: 'var(--muted-foreground)' }} axisLine={false} />
                      <YAxis type="category" dataKey="intent" width={100} tick={{ fontSize: 10, fill: 'var(--muted-foreground)' }} axisLine={false} />
                      <Tooltip />
                      <Bar dataKey="count" fill="#3b82f6" radius={[0, 3, 3, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>

              {/* Top Gap Types */}
              <Card className="border-border/30 bg-card/50">
                <CardHeader><CardTitle className="text-sm">Top Gap Types</CardTitle></CardHeader>
                <CardContent className="h-48">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={data.top_gap_types} layout="vertical">
                      <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" horizontal={false} />
                      <XAxis type="number" tick={{ fontSize: 10, fill: 'var(--muted-foreground)' }} axisLine={false} />
                      <YAxis type="category" dataKey="gap_type" width={120} tick={{ fontSize: 10, fill: 'var(--muted-foreground)' }} axisLine={false} />
                      <Tooltip />
                      <Bar dataKey="count" fill="#8b5cf6" radius={[0, 3, 3, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>
            </div>

            {/* Recurring Questions */}
            <Card className="border-border/30 bg-card/50">
              <CardHeader><CardTitle className="text-sm">Recurring Awareness Gap Questions</CardTitle></CardHeader>
              <CardContent className="space-y-2">
                {data.recurring_questions?.length === 0 && <p className="text-xs text-muted-foreground">No recurring questions found.</p>}
                {data.recurring_questions?.slice(0, 8).map((q: any, i: number) => (
                  <div key={i} className="p-3 rounded-lg bg-white/[0.02] border border-border/20">
                    <p className="text-xs text-foreground/90 leading-relaxed">{q.text}</p>
                    {q.gap_type && <span className="text-[10px] px-2 py-0.5 rounded-full bg-purple-500/10 text-purple-400 mt-1 inline-block">{q.gap_type}</span>}
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
