"use client";

import { useRouter } from "next/navigation";

export default function TopBar() {
  const router = useRouter();

  return (
    <div className="flex items-center justify-between gap-3">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-2xl bg-slate-900 text-white grid place-items-center font-bold">A</div>
        <div>
          <div className="text-lg font-semibold leading-tight">Alive28 · 纯前端模拟</div>
          <div className="text-sm text-slate-500">无后端 / LocalStorage 记录 / keccak256 proofHash</div>
        </div>
      </div>

      <div className="flex items-center gap-2">
        <button
          className="px-3 py-2 rounded-xl border border-slate-200 hover:bg-slate-50 text-sm"
          onClick={() => router.push("/")}
        >
          首页
        </button>
        <button
          className="px-3 py-2 rounded-xl border border-slate-200 hover:bg-slate-50 text-sm"
          onClick={() => router.push("/progress")}
        >
          进度
        </button>
        <button
          className="px-3 py-2 rounded-xl border border-slate-200 hover:bg-slate-50 text-sm"
          onClick={() => router.push("/report?range=week")}
        >
          周报
        </button>
        <button
          className="px-3 py-2 rounded-xl border border-slate-200 hover:bg-slate-50 text-sm"
          onClick={() => router.push("/report?range=final")}
        >
          结营报告
        </button>
      </div>
    </div>
  );
}
