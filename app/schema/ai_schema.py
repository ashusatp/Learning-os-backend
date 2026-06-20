from pydantic import BaseModel


class HierarchyContext(BaseModel):
    goal: str | None = None
    subject: str | None = None
    topic: str | None = None
    subtopic: str | None = None


class AIChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str


class AIHelpRequest(BaseModel):
    messages: list[AIChatMessage]
    hierarchy: HierarchyContext
    current_notes_html: str = ""
    selected_text: str = ""
