# app/crud.py
from __future__ import annotations

from datetime import datetime
import json
import re

from sqlalchemy.orm import Session
from sqlalchemy import select, desc, delete, update, func, or_

from . import models, schemas
from .services import drive_sync_service
from .storage import remove_entity_files


# ------------------------------------------------------------------ #
#  EXPERIMENTS
# ------------------------------------------------------------------ #

def create_experiment(db: Session, data: schemas.ExperimentCreate):
    obj = models.Experiment(
        project_name=data.project_name,
        hypothesis=data.hypothesis,
        traffic_type=data.traffic_type,
        hypothesis_type=data.hypothesis_type,
        independent_variable=(data.independent_variable or "").strip() or None,
        metric_x=(data.metric_x or "").strip() or None,
        primary_metric=data.primary_metric,
        validation_threshold=(data.validation_threshold or "").strip() or None,
        threshold_value=data.threshold_value,
        threshold_type=data.threshold_type,
        threshold_operator=data.threshold_operator,
        experiment_status=data.experiment_status or "draft",
        min_volume=data.min_volume,
        volume_min_value=data.volume_min_value,
        volume_unit=data.volume_unit,
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)

    # Auto-create documentation with initial note if contexto is provided
    contexto = (getattr(data, "contexto", None) or "").strip()
    if contexto:
        create_documentation_note(db, "experiment", obj.id, contexto)
    drive_sync_service.ensure_hypothesis_folder(db, obj)
    return obj


def get_experiments(db: Session):
    q = select(models.Experiment).order_by(desc(models.Experiment.created_at))
    return list(db.execute(q).scalars().all())


def get_experiment(db: Session, experiment_id: int):
    q = select(models.Experiment).where(models.Experiment.id == experiment_id)
    return db.execute(q).scalar_one_or_none()


def update_experiment(db: Session, experiment_id: int, data: schemas.ExperimentUpdate):
    exp = get_experiment(db, experiment_id)
    if not exp:
        return None

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if isinstance(value, str):
            value = value.strip() or None
        setattr(exp, field, value)
    exp.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(exp)
    drive_sync_service.ensure_hypothesis_folder(db, exp)
    return exp


def delete_experiment(db: Session, experiment_id: int):
    exp = get_experiment(db, experiment_id)
    if not exp:
        return None
    drive_sync_service.archive_drive_path(exp.drive_folder_path)
    for record in exp.records:
        drive_sync_service.archive_drive_path(record.drive_folder_path)
    record_ids = [record.id for record in exp.records]
    if record_ids:
        db.execute(
            delete(models.Documentation).where(
                models.Documentation.entity_type == "record",
                models.Documentation.entity_id.in_(record_ids),
            )
        )
        db.execute(
            delete(models.AIAnalysis).where(
                models.AIAnalysis.entity_type == "record",
                models.AIAnalysis.entity_id.in_(record_ids),
            )
        )
        db.execute(
            delete(models.EntityFile).where(
                models.EntityFile.entity_type == "record",
                models.EntityFile.entity_id.in_(record_ids),
            )
        )

    db.execute(
        delete(models.Documentation).where(
            models.Documentation.entity_type == "experiment",
            models.Documentation.entity_id == experiment_id,
        )
    )
    db.execute(
        delete(models.AIAnalysis).where(
            models.AIAnalysis.entity_type == "experiment",
            models.AIAnalysis.entity_id == experiment_id,
        )
    )
    db.execute(
        delete(models.EntityFile).where(
            models.EntityFile.entity_type == "experiment",
            models.EntityFile.entity_id == experiment_id,
        )
    )
    db.delete(exp)
    db.commit()
    remove_entity_files("experiment", experiment_id)
    for record_id in record_ids:
        remove_entity_files("record", record_id)
    return exp


def delete_project(db: Session, project_name: str):
    exp_ids = list(
        db.execute(
            select(models.Experiment.id).where(models.Experiment.project_name == project_name)
        ).scalars()
    )
    if not exp_ids:
        return 0
    for exp in db.scalars(select(models.Experiment).where(models.Experiment.id.in_(exp_ids))).all():
        drive_sync_service.archive_drive_path(exp.drive_folder_path)

    record_ids = list(
        db.execute(
            select(models.ExperimentRecord.id).where(
                models.ExperimentRecord.experiment_id.in_(exp_ids)
            )
        ).scalars()
    )

    if record_ids:
        for rec in db.scalars(select(models.ExperimentRecord).where(models.ExperimentRecord.id.in_(record_ids))).all():
            drive_sync_service.archive_drive_path(rec.drive_folder_path)
        db.execute(
            delete(models.Documentation).where(
                models.Documentation.entity_type == "record",
                models.Documentation.entity_id.in_(record_ids),
            )
        )
        db.execute(
            delete(models.AIAnalysis).where(
                models.AIAnalysis.entity_type == "record",
                models.AIAnalysis.entity_id.in_(record_ids),
            )
        )
        db.execute(
            delete(models.ExperimentRecord).where(
                models.ExperimentRecord.id.in_(record_ids)
            )
        )

    db.execute(
        delete(models.Documentation).where(
            models.Documentation.entity_type == "experiment",
            models.Documentation.entity_id.in_(exp_ids),
        )
    )
    db.execute(
        delete(models.AIAnalysis).where(
            models.AIAnalysis.entity_type == "experiment",
            models.AIAnalysis.entity_id.in_(exp_ids),
        )
    )
    db.execute(delete(models.Experiment).where(models.Experiment.id.in_(exp_ids)))
    db.commit()
    return len(exp_ids)


def rename_project(db: Session, project_name: str, new_project_name: str):
    result = db.execute(
        update(models.Experiment)
        .where(models.Experiment.project_name == project_name)
        .values(project_name=new_project_name, updated_at=datetime.utcnow())
    )
    db.commit()
    return result.rowcount or 0


# ------------------------------------------------------------------ #
#  RECORDS
# ------------------------------------------------------------------ #

def _normalize_public_name(name: str) -> str:
    return " ".join(name.strip().lower().split())


def _is_unassigned_public(name: str) -> bool:
    return name in {"sin publico", "sin público", "no asignado", "no asignada"}


