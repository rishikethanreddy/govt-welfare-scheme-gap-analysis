"use client";

import React, { useState } from "react";
import { ComposableMap, Geographies, Geography } from "react-simple-maps";
import { scaleLinear } from "d3-scale";

const geoUrl = "/india.geojson";

interface RegionData {
  state: string;
  district?: string;
  total_records: number;
  gap_signals: number;
  gap_rate: number;
  dominant_gap_type?: string;
  top_schemes?: { scheme: string; count: number }[];
}

interface IndiaMapProps {
  data: RegionData[];
  metric?: "gap_signals" | "gap_rate" | "records";
}

export default function IndiaMap({ data, metric = "gap_signals" }: IndiaMapProps) {
  const [tooltip, setTooltip] = useState<RegionData | null>(null);
  const [tooltipName, setTooltipName] = useState("");

  // Get the metric value for a region
  const getMetricValue = (d: RegionData) => {
    if (metric === "gap_rate") return d.gap_rate;
    if (metric === "records") return d.total_records;
    return d.gap_signals;
  };

  const maxVal = Math.max(...data.map(getMetricValue), 1);

  // Color scale: only color regions with gap signals
  const colorScale = scaleLinear<string>()
    .domain([0, maxVal])
    .range(["#fef3c7", "#ea580c"]);

  return (
    <div className="relative w-full h-full flex items-center justify-center bg-card/30 rounded-xl border border-border/30 overflow-hidden">
      <ComposableMap
        projection="geoMercator"
        projectionConfig={{ scale: 1000, center: [80, 22] }}
        width={800}
        height={600}
        style={{ width: "100%", height: "100%" }}
      >
        <Geographies geography={geoUrl}>
          {({ geographies }) =>
            geographies.map((geo) => {
              const geoName = geo.properties.NAME_1 || geo.properties.NAME_2 || geo.properties.district;

              let matched: RegionData | null = null;

              if (data.length > 0 && data[0].district && geo.properties.NAME_1 && !geo.properties.NAME_2) {
                // Aggregate district data to state geometry
                const stateDistricts = data.filter(d => d.state?.toLowerCase() === (geoName || "").toLowerCase());
                if (stateDistricts.length > 0) {
                  const gapSignals = stateDistricts.reduce((sum, d) => sum + (d.gap_signals || 0), 0);
                  const totalRecords = stateDistricts.reduce((sum, d) => sum + (d.total_records || 0), 0);
                  const gapRate = totalRecords > 0 ? Math.round((gapSignals / totalRecords) * 100) : 0;
                  // Find dominant gap type across districts
                  const gapTypeCounts: Record<string, number> = {};
                  stateDistricts.forEach(d => {
                    if (d.dominant_gap_type) {
                      gapTypeCounts[d.dominant_gap_type] = (gapTypeCounts[d.dominant_gap_type] || 0) + d.gap_signals;
                    }
                  });
                  const dominantGapType = Object.entries(gapTypeCounts).sort(([,a],[,b]) => b - a)[0]?.[0];
                  // Merge top schemes
                  const schemeCounts: Record<string, number> = {};
                  stateDistricts.forEach(d => d.top_schemes?.forEach(s => {
                    schemeCounts[s.scheme] = (schemeCounts[s.scheme] || 0) + s.count;
                  }));
                  const topSchemes = Object.entries(schemeCounts)
                    .sort(([,a],[,b]) => b - a)
                    .slice(0, 3)
                    .map(([scheme, count]) => ({ scheme, count }));

                  matched = {
                    state: geoName,
                    total_records: totalRecords,
                    gap_signals: gapSignals,
                    gap_rate: gapRate,
                    dominant_gap_type: dominantGapType,
                    top_schemes: topSchemes,
                  };
                }
              } else {
                const exactMatch = data.find(
                  (s) => (s.district || s.state)?.toLowerCase() === (geoName || "").toLowerCase()
                );
                if (exactMatch) matched = exactMatch;
              }

              const hasGapSignals = matched && matched.gap_signals > 0;
              const fillColor = hasGapSignals
                ? colorScale(getMetricValue(matched!))
                : "var(--muted)";

              return (
                <Geography
                  key={geo.rsmKey}
                  geography={geo}
                  fill={fillColor}
                  stroke="var(--border)"
                  strokeWidth={0.5}
                  onMouseEnter={() => {
                    setTooltipName(geoName || "Unknown");
                    setTooltip(matched);
                  }}
                  onMouseLeave={() => {
                    setTooltip(null);
                    setTooltipName("");
                  }}
                  style={{
                    default: { outline: "none", transition: "all 250ms" },
                    hover: { outline: "none", fill: hasGapSignals ? "#f59e0b" : "var(--accent)", cursor: "pointer", transition: "all 250ms" },
                    pressed: { outline: "none" },
                  }}
                />
              );
            })
          }
        </Geographies>
      </ComposableMap>

      {/* Enhanced Tooltip */}
      {tooltipName && (
        <div className="absolute top-4 left-4 bg-background/95 backdrop-blur-sm border border-border shadow-2xl p-4 rounded-xl pointer-events-none min-w-[220px]">
          <p className="text-sm font-bold text-foreground mb-2">{tooltipName}</p>
          {tooltip ? (
            <div className="space-y-1.5">
              <div className="flex justify-between text-xs">
                <span className="text-muted-foreground">Records Analyzed</span>
                <span className="font-medium">{tooltip.total_records}</span>
              </div>
              <div className="flex justify-between text-xs">
                <span className="text-muted-foreground">Gap Signals</span>
                <span className="font-medium text-amber-500">{tooltip.gap_signals}</span>
              </div>
              <div className="flex justify-between text-xs">
                <span className="text-muted-foreground">Gap Rate</span>
                <span className={`font-medium ${tooltip.gap_rate > 70 ? "text-red-400" : tooltip.gap_rate > 50 ? "text-orange-400" : "text-green-400"}`}>
                  {tooltip.gap_rate}%
                </span>
              </div>
              {tooltip.dominant_gap_type && (
                <div className="flex justify-between text-xs">
                  <span className="text-muted-foreground">Dominant Gap</span>
                  <span className="font-medium text-purple-400">{tooltip.dominant_gap_type}</span>
                </div>
              )}
              {tooltip.top_schemes && tooltip.top_schemes.length > 0 && (
                <div className="pt-1.5 mt-1.5 border-t border-border/30">
                  <p className="text-[10px] text-muted-foreground mb-1">Schemes</p>
                  {tooltip.top_schemes.map((s, i) => (
                    <p key={i} className="text-[10px] text-foreground/80">{s.scheme} ({s.count})</p>
                  ))}
                </div>
              )}
            </div>
          ) : (
            <p className="text-xs text-muted-foreground">No data in analyzed dataset</p>
          )}
        </div>
      )}

      {/* Legend */}
      <div className="absolute bottom-4 right-4 flex flex-col items-end pointer-events-none">
        <span className="text-xs text-muted-foreground mb-1">
          {metric === "gap_signals" ? "Gap Signals" : metric === "gap_rate" ? "Gap Rate %" : "Records"}
        </span>
        <div className="flex items-center space-x-2">
          <span className="text-xs">0</span>
          <div className="w-24 h-2 rounded-full bg-gradient-to-r from-amber-50 to-orange-600 border border-border/50" />
          <span className="text-xs">{maxVal}</span>
        </div>
        <p className="text-[9px] text-muted-foreground mt-1">Regions without gap signals shown in grey</p>
      </div>
    </div>
  );
}
