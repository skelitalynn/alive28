"use client";

import { useState } from "react";
import { useAccount } from "wagmi";
import { getReport } from "../../lib/api";
import ReactECharts from "echarts-for-react";

export default function ReportPage() {
  const { address } = useAccount();
  const [data, setData] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  const load = async (range: "week" | "final") => {
    if (!address) return;
    try {
      setError(null);
      const res = await getReport(address, range);
      setData(res);
    } catch (e: any) {
      setError(e?.message || "无法获取报告，请确认后端是否启动");
    }
  };

  const option = data
    ? {
        xAxis: {
          type: "category",
          data: data.chartData.checkins.map((c: any) => c.dateKey)
        },
        yAxis: { type: "value" },
        series: [
          {
            data: data.chartData.checkins.map((c: any) => (c.done ? 1 : 0)),
            type: "bar"
          }
        ]
      }
    : {};

  return (
    <main className="min-h-screen p-10 space-y-6">
      <h1 className="text-2xl font-bold">报告</h1>
      <div className="space-x-3">
        <button className="px-4 py-2 bg-[#35d0ba] text-black rounded" onClick={() => load("week")}>
          周报
        </button>
        <button className="px-4 py-2 bg-[#222] rounded" onClick={() => load("final")}>
          结营报告
        </button>
      </div>
      {error && <div className="text-xs text-red-400">{error}</div>}
      {data && (
        <div className="p-4 bg-[#15151a] rounded space-y-3">
          <div>{data.reportText}</div>
          <ReactECharts option={option} style={{ height: 300 }} />
        </div>
      )}
    </main>
  );
}
