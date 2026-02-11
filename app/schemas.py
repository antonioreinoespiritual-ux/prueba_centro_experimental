# app/schemas.py
from __future__ import annotations

from datetime import datetime
from typing import Optional, Literal, Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


TrafficType = Literal["paid", "organic", "mixed", "live"]

HypothesisType = Literal[
    # legacy values (backward compatibility)
    "acquisition",
    "activation",
    "retention",
    "monetization",
    "trust_credibility",
    "message_market_fit",
    "channel_fit",
    "pricing",
    "funnel_friction",
    # canonical values
    "ACQUISITION",
    "ACTIVATION",
    "RETENTION",
    "MONETIZATION",
    "TRUST",
    "MESSAGE_MARKET_FIT",
    "CHANNEL_FIT",
    "PRICING",
    "FUNNEL_FRICTION",
    # new canonical values
    "PROBLEM",
    "CUSTOMER_SEGMENT",
    "SOLUTION",
    "VALUE",
]


_HYPOTHESIS_TYPE_NORMALIZATION = {
    "problema": "PROBLEM",
    "problem": "PROBLEM",
    "cliente_segmento": "CUSTOMER_SEGMENT",
    "cliente-segmento": "CUSTOMER_SEGMENT",
    "customer_segment": "CUSTOMER_SEGMENT",
    "customer-segment": "CUSTOMER_SEGMENT",
    "solucion": "SOLUTION",
    "solución": "SOLUTION",
    "solution": "SOLUTION",
    "valor": "VALUE",
    "value": "VALUE",
}


def _normalize_hypothesis_type(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    if not stripped:
        return None
    lowered = stripped.lower()
    return _HYPOTHESIS_TYPE_NORMALIZATION.get(lowered, stripped)

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

RecordStatus = Literal["draft", "collecting", "closed"]


EntityType = Literal["experiment", "record"]
AIAnalysisType = Literal["metrics", "notes", "combined"]


# ---------- Documentation ----------
class DocumentationNoteCreate(BaseModel):
    body: str = Field(min_length=1, max_length=50000)


class DocumentationNoteUpdate(BaseModel):
    body: str = Field(min_length=1, max_length=50000)


class DocumentationNoteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    documentation_id: int
    body: str
    created_at: datetime
    updated_at: Optional[datetime] = None


class DocumentationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    entity_type: str
    entity_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    notes: list[DocumentationNoteOut] = []


# ---------- Files ----------
class EntityFileRename(BaseModel):
    display_name: Optional[str] = Field(default=None, max_length=255)
    folder: Optional[str] = Field(default=None, max_length=255)


class EntityFileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    entity_type: str
    entity_id: int
    display_name: str
    stored_name: str
    folder: Optional[str] = None
    content_type: Optional[str] = None
    size_bytes: int
    created_at: datetime
    updated_at: Optional[datetime] = None


# ---------- AI Analysis ----------
class AIAnalysisOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    entity_type: str
    entity_id: int
    analysis_type: str
    model: str
    prompt_version: str
    input_snapshot: str
    output: str
    created_at: datetime


class AIAnalysisResponse(BaseModel):
    ai_analysis_id: int
    output: str


# ---------- Experiments ----------
class ExperimentCreate(BaseModel):
    @field_validator("hypothesis_type", mode="before")
    @classmethod
    def normalize_hypothesis_type(cls, value: str | None):
        return _normalize_hypothesis_type(value)

    project_name: str = Field(min_length=1, max_length=200)
    hypothesis: str = Field(min_length=1, max_length=5000)
    traffic_type: TrafficType

    # Contexto cualitativo (documentacion, NO metrica)
    contexto: Optional[str] = Field(default=None, max_length=50000)

    # Lean hypothesis fields
    hypothesis_type: Optional[HypothesisType] = None
    independent_variable: Optional[str] = Field(default=None, max_length=500)
    metric_x: Optional[str] = Field(default=None, max_length=100)
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
    @field_validator("hypothesis_type", mode="before")
    @classmethod
    def normalize_hypothesis_type(cls, value: str | None):
        return _normalize_hypothesis_type(value)

    hypothesis: Optional[str] = Field(default=None, min_length=1, max_length=5000)
    hypothesis_type: Optional[HypothesisType] = None
    independent_variable: Optional[str] = Field(default=None, max_length=500)
    metric_x: Optional[str] = Field(default=None, max_length=100)
    primary_metric: Optional[PrimaryMetric] = None
    validation_threshold: Optional[str] = Field(default=None, max_length=200)
    threshold_value: Optional[float] = Field(default=None, ge=0)
    threshold_type: Optional[ThresholdType] = None
    threshold_operator: Optional[ThresholdOperator] = None
    experiment_status: Optional[ExperimentStatus] = None
    min_volume: Optional[int] = Field(default=None, ge=1)
    volume_min_value: Optional[int] = Field(default=None, ge=1)
    volume_unit: Optional[VolumeUnit] = None


class ProjectRename(BaseModel):
    new_project_name: str = Field(min_length=1, max_length=200)


class ExperimentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_name: str
    hypothesis: str
    traffic_type: TrafficType
    created_at: datetime
    updated_at: Optional[datetime] = None
    drive_folder_path: Optional[str] = None

    hypothesis_type: Optional[str] = None
    independent_variable: Optional[str] = None
    metric_x: Optional[str] = None
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
    segmented_by_public: bool = False
    segments: list["ExperimentEvaluationSegment"] = []


class ExperimentEvaluationSegment(BaseModel):
    publico: str
    records_total: int = 0
    aggregated_value: Optional[float] = None
    comparison_value: Optional[float] = None
    total_volume: int = 0
    volume_sufficient: bool = False
    all_records_closed: bool = False
    ready_to_evaluate: bool = False
    suggested_status: str = "inconclusive"
    explanation: str = "evidencia insuficiente"


class ExperimentAnalysis(BaseModel):
    experiment_id: int
    analysis: str


# ---------- Publics ----------
class PublicCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, max_length=2000)


class PublicUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, max_length=2000)


class PublicOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    records_count: int = 0


class PublicMetrics(BaseModel):
    records_total: int = 0
    clicks_total: int = 0
    views_total: int = 0
    purchases_total: int = 0
    leads_total: int = 0
    initiate_checkouts_total: int = 0


class PublicDetail(BaseModel):
    public: PublicOut
    metrics: PublicMetrics
    records: list["RecordOut"] = []


# ---------- Records ----------
class RecordCreate(BaseModel):
    experiment_id: int
    session_id: str = Field(min_length=1, max_length=200)
    iteration_number: Optional[int] = Field(default=None, ge=1)

    # Contexto cualitativo (documentacion, NO metrica)
    contexto_record: Optional[str] = Field(default=None, max_length=50000)

    # comunes
    clicks: Optional[int] = Field(default=None, ge=0)
    views: Optional[int] = Field(default=None, ge=0)
    views_profile: Optional[int] = Field(default=None, ge=0)
    inicia_test: Optional[int] = Field(default=None, ge=0)

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
    public_id: Optional[int] = None
    publico: Optional[str] = Field(default=None, max_length=200)
    hook_text: Optional[str] = Field(default=None, max_length=2000)
    hook_type: Optional[HookType] = None
    cta_text: Optional[str] = Field(default=None, max_length=500)
    cta_type: Optional[CtaType] = None
    creative_id: Optional[str] = Field(default=None, max_length=200)
    record_status: Optional[RecordStatus] = None


class RecordUpdate(BaseModel):
    """For updating metrics on an existing record (same execution, new data)."""
    clicks: Optional[int] = Field(default=None, ge=0)
    views: Optional[int] = Field(default=None, ge=0)
    views_profile: Optional[int] = Field(default=None, ge=0)
    inicia_test: Optional[int] = Field(default=None, ge=0)

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
    public_id: Optional[int] = None
    publico: Optional[str] = Field(default=None, max_length=200)
    hook_type: Optional[HookType] = None
    cta_text: Optional[str] = Field(default=None, max_length=500)
    cta_type: Optional[CtaType] = None


class RecordOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    experiment_id: int
    session_id: str
    iteration_number: Optional[int] = None

    clicks: Optional[int] = None
    views: Optional[int] = None
    views_profile: Optional[int] = None
    inicia_test: Optional[int] = None

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
    public_id: Optional[int] = None
    publico: Optional[str] = None
    hook_text: Optional[str] = None
    hook_type: Optional[str] = None
    cta_text: Optional[str] = None
    cta_type: Optional[str] = None
    creative_id: Optional[str] = None
    record_status: str = "collecting"
    drive_folder_path: Optional[str] = None

    created_at: datetime
    updated_at: Optional[datetime] = None


class BulkRecordUpdateItem(BaseModel):
    record_id: Optional[int] = None
    session_id: Optional[str] = None
    record_name: Optional[str] = None
    fields: dict[str, Any] = Field(default_factory=dict)


class BulkRecordUpdateRequest(BaseModel):
    updates: list[BulkRecordUpdateItem] = Field(default_factory=list)


class BulkRecordUpdatePreview(BaseModel):
    record_identifier: str
    record_id: Optional[int] = None
    status: Literal["ready", "not_found", "error"]
    fields_to_update: list[str] = []
    unknown_fields: list[str] = []
    errors: list[str] = []


class BulkRecordUpdateResponse(BaseModel):
    updated_count: int = 0
    not_found: list[str] = []
    unknown_fields: dict[str, list[str]] = {}
    errors: dict[str, list[str]] = {}
    preview: list[BulkRecordUpdatePreview] = []


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    conversation_id: Optional[str] = Field(default=None, max_length=100)
    model: Optional[str] = Field(default=None, max_length=200)


class ConsultChatResponse(BaseModel):
    answer: str
    refs: dict[str, Any] | None = None


class OpenClawChatResponse(BaseModel):
    mode: Literal["idle", "drafting", "draft", "preview", "needs_input", "ready_to_confirm", "created"]
    draft: dict[str, Any] | None = None
    questions: list[str] = []


# ---------- Cloud Drive ----------
class CloudLibraryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    owner_id: Optional[str] = None


class CloudLibraryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    root_path: str
    is_system: bool = False
    owner_id: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None


class CloudItemCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    library_id: int
    parent_id: Optional[int] = None
    owner_id: Optional[str] = None


class CloudItemUpdate(BaseModel):
    name: Optional[str] = Field(default=None, max_length=255)
    parent_id: Optional[int] = None


class CloudItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    parent_id: Optional[int] = None
    library_id: int
    item_type: str
    size: Optional[int] = None
    path: Optional[str] = None
    rel_path: Optional[str] = None
    owner_id: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None


class CloudUploadInit(BaseModel):
    filename: str
    library_id: int
    parent_id: Optional[int] = None
    size: Optional[int] = None


class CloudUploadComplete(BaseModel):
    filename: str
    library_id: int
    parent_id: Optional[int] = None
    size: Optional[int] = None
    owner_id: Optional[str] = None


class CloudShareCreate(BaseModel):
    shared_with: str = Field(min_length=1, max_length=200)
    permission: Literal["view", "edit", "upload", "delete"]


class CloudShareOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    item_id: int
    shared_with: str
    permission: str
    created_at: datetime


class CloudSearchResponse(BaseModel):
    results: list[CloudItemOut] = []


class CloudDisplayEntry(BaseModel):
    item_id: int
    display_name: str
    badge: Optional[str] = None


class CloudDisplayMap(BaseModel):
    items: list[CloudDisplayEntry] = []


class CloudRecordNode(BaseModel):
    name: str
    rel_path: str


class CloudHypothesisNode(BaseModel):
    name: str
    rel_path: str
    records: list[CloudRecordNode] = []


class CloudProjectNode(BaseModel):
    name: str
    rel_path: str
    hypotheses: list[CloudHypothesisNode] = []


class CloudProjectsTree(BaseModel):
    projects: list[CloudProjectNode] = []


class CloudProjectOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_name: str
    project_key: str
    folder_path: str


class CloudProjectHypothesisOut(BaseModel):
    id: int
    experiment_id: int
    display_name: str
    drive_folder_path: Optional[str] = None
