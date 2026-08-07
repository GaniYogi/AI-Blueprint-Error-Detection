from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app.db.database import get_db
from app.db import models
from app.schemas import schemas
from app.core import auth

router = APIRouter(prefix="/compliance", tags=["Compliance"])

@router.get("/", response_model=List[schemas.ComplianceRuleResponse])
def get_compliance_rules(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    return db.query(models.ComplianceRule).all()
