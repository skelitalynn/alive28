"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { useAccount, useConnect, useDisconnect } from "wagmi";
import { useAddress } from "./addressContext";

export default function WalletConnect() {
  const router = useRouter();
  const { address: wagmiAddress, isConnected } = useAccount();
  const { connect, connectors, isPending } = useConnect();
  const { disconnect } = useDisconnect();
  const { setAddress } = useAddress();
  const wasConnected = useRef(false);
  const [mounted, setMounted] = useState(false);

  // 避免服务端与客户端渲染不一致导致 Hydration 错误：仅在客户端挂载后再按钱包状态渲染
  useEffect(() => setMounted(true), []);

  // 当钱包连接时，同步地址到 addressContext（标记来源为钱包，刷新后若未连接则不恢复）
  if (mounted && isConnected && wagmiAddress) {
    setAddress(wagmiAddress, "wallet");
  }

  // 仅当「从已连接变为未连接」时清空身份并跳回首页（例如在钱包插件里断开）
  useEffect(() => {
    if (!mounted) return;
    if (isConnected) wasConnected.current = true;
    else if (wasConnected.current) {
      wasConnected.current = false;
      setAddress("");
      router.push("/");
    }
  }, [mounted, isConnected, setAddress, router]);

  if (!mounted) {
    return (
      <div className="flex items-center gap-2">
        <div className="px-4 py-2 rounded-xl border border-pink-100 bg-white/80 text-pink-500/70 text-sm animate-pulse">
          加载中...
        </div>
      </div>
    );
  }

  if (isConnected) {
    return (
      <div className="flex items-center gap-3">
        <div className="px-4 py-2 rounded-xl border border-pink-100 bg-white/80 text-pink-700 text-sm">
          {wagmiAddress?.slice(0, 6)}...{wagmiAddress?.slice(-4)}
        </div>
        <button
          className="px-4 py-2 rounded-xl border border-pink-100 bg-white text-pink-700 text-sm hover:bg-pink-50/50 transition-all btn-press"
          onClick={() => {
            setAddress("");
            disconnect();
            router.push("/");
          }}
        >
          断开
        </button>
      </div>
    );
  }

  return (
    <div className="flex items-center gap-2">
      {connectors.map((connector) => (
        <button
          key={connector.uid}
          className="px-4 py-2 rounded-xl bg-gradient-to-r from-pink-200 to-rose-200 text-pink-700 text-sm font-medium hover:from-pink-300 hover:to-rose-300 transition-all shadow-sm btn-press disabled:opacity-50"
          onClick={() => connect({ connector })}
          disabled={isPending}
        >
          {isPending ? "连接中..." : `连接 ${connector.name}`}
        </button>
      ))}
    </div>
  );
}
