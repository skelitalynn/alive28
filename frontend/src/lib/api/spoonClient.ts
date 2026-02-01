import type { Reflection } from "../store/schema";
import type { DailyTask } from "../store/schema";

/**
 * SpoonOS AI 客户端
 * 使用 React Agent 或 Graph Agent 生成心理辅导反馈
 * 严格按照 README 要求，Agent 体系作为核心功能模块
 */
export class SpoonOSClient {
  private apiBase: string;
  private apiKey: string;

  constructor() {
    const base = process.env.NEXT_PUBLIC_API_BASE || "http://127.0.0.1:8000";
    this.apiBase = base.replace(/\/$/, "") + "/ai";
    this.apiKey = process.env.NEXT_PUBLIC_SPOONOS_API_KEY || "";
  }

  /**
   * 生成心理辅导反馈
   * 使用 SpoonOS React Agent 或 Graph Agent
   * @param task 每日任务
   * @param userText 用户输入的文字
   * @param dayIndex 天数索引
   */
  async generateReflection(
    task: DailyTask,
    userText: string,
    dayIndex: number
  ): Promise<Reflection> {
    try {
      // 调用 Next.js API 路由（内部使用 React Agent 或 Graph Agent）
      const response = await fetch(`${this.apiBase}/reflection`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          task: {
            dayIndex: task.dayIndex,
            title: task.title,
            instruction: task.instruction,
            hint: task.hint,
          },
          userText,
          dayIndex,
        }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || "Failed to generate reflection");
      }

      const data = await response.json();
      return data.reflection;
    } catch (error: any) {
      console.error("Error calling SpoonOS Agent:", error);
      // 如果 API 调用失败，返回降级反馈
      return this.getFallbackReflection(task, userText);
    }
  }

  /**
   * 降级方案：当 API 不可用时使用
   */
  private getFallbackReflection(task: DailyTask, userText: string): Reflection {
    const t = userText || "";
    const mood = (() => {
      const map: Array<[string, string]> = [
        ["累", "有点累也正常。"],
        ["烦", "今天确实挺烦的。"],
        ["焦虑", "焦虑出现很常见。"],
        ["害怕", "害怕的时候更需要抓住可控的点。"],
        ["开心", "能开心一下很珍贵。"],
        ["难过", "难过不丢人。"],
      ];
      for (const [k, v] of map) if (t.includes(k)) return v;
      return "今天你把这件事写出来了。";
    })();

    const note =
      t.length < 8
        ? `${mood}就先从一句开始也可以。`
        : `${mood}你在做的是把一天重新收回来。`;

    const next = (() => {
      if (task.dayIndex === 6) return "用1分钟补全：我感到__，因为__。";
      if (t.includes("拖") || t.includes("没做"))
        return "现在定个2分钟计时，只做最小一步。";
      if (t.includes("想") && t.length > 20)
        return "划掉一句多余的话，只留最关键的一句。";
      return "写一句：我现在最在意的是__。";
    })();

    return { note: note.slice(0, 50), next: next.slice(0, 30) };
  }
}

export const spoonClient = new SpoonOSClient();
