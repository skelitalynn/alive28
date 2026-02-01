"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "../lib/api";
import { useAddress } from "../components/addressContext";

export default function HomePage() {
  const router = useRouter();
  const { address, storeVersion, ready } = useAddress();
  const [dayBtnLabel, setDayBtnLabel] = useState("Day 1");
  const [dayBtnTarget, setDayBtnTarget] = useState(1);
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    if (!ready) return;
    api.getHomeSnapshot(address).then((res) => {
      setDayBtnLabel(res.dayBtnLabel);
      setDayBtnTarget(res.dayBtnTarget);
    });
    if (address) {
      api.getProgress({ address }).then((data) => {
        const p = Math.round(((data?.dayMintCount || 0) / 28) * 100);
        setProgress(p);
      });
    }
  }, [address, storeVersion, ready]);

  if (!ready) return null;

  if (!address) {
    return (
      <div className="max-w-2xl mx-auto text-center py-12 animate-fade-in">
        <div className="text-6xl mb-6 animate-pulse-slow">🌿</div>
        <h1 className="text-3xl font-semibold text-pink-800 mb-4">欢迎来到 Alive28</h1>
        <p className="text-lg text-pink-600/80 leading-relaxed mb-8">
          这是一段28天的自我探索之旅<br />
          每天一个小任务，记录你的感受与成长<br />
          让我们开始吧 ✨
        </p>
        <div className="mt-8 text-sm text-pink-500/70">
          请在上方设置你的身份标识，开始这段美好的旅程
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto animate-fade-in">
      <div className="rounded-2xl border border-pink-100 bg-white/80 backdrop-blur-sm p-8 shadow-sm card-hover">
        <div className="text-center mb-8">
          <div className="text-5xl mb-4 animate-pulse-slow">💫</div>
          <h1 className="text-2xl font-semibold text-pink-800 mb-2">今天也要加油呀</h1>
          <p className="text-pink-600/70">继续你的成长之旅，记录当下的感受</p>
        </div>

        {/* 进度条 */}
        {progress > 0 && (
          <div className="mb-6 animate-slide-in">
            <div className="flex justify-between text-sm text-pink-600/70 mb-2">
              <span>整体进度</span>
              <span>{progress}%</span>
            </div>
            <div className="progress-bar">
              <div className="progress-fill" style={{ width: `${progress}%` }}></div>
            </div>
          </div>
        )}

        <div className="mt-8 flex flex-wrap justify-center gap-4">
          <button
            className="px-8 py-4 rounded-2xl bg-gradient-to-r from-pink-200 to-rose-200 text-pink-700 text-lg font-medium hover:from-pink-300 hover:to-rose-300 transition-all shadow-sm transform hover:scale-105 btn-press"
            onClick={() => router.push(`/daily/${dayBtnTarget}`)}
          >
            {dayBtnLabel}
          </button>
          <button
            className="px-6 py-4 rounded-2xl border border-pink-100 bg-white/90 text-pink-700 text-base hover:bg-pink-50/50 transition-all btn-press"
            onClick={() => router.push("/progress")}
          >
            查看进度
          </button>
          <button
            className="px-6 py-4 rounded-2xl border border-pink-100 bg-white/90 text-pink-700 text-base hover:bg-pink-50/50 transition-all btn-press"
            onClick={() => router.push("/report?range=week")}
          >
            我的周报
          </button>
        </div>
      </div>
    </div>
  );
}
