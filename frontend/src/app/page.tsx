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

  useEffect(() => {
    if (!ready) return;
    api.getHomeSnapshot(address).then((res) => {
      setDayBtnLabel(res.dayBtnLabel);
      setDayBtnTarget(res.dayBtnTarget);
    });
  }, [address, storeVersion, ready]);

  if (!ready) return null;

  return (
    <div className="grid md:grid-cols-2 gap-4">
      <div className="rounded-2xl border border-slate-200 p-6">
        <div className="text-xl font-semibold">你要看到的效果</div>
        <div className="mt-2 text-sm text-slate-600 leading-relaxed">
          这是 Alive28 的“可点可跑”前端 Demo：<br />
          - 每日任务卡（Day 1..28）<br />
          - 输入一句话 → 生成 note/next<br />
          - 生成 proofHash（keccak256）<br />
          - 模拟 submitProof / mintDay / composeFinal（记录 txHash）<br />
          - 进度页/报告页（ECharts）
        </div>

        <div className="mt-5 flex flex-wrap gap-2">
          <button
            className="px-3 py-2 rounded-xl bg-slate-900 text-white text-sm hover:bg-slate-800"
            onClick={() => router.push(`/daily/${dayBtnTarget}`)}
          >
            {dayBtnLabel}
          </button>
          <button
            className="px-3 py-2 rounded-xl border border-slate-200 text-sm hover:bg-slate-50"
            onClick={() => router.push("/progress")}
          >
            进度页
          </button>
          <button
            className="px-3 py-2 rounded-xl border border-slate-200 text-sm hover:bg-slate-50"
            onClick={() => router.push("/report?range=week")}
          >
            周报
          </button>
        </div>

        <div className="mt-6 text-xs text-slate-500">
          当前模式：mock（LocalStorage）。之后接你后端：把 mockClient 换成 httpClient 即可。
        </div>
      </div>

      <div className="rounded-2xl border border-slate-200 p-6">
        <div className="text-xl font-semibold">快速提示</div>
        <div className="mt-2 text-sm text-slate-600 leading-relaxed">
          1) 上面先设置一个 address（随便填一个 0x...）<br />
          2) 去 Daily 页做一次打卡<br />
          3) 点“模拟提交 Proof”→ 记录 txHash<br />
          4) 点“模拟 Mint Day SBT”→ dayMintCount +1<br />
          5) 进度页会显示 shouldComposeFinal 条件（这里你得把 1..28 都打卡才能合成）
        </div>

        <div className="mt-5 rounded-xl bg-slate-50 p-4">
          <div className="text-sm font-semibold">当前地址</div>
          <div className="mt-1 font-mono text-sm break-all">{address ? address : "未连接"}</div>
          <div className="mt-3 text-xs text-slate-500">这只是模拟；真实版本用 wagmi/viem 连接钱包并发交易。</div>
        </div>
      </div>
    </div>
  );
}
