"use client";

import React, { useState, useEffect } from 'react';
import AppShell from '@/components/AppShell';
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, Legend, ResponsiveContainer,
  AreaChart, Area
} from 'recharts';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";

export default function PipelineHealthPage() {
  const [funnelData, setFunnelData] = useState<any[]>([]);
  const [overviewData, setOverviewData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const funnelRes = await fetch('http://localhost:8000/api/collection/funnel');
        const overviewRes = await fetch('http://localhost:8000/api/collection/overview');
        
        const funnelJson = await funnelRes.json();
        const overviewJson = await overviewRes.json();

        setFunnelData(funnelJson.funnel || []);
        setOverviewData(overviewJson);
      } catch (error) {
        console.error("Error fetching pipeline health:", error);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  if (loading) {
    return (
      <AppShell>
        <div className="flex items-center justify-center min-h-[500px]">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
        </div>
      </AppShell>
    );
  }

  return (
    <AppShell>
      <div className="p-6 space-y-6 max-w-[1400px] mx-auto">
        <header className="mb-8">
          <h1 className="text-2xl font-bold text-foreground">Pipeline Health Diagnostics</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Monitor data collection stages, identify bottlenecks, and track record provenance.
          </p>
        </header>

        {/* Funnel Section */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card className="border-border/30 bg-card/50">
            <CardHeader>
              <CardTitle className="text-sm font-medium">Collection Funnel</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {funnelData.map((item, idx) => (
                  <div key={idx} className="relative">
                    <div className="flex justify-between items-center mb-1">
                      <span className={`text-sm font-medium ${item.highlight ? 'text-primary font-bold' : 'text-foreground/80'}`}>
                        {item.stage}
                      </span>
                      <span className={`text-sm font-medium ${item.delta ? 'text-destructive' : 'text-foreground'}`}>
                        {item.count.toLocaleString()}
                      </span>
                    </div>
                    <div className="w-full bg-secondary rounded-full h-2.5 overflow-hidden">
                      <div 
                        className={`h-2.5 rounded-full ${item.delta ? 'bg-destructive' : (item.highlight ? 'bg-primary' : 'bg-blue-400')}`}
                        style={{ width: `${Math.max(1, (item.count / Math.max(...funnelData.map(d => d.count))) * 100)}%` }}
                      ></div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* URL Status Breakdown */}
          <Card className="border-border/30 bg-card/50">
            <CardHeader>
              <CardTitle className="text-sm font-medium">Worker Queue Status</CardTitle>
            </CardHeader>
            <CardContent className="h-72">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart
                  data={Object.entries(overviewData?.url_status_breakdown || {}).map(([status, count]) => ({ status, count }))}
                  margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                >
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" opacity={0.5} vertical={false} />
                  <XAxis dataKey="status" stroke="var(--muted-foreground)" tick={{ fontSize: 11 }} axisLine={false} tickLine={false} />
                  <YAxis stroke="var(--muted-foreground)" tick={{ fontSize: 11 }} axisLine={false} tickLine={false} />
                  <RechartsTooltip 
                    contentStyle={{ backgroundColor: 'var(--card)', border: '1px solid var(--border)', borderRadius: '0.5rem', color: 'var(--foreground)' }}
                    itemStyle={{ color: 'var(--foreground)' }}
                  />
                  <Bar dataKey="count" fill="var(--muted-foreground)" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Source Yield */}
          <Card className="border-border/30 bg-card/50">
            <CardHeader>
              <CardTitle className="text-sm font-medium">Top Sources by Yield</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {overviewData?.records_by_source?.slice(0, 8).map((source: any, idx: number) => (
                  <div key={idx} className="flex items-center justify-between p-3 bg-white/[0.02] border border-border/20 rounded-lg">
                    <span className="text-sm font-medium text-foreground">{source.source}</span>
                    <span className="text-sm font-semibold text-primary">
                      {source.count.toLocaleString()} records
                    </span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
          
          {/* Scheme Coverage */}
          <Card className="border-border/30 bg-card/50">
            <CardHeader>
              <CardTitle className="text-sm font-medium">Scheme Coverage</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {overviewData?.records_by_scheme?.slice(0, 8).map((scheme: any, idx: number) => (
                  <div key={idx} className="flex items-center justify-between p-3 bg-white/[0.02] border border-border/20 rounded-lg">
                    <span className="text-sm font-medium text-foreground truncate max-w-[250px]" title={scheme.scheme}>
                      {scheme.scheme}
                    </span>
                    <span className="text-sm font-semibold text-primary">
                      {scheme.count.toLocaleString()} records
                    </span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </AppShell>
  );
}