def get_public_by_normalized(db: Session, name_normalized: str):
    q = select(models.Public).where(models.Public.name_normalized == name_normalized)
    return db.execute(q).scalar_one_or_none()


def get_public(db: Session, public_id: int):
    q = select(models.Public).where(models.Public.id == public_id)
    return db.execute(q).scalar_one_or_none()


def get_publics(db: Session, search: str | None = None):
    q = (
        select(models.Public, func.count(models.ExperimentRecord.id))
        .join(models.ExperimentRecord, models.ExperimentRecord.public_id == models.Public.id, isouter=True)
        .group_by(models.Public.id)
        .order_by(models.Public.name)
    )
    if search:
        q = q.where(models.Public.name.ilike(f"%{search}%"))
    return list(db.execute(q).all())


def create_public(db: Session, data: schemas.PublicCreate):
    name = data.name.strip()
    normalized = _normalize_public_name(name)
    if not normalized or _is_unassigned_public(normalized):
        raise ValueError("Public name is not allowed.")
    existing = get_public_by_normalized(db, normalized)
    if existing:
        raise ValueError("Public already exists.")
    obj = models.Public(
        name=name,
        name_normalized=normalized,
        description=(data.description or "").strip() or None,
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def update_public(db: Session, public_id: int, data: schemas.PublicUpdate):
    public = get_public(db, public_id)
    if not public:
        return None
    update_data = data.model_dump(exclude_unset=True)
    name = update_data.get("name")
    if name is not None:
        name = name.strip()
        normalized = _normalize_public_name(name)
        if not normalized or _is_unassigned_public(normalized):
            raise ValueError("Public name is not allowed.")
        existing = get_public_by_normalized(db, normalized)
        if existing and existing.id != public_id:
            raise ValueError("Public already exists.")
        public.name = name
        public.name_normalized = normalized
    if "description" in update_data:
        public.description = (update_data.get("description") or "").strip() or None
    public.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(public)
    return public


def get_public_detail(db: Session, public_id: int):
    public = get_public(db, public_id)
    if not public:
        return None, [], schemas.PublicMetrics()
    records = list(
        db.execute(
            select(models.ExperimentRecord).where(
                or_(
                    models.ExperimentRecord.public_id == public_id,
                    models.ExperimentRecord.publico == public.name,
                )
            ).order_by(desc(models.ExperimentRecord.created_at))
        ).scalars().all()
    )
    metrics = schemas.PublicMetrics(
        records_total=len(records),
        clicks_total=sum(r.clicks or 0 for r in records),
        views_total=sum(r.views or 0 for r in records),
        purchases_total=sum(r.purchase or 0 for r in records),
        leads_total=sum(r.lead_form or 0 for r in records),
        initiate_checkouts_total=sum(r.initiate_checkouts or 0 for r in records),
    )
    return public, records, metrics




def delete_public(db: Session, public_id: int):
    public = get_public(db, public_id)
    if not public:
        return None

    affected = db.execute(
        update(models.ExperimentRecord)
        .where(models.ExperimentRecord.public_id == public_id)
        .values(public_id=None, publico=None)
    )
    db.delete(public)
    db.commit()
    return {"deleted": True, "public_id": public_id, "records_unlinked": affected.rowcount or 0}

def create_record(db: Session, data: schemas.RecordCreate):
    # Normalización: si viene string vacío => None (por seguridad)
    organic_piece_type = (data.organic_piece_type or "").strip() or None
    video_url = (data.video_url or "").strip() or None
    campaign_id = (data.campaign_id or "").strip() or None
    ad_set_id = (data.ad_set_id or "").strip() or None
    ad_id = (data.ad_id or "").strip() or None
    publico = (data.publico or "").strip() or None
    hook_text = (data.hook_text or "").strip() or None
    cta_text = (data.cta_text or "").strip() or None
    creative_id = (data.creative_id or "").strip() or None
    public_id = data.public_id
    public = None

    if public_id:
        public = get_public(db, public_id)
        if not public:
            raise ValueError("Public not found.")
    elif publico:
        normalized = _normalize_public_name(publico)
        if not _is_unassigned_public(normalized):
            public = get_public_by_normalized(db, normalized)
            if not public:
                public = models.Public(name=publico, name_normalized=normalized)
                db.add(public)
                db.commit()
                db.refresh(public)

    if public:
        public_id = public.id
        publico = public.name
    elif publico and _is_unassigned_public(_normalize_public_name(publico)):
        publico = None

    obj = models.ExperimentRecord(
        experiment_id=data.experiment_id,
        session_id=data.session_id,
        iteration_number=data.iteration_number,

        clicks=data.clicks,
        views=data.views,
        views_profile=data.views_profile,
        inicia_test=data.inicia_test,

        # orgánico
        organic_piece_type=organic_piece_type,
        likes=data.likes,
        comments=data.comments,
        shares=data.shares,
        saves=data.saves,

        # orgánico - video metrics
        video_url=video_url,
        views_finish_pct=data.views_finish_pct,
        retention_pct=data.retention_pct,
        avg_watch_time=data.avg_watch_time,
        video_duration=data.video_duration,

        # paid
        ctr=data.ctr,
        cpc=data.cpc,
        initiate_checkouts=data.initiate_checkouts,
        view_content=data.view_content,
        lead_form=data.lead_form,
        purchase=data.purchase,

        # paid - video and campaign metrics
        paid_video_duration=data.paid_video_duration,
        campaign_id=campaign_id,
        ad_set_id=ad_set_id,
        ad_id=ad_id,

        # live metrics
        live_viewers_peak=data.live_viewers_peak,
        live_avg_viewers=data.live_avg_viewers,
        live_duration=data.live_duration,
        live_new_followers=data.live_new_followers,

        # creative / execution
        execution_type=data.execution_type,
        record_name=(data.record_name or "").strip() or None,
        publico=publico,
        public_id=public_id,
        hook_text=hook_text,
        hook_type=data.hook_type,
        cta_text=cta_text,
        cta_type=data.cta_type,
        creative_id=creative_id,
        record_status=data.record_status or "collecting",
    )
    obj.updated_at = datetime.utcnow()
    exp = get_experiment(db, data.experiment_id)
    if exp:
        exp.updated_at = datetime.utcnow()
    db.add(obj)
    db.commit()
    db.refresh(obj)

    # Auto-create documentation with initial note if contexto_record is provided
    contexto_record = (getattr(data, "contexto_record", None) or "").strip()
    if contexto_record:
        create_documentation_note(db, "record", obj.id, contexto_record)
    drive_sync_service.ensure_record_folder(db, obj)
    return obj


def get_record(db: Session, record_id: int):
    q = select(models.ExperimentRecord).where(models.ExperimentRecord.id == record_id)
    return db.execute(q).scalar_one_or_none()


def update_record(db: Session, record_id: int, data: schemas.RecordUpdate):
    """Update metrics on an existing record. Does NOT create a new record."""
    rec = get_record(db, record_id)
    if not rec:
        return None

    update_data = data.model_dump(exclude_unset=True)
    if "public_id" in update_data or "publico" in update_data:
        public_id = update_data.pop("public_id", None)
        publico = update_data.pop("publico", None)
        public = None
        if public_id:
            public = get_public(db, public_id)
            if not public:
                raise ValueError("Public not found.")
        elif publico:
            normalized = _normalize_public_name(publico)
            if not _is_unassigned_public(normalized):
                public = get_public_by_normalized(db, normalized)
                if not public:
                    public = models.Public(name=publico.strip(), name_normalized=normalized)
                    db.add(public)
                    db.commit()
                    db.refresh(public)
        if public:
            rec.public_id = public.id
            rec.publico = public.name
        else:
            rec.public_id = None
            rec.publico = None

    for field, value in update_data.items():
        if isinstance(value, str):
            value = value.strip() or None
        setattr(rec, field, value)

    rec.updated_at = datetime.utcnow()
    exp = get_experiment(db, rec.experiment_id)
    if exp:
        exp.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(rec)
    drive_sync_service.ensure_record_folder(db, rec)
    return rec


def close_record(db: Session, record_id: int):
    """Mark a record as closed (no longer receiving traffic)."""
    rec = get_record(db, record_id)
    if not rec:
        return None
    rec.record_status = "closed"
    rec.updated_at = datetime.utcnow()
    exp = get_experiment(db, rec.experiment_id)
    if exp:
        exp.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(rec)
    return rec


def reopen_record(db: Session, record_id: int):
    """Reopen a closed record (back to collecting)."""
    rec = get_record(db, record_id)
    if not rec:
        return None
    rec.record_status = "collecting"
    rec.updated_at = datetime.utcnow()
    exp = get_experiment(db, rec.experiment_id)
    if exp:
        exp.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(rec)
    return rec


def delete_record(db: Session, record_id: int):
    rec = get_record(db, record_id)
    if not rec:
        return None
    drive_sync_service.archive_drive_path(rec.drive_folder_path)
    db.execute(
        delete(models.Documentation).where(
            models.Documentation.entity_type == "record",
            models.Documentation.entity_id == record_id,
        )
    )
    db.execute(
        delete(models.AIAnalysis).where(
            models.AIAnalysis.entity_type == "record",
            models.AIAnalysis.entity_id == record_id,
        )
    )
    db.execute(
        delete(models.EntityFile).where(
            models.EntityFile.entity_type == "record",
            models.EntityFile.entity_id == record_id,
        )
    )
    db.delete(rec)
    db.commit()
    remove_entity_files("record", record_id)
    return rec


def get_records(
    db: Session,
    experiment_id: int | None = None,
    limit: int = 5000,
):
    q = select(models.ExperimentRecord).order_by(desc(models.ExperimentRecord.created_at)).limit(limit)
    if experiment_id:
        q = q.where(models.ExperimentRecord.experiment_id == experiment_id)
    return list(db.execute(q).scalars().all())


def _get_record_by_session_id(db: Session, session_id: str):
    q = (
        select(models.ExperimentRecord)
        .where(models.ExperimentRecord.session_id == session_id)
        .order_by(desc(models.ExperimentRecord.created_at))
    )
    return db.execute(q).scalars().first()


def _get_record_by_name(db: Session, record_name: str):
    q = (
        select(models.ExperimentRecord)
        .where(models.ExperimentRecord.record_name == record_name)
        .order_by(desc(models.ExperimentRecord.created_at))
    )
    return db.execute(q).scalars().first()


def create_record_update_audit(
    db: Session,
    record_id: int,
    source: str,
    changed_fields: list[str],
) -> models.RecordUpdateAudit:
    audit = models.RecordUpdateAudit(
        record_id=record_id,
        source=source,
        changed_fields=json.dumps(changed_fields, ensure_ascii=False),
    )
    db.add(audit)
    return audit


def bulk_update_records(
    db: Session,
    updates: list[schemas.BulkRecordUpdateItem],
    apply_changes: bool,
) -> schemas.BulkRecordUpdateResponse:
    field_aliases = {
        "avg_watch_time_seconds": "avg_watch_time",
        "leads": "lead_form",
        "initiate_test": "inicia_test",
        "initiate_checkout": "initiate_checkouts",
        "purchases": "purchase",
        "new_followers": "live_new_followers",
    }
    update_fields = set(schemas.RecordUpdate.model_fields.keys())
    int_fields = {
        "clicks",
        "views",
        "views_profile",
        "inicia_test",
        "likes",
        "comments",
        "shares",
        "saves",
        "initiate_checkouts",
        "view_content",
        "lead_form",
        "purchase",
        "live_viewers_peak",
        "live_avg_viewers",
        "live_new_followers",
        "public_id",
    }
    float_fields = {
        "views_finish_pct",
        "retention_pct",
        "avg_watch_time",
        "video_duration",
        "ctr",
        "cpc",
        "live_duration",
    }
    string_fields = {
        "hook_text",
        "record_name",
        "publico",
        "hook_type",
        "cta_text",
        "cta_type",
    }

    def parse_int(value: object) -> int | None:
        if value is None:
            return None
        if isinstance(value, bool):
            raise ValueError("Valor booleano no permitido.")
        if isinstance(value, int):
            return value
        if isinstance(value, float):
            if value.is_integer():
                return int(value)
            raise ValueError("Valor decimal no permitido para entero.")
        if isinstance(value, str):
            raw = value.strip().replace(" ", "")
            if raw.endswith("%"):
                raw = raw[:-1].strip()
            if not raw:
                return None
            raw = raw.replace(".", "").replace(",", "")
            if not raw.isdigit():
                raise ValueError("Valor entero invalido.")
            return int(raw)
        raise ValueError("Tipo no soportado para entero.")

    def parse_float(value: object) -> float | None:
        if value is None:
            return None
        if isinstance(value, bool):
            raise ValueError("Valor booleano no permitido.")
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            raw = value.strip().replace(" ", "")
            if raw.endswith("%"):
                raw = raw[:-1].strip()
            if not raw:
                return None
            if re.match(r"^\d{1,3}(\.\d{3})+$", raw):
                raw = raw.replace(".", "")
            if "," in raw and "." not in raw:
                raw = raw.replace(",", ".")
            elif "," in raw and "." in raw:
                raw = raw.replace(",", "")
            try:
                return float(raw)
            except ValueError as exc:
                raise ValueError("Valor decimal invalido.") from exc
        raise ValueError("Tipo no soportado para decimal.")

    def parse_string(value: object) -> str | None:
        if value is None:
            return None
        if isinstance(value, str):
            trimmed = value.strip()
            return trimmed or None
        raise ValueError("Tipo no soportado para texto.")

    response = schemas.BulkRecordUpdateResponse()

    for index, update in enumerate(updates, start=1):
        identifier = None
        record = None
        if update.record_id:
            identifier = f"record_id:{update.record_id}"
            record = get_record(db, update.record_id)
        elif update.session_id:
            identifier = f"session_id:{update.session_id}"
            record = _get_record_by_session_id(db, update.session_id)
        elif update.record_name:
            identifier = f"record_name:{update.record_name}"
            record = _get_record_by_name(db, update.record_name)
        else:
            identifier = f"update_{index}"

        preview_item = schemas.BulkRecordUpdatePreview(
            record_identifier=identifier,
            record_id=record.id if record else None,
            status="error",
            fields_to_update=[],
            unknown_fields=[],
            errors=[],
        )

        if not (update.record_id or update.session_id or update.record_name):
            preview_item.errors.append("Falta record_id, session_id o record_name.")
            response.errors.setdefault(identifier, []).append("Falta identificador.")
            response.preview.append(preview_item)
            continue

        if not record:
            preview_item.status = "not_found"
            response.not_found.append(identifier)
            response.preview.append(preview_item)
            continue

        parsed_fields: dict[str, object] = {}
        for field, raw_value in update.fields.items():
            mapped_field = field_aliases.get(field, field)
            if not mapped_field or mapped_field not in update_fields:
                preview_item.unknown_fields.append(field)
                continue
            try:
                if mapped_field in int_fields:
                    parsed_fields[mapped_field] = parse_int(raw_value)
                elif mapped_field in float_fields:
                    parsed_fields[mapped_field] = parse_float(raw_value)
                elif mapped_field in string_fields:
                    parsed_fields[mapped_field] = parse_string(raw_value)
                else:
                    preview_item.errors.append(f"Campo '{field}' no soportado.")
            except ValueError as exc:
                preview_item.errors.append(f"{field}: {exc}")

        if preview_item.unknown_fields:
            response.unknown_fields[identifier] = preview_item.unknown_fields

        if preview_item.errors:
            response.errors[identifier] = preview_item.errors

        if not parsed_fields:
            preview_item.errors.append("No hay campos validos para actualizar.")
            response.errors[identifier] = preview_item.errors
            response.preview.append(preview_item)
            continue

        preview_item.fields_to_update = sorted(parsed_fields.keys())
        preview_item.status = "ready" if not preview_item.errors else "error"
        response.preview.append(preview_item)

        if preview_item.status != "ready":
            continue

        response.updated_count += 1

        if apply_changes:
            old_values = {field: getattr(record, field) for field in parsed_fields}
            update_schema = schemas.RecordUpdate(**parsed_fields)
            updated_record = update_record(db, record.id, update_schema)
            changed_fields = [
                field for field, old_value in old_values.items()
                if getattr(updated_record, field) != old_value
            ]
            if changed_fields:
                create_record_update_audit(
                    db,
                    record_id=record.id,
                    source="manual_from_screenshot",
                    changed_fields=changed_fields,
                )
                db.commit()

    return response


# ------------------------------------------------------------------ #
#  DOCUMENTATION (qualitative, separate from metrics)
# ------------------------------------------------------------------ #

def get_or_create_documentation(db: Session, entity_type: str, entity_id: int) -> models.Documentation:
    q = select(models.Documentation).where(
        models.Documentation.entity_type == entity_type,
        models.Documentation.entity_id == entity_id,
    )
    doc = db.execute(q).scalar_one_or_none()
    if doc:
        return doc
    doc = models.Documentation(entity_type=entity_type, entity_id=entity_id)
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


def get_documentation(db: Session, entity_type: str, entity_id: int):
    q = select(models.Documentation).where(
        models.Documentation.entity_type == entity_type,
        models.Documentation.entity_id == entity_id,
    )
    return db.execute(q).scalar_one_or_none()


def create_documentation_note(db: Session, entity_type: str, entity_id: int, body: str) -> models.DocumentationNote:
    doc = get_or_create_documentation(db, entity_type, entity_id)
    note = models.DocumentationNote(documentation_id=doc.id, body=body)
    db.add(note)
    doc.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(note)
    db.refresh(doc)
    return note


def update_documentation_note(db: Session, note_id: int, body: str):
    q = select(models.DocumentationNote).where(models.DocumentationNote.id == note_id)
    note = db.execute(q).scalar_one_or_none()
    if not note:
        return None
    note.body = body
    note.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(note)
    return note


# ------------------------------------------------------------------ #
#  FILES
# ------------------------------------------------------------------ #

def create_entity_file(
    db: Session,
    entity_type: str,
    entity_id: int,
    display_name: str,
    stored_name: str,
    folder: str | None,
    content_type: str | None,
    size_bytes: int,
) -> models.EntityFile:
    obj = models.EntityFile(
        entity_type=entity_type,
        entity_id=entity_id,
        display_name=display_name,
        stored_name=stored_name,
        folder=folder,
        content_type=content_type,
        size_bytes=size_bytes,
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def get_entity_file(db: Session, file_id: int) -> models.EntityFile | None:
    q = select(models.EntityFile).where(models.EntityFile.id == file_id)
    return db.execute(q).scalar_one_or_none()


def list_entity_files(db: Session, entity_type: str, entity_id: int) -> list[models.EntityFile]:
    q = (
        select(models.EntityFile)
        .where(models.EntityFile.entity_type == entity_type, models.EntityFile.entity_id == entity_id)
        .order_by(desc(models.EntityFile.created_at))
    )
    return list(db.execute(q).scalars().all())


def update_entity_file(
    db: Session,
    file_id: int,
    display_name: str | None = None,
    folder: str | None = None,
) -> models.EntityFile | None:
    file_obj = get_entity_file(db, file_id)
    if not file_obj:
        return None
    if display_name is not None:
        file_obj.display_name = display_name
    if folder is not None:
        file_obj.folder = folder
    file_obj.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(file_obj)
    return file_obj


def delete_entity_file(db: Session, file_id: int) -> models.EntityFile | None:
    file_obj = get_entity_file(db, file_id)
    if not file_obj:
        return None
    db.delete(file_obj)
    db.commit()
    return file_obj


# ------------------------------------------------------------------ #
#  AI ANALYSIS
# ------------------------------------------------------------------ #

def create_ai_analysis(
    db: Session,
    entity_type: str,
    entity_id: int,
    analysis_type: str,
    model: str,
    prompt_version: str,
    input_snapshot: str,
    output: str,
) -> models.AIAnalysis:
    obj = models.AIAnalysis(
        entity_type=entity_type,
        entity_id=entity_id,
        analysis_type=analysis_type,
        model=model,
        prompt_version=prompt_version,
        input_snapshot=input_snapshot,
        output=output,
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def get_ai_analyses(
    db: Session,
    entity_type: str,
    entity_id: int,
    analysis_type: str | None = None,
) -> list[models.AIAnalysis]:
    q = (
        select(models.AIAnalysis)
        .where(
            models.AIAnalysis.entity_type == entity_type,
            models.AIAnalysis.entity_id == entity_id,
        )
        .order_by(desc(models.AIAnalysis.created_at))
    )
    if analysis_type:
        q = q.where(models.AIAnalysis.analysis_type == analysis_type)
    return list(db.execute(q).scalars().all())


# ------------------------------------------------------------------ #
#  HYPOTHESIS EVALUATION
# ------------------------------------------------------------------ #

def _compute_aggregated_metric(records: list[models.ExperimentRecord], metric: str) -> tuple[float | None, int]:
    """Compute an aggregated metric across all records.

    For rate/percentage metrics: compute a robust aggregate (median) of per-record values.
    For direct count metrics: sum all values.

    Returns (aggregated_value, total_volume).
    """
    def median(values: list[float]) -> float | None:
        if not values:
            return None
        values.sort()
        mid = len(values) // 2
        if len(values) % 2 == 1:
            return values[mid]
        return (values[mid - 1] + values[mid]) / 2

    # Rate metrics require numerator/denominator aggregation
    rate_definitions = {
        "initiate_checkout_rate": ("initiate_checkouts", "views"),
        "view_content_rate": ("view_content", "views"),
        "lead_rate": ("lead_form", "views"),
        "purchase_rate": ("purchase", "views"),
        "ctr": ("clicks", "views"),
    }

    if metric in rate_definitions:
        num_field, den_field = rate_definitions[metric]
        values = []
        for r in records:
            n = getattr(r, num_field, None) or 0
            d = getattr(r, den_field, None) or 0
            if d > 0:
                values.append((n / d) * 100)
        aggregated = median(values)
        if aggregated is None:
            return None, 0
        return aggregated, len(values)

    # Cost metrics: use median to avoid summing across records
    if metric == "cpc":
        values = []
        for r in records:
            v = getattr(r, "cpc", None)
            if v is not None:
                values.append(float(v))
        aggregated = median(values)
        if aggregated is None:
            return None, 0
        return aggregated, len(values)

    # Averaged metrics (percentages, time)
    averaged_metrics = {"views_finish_pct", "retention_pct", "avg_watch_time"}
    if metric in averaged_metrics:
        values = []
        for r in records:
            v = getattr(r, metric, None)
            if v is not None:
                values.append(float(v))
        aggregated = median(values)
        if aggregated is None:
            return None, 0
        return aggregated, len(values)

    # Simple sum metrics
    total = 0
    count = 0
    for r in records:
        v = getattr(r, metric, None)
        if v is not None:
            total += v
            count += 1
    if count == 0:
        return None, 0
    return float(total), count


def _parse_threshold(raw: str | None) -> tuple[str | None, float | None, bool]:
    """Parse threshold like '>= 3%' into (operator, value, is_percent)."""
    if not raw:
        return None, None, False
    raw = raw.strip()
    is_percent = raw.endswith("%")
    raw = raw.rstrip("%").strip()
    match = re.match(r"(>=|<=|>|<|=)\s*([\d.]+)", raw)
    if not match:
        return None, None, is_percent
    return match.group(1), float(match.group(2)), is_percent


def _infer_threshold_type(metric: str | None, is_percent: bool) -> str | None:
    if not metric:
        return "percentage" if is_percent else None
    if is_percent:
        return "percentage"
    if _is_count_metric(metric):
        return "absolute"
    return "decimal"


def _compute_volume_total(records: list[models.ExperimentRecord], volume_unit: str | None) -> int:
    if not volume_unit:
        return 0
    volume_field_map = {
        "clicks": "clicks",
        "ctr": "views",
        "cpc": "clicks",
        "initiate_checkout_rate": "views",
        "view_content_rate": "views",
        "lead_rate": "views",
        "purchase_rate": "views",
        "views": "views",
        "views_profile": "views_profile",
        "inicia_test": "inicia_test",
        "likes": "likes",
        "comments": "comments",
        "shares": "shares",
        "saves": "saves",
        "views_finish_pct": "views",
        "retention_pct": "views",
        "avg_watch_time": "views",
        "live_viewers_peak": "live_viewers_peak",
        "live_avg_viewers": "live_avg_viewers",
        "live_new_followers": "live_new_followers",
    }
    field = volume_field_map.get(volume_unit)
    if not field:
        return 0
    total = 0
    for r in records:
        total += getattr(r, field, None) or 0
    return total


def _is_rate_metric(metric: str) -> bool:
    return metric.endswith("_rate") or metric in {"ctr"}


def _is_percentage_metric(metric: str) -> bool:
    return metric in {"views_finish_pct", "retention_pct"}


def _is_average_metric(metric: str) -> bool:
    return metric in {"avg_watch_time"}


def _is_count_metric(metric: str) -> bool:
    if _is_rate_metric(metric) or _is_percentage_metric(metric) or _is_average_metric(metric):
        return False
    return metric in {
        "clicks",
        "views",
        "views_profile",
        "inicia_test",
        "likes",
        "comments",
        "shares",
        "saves",
        "initiate_checkouts",
        "view_content",
        "lead_form",
        "purchase",
        "live_viewers_peak",
        "live_avg_viewers",
        "live_new_followers",
    }


def _compare_threshold(op: str, value: float, target: float) -> bool:
    if op == ">=":
        return value >= target
    if op == ">":
        return value > target
    if op == "<=":
        return value <= target
    if op == "<":
        return value < target
    return False


def _compute_comparison_value(
    metric: str | None,
    threshold_type: str | None,
    aggregated_value: float | None,
    volume_total: int,
) -> float | None:
    if aggregated_value is None or not metric or not threshold_type:
        return None

    if threshold_type == "percentage":
        if _is_rate_metric(metric) or _is_percentage_metric(metric):
            return aggregated_value
        if _is_count_metric(metric) and volume_total > 0:
            return (aggregated_value / volume_total) * 100
    elif threshold_type in {"absolute", "decimal"}:
        if not _is_rate_metric(metric) and not _is_percentage_metric(metric):
            return aggregated_value
    return None


def _evaluate_records_segment(
    records: list[models.ExperimentRecord],
    exp: models.Experiment,
    op: str | None,
    threshold_val: float | None,
    threshold_type: str | None,
) -> dict:
    records_collecting = sum(1 for r in records if r.record_status == "collecting")
    records_closed = sum(1 for r in records if r.record_status == "closed")
    all_closed = records_collecting == 0 and len(records) > 0

    aggregated_value = None
    if exp.primary_metric and records:
        aggregated_value, _ = _compute_aggregated_metric(records, exp.primary_metric)

    volume_total = _compute_volume_total(records, exp.volume_unit)
    min_vol = exp.volume_min_value
    volume_sufficient = bool(min_vol and volume_total >= min_vol)
    ready = volume_sufficient and all_closed

    comparison_value = None
    suggested_status = "inconclusive"
    explanation = "evidencia insuficiente"

    if ready and aggregated_value is not None and op and threshold_val is not None and threshold_type:
        comparison_value = _compute_comparison_value(
            exp.primary_metric,
            threshold_type,
            aggregated_value,
            volume_total,
        )
        if comparison_value is not None:
            if _compare_threshold(op, comparison_value, threshold_val):
                suggested_status = "validated"
                explanation = "cumple umbral"
            else:
                suggested_status = "invalidated"
                explanation = "no cumple umbral"

    return {
        "aggregated_value": round(aggregated_value, 4) if aggregated_value is not None else None,
        "comparison_value": round(comparison_value, 4) if comparison_value is not None else None,
        "total_volume": volume_total,
        "volume_sufficient": volume_sufficient,
        "all_records_closed": all_closed,
        "ready_to_evaluate": ready,
        "suggested_status": suggested_status,
        "explanation": explanation,
        "records_collecting": records_collecting,
        "records_closed": records_closed,
    }


def evaluate_experiment(db: Session, experiment_id: int) -> schemas.ExperimentEvaluation:
    """Evaluate a hypothesis by aggregating all its records and comparing to threshold."""
    exp = get_experiment(db, experiment_id)
    if not exp:
        return None

    records = get_records(db, experiment_id=experiment_id, limit=50000)

    suggested_status = None
    op = exp.threshold_operator
    threshold_val = exp.threshold_value
    threshold_type = exp.threshold_type
    if (not op or threshold_val is None or not threshold_type) and exp.validation_threshold:
        parsed_op, parsed_val, parsed_percent = _parse_threshold(exp.validation_threshold)
        op = op or parsed_op
        threshold_val = threshold_val if threshold_val is not None else parsed_val
        threshold_type = threshold_type or _infer_threshold_type(exp.primary_metric, parsed_percent)

    grouped: dict[str, list[models.ExperimentRecord]] = {}
    for record in records:
        publico = (record.publico or "").strip() or "Sin público"
        grouped.setdefault(publico, []).append(record)

    segments: list[schemas.ExperimentEvaluationSegment] = []
    for publico in sorted(grouped.keys()):
        segment_values = _evaluate_records_segment(
            grouped[publico],
            exp,
            op,
            threshold_val,
            threshold_type,
        )
        segments.append(
            schemas.ExperimentEvaluationSegment(
                publico=publico,
                records_total=len(grouped[publico]),
                aggregated_value=segment_values["aggregated_value"],
                comparison_value=segment_values["comparison_value"],
                total_volume=segment_values["total_volume"],
                volume_sufficient=segment_values["volume_sufficient"],
                all_records_closed=segment_values["all_records_closed"],
                ready_to_evaluate=segment_values["ready_to_evaluate"],
                suggested_status=segment_values["suggested_status"],
                explanation=segment_values["explanation"],
            )
        )

    segmented_by_public = len(segments) > 1

    records_collecting = sum(1 for r in records if r.record_status == "collecting")
    records_closed = sum(1 for r in records if r.record_status == "closed")
    all_closed = records_collecting == 0 and len(records) > 0
    volume_total = _compute_volume_total(records, exp.volume_unit)
    min_vol = exp.volume_min_value
    volume_sufficient = bool(min_vol and volume_total >= min_vol)

    ready = volume_sufficient and all_closed and not segmented_by_public
    aggregated_value = None
    if exp.primary_metric and records and not segmented_by_public:
        aggregated_value, _ = _compute_aggregated_metric(records, exp.primary_metric)

    if ready and aggregated_value is not None and op and threshold_val is not None and threshold_type:
        comparison_value = _compute_comparison_value(
            exp.primary_metric,
            threshold_type,
            aggregated_value,
            volume_total,
        )
        if comparison_value is not None:
            suggested_status = "validated" if _compare_threshold(op, comparison_value, threshold_val) else "invalidated"

    return schemas.ExperimentEvaluation(
        experiment_id=experiment_id,
        primary_metric=exp.primary_metric,
        aggregated_value=round(aggregated_value, 4) if aggregated_value is not None else None,
        threshold_raw=exp.validation_threshold,
        threshold_value=threshold_val,
        threshold_type=threshold_type,
        threshold_operator=op,
        total_volume=volume_total,
        min_volume=exp.min_volume,
        volume_min_value=exp.volume_min_value,
        volume_unit=exp.volume_unit,
        volume_sufficient=volume_sufficient,
        all_records_closed=all_closed,
        ready_to_evaluate=ready,
        suggested_status=suggested_status,
        records_collecting=records_collecting,
        records_closed=records_closed,
        segmented_by_public=segmented_by_public,
        segments=segments,
    )


# ------------------------------------------------------------------ #
#  INTERVIEWS
# ------------------------------------------------------------------ #

def _template_out(template: models.InterviewTemplate) -> schemas.InterviewTemplateOut:
    return schemas.InterviewTemplateOut(
        id=template.id,
        project_id=template.project_id,
        name=template.name,
        description=template.description,
        fields_json=json.loads(template.fields_json or "{}"),
        created_at=template.created_at,
    )


def _session_out(session: models.InterviewSession) -> schemas.InterviewSessionOut:
    return schemas.InterviewSessionOut(
        id=session.id,
        template_id=session.template_id,
        project_id=session.project_id,
        hypothesis_id=session.hypothesis_id,
        client_id=session.client_id,
        metric_name=session.metric_name,
        interviewee_name=session.interviewee_name,
        notes=session.notes,
        responses_json=json.loads(session.responses_json or "{}"),
        created_at=session.created_at,
        updated_at=session.updated_at,
    )


def create_interview_template(db: Session, data: schemas.InterviewTemplateCreate):
    obj = models.InterviewTemplate(
        project_id=data.project_id,
        name=data.name.strip(),
        description=(data.description or "").strip() or None,
        fields_json=json.dumps(data.fields_json),
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return _template_out(obj)


def list_interview_templates(db: Session, project_id: int | None = None):
    query = select(models.InterviewTemplate)
    if project_id is not None:
        query = query.where(models.InterviewTemplate.project_id == project_id)
    query = query.order_by(desc(models.InterviewTemplate.created_at))
    return [_template_out(item) for item in db.scalars(query).all()]


def get_interview_template(db: Session, template_id: int):
    item = db.get(models.InterviewTemplate, template_id)
    return _template_out(item) if item else None


def update_interview_template(db: Session, template_id: int, data: schemas.InterviewTemplateUpdate):
    item = db.get(models.InterviewTemplate, template_id)
    if not item:
        return None
    payload = data.model_dump(exclude_unset=True)
    if "name" in payload:
        item.name = (payload["name"] or "").strip()
    if "description" in payload:
        item.description = (payload["description"] or "").strip() or None
    if "fields_json" in payload and payload["fields_json"] is not None:
        item.fields_json = json.dumps(payload["fields_json"])
    db.commit()
    db.refresh(item)
    return _template_out(item)


def delete_interview_template(db: Session, template_id: int):
    item = db.get(models.InterviewTemplate, template_id)
    if not item:
        return None
    db.execute(delete(models.InterviewSession).where(models.InterviewSession.template_id == template_id))
    db.delete(item)
    db.commit()
    return {"deleted": True, "template_id": template_id}


def create_interview_session(db: Session, data: schemas.InterviewSessionCreate):
    obj = models.InterviewSession(
        template_id=data.template_id,
        project_id=data.project_id,
        hypothesis_id=data.hypothesis_id,
        client_id=data.client_id,
        metric_name=(data.metric_name or "").strip() or None,
        interviewee_name=data.interviewee_name.strip(),
        notes=(data.notes or "").strip() or None,
        responses_json=json.dumps(data.responses_json),
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return _session_out(obj)


def list_interview_sessions(db: Session, project_id: int | None = None):
    query = select(models.InterviewSession)
    if project_id is not None:
        query = query.where(models.InterviewSession.project_id == project_id)
    query = query.order_by(desc(models.InterviewSession.created_at))
    return [_session_out(item) for item in db.scalars(query).all()]


def get_interview_session(db: Session, session_id: int):
    item = db.get(models.InterviewSession, session_id)
    return _session_out(item) if item else None


def update_interview_session(db: Session, session_id: int, data: schemas.InterviewSessionUpdate):
    item = db.get(models.InterviewSession, session_id)
    if not item:
        return None
    payload = data.model_dump(exclude_unset=True)
    for key in ["hypothesis_id", "client_id", "template_id", "metric_name"]:
        if key in payload:
            setattr(item, key, payload[key])
    if "interviewee_name" in payload:
        item.interviewee_name = (payload["interviewee_name"] or "").strip()
    if "notes" in payload:
        item.notes = (payload["notes"] or "").strip() or None
    if "responses_json" in payload and payload["responses_json"] is not None:
        item.responses_json = json.dumps(payload["responses_json"])
    item.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(item)
    return _session_out(item)


def delete_interview_session(db: Session, session_id: int):
    item = db.get(models.InterviewSession, session_id)
    if not item:
        return None
    db.delete(item)
    db.commit()
    return {"deleted": True, "session_id": session_id}

# ------------------------------------------------------------------ #
#  CLIENTS + INTERVIEWS V2 + ATTACHMENTS
# ------------------------------------------------------------------ #

def _client_out(client: models.Client) -> schemas.ClientOut:
    return schemas.ClientOut(
        id=client.id,
        full_name=client.full_name,
        age=client.age,
        email=client.email,
        phone=client.phone,
        country=client.country,
        state=client.state,
        city=client.city,
        nationality=client.nationality,
        gender=client.gender,
        tags=json.loads(client.tags_json or "[]"),
        notes=client.notes,
        created_at=client.created_at,
        updated_at=client.updated_at,
    )


def create_client(db: Session, data: schemas.ClientCreate):
    obj = models.Client(
        full_name=data.full_name.strip(),
        age=data.age,
        email=(data.email or "").strip() or None,
        phone=(data.phone or "").strip() or None,
        country=data.country.strip(),
        state=(data.state or "").strip() or None,
        city=(data.city or "").strip() or None,
        nationality=(data.nationality or "").strip() or None,
        gender=(data.gender or "").strip() or None,
        tags_json=json.dumps(data.tags or []),
        notes=(data.notes or "").strip() or None,
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return _client_out(obj)


def list_clients(db: Session, search: str | None = None, country: str | None = None, limit: int = 100, offset: int = 0):
    q = select(models.Client)
    if search:
        term = f"%{search.strip()}%"
        q = q.where(or_(models.Client.full_name.ilike(term), models.Client.email.ilike(term), models.Client.phone.ilike(term), models.Client.country.ilike(term)))
    if country:
        q = q.where(models.Client.country.ilike(country.strip()))
    q = q.order_by(desc(models.Client.created_at)).offset(offset).limit(limit)
    return [_client_out(x) for x in db.scalars(q).all()]


def get_client(db: Session, client_id: int):
    obj = db.get(models.Client, client_id)
    return _client_out(obj) if obj else None


def update_client(db: Session, client_id: int, data: schemas.ClientUpdate):
    obj = db.get(models.Client, client_id)
    if not obj:
        return None
    payload = data.model_dump(exclude_unset=True)
    for key in ["full_name", "age", "email", "phone", "country", "state", "city", "nationality", "gender", "notes"]:
        if key in payload:
            val = payload[key]
            if isinstance(val, str):
                val = val.strip() or None
            setattr(obj, key, val)
    if "tags" in payload and payload["tags"] is not None:
        obj.tags_json = json.dumps(payload["tags"])
    obj.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(obj)
    return _client_out(obj)


def delete_client(db: Session, client_id: int):
    obj = db.get(models.Client, client_id)
    if not obj:
        return None
    db.execute(update(models.InterviewSession).where(models.InterviewSession.client_id == client_id).values(client_id=None))
    db.delete(obj)
    db.commit()
    return {"deleted": True, "client_id": client_id}


def list_client_interviews(db: Session, client_id: int):
    q = select(models.InterviewSession).where(models.InterviewSession.client_id == client_id).order_by(desc(models.InterviewSession.created_at))
    return [_session_out(item) for item in db.scalars(q).all()]


def create_interview_v2(db: Session, data: schemas.InterviewSessionCreateV2):
    obj = models.InterviewSession(
        project_id=data.project_id,
        hypothesis_id=data.hypothesis_id,
        client_id=data.client_id,
        template_id=data.template_id,
        metric_name=(data.metric_name or "").strip() or None,
        interviewee_name=data.interviewee_name.strip(),
        responses_json=json.dumps(data.responses_json or {}),
        notes=(data.notes or "").strip() or None,
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return _session_out(obj)


def list_interviews_v2(db: Session, project_id: int | None = None, hypothesis_id: int | None = None, client_id: int | None = None, limit: int = 100, offset: int = 0):
    q = select(models.InterviewSession)
    if project_id is not None:
        q = q.where(models.InterviewSession.project_id == project_id)
    if hypothesis_id is not None:
        q = q.where(models.InterviewSession.hypothesis_id == hypothesis_id)
    if client_id is not None:
        q = q.where(models.InterviewSession.client_id == client_id)
    q = q.order_by(desc(models.InterviewSession.created_at)).offset(offset).limit(limit)
    return [_session_out(item) for item in db.scalars(q).all()]


def patch_interview_v2(db: Session, interview_id: int, data: schemas.InterviewSessionPatchV2):
    obj = db.get(models.InterviewSession, interview_id)
    if not obj:
        return None
    payload = data.model_dump(exclude_unset=True)
    for key in ["project_id", "hypothesis_id", "client_id", "template_id", "interviewee_name", "metric_name", "notes"]:
        if key in payload:
            val = payload[key]
            if isinstance(val, str):
                val = val.strip() or None
            setattr(obj, key, val)
    if "responses_json" in payload and payload["responses_json"] is not None:
        obj.responses_json = json.dumps(payload["responses_json"])
    obj.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(obj)
    return _session_out(obj)


def create_interview_attachment(db: Session, interview_id: int, filename: str, content_type: str | None, size: int, storage_path: str):
    obj = models.InterviewAttachment(
        interview_session_id=interview_id,
        filename=filename,
        content_type=content_type,
        size=size,
        storage_path=storage_path,
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return schemas.InterviewAttachmentOut.model_validate(obj)


def list_interview_attachments(db: Session, interview_id: int):
    q = select(models.InterviewAttachment).where(models.InterviewAttachment.interview_session_id == interview_id).order_by(desc(models.InterviewAttachment.created_at))
    return [schemas.InterviewAttachmentOut.model_validate(x) for x in db.scalars(q).all()]


def get_attachment(db: Session, attachment_id: int):
    return db.get(models.InterviewAttachment, attachment_id)


def delete_attachment(db: Session, attachment_id: int):
    obj = db.get(models.InterviewAttachment, attachment_id)
    if not obj:
        return None
    db.delete(obj)
    db.commit()
    return obj
