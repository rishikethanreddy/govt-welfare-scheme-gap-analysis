"use client";
import React, { useEffect, useState, useCallback } from "react";
import AppShell from "@/components/AppShell";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { api } from "@/lib/api";
import { Search, ChevronLeft, ChevronRight, Eye, Download } from "lucide-react";

export default function ExplorerPage() {
  const [data, setData] = useState<any>({ items: [], total: 0, page: 1, page_size: 25, total_pages: 0 });
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState<any>(null);
  const [params, setParams] = useState<Record<string, string>>({ page: "1", page_size: "25" });
  const [search, setSearch] = useState("");
  const [selected, setSelected] = useState<any>(null);

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const p = { ...params };
      if (search) p.search = search;
      const [docs, flt] = await Promise.all([
        api.documents(p),
        !filters ? api.dashboardFilters() : Promise.resolve(filters),
      ]);
      setData(docs);
      if (!filters) setFilters(flt);
    } catch {}
    setLoading(false);
  }, [params, search, filters]);

  useEffect(() => { loadData(); }, [loadData]);

  const setParam = (key: string, value: string) => {
    setParams((prev) => {
      const next = { ...prev, page: "1" };
      if (value) next[key] = value;
      else delete next[key];
      return next;
    });
  };

  return (
    <AppShell>
      <div className="p-6 space-y-4 max-w-[1400px] mx-auto">
        <div className="flex items-center justify-between">
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-bold">Dataset Explorer</h1>
              <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-500/15 text-emerald-500 border border-emerald-500/20">ANALYZED DATASET</span>
            </div>
            <p className="text-sm text-muted-foreground mt-0.5">{data.total} records</p>
          </div>
        </div>

        {/* Search + Filters */}
        <div className="flex flex-wrap gap-2">
          <div className="relative flex-1 min-w-[200px] max-w-md">
            <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
            <input
              type="text"
              placeholder="Search records..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && loadData()}
              className="w-full pl-9 pr-3 py-2 text-xs rounded-lg border border-border/40 bg-card text-foreground placeholder:text-muted-foreground/50 focus:outline-none focus:ring-1 focus:ring-amber-500/50"
            />
          </div>
          {filters && [
            { key: "scheme", label: "Scheme", options: filters.schemes },
            { key: "state", label: "State", options: filters.states },
            { key: "intent", label: "Intent", options: filters.intents },
            { key: "awareness_gap", label: "Gap", options: ["yes", "no"] },
          ].map(({ key, label, options }) => (
            <select key={key} value={params[key] || ""} onChange={(e) => setParam(key, e.target.value)}
              className="text-xs px-3 py-2 rounded-lg border border-border/40 bg-card text-foreground min-w-[110px]">
              <option value="">All {label}s</option>
              {options?.map((o: string) => <option key={o} value={o}>{o}</option>)}
            </select>
          ))}
        </div>

        {/* Table */}
        <Card className="border-border/30 bg-card/50">
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow className="border-border/30">
                    <TableHead className="text-xs w-8">#</TableHead>
                    <TableHead className="text-xs min-w-[300px]">Text</TableHead>
                    <TableHead className="text-xs">Scheme</TableHead>
                    <TableHead className="text-xs">Intent</TableHead>
                    <TableHead className="text-xs">Gap</TableHead>
                    <TableHead className="text-xs">Gap Type</TableHead>
                    <TableHead className="text-xs">State</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {data.items.map((doc: any) => (
                    <TableRow key={doc.id} className="border-border/20 cursor-pointer hover:bg-white/[0.02]" onClick={() => setSelected(doc)}>
                      <TableCell className="text-xs text-muted-foreground">{doc.id}</TableCell>
                      <TableCell className="text-xs max-w-[400px]">
                        <p className="line-clamp-2 leading-relaxed">{doc.original_text}</p>
                      </TableCell>
                      <TableCell className="text-xs">
                        <span className="px-2 py-0.5 rounded-full bg-amber-500/10 text-amber-400 text-[10px]">{doc.scheme_name}</span>
                      </TableCell>
                      <TableCell className="text-xs text-muted-foreground">{doc.intent}</TableCell>
                      <TableCell className="text-xs">
                        <span className={`px-2 py-0.5 rounded-full text-[10px] ${doc.awareness_gap === "yes" ? "bg-red-500/10 text-red-400" : "bg-green-500/10 text-green-400"}`}>
                          {doc.awareness_gap}
                        </span>
                      </TableCell>
                      <TableCell className="text-xs text-muted-foreground">{doc.gap_type || "—"}</TableCell>
                      <TableCell className="text-xs text-muted-foreground">{doc.state || "—"}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>

            {/* Pagination */}
            <div className="flex items-center justify-between px-4 py-3 border-t border-border/20">
              <p className="text-xs text-muted-foreground">
                Page {data.page} of {data.total_pages} ({data.total} records)
              </p>
              <div className="flex gap-1">
                <button
                  disabled={data.page <= 1}
                  onClick={() => setParams((p) => ({ ...p, page: String(data.page - 1) }))}
                  className="p-1.5 rounded-lg border border-border/40 hover:bg-white/5 disabled:opacity-30 disabled:cursor-not-allowed"
                >
                  <ChevronLeft className="w-4 h-4" />
                </button>
                <button
                  disabled={data.page >= data.total_pages}
                  onClick={() => setParams((p) => ({ ...p, page: String(data.page + 1) }))}
                  className="p-1.5 rounded-lg border border-border/40 hover:bg-white/5 disabled:opacity-30 disabled:cursor-not-allowed"
                >
                  <ChevronRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Detail Panel */}
        {selected && (
          <Card className="border-border/30 bg-card/50">
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle className="text-sm">Record Detail — #{selected.id}</CardTitle>
              <button onClick={() => setSelected(null)} className="text-xs text-muted-foreground hover:text-foreground">Close</button>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <p className="text-xs font-medium text-muted-foreground mb-1">Original Text</p>
                <p className="text-sm text-foreground leading-relaxed p-3 rounded-lg bg-white/[0.02] border border-border/20">{selected.original_text}</p>
              </div>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                {[
                  ["Scheme", selected.scheme_name],
                  ["Intent", selected.intent],
                  ["Awareness Gap", selected.awareness_gap],
                  ["Gap Type", selected.gap_type],
                  ["State", selected.state],
                  ["District", selected.district],
                  ["Source Type", selected.source_type],
                  ["Confidence", selected.confidence],
                  ["Synthetic", selected.is_synthetic ? "Yes" : "No"],
                  ["Split", selected.split],
                  ["Processing", selected.processing_status],
                  ["Language", selected.language],
                ].map(([label, value]) => (
                  <div key={label as string}>
                    <p className="text-[10px] text-muted-foreground uppercase">{label}</p>
                    <p className="text-xs font-medium">{value || "—"}</p>
                  </div>
                ))}
              </div>
              {selected.notes && (
                <div>
                  <p className="text-xs font-medium text-muted-foreground mb-1">Notes</p>
                  <p className="text-xs text-muted-foreground leading-relaxed">{selected.notes}</p>
                </div>
              )}
              {selected.source_name && (
                <div>
                  <p className="text-xs font-medium text-muted-foreground mb-1">Source</p>
                  <p className="text-xs text-foreground">{selected.source_name}</p>
                  {selected.source_url && <a href={selected.source_url} target="_blank" rel="noopener" className="text-[10px] text-amber-400 hover:underline">{selected.source_url}</a>}
                </div>
              )}
            </CardContent>
          </Card>
        )}
      </div>
    </AppShell>
  );
}
