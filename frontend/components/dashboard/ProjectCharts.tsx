"use client";

import Card from "@/components/horizon/Card";
import LineChart from "@/components/horizon/LineChart";
import BarChart from "@/components/horizon/BarChart";
import PieChart from "@/components/horizon/PieChart";
import { DASHBOARD_TEXT } from "@/app/dashboard/constants";
import { getSTCTrendData, getCoordinationData, getRoleDistributionData } from "@/app/dashboard/mockData";

interface ProjectChartsProps {
  projectId: string;
  branchName: string;
}

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

  return (
    <div className="space-y-6">
      {/* STC Trend Chart */}
      <Card>
        <div className="p-6">
            <h4 className="text-lg font-semibold text-foreground mb-4">
              {DASHBOARD_TEXT.CHART_STC_TREND}
            </h4>
          {stcTrendData.length > 0 ? (
            <div className="h-[300px]">
              <LineChart
                chartData={[{
                  name: 'STC Score',
                  data: stcTrendData,
                }]}
                chartOptions={stcTrendOptions}
              />
            </div>
          ) : (
            <div className="h-[300px] flex items-center justify-center text-gray-500 dark:text-gray-400">
              {DASHBOARD_TEXT.MSG_NO_DATA}
            </div>
          )}
        </div>
      </Card>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Coordination Chart */}
        <Card>
          <div className="p-6">
            <h4 className="text-lg font-semibold text-foreground mb-4">
              {DASHBOARD_TEXT.CHART_COORDINATION}
            </h4>
            {coordinationData.length > 0 ? (
              <div className="h-[250px]">
                <BarChart
                  chartData={[
                    {
                      name: 'Required',
                      data: coordinationData.map(item => item.y * 0.8),
                    },
                    {
                      name: 'Actual',
                      data: coordinationData.map(item => item.y),
                    },
                  ]}
                  chartOptions={coordinationOptions}
                />
              </div>
            ) : (
              <div className="h-[250px] flex items-center justify-center text-gray-500 dark:text-gray-400">
                {DASHBOARD_TEXT.MSG_NO_DATA}
              </div>
            )}
          </div>
        </Card>

        {/* Role Distribution Chart */}
        <Card>
          <div className="p-6">
            <h4 className="text-lg font-semibold text-foreground mb-4">
              {DASHBOARD_TEXT.CHART_ROLE_DISTRIBUTION}
            </h4>
            {roleDistributionData.length > 0 ? (
              <div className="h-[250px]">
                <PieChart
                  chartData={roleDistributionData.map(item => item.y)}
                  chartOptions={roleDistributionOptions}
                />
              </div>
            ) : (
              <div className="h-[250px] flex items-center justify-center text-gray-500 dark:text-gray-400">
                {DASHBOARD_TEXT.MSG_NO_DATA}
              </div>
            )}
          </div>
        </Card>
      </div>
    </div>
  );
}

