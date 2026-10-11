"use client";
import React, { useEffect, useState } from "react";
import AppShell from "@/components/AppShell";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { api } from "@/lib/api";
import { Activity, Play, Plus, Loader2, RefreshCw } from "lucide-react";

export default function LiveCampaignsPage() {
  const [campaigns, setCampaigns] = useState<any[]>([]);
  const [funnel, setFunnel] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [running, setRunning] = useState<number | null>(null);

  const fetchData = async () => {
    try {
      const [c, f] = await Promise.all([
        api.get("/api/collection/campaigns"),
        api.get("/api/collection/funnel"),
      ]);
      setCampaigns(c);
      setFunnel(f);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchData(); }, []);

  const createCampaign = async () => {
    setCreating(true);
    try {
      await api.post("/api/collection/campaigns?name=Auto Campaign&max_urls=5000&max_depth=3");
      await fetchData();
    } catch (e) {
      console.error(e);
    } finally {
      setCreating(false);
    }
  };

  const runCampaign = async (id: number) => {
    setRunning(id);
    try {
      await api.post(`/api/collection/campaigns/${id}/run-async`);
      await fetchData();
    } catch (e) {
      console.error(e);
    } finally {
      setRunning(null);
    }
  };

  return (
    <AppShell>
      <div className="p-6 space-y-6 max-w-[1400px] mx-auto">
        <div className="flex items-center justify-between">
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-bold flex items-center gap-2">
                <Activity className="w-6 h-6 text-cyan-400" />
                Collection Campaigns
              </h1>
              <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-red-500/15 text-red-400 border border-red-500/20">LIVE DATA</span>
            </div>
            <p className="text-sm text-muted-foreground mt-0.5">
              Manage and monitor large-scale collection campaigns
            </p>
          </div>
          <div className="flex gap-2">
            <button
              onClick={createCampaign}
              disabled={creating}
              className="flex items-center gap-2 px-4 py-2 text-xs rounded-lg bg-amber-500 hover:bg-amber-600 text-black font-medium disabled:opacity-50 transition-colors"
            >
              {creating ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Plus className="w-3.5 h-3.5" />}
              New Campaign
            </button>
            <button onClick={fetchData} className="flex items-center gap-2 px-3 py-2 text-xs rounded-lg border border-border/40 bg-secondary hover:bg-secondary/80 text-muted-foreground transition-colors">
              <RefreshCw className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>

        {/* Pipeline Funnel */}
        {funnel && (
          <Card className="border-border/30 bg-card/50">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm">Global Pipeline Funnel</CardTitle>
              <CardDescription className="text-xs">Where records are gained or lost across all campaigns</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-5 gap-2">
                {(funnel.funnel || []).map((stage: any) => (
                  <div
                    key={stage.stage}
                    className={`p-3 rounded-lg border text-center ${
                      stage.highlight ? "border-amber-500/30 bg-amber-500/5" :
                      stage.delta ? "border-red-500/20 bg-red-500/5" : "border-border/20 bg-secondary/30"
                    }`}
                  >
                    <p className={`text-lg font-bold ${stage.highlight ? "text-amber-500" : stage.delta ? "text-red-400" : ""}`}>
                      {stage.count}
                    </p>
                    <p className="text-[10px] text-muted-foreground">{stage.stage}</p>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Campaigns Table */}
        {loading ? (
          <Card className="h-60 animate-pulse border-border/30" />
        ) : (
          <Card className="border-border/30 bg-card/50">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm">Campaigns ({campaigns.length})</CardTitle>
            </CardHeader>
            <CardContent>
              {campaigns.length === 0 ? (
                <p className="text-xs text-muted-foreground text-center py-12">No campaigns created yet. Click &quot;New Campaign&quot; to start.</p>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow className="border-border/30">
                      <TableHead className="text-xs">Name</TableHead>
                      <TableHead className="text-xs">Status</TableHead>
                      <TableHead className="text-xs text-right">URLs</TableHead>
                      <TableHead className="text-xs text-right">Pages</TableHead>
                      <TableHead className="text-xs text-right">Records</TableHead>
                      <TableHead className="text-xs text-right">Final</TableHead>
                      <TableHead className="text-xs text-center">Action</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {campaigns.map((c) => (
                      <TableRow key={c.id} className="border-border/20">
                        <TableCell className="text-xs font-medium">{c.name}</TableCell>
                        <TableCell className="text-xs">
                          <span className={`px-1.5 py-0.5 rounded text-[10px] ${
                            c.status === "completed" ? "bg-emerald-500/10 text-emerald-400" :
                            c.status === "failed" ? "bg-red-500/10 text-red-400" :
                            ["pending","discovering","collecting"].includes(c.status) ? "bg-amber-500/10 text-amber-500" :
                            "bg-secondary text-muted-foreground"
                          }`}>
                            {c.status}
                          </span>
                        </TableCell>
                        <TableCell className="text-xs text-right">{c.urls_discovered || 0}</TableCell>
                        <TableCell className="text-xs text-right">{c.pages_downloaded || 0}</TableCell>
                        <TableCell className="text-xs text-right">{c.records_extracted || 0}</TableCell>
                        <TableCell className="text-xs text-right font-medium text-amber-500">{c.records_final || 0}</TableCell>
                        <TableCell className="text-center">
                          <button
                            onClick={() => runCampaign(c.id)}
                            disabled={running === c.id || ["collecting", "discovering", "pending"].includes(c.status)}
                            className="p-1 rounded hover:bg-secondary transition-colors disabled:opacity-30"
                          >
                            {running === c.id ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Play className="w-3.5 h-3.5 text-amber-500" />}
                          </button>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        )}
      </div>
    </AppShell>
  );
}
