"use client";

import { useAccount, useConnect, useDisconnect } from "wagmi";
import { useState } from "react";
import Link from "next/link";

export default function EnterPage() {
  const { address, isConnected } = useAccount();
  const { connect, connectors } = useConnect();
  const { disconnect } = useDisconnect();
  const [started, setStarted] = useState(false);

  return (
    <main className="min-h-screen p-10">
      <h1 className="text-2xl font-bold mb-4">进入挑战</h1>
      {!isConnected ? (
        <button className="px-4 py-2 bg-[#35d0ba] text-black rounded" onClick={() => connect({ connector: connectors[0] })}>
          连接钱包
        </button>
      ) : (
        <div className="space-y-4">
          <div className="text-sm">已连接：{address}</div>
          <button className="px-4 py-2 bg-[#222] rounded" onClick={() => disconnect()}>
            断开
          </button>
          <button className="px-4 py-2 bg-[#35d0ba] text-black rounded" onClick={() => setStarted(true)}>
            开始 28 天挑战
          </button>
          {started && (
            <div className="mt-4">
              <Link className="underline" href="/daily/1">进入 Day 1</Link>
            </div>
          )}
        </div>
      )}
    </main>
  );
}
