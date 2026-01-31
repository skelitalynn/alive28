"use client";

import { useEffect, useMemo, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import NeedAddress from "../../../components/NeedAddress";
import { api } from "../../../lib/api";
import { useAddress } from "../../../components/addressContext";
import type { DailyLog, DailyTask } from "../../../lib/store/schema";

export default function DailyPage() {
  const params = useParams();
  const router = useRouter();
  const { address, storeVersion, ready } = useAddress();

  const rawParam = params?.dayIndex;
  const rawDayIndex = Array.isArray(rawParam) ? rawParam[0] : rawParam;
  const parsed = Number(rawDayIndex || "1");
  const dayIndex = Number.isFinite(parsed) ? parsed : 1;

  const [task, setTask] = useState<DailyTask | null>(null);
  const [dateKey, setDateKey] = useState("");
  const [log, setLog] = useState<DailyLog | null>(null);
  const [already, setAlready] = useState(false);
  const [text, setText] = useState("");
  const [output, setOutput] = useState<{ log: DailyLog; alreadyCheckedIn: boolean } | null>(null);

  const canAct = useMemo(() => !!log, [log]);

  const loadSnapshot = async (syncText: boolean) => {
    if (!address) return;
    const data = await api.getDailySnapshot(address, dayIndex);
    setTask(data.task);
    setDateKey(data.dateKey);
    setLog(data.log);
    setAlready(data.alreadyCheckedIn);
    if (syncText) {
      setText(data.log?.normalizedText || "");
    } else if (!data.log) {
      setText("");
    }
    if (!data.log) {
      setOutput(null);
      return;
    }
    setOutput((prev) => {
      if (!prev || prev.log.id !== data.log!.id) {
        return { log: data.log!, alreadyCheckedIn: true };
      }
      return { log: data.log!, alreadyCheckedIn: prev.alreadyCheckedIn };
    });
  };

  useEffect(() => {
    if (!ready || !address) return;
    loadSnapshot(true);
  }, [address, dayIndex, ready]);

  useEffect(() => {
    if (!ready || !address) return;
    loadSnapshot(false);
  }, [storeVersion, ready]);

  if (!ready) return null;
  if (!address) return <NeedAddress />;

  const handleCheckin = async () => {
    try {
      const res = await api.checkin({ address, dayIndex, text });
      setLog(res.log);
      setAlready(true);
      setOutput({ log: res.log, alreadyCheckedIn: res.alreadyCheckedIn });
    } catch (e: any) {
      alert(e?.message || "Checkin failed");
    }
  };

  const handleSubmitProof = async () => {
    try {
      const updated = await api.submitProof({ address });
      setLog(updated);
      setOutput((prev) => (prev ? { log: updated, alreadyCheckedIn: prev.alreadyCheckedIn } : { log: updated, alreadyCheckedIn: true }));
      alert("已模拟提交 Proof（已记录 txHash）");
    } catch (e: any) {
      alert(e?.message || "提交失败");
    }
  };

  const handleMintDay = async () => {
    try {
      const updated = await api.mintDay({ address });
      setLog(updated);
      setOutput((prev) => (prev ? { log: updated, alreadyCheckedIn: prev.alreadyCheckedIn } : { log: updated, alreadyCheckedIn: true }));
      alert("已模拟 Mint DaySBT（已记录 txHash）");
    } catch (e: any) {
      alert(e?.message || "Mint 失败");
    }
  };

  const taskTitle = task?.title || "";
  const taskInstruction = task?.instruction || "";
  const taskHint = task?.hint || "—";

  return (
    <div className="grid lg:grid-cols-3 gap-4">
      <div className="lg:col-span-2 rounded-2xl border border-slate-200 p-6">
        <div className="flex items-start justify-between gap-3">
          <div>
            <div className="text-sm text-slate-500">今日任务</div>
            <div className="mt-1 text-xl font-semibold">{taskTitle}</div>
            <div className="mt-3 text-sm text-slate-700">指令：{taskInstruction}</div>
            <div className="mt-1 text-sm text-slate-500">提示：{taskHint}</div>
          </div>
          <div className="text-right">
            <div className="text-sm text-slate-500">DayIndex</div>
            <div className="mt-1 font-mono text-lg">{dayIndex}</div>
            <div className="mt-2 text-sm text-slate-500">dateKey</div>
            <div className="mt-1 font-mono text-sm">{dateKey}</div>
          </div>
        </div>

        <div className="mt-6">
          <div className="text-sm font-semibold">打卡输入</div>
          <textarea
            className="mt-2 w-full min-h-[110px] px-3 py-2 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-slate-200 text-sm"
            placeholder="写一句话就行（≤280字）"
            value={text}
            onChange={(e) => setText(e.target.value)}
          />

          <div className="mt-3 flex flex-wrap gap-2">
            <button
              className="px-3 py-2 rounded-xl bg-slate-900 text-white text-sm hover:bg-slate-800"
              onClick={handleCheckin}
            >
              生成反馈 + ProofHash（模拟 /checkin）
            </button>
            <button
              className="px-3 py-2 rounded-xl border border-slate-200 text-sm hover:bg-slate-50"
              disabled={!canAct}
              onClick={handleSubmitProof}
            >
              模拟提交 Proof（记录 txHash）
            </button>
            <button
              className="px-3 py-2 rounded-xl border border-slate-200 text-sm hover:bg-slate-50"
              disabled={!canAct}
              onClick={handleMintDay}
            >
              模拟 Mint Day SBT（记录 txHash）
            </button>
          </div>

          <div className="mt-3 text-xs text-slate-500">
            幂等：同一天重复 checkin 只会返回第一次的 log（firstWins）。想重新体验请点上方“清空数据”。
          </div>
        </div>

        {output && (
          <div className="mt-6">
            <div className="rounded-2xl bg-slate-50 p-5 border border-slate-200">
              <div className="flex items-center justify-between gap-3">
                <div className="text-sm font-semibold">/checkin 输出（模拟）</div>
                <div className="text-xs text-slate-500">
                  {output.alreadyCheckedIn ? "alreadyCheckedIn=true（幂等返回）" : "alreadyCheckedIn=false"}
                </div>
              </div>

              <div className="mt-3 grid md:grid-cols-2 gap-4">
                <div>
                  <div className="text-xs text-slate-500">reflection</div>
                  <div className="mt-1 text-sm">
                    <span className="font-semibold">note：</span>
                    {output.log.reflection.note}
                  </div>
                  <div className="mt-1 text-sm">
                    <span className="font-semibold">next：</span>
                    {output.log.reflection.next}
                  </div>
                </div>
                <div>
                  <div className="text-xs text-slate-500">proof inputs</div>
                  <div className="mt-1 text-xs font-mono break-all">saltHex: {output.log.saltHex}</div>
                  <div className="mt-1 text-xs font-mono break-all">proofHash: {output.log.proofHash}</div>
                </div>
              </div>

              <div className="mt-4 text-xs text-slate-500">下一步：点“模拟提交 Proof”→ 记录 txHash → 再点“模拟 Mint Day SBT”。</div>
            </div>
          </div>
        )}
      </div>

      <div className="rounded-2xl border border-slate-200 p-6">
        <div className="text-sm text-slate-500">本日状态</div>
        <div className="mt-2">
          <div className="text-sm">
            今日是否已打卡：<span className="font-semibold">{already ? "是（firstWins）" : "否"}</span>
          </div>
          <div className="mt-2 text-sm">
            Proof 提交状态：<span className="font-semibold">{log?.status || "—"}</span>
          </div>
          <div className="mt-2 text-sm">
            Proof txHash：
            <div className="mt-1 font-mono text-xs break-all">{log?.txHash || "—"}</div>
          </div>
          <div className="mt-3 text-sm">
            DaySBT txHash：
            <div className="mt-1 font-mono text-xs break-all">{log?.daySbtTxHash || "—"}</div>
          </div>
        </div>

        <div className="mt-6 border-t border-slate-200 pt-5">
          <div className="text-sm text-slate-500">快速跳转</div>
          <div className="mt-3 flex flex-wrap gap-2">
            <button
              className="px-3 py-2 rounded-xl border border-slate-200 text-sm hover:bg-slate-50"
              onClick={() => router.push(`/daily/${Math.max(1, dayIndex - 1)}`)}
            >
              上一天
            </button>
            <button
              className="px-3 py-2 rounded-xl border border-slate-200 text-sm hover:bg-slate-50"
              onClick={() => {
                if (dayIndex === 7) router.push("/milestone/1");
                else if (dayIndex === 14) router.push("/milestone/2");
                else if (dayIndex === 28) router.push("/milestone/final");
                else router.push(`/daily/${Math.min(28, dayIndex + 1)}`);
              }}
            >
              下一天
            </button>
            <button
              className="px-3 py-2 rounded-xl border border-slate-200 text-sm hover:bg-slate-50"
              onClick={() => router.push("/progress")}
            >
              进度
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
