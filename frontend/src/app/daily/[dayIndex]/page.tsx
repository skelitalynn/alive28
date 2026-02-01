"use client";

import { useEffect, useMemo, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import NeedAddress from "../../../components/NeedAddress";
import { api } from "../../../lib/api";
import { useAddress } from "../../../components/addressContext";
import type { DailyLog, DailyTask } from "../../../lib/store/schema";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://127.0.0.1:8000";

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

  // NFT 生成相关状态
  const [nftImage, setNftImage] = useState<string | null>(null);
  const [isGeneratingNFT, setIsGeneratingNFT] = useState(false);
  const [nftError, setNftError] = useState<string | null>(null);

  const canAct = useMemo(() => !!log, [log]);
  const dayProgress = (dayIndex / 28) * 100;

  const loadSnapshot = async (syncText: boolean) => {
    if (!address) return;
    const data = await api.getDailySnapshot(address, dayIndex);
    setTask(data.task);
    setDateKey(data.dateKey);
    setLog(data.log);

    // 只有当找到的日志的 dayIndex 匹配时才认为已完成
    const isAlreadyCheckedIn = !!(data.log && data.log.dayIndex === dayIndex);
    setAlready(isAlreadyCheckedIn);

    if (syncText) {
      setText(data.log?.normalizedText || "");
    } else if (!data.log || data.log.dayIndex !== dayIndex) {
      setText("");
    }

    if (!data.log || data.log.dayIndex !== dayIndex) {
      setOutput(null);
      return;
    }

    setOutput((prev) => {
      if (!prev || prev.log.id !== data.log!.id) {
        return { log: data.log!, alreadyCheckedIn: isAlreadyCheckedIn };
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
      alert(e?.message || "提交失败，请重试");
    }
  };

  const handleSubmitProof = async () => {
    try {
      const updated = await api.submitProof({ address });
      setLog(updated);
      setOutput((prev) => (prev ? { log: updated, alreadyCheckedIn: prev.alreadyCheckedIn } : { log: updated, alreadyCheckedIn: true }));
      alert("✨ 已保存你的记录");
    } catch (e: any) {
      alert(e?.message || "保存失败，请重试");
    }
  };

  const handleMintDay = async () => {
    try {
      const updated = await api.mintDay({ address });
      setLog(updated);
      setOutput((prev) => (prev ? { log: updated, alreadyCheckedIn: prev.alreadyCheckedIn } : { log: updated, alreadyCheckedIn: true }));
      alert("🎉 恭喜完成今日任务！");
    } catch (e: any) {
      alert(e?.message || "操作失败，请重试");
    }
  };

  // 生成NFT图片
  const handleGenerateNFT = async () => {
    if (!output?.log) return;

    setIsGeneratingNFT(true);
    setNftError(null);

    try {
      const response = await fetch(`${API_BASE}/ai/generate-nft`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          dayIndex,
          taskTitle: task?.title || `Day ${dayIndex}`,
          userText: output.log.normalizedText,
          reflectionNote: output.log.reflection.note,
          reflectionNext: output.log.reflection.next,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || "生成失败");
      }

      setNftImage(data.image);
    } catch (e: any) {
      console.error("NFT generation error:", e);
      setNftError(e?.message || "NFT 生成失败，请重试");
    } finally {
      setIsGeneratingNFT(false);
    }
  };

  // 下载NFT图片
  const handleDownloadNFT = () => {
    if (!nftImage) return;

    const link = document.createElement("a");
    link.href = nftImage;
    link.download = `alive28-day${dayIndex}-nft.png`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const taskTitle = task?.title || "";
  const taskInstruction = task?.instruction || "";
  const taskHint = task?.hint || "";

  return (
    <div className="grid lg:grid-cols-3 gap-6 animate-fade-in">
      <div className="lg:col-span-2 rounded-2xl border border-pink-100 bg-white/80 backdrop-blur-sm p-8 shadow-sm card-hover">
        {/* 天数进度条 */}
        <div className="mb-6 animate-slide-in">
          <div className="flex justify-between text-sm text-pink-600/70 mb-2">
            <span>第 {dayIndex} 天 / 28 天</span>
            <span>{Math.round(dayProgress)}%</span>
          </div>
          <div className="progress-bar">
            <div className="progress-fill" style={{ width: `${dayProgress}%` }}></div>
          </div>
        </div>

        <div className="mb-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="text-3xl animate-pulse-slow">📝</div>
            <div>
              <div className="text-sm text-pink-700/70">今日任务</div>
              <div className="mt-1 text-2xl font-semibold text-pink-900">{taskTitle}</div>
            </div>
          </div>

          {taskInstruction && (
            <div className="mt-4 p-4 rounded-xl bg-pink-50/30 border border-pink-100 animate-slide-in">
              <div className="text-sm font-medium text-pink-700 mb-2">💭 今日任务</div>
              <div className="text-sm text-pink-700 leading-relaxed">{taskInstruction}</div>
            </div>
          )}

          {taskHint && (
            <div className="mt-3 text-sm text-pink-600/70 italic animate-slide-in">💡 {taskHint}</div>
          )}
        </div>

        <div className="mt-6">
          <div className="text-sm font-medium text-pink-700 mb-3">写下你的感受</div>
          <textarea
            className="w-full min-h-[140px] px-4 py-3 rounded-xl border border-pink-100 bg-white focus:outline-none focus:ring-2 focus:ring-pink-200 text-sm text-pink-800 placeholder:text-pink-400/60 resize-none transition-all"
            placeholder={log?.daySbtTxHash ? "今日已完成，可以查看反馈" : "记录下此刻的想法和感受吧..."}
            value={text}
            onChange={(e) => setText(e.target.value)}
            disabled={!!log?.daySbtTxHash}
          />
          <div className="mt-2 text-xs text-pink-500/70 text-right">{text.length}/280</div>

          <div className="mt-4 flex flex-wrap gap-3">
            <button
              className="px-6 py-3 rounded-xl bg-gradient-to-r from-pink-200 to-rose-200 text-pink-700 text-sm font-medium hover:from-pink-300 hover:to-rose-300 transition-all shadow-sm disabled:opacity-50 disabled:cursor-not-allowed btn-press"
              onClick={handleCheckin}
              disabled={!text.trim() || !!log?.daySbtTxHash}
            >
              {already ? "更新反馈" : "生成反馈"}
            </button>
            {canAct && (
              <>
                <button
                  className="px-5 py-3 rounded-xl border border-pink-100 bg-white text-pink-700 text-sm hover:bg-pink-50/50 transition-all disabled:opacity-50 btn-press"
                  disabled={!!log?.daySbtTxHash}
                  onClick={handleSubmitProof}
                >
                  {log?.status === "SUBMITTED" ? "✓ 已保存" : "保存记录"}
                </button>
                <button
                  className="px-5 py-3 rounded-xl border border-pink-100 bg-white text-pink-700 text-sm hover:bg-pink-50/50 transition-all disabled:opacity-50 btn-press"
                  disabled={!!log?.daySbtTxHash}
                  onClick={() => {
                    if (window.confirm("确认完成今日任务并铸造 NFT 吗？\n\n铸造后今日感受将无法再修改！")) {
                      handleMintDay();
                    }
                  }}
                >
                  {log?.daySbtTxHash ? "✓ 已完成" : "完成今日"}
                </button>
              </>
            )}
          </div>
        </div>

        {output && (
          <div className="mt-6 rounded-2xl bg-gradient-to-br from-pink-50/50 to-rose-50/50 p-6 border border-pink-100 shadow-sm animate-fade-in">
            <div className="text-lg font-semibold text-pink-800 mb-4 flex items-center gap-2">
              <span className="animate-pulse-slow">✨</span>
              <span>你的反馈</span>
            </div>

            <div className="space-y-4">
              <div className="p-4 rounded-xl bg-white/90 border border-pink-100 animate-slide-in">
                <div className="text-xs text-pink-600/70 mb-1">💭 今日感悟</div>
                <div className="text-sm text-pink-800 leading-relaxed">{output.log.reflection.note}</div>
              </div>

              <div className="p-4 rounded-xl bg-white/90 border border-pink-100 animate-slide-in">
                <div className="text-xs text-pink-600/70 mb-1">🌱 下一步</div>
                <div className="text-sm text-pink-800 leading-relaxed">{output.log.reflection.next}</div>
              </div>

              {/* NFT 铸造区域 */}
              <div className="p-4 rounded-xl bg-gradient-to-r from-purple-50/80 to-pink-50/80 border border-purple-100 animate-slide-in">
                <div className="text-xs text-purple-600/70 mb-3 flex items-center gap-1">
                  <span>🎨</span>
                  <span>铸造你的专属 NFT</span>
                </div>

                {!nftImage ? (
                  <div className="space-y-3">
                    <p className="text-sm text-purple-700/80">
                      根据你今天的感受，生成一幅独一无二的艺术作品
                    </p>
                    <button
                      className="w-full px-5 py-3 rounded-xl bg-gradient-to-r from-purple-400 to-pink-400 text-white text-sm font-medium hover:from-purple-500 hover:to-pink-500 transition-all shadow-md disabled:opacity-50 disabled:cursor-not-allowed btn-press flex items-center justify-center gap-2"
                      onClick={handleGenerateNFT}
                      disabled={isGeneratingNFT}
                    >
                      {isGeneratingNFT ? (
                        <>
                          <span className="animate-spin">🌀</span>
                          <span>正在生成艺术作品...</span>
                        </>
                      ) : (
                        <>
                          <span>🎨</span>
                          <span>生成 NFT 图片</span>
                        </>
                      )}
                    </button>
                    {nftError && (
                      <div className="text-sm text-red-500 bg-red-50 p-3 rounded-lg">
                        ⚠️ {nftError}
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="space-y-4">
                    <div className="relative rounded-xl overflow-hidden border-2 border-purple-200 shadow-lg">
                      <img
                        src={nftImage}
                        alt={`Day ${dayIndex} NFT`}
                        className="w-full aspect-square object-cover"
                      />
                      <div className="absolute top-2 right-2 px-2 py-1 bg-black/50 rounded-full text-white text-xs backdrop-blur-sm">
                        Day {dayIndex} / 28
                      </div>
                    </div>
                    <div className="flex gap-2">
                      <button
                        className="flex-1 px-4 py-2 rounded-xl bg-gradient-to-r from-purple-400 to-pink-400 text-white text-sm font-medium hover:from-purple-500 hover:to-pink-500 transition-all shadow-sm btn-press flex items-center justify-center gap-1"
                        onClick={handleDownloadNFT}
                      >
                        <span>📥</span>
                        <span>下载图片</span>
                      </button>
                      <button
                        className="px-4 py-2 rounded-xl border border-purple-200 bg-white text-purple-600 text-sm hover:bg-purple-50 transition-all btn-press flex items-center justify-center gap-1"
                        onClick={() => setNftImage(null)}
                      >
                        <span>🔄</span>
                        <span>重新生成</span>
                      </button>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </div>

      <div className="rounded-2xl border border-pink-100 bg-white/80 backdrop-blur-sm p-6 shadow-sm card-hover animate-slide-in">
        <div className="text-sm font-medium text-pink-700 mb-4">📊 今日状态</div>
        <div className="space-y-3">
          <div className="p-3 rounded-xl bg-pink-50/30 border border-pink-100">
            <div className="text-xs text-pink-600/70">完成状态</div>
            <div className="mt-1 text-sm font-medium text-pink-700">
              {already ? "✓ 已完成" : "未完成"}
            </div>
          </div>

          {log?.status === "SUBMITTED" && (
            <div className="p-3 rounded-xl bg-pink-50/30 border border-pink-100 animate-fade-in">
              <div className="text-xs text-pink-600/70">记录状态</div>
              <div className="mt-1 text-sm font-medium text-pink-700">✓ 已保存</div>
            </div>
          )}

          {log?.daySbtTxHash && (
            <div className="p-3 rounded-xl bg-pink-50/30 border border-pink-100 animate-fade-in">
              <div className="text-xs text-pink-600/70">任务状态</div>
              <div className="mt-1 text-sm font-medium text-pink-700">🎉 已完成</div>
            </div>
          )}
        </div>

        <div className="mt-6 pt-6 border-t border-pink-100">
          <div className="text-sm font-medium text-pink-700 mb-3">导航</div>
          <div className="flex flex-wrap gap-2">
            <button
              className="px-4 py-2 rounded-xl border border-pink-100 bg-white text-pink-700 text-sm hover:bg-pink-50/50 transition-all btn-press"
              onClick={() => router.push(`/daily/${Math.max(1, dayIndex - 1)}`)}
            >
              ← 上一天
            </button>
            <button
              className="px-4 py-2 rounded-xl border border-pink-100 bg-white text-pink-700 text-sm hover:bg-pink-50/50 transition-all btn-press"
              onClick={() => {
                if (dayIndex === 7) router.push("/milestone/1");
                else if (dayIndex === 14) router.push("/milestone/2");
                else if (dayIndex === 28) router.push("/milestone/final");
                else router.push(`/daily/${Math.min(28, dayIndex + 1)}`);
              }}
            >
              下一天 →
            </button>
            <button
              className="px-4 py-2 rounded-xl border border-pink-100 bg-white text-pink-700 text-sm hover:bg-pink-50/50 transition-all btn-press"
              onClick={() => router.push("/progress")}
            >
              查看进度
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
