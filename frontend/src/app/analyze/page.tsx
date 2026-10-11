"use client";
import React, { useState } from "react";
import AppShell from "@/components/AppShell";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { api } from "@/lib/api";
import { Brain, Send, AlertTriangle, CheckCircle, Loader2 } from "lucide-react";

export default function AnalyzePage() {
  const [text, setText] = useState("");
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleAnalyze = async () => {
    if (!text.trim() || text.length < 5) return;
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const r = await api.analyze(text);
      setResult(r);
    } catch (e: any) {
      setError(e.message);
    }
    setLoading(false);
  };

  return (
    <AppShell>
      <div className="p-6 space-y-6 max-w-[900px] mx-auto">
        <div>
          <h1 className="text-2xl font-bold">Text Analyzer</h1>
          <p className="text-sm text-muted-foreground mt-0.5">Analyze any text through the NLP pipeline</p>
        </div>

        {/* Input */}
        <Card className="border-border/30 bg-card/50">
          <CardContent className="p-5 space-y-3">
            <textarea
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder="Enter a question, complaint, or query about a government welfare scheme..."
              rows={4}
              className="w-full p-3 rounded-lg bg-card border border-border/40 text-sm text-foreground placeholder:text-muted-foreground/50 resize-none focus:outline-none focus:ring-1 focus:ring-amber-500/50"
            />
            <div className="flex items-center justify-between">
              <p className="text-xs text-muted-foreground">{text.length} characters (min 5)</p>
              <button
                onClick={handleAnalyze}
                disabled={loading || text.length < 5}
                className="flex items-center gap-2 px-4 py-2 rounded-lg bg-amber-500 hover:bg-amber-600 text-black text-xs font-medium disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
              >
                {loading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Send className="w-3.5 h-3.5" />}
                Analyze
              </button>
            </div>
          </CardContent>
        </Card>

        {/* Error */}
        {error && (
          <div className="p-4 rounded-lg border border-red-500/30 bg-red-500/5 text-red-400 text-sm">
            <AlertTriangle className="w-4 h-4 inline mr-2" />{error}
          </div>
        )}

        {/* Results */}
        {result && (
          <Card className="border-border/30 bg-card/50">
            <CardHeader>
              <CardTitle className="text-sm flex items-center gap-2">
                <Brain className="w-4 h-4 text-amber-400" /> Analysis Results
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* NLP Results Grid */}
              <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                {[
                  { label: "Scheme", value: result.scheme, confidence: result.scheme_confidence, color: "amber" },
                  { label: "Intent", value: result.intent, confidence: result.intent_confidence, color: "blue" },
                  { label: "Awareness Gap", value: result.awareness_gap, confidence: result.gap_confidence, color: result.awareness_gap === "yes" ? "red" : "green" },
                  { label: "Gap Type", value: result.gap_type, confidence: result.gap_type_confidence, color: "purple" },
                  { label: "Language", value: result.language, color: "cyan" },
                ].map(({ label, value, confidence, color }) => (
                  <div key={label} className={`p-3 rounded-lg border border-border/20 bg-${color}-500/5`}>
                    <p className="text-[10px] text-muted-foreground uppercase tracking-wider mb-1">{label}</p>
                    <p className={`text-sm font-medium text-${color}-400`}>{value || "N/A"}</p>
                    {confidence != null && (
                      <p className="text-[10px] text-muted-foreground mt-1">
                        Confidence: {(confidence * 100).toFixed(1)}%
                      </p>
                    )}
                  </div>
                ))}
              </div>

              {/* Supporting Signals */}
              {result.supporting_signals?.length > 0 && (
                <div>
                  <p className="text-xs font-medium text-muted-foreground mb-2">Supporting Signals</p>
                  {result.supporting_signals.map((s: any, i: number) => (
                    <div key={i} className="flex items-start gap-2 p-2 rounded bg-white/[0.02] mb-1">
                      <CheckCircle className="w-3 h-3 text-green-400 mt-0.5 shrink-0" />
                      <div>
                        <p className="text-xs font-medium">{s.signal}</p>
                        <p className="text-[10px] text-muted-foreground">{s.detail}</p>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        )}

        {/* Example Queries */}
        <Card className="border-border/30 bg-card/50">
          <CardHeader>
            <CardTitle className="text-sm">Try These Examples</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {[
              "How do I apply for PM-KISAN if I don't have a land record in my name?",
              "My Ayushman Bharat card was rejected at the hospital. What should I do?",
              "MGNREGA payment has been delayed for 3 months in our village",
              "Is PM Awas Yojana available for families living in rented houses?",
            ].map((example) => (
              <button
                key={example}
                onClick={() => setText(example)}
                className="w-full text-left p-3 rounded-lg bg-white/[0.02] border border-border/20 hover:border-amber-500/30 hover:bg-white/[0.03] text-xs text-muted-foreground hover:text-foreground transition-all"
              >
                {example}
              </button>
            ))}
          </CardContent>
        </Card>
      </div>
    </AppShell>
  );
}
