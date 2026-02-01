import json
from typing import Dict
from spoon_ai.chat import ChatBot

SYSTEM_PROMPT = """
你是一个反思助手。只输出 JSON，不要 Markdown，不要解释。
输出必须且仅包含字段 note 和 next。
必须结合“当天任务”和“用户输入”进行反馈，不要泛泛而谈。
note: 200~300字，情绪共情 + 具体回应用户内容，避免重复原文，语气自然、有温度。
next: 25~40字，只给1个10分钟内可开始的动作，且与当天任务以及用户内容强相关。
禁止医疗/心理诊断与用药建议。
""".strip()

FALLBACK = {
    "note": "谢谢你把今天的感受写出来。即使文字不多，也是在照顾自己、确认自己的存在。你愿意停下来记录，就是在给自己一点空间和温度。今天这一步不需要完美，它本身就很重要。接下来我们只做一件很小、很具体的事，让今天的努力有一个可以落地的形状。",
    "next": "现在用10分钟写下：我最想对自己说的一句话，并读三遍。"
}


def _truncate(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    return text[:limit]


def _safe_reflection(obj: Dict[str, str]) -> Dict[str, str]:
    note = _truncate(obj.get("note", ""), 300)
    next_step = _truncate(obj.get("next", ""), 40)
    if not note or not next_step:
        return FALLBACK
    return {"note": note, "next": next_step}


def _extract_json(text: str) -> Dict[str, str]:
    try:
        return json.loads(text)
    except Exception:
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end >= 0 and end > start:
            try:
                return json.loads(text[start : end + 1])
            except Exception:
                return FALLBACK
        return FALLBACK


async def generate_reflection(task: dict, normalized_text: str) -> Dict[str, str]:
    bot = ChatBot()
    user_prompt = (
        f"任务标题: {task.get('title', '')}\n"
        f"任务内容: {task.get('instruction', '')}\n"
        f"提示: {task.get('hint', '')}\n"
        f"用户输入: {normalized_text}\n"
        "请基于任务与输入生成简短反馈，只输出 JSON。"
    )
    try:
        raw = await bot.ask([{"role": "user", "content": user_prompt}], system_msg=SYSTEM_PROMPT)
        obj = _extract_json(raw)
        return _safe_reflection(obj)
    except Exception:
        return FALLBACK
