"use client";

import { useEffect, useState } from "react";
import dynamic from "next/dynamic";
import Card from "@/components/horizon/Card";
import { getLatestSTCAnalysis, getSTCMatrix } from "@/lib/api/stc";
import type { STCMatrixResponse } from "@/lib/types/stc";
import { ApexOptions } from "apexcharts";

// Dynamically import Chart to avoid SSR issues
const Chart = dynamic(() => import("react-apexcharts"), { ssr: false });

interface STCMatrixProps {
  projectId?: string;
  analysisId?: string;
}

export function STCMatrix({ projectId, analysisId }: STCMatrixProps) {
  const [data, setData] = useState<STCMatrixResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        let targetAnalysisId = analysisId;
        
        // If no analysisId provided, get latest for projectId
        if (!targetAnalysisId && projectId) {
          const latestAnalysis = await getLatestSTCAnalysis(projectId);
          targetAnalysisId = latestAnalysis.id;
        }
        
        if (!targetAnalysisId) {
          throw new Error("No analysis ID or project ID provided");
        }
        
        // Get matrix data for this analysis
        const response = await getSTCMatrix(targetAnalysisId);
        setData(response);
      } catch (err: any) {
        console.error("Failed to load STC matrix:", err);
        setError(err.message || "Failed to load STC matrix data");
      } finally {
        setLoading(false);
      }
    };

    if (projectId || analysisId) {
      fetchData();
    }
  }, [projectId, analysisId]);

  if (loading) {
    return (
      <Card className="h-[400px] flex items-center justify-center">
        <div className="text-muted-foreground">Loading matrix...</div>
      </Card>
    );
  }

  if (error || !data) {
    return (
      <Card className="h-[400px] flex items-center justify-center">
        <div className="text-destructive">{error || "No data available"}</div>
      </Card>
    );
  }

  const series = data.users.map(user => ({
    name: user.name,
    data: data.users.map(targetUser => {
      if (user.id === targetUser.id) return { x: targetUser.name, y: 0 };
      
      const cell = data.matrix.find(
        c => c.x === user.name && c.y === targetUser.name
      );
      
      return {
        x: targetUser.name,
        y: cell ? cell.value : 0
      };
    })
  }));

  const options: ApexOptions = {
    chart: {
      type: 'heatmap',
      toolbar: { show: false },
      background: 'transparent'
    },
    dataLabels: { enabled: false },
    colors: ["#e2e8f0", "#10b981", "#ef4444", "#f59e0b"], // 0: None, 1: Congruent, 2: Missed, 3: Unnecessary
    plotOptions: {
      heatmap: {
        shadeIntensity: 0.5,
        radius: 0,
        useFillColorAsStroke: true,
        colorScale: {
          ranges: [
            { from: 0, to: 0, color: '#e2e8f0', name: 'None' },
            { from: 1, to: 1, color: '#10b981', name: 'Congruent' },
            { from: 2, to: 2, color: '#ef4444', name: 'Missed' },
            { from: 3, to: 3, color: '#f59e0b', name: 'Unnecessary' }
          ]
        }
      }
    },
    stroke: { width: 1, colors: ['var(--background)'] },
    xaxis: {
      labels: {
        show: false // Hide x-axis labels if too many users
      },
      tooltip: { enabled: false }
    },
    yaxis: {
      labels: {
        style: { colors: 'hsl(var(--muted-foreground))' }
      }
    },
    theme: { mode: 'light' }, // Adjust based on theme
    title: {
      text: `STC Matrix (Score: ${data.stc_value.toFixed(2)})`,
      align: 'left',
      style: { color: 'hsl(var(--foreground))' }
    }
  };

  return (
    <Card className="p-6">
      <div className="h-[400px]">
        <Chart
          options={options}
          series={series}
          type="heatmap"
          height="100%"
          width="100%"
        />
      </div>
      <div className="flex gap-4 mt-4 justify-center text-sm">
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 bg-emerald-500 rounded-sm"></div>
          <span>Congruent</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 bg-red-500 rounded-sm"></div>
          <span>Missed</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 bg-amber-500 rounded-sm"></div>
          <span>Unnecessary</span>
        </div>
      </div>
    </Card>
  );
}
