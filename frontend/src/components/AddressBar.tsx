"use client";

import { useAddress } from "./addressContext";

export default function AddressBar() {
  const { address, input, setInput, applyInputAsAddress, randomAddress, resetData, inputRef } = useAddress();

  return (
    <div className="mt-5 rounded-2xl border border-slate-200 p-4">
      <div className="flex flex-col md:flex-row md:items-center gap-3">
        <div className="flex-1">
          <div className="text-sm text-slate-500">当前地址（模拟钱包）</div>
          <div className="mt-1 font-mono text-sm break-all">{address ? address.toLowerCase() : "未连接"}</div>
        </div>
        <div className="flex flex-col sm:flex-row gap-2">
          <input
            ref={inputRef}
            className="px-3 py-2 rounded-xl border border-slate-200 w-full sm:w-80 font-mono text-sm"
            placeholder="输入 0x... 或点随机生成"
            value={input}
            onChange={(e) => setInput(e.target.value)}
          />
          <button
            className="px-3 py-2 rounded-xl bg-slate-900 text-white text-sm hover:bg-slate-800"
            onClick={applyInputAsAddress}
          >
            设为当前
          </button>
          <button className="px-3 py-2 rounded-xl border border-slate-200 text-sm hover:bg-slate-50" onClick={randomAddress}>
            随机地址
          </button>
          <button
            className="px-3 py-2 rounded-xl border border-rose-200 text-rose-600 text-sm hover:bg-rose-50"
            onClick={resetData}
          >
            清空数据
          </button>
        </div>
      </div>
      <div className="mt-3 text-xs text-slate-500">
        说明：这是前端纯模拟版本。链上 submitProof/mintDay/composeFinal 这里不发真实交易，只是模拟“确认”并记录 txHash。
        （你之后接入 wagmi/viem 时，把确认按钮替换成真实交易即可）
      </div>
    </div>
  );
}
