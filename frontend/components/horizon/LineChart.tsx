"use client";
import { useEffect, useState } from "react";

interface LineChartProps {
  chartData: any[];
  chartOptions: any;
}

const LineChart = (props: LineChartProps) => {
  const { chartData, chartOptions } = props;
  const [Chart, setChart] = useState<any>(null);
  const [isClient, setIsClient] = useState(false);

  useEffect(() => {
    setIsClient(true);
    // Dynamically import react-apexcharts to avoid SSR issues
    import("react-apexcharts").then((mod) => {
      setChart(() => mod.default);
    });
  }, []);

  if (!isClient || !Chart) {
    return (
      <div className="h-[300px] flex items-center justify-center text-gray-500 dark:text-gray-400">
        Loading chart...
      </div>
    );
  }

  return (
    <Chart
      options={chartOptions}
      type="line"
      width="100%"
      height="100%"
      series={chartData}
    />
  );
};

export default LineChart;
