"use client";
import React, { useEffect, useState } from "react";
import AppShell from "@/components/AppShell";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { api } from "@/lib/api";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from "recharts";
import IndiaMap from "@/components/IndiaMap";
import { MapPin, AlertTriangle } from "lucide-react";

export default function GeographyPage() {
  const [heatmapData, setHeatmapData] = useState<any>(null);
  const [level, setLevel] = useState<"state" | "district">("state");
  const [metric, setMetric] = useState<"gap_signals" | "gap_rate" | "records">("gap_signals");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    api.get(`/api/geography/heatmap?level=${level}&metric=${metric}`)
      .then((data) => setHeatmapData(data))
      .catch((e) => console.error("Failed to load heatmap data", e))
      .finally(() => setLoading(false));
  }, [level, metric]);

  const regions = heatmapData?.regions || [];
  const hasData = regions.length > 0;

  // Prepare map data in the format IndiaMap expects
  const mapData = regions.map((r: any) => ({
    state: r.state,
    district: r.district,
    total_records: r.total_records,
    gap_signals: r.gap_signals,
    gap_rate: r.gap_rate,
    dominant_gap_type: r.dominant_gap_type,
    top_schemes: r.top_schemes,
  }));

  return (
    <AppShell>
      <div className="p-6 space-y-6 max-w-[1400px] mx-auto">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold flex items-center gap-2">
              <MapPin className="w-6 h-6 text-amber-500" />
              Geographic Gap Analysis
            </h1>
            <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-500/15 text-emerald-500 border border-emerald-500/20">ANALYZED DATASET</span>
          </div>
          <p className="text-sm text-muted-foreground mt-0.5">
            Where are awareness gap signals concentrated geographically?
          </p>
        </div>

        {/* Controls */}
        <div className="flex flex-wrap items-center gap-3">
          <div className="flex rounded-lg border border-border/40 overflow-hidden">
            {(["state", "district"] as const).map((l) => (
              <button
                key={l}
                onClick={() => setLevel(l)}
                className={`px-4 py-2 text-xs font-medium transition-colors ${
                  level === l
                    ? "bg-amber-500/15 text-amber-500"
                    : "bg-card text-muted-foreground hover:bg-secondary"
                }`}
              >
                {l === "state" ? "State Level" : "District Level"}
              </button>
            ))}
          </div>
          <div className="flex rounded-lg border border-border/40 overflow-hidden">
            {([
              { key: "gap_signals", label: "Gap Signals" },
              { key: "gap_rate", label: "Gap Rate" },
              { key: "records", label: "Records" },
            ] as const).map((m) => (
              <button
                key={m.key}
                onClick={() => setMetric(m.key as any)}
                className={`px-4 py-2 text-xs font-medium transition-colors ${
                  metric === m.key
                    ? "bg-amber-500/15 text-amber-500"
                    : "bg-card text-muted-foreground hover:bg-secondary"
                }`}
              >
                {m.label}
              </button>
            ))}
          </div>
        </div>

        {loading ? (
          <Card className="h-[600px] border-border/30 animate-pulse" />
        ) : !hasData ? (
          <Card className="border-border/30 bg-card/50">
            <CardContent className="p-12 text-center">
              <AlertTriangle className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
              <p className="text-lg font-medium text-foreground mb-2">Insufficient Geographic Data</p>
              <p className="text-sm text-muted-foreground max-w-md mx-auto">
                No geographic signals found in the current dataset. Upload data with state/district fields to enable this visualization.
              </p>
            </CardContent>
          </Card>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Map */}
            <div className="lg:col-span-2">
              <Card className="border-border/30 bg-card/50 h-full">
                <CardHeader className="pb-1">
                  <CardTitle className="text-sm">Awareness Gap Heatmap — India</CardTitle>
                  <CardDescription className="text-xs">
                    Intensity based on {metric === "gap_signals" ? "number of gap signals" : metric === "gap_rate" ? "gap rate percentage" : "total records analyzed"}. 
                    Hover for region details.
                  </CardDescription>
                </CardHeader>
                <CardContent className="h-[600px] p-0 px-4 pb-4">
                  <IndiaMap data={mapData} metric={metric} />
                </CardContent>
              </Card>
            </div>

            {/* Side Panel */}
            <div className="lg:col-span-1 space-y-4">
              {/* Bar Chart */}
              <Card className="border-border/30 bg-card/50">
                <CardHeader className="pb-1">
                  <CardTitle className="text-sm">Top Regions by Gap Signals</CardTitle>
                </CardHeader>
                <CardContent className="h-[250px]">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={regions.slice(0, 10)} layout="vertical" margin={{ left: 10, right: 20 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" horizontal={false} />
                      <XAxis type="number" tick={{ fontSize: 11, fill: 'var(--muted-foreground)' }} axisLine={false} tickLine={false} />
                      <YAxis type="category" dataKey={level === "district" ? "district" : "state"} width={90} tick={{ fontSize: 10, fill: 'var(--muted-foreground)' }} axisLine={false} tickLine={false} />
                      <Tooltip />
                      <Bar dataKey="gap_signals" fill="#f59e0b" radius={[0, 3, 3, 0]} name="Gap Signals" />
                    </BarChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>

              {/* Region Rankings Table */}
              <Card className="border-border/30 bg-card/50">
                <CardHeader className="pb-1">
                  <CardTitle className="text-sm">Region Rankings</CardTitle>
                </CardHeader>
                <CardContent className="max-h-[300px] overflow-y-auto">
                  <Table>
                    <TableHeader>
                      <TableRow className="border-border/30">
                        <TableHead className="text-xs">Region</TableHead>
                        <TableHead className="text-xs text-right">Gaps</TableHead>
                        <TableHead className="text-xs text-right">Rate</TableHead>
                        <TableHead className="text-xs">Dominant Gap</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {regions.map((r: any, i: number) => (
                        <TableRow key={i} className="border-border/20">
                          <TableCell className="text-xs font-medium truncate max-w-[100px]" title={r.district || r.state}>
                            {r.district || r.state}
                          </TableCell>
                          <TableCell className="text-xs text-right text-amber-500">{r.gap_signals}</TableCell>
                          <TableCell className="text-xs text-right">
                            <span className={r.gap_rate > 70 ? "text-red-400" : r.gap_rate > 50 ? "text-orange-400" : "text-green-400"}>
                              {r.gap_rate}%
                            </span>
                          </TableCell>
                          <TableCell className="text-[10px] text-muted-foreground truncate max-w-[80px]" title={r.dominant_gap_type}>
                            {r.dominant_gap_type || "—"}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </CardContent>
              </Card>
            </div>
          </div>
        )}
      </div>
    </AppShell>
  );
}
