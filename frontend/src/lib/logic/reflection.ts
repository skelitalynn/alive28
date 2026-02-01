import type { DailyTask, Reflection } from "../store/schema";

export function reflectionTemplate(task: DailyTask, normalizedText: string): Reflection {
  const t = normalizedText || "";
  const mood = (() => {
    const map: Array<[string, string]> = [
      ["累", "有点累也正常。"],
      ["烦", "今天确实挺烦的。"],
      ["焦虑", "焦虑出现很常见。"],
      ["害怕", "害怕的时候更需要抓住可控的点。"],
      ["开心", "能开心一下很珍贵。"],
      ["难过", "难过不丢人。"]
    ];
    for (const [k, v] of map) if (t.includes(k)) return v;
    return "今天你把这件事写出来了。";
  })();

  const note =
    t.length < 8
      ? `${mood}今天能留下哪怕一句话也很重要。别要求自己一次写得很完整，你可以先从一句最真实的话开始。你愿意停下来记录，就是在照顾自己。`
      : `${mood}你在做的是把一天重新收回来，这份诚实本身就很珍贵。请允许自己先被看见，再慢慢整理。你已经在往前走了。`;

  const next = (() => {
    if (task.dayIndex === 6) return "用1分钟补全：我感到__，因为__，然后深呼吸三次。";
    if (t.includes("拖") || t.includes("没做")) return "现在定个2分钟计时，只做最小一步并记录一句话。";
    if (t.includes("想") && t.length > 20) return "划掉一句多余的话，只保留最关键的一句并写清原因。";
    return "写一句：我现在最在意的是__，并说明原因。";
  })();

  return { note: note.slice(0, 300), next: next.slice(0, 40) };
}
