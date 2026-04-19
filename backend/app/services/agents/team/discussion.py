from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class AdvisorMessage:
    advisor: str  # hormozi | bwnc | walker | manager
    content: str
    round_number: int = 0


@dataclass
class DiscussionState:
    goal: str
    business_name: str
    user_answers: dict = field(default_factory=dict)
    clarifying_questions: list[str] = field(default_factory=list)
    round1: list[AdvisorMessage] = field(default_factory=list)
    round2: list[AdvisorMessage] = field(default_factory=list)
    consensus: str = ""
    past_memory: str = ""
