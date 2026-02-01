"use client";

import { useAddress } from "./addressContext";
import WalletConnect from "./WalletConnect";
import { useAccount } from "wagmi";
import { useEffect } from "react";

export default function AddressBar() {
  const { address, input, setInput, applyInputAsAddress, randomAddress, resetData, inputRef, setAddress } = useAddress();
  const { address: wagmiAddress, isConnected } = useAccount();

  // 同步钱包地址到 addressContext（标记为钱包来源）
  useEffect(() => {
    if (isConnected && wagmiAddress) {
      setAddress(wagmiAddress, "wallet");
    }
  }, [isConnected, wagmiAddress, setAddress]);

  // 如果已连接钱包，显示钱包信息
  if (isConnected && wagmiAddress) {
    return (
      <div className="mt-5 rounded-2xl border border-pink-100 bg-white/80 backdrop-blur-sm p-4 shadow-sm animate-fade-in">
        <WalletConnect />
      </div>
    );
  }

  // 如果已有地址（手动输入），不显示
  if (address) {
    return null;
  }

  return (
    <div className="mt-5 rounded-2xl border border-pink-100 bg-white/80 backdrop-blur-sm p-6 shadow-sm animate-fade-in card-hover">
      <div className="flex flex-col md:flex-row md:items-center gap-4">
        <div className="flex-1">
          <div className="text-sm text-pink-800 font-medium">开始你的旅程</div>
          <div className="mt-1 text-sm text-pink-700/70">连接钱包或设置你的身份标识</div>
        </div>
        <div className="flex flex-col gap-3">
          <div className="flex flex-col sm:flex-row gap-2">
            <WalletConnect />
          </div>
          <div className="text-xs text-pink-600/70 text-center">或</div>
          <div className="flex flex-col sm:flex-row gap-2">
            <input
              ref={inputRef}
              className="px-4 py-2 rounded-xl border border-pink-100 bg-white w-full sm:w-80 text-sm text-pink-900 placeholder:text-pink-400/60 focus:outline-none focus:ring-2 focus:ring-pink-200 transition-all"
              placeholder="输入你的标识..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
            />
            <button
              className="px-4 py-2 rounded-xl bg-gradient-to-r from-pink-200 to-rose-200 text-pink-700 text-sm font-medium hover:from-pink-300 hover:to-rose-300 transition-all shadow-sm btn-press"
              onClick={applyInputAsAddress}
            >
              开始
            </button>
            <button 
              className="px-4 py-2 rounded-xl border border-pink-100 bg-white text-pink-600 text-sm hover:bg-pink-50/50 transition-all btn-press" 
              onClick={randomAddress}
            >
              快速开始
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
