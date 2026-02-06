# app/schemas.py
from __future__ import annotations

from datetime import datetime
from typing import Optional, Literal

from pydantic import BaseModel, ConfigDict, Field


TrafficType = Literal["paid", "organic", "mixed", "live"]

HypothesisType = Literal[
    "acquisition",
    "activation",
    "retention",
    "monetization",
    "trust_credibility",
    "message_market_fit",
    "channel_fit",
    "pricing",
    "funnel_friction",
]

ExperimentStatus = Literal[
    "draft",
    "running",
    "validated",
    "invalidated",
    "pivot_candidate",
    "archived",
]

PrimaryMetric = Literal[
    "ctr",
    "cpc",
    "initiate_checkout_rate",
    "view_content_rate",
    "lead_rate",
    "purchase_rate",
    "views",
    "likes",
    "comments",
    "shares",
    "saves",
    "views_finish_pct",
    "retention_pct",
    "avg_watch_time",
    "live_viewers_peak",
    "live_avg_viewers",
    "live_new_followers",
]

VolumeUnit = Literal[
    "clicks",
    "live_new_followers",
    "ctr",
    "cpc",
    "initiate_checkout_rate",
    "view_content_rate",
    "lead_rate",
    "purchase_rate",
    "views",
    "likes",
    "comments",
    "shares",
    "saves",
    "views_finish_pct",
    "retention_pct",
    "avg_watch_time",
    "live_viewers_peak",
    "live_avg_viewers",
]

ThresholdType = Literal["percentage", "absolute", "decimal"]

ThresholdOperator = Literal[">=", "<=", ">", "<"]


ExecutionType = Literal["organic_video", "paid_ad", "live_session"]

HookType = Literal[
    "dolor",
    "amenaza_perdida",
    "autoridad",
    "alivio",
    "curiosidad",
    "validacion_emocional",
]

CtaType = Literal[
    "accion_directa",
    "condicional",
    "urgencia",
    "informativo",
]

RecordStatus = Literal["collecting", "closed"]


# ---------- Experiments ----------
class ExperimentCreate(BaseModel):
    project_name: str = Field(min_length=1, max_length=200)
    hypothesis: str = Field(min_length=1, max_length=5000)
    traffic_type: TrafficType

    # Lean hypothesis fields
    hypothesis_type: Optional[HypothesisType] = None
    independent_variable: Optional[str] = Field(default=None, max_length=500)
    primary_metric: Optional[PrimaryMetric] = None
    validation_threshold: Optional[str] = Field(default=None, max_length=200)
    threshold_value: Optional[float] = Field(default=None, ge=0)
    threshold_type: Optional[ThresholdType] = None
    threshold_operator: Optional[ThresholdOperator] = None
    experiment_status: ExperimentStatus = "draft"
    min_volume: Optional[int] = Field(default=None, ge=1)
    volume_min_value: Optional[int] = Field(default=None, ge=1)
    volume_unit: Optional[VolumeUnit] = None


class ExperimentUpdate(BaseModel):
    hypothesis: Optional[str] = Field(default=None, min_length=1, max_length=5000)
    hypothesis_type: Optional[HypothesisType] = None
    independent_variable: Optional[str] = Field(default=None, max_length=500)
    primary_metric: Optional[PrimaryMetric] = None
    validation_threshold: Optional[str] = Field(default=None, max_length=200)
    threshold_value: Optional[float] = Field(default=None, ge=0)
    threshold_type: Optional[ThresholdType] = None
    threshold_operator: Optional[ThresholdOperator] = None
    experiment_status: Optional[ExperimentStatus] = None
    min_volume: Optional[int] = Field(default=None, ge=1)
    volume_min_value: Optional[int] = Field(default=None, ge=1)
    volume_unit: Optional[VolumeUnit] = None


class ExperimentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_name: str
    hypothesis: str
    traffic_type: TrafficType
    created_at: datetime

    hypothesis_type: Optional[str] = None
    independent_variable: Optional[str] = None
    primary_metric: Optional[str] = None
    validation_threshold: Optional[str] = None
    threshold_value: Optional[float] = None
    threshold_type: Optional[str] = None
    threshold_operator: Optional[str] = None
    experiment_status: str = "draft"
    min_volume: Optional[int] = None
    volume_min_value: Optional[int] = None
    volume_unit: Optional[str] = None


class ExperimentEvaluation(BaseModel):
    experiment_id: int
    primary_metric: Optional[str] = None
    aggregated_value: Optional[float] = None
    threshold_raw: Optional[str] = None
    threshold_value: Optional[float] = None
    threshold_type: Optional[str] = None
    threshold_operator: Optional[str] = None
    total_volume: int = 0
    min_volume: Optional[int] = None
    volume_min_value: Optional[int] = None
    volume_unit: Optional[str] = None
    volume_sufficient: bool = False
    all_records_closed: bool = False
    ready_to_evaluate: bool = False
    suggested_status: Optional[str] = None
    records_collecting: int = 0
    records_closed: int = 0


