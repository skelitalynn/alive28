"use client";

import { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import NeedAddress from "../../../components/NeedAddress";
import { api } from "../../../lib/api";
import { useAddress } from "../../../components/addressContext";

export default function MilestonePage() {
  const params = useParams();
  const router = useRouter();
  const { address, ready } = useAddress();

  const idRaw = params?.id;
  const idValue = Array.isArray(idRaw) ? idRaw[0] : idRaw;
  const milestoneId = idValue === "final" ? 3 : Number(idValue);
  const isValidId = milestoneId === 1 || milestoneId === 2 || milestoneId === 3;
  const isFinal = milestoneId === 3;
  const apiMode = process.env.NEXT_PUBLIC_API_MODE || "mock";
  const canMintMilestone = apiMode !== "http" || isFinal;

  const [loading, setLoading] = useState(false);

  if (!ready) return null;
  if (!address) return <NeedAddress />;

  if (!isValidId) {
    return (
      <div className="max-w-3xl mx-auto rounded-2xl border border-slate-200 p-8 text-center">
        <div className="text-2xl font-semibold text-slate-900">无效里程碑</div>
        <div className="mt-2 text-sm text-slate-500">请检查链接是否正确。</div>
        <div className="mt-6">
          <button
            className="px-6 py-3 rounded-xl border border-slate-200 font-semibold hover:bg-slate-50"
            onClick={() => router.push("/")}
          >
            返回首页
          </button>
        </div>
      </div>
    );
  }

  const handleMint = async () => {
    if (!canMintMilestone) {
      alert("后端未提供里程碑 NFT 接口，请先使用 mock 模式或等后端补齐。");
      return;
    }
    setLoading(true);
    try {
      if (isFinal) {
        await api.composeFinal({ address });
        alert("🎉 结营 NFT 铸造成功！");
      } else {
        await api.mintMilestone({ address, milestoneId });
        alert(`🎉 Week ${milestoneId} 里程碑 NFT 铸造成功！`);
      }
      window.dispatchEvent(new Event("alive28:store"));
    } catch (e: any) {
      alert(e.message || "Mint failed");
    } finally {
      setLoading(false);
    }
  };

  const nextDay = milestoneId === 1 ? 8 : milestoneId === 2 ? 15 : null;

  return (
        <div className="max-w-3xl mx-auto rounded-2xl border border-slate-200 p-8 text-center">
            <div className="text-4xl mb-4">🏆</div>
            <h1 className="text-2xl font-bold text-slate-900">
                {isFinal ? "恭喜完成 28 天挑战" : `恭喜完成第 ${milestoneId} 周`}
            </h1>
            <p className="mt-4 text-slate-600 leading-relaxed">
                {milestoneId === 1 && "你已经坚持了 7 天。这是第一个重要的里程碑。"}
                {milestoneId === 2 && "14 天过去了，你已经走过了一半的旅程。"}
                {isFinal && "28 天，你做到了。这不是结束，而是新的开始。"}
                <br />
                现在，铸造属于你的里程碑 NFT 吧。
            </p>

            <div className="mt-8 flex justify-center gap-4">
                <button
                    className="px-6 py-3 rounded-xl bg-slate-900 text-white font-semibold hover:bg-slate-800 disabled:opacity-50"
                    onClick={handleMint}
                    disabled={loading || !canMintMilestone}
                >
                    {loading ? "铸造中..." : "铸造里程碑 NFT"}
                </button>

                {nextDay && (
                    <button
                        className="px-6 py-3 rounded-xl border border-slate-200 font-semibold hover:bg-slate-50"
                        onClick={() => router.push(`/daily/${nextDay}`)}
                    >
                        开启第 {nextDay} 天
                    </button>
                )}
                {isFinal && (
                    <button
                        className="px-6 py-3 rounded-xl border border-slate-200 font-semibold hover:bg-slate-50"
                        onClick={() => router.push(`/report?range=final`)}
                    >
                        查看结营报告
                    </button>
                )}
            </div>

            <div className="mt-8 text-xs text-slate-400">
                里程碑 ID: {milestoneId} · 风格保持一致
            </div>
        </div>
    );
}
