"use client";
import React, { useState } from "react";
import AppShell from "@/components/AppShell";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Upload as UploadIcon, FileText, CheckCircle, AlertTriangle, Loader2 } from "lucide-react";

export default function UploadPage() {
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  const handleUpload = async () => {
    if (!file) return;
    setUploading(true);
    setError(null);
    setResult(null);

    const formData = new FormData();
    formData.append("file", file);

    try {
      const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const res = await fetch(`${API_BASE}/api/datasets/upload`, {
        method: "POST",
        body: formData,
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `Upload failed: ${res.status}`);
      }
      setResult(await res.json());
    } catch (e: any) {
      setError(e.message);
    }
    setUploading(false);
  };

  return (
    <AppShell>
      <div className="p-6 space-y-6 max-w-[700px] mx-auto">
        <div>
          <h1 className="text-2xl font-bold">Upload Dataset</h1>
          <p className="text-sm text-muted-foreground mt-0.5">Import CSV data with automatic column detection</p>
        </div>

        {/* Upload Area */}
        <Card className="border-border/30 bg-card/50">
          <CardContent className="p-6">
            <div
              className="border-2 border-dashed border-border/40 rounded-xl p-8 text-center hover:border-amber-500/40 transition-colors cursor-pointer"
              onClick={() => document.getElementById("file-input")?.click()}
              onDragOver={(e) => e.preventDefault()}
              onDrop={(e) => { e.preventDefault(); if (e.dataTransfer.files[0]) setFile(e.dataTransfer.files[0]); }}
            >
              <input id="file-input" type="file" accept=".csv,.json,.xlsx" className="hidden" onChange={(e) => setFile(e.target.files?.[0] || null)} />
              <UploadIcon className="w-10 h-10 text-muted-foreground mx-auto mb-3" />
              <p className="text-sm text-foreground font-medium">
                {file ? file.name : "Drop a CSV file here or click to browse"}
              </p>
              <p className="text-xs text-muted-foreground mt-1">
                {file ? `${(file.size / 1024).toFixed(1)} KB` : "Supports .csv, .json, .xlsx (max 50MB)"}
              </p>
            </div>

            {file && (
              <div className="mt-4 flex justify-end">
                <button
                  onClick={handleUpload}
                  disabled={uploading}
                  className="flex items-center gap-2 px-5 py-2.5 rounded-lg bg-amber-500 hover:bg-amber-600 text-black text-sm font-medium disabled:opacity-40 transition-colors"
                >
                  {uploading ? <Loader2 className="w-4 h-4 animate-spin" /> : <UploadIcon className="w-4 h-4" />}
                  {uploading ? "Importing..." : "Import Dataset"}
                </button>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Error */}
        {error && (
          <div className="p-4 rounded-lg border border-red-500/30 bg-red-500/5 text-red-400 text-sm">
            <AlertTriangle className="w-4 h-4 inline mr-2" />{error}
          </div>
        )}

        {/* Success Result */}
        {result && (
          <Card className="border-green-500/30 bg-green-500/5">
            <CardContent className="p-5 space-y-3">
              <div className="flex items-center gap-2">
                <CheckCircle className="w-5 h-5 text-green-400" />
                <p className="text-sm font-medium text-green-400">Dataset Imported Successfully</p>
              </div>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                {[
                  ["Version", result.version],
                  ["Valid Records", result.valid_records],
                  ["Duplicates", result.duplicate_records],
                  ["Rejected", result.rejected_records],
                ].map(([label, value]) => (
                  <div key={label as string}>
                    <p className="text-[10px] text-muted-foreground uppercase">{label}</p>
                    <p className="text-sm font-bold">{value}</p>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Instructions */}
        <Card className="border-border/30 bg-card/50">
          <CardHeader>
            <CardTitle className="text-sm">Expected CSV Format</CardTitle>
            <CardDescription className="text-xs">Column auto-detection maps these fields automatically</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-2 text-xs">
              {[
                ["text / query / question", "The main text content (required)"],
                ["scheme / scheme_name", "Welfare scheme name"],
                ["intent", "User intent category"],
                ["awareness_gap / gap", "Gap signal (yes/no)"],
                ["gap_type", "Gap type category"],
                ["state", "Indian state name"],
                ["district", "District name"],
                ["source", "Data source name"],
                ["split", "ML split (train/val/test)"],
              ].map(([col, desc]) => (
                <div key={col} className="p-2 rounded bg-secondary/50">
                  <code className="text-amber-400 text-[10px]">{col}</code>
                  <p className="text-[10px] text-muted-foreground mt-0.5">{desc}</p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </AppShell>
  );
}
