from typing import List, Dict, Any
from spoon_ai.chat import ChatBot

from .tasks import get_task_by_day_index

SYSTEM_PROMPT = """
你是一个简洁的周报/结营总结助手。
只输出纯文本，不要 Markdown，不要标题，不要列表，不要引号。
禁止引用/复述用户原文（不要出现任何原话）。
字数 <= 120。
""".strip()

FALLBACK_WEEK = "这一周你有持续记录，节奏在慢慢稳定。继续保持每天一小步，优先把最重要的一件事写下来。"
FALLBACK_FINAL = "你已经完成了阶段性的坚持，说明你有稳定的行动力。下一步建议把其中一条最重要的边界固定下来，形成长期习惯。"


def _truncate(text: str, limit: int = 120) -> str:
    text = (text or "").strip()
    if len(text) <= limit:
        return text
    return text[:limit]


def _parse_reflection(value: Any) -> Dict[str, str]:
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        # best-effort, but reflection should already be dict
        return {"note": value, "next": ""}
    return {"note": "", "next": ""}


def _format_logs(logs: List[Any]) -> str:
    lines = []
    for log in logs:
        try:
            task = get_task_by_day_index(int(log.day_index))
        except Exception:
            task = {"instruction": ""}
        reflection = _parse_reflection(log.reflection)
        normalized = (log.normalized_text or "").replace("\n", " ")
        if len(normalized) > 60:
            normalized = normalized[:60]
        lines.append(
            f"Day {log.day_index} | {log.date_key}\n"
            f"任务: {task.get('instruction','')}\n"
            f"内容摘要: {normalized}\n"
            f"反思: {reflection.get('note','')} / 下一步: {reflection.get('next','')}"
        )
    return "\n---\n".join(lines)


async def generate_report_text(logs: List[Any], range_value: str) -> str:
    if not logs:
        return ""
    bot = ChatBot()
    summary_scope = "周报" if range_value == "week" else "结营报告"
    user_prompt = (
        f"请生成{summary_scope}总结。\n"
        "注意：不得引用/复述用户原话，只输出抽象总结。\n"
        "以下是记录：\n"
        f"{_format_logs(logs)}"
    )
    try:
        raw = await bot.ask([
            {"role": "user", "content": user_prompt}
        ], system_msg=SYSTEM_PROMPT)
        text = _truncate(raw, 120)
        if not text:
            return FALLBACK_WEEK if range_value == "week" else FALLBACK_FINAL
        return text
    except Exception:
        return FALLBACK_WEEK if range_value == "week" else FALLBACK_FINAL
