"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { useAccount, useChainId, useWriteContract } from "wagmi";
import { getDailyPrompt, checkin, confirmTx } from "../../../lib/api";
import { ProofRegistryABI } from "../../../lib/abi";

export default function DailyPage() {
  const params = useParams();
  const dayIndex = Number(params.dayIndex);
  const { address } = useAccount();
  const chainId = useChainId();
  const [prompt, setPrompt] = useState<any>(null);
  const [text, setText] = useState("");
  const [result, setResult] = useState<any>(null);
  const [txHash, setTxHash] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const { writeContractAsync } = useWriteContract();

  useEffect(() => {
    setError(null);
    getDailyPrompt(dayIndex)
      .then(setPrompt)
      .catch((e) => {
        setPrompt(null);
        setError(e?.message || "无法获取任务卡，请确认后端是否启动");
      });
  }, [dayIndex]);

  const onCheckin = async () => {
    if (!address) return;
    try {
      setError(null);
      const payload = {
        address,
        timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
        text
      };
      const data = await checkin(payload);
      setResult(data);
    } catch (e: any) {
      setError(e?.message || "请求失败，请确认后端可访问");
    }
  };

  const onSubmitProof = async () => {
    if (!result) return;
    try {
      setError(null);
      const proofRegistry = process.env.NEXT_PUBLIC_PROOF_REGISTRY as `0x${string}`;
      const hash = result.proofHash as `0x${string}`;
      const tx = await writeContractAsync({
        address: proofRegistry,
        abi: ProofRegistryABI,
        functionName: "submitProof",
        args: [result.dayIndex, hash]
      });
      setTxHash(tx as string);

      await confirmTx({
        logId: result.logId,
        address,
        txHash: tx,
        chainId,
        contractAddress: proofRegistry
      });
    } catch (e: any) {
      setError(e?.message || "上链或回传失败");
    }
  };

  return (
    <main className="min-h-screen p-10 space-y-6">
      <h1 className="text-2xl font-bold">Day {dayIndex}</h1>
      {prompt && (
        <div className="p-4 bg-[#15151a] rounded">
          <div className="text-lg font-semibold">{prompt.title}</div>
          <div className="text-sm text-gray-300">{prompt.instruction}</div>
          {prompt.hint && <div className="text-xs text-gray-400 mt-2">{prompt.hint}</div>}
        </div>
      )}

      <textarea
        className="w-full p-3 rounded bg-[#222]"
        rows={4}
        placeholder="写下今天一句话..."
        value={text}
        onChange={(e) => setText(e.target.value)}
      />

      <button className="px-4 py-2 bg-[#35d0ba] text-black rounded" onClick={onCheckin}>
        打卡并生成 proofHash
      </button>
      {error && <div className="text-xs text-red-400">{error}</div>}

      {result && (
        <div className="p-4 bg-[#15151a] rounded space-y-2">
          <div className="text-sm">Reflection</div>
          <div className="text-sm">note: {result.reflection.note}</div>
          <div className="text-sm">next: {result.reflection.next}</div>
          <details className="text-xs text-gray-400">
            <summary>proofHash</summary>
            {result.proofHash}
          </details>
          <button className="px-4 py-2 bg-[#222] rounded" onClick={onSubmitProof}>
            上链提交
          </button>
          {txHash && <div className="text-xs">txHash: {txHash}</div>}
        </div>
      )}
    </main>
  );
}
