import json
from typing import Dict
from spoon_ai.chat import ChatBot

SYSTEM_PROMPT = """
你是一个简洁的反思助手。只输出 JSON，不要 Markdown，不要解释。
输出必须且仅包含字段 note 和 next。
note: <=50字，口语、具体，避免套话与说教。
next: <=30字，只给1个10分钟内可开始的动作。
禁止医疗/心理诊断与用药建议。
""".strip()

FALLBACK = {
    "note": "收到你的记录，今天你已经迈出一步了。",
    "next": "用1分钟写下：我今天最想继续做的一件小事。"
}


def _truncate(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    return text[:limit]


def _safe_reflection(obj: Dict[str, str]) -> Dict[str, str]:
    note = _truncate(obj.get("note", ""), 50)
    next_step = _truncate(obj.get("next", ""), 30)
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
        f"任务: {task.get('instruction', '')}\n"
        f"用户输入: {normalized_text}\n"
        "只输出 JSON。"
    )
    try:
        raw = await bot.ask([{"role": "user", "content": user_prompt}], system_msg=SYSTEM_PROMPT)
        obj = _extract_json(raw)
        return _safe_reflection(obj)
    except Exception:
        return FALLBACK
