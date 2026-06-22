"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { useAccount, useConnect, useDisconnect, useSignMessage } from "wagmi";
import { useAddress } from "./addressContext";
import { api } from "../lib/api";

export default function WalletConnect() {
  const router = useRouter();
  const { address: wagmiAddress, isConnected } = useAccount();
  const { connect, connectors, isPending } = useConnect();
  const { disconnect } = useDisconnect();
  const { signMessageAsync } = useSignMessage();
  const { setAddress } = useAddress();
  const wasConnected = useRef(false);
  const authenticatedAddress = useRef<string | null>(null);
  const [mounted, setMounted] = useState(false);
  const [isAuthenticating, setIsAuthenticating] = useState(false);
  const [authError, setAuthError] = useState<string | null>(null);

  // 避免服务端与客户端渲染不一致导致 Hydration 错误：仅在客户端挂载后再按钱包状态渲染
  useEffect(() => setMounted(true), []);

  useEffect(() => {
    if (!mounted || !isConnected || !wagmiAddress) return;
    const normalized = wagmiAddress.toLowerCase();
    if (authenticatedAddress.current === normalized) return;

    let cancelled = false;
    setIsAuthenticating(true);
    setAuthError(null);
    api.authenticateWallet(
      normalized,
      (message) => signMessageAsync({ message })
    )
      .then(() => {
        if (cancelled) return;
        authenticatedAddress.current = normalized;
        setAddress(normalized, "wallet");
      })
      .catch((error) => {
        if (cancelled) return;
        api.clearWalletSession();
        authenticatedAddress.current = null;
        setAddress("");
        setAuthError(error?.message || "钱包签名认证失败");
      })
      .finally(() => {
        if (!cancelled) setIsAuthenticating(false);
      });
    return () => {
      cancelled = true;
    };
  }, [mounted, isConnected, wagmiAddress, setAddress, signMessageAsync]);

  // 仅当「从已连接变为未连接」时清空身份并跳回首页（例如在钱包插件里断开）
  useEffect(() => {
    if (!mounted) return;
    if (isConnected) wasConnected.current = true;
    else if (wasConnected.current) {
      wasConnected.current = false;
      authenticatedAddress.current = null;
      api.clearWalletSession();
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
          {isAuthenticating
            ? "等待钱包签名..."
            : `${wagmiAddress?.slice(0, 6)}...${wagmiAddress?.slice(-4)}`}
        </div>
        <button
          className="px-4 py-2 rounded-xl border border-pink-100 bg-white text-pink-700 text-sm hover:bg-pink-50/50 transition-all btn-press"
          onClick={() => {
            authenticatedAddress.current = null;
            api.clearWalletSession();
            setAddress("");
            disconnect();
            router.push("/");
          }}
        >
          断开
        </button>
        {authError && <div className="text-xs text-red-500">{authError}</div>}
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
