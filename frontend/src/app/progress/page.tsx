"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import NeedAddress from "../../components/NeedAddress";
import { api } from "../../lib/api";
import type { ProgressData } from "../../lib/api";
import { useAddress } from "../../components/addressContext";

export default function ProgressPage() {
  const router = useRouter();
  const { address, storeVersion, ready } = useAddress();
  const [data, setData] = useState<ProgressData | null>(null);

  const load = async () => {
    if (!address) return;
    const res = await api.getProgress({ address });
    setData(res);
  };

  useEffect(() => {
    if (!ready || !address) return;
    load();
  }, [address, storeVersion, ready]);

  if (!ready) return null;
  if (!address) return <NeedAddress />;

  const handleComposeFinal = async () => {
    if (!data?.shouldComposeFinal) return;
    try {
      await api.composeFinal({ address });
      alert("已模拟合成 FinalSBT");
      load();
    } catch (e: any) {
      alert(e?.message || "合成失败");
    }
  };

  const completedDays = data?.completedDays || [];
  const mintableDayIndex = data?.mintableDayIndex ?? null;

  return (
    <div className="grid lg:grid-cols-3 gap-4">
      <div className="lg:col-span-2 rounded-2xl border border-slate-200 p-6">
        <div className="flex items-start justify-between">
          <div>
            <div className="text-sm text-slate-500">进度</div>
            <div className="mt-1 text-xl font-semibold">你的挑战状态</div>
          </div>
          <div className="text-right">
            <div className="text-sm text-slate-500">dateKey</div>
            <div className="mt-1 font-mono text-sm">{data?.dateKey || ""}</div>
          </div>
        </div>

        <div className="mt-5 grid sm:grid-cols-2 gap-4">
          <div className="rounded-2xl bg-slate-50 border border-slate-200 p-5">
            <div className="text-xs text-slate-500">streak</div>
            <div className="mt-1 text-3xl font-semibold">{data?.streak || 0}</div>
            <div className="mt-2 text-sm text-slate-600">连续完成天数（模拟规则）</div>
          </div>

          <div className="rounded-2xl bg-slate-50 border border-slate-200 p-5">
            <div className="text-xs text-slate-500">DaySBT 已铸造</div>
            <div className="mt-1 text-3xl font-semibold">
              {data?.dayMintCount || 0}
              <span className="text-base font-normal text-slate-400">/28</span>
            </div>
            <div className="mt-2 text-sm text-slate-600">每日一枚（模拟 /sbt/confirm）</div>
          </div>
        </div>

        <div className="mt-4 rounded-2xl border border-slate-200 p-5">
          <div className="text-sm font-semibold">按钮状态</div>
          <div className="mt-2 text-sm text-slate-700">
            shouldMintDay：<span className="font-semibold">{data?.shouldMintDay ? "true" : "false"}</span>
            {data?.shouldMintDay && mintableDayIndex ? (
              <span className="text-slate-500">（可 mint Day {mintableDayIndex}）</span>
            ) : null}
          </div>
          <div className="mt-1 text-sm text-slate-700">
            shouldComposeFinal：<span className="font-semibold">{data?.shouldComposeFinal ? "true" : "false"}</span>
          </div>

          <div className="mt-4 flex flex-wrap gap-2">
            <button
              className="px-3 py-2 rounded-xl border border-slate-200 text-sm hover:bg-slate-50"
              onClick={() => router.push(`/daily/${mintableDayIndex || 1}`)}
            >
              去今日
            </button>
            <button
              className="px-3 py-2 rounded-xl bg-slate-900 text-white text-sm hover:bg-slate-800"
              disabled={!data?.shouldComposeFinal}
              onClick={handleComposeFinal}
            >
              {data?.shouldComposeFinal ? "模拟合成 FinalSBT" : "未满足合成条件"}
            </button>
          </div>

          <div className="mt-3 text-xs text-slate-500">合成条件：dayMintCount == 28 且 finalMinted == false（这里不查链）。</div>
        </div>

        <div className="mt-4 rounded-2xl border border-slate-200 p-5">
          <div className="text-sm font-semibold">完成的 DayIndex</div>
          <div className="mt-3 flex flex-wrap gap-2">
            {completedDays.length ? (
              completedDays.map((d) => (
                <button
                  key={d}
                  className="px-2.5 py-1.5 rounded-xl border border-slate-200 text-sm hover:bg-slate-50"
                  onClick={() => router.push(`/daily/${d}`)}
                >
                  Day {d}
                </button>
              ))
            ) : (
              <div className="text-sm text-slate-500">暂无记录</div>
            )}
          </div>
        </div>
      </div>

      <div className="rounded-2xl border border-slate-200 p-6">
        <div className="text-sm text-slate-500">FinalSBT</div>
        <div className="mt-2 text-lg font-semibold">{data?.finalMinted ? "已合成" : "未合成"}</div>
        <div className="mt-3 text-sm text-slate-700">
          finalMinted：<span className="font-semibold">{data?.finalMinted ? "true" : "false"}</span>
        </div>
        <div className="mt-3 text-sm text-slate-700">final txHash：</div>
        <div className="mt-1 font-mono text-xs break-all">{data?.finalSbtTxHash || "—"}</div>

        <div className="mt-6 border-t border-slate-200 pt-5">
          <div className="text-sm text-slate-500">报告</div>
          <div className="mt-3 flex flex-wrap gap-2">
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
      </div>
    </div>
  );
}
