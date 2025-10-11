"use client";

import Card from "@/components/horizon/Card";
import LineChart from "@/components/horizon/LineChart";
import BarChart from "@/components/horizon/BarChart";
import PieChart from "@/components/horizon/PieChart";
import { DASHBOARD_TEXT } from "@/app/dashboard/constants";
import { getSTCTrendData, getCoordinationData, getRoleDistributionData } from "@/app/dashboard/mockData";
import type { ProjectChartsProps } from "@/lib/types";

export function ProjectCharts({ projectId, branchName }: ProjectChartsProps) {
  // Get chart data
  const stcTrendData = getSTCTrendData(projectId, branchName);
  const coordinationData = getCoordinationData(projectId, branchName);
  const roleDistributionData = getRoleDistributionData(projectId, branchName);

  // Chart configurations
  const stcTrendOptions = {
    chart: {
      type: 'line',
      toolbar: {
        show: false,
      },
    },
    stroke: {
      curve: 'smooth',
      width: 3,
    },
    colors: ['hsl(var(--primary))'],
    xaxis: {
      type: 'datetime',
      labels: {
        format: 'MMM dd',
      },
    },
    yaxis: {
      title: {
        text: 'STC Score',
      },
      min: 0,
      max: 1,
    },
    tooltip: {
      x: {
        format: 'MMM dd, yyyy',
      },
    },
  };

  const coordinationOptions = {
    chart: {
      type: 'bar',
      toolbar: {
        show: false,
      },
    },
    colors: ['hsl(var(--primary))', 'hsl(var(--secondary))'],
    plotOptions: {
      bar: {
        horizontal: false,
        columnWidth: '55%',
      },
    },
    dataLabels: {
      enabled: false,
    },
    xaxis: {
      categories: coordinationData.map(item => item.x),
    },
    yaxis: {
      title: {
        text: 'Coordination Score',
      },
    },
  };

  const roleDistributionOptions = {
    chart: {
      type: 'pie',
      toolbar: {
        show: false,
      },
    },
    colors: ['hsl(var(--primary))', 'hsl(var(--secondary))', 'hsl(var(--accent))', 'hsl(var(--destructive))', 'hsl(var(--muted))'],
    labels: roleDistributionData.map(item => item.x),
    legend: {
      position: 'bottom',
    },
  };

  // hide the charts
  return null;
}

