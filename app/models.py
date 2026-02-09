# app/models.py
from __future__ import annotations

from datetime import datetime

from sqlalchemy import String, Integer, DateTime, ForeignKey, Float, Text, UniqueConstraint
from typing import Optional
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class Experiment(Base):
    __tablename__ = "experiments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    project_name: Mapped[str] = mapped_column(String(200), nullable=False)
    hypothesis: Mapped[str] = mapped_column(String(5000), nullable=False)
    traffic_type: Mapped[str] = mapped_column(String(20), nullable=False)  # paid/organic/mixed/live
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=True,
        onupdate=datetime.utcnow,
    )

    # --- Lean Hypothesis fields (new) ---
    hypothesis_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    independent_variable: Mapped[str | None] = mapped_column(String(500), nullable=True)
    metric_x: Mapped[str | None] = mapped_column(String(100), nullable=True)
    primary_metric: Mapped[str | None] = mapped_column(String(100), nullable=True)
    validation_threshold: Mapped[str | None] = mapped_column(String(200), nullable=True)
    threshold_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    threshold_type: Mapped[str | None] = mapped_column(String(30), nullable=True)
    threshold_operator: Mapped[str | None] = mapped_column(String(5), nullable=True)
    experiment_status: Mapped[str] = mapped_column(String(30), nullable=False, default="draft")
    min_volume: Mapped[int | None] = mapped_column(Integer, nullable=True)
    volume_min_value: Mapped[int | None] = mapped_column(Integer, nullable=True)
    volume_unit: Mapped[str | None] = mapped_column(String(30), nullable=True)
    drive_folder_path: Mapped[str | None] = mapped_column(String(500), nullable=True, index=True)

    records: Mapped[list["ExperimentRecord"]] = relationship(
        "ExperimentRecord",
        back_populates="experiment",
        cascade="all, delete-orphan",
    )


class Public(Base):
    __tablename__ = "publics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    name_normalized: Mapped[str] = mapped_column(String(200), nullable=False, unique=True, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, onupdate=datetime.utcnow)

    records: Mapped[list["ExperimentRecord"]] = relationship(
        "ExperimentRecord",
        back_populates="public",
    )


class ExperimentRecord(Base):
    __tablename__ = "experiment_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    experiment_id: Mapped[int] = mapped_column(ForeignKey("experiments.id"), nullable=False, index=True)
    session_id: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    iteration_number: Mapped[int | None] = mapped_column(Integer, nullable=True)

    clicks: Mapped[int | None] = mapped_column(Integer, nullable=True)
    views: Mapped[int | None] = mapped_column(Integer, nullable=True)
    views_profile: Mapped[int | None] = mapped_column(Integer, nullable=True)
    inicia_test: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # orgánico
    organic_piece_type: Mapped[str | None] = mapped_column(String(200), nullable=True)
    likes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    comments: Mapped[int | None] = mapped_column(Integer, nullable=True)
    shares: Mapped[int | None] = mapped_column(Integer, nullable=True)
    saves: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # orgánico - video metrics
    video_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    views_finish_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    retention_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    avg_watch_time: Mapped[float | None] = mapped_column(Float, nullable=True)
    video_duration: Mapped[float | None] = mapped_column(Float, nullable=True)

    # paid
    ctr: Mapped[float | None] = mapped_column(Float, nullable=True)
    cpc: Mapped[float | None] = mapped_column(Float, nullable=True)
    initiate_checkouts: Mapped[int | None] = mapped_column(Integer, nullable=True)
    view_content: Mapped[int | None] = mapped_column(Integer, nullable=True)
    lead_form: Mapped[int | None] = mapped_column(Integer, nullable=True)
    purchase: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # paid - video and campaign metrics
    paid_video_duration: Mapped[float | None] = mapped_column(Float, nullable=True)
    campaign_id: Mapped[str | None] = mapped_column(String(200), nullable=True)
    ad_set_id: Mapped[str | None] = mapped_column(String(200), nullable=True)
    ad_id: Mapped[str | None] = mapped_column(String(200), nullable=True)

    # live metrics
    live_viewers_peak: Mapped[int | None] = mapped_column(Integer, nullable=True)
    live_avg_viewers: Mapped[int | None] = mapped_column(Integer, nullable=True)
    live_duration: Mapped[float | None] = mapped_column(Float, nullable=True)
    live_new_followers: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # --- Creative / Execution fields (new) ---
    execution_type: Mapped[str | None] = mapped_column(String(30), nullable=True)
    record_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    publico: Mapped[str | None] = mapped_column(String(200), nullable=True)
    public_id: Mapped[int | None] = mapped_column(ForeignKey("publics.id"), nullable=True, index=True)
    hook_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    hook_type: Mapped[str | None] = mapped_column(String(30), nullable=True)
    cta_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    cta_type: Mapped[str | None] = mapped_column(String(30), nullable=True)
    creative_id: Mapped[str | None] = mapped_column(String(200), nullable=True)
    record_status: Mapped[str] = mapped_column(String(20), nullable=False, default="collecting")
    drive_folder_path: Mapped[str | None] = mapped_column(String(500), nullable=True, index=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, onupdate=datetime.utcnow)

    experiment: Mapped["Experiment"] = relationship("Experiment", back_populates="records")
    public: Mapped[Public | None] = relationship("Public", back_populates="records")


