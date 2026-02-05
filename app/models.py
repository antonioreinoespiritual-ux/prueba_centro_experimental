# app/models.py
from __future__ import annotations

from datetime import datetime

from sqlalchemy import String, Integer, DateTime, ForeignKey, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class Experiment(Base):
    __tablename__ = "experiments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    project_name: Mapped[str] = mapped_column(String(200), nullable=False)
    hypothesis: Mapped[str] = mapped_column(String(5000), nullable=False)
    traffic_type: Mapped[str] = mapped_column(String(20), nullable=False)  # paid/organic/mixed
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    records: Mapped[list["ExperimentRecord"]] = relationship(
        "ExperimentRecord",
        back_populates="experiment",
        cascade="all, delete-orphan",
    )


class ExperimentRecord(Base):
    __tablename__ = "experiment_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    experiment_id: Mapped[int] = mapped_column(ForeignKey("experiments.id"), nullable=False, index=True)
    session_id: Mapped[str] = mapped_column(String(200), nullable=False, index=True)

    clicks: Mapped[int | None] = mapped_column(Integer, nullable=True)
    views: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # orgánico
    organic_piece_type: Mapped[str | None] = mapped_column(String(200), nullable=True)
    likes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    comments: Mapped[int | None] = mapped_column(Integer, nullable=True)
    shares: Mapped[int | None] = mapped_column(Integer, nullable=True)
    saves: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # paid
    ctr: Mapped[float | None] = mapped_column(Float, nullable=True)
    cpc: Mapped[float | None] = mapped_column(Float, nullable=True)
    initiate_checkouts: Mapped[int | None] = mapped_column(Integer, nullable=True)
    view_content: Mapped[int | None] = mapped_column(Integer, nullable=True)
    lead_form: Mapped[int | None] = mapped_column(Integer, nullable=True)
    purchase: Mapped[int | None] = mapped_column(Integer, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    experiment: Mapped["Experiment"] = relationship("Experiment", back_populates="records")
