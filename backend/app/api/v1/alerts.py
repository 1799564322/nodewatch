import uuid
from datetime import UTC, datetime
from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import select
from app.api.deps import AdminUser, CurrentUser, DbSession
from app.models.alert import AlertEvent, AlertRule
from app.schemas.alert import AlertEventResponse, AlertRuleCreate, AlertRuleResponse, AlertRuleUpdate

router = APIRouter(tags=["alerts"])

@router.get("/alerts", response_model=list[AlertEventResponse])
def list_alerts(session: DbSession, _: CurrentUser, event_status: str | None = Query(default=None, alias="status"), severity: str | None = None, device_id: uuid.UUID | None = None) -> list[AlertEvent]:
    query = select(AlertEvent)
    if event_status:
        query = query.where(AlertEvent.status == event_status)
    if severity:
        query = query.where(AlertEvent.severity == severity)
    if device_id:
        query = query.where(AlertEvent.device_id == device_id)
    return list(session.scalars(query.order_by(AlertEvent.started_at.desc()).limit(100)))

@router.post("/alerts/{alert_id}/acknowledge", response_model=AlertEventResponse)
def acknowledge(alert_id: uuid.UUID, session: DbSession, admin: AdminUser) -> AlertEvent:
    event = session.get(AlertEvent, alert_id)
    if event is None:
        raise HTTPException(status_code=404, detail="告警不存在")
    if event.resolved_at is not None:
        raise HTTPException(status_code=409, detail="已恢复告警不能确认")
    event.status = "acknowledged"
    event.acknowledged_at = datetime.now(UTC)
    event.acknowledged_by = admin.id
    session.commit()
    return event

@router.get("/alert-rules", response_model=list[AlertRuleResponse])
def list_rules(session: DbSession, _: CurrentUser) -> list[AlertRule]:
    return list(session.scalars(select(AlertRule).order_by(AlertRule.name)))

@router.post("/alert-rules", response_model=AlertRuleResponse, status_code=201)
def create_rule(payload: AlertRuleCreate, session: DbSession, _: AdminUser) -> AlertRule:
    rule = AlertRule(**payload.model_dump(), cooldown_seconds=600, is_enabled=True)
    session.add(rule)
    session.commit()
    return rule

@router.patch("/alert-rules/{rule_id}", response_model=AlertRuleResponse)
def update_rule(rule_id: uuid.UUID, payload: AlertRuleUpdate, session: DbSession, _: AdminUser) -> AlertRule:
    rule = session.get(AlertRule, rule_id)
    if rule is None:
        raise HTTPException(status_code=404, detail="规则不存在")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(rule, field, value)
    session.commit()
    return rule
