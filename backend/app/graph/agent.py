from spoon_ai.graph import StateGraph, END
from spoon_ai.graph.agent import GraphAgent as GraphRunner
from .state import GraphState
from .nodes import (
    daily_prompt_node,
    user_input_node,
    risk_classify_node,
    crisis_response_node,
    input_quality_node,
    clarification_response_node,
    rejected_input_node,
    reflection_node,
    validate_reflection_node,
    repair_reflection_node,
    fallback_reflection_node,
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
    graph.add_node("RiskClassify", risk_classify_node)
    graph.add_node("CrisisResponse", crisis_response_node)
    graph.add_node("InputQuality", input_quality_node)
    graph.add_node("ClarificationResponse", clarification_response_node)
    graph.add_node("RejectedInput", rejected_input_node)
    graph.add_node("Reflection", reflection_node)
    graph.add_node("ValidateReflection", validate_reflection_node)
    graph.add_node("RepairReflection", repair_reflection_node)
    graph.add_node("ValidateRepairedReflection", validate_reflection_node)
    graph.add_node("FallbackReflection", fallback_reflection_node)
    graph.add_node("ProofBuilder", proof_builder_node)
    graph.add_node("OnchainSubmit", onchain_submit_node)
    graph.add_node("TxConfirm", tx_confirm_node)
    graph.add_node("ProgressUpdate", progress_update_node)
    graph.add_node("BadgeCheck", badge_check_node)
    graph.add_node("WeeklyReport", weekly_report_node)
    graph.add_node("FinalReport", final_report_node)

    graph.set_entry_point("DailyPrompt")

    def after_daily_prompt(state):
        flow = state.get("flow")
        if flow == "tx_confirm":
            return "tx"
        if flow == "report_week":
            return "week"
        if flow == "report_final":
            return "final"
        if flow == "progress":
            return "progress"
        if state.get("alreadyCheckedIn"):
            return "progress"
        return "input"

    graph.add_conditional_edges("DailyPrompt", after_daily_prompt, {
        "tx": "TxConfirm",
        "week": "WeeklyReport",
        "final": "FinalReport",
        "progress": "ProgressUpdate",
        "input": "UserInput",
    })

    graph.add_edge("UserInput", "RiskClassify")

    def after_risk_classification(state):
        return "crisis" if state.get("riskLevel") == "crisis" else "ordinary"

    graph.add_conditional_edges("RiskClassify", after_risk_classification, {
        "crisis": "CrisisResponse",
        "ordinary": "InputQuality",
    })
    graph.add_edge("CrisisResponse", END)

    def after_input_quality(state):
        return state.get("inputDecision", "clarify")

    graph.add_conditional_edges("InputQuality", after_input_quality, {
        "accept": "Reflection",
        "clarify": "ClarificationResponse",
        "rejected": "RejectedInput",
    })
    graph.add_edge("ClarificationResponse", END)
    graph.add_edge("RejectedInput", END)
    graph.add_edge("Reflection", "ValidateReflection")

    def after_reflection_validation(state):
        if state.get("reflectionValid"):
            return "valid"
        if state.get("generationError"):
            return "fallback"
        return "repair"

    graph.add_conditional_edges("ValidateReflection", after_reflection_validation, {
        "valid": "ProofBuilder",
        "repair": "RepairReflection",
        "fallback": "FallbackReflection",
    })
    graph.add_edge("RepairReflection", "ValidateRepairedReflection")

    def after_repair_validation(state):
        return "valid" if state.get("reflectionValid") else "fallback"

    graph.add_conditional_edges("ValidateRepairedReflection", after_repair_validation, {
        "valid": "ProofBuilder",
        "fallback": "FallbackReflection",
    })
    graph.add_edge("FallbackReflection", "ProofBuilder")
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
