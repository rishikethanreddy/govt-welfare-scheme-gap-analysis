"use client";
import React, { useEffect, useState } from "react";
import AppShell from "@/components/AppShell";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { api } from "@/lib/api";
import { Globe, Play, ToggleLeft, ToggleRight, CheckCircle, AlertTriangle, RefreshCw, Loader2 } from "lucide-react";

export default function LiveSourcesPage() {
  const [sources, setSources] = useState<any[]>([]);
  const [registry, setRegistry] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [registering, setRegistering] = useState(false);
  const [scraping, setScraping] = useState<number | null>(null);

  const fetchSources = async () => {
    try {
      const [src, reg] = await Promise.all([
        api.get("/api/sources"),
        api.get("/api/collection/source-registry"),
      ]);
      setSources(src);
      setRegistry(reg);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchSources(); }, []);

  const registerAll = async () => {
    setRegistering(true);
    try {
      await api.post("/api/collection/register-all-sources");
      await fetchSources();
    } catch (e) {
      console.error(e);
    } finally {
      setRegistering(false);
    }
  };

  const toggleSource = async (id: number) => {
    try {
      await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/sources/${id}/toggle`, { method: 'PATCH' });
      await fetchSources();
    } catch (e) {
      console.error(e);
    }
  };

  const scrapeSource = async (id: number) => {
    setScraping(id);
    try {
      await api.post(`/api/sources/${id}/scrape?max_records=50`);
      await fetchSources();
    } catch (e) {
      console.error(e);
    } finally {
      setScraping(null);
    }
  };

  const activeSources = sources.filter(s => s.active);

  return (
    <AppShell>
      <div className="p-6 space-y-6 max-w-[1400px] mx-auto">
        <div className="flex items-center justify-between">
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-bold flex items-center gap-2">
                <Globe className="w-6 h-6 text-blue-400" />
                Source Registry
              </h1>
              <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-red-500/15 text-red-400 border border-red-500/20">LIVE DATA</span>
            </div>
            <p className="text-sm text-muted-foreground mt-0.5">
              {activeSources.length} active sources · {sources.length} registered · {registry?.total_sources || 0} available
            </p>
          </div>
          <div className="flex gap-2">
            <button
              onClick={registerAll}
              disabled={registering}
              className="flex items-center gap-2 px-4 py-2 text-xs rounded-lg bg-blue-500 hover:bg-blue-600 text-white font-medium disabled:opacity-50 transition-colors"
            >
              {registering ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Globe className="w-3.5 h-3.5" />}
              Register All Sources
            </button>
            <button
              onClick={fetchSources}
              className="flex items-center gap-2 px-3 py-2 text-xs rounded-lg border border-border/40 bg-secondary hover:bg-secondary/80 text-muted-foreground transition-colors"
            >
              <RefreshCw className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>

        {loading ? (
          <Card className="h-96 animate-pulse border-border/30" />
        ) : (
          <>
            {/* Sources by category from registry */}
            {registry && Object.entries(registry.categories || {}).length > 0 && sources.length === 0 && (
              <Card className="border-border/30 bg-card/50">
                <CardHeader>
                  <CardTitle className="text-sm">Available Source Categories</CardTitle>
                  <CardDescription className="text-xs">Click &quot;Register All Sources&quot; to activate these</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                    {Object.entries(registry.categories as Record<string, any[]>).map(([cat, items]) => (
                      <div key={cat} className="p-3 rounded-lg bg-secondary/50 border border-border/20">
                        <p className="text-xs font-medium capitalize">{cat}</p>
                        <p className="text-lg font-bold">{items.length}</p>
                        <p className="text-[10px] text-muted-foreground">sources</p>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Registered Sources Table */}
            {sources.length > 0 && (
              <Card className="border-border/30 bg-card/50">
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm">Registered Sources ({sources.length})</CardTitle>
                  <CardDescription className="text-xs">Click play to scrape individual sources, or toggle to enable/disable</CardDescription>
                </CardHeader>
                <CardContent className="max-h-[600px] overflow-y-auto">
                  <Table>
                    <TableHeader>
                      <TableRow className="border-border/30">
                        <TableHead className="text-xs">Source</TableHead>
                        <TableHead className="text-xs">URL</TableHead>
                        <TableHead className="text-xs">Type</TableHead>
                        <TableHead className="text-xs">Policy</TableHead>
                        <TableHead className="text-xs text-right">Records</TableHead>
                        <TableHead className="text-xs text-right">Runs</TableHead>
                        <TableHead className="text-xs text-center">Actions</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {sources.map((s) => (
                        <TableRow key={s.id} className={`border-border/20 ${!s.active ? "opacity-50" : ""}`}>
                          <TableCell className="text-xs font-medium max-w-[180px] truncate" title={s.name}>{s.name}</TableCell>
                          <TableCell className="text-[10px] text-muted-foreground max-w-[200px] truncate" title={s.url}>{s.url}</TableCell>
                          <TableCell className="text-[10px] text-muted-foreground">{s.source_type}</TableCell>
                          <TableCell className="text-[10px]">
                            <span className={
                              s.policy_status === "allowed" ? "text-emerald-400" :
                              s.policy_status === "blocked" ? "text-red-400" : "text-muted-foreground"
                            }>
                              {s.policy_status || "—"}
                            </span>
                          </TableCell>
                          <TableCell className="text-xs text-right">{s.total_records_collected}</TableCell>
                          <TableCell className="text-xs text-right text-muted-foreground">{s.total_runs}</TableCell>
                          <TableCell className="text-center">
                            <div className="flex items-center justify-center gap-1">
                              <button
                                onClick={() => scrapeSource(s.id)}
                                disabled={scraping === s.id || !s.active}
                                className="p-1 rounded hover:bg-secondary transition-colors disabled:opacity-30"
                                title="Scrape this source"
                              >
                                {scraping === s.id ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Play className="w-3.5 h-3.5 text-amber-500" />}
                              </button>
                              <button
                                onClick={() => toggleSource(s.id)}
                                className="p-1 rounded hover:bg-secondary transition-colors"
                                title={s.active ? "Disable" : "Enable"}
                              >
                                {s.active ? <ToggleRight className="w-4 h-4 text-emerald-400" /> : <ToggleLeft className="w-4 h-4 text-muted-foreground" />}
                              </button>
                            </div>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </CardContent>
              </Card>
            )}
          </>
        )}
      </div>
    </AppShell>
  );
}
