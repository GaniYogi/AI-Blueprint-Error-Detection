from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.db.database import get_db
from app.db import models
from app.schemas import schemas
from app.core import auth

router = APIRouter(prefix="/rules", tags=["Compliance Rules"])

DEFAULT_RULES = [
    {
        "rule_key": "min_bedroom_area",
        "name": "Minimum Bedroom Area",
        "description": "Standard minimum floor area for habitable bedrooms in residential projects.",
        "category": "space",
        "default_value": 70.0,
        "current_value": 70.0,
        "unit": "sq ft",
        "severity": "High"
    },
    {
        "rule_key": "min_door_width",
        "name": "Minimum Door Width",
        "description": "Clear opening dimension for bedroom, bathroom, and entry doors.",
        "category": "accessibility",
        "default_value": 2.8,
        "current_value": 2.8,
        "unit": "ft",
        "severity": "Medium"
    },
    {
        "rule_key": "min_corridor_width",
        "name": "Minimum Corridor Width",
        "description": "Minimum width for hallways, passages, and access corridors.",
        "category": "accessibility",
        "default_value": 3.0,
        "current_value": 3.0,
        "unit": "ft",
        "severity": "Medium"
    },
    {
        "rule_key": "window_ventilation_ratio",
        "name": "Window Ventilation Ratio",
        "description": "The ratio of window glass surface area to the bedroom floor area.",
        "category": "ventilation",
        "default_value": 8.0,
        "current_value": 8.0,
        "unit": "%",
        "severity": "Medium"
    },
    {
        "rule_key": "accessibility_compliance",
        "name": "Accessibility Compliance Check",
        "description": "Enables strict checks for bathroom door swings and wheelchair clear spaces.",
        "category": "accessibility",
        "default_value": 1.0,
        "current_value": 1.0,
        "unit": "binary",
        "severity": "High"
    }
]

def init_default_rules(db: Session):
    for r in DEFAULT_RULES:
        exists = db.query(models.ComplianceRule).filter(models.ComplianceRule.rule_key == r["rule_key"]).first()
        if not exists:
            db_rule = models.ComplianceRule(**r)
            db.add(db_rule)
    db.commit()

@router.get("/", response_model=List[schemas.ComplianceRuleResponse])
def get_rules(db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    # Initialize rules if table is empty
    count = db.query(models.ComplianceRule).count()
    if count == 0:
        init_default_rules(db)
    return db.query(models.ComplianceRule).all()

@router.put("/{rule_key}", response_model=schemas.ComplianceRuleResponse)
def update_rule(
    rule_key: str,
    rule_in: schemas.ComplianceRuleUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    rule = db.query(models.ComplianceRule).filter(models.ComplianceRule.rule_key == rule_key).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Compliance rule not found.")
        
    rule.current_value = rule_in.current_value
    db.commit()
    db.refresh(rule)
    return rule
