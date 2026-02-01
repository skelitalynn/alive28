"use client";

import { useAccount, useConnect, useDisconnect } from "wagmi";
import { useAddress } from "./addressContext";

export default function WalletConnect() {
  const { address: wagmiAddress, isConnected } = useAccount();
  const { connect, connectors, isPending } = useConnect();
  const { disconnect } = useDisconnect();
  const { setAddress } = useAddress();

  // 当钱包连接时，同步地址到 addressContext
  if (isConnected && wagmiAddress) {
    setAddress(wagmiAddress);
  }

  if (isConnected) {
    return (
      <div className="flex items-center gap-3">
        <div className="px-4 py-2 rounded-xl border border-pink-100 bg-white/80 text-pink-700 text-sm">
          {wagmiAddress?.slice(0, 6)}...{wagmiAddress?.slice(-4)}
        </div>
        <button
          className="px-4 py-2 rounded-xl border border-pink-100 bg-white text-pink-700 text-sm hover:bg-pink-50/50 transition-all btn-press"
          onClick={() => disconnect()}
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
