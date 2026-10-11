"use client";
import React, { useEffect, useState, useCallback, useRef } from "react";
import AppShell from "@/components/AppShell";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { api } from "@/lib/api";
import {
  Radio, Globe, Zap, Play, Square, RefreshCw,
  AlertTriangle, CheckCircle, Loader2, ArrowRight
} from "lucide-react";

export default function LiveDashboardPage() {
  const [overview, setOverview] = useState<any>(null);
  const [feed, setFeed] = useState<any>(null);
  const [workerStatus, setWorkerStatus] = useState<any>(null);
  const [sources, setSources] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const pollRef = useRef<NodeJS.Timeout | null>(null);

  const fetchData = useCallback(async () => {
    try {
      const [ov, fd, ws, src] = await Promise.all([
        api.get("/api/collection/overview"),
        api.get("/api/collection/live-feed"),
        api.get("/api/collection/worker-status"),
        api.get("/api/sources"),
      ]);
      setOverview(ov);
      setFeed(fd);
      setWorkerStatus(ws);
      setSources(src);
    } catch (e) {
      console.error("Live dashboard fetch error", e);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
    // Auto-refresh every 5 seconds for live feel
    pollRef.current = setInterval(fetchData, 5000);
    return () => { if (pollRef.current) clearInterval(pollRef.current); };
  }, [fetchData]);

  const toggleAutopilot = async (enable: boolean) => {
    await api.post(`/api/collection/toggle-autopilot?enable=${enable}`);
    fetchData();
  };

  const startScrapeAll = async () => {
    try {
      await api.post("/api/sources/scrape-all?max_records=50");
      fetchData();
    } catch (e) {
      console.error("Scrape all failed", e);
    }
  };

  const activeSources = sources.filter(s => s.active);
  const isRunning = workerStatus?.status === "running";

  // Recent gap signals from live feed
  const recentGapSignals = (feed?.recent_documents || []).filter((d: any) => 
    d.gap && d.gap.toLowerCase() === "yes"
  );

  return (
    <AppShell>
      <div className="p-6 space-y-6 max-w-[1400px] mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-bold flex items-center gap-2">
                <Radio className={`w-6 h-6 ${isRunning ? "text-red-400 animate-pulse" : "text-muted-foreground"}`} />
                Live Scraping Intelligence
              </h1>
              <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-red-500/15 text-red-400 border border-red-500/20">LIVE DATA</span>
            </div>
            <p className="text-sm text-muted-foreground mt-0.5">
              Real-time collection from public sources — what the system is discovering right now
            </p>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={startScrapeAll}
              className="flex items-center gap-2 px-4 py-2 text-xs rounded-lg bg-amber-500 hover:bg-amber-600 text-black font-medium transition-colors"
            >
              <Play className="w-3.5 h-3.5" />
              Scrape All Sources
            </button>
            <button
              onClick={() => toggleAutopilot(!workerStatus?.auto_pilot_enabled)}
              className={`flex items-center gap-2 px-4 py-2 text-xs rounded-lg border font-medium transition-colors ${
                workerStatus?.auto_pilot_enabled
                  ? "border-red-500/30 bg-red-500/10 text-red-400 hover:bg-red-500/20"
                  : "border-emerald-500/30 bg-emerald-500/10 text-emerald-400 hover:bg-emerald-500/20"
              }`}
            >
              {workerStatus?.auto_pilot_enabled ? <Square className="w-3.5 h-3.5" /> : <Play className="w-3.5 h-3.5" />}
              {workerStatus?.auto_pilot_enabled ? "Stop Autopilot" : "Start Autopilot"}
            </button>
          </div>
        </div>

        {loading ? (
          <div className="grid grid-cols-2 lg:grid-cols-5 gap-3">
            {Array.from({ length: 5 }).map((_, i) => (
              <Card key={i} className="animate-pulse border-border/30"><CardContent className="p-5 h-20" /></Card>
            ))}
          </div>
        ) : (
          <>
            {/* Live KPIs */}
            <div className="grid grid-cols-2 lg:grid-cols-5 gap-3">
              {[
                { label: "Active Sources", value: overview?.active_sources || 0, icon: Globe },
                { label: "URLs Discovered", value: overview?.total_urls_discovered || 0, icon: ArrowRight },
                { label: "Pages Collected", value: overview?.total_pages_collected || 0, icon: CheckCircle },
                { label: "Records Extracted", value: overview?.total_documents || 0, icon: Zap },
                { label: "Active Campaigns", value: overview?.total_campaigns || 0, icon: Radio },
              ].map((kpi) => (
                <Card key={kpi.label} className="border-border/30 bg-card/50">
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-xs text-muted-foreground">{kpi.label}</p>
                        <p className="text-xl font-bold">{kpi.value}</p>
                      </div>
                      <kpi.icon className="w-5 h-5 text-muted-foreground" />
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>

            {/* Collection Pipeline Funnel */}
            {overview && (
              <Card className="border-border/30 bg-card/50">
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm">Collection Pipeline</CardTitle>
                  <CardDescription className="text-xs">Source → URLs → Pages → Records → Questions → Gap Signals</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="flex items-center justify-between gap-2 py-2">
                    {[
                      { label: "Sources", value: overview.active_sources, color: "bg-blue-500" },
                      { label: "URLs", value: overview.total_urls_discovered, color: "bg-cyan-500" },
                      { label: "Pages", value: overview.total_pages_collected, color: "bg-emerald-500" },
                      { label: "Records", value: overview.total_documents, color: "bg-amber-500" },
                    ].map((stage, i) => (
                      <React.Fragment key={stage.label}>
                        <div className="flex-1 text-center">
                          <div className={`w-12 h-12 mx-auto rounded-xl ${stage.color}/15 flex items-center justify-center mb-1`}>
                            <span className="text-sm font-bold">{stage.value}</span>
                          </div>
                          <p className="text-[10px] text-muted-foreground">{stage.label}</p>
                        </div>
                        {i < 3 && <ArrowRight className="w-4 h-4 text-muted-foreground/40 shrink-0" />}
                      </React.Fragment>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              {/* Live Gap Signal Stream (Mini) */}
              <Card className="border-border/30 bg-card/50">
                <CardHeader className="pb-2">
                  <div className="flex items-center gap-2">
                    <CardTitle className="text-sm">Recent Gap Signals</CardTitle>
                    {isRunning && <span className="w-2 h-2 rounded-full bg-red-400 animate-pulse" />}
                  </div>
                  <CardDescription className="text-xs">Latest awareness gap signals discovered from live sources</CardDescription>
                </CardHeader>
                <CardContent className="space-y-2 max-h-[350px] overflow-y-auto">
                  {recentGapSignals.length === 0 ? (
                    <p className="text-xs text-muted-foreground text-center py-8">No gap signals detected yet. Start scraping to discover new signals.</p>
                  ) : (
                    recentGapSignals.slice(0, 8).map((doc: any, i: number) => (
                      <div key={i} className="p-3 rounded-lg bg-secondary/50 border border-amber-500/10 animate-in fade-in slide-in-from-left-2">
                        <p className="text-xs text-foreground/90 line-clamp-2">&ldquo;{doc.text}&rdquo;</p>
                        <div className="flex flex-wrap gap-1.5 mt-2">
                          {doc.scheme && <span className="text-[9px] px-1.5 py-0.5 rounded bg-amber-500/10 text-amber-500">{doc.scheme}</span>}
                          {doc.gap_type && <span className="text-[9px] px-1.5 py-0.5 rounded bg-purple-500/10 text-purple-400">{doc.gap_type}</span>}
                          {doc.state && <span className="text-[9px] px-1.5 py-0.5 rounded bg-blue-500/10 text-blue-400">{doc.state}</span>}
                          {doc.source && <span className="text-[9px] px-1.5 py-0.5 rounded bg-slate-500/10 text-muted-foreground">{doc.source}</span>}
                        </div>
                      </div>
                    ))
                  )}
                </CardContent>
              </Card>

              {/* Recent URLs */}
              <Card className="border-border/30 bg-card/50">
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm">Recent Scraping Activity</CardTitle>
                  <CardDescription className="text-xs">Latest URLs processed by the scraper</CardDescription>
                </CardHeader>
                <CardContent className="max-h-[350px] overflow-y-auto">
                  <Table>
                    <TableHeader>
                      <TableRow className="border-border/30">
                        <TableHead className="text-xs">URL</TableHead>
                        <TableHead className="text-xs text-right">Status</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {(feed?.recent_urls || []).map((u: any, i: number) => (
                        <TableRow key={i} className="border-border/20">
                          <TableCell className="text-xs text-muted-foreground truncate max-w-[300px]" title={u.url}>
                            {u.url}
                          </TableCell>
                          <TableCell className="text-xs text-right">
                            <span className={`px-1.5 py-0.5 rounded text-[10px] ${
                              u.status === "success" ? "bg-emerald-500/10 text-emerald-400" :
                              u.status === "failed" ? "bg-red-500/10 text-red-400" :
                              "bg-blue-500/10 text-blue-400"
                            }`}>
                              {u.status}
                            </span>
                          </TableCell>
                        </TableRow>
                      ))}
                      {(!feed?.recent_urls || feed.recent_urls.length === 0) && (
                        <TableRow>
                          <TableCell colSpan={2} className="text-xs text-muted-foreground text-center py-8">
                            No scraping activity yet
                          </TableCell>
                        </TableRow>
                      )}
                    </TableBody>
                  </Table>
                </CardContent>
              </Card>
            </div>

            {/* Source Registry Summary */}
            <Card className="border-border/30 bg-card/50">
              <CardHeader className="pb-2">
                <CardTitle className="text-sm">Active Source Registry</CardTitle>
                <CardDescription className="text-xs">{activeSources.length} active sources out of {sources.length} registered</CardDescription>
              </CardHeader>
              <CardContent className="max-h-[300px] overflow-y-auto">
                <Table>
                  <TableHeader>
                    <TableRow className="border-border/30">
                      <TableHead className="text-xs">Source</TableHead>
                      <TableHead className="text-xs">Type</TableHead>
                      <TableHead className="text-xs">Policy</TableHead>
                      <TableHead className="text-xs text-right">Records</TableHead>
                      <TableHead className="text-xs text-right">Runs</TableHead>
                      <TableHead className="text-xs text-right">Status</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {sources.slice(0, 20).map((s: any) => (
                      <TableRow key={s.id} className="border-border/20">
                        <TableCell className="text-xs font-medium truncate max-w-[200px]" title={s.name}>{s.name}</TableCell>
                        <TableCell className="text-[10px] text-muted-foreground">{s.source_type}</TableCell>
                        <TableCell className="text-[10px]">
                          <span className={s.policy_status === "allowed" ? "text-emerald-400" : s.policy_status === "blocked" ? "text-red-400" : "text-muted-foreground"}>
                            {s.policy_status || "unknown"}
                          </span>
                        </TableCell>
                        <TableCell className="text-xs text-right">{s.total_records_collected}</TableCell>
                        <TableCell className="text-xs text-right text-muted-foreground">{s.total_runs}</TableCell>
                        <TableCell className="text-xs text-right">
                          <span className={`w-2 h-2 rounded-full inline-block ${s.active ? "bg-emerald-400" : "bg-muted-foreground/30"}`} />
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
