from dataclasses import dataclass


@dataclass
class AIAnalysisResult:
    sentiment: str
    category: str
    reply: str
    ai_used: bool


class AIServiceError(Exception):
    pass
