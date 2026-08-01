"""
Pydantic schemas for AgentSession and agent invocation requests.
"""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict


class AgentRunRequest(BaseModel):
    """Payload sent by the client to trigger an agentic workflow."""
    project_id: uuid.UUID
    agent_type: str  # e.g. "script_writer", "location_scout", "scheduler"
    input_data: Dict[str, Any] = {}


class AgentSessionRead(BaseModel):
    """Persisted agent session returned to the client."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    project_id: uuid.UUID
    agent_type: str
    status: str
    state_snapshot: Optional[Dict[str, Any]] = None
    messages: Optional[List[Any]] = None
    created_at: datetime
    updated_at: datetime
