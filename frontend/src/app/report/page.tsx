"use client";

import { Suspense, useEffect, useMemo, useState } from "react";
import dynamic from "next/dynamic";
import { useRouter, useSearchParams } from "next/navigation";
import NeedAddress from "../../components/NeedAddress";
import { api } from "../../lib/api";
import type { ReportData } from "../../lib/api";
import { useAddress } from "../../components/addressContext";

const ReactECharts = dynamic(() => import("echarts-for-react"), { ssr: false });

function ReportContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { address, storeVersion, ready } = useAddress();
  const [data, setData] = useState<ReportData | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const rangeParam = searchParams.get("range");
  const range = rangeParam === "final" ? "final" : "week";

  const load = async () => {
    if (!address) return;
    setIsLoading(true);
    // 稍微延迟一下以展示 loading 效果（如果请求太快用户会感觉闪烁）
    // await new Promise(r => setTimeout(r, 300)); 
    try {
      const res = await api.getReport({ address, range });
      setData(res);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (!ready || !address) return;
    load();
  }, [address, range, storeVersion, ready]);

  const option = useMemo(() => {
    if (!data) return {};
    return {
      tooltip: {
        trigger: "axis",
        backgroundColor: "rgba(255, 255, 255, 0.95)",
        borderColor: "#f472b6",
        textStyle: { color: "#831843" }
      },
      grid: {
        left: "3%",
        right: "4%",
        bottom: "3%",
        containLabel: true
      },
      xAxis: {
        type: "category",
        data: data.chartByDay.map((_, i) => `第${i + 1}天`),
        axisLine: { lineStyle: { color: "#f472b6" } },
        axisLabel: { color: "#831843" }
      },
      yAxis: {
        type: "value",
        axisLine: { lineStyle: { color: "#f472b6" } },
        axisLabel: { color: "#831843" }
      },
      series: [{
        type: "bar",
        data: data.chartByDay,
        itemStyle: {
          color: {
            type: "linear",
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              { offset: 0, color: "#f472b6" },
              { offset: 1, color: "#fb7185" }
            ]
          }
        }
      }]
    };
  }, [data]);

  if (!ready) return null;
  if (!address) return <NeedAddress />;

  const fallbackTitle = range === "final" ? "结营报告" : "周报";
  const isFinal = range === "final";

  return (
    <div className="rounded-2xl border border-pink-100 bg-white/80 backdrop-blur-sm p-8 shadow-sm animate-fade-in card-hover relative min-h-[400px]">
      {isLoading && (
        <div className="absolute inset-0 z-10 bg-white/60 backdrop-blur-[2px] flex items-center justify-center rounded-2xl">
          <div className="text-pink-600 animate-pulse font-medium">✨生成报告中...</div>
        </div>
      )}

      <div className="flex items-start justify-between gap-3 mb-6">
        <div>
          <div className="text-3xl mb-2 animate-pulse-slow">📊</div>
          <div className="text-2xl font-semibold text-pink-800">{data?.title || fallbackTitle}</div>
          <div className="mt-1 text-sm text-pink-600/70">回顾你的成长历程</div>
        </div>
        <div className="flex gap-2">
          <button
            className={`px-4 py-2 rounded-xl border text-sm transition-all btn-press ${!isFinal
              ? "bg-pink-100 border-pink-200 text-pink-800 font-medium"
              : "bg-white border-pink-100 text-pink-600 hover:bg-pink-50/50"
              }`}
            onClick={() => router.push("/report?range=week")}
            disabled={isLoading}
          >
            周报
          </button>
          <button
            className={`px-4 py-2 rounded-xl border text-sm transition-all btn-press ${isFinal
              ? "bg-pink-100 border-pink-200 text-pink-800 font-medium"
              : "bg-white border-pink-100 text-pink-600 hover:bg-pink-50/50"
              }`}
            onClick={() => router.push("/report?range=final")}
            disabled={isLoading}
          >
            结营报告
          </button>
        </div>
      </div>

      <div className="grid lg:grid-cols-2 gap-6 mb-6">
        <div className="rounded-2xl bg-gradient-to-br from-pink-50/50 to-rose-50/50 border border-pink-100 p-6 animate-slide-in card-hover">
          <div className="text-sm font-semibold text-pink-700 mb-3">💭 成长总结</div>
          <div className="text-sm text-pink-700 leading-relaxed whitespace-pre-line">{data?.reportText || "还没有记录，去开始你的第一天吧！"}</div>
        </div>

        <div className="rounded-2xl bg-gradient-to-br from-pink-50/50 to-rose-50/50 border border-pink-100 p-6 animate-slide-in card-hover">
          <div className="text-sm font-semibold text-pink-700 mb-3">📈 完成情况</div>
          <div className="mt-3" style={{ width: "100%", height: 260 }}>
            {data ? <ReactECharts option={option} style={{ width: "100%", height: 260 }} /> : (
              <div className="flex items-center justify-center h-full text-pink-600/50 text-sm">暂无数据</div>
            )}
          </div>
        </div>
      </div>

      <div className="rounded-2xl border border-pink-100 bg-white/90 p-6 animate-slide-in">
        <div className="text-sm font-semibold text-pink-700 mb-4">📝 最近的记录</div>
        <div className="space-y-3">
          {(data?.recentLogs || []).length > 0 ? (
            (data?.recentLogs || []).map((l, i) => (
              <div key={l.id} className="rounded-xl bg-pink-50/30 border border-pink-100 p-4 animate-fade-in card-hover" style={{ animationDelay: `${i * 0.1}s` }}>
                <div className="flex items-center justify-between gap-3 mb-3">
                  <div className="text-sm font-medium text-pink-700">第 {l.dayIndex} 天</div>
                  <div className="text-xs text-pink-600/70">
                    {l.daySbtTxHash && <span className="inline-block mr-2">✓ 已完成</span>}
                    {l.txHash && <span className="inline-block">✓ 已保存</span>}
                  </div>
                </div>
                <div className="mt-2 text-sm text-pink-700 leading-relaxed">
                  <div className="mb-2">
                    <span className="text-pink-600/70">💭 </span>
                    {l.reflection.note}
                  </div>
                  <div>
                    <span className="text-pink-600/70">🌱 </span>
                    {l.reflection.next}
                  </div>
                </div>
              </div>
            ))
          ) : (
            <div className="text-sm text-pink-600/70 text-center py-8">还没有记录，去开始你的第一天吧！</div>
          )}
        </div>
      </div>
    </div>
  );
}

export default function ReportPage() {
  return (
    <Suspense fallback={<div className="p-6 text-pink-800 animate-fade-in">加载中...</div>}>
      <ReportContent />
    </Suspense>
  );
}
