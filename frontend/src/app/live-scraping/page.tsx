"use client";
import React, { useEffect, useState } from "react";
import AppShell from "@/components/AppShell";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Activity, Power, PowerOff, RefreshCw, Radio, Server, FileText, Link as LinkIcon, CheckCircle2, XCircle } from "lucide-react";
import { api } from "@/lib/api";

export default function LiveScrapingPage() {
  const [feed, setFeed] = useState<any>({ recent_urls: [], recent_documents: [], active_campaigns: [] });
  const [status, setStatus] = useState<any>({ auto_pilot_enabled: false, active_campaigns: 0, status: 'idle' });
  const [loading, setLoading] = useState(true);

  const fetchStatusAndFeed = async () => {
    try {
      const [feedData, statusData] = await Promise.all([
        api.get("/api/collection/live-feed"),
        api.get("/api/collection/worker-status")
      ]);
      setFeed(feedData);
      setStatus(statusData);
    } catch (e) {
      console.error("Failed to fetch live feed", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStatusAndFeed();
    // Poll every 3 seconds
    const interval = setInterval(fetchStatusAndFeed, 3000);
    return () => clearInterval(interval);
  }, []);

  const toggleAutoPilot = async () => {
    const newState = !status.auto_pilot_enabled;
    // optimistic update
    setStatus({ ...status, auto_pilot_enabled: newState });
    try {
      await api.post(`/api/collection/toggle-autopilot?enable=${newState}`);
      fetchStatusAndFeed();
    } catch (e) {
      console.error(e);
      // revert on fail
      setStatus({ ...status, auto_pilot_enabled: !newState });
    }
  };

  const getStatusColor = (s: string) => {
    switch (s) {
      case "success": return "text-green-400";
      case "failed": return "text-red-400";
      case "queued": return "text-blue-400";
      case "collecting": return "text-amber-400";
      default: return "text-muted-foreground";
    }
  };

  return (
    <AppShell>
      <div className="p-6 space-y-6 max-w-[1400px] mx-auto">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold flex items-center gap-2">
              <Radio className="w-6 h-6 text-amber-500 animate-pulse" />
              Live Scraping Feed
            </h1>
            <p className="text-sm text-muted-foreground mt-0.5">Real-time monitoring of continuous collection</p>
          </div>
          
          <div className="flex items-center gap-3">
            <div className={`px-3 py-1.5 rounded-md text-xs font-medium flex items-center gap-2 border ${status.status === 'running' ? 'bg-amber-500/10 border-amber-500/30 text-amber-500' : 'bg-muted border-border text-muted-foreground'}`}>
              <Server className="w-3.5 h-3.5" />
              Worker: {status.status.toUpperCase()}
            </div>
            
            <button
              onClick={toggleAutoPilot}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                status.auto_pilot_enabled 
                  ? "bg-red-500/20 text-red-500 hover:bg-red-500/30 border border-red-500/50"
                  : "bg-green-500/20 text-green-500 hover:bg-green-500/30 border border-green-500/50"
              }`}
            >
              {status.auto_pilot_enabled ? <PowerOff className="w-4 h-4" /> : <Power className="w-4 h-4" />}
              {status.auto_pilot_enabled ? "Stop Auto-Pilot" : "Start Auto-Pilot"}
            </button>
          </div>
        </div>

        {/* Active Campaigns */}
        <Card className="border-border/30 bg-card/50">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm flex items-center gap-2">
              <Activity className="w-4 h-4 text-amber-500" /> Active Campaigns
            </CardTitle>
          </CardHeader>
          <CardContent>
            {feed.active_campaigns.length === 0 ? (
              <p className="text-sm text-muted-foreground py-4 text-center border border-dashed border-border/50 rounded-lg">
                No active campaigns. {status.auto_pilot_enabled ? "Waiting for Auto-Pilot tick..." : "Enable Auto-Pilot to automatically discover and scrape sources."}
              </p>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {feed.active_campaigns.map((c: any) => (
                  <div key={c.id} className="p-4 rounded-lg bg-background border border-border/50 space-y-3 relative overflow-hidden">
                    <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-amber-500 to-orange-600 opacity-50" />
                    <div className="flex justify-between items-start">
                      <p className="text-sm font-semibold truncate">{c.name}</p>
                      <span className="text-[10px] uppercase px-2 py-0.5 rounded-full bg-amber-500/10 text-amber-500 font-bold">
                        {c.status}
                      </span>
                    </div>
                    <div className="grid grid-cols-2 gap-2">
                      <div className="bg-card/50 p-2 rounded text-center border border-border/30">
                        <p className="text-[10px] text-muted-foreground uppercase">Discovered</p>
                        <p className="text-sm font-medium">{c.urls_discovered}</p>
                      </div>
                      <div className="bg-card/50 p-2 rounded text-center border border-border/30">
                        <p className="text-[10px] text-muted-foreground uppercase">Extracted</p>
                        <p className="text-sm font-medium text-green-400">{c.records_final}</p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Live URL Feed */}
          <Card className="border-border/30 bg-card/50 flex flex-col h-[500px]">
            <CardHeader className="pb-3 border-b border-border/30">
              <CardTitle className="text-sm flex items-center justify-between">
                <span className="flex items-center gap-2"><LinkIcon className="w-4 h-4 text-blue-400" /> URL Discovery Feed</span>
                {loading && <RefreshCw className="w-3 h-3 text-muted-foreground animate-spin" />}
              </CardTitle>
            </CardHeader>
            <CardContent className="p-0 flex-1 overflow-auto">
              <Table>
                <TableHeader className="bg-card/50 sticky top-0">
                  <TableRow className="border-border/30">
                    <TableHead className="text-xs">Time</TableHead>
                    <TableHead className="text-xs">URL</TableHead>
                    <TableHead className="text-xs text-right">Status</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {feed.recent_urls.map((u: any, i: number) => (
                    <TableRow key={i} className="border-border/10">
                      <TableCell className="text-[10px] text-muted-foreground whitespace-nowrap">
                        {new Date(u.time).toLocaleTimeString()}
                      </TableCell>
                      <TableCell className="text-xs font-mono max-w-[200px] truncate opacity-80" title={u.url}>
                        {u.url.replace(/^https?:\/\/(www\.)?/, '')}
                      </TableCell>
                      <TableCell className={`text-[10px] font-bold text-right uppercase ${getStatusColor(u.status)}`}>
                        {u.status}
                      </TableCell>
                    </TableRow>
                  ))}
                  {feed.recent_urls.length === 0 && !loading && (
                    <TableRow>
                      <TableCell colSpan={3} className="text-center text-xs text-muted-foreground py-8">
                        No recent URLs
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </CardContent>
          </Card>

          {/* Live Documents Feed */}
          <Card className="border-border/30 bg-card/50 flex flex-col h-[500px]">
            <CardHeader className="pb-3 border-b border-border/30">
              <CardTitle className="text-sm flex items-center justify-between">
                <span className="flex items-center gap-2"><FileText className="w-4 h-4 text-emerald-400" /> Records Extracted</span>
                {loading && <RefreshCw className="w-3 h-3 text-muted-foreground animate-spin" />}
              </CardTitle>
            </CardHeader>
            <CardContent className="p-0 flex-1 overflow-auto">
              <Table>
                <TableHeader className="bg-card/50 sticky top-0">
                  <TableRow className="border-border/30">
                    <TableHead className="text-xs">Time</TableHead>
                    <TableHead className="text-xs">Scheme</TableHead>
                    <TableHead className="text-xs">Intent</TableHead>
                    <TableHead className="text-xs text-right">Gap</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {feed.recent_documents.map((d: any, i: number) => (
                    <TableRow key={i} className="border-border/10">
                      <TableCell className="text-[10px] text-muted-foreground whitespace-nowrap">
                        {new Date(d.time).toLocaleTimeString()}
                      </TableCell>
                      <TableCell className="text-xs max-w-[150px] truncate font-medium">
                        {d.scheme || "General"}
                      </TableCell>
                      <TableCell className="text-xs">
                        <span className="px-1.5 py-0.5 bg-secondary text-secondary-foreground rounded text-[10px]">
                          {d.intent}
                        </span>
                      </TableCell>
                      <TableCell className="text-right">
                        {d.gap?.toLowerCase() === 'yes' ? (
                          <XCircle className="w-3 h-3 text-red-500 inline" />
                        ) : (
                          <CheckCircle2 className="w-3 h-3 text-green-500 inline" />
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                  {feed.recent_documents.length === 0 && !loading && (
                    <TableRow>
                      <TableCell colSpan={4} className="text-center text-xs text-muted-foreground py-8">
                        No recent records
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </div>
      </div>
    </AppShell>
  );
}
