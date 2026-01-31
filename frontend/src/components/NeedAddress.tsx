"use client";

import { useAddress } from "./addressContext";

export default function NeedAddress() {
  const { focusInput, randomAddress } = useAddress();

  return (
    <div className="rounded-2xl border border-slate-200 p-6">
      <div className="text-lg font-semibold">先设置一个地址</div>
      <div className="mt-2 text-slate-500 text-sm">这是纯前端模拟：需要一个 address 来写入 LocalStorage 进度。</div>
      <div className="mt-4 flex gap-2">
        <button className="px-3 py-2 rounded-xl bg-slate-900 text-white text-sm" onClick={focusInput}>
          去上面输入地址
        </button>
        <button className="px-3 py-2 rounded-xl border border-slate-200 text-sm" onClick={randomAddress}>
          随机生成
        </button>
      </div>
    </div>
  );
}
