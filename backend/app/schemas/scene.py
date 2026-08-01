"""
Pydantic schemas for Scene.
"""

import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict


class SceneBase(BaseModel):
    scene_number: int
    title: Optional[str] = None
    description: Optional[str] = None
    location_query: Optional[str] = None


class SceneCreate(SceneBase):
    """Payload for creating a scene inside a project."""
    pass


class SceneUpdate(BaseModel):
    """Partial update schema for a scene."""
    title: Optional[str] = None
    description: Optional[str] = None
    location_query: Optional[str] = None
    location_data: Optional[Dict[str, Any]] = None
    weather_data: Optional[Dict[str, Any]] = None
    ai_suggestions: Optional[Dict[str, Any]] = None


class SceneRead(SceneBase):
    """Full scene representation including agent-populated fields."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    project_id: uuid.UUID
    location_data: Optional[Dict[str, Any]] = None
    weather_data: Optional[Dict[str, Any]] = None
    ai_suggestions: Optional[Dict[str, Any]] = None
    created_at: datetime
