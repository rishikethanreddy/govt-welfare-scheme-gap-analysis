"use client";
import React, { useEffect, useState } from "react";
import AppShell from "@/components/AppShell";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { api } from "@/lib/api";
import { Shield, TrendingUp, ArrowRight } from "lucide-react";
import Link from "next/link";

export default function SchemesPage() {
  const [schemes, setSchemes] = useState<any[]>([]);
  const [distribution, setDistribution] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([api.schemes(), api.dashboardSchemes()])
      .then(([s, d]) => { setSchemes(s); setDistribution(d); })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const getDistro = (name: string) => distribution.find((d) => d.scheme === name || d.scheme === name);

  return (
    <AppShell>
      <div className="p-6 space-y-6 max-w-[1400px] mx-auto">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold">Scheme Analysis</h1>
            <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-500/15 text-emerald-500 border border-emerald-500/20">ANALYZED DATASET</span>
          </div>
          <p className="text-sm text-muted-foreground mt-0.5">Per-scheme awareness gap analysis — questions analyzed, gap signals, geographic distribution</p>
        </div>

        {loading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {Array.from({ length: 6 }).map((_, i) => (
              <Card key={i} className="animate-pulse border-border/30"><CardContent className="p-6 h-40" /></Card>
            ))}
          </div>
        ) : (
          <>
            {/* Scheme Cards Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {schemes.map((scheme) => {
                const dist = distribution.find((d) => d.scheme === scheme.short_name || d.scheme === scheme.name);
                return (
                  <Link href={`/schemes/${encodeURIComponent(scheme.short_name || scheme.name)}`} key={scheme.id}>
                    <Card className="border-border/30 bg-card/50 hover:border-amber-500/30 hover:bg-card/70 transition-all cursor-pointer group">
                      <CardContent className="p-5">
                        <div className="flex items-start justify-between mb-3">
                          <div>
                            <h3 className="text-sm font-semibold text-foreground group-hover:text-amber-400 transition-colors">
                              {scheme.short_name || scheme.name}
                            </h3>
                            <p className="text-[10px] text-muted-foreground mt-0.5">{scheme.category}</p>
                          </div>
                          <ArrowRight className="w-4 h-4 text-muted-foreground group-hover:text-amber-400 transition-colors" />
                        </div>
                        <p className="text-[11px] text-muted-foreground line-clamp-2 mb-4">
                          {scheme.ministry || scheme.name}
                        </p>
                        <div className="grid grid-cols-3 gap-2">
                          <div>
                            <p className="text-lg font-bold">{dist?.total_records || 0}</p>
                            <p className="text-[10px] text-muted-foreground">Records</p>
                          </div>
                          <div>
                            <p className="text-lg font-bold text-amber-400">{dist?.gap_signals || 0}</p>
                            <p className="text-[10px] text-muted-foreground">Gap Signals</p>
                          </div>
                          <div>
                            <p className="text-lg font-bold text-orange-400">{dist?.gap_rate || 0}%</p>
                            <p className="text-[10px] text-muted-foreground">Gap Rate</p>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  </Link>
                );
              })}
            </div>

            {/* Summary Table */}
            <Card className="border-border/30 bg-card/50">
              <CardHeader>
                <CardTitle className="text-sm">Scheme Comparison</CardTitle>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow className="border-border/30">
                      <TableHead className="text-xs">Scheme</TableHead>
                      <TableHead className="text-xs">Category</TableHead>
                      <TableHead className="text-xs text-right">Records</TableHead>
                      <TableHead className="text-xs text-right">Gap Signals</TableHead>
                      <TableHead className="text-xs text-right">Gap Rate</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {distribution.map((d) => (
                      <TableRow key={d.scheme} className="border-border/20">
                        <TableCell className="text-xs font-medium">{d.scheme}</TableCell>
                        <TableCell className="text-xs text-muted-foreground">
                          {schemes.find((s) => s.short_name === d.scheme)?.category || "—"}
                        </TableCell>
                        <TableCell className="text-xs text-right">{d.total_records}</TableCell>
                        <TableCell className="text-xs text-right text-amber-400">{d.gap_signals}</TableCell>
                        <TableCell className="text-xs text-right">
                          <span className={d.gap_rate > 70 ? "text-red-400" : d.gap_rate > 50 ? "text-orange-400" : "text-green-400"}>
                            {d.gap_rate}%
                          </span>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          </>
        )}
      </div>
    </AppShell>
  );
}
