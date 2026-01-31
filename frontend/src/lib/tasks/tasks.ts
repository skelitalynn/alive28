import type { DailyTask } from "../store/schema";

export const tasks: DailyTask[] = Array.from({ length: 28 }, (_, i) => {
  const d = i + 1;
  const titlePool = ["我一定能活下来", "感恩自己", "夸夸自己", "给明天留一点希望", "把今天过小一点", "接纳情绪", "重新选择一个边界"];
  const title = titlePool[(d - 1) % titlePool.length] + ` · Day ${d}`;
  const instruction =
    d === 1
      ? "写一句：我会活下来。"
      : d === 6
        ? "记录今天最强烈的情绪，不评判。"
        : "写下今天最想保住的一件事。";
  const hint = d === 6 ? "写“我感到___，因为___”。" : "越短越好。";
  return { dayIndex: d, title, instruction, hint };
});
