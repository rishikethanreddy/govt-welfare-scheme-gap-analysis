"use client";
import React, { useEffect, useState, useCallback } from "react";
import AppShell from "@/components/AppShell";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { api } from "@/lib/api";
import { Globe, CheckCircle, XCircle, Play, RefreshCw, Plus, Loader2, Shield } from "lucide-react";

export default function SourcesPage() {
  const [sources, setSources] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [scraping, setScraping] = useState<Record<number, boolean>>({});
  const [registering, setRegistering] = useState(false);
  const [results, setResults] = useState<Record<number, any>>({});

  const load = useCallback(() => {
    setLoading(true);
    api.sources().then(setSources).catch(() => {}).finally(() => setLoading(false));
  }, []);

  useEffect(() => { load(); }, [load]);

  const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  const registerDefaults = async () => {
    setRegistering(true);
    try {
      await fetch(`${API_BASE}/api/sources/register-defaults`, { method: "POST" });
      load();
    } catch {}
    setRegistering(false);
  };

  const runScrape = async (sourceId: number) => {
    setScraping(prev => ({ ...prev, [sourceId]: true }));
    setResults(prev => ({ ...prev, [sourceId]: null }));
    try {
      const res = await fetch(`${API_BASE}/api/sources/${sourceId}/scrape?max_records=50`, { method: "POST" });
      const data = await res.json();
      setResults(prev => ({ ...prev, [sourceId]: data }));
      load(); // refresh counts
    } catch (e: any) {
      setResults(prev => ({ ...prev, [sourceId]: { error: e.message } }));
    }
    setScraping(prev => ({ ...prev, [sourceId]: false }));
  };

  return (
    <AppShell>
      <div className="p-6 space-y-6 max-w-[1400px] mx-auto">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold">Data Sources</h1>
            <p className="text-sm text-muted-foreground mt-0.5">Registered data collection sources and scraping controls</p>
          </div>
          <div className="flex gap-2">
            <button
              onClick={registerDefaults}
              disabled={registering}
              className="flex items-center gap-2 px-3 py-2 text-xs rounded-lg border border-border/40 bg-white/5 hover:bg-white/10 text-muted-foreground disabled:opacity-40"
            >
              {registering ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Plus className="w-3.5 h-3.5" />}
              Register Defaults
            </button>
            <button onClick={load} className="flex items-center gap-2 px-3 py-2 text-xs rounded-lg border border-border/40 bg-white/5 hover:bg-white/10 text-muted-foreground">
              <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} /> Refresh
            </button>
          </div>
        </div>

        {/* Summary Cards */}
        <div className="grid grid-cols-4 gap-3">
          <Card className="border-border/30 bg-card/50">
            <CardContent className="p-4 text-center">
              <p className="text-2xl font-bold">{sources.length}</p>
              <p className="text-xs text-muted-foreground">Total Sources</p>
            </CardContent>
          </Card>
          <Card className="border-border/30 bg-card/50">
            <CardContent className="p-4 text-center">
              <p className="text-2xl font-bold text-green-400">{sources.filter(s => s.active).length}</p>
              <p className="text-xs text-muted-foreground">Active</p>
            </CardContent>
          </Card>
          <Card className="border-border/30 bg-card/50">
            <CardContent className="p-4 text-center">
              <p className="text-2xl font-bold text-amber-400">{sources.reduce((sum: number, s: any) => sum + (s.total_records_collected || 0), 0)}</p>
              <p className="text-xs text-muted-foreground">Total Scraped</p>
            </CardContent>
          </Card>
          <Card className="border-border/30 bg-card/50">
            <CardContent className="p-4 text-center">
              <p className="text-2xl font-bold text-blue-400">{sources.filter(s => s.policy_status === "allowed").length}</p>
              <p className="text-xs text-muted-foreground">Policy Allowed</p>
            </CardContent>
          </Card>
        </div>

        {/* Sources Table */}
        <Card className="border-border/30 bg-card/50">
          <CardHeader>
            <CardTitle className="text-sm">Source Registry</CardTitle>
            <CardDescription className="text-xs">All sources comply with robots.txt policies before scraping</CardDescription>
          </CardHeader>
          <CardContent>
            {loading && sources.length === 0 ? (
              <div className="animate-pulse space-y-3">
                {Array.from({ length: 3 }).map((_, i) => <div key={i} className="h-10 bg-white/5 rounded" />)}
              </div>
            ) : sources.length === 0 ? (
              <div className="text-center py-8">
                <Globe className="w-10 h-10 text-muted-foreground mx-auto mb-3" />
                <p className="text-sm text-muted-foreground">No sources registered yet.</p>
                <button onClick={registerDefaults} className="mt-3 px-4 py-2 rounded-lg bg-amber-500 hover:bg-amber-600 text-black text-xs font-medium">
                  Register Default Sources
                </button>
              </div>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow className="border-border/30">
                    <TableHead className="text-xs">Name</TableHead>
                    <TableHead className="text-xs">Type</TableHead>
                    <TableHead className="text-xs">Method</TableHead>
                    <TableHead className="text-xs">
                      <div className="flex items-center gap-1"><Shield className="w-3 h-3" /> Policy</div>
                    </TableHead>
                    <TableHead className="text-xs text-center">Active</TableHead>
                    <TableHead className="text-xs text-right">Records</TableHead>
                    <TableHead className="text-xs text-right">Runs</TableHead>
                    <TableHead className="text-xs text-center">Scrape</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {sources.map((s) => (
                    <React.Fragment key={s.id}>
                      <TableRow className="border-border/20">
                        <TableCell className="text-xs">
                          <div>
                            <span className="font-medium">{s.name}</span>
                            {s.url && (
                              <p className="text-[10px] text-muted-foreground truncate max-w-[200px]">{s.url}</p>
                            )}
                          </div>
                        </TableCell>
                        <TableCell className="text-xs">
                          <span className="px-2 py-0.5 rounded-full bg-blue-500/10 text-blue-400 text-[10px]">
                            {s.scraper_type || s.source_type}
                          </span>
                        </TableCell>
                        <TableCell className="text-xs text-muted-foreground">{s.collection_method || "manual"}</TableCell>
                        <TableCell className="text-xs">
                          <span className={`px-2 py-0.5 rounded-full text-[10px] ${
                            s.policy_status === "allowed" ? "bg-green-500/10 text-green-400" :
                            s.policy_status === "blocked" ? "bg-red-500/10 text-red-400" :
                            "bg-amber-500/10 text-amber-400"
                          }`}>
                            {s.robots_checked ? "✓ " : ""}{s.policy_status}
                          </span>
                        </TableCell>
                        <TableCell className="text-xs text-center">
                          {s.active ? <CheckCircle className="w-4 h-4 text-green-400 inline" /> : <XCircle className="w-4 h-4 text-red-400 inline" />}
                        </TableCell>
                        <TableCell className="text-xs text-right font-medium">{s.total_records_collected}</TableCell>
                        <TableCell className="text-xs text-right">{s.total_runs}</TableCell>
                        <TableCell className="text-xs text-center">
                          {s.active && s.policy_status === "allowed" && s.collection_method === "scraper" ? (
                            <button
                              onClick={() => runScrape(s.id)}
                              disabled={scraping[s.id]}
                              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-amber-500/10 hover:bg-amber-500/20 text-amber-400 text-[10px] font-medium disabled:opacity-40 transition-colors"
                            >
                              {scraping[s.id] ? <Loader2 className="w-3 h-3 animate-spin" /> : <Play className="w-3 h-3" />}
                              {scraping[s.id] ? "Running..." : "Scrape"}
                            </button>
                          ) : (
                            <span className="text-[10px] text-muted-foreground">—</span>
                          )}
                        </TableCell>
                      </TableRow>
                      {/* Inline result */}
                      {results[s.id] && (
                        <TableRow className="border-border/10">
                          <TableCell colSpan={8} className="py-1.5 px-4">
                            {results[s.id].error ? (
                              <span className="text-[10px] text-red-400">✗ {results[s.id].error}</span>
                            ) : (
                              <span className="text-[10px] text-green-400">
                                ✓ Extracted {results[s.id].records_extracted}, stored {results[s.id].records_stored},
                                {" "}{results[s.id].records_duplicate} duplicates, {results[s.id].records_rejected} rejected
                              </span>
                            )}
                          </TableCell>
                        </TableRow>
                      )}
                    </React.Fragment>
                  ))}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>

        {/* Policy disclaimer */}
        <Card className="border-border/30 bg-card/50">
          <CardContent className="p-4">
            <div className="flex items-start gap-3">
              <Shield className="w-5 h-5 text-blue-400 shrink-0 mt-0.5" />
              <p className="text-xs text-muted-foreground leading-relaxed">
                <span className="font-medium text-foreground">Ethical Scraping Policy:</span>{" "}
                All sources are checked against robots.txt before collection. Rate limiting is enforced
                per-domain based on crawl-delay directives. Sources marked &quot;blocked&quot; are never scraped.
                No authentication-gated or login-protected content is accessed.
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    </AppShell>
  );
}
