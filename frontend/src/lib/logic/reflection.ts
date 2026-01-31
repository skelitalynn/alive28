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

  const note = t.length < 8 ? `${mood}就先从一句开始也可以。` : `${mood}你在做的是把一天重新收回来。`;

  const next = (() => {
    if (task.dayIndex === 6) return "用1分钟补全：我感到__，因为__。";
    if (t.includes("拖") || t.includes("没做")) return "现在定个2分钟计时，只做最小一步。";
    if (t.includes("想") && t.length > 20) return "划掉一句多余的话，只留最关键的一句。";
    return "写一句：我现在最在意的是__。";
  })();

  return { note: note.slice(0, 50), next: next.slice(0, 30) };
}
