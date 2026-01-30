from typing import List, Dict, Any
from datetime import date


def build_report(logs: List[dict], from_date: str, to_date: str) -> Dict[str, Any]:
    completed = [log for log in logs]
    report_text = f"本段时间你完成了{len(completed)}天打卡。保持节奏，你已经在积累稳定性。"

    chart_data = {
        "checkins": [
            {"dateKey": log["date_key"], "done": True} for log in logs
        ],
        "keywords": []  # TODO: 关键词提取规则未在文档中定义
    }
    return {"reportText": report_text, "chartData": chart_data}
