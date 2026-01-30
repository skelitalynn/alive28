"use client";

import { useState } from "react";
import { useAccount } from "wagmi";
import { getProgress } from "../../lib/api";
import Link from "next/link";

export default function ProgressPage() {
  const { address } = useAccount();
  const [data, setData] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  const load = async () => {
    if (!address) return;
    try {
      setError(null);
      const res = await getProgress(address);
      setData(res);
    } catch (e: any) {
      setError(e?.message || "无法获取进度，请确认后端是否启动");
    }
  };

  return (
    <main className="min-h-screen p-10 space-y-6">
      <h1 className="text-2xl font-bold">进度</h1>
      <button className="px-4 py-2 bg-[#35d0ba] text-black rounded" onClick={load}>
        刷新进度
      </button>
      {error && <div className="text-xs text-red-400">{error}</div>}
      {data && (
        <div className="p-4 bg-[#15151a] rounded space-y-2">
          <div>streak: {data.streak}</div>
          <div>completedDays: {data.completedDays.join(", ")}</div>
          <div>eligible7: {String(data.milestonesEligible.eligible7)}</div>
          <div>eligible14: {String(data.milestonesEligible.eligible14)}</div>
          <div>eligible28: {String(data.milestonesEligible.eligible28)}</div>
          <Link className="underline" href="/report">去报告</Link>
        </div>
      )}
    </main>
  );
}
