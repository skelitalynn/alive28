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

  const rangeParam = searchParams.get("range");
  const range = rangeParam === "final" ? "final" : "week";

  const load = async () => {
    if (!address) return;
    const res = await api.getReport({ address, range });
    setData(res);
  };

  useEffect(() => {
    if (!ready || !address) return;
    load();
  }, [address, range, storeVersion, ready]);

  const option = useMemo(() => {
    if (!data) return {};
    return {
      tooltip: {},
      xAxis: { type: "category", data: data.chartByDay.map((_, i) => String(i + 1)) },
      yAxis: { type: "value" },
      series: [{ type: "bar", data: data.chartByDay }]
    };
  }, [data]);

  if (!ready) return null;
  if (!address) return <NeedAddress />;

  const fallbackTitle = range === "final" ? "结营报告（模拟）" : "周报（模拟）";

  return (
    <div className="rounded-2xl border border-slate-200 p-6">
      <div className="flex items-start justify-between gap-3">
        <div>
          <div className="text-sm text-slate-500">报告</div>
          <div className="mt-1 text-xl font-semibold">{data?.title || fallbackTitle}</div>
        </div>
        <div className="flex gap-2">
          <button
            className="px-3 py-2 rounded-xl border border-slate-200 text-sm hover:bg-slate-50"
            onClick={() => router.push("/report?range=week")}
          >
            周报
          </button>
          <button
            className="px-3 py-2 rounded-xl border border-slate-200 text-sm hover:bg-slate-50"
            onClick={() => router.push("/report?range=final")}
          >
            结营
          </button>
        </div>
      </div>

      <div className="mt-5 grid lg:grid-cols-2 gap-4">
        <div className="rounded-2xl bg-slate-50 border border-slate-200 p-5">
          <div className="text-sm font-semibold">reportText</div>
          <div className="mt-3 text-sm text-slate-700 leading-relaxed">{data?.reportText || ""}</div>
        </div>

        <div className="rounded-2xl bg-slate-50 border border-slate-200 p-5">
          <div className="text-sm font-semibold">chartData（打卡次数）</div>
          <div className="mt-3" style={{ width: "100%", height: 260 }}>
            {data ? <ReactECharts option={option} style={{ width: "100%", height: 260 }} /> : null}
          </div>
        </div>
      </div>

      <div className="mt-5 rounded-2xl border border-slate-200 p-5">
        <div className="text-sm font-semibold">最近 6 条日志（reflection）</div>
        <div className="mt-3 space-y-3">
          {(data?.recentLogs || []).map((l) => (
            <div key={l.id} className="rounded-xl bg-white border border-slate-200 p-4">
              <div className="flex items-center justify-between gap-3">
                <div className="text-sm font-semibold">Day {l.dayIndex} · {l.dateKey}</div>
                <div className="text-xs text-slate-500">
                  {l.daySbtTxHash ? "DaySBT✅" : "DaySBT—"} · {l.txHash ? "Proof✅" : "Proof—"}
                </div>
              </div>
              <div className="mt-2 text-sm">
                <span className="text-slate-500">note：</span>{l.reflection.note}
              </div>
              <div className="mt-1 text-sm">
                <span className="text-slate-500">next：</span>{l.reflection.next}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export default function ReportPage() {
  return (
    <Suspense fallback={<div className="p-6">Loading report...</div>}>
      <ReportContent />
    </Suspense>
  );
}

