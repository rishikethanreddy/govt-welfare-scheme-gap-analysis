"use client";
import React, { useEffect, useState } from "react";
import AppShell from "@/components/AppShell";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { api } from "@/lib/api";
import { Activity, CheckCircle, XCircle, Database, Cpu, Clock, AlertTriangle, RefreshCw } from "lucide-react";

export default function SystemPage() {
  const [health, setHealth] = useState<any>(null);
  const [logs, setLogs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const load = () => {
    setLoading(true);
    Promise.all([api.systemHealth(), api.auditLogs(30)])
      .then(([h, l]) => { setHealth(h); setLogs(l); })
      .catch(() => {})
      .finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, []);

  const StatusBadge = ({ ok }: { ok: boolean }) => ok
    ? <CheckCircle className="w-4 h-4 text-green-400" />
    : <XCircle className="w-4 h-4 text-red-400" />;

  return (
    <AppShell>
      <div className="p-6 space-y-6 max-w-[1200px] mx-auto">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold">System Health</h1>
            <p className="text-sm text-muted-foreground mt-0.5">Infrastructure and operational monitoring</p>
          </div>
          <button onClick={load} className="flex items-center gap-2 px-3 py-2 text-xs rounded-lg border border-border/40 bg-white/5 hover:bg-white/10 text-muted-foreground">
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} /> Refresh
          </button>
        </div>

        {health && (
          <>
            {/* Status Cards */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              {[
                { label: "API", status: health.api_status === "healthy", value: health.api_status, icon: Activity },
                { label: "Database", status: health.database_status === "connected", value: `${health.database_type} — ${health.database_status}`, icon: Database },
                { label: "Documents", status: health.total_documents > 0, value: health.total_documents?.toLocaleString(), icon: Database },
                { label: "Active Jobs", status: health.active_jobs === 0, value: health.active_jobs, icon: Cpu },
              ].map(({ label, status, value, icon: Icon }) => (
                <Card key={label} className="border-border/30 bg-card/50">
                  <CardContent className="p-4 flex items-center gap-3">
                    <div className="w-10 h-10 rounded-xl bg-white/5 flex items-center justify-center">
                      <Icon className="w-5 h-5 text-muted-foreground" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between">
                        <p className="text-xs text-muted-foreground">{label}</p>
                        <StatusBadge ok={status} />
                      </div>
                      <p className="text-sm font-medium truncate">{value}</p>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>

            {/* Failed Jobs Warning */}
            {health.failed_jobs_24h > 0 && (
              <div className="p-3 rounded-lg border border-amber-500/30 bg-amber-500/5 flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 text-amber-400" />
                <p className="text-xs text-amber-400">{health.failed_jobs_24h} failed jobs in the last 24 hours</p>
              </div>
            )}
          </>
        )}

        {/* Audit Logs */}
        <Card className="border-border/30 bg-card/50">
          <CardHeader><CardTitle className="text-sm">Recent Audit Logs</CardTitle></CardHeader>
          <CardContent className="space-y-1">
            {logs.length === 0 ? (
              <p className="text-xs text-muted-foreground py-4 text-center">No audit logs yet</p>
            ) : (
              logs.map((log) => (
                <div key={log.id} className="flex items-start gap-3 p-2.5 rounded-lg hover:bg-white/[0.02] transition-colors">
                  <div className={`w-2 h-2 rounded-full mt-1.5 shrink-0 ${
                    log.severity === "error" ? "bg-red-400" :
                    log.severity === "warning" ? "bg-amber-400" :
                    "bg-green-400"
                  }`} />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="text-[10px] px-2 py-0.5 rounded-full bg-white/5 text-muted-foreground">{log.action}</span>
                      {log.entity_type && <span className="text-[10px] text-muted-foreground">{log.entity_type}#{log.entity_id}</span>}
                    </div>
                    <p className="text-xs text-foreground/80 mt-0.5">{log.description}</p>
                    <p className="text-[10px] text-muted-foreground mt-0.5">
                      <Clock className="w-3 h-3 inline mr-1" />
                      {log.created_at ? new Date(log.created_at).toLocaleString() : "—"}
                    </p>
                  </div>
                </div>
              ))
            )}
          </CardContent>
        </Card>
      </div>
    </AppShell>
  );
}
