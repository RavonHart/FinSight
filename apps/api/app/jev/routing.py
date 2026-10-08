from typing import Optional
from app.core.config import settings
from app.jev.schemas import ConfidenceRoutingAction, RoutingDecision


def route_confidence(
    confidence: float,
    context: str = "profile",
    high_threshold: Optional[float] = None,
    medium_threshold: Optional[float] = None,
    clarification_prompt: Optional[str] = None,
) -> RoutingDecision:
    """
    Implements §14 Jev Confidence Routing:
    - High confidence (>= high_threshold) -> CONTINUE
    - Medium confidence (>= medium_threshold) -> GATHER_MORE_EVIDENCE
    - Low confidence (< medium_threshold) ->
        - In 'profile' context: REQUEST_CLARIFICATION
        - In 'research' context: MARK_INSUFFICIENT
    
    Confidence values are strictly preserved and never silently upgraded.
    """
    high = high_threshold if high_threshold is not None else settings.JEV_HIGH_CONFIDENCE_THRESHOLD
    med = medium_threshold if medium_threshold is not None else settings.JEV_MEDIUM_CONFIDENCE_THRESHOLD

    if confidence >= high:
        return RoutingDecision(
            action=ConfidenceRoutingAction.CONTINUE,
            confidence=confidence,
            high_threshold=high,
            medium_threshold=med,
            reason=f"Confidence {confidence:.2f} meets or exceeds high threshold {high:.2f}",
        )
    elif confidence >= med:
        return RoutingDecision(
            action=ConfidenceRoutingAction.GATHER_MORE_EVIDENCE,
            confidence=confidence,
            high_threshold=high,
            medium_threshold=med,
            reason=f"Confidence {confidence:.2f} is moderate (between {med:.2f} and {high:.2f}); gathering additional inputs recommended",
            follow_up_prompt=clarification_prompt,
        )
    else:
        if context == "profile":
            return RoutingDecision(
                action=ConfidenceRoutingAction.REQUEST_CLARIFICATION,
                confidence=confidence,
                high_threshold=high,
                medium_threshold=med,
                reason=f"Confidence {confidence:.2f} is below minimum threshold {med:.2f}; user clarification required",
                follow_up_prompt=clarification_prompt or "Your responses indicate conflicting financial preferences. Please clarify your primary priority.",
            )
        elif context == "advisory":
            return RoutingDecision(
                action=ConfidenceRoutingAction.REQUEST_CLARIFICATION,
                confidence=confidence,
                high_threshold=high,
                medium_threshold=med,
                reason=f"Confidence {confidence:.2f} is below minimum threshold {med:.2f}; pedagogical clarification requested",
                follow_up_prompt=clarification_prompt or "Please rephrase your question around theoretical or educational concepts.",
            )
        else:
            return RoutingDecision(
                action=ConfidenceRoutingAction.MARK_INSUFFICIENT,
                confidence=confidence,
                high_threshold=high,
                medium_threshold=med,
                reason=f"Confidence {confidence:.2f} is below minimum threshold {med:.2f}; marked as insufficient in research evaluation",
            )
