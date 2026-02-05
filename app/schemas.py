# app/schemas.py
from __future__ import annotations

from datetime import datetime
from typing import Optional, Literal

from pydantic import BaseModel, ConfigDict, Field


TrafficType = Literal["paid", "organic", "mixed", "live"]


# ---------- Experiments ----------
class ExperimentCreate(BaseModel):
    project_name: str = Field(min_length=1, max_length=200)
    hypothesis: str = Field(min_length=1, max_length=5000)
    traffic_type: TrafficType


class ExperimentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_name: str
    hypothesis: str
    traffic_type: TrafficType
    created_at: datetime


# ---------- Records ----------
class RecordCreate(BaseModel):
    experiment_id: int
    session_id: str = Field(min_length=1, max_length=200)

    # comunes
    clicks: Optional[int] = Field(default=None, ge=0)
    views: Optional[int] = Field(default=None, ge=0)

    # orgánico
    organic_piece_type: Optional[str] = Field(default=None, max_length=200)
    likes: Optional[int] = Field(default=None, ge=0)
    comments: Optional[int] = Field(default=None, ge=0)
    shares: Optional[int] = Field(default=None, ge=0)
    saves: Optional[int] = Field(default=None, ge=0)
    video_url: Optional[str] = Field(default=None, max_length=500)
    views_finish_percent: Optional[float] = Field(default=None, ge=0, le=100)
    retention_percent: Optional[float] = Field(default=None, ge=0, le=100)
    average_watch_time: Optional[float] = Field(default=None, ge=0)
    video_duration: Optional[float] = Field(default=None, ge=0)

    # paid
    ctr: Optional[float] = Field(default=None, ge=0)
    cpc: Optional[float] = Field(default=None, ge=0)
    initiate_checkouts: Optional[int] = Field(default=None, ge=0)
    view_content: Optional[int] = Field(default=None, ge=0)
    lead_form: Optional[int] = Field(default=None, ge=0)
    purchase: Optional[int] = Field(default=None, ge=0)
    paid_video_duration: Optional[float] = Field(default=None, ge=0)
    campaign_id: Optional[str] = Field(default=None, max_length=200)
    ad_set_id: Optional[str] = Field(default=None, max_length=200)
    ad_id: Optional[str] = Field(default=None, max_length=200)


class RecordOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    experiment_id: int
    session_id: str

    clicks: Optional[int] = None
    views: Optional[int] = None

    organic_piece_type: Optional[str] = None
    likes: Optional[int] = None
    comments: Optional[int] = None
    shares: Optional[int] = None
    saves: Optional[int] = None
    video_url: Optional[str] = None
    views_finish_percent: Optional[float] = None
    retention_percent: Optional[float] = None
    average_watch_time: Optional[float] = None
    video_duration: Optional[float] = None

    ctr: Optional[float] = None
    cpc: Optional[float] = None
    initiate_checkouts: Optional[int] = None
    view_content: Optional[int] = None
    lead_form: Optional[int] = None
    purchase: Optional[int] = None
    paid_video_duration: Optional[float] = None
    campaign_id: Optional[str] = None
    ad_set_id: Optional[str] = None
    ad_id: Optional[str] = None

    created_at: datetime
