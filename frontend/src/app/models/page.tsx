"use client";
import React, { useEffect, useState } from "react";
import AppShell from "@/components/AppShell";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { api } from "@/lib/api";
import { Cpu, CheckCircle, XCircle, AlertCircle } from "lucide-react";

export default function ModelsPage() {
  const [models, setModels] = useState<any[]>([]);
  const [nlpStatus, setNlpStatus] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([api.models().catch(() => []), api.nlpStatus().catch(() => null)])
      .then(([m, s]) => { setModels(m); setNlpStatus(s); })
      .finally(() => setLoading(false));
  }, []);

  return (
    <AppShell>
      <div className="p-6 space-y-6 max-w-[1200px] mx-auto">
        <div>
          <h1 className="text-2xl font-bold">Model Registry</h1>
          <p className="text-sm text-muted-foreground mt-0.5">NLP model versions and evaluation metrics</p>
        </div>

        {/* NLP Pipeline Status */}
        <Card className="border-border/30 bg-card/50">
          <CardHeader><CardTitle className="text-sm">NLP Pipeline Status</CardTitle></CardHeader>
          <CardContent>
            {nlpStatus ? (
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                {[
                  ["Initialized", nlpStatus.initialized],
                  ["Scheme Detector", nlpStatus.scheme_detector],
                  ["Intent Classifier", nlpStatus.intent_classifier],
                  ["Gap Classifier", nlpStatus.gap_classifier],
                ].map(([label, value]) => (
                  <div key={label as string} className="flex items-center gap-2 p-3 rounded-lg bg-white/[0.02] border border-border/20">
                    {value ? <CheckCircle className="w-4 h-4 text-green-400" /> : <XCircle className="w-4 h-4 text-red-400" />}
                    <div>
                      <p className="text-xs font-medium">{label}</p>
                      <p className="text-[10px] text-muted-foreground">{value ? "Loaded" : "Not loaded"}</p>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-xs text-muted-foreground">Unable to fetch NLP status</p>
            )}
          </CardContent>
        </Card>

        {/* Model Registry Table */}
        <Card className="border-border/30 bg-card/50">
          <CardHeader><CardTitle className="text-sm">Registered Models</CardTitle></CardHeader>
          <CardContent>
            {models.length === 0 ? (
              <div className="text-center py-8">
                <Cpu className="w-10 h-10 text-muted-foreground mx-auto mb-3" />
                <p className="text-sm text-muted-foreground">No models registered yet.</p>
                <p className="text-xs text-muted-foreground mt-1">
                  Models will appear here after training and evaluation. Metrics are only shown from actual evaluations — nothing is fabricated.
                </p>
              </div>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow className="border-border/30">
                    <TableHead className="text-xs">Model</TableHead>
                    <TableHead className="text-xs">Type</TableHead>
                    <TableHead className="text-xs">Version</TableHead>
                    <TableHead className="text-xs">Status</TableHead>
                    <TableHead className="text-xs text-right">Accuracy</TableHead>
                    <TableHead className="text-xs text-right">F1</TableHead>
                    <TableHead className="text-xs text-center">Active</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {models.map((m) => (
                    <TableRow key={m.id} className="border-border/20">
                      <TableCell className="text-xs font-medium">{m.model_name}</TableCell>
                      <TableCell className="text-xs text-muted-foreground">{m.model_type}</TableCell>
                      <TableCell className="text-xs">{m.version}</TableCell>
                      <TableCell className="text-xs">
                        <span className={`px-2 py-0.5 rounded-full text-[10px] ${
                          m.status === "deployed" ? "bg-green-500/10 text-green-400" :
                          m.status === "evaluated" ? "bg-blue-500/10 text-blue-400" :
                          "bg-amber-500/10 text-amber-400"
                        }`}>{m.status}</span>
                      </TableCell>
                      <TableCell className="text-xs text-right">{m.accuracy != null ? `${(m.accuracy * 100).toFixed(1)}%` : "—"}</TableCell>
                      <TableCell className="text-xs text-right">{m.f1_score != null ? `${(m.f1_score * 100).toFixed(1)}%` : "—"}</TableCell>
                      <TableCell className="text-xs text-center">
                        {m.is_active ? <CheckCircle className="w-3.5 h-3.5 text-green-400 inline" /> : <span className="text-muted-foreground">—</span>}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>

        {/* Disclaimer */}
        <Card className="border-border/30 bg-card/50">
          <CardContent className="p-4">
            <div className="flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-blue-400 shrink-0 mt-0.5" />
              <p className="text-xs text-muted-foreground leading-relaxed">
                <span className="font-medium text-foreground">Evaluation Policy:</span> All metrics shown (accuracy, precision, recall, F1)
                are from actual evaluation runs against held-out validation data. No metrics are fabricated or estimated.
                If a model has not been formally evaluated, its metrics will show as &quot;—&quot;.
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    </AppShell>
  );
}
