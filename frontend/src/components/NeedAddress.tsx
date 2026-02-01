"use client";

import { useAddress } from "./addressContext";

export default function NeedAddress() {
  const { focusInput, randomAddress } = useAddress();

  return (
    <div className="rounded-2xl border border-pink-100 bg-white/80 backdrop-blur-sm p-8 text-center shadow-sm animate-fade-in">
      <div className="text-4xl mb-4 animate-pulse-slow">🌱</div>
      <div className="text-xl font-semibold text-pink-800">开始你的成长之旅</div>
      <div className="mt-2 text-pink-600/70 text-sm">请先设置你的身份标识，让我们开始这段美好的旅程</div>
      <div className="mt-6 flex justify-center gap-3">
        <button 
          className="px-6 py-3 rounded-xl bg-gradient-to-r from-pink-200 to-rose-200 text-pink-700 text-sm font-medium hover:from-pink-300 hover:to-rose-300 transition-all shadow-sm btn-press" 
          onClick={focusInput}
        >
          设置标识
        </button>
        <button 
          className="px-6 py-3 rounded-xl border border-pink-100 bg-white text-pink-600 text-sm hover:bg-pink-50/50 transition-all btn-press" 
          onClick={randomAddress}
        >
          快速开始
        </button>
      </div>
    </div>
  );
}