class RecordUpdateAudit(Base):
    __tablename__ = "record_update_audits"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    record_id: Mapped[int] = mapped_column(ForeignKey("experiment_records.id"), nullable=False, index=True)
    source: Mapped[str] = mapped_column(String(100), nullable=False)
    changed_fields: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

class Documentation(Base):
    __tablename__ = "documentation"
    __table_args__ = (
        UniqueConstraint("entity_type", "entity_id", name="uq_documentation_entity"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    entity_type: Mapped[str] = mapped_column(String(20), nullable=False)  # 'experiment' | 'record'
    entity_id: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, onupdate=datetime.utcnow)

    notes: Mapped[list["DocumentationNote"]] = relationship(
        "DocumentationNote",
        back_populates="documentation",
        cascade="all, delete-orphan",
        order_by="desc(DocumentationNote.created_at)",
    )


class DocumentationNote(Base):
    __tablename__ = "documentation_note"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    documentation_id: Mapped[int] = mapped_column(ForeignKey("documentation.id"), nullable=False, index=True)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, onupdate=datetime.utcnow)

    documentation: Mapped["Documentation"] = relationship("Documentation", back_populates="notes")


class AIAnalysis(Base):
    __tablename__ = "ai_analysis"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    entity_type: Mapped[str] = mapped_column(String(20), nullable=False)  # 'experiment' | 'record'
    entity_id: Mapped[int] = mapped_column(Integer, nullable=False)
    analysis_type: Mapped[str] = mapped_column(String(20), nullable=False)  # 'metrics' | 'notes'
    model: Mapped[str] = mapped_column(String(100), nullable=False)
    prompt_version: Mapped[str] = mapped_column(String(50), nullable=False)
    input_snapshot: Mapped[str] = mapped_column(Text, nullable=False)
    output: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class EntityFile(Base):
    __tablename__ = "entity_files"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    entity_type: Mapped[str] = mapped_column(String(20), nullable=False)
    entity_id: Mapped[int] = mapped_column(Integer, nullable=False)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    stored_name: Mapped[str] = mapped_column(String(255), nullable=False)
    folder: Mapped[str | None] = mapped_column(String(255), nullable=True)
    content_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, onupdate=datetime.utcnow)


class ChatMemory(Base):
    __tablename__ = "chat_memory"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    assistant_type: Mapped[str] = mapped_column(String(20), nullable=False, default="consult", index=True)
    memory_type: Mapped[str] = mapped_column(String(30), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    references_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, onupdate=datetime.utcnow)


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    conversation_id: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    assistant_type: Mapped[str] = mapped_column(String(20), nullable=False, default="consult", index=True)
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    references_json: Mapped[str | None] = mapped_column(Text, nullable=True)


class CloudLibrary(Base):
    __tablename__ = "cloud_libraries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    root_path: Mapped[str] = mapped_column(String(500), nullable=False)
    owner_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, onupdate=datetime.utcnow)

    items: Mapped[list["CloudItem"]] = relationship(
        "CloudItem",
        back_populates="library",
        cascade="all, delete-orphan",
    )


class CloudItem(Base):
    __tablename__ = "cloud_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    parent_id: Mapped[int | None] = mapped_column(ForeignKey("cloud_items.id"), nullable=True, index=True)
    library_id: Mapped[int] = mapped_column(ForeignKey("cloud_libraries.id"), nullable=False, index=True)
    item_type: Mapped[str] = mapped_column(String(20), nullable=False)  # folder | file
    size: Mapped[int | None] = mapped_column(Integer, nullable=True)
    path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    rel_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    owner_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, onupdate=datetime.utcnow)

    library: Mapped["CloudLibrary"] = relationship("CloudLibrary", back_populates="items")
    parent: Mapped[Optional["CloudItem"]] = relationship("CloudItem", remote_side="CloudItem.id")


class CloudShare(Base):
    __tablename__ = "cloud_shares"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    item_id: Mapped[int] = mapped_column(ForeignKey("cloud_items.id"), nullable=False, index=True)
    shared_with: Mapped[str] = mapped_column(String(200), nullable=False)
    permission: Mapped[str] = mapped_column(String(20), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class CloudAudit(Base):
    __tablename__ = "cloud_audits"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    item_id: Mapped[int | None] = mapped_column(ForeignKey("cloud_items.id"), nullable=True, index=True)
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    user_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class AssistantDraft(Base):
    __tablename__ = "assistant_drafts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    conversation_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    assistant_type: Mapped[str] = mapped_column(String(20), nullable=False, default="openclaw", index=True)
    draft_type: Mapped[str] = mapped_column(String(20), nullable=False)
    payload_json: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, onupdate=datetime.utcnow)
