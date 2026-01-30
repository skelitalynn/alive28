from spoon_ai.graph import StateGraph, END
from spoon_ai.graph.agent import GraphAgent as GraphRunner
from .state import GraphState
from .nodes import (
    daily_prompt_node,
    user_input_node,
    reflection_node,
    proof_builder_node,
    onchain_submit_node,
    tx_confirm_node,
    progress_update_node,
    badge_check_node,
    weekly_report_node,
    final_report_node,
)


def build_graph() -> StateGraph:
    graph = StateGraph(GraphState)

    graph.add_node("DailyPrompt", daily_prompt_node)
    graph.add_node("UserInput", user_input_node)
    graph.add_node("Reflection", reflection_node)
    graph.add_node("ProofBuilder", proof_builder_node)
    graph.add_node("OnchainSubmit", onchain_submit_node)
    graph.add_node("TxConfirm", tx_confirm_node)
    graph.add_node("ProgressUpdate", progress_update_node)
    graph.add_node("BadgeCheck", badge_check_node)
    graph.add_node("WeeklyReport", weekly_report_node)
    graph.add_node("FinalReport", final_report_node)

    graph.set_entry_point("DailyPrompt")
    graph.add_edge("DailyPrompt", "UserInput")
    graph.add_edge("UserInput", "Reflection")
    graph.add_edge("Reflection", "ProofBuilder")
    graph.add_edge("ProofBuilder", "OnchainSubmit")

    def after_onchain(state):
        return "tx" if state.get("txHash") else "no_tx"

    graph.add_conditional_edges("OnchainSubmit", after_onchain, {
        "tx": "TxConfirm",
        "no_tx": "ProgressUpdate",
    })

    graph.add_edge("TxConfirm", "ProgressUpdate")
    graph.add_edge("ProgressUpdate", "BadgeCheck")

    def after_progress(state):
        if state.get("reportRange") == "week":
            return "week"
        if state.get("reportRange") == "final":
            return "final"
        return "end"

    graph.add_conditional_edges("BadgeCheck", after_progress, {
        "week": "WeeklyReport",
        "final": "FinalReport",
        "end": END,
    })
    graph.add_edge("WeeklyReport", END)
    graph.add_edge("FinalReport", END)

    return graph


def create_agent() -> GraphRunner:
    graph = build_graph()
    return GraphRunner(name="alive_graph_agent", graph=graph)
