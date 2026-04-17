from app.services.agents.base_agent import BaseMarketingAgent
from app.services.agents.copy_agent import CopyAgent
from app.services.agents.email_agent import EmailAgent
from app.services.agents.video_agent import VideoAgent
from app.services.agents.strategy_agent import StrategyAgent
from app.services.agents.ads_agent import AdsAgent

AGENT_MAP: dict[str, BaseMarketingAgent] = {
    "copy": CopyAgent(),
    "email": EmailAgent(),
    "video": VideoAgent(),
    "strategy": StrategyAgent(),
    "ads": AdsAgent(),
}

ROUTING_KEYWORDS: dict[str, list[str]] = {
    "copy": ["vsl", "landing page", "sales page", "headline", "offer", "copy", "grand slam", "upsell", "bump", "copywriting"],
    "email": ["email", "sequence", "nurture", "broadcast", "launch", "drip", "subject line", "autoresponder", "newsletter"],
    "video": ["script", "youtube", "tiktok", "hook", "video", "reel", "shorts", "cta", "thumbnail", "shorts"],
    "strategy": ["strategy", "value ladder", "offer stack", "pricing", "revenue", "100m", "roadmap", "consulting", "funnel", "scale"],
    "ads": ["ad", "facebook", "google", "paid", "campaign", "creative", "targeting", "roas", "meta", "ppc"],
}


def route_to_agent(message: str, explicit_agent: str | None = None) -> BaseMarketingAgent:
    if explicit_agent and explicit_agent in AGENT_MAP:
        return AGENT_MAP[explicit_agent]

    msg_lower = message.lower()
    scores: dict[str, int] = {agent_type: 0 for agent_type in AGENT_MAP}
    for agent_type, keywords in ROUTING_KEYWORDS.items():
        for kw in keywords:
            if kw in msg_lower:
                scores[agent_type] += 1

    best = max(scores, key=lambda k: scores[k])
    if scores[best] == 0:
        return AGENT_MAP["copy"]
    return AGENT_MAP[best]
