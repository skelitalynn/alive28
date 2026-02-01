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
      alert("🎉 恭喜完成28天挑战！");
      load();
    } catch (e: any) {
      alert(e?.message || "操作失败，请重试");
    }
  };

  const completedDays = data?.completedDays || [];
  const mintableDayIndex = data?.mintableDayIndex ?? null;
  const overallProgress = Math.round(((data?.dayMintCount || 0) / 28) * 100);

  return (
    <div className="grid lg:grid-cols-3 gap-6 animate-fade-in">
      <div className="lg:col-span-2 rounded-2xl border border-pink-100 bg-white/80 backdrop-blur-sm p-8 shadow-sm card-hover">
        <div className="mb-6">
          <div className="text-3xl mb-2 animate-pulse-slow">📈</div>
          <h1 className="text-2xl font-semibold text-pink-800">我的成长进度</h1>
          <p className="text-sm text-pink-600/70 mt-1">记录你的每一步成长</p>
        </div>

        {/* 整体进度条 */}
        <div className="mb-6 animate-slide-in">
          <div className="flex justify-between text-sm text-pink-600/70 mb-2">
            <span>整体进度</span>
            <span>{overallProgress}%</span>
          </div>
          <div className="progress-bar">
            <div className="progress-fill" style={{ width: `${overallProgress}%` }}></div>
          </div>
        </div>

        <div className="grid sm:grid-cols-2 gap-4 mb-6">
          <div className="rounded-2xl bg-gradient-to-br from-pink-50 to-rose-50 border border-pink-100 p-6 animate-slide-in card-hover">
            <div className="text-xs text-pink-600/70 mb-1">🔥 连续完成</div>
            <div className="text-4xl font-bold text-pink-800">{data?.streak || 0}</div>
            <div className="mt-2 text-sm text-pink-700">天</div>
          </div>

          <div className="rounded-2xl bg-gradient-to-br from-pink-50 to-rose-50 border border-pink-100 p-6 animate-slide-in card-hover">
            <div className="text-xs text-pink-600/70 mb-1">✨ 已完成任务</div>
            <div className="text-4xl font-bold text-pink-800">
              {data?.dayMintCount || 0}
              <span className="text-xl font-normal text-pink-600/70">/28</span>
            </div>
            <div className="mt-2 text-sm text-pink-700">已完成 {overallProgress}%</div>
          </div>
        </div>

        {data?.shouldComposeFinal && (
          <div className="mt-6 rounded-2xl bg-gradient-to-r from-pink-200 to-rose-200 p-6 border border-pink-200 shadow-sm animate-fade-in">
            <div className="text-pink-800">
              <div className="text-lg font-semibold mb-2">🎉 恭喜完成28天挑战！</div>
              <div className="text-sm text-pink-700/90 mb-4">你已经完成了所有任务，现在可以合成最终纪念徽章了</div>
              <button
                className="px-6 py-3 rounded-xl bg-white text-pink-700 font-medium hover:bg-pink-50/50 transition-all shadow-sm btn-press"
                onClick={handleComposeFinal}
              >
                合成最终徽章
              </button>
            </div>
          </div>
        )}

        {!data?.shouldComposeFinal && mintableDayIndex && (
          <div className="mt-6 rounded-2xl border border-pink-100 bg-pink-50/30 p-5 animate-slide-in">
            <div className="text-sm text-pink-700 mb-3">继续你的旅程</div>
            <button
              className="px-5 py-2 rounded-xl border border-pink-100 bg-white text-pink-700 text-sm hover:bg-pink-50/50 transition-all btn-press"
              onClick={() => router.push(`/daily/${mintableDayIndex}`)}
            >
              前往第 {mintableDayIndex} 天 →
            </button>
          </div>
        )}

        <div className="mt-6 rounded-2xl border border-pink-100 bg-white/90 p-6 animate-slide-in">
          <div className="text-sm font-medium text-pink-700 mb-4">已完成的天数</div>
          <div className="flex flex-wrap gap-2">
            {completedDays.length ? (
              completedDays.map((d, i) => (
                <button
                  key={d}
                  className="px-3 py-2 rounded-xl border border-pink-100 bg-pink-50/50 text-pink-700 text-sm hover:bg-pink-50 transition-all btn-press animate-fade-in"
                  style={{ animationDelay: `${i * 0.05}s` }}
                  onClick={() => router.push(`/daily/${d}`)}
                >
                  第 {d} 天
                </button>
              ))
            ) : (
              <div className="text-sm text-pink-600/70">还没有完成的任务，去开始你的第一天吧！</div>
            )}
          </div>
        </div>
      </div>

      <div className="rounded-2xl border border-pink-100 bg-white/80 backdrop-blur-sm p-6 shadow-sm card-hover animate-slide-in">
        <div className="text-sm font-medium text-pink-700 mb-4">🏆 成就</div>
        <div className="space-y-3">
          <div className="p-4 rounded-xl bg-pink-50/30 border border-pink-100">
            <div className="text-sm font-medium text-pink-700 mb-1">
              {data?.finalMinted ? "🎉 最终徽章" : "最终徽章"}
            </div>
            <div className="text-xs text-pink-600/70">
              {data?.finalMinted ? "已获得" : "未获得"}
            </div>
          </div>
        </div>

        <div className="mt-6 pt-6 border-t border-pink-100">
          <div className="text-sm font-medium text-pink-700 mb-3">报告</div>
          <div className="space-y-2">
            <button
              className="w-full px-4 py-2 rounded-xl border border-pink-100 bg-white text-pink-700 text-sm hover:bg-pink-50/50 transition-all text-left btn-press"
              onClick={() => router.push("/report?range=week")}
            >
              查看周报
            </button>
            <button
              className="w-full px-4 py-2 rounded-xl border border-pink-100 bg-white text-pink-700 text-sm hover:bg-pink-50/50 transition-all text-left btn-press"
              onClick={() => router.push("/report?range=final")}
            >
              查看结营报告
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