class ExperimentAnalysis(BaseModel):
    experiment_id: int
    analysis: str


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

    # orgánico - video metrics
    video_url: Optional[str] = Field(default=None, max_length=500)
    views_finish_pct: Optional[float] = Field(default=None, ge=0, le=100)
    retention_pct: Optional[float] = Field(default=None, ge=0, le=100)
    avg_watch_time: Optional[float] = Field(default=None, ge=0)
    video_duration: Optional[float] = Field(default=None, ge=0)

    # paid
    ctr: Optional[float] = Field(default=None, ge=0)
    cpc: Optional[float] = Field(default=None, ge=0)
    initiate_checkouts: Optional[int] = Field(default=None, ge=0)
    view_content: Optional[int] = Field(default=None, ge=0)
    lead_form: Optional[int] = Field(default=None, ge=0)
    purchase: Optional[int] = Field(default=None, ge=0)

    # paid - video and campaign metrics
    paid_video_duration: Optional[float] = Field(default=None, ge=0)
    campaign_id: Optional[str] = Field(default=None, max_length=200)
    ad_set_id: Optional[str] = Field(default=None, max_length=200)
    ad_id: Optional[str] = Field(default=None, max_length=200)

    # live metrics
    live_viewers_peak: Optional[int] = Field(default=None, ge=0)
    live_avg_viewers: Optional[int] = Field(default=None, ge=0)
    live_duration: Optional[float] = Field(default=None, ge=0)
    live_new_followers: Optional[int] = Field(default=None, ge=0)

    # creative / execution fields (new)
    execution_type: Optional[ExecutionType] = None
    record_name: Optional[str] = Field(default=None, max_length=200)
    hook_text: Optional[str] = Field(default=None, max_length=2000)
    hook_type: Optional[HookType] = None
    cta_text: Optional[str] = Field(default=None, max_length=500)
    cta_type: Optional[CtaType] = None
    creative_id: Optional[str] = Field(default=None, max_length=200)


class RecordUpdate(BaseModel):
    """For updating metrics on an existing record (same execution, new data)."""
    clicks: Optional[int] = Field(default=None, ge=0)
    views: Optional[int] = Field(default=None, ge=0)

    likes: Optional[int] = Field(default=None, ge=0)
    comments: Optional[int] = Field(default=None, ge=0)
    shares: Optional[int] = Field(default=None, ge=0)
    saves: Optional[int] = Field(default=None, ge=0)

    views_finish_pct: Optional[float] = Field(default=None, ge=0, le=100)
    retention_pct: Optional[float] = Field(default=None, ge=0, le=100)
    avg_watch_time: Optional[float] = Field(default=None, ge=0)
    video_duration: Optional[float] = Field(default=None, ge=0)

    ctr: Optional[float] = Field(default=None, ge=0)
    cpc: Optional[float] = Field(default=None, ge=0)
    initiate_checkouts: Optional[int] = Field(default=None, ge=0)
    view_content: Optional[int] = Field(default=None, ge=0)
    lead_form: Optional[int] = Field(default=None, ge=0)
    purchase: Optional[int] = Field(default=None, ge=0)

    live_viewers_peak: Optional[int] = Field(default=None, ge=0)
    live_avg_viewers: Optional[int] = Field(default=None, ge=0)
    live_duration: Optional[float] = Field(default=None, ge=0)
    live_new_followers: Optional[int] = Field(default=None, ge=0)

    hook_text: Optional[str] = Field(default=None, max_length=2000)
    record_name: Optional[str] = Field(default=None, max_length=200)
    hook_type: Optional[HookType] = None
    cta_text: Optional[str] = Field(default=None, max_length=500)
    cta_type: Optional[CtaType] = None


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
    views_finish_pct: Optional[float] = None
    retention_pct: Optional[float] = None
    avg_watch_time: Optional[float] = None
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

    live_viewers_peak: Optional[int] = None
    live_avg_viewers: Optional[int] = None
    live_duration: Optional[float] = None
    live_new_followers: Optional[int] = None

    # creative / execution fields (new)
    execution_type: Optional[str] = None
    record_name: Optional[str] = None
    hook_text: Optional[str] = None
    hook_type: Optional[str] = None
    cta_text: Optional[str] = None
    cta_type: Optional[str] = None
    creative_id: Optional[str] = None
    record_status: str = "collecting"

    created_at: datetime
    updated_at: Optional[datetime] = None
