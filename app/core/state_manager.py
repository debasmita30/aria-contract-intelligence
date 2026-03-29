"""
ARIA — State Manager
Typed workflow state with structured logging.
"""
 
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
 
 
class AgentStatus:
    SUCCESS  = "success"
    FAILED   = "failed"
    RECOVERED= "recovered"
    RUNNING  = "running"
    SKIPPED  = "skipped"
 
 
@dataclass
class WorkflowState:
    contract_text:        str
    agent_results:        dict[str, Any]  = field(default_factory=dict)
    reliability:          float | None    = None
    uncertainty:          dict | None     = None
    logs:                 list[dict]      = field(default_factory=list)
    requires_human_review:bool            = False
    started_at:           str             = field(default_factory=lambda: datetime.utcnow().isoformat())
 
    def log(self, level: str, agent: str, message: str) -> None:
        elapsed = self._elapsed()
        self.logs.append({
            "timestamp": elapsed,
            "agent":     agent,
            "level":     level,
            "message":   message,
        })
 
    def _elapsed(self) -> str:
        """Return HH:MM:SS.mmm since workflow start."""
        try:
            start = datetime.fromisoformat(self.started_at)
            delta = (datetime.utcnow() - start).total_seconds()
            mins  = int(delta // 60)
            secs  = delta % 60
            return f"{mins:02d}:{secs:06.3f}"
        except Exception:
            return "00:00.000"
 