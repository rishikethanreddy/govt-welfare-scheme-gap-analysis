"use client";
import React, { useEffect, useState, useCallback, useRef } from "react";
import AppShell from "@/components/AppShell";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { api } from "@/lib/api";
import { Zap, Radio, MapPin, Shield, AlertTriangle } from "lucide-react";

interface GapSignal {
  text: string;
  scheme: string | null;
  state: string | null;
  district: string | null;
  intent: string | null;
  gap: string | null;
  gap_type: string | null;
  source: string | null;
  time: string | null;
}

export default function LiveStreamPage() {
  const [signals, setSignals] = useState<GapSignal[]>([]);
  const [allDocs, setAllDocs] = useState<GapSignal[]>([]);
  const [globalStats, setGlobalStats] = useState({ total_documents: 0, total_gaps: 0 });
  const [isPolling, setIsPolling] = useState(true);
  const seenTextsRef = useRef<Set<string>>(new Set());
  const pollRef = useRef<NodeJS.Timeout | null>(null);

  const fetchFeed = useCallback(async () => {
    try {
      const data = await api.get("/api/collection/live-feed");
      
      if (data.stats) {
        setGlobalStats(data.stats);
      }

      const docs: GapSignal[] = data.recent_documents || [];
      
      // Find new items we haven't seen
      const newDocs: GapSignal[] = [];
      docs.forEach((doc) => {
        const key = (doc.text || "").slice(0, 80);
        if (key && !seenTextsRef.current.has(key)) {
          seenTextsRef.current.add(key);
          newDocs.push(doc);
        }
      });

      if (newDocs.length > 0) {
        setAllDocs(prev => [...newDocs, ...prev].slice(0, 100));
        // Only gap signals
        const gapDocs = newDocs.filter(d => d.gap && d.gap.toLowerCase() === "yes");
        if (gapDocs.length > 0) {
          setSignals(prev => [...gapDocs, ...prev].slice(0, 50));
        }
      }
    } catch (e) {
      console.error("Live stream fetch error", e);
    }
  }, []);

  useEffect(() => {
    fetchFeed();
    if (isPolling) {
      pollRef.current = setInterval(fetchFeed, 3000);
    }
    return () => { if (pollRef.current) clearInterval(pollRef.current); };
  }, [fetchFeed, isPolling]);

  const gapCount = globalStats.total_gaps;
  const totalCount = globalStats.total_documents;

  return (
    <AppShell>
      <div className="p-6 space-y-6 max-w-[1200px] mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-bold flex items-center gap-2">
                <Zap className="w-6 h-6 text-amber-500" />
                Live Awareness Gap Signals
              </h1>
              <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-red-500/15 text-red-400 border border-red-500/20">LIVE DATA</span>
              {isPolling && <span className="w-2 h-2 rounded-full bg-red-400 animate-pulse" />}
            </div>
            <p className="text-sm text-muted-foreground mt-0.5">
              Newly discovered public questions/records processed and classified in real-time
            </p>
          </div>
          <button
            onClick={() => setIsPolling(p => !p)}
            className={`flex items-center gap-2 px-4 py-2 text-xs rounded-lg border font-medium transition-colors ${
              isPolling
                ? "border-red-500/30 bg-red-500/10 text-red-400"
                : "border-emerald-500/30 bg-emerald-500/10 text-emerald-400"
            }`}
          >
            <Radio className="w-3.5 h-3.5" />
            {isPolling ? "Pause Stream" : "Resume Stream"}
          </button>
        </div>

        {/* Stream Stats */}
        <div className="grid grid-cols-3 gap-3">
          <Card className="border-border/30 bg-card/50">
            <CardContent className="p-4 text-center">
              <p className="text-2xl font-bold">{totalCount}</p>
              <p className="text-xs text-muted-foreground">Records Discovered</p>
            </CardContent>
          </Card>
          <Card className="border-border/30 bg-card/50">
            <CardContent className="p-4 text-center">
              <p className="text-2xl font-bold text-amber-500">{gapCount}</p>
              <p className="text-xs text-muted-foreground">Gap Signals Detected</p>
            </CardContent>
          </Card>
          <Card className="border-border/30 bg-card/50">
            <CardContent className="p-4 text-center">
              <p className="text-2xl font-bold text-orange-500">{totalCount > 0 ? Math.round(gapCount / totalCount * 100) : 0}%</p>
              <p className="text-xs text-muted-foreground">Live Gap Rate</p>
            </CardContent>
          </Card>
        </div>

        {/* Live Signal Stream */}
        <Card className="border-border/30 bg-card/50">
          <CardHeader className="pb-2">
            <div className="flex items-center gap-2">
              <CardTitle className="text-sm">Live Signal Feed</CardTitle>
              {isPolling && <span className="text-[10px] px-2 py-0.5 rounded-full bg-red-500/10 text-red-400 animate-pulse">● LIVE</span>}
            </div>
            <CardDescription className="text-xs">
              Questions and records being discovered, classified into Scheme → Intent → Awareness Gap → Gap Type → Region
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3 max-h-[600px] overflow-y-auto">
            {signals.length === 0 && allDocs.length === 0 && (
              <div className="text-center py-16">
                <Zap className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
                <p className="text-sm font-medium text-foreground mb-1">Waiting for new questions from configured public sources...</p>
                <p className="text-xs text-muted-foreground">
                  Genuine public queries will appear here in real-time as they are collected and processed.
                </p>
              </div>
            )}

            {/* Show all new signals in a unified stream, highlighting gaps */}
            {allDocs.map((sig, i) => {
              const isGap = sig.gap && sig.gap.toLowerCase() === "yes";
              return (
                <div
                  key={`sig-${i}`}
                  className={`p-4 rounded-xl border transition-all duration-500 animate-in fade-in slide-in-from-top-3 ${
                    isGap ? "border-amber-500/30 bg-amber-500/5" : "border-border/20 bg-secondary/30"
                  }`}
                  style={{ animationDelay: `${i * 30}ms` }}
                >
                  <div className="flex items-center gap-2 mb-2">
                    <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded animate-pulse ${
                      isGap ? "bg-amber-500/20 text-amber-500" : "bg-blue-500/20 text-blue-400"
                    }`}>
                      NEW
                    </span>
                    {sig.time && (
                      <span className="text-[9px] text-muted-foreground">
                        {new Date(sig.time).toLocaleTimeString()}
                      </span>
                    )}
                    {sig.source && (
                      <span className="text-[9px] px-1.5 py-0.5 rounded bg-slate-500/10 text-muted-foreground/80 flex items-center gap-1">
                        <Radio className="w-2.5 h-2.5" />
                        {sig.source}
                      </span>
                    )}
                  </div>
                  <p className="text-sm text-foreground leading-relaxed mb-3">
                    &ldquo;{sig.text}&rdquo;
                  </p>
                  <div className="flex flex-wrap gap-2">
                    {sig.scheme && (
                      <div className="flex items-center gap-1 text-[10px] px-2 py-1 rounded-lg bg-blue-500/10 text-blue-400">
                        <Shield className="w-3 h-3" />
                        {sig.scheme}
                      </div>
                    )}
                    {isGap ? (
                      <div className="flex items-center gap-1 text-[10px] px-2 py-1 rounded-lg bg-red-500/10 text-red-400 font-medium">
                        Awareness Gap
                      </div>
                    ) : (
                      <div className="flex items-center gap-1 text-[10px] px-2 py-1 rounded-lg bg-emerald-500/10 text-emerald-400 font-medium">
                        No Gap
                      </div>
                    )}
                    {sig.gap_type && (
                      <div className="flex items-center gap-1 text-[10px] px-2 py-1 rounded-lg bg-purple-500/10 text-purple-400">
                        <AlertTriangle className="w-3 h-3" />
                        {sig.gap_type}
                      </div>
                    )}
                    {sig.state && (
                      <div className="flex items-center gap-1 text-[10px] px-2 py-1 rounded-lg bg-emerald-500/10 text-emerald-400">
                        <MapPin className="w-3 h-3" />
                        {sig.state}{sig.district ? `, ${sig.district}` : ""}
                      </div>
                    )}
                    {sig.intent && (
                      <div className="text-[10px] px-2 py-1 rounded-lg bg-slate-500/10 text-muted-foreground">
                        {sig.intent}
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </CardContent>
        </Card>
      </div>
    </AppShell>
  );
}
