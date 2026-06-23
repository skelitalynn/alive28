"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { useAccount, usePublicClient, useWalletClient } from "wagmi";
import NeedAddress from "../../../components/NeedAddress";
import { api } from "../../../lib/api";
import { useAddress } from "../../../components/addressContext";
import { mintMilestoneNFT } from "../../../lib/nft/mintMilestone";
import { getMilestoneImageForId } from "../../../lib/nft/milestoneNFT";

export default function MilestonePage() {
  const params = useParams();
  const router = useRouter();
  const { address, ready } = useAddress();
  const { address: wagmiAddress, isConnected } = useAccount();
  const publicClient = usePublicClient();
  const { data: walletClient } = useWalletClient();

  const idRaw = params?.id;
  const idValue = Array.isArray(idRaw) ? idRaw[0] : idRaw;
  const milestoneId = idValue === "final" ? 3 : Number(idValue);
  const isValidId = milestoneId === 1 || milestoneId === 2 || milestoneId === 3;
  const isFinal = milestoneId === 3;

  const [loading, setLoading] = useState(false);
  const [mintedImage, setMintedImage] = useState<string | null>(null);
  const [demoMode, setDemoMode] = useState<boolean | null>(null);

  useEffect(() => {
    api.getConfig().then((c) => setDemoMode(c.demo_mode)).catch(() => setDemoMode(false));
  }, []);

  if (!ready) return null;
  if (!address) return <NeedAddress />;

  if (!isValidId) {
    return (
      <div className="max-w-3xl mx-auto rounded-2xl border border-pink-100 bg-white/80 backdrop-blur-sm p-8 text-center shadow-sm animate-fade-in">
        <div className="text-2xl font-semibold text-pink-800">里程碑不存在</div>
        <div className="mt-2 text-sm text-pink-700/70">请从进度页进入正确的里程碑</div>
        <div className="mt-6">
          <button
            className="px-6 py-3 rounded-xl border border-pink-100 bg-white text-pink-700 font-semibold hover:bg-pink-50/50 transition-all btn-press"
            onClick={() => router.push("/")}
          >
            返回首页
          </button>
        </div>
      </div>
    );
  }

  // 本里程碑对应的图片（来自 public/nft，不依赖合约）
  const milestoneImage = getMilestoneImageForId(milestoneId as 1 | 2 | 3);
  const isDemoMode = demoMode === true;

  const handleMint = async () => {
    setLoading(true);
    try {
      // 未连接钱包：只走后端记录，并展示本地 NFT 图片（DEMO 行为）
      if (!isConnected || !wagmiAddress || !walletClient || !publicClient) {
        await api.mintMilestone({ address, milestoneId });
        setMintedImage(milestoneImage);
        alert(`已记录里程碑 ${milestoneId}`);
        window.dispatchEvent(new Event("alive28:store"));
        setLoading(false);
        return;
      }

      setMintedImage(milestoneImage);

      // DEMO_MODE：连接钱包也仅走后端记录，不上链
      if (isDemoMode) {
        await api.mintMilestone({ address: wagmiAddress, milestoneId });
        alert(`已记录里程碑 ${milestoneId}（DEMO 模式）`);
        window.dispatchEvent(new Event("alive28:store"));
        setLoading(false);
        return;
      }

      // 正常模式：必须上链铸造
      const preparation = await api.prepareMilestone({
        address: wagmiAddress,
        milestoneId
      });
      const { txHash } = await mintMilestoneNFT(
        wagmiAddress as `0x${string}`,
        milestoneId,
        BigInt(preparation.tokenId),
        preparation.tokenUri,
        publicClient,
        walletClient
      );
      await api.mintMilestone({ address: wagmiAddress, milestoneId, txHash });
      alert(`✅ 里程碑 NFT 铸造成功\n交易: ${txHash.slice(0, 10)}...`);
      window.dispatchEvent(new Event("alive28:store"));
    } catch (e: any) {
      console.error("Mint error:", e);
      alert(e?.message || "操作失败，请重试");
    } finally {
      setLoading(false);
    }
  };

  const nextDay = milestoneId === 1 ? 8 : milestoneId === 2 ? 15 : null;

  const milestoneMessages = {
    1: {
      emoji: "🌱",
      title: "第 7 天里程碑",
      message: "你已经坚持了一周，这是一个很棒的开始。继续把每天的感受记录下来。",
      nextMessage: "继续第 8 天"
    },
    2: {
      emoji: "🌸",
      title: "第 14 天里程碑",
      message: "两周的坚持很不容易，你已经在用行动照顾自己。",
      nextMessage: "继续第 15 天"
    },
    3: {
      emoji: "🏁",
      title: "第 28 天结营里程碑",
      message: "恭喜完成 28 天游程，愿你带着这些感受继续前行。",
      nextMessage: "查看结营报告"
    }
  };

  const current = milestoneMessages[milestoneId as keyof typeof milestoneMessages];

  return (
    <div className="max-w-3xl mx-auto rounded-2xl border border-pink-100 bg-white/80 backdrop-blur-sm p-8 text-center shadow-sm animate-fade-in card-hover">
      <div className="text-6xl mb-6 animate-pulse-slow">{current.emoji}</div>
      <h1 className="text-3xl font-bold text-pink-800 mb-4">{current.title}</h1>
      <p className="mt-4 text-pink-700 leading-relaxed text-lg">{current.message}</p>

      {/* 始终展示本里程碑对应的 NFT 图片（来自 public/nft，无需合约） */}
      <div className="mt-6 animate-fade-in">
        <div className="text-sm text-pink-700/70 mb-2">{mintedImage ? "你的里程碑 NFT" : "本里程碑 NFT"}</div>
        <div className="inline-block p-4 rounded-2xl bg-pink-50/50 border border-pink-100">
          <img
            src={milestoneImage}
            alt={`Milestone ${milestoneId} NFT`}
            className="w-48 h-48 object-contain rounded-xl"
          />
        </div>
      </div>

      <div className="mt-8 flex justify-center gap-4 flex-wrap">
        <button
          className="px-8 py-4 rounded-2xl bg-gradient-to-r from-pink-200 to-rose-200 text-pink-700 font-semibold hover:from-pink-300 hover:to-rose-300 transition-all shadow-sm transform hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed btn-press"
          onClick={handleMint}
          disabled={loading || demoMode === null}
        >
          {loading ? "处理中..." : demoMode === null ? "加载中..." : isConnected && !isDemoMode ? "铸造里程碑 NFT" : "记录里程碑"}
        </button>

        {nextDay && (
          <button
            className="px-6 py-4 rounded-2xl border border-pink-100 bg-white text-pink-700 font-semibold hover:bg-pink-50/50 transition-all btn-press"
            onClick={() => router.push(`/daily/${nextDay}`)}
          >
            {current.nextMessage}
          </button>
        )}
        {isFinal && (
          <button
            className="px-6 py-4 rounded-2xl border border-pink-100 bg-white text-pink-700 font-semibold hover:bg-pink-50/50 transition-all btn-press"
            onClick={() => router.push(`/report?range=final`)}
          >
            查看结营报告
          </button>
        )}
      </div>

    </div>
  );
}
