"use client";
import React, { useEffect, useState } from "react";
import AppShell from "@/components/AppShell";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { FileSearch, Database, Activity, RefreshCw, BarChart as BarChartIcon, CheckCircle2, ShieldAlert } from "lucide-react";
import { api } from "@/lib/api";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, PieChart, Pie, Cell } from "recharts";

export default function DatasetAnalyticsPage() {
  const [overview, setOverview] = useState<any>(null);
  const [intents, setIntents] = useState<any[]>([]);
  const [versions, setVersions] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchAnalytics = async () => {
      setLoading(true);
      try {
        // Fetch global analytics filtered for csv_upload
        const [overviewRes, intentsRes, versionsRes] = await Promise.all([
          api.get("/api/analytics/overview?source_type=csv_upload"),
          api.get("/api/analytics/intents?source_type=csv_upload"),
          api.get("/api/datasets")
        ]);
        setOverview(overviewRes);
        setIntents(intentsRes.intents || []);
        setVersions(versionsRes);
      } catch (e) {
        console.error("Failed to fetch dataset analytics", e);
      } finally {
        setLoading(false);
      }
    };
    fetchAnalytics();
  }, []);

  const COLORS = ["#f59e0b", "#10b981", "#3b82f6", "#8b5cf6", "#ec4899", "#64748b"];

  return (
    <AppShell>
      <div className="p-6 space-y-6 max-w-[1400px] mx-auto">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold flex items-center gap-2">
              <FileSearch className="w-6 h-6 text-amber-500" />
              Dataset Analytics
            </h1>
            <p className="text-sm text-muted-foreground mt-0.5">Health and intelligence metrics for imported datasets</p>
          </div>
          <div className="flex items-center gap-2">
            <Database className="w-4 h-4 text-muted-foreground" />
            <span className="text-sm font-medium">{versions.length} Datasets Imported</span>
          </div>
        </div>

        {loading ? (
          <div className="h-64 flex items-center justify-center">
            <RefreshCw className="w-6 h-6 text-muted-foreground animate-spin" />
          </div>
        ) : (
          <>
            {/* KPI Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <Card className="border-border/30 bg-card/50">
                <CardContent className="p-6">
                  <div className="flex justify-between items-start">
                    <div>
                      <p className="text-sm font-medium text-muted-foreground">Total Imported Records</p>
                      <h3 className="text-3xl font-bold mt-1">{overview?.total_records?.toLocaleString() || 0}</h3>
                    </div>
                    <Database className="w-8 h-8 text-blue-500/20" />
                  </div>
                </CardContent>
              </Card>
              <Card className="border-border/30 bg-card/50">
                <CardContent className="p-6">
                  <div className="flex justify-between items-start">
                    <div>
                      <p className="text-sm font-medium text-muted-foreground">Schemes Identified</p>
                      <h3 className="text-3xl font-bold mt-1">{overview?.schemes_analyzed || 0}</h3>
                    </div>
                    <BarChartIcon className="w-8 h-8 text-purple-500/20" />
                  </div>
                </CardContent>
              </Card>
              <Card className="border-border/30 bg-card/50">
                <CardContent className="p-6">
                  <div className="flex justify-between items-start">
                    <div>
                      <p className="text-sm font-medium text-muted-foreground">Awareness Gap Signals</p>
                      <h3 className="text-3xl font-bold mt-1 text-amber-500">{overview?.awareness_gap_signals?.toLocaleString() || 0}</h3>
                    </div>
                    <ShieldAlert className="w-8 h-8 text-amber-500/20" />
                  </div>
                </CardContent>
              </Card>
              <Card className="border-border/30 bg-card/50">
                <CardContent className="p-6">
                  <div className="flex justify-between items-start">
                    <div>
                      <p className="text-sm font-medium text-muted-foreground">Overall Gap Rate</p>
                      <h3 className="text-3xl font-bold mt-1 text-red-400">{overview?.gap_rate || 0}%</h3>
                    </div>
                    <Activity className="w-8 h-8 text-red-500/20" />
                  </div>
                </CardContent>
              </Card>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Intent Distribution */}
              <Card className="lg:col-span-1 border-border/30 bg-card/50">
                <CardHeader>
                  <CardTitle className="text-sm">Intent Distribution</CardTitle>
                </CardHeader>
                <CardContent className="h-64 flex items-center justify-center">
                  {intents.length > 0 ? (
                    <ResponsiveContainer width="100%" height="100%">
                      <PieChart>
                        <Pie
                          data={intents}
                          dataKey="count"
                          nameKey="intent"
                          cx="50%"
                          cy="50%"
                          innerRadius={60}
                          outerRadius={80}
                          paddingAngle={2}
                        >
                          {intents.map((_, index) => (
                            <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                          ))}
                        </Pie>
                        <Tooltip contentStyle={{ backgroundColor: '#1e293b', borderColor: '#334155' }} />
                      </PieChart>
                    </ResponsiveContainer>
                  ) : (
                    <p className="text-sm text-muted-foreground">No intent data available</p>
                  )}
                </CardContent>
                <div className="px-6 pb-6 pt-0">
                   <div className="flex flex-wrap gap-2">
                     {intents.map((i: any, idx: number) => (
                       <span key={i.intent} className="text-[10px] flex items-center gap-1">
                         <span className="w-2 h-2 rounded-full" style={{ backgroundColor: COLORS[idx % COLORS.length] }}></span>
                         {i.intent} ({i.percentage}%)
                       </span>
                     ))}
                   </div>
                </div>
              </Card>

              {/* Uploaded Versions History */}
              <Card className="lg:col-span-2 border-border/30 bg-card/50">
                <CardHeader>
                  <CardTitle className="text-sm">Import History</CardTitle>
                  <CardDescription className="text-xs">Log of all dataset imports and their resulting health</CardDescription>
                </CardHeader>
                <CardContent>
                  <Table>
                    <TableHeader>
                      <TableRow className="border-border/30">
                        <TableHead className="text-xs">Version</TableHead>
                        <TableHead className="text-xs">File</TableHead>
                        <TableHead className="text-xs text-right">Valid Records</TableHead>
                        <TableHead className="text-xs text-right">Duplicates</TableHead>
                        <TableHead className="text-xs text-right">Status</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {versions.map((v) => (
                        <TableRow key={v.id} className="border-border/20">
                          <TableCell className="text-xs font-bold text-amber-500">{v.version}</TableCell>
                          <TableCell className="text-xs max-w-[200px] truncate">{v.source_file}</TableCell>
                          <TableCell className="text-xs text-right font-medium">{v.valid_records}</TableCell>
                          <TableCell className="text-xs text-right text-muted-foreground">{v.duplicate_records}</TableCell>
                          <TableCell className="text-xs text-right">
                            {v.processing_status === 'imported' ? (
                              <span className="text-green-400 flex items-center justify-end gap-1"><CheckCircle2 className="w-3 h-3"/> Imported</span>
                            ) : (
                              <span className="text-amber-400">{v.processing_status}</span>
                            )}
                          </TableCell>
                        </TableRow>
                      ))}
                      {versions.length === 0 && (
                        <TableRow>
                          <TableCell colSpan={5} className="text-center text-xs text-muted-foreground py-8">
                            No datasets have been imported yet.
                          </TableCell>
                        </TableRow>
                      )}
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
