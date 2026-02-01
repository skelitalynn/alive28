"use client";

import { useRouter } from "next/navigation";

export default function TopBar() {
  const router = useRouter();

  return (
    <div className="flex items-center justify-between gap-3 animate-fade-in">
      <div className="flex items-center gap-3">
        <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-pink-200 to-rose-200 text-pink-700 grid place-items-center font-bold text-xl shadow-sm card-hover">
          ✨
        </div>
        <div>
          <div className="text-xl font-semibold leading-tight text-pink-800">HOPE小希</div>
          <div className="text-sm text-pink-600/70">28天心灵成长之旅</div>
        </div>
      </div>

      <div className="flex items-center gap-2">
        <button
          className="px-4 py-2 rounded-xl border border-pink-100 bg-white/70 hover:bg-pink-50/50 text-sm text-pink-700 transition-all duration-200 btn-press"
          onClick={() => router.push("/")}
        >
          首页
        </button>
        <button
          className="px-4 py-2 rounded-xl border border-pink-100 bg-white/70 hover:bg-pink-50/50 text-sm text-pink-700 transition-all duration-200 btn-press"
          onClick={() => router.push("/progress")}
        >
          我的进度
        </button>
        <button
          className="px-4 py-2 rounded-xl border border-pink-100 bg-white/70 hover:bg-pink-50/50 text-sm text-pink-700 transition-all duration-200 btn-press"
          onClick={() => router.push("/report?range=week")}
        >
          周报
        </button>
        <button
          className="px-4 py-2 rounded-xl border border-pink-100 bg-white/70 hover:bg-pink-50/50 text-sm text-pink-700 transition-all duration-200 btn-press"
          onClick={() => router.push("/report?range=final")}
        >
          结营报告
        </button>
      </div>
    </div>
  );
}
