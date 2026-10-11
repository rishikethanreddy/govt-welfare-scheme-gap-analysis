"use client";
import React, { useEffect, useState } from "react";
import AppShell from "@/components/AppShell";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  CartesianGrid, PieChart, Pie, Cell, Legend
} from "recharts";
import { api } from "@/lib/api";

const COLORS = ["#f59e0b", "#3b82f6", "#8b5cf6", "#10b981", "#ef4444", "#ec4899", "#06b6d4", "#f97316"];

export default function IntentsPage() {
  const [intents, setIntents] = useState<any[]>([]);
  const [gapTypes, setGapTypes] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([api.dashboardIntents(), api.dashboardGapTypes()])
      .then(([i, g]) => { setIntents(i); setGapTypes(g); })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  return (
    <AppShell>
      <div className="p-6 space-y-6 max-w-[1400px] mx-auto">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold">Intent &amp; Gap Types</h1>
            <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-500/15 text-emerald-500 border border-emerald-500/20">ANALYZED DATASET</span>
          </div>
          <p className="text-sm text-muted-foreground mt-0.5">
            What people are asking and what types of awareness gaps are detected
          </p>
        </div>

        {loading ? (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {[1,2].map(i => <Card key={i} className="h-80 animate-pulse border-border/30" />)}
          </div>
        ) : (
          <>
            {/* Charts */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              <Card className="border-border/30 bg-card/50">
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm">User Intent Distribution</CardTitle>
                  <CardDescription className="text-xs">What types of questions/queries are people asking about welfare schemes?</CardDescription>
                </CardHeader>
                <CardContent className="h-80">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie data={intents} dataKey="count" nameKey="intent" cx="50%" cy="50%" innerRadius={55} outerRadius={95} paddingAngle={2} strokeWidth={0}>
                        {intents.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                      </Pie>
                      <Tooltip />
                      <Legend iconType="circle" iconSize={8} wrapperStyle={{ fontSize: '11px', color: 'var(--muted-foreground)' }} />
                    </PieChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>

              <Card className="border-border/30 bg-card/50">
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm">Gap Type Distribution</CardTitle>
                  <CardDescription className="text-xs">What types of awareness gaps are detected in the dataset?</CardDescription>
                </CardHeader>
                <CardContent className="h-80">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={gapTypes} layout="vertical" margin={{ left: 10, right: 20 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" horizontal={false} />
                      <XAxis type="number" tick={{ fontSize: 11, fill: 'var(--muted-foreground)' }} axisLine={false} tickLine={false} />
                      <YAxis type="category" dataKey="gap_type" tick={{ fontSize: 10, fill: 'var(--muted-foreground)' }} width={120} axisLine={false} tickLine={false} />
                      <Tooltip />
                      <Bar dataKey="count" fill="#8b5cf6" radius={[0, 3, 3, 0]} name="Occurrences" />
                    </BarChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>
            </div>

            {/* Tables */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              <Card className="border-border/30 bg-card/50">
                <CardHeader>
                  <CardTitle className="text-sm">Intents Table</CardTitle>
                </CardHeader>
                <CardContent>
                  <Table>
                    <TableHeader>
                      <TableRow className="border-border/30">
                        <TableHead className="text-xs">Intent</TableHead>
                        <TableHead className="text-xs text-right">Count</TableHead>
                        <TableHead className="text-xs text-right">Percentage</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {intents.map((r, i) => (
                        <TableRow key={r.intent} className="border-border/20">
                          <TableCell className="text-xs font-medium">
                            <div className="flex items-center gap-2">
                              <div className="w-2 h-2 rounded-full" style={{ backgroundColor: COLORS[i % COLORS.length] }} />
                              {r.intent}
                            </div>
                          </TableCell>
                          <TableCell className="text-xs text-right">{r.count}</TableCell>
                          <TableCell className="text-xs text-right text-muted-foreground">{r.percentage}%</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </CardContent>
              </Card>

              <Card className="border-border/30 bg-card/50">
                <CardHeader>
                  <CardTitle className="text-sm">Gap Types Table</CardTitle>
                </CardHeader>
                <CardContent>
                  <Table>
                    <TableHeader>
                      <TableRow className="border-border/30">
                        <TableHead className="text-xs">Gap Type</TableHead>
                        <TableHead className="text-xs text-right">Count</TableHead>
                        <TableHead className="text-xs text-right">Percentage</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {gapTypes.map((r) => (
                        <TableRow key={r.gap_type} className="border-border/20">
                          <TableCell className="text-xs font-medium">{r.gap_type}</TableCell>
                          <TableCell className="text-xs text-right">{r.count}</TableCell>
                          <TableCell className="text-xs text-right text-muted-foreground">{r.percentage}%</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </CardContent>
              </Card>
            </div>
          </>
        )}
      </div>
    </AppShell>
  );
}
