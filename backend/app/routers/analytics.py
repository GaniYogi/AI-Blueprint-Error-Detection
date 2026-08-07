import json
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db.database import get_db
from app.db import models
from app.schemas import schemas
from app.core import auth

router = APIRouter(prefix="/analytics", tags=["Dashboard Analytics"])

@router.get("/dashboard", response_model=schemas.DashboardAnalytics)
def get_dashboard_analytics(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    # Get user blueprints
    user_blueprints = db.query(models.Blueprint).filter(
        models.Blueprint.owner_id == current_user.id
    ).all()
    
    total_blueprints = len(user_blueprints)
    
    # Initialize aggregates
    total_errors = 0
    total_violations = 0
    sum_compliance_scores = 0.0
    completed_count = 0
    
    severity_breakdown = {
        "Low": 0,
        "Medium": 0,
        "High": 0,
        "Critical": 0
    }
    
    compliance_history = []
    
    # Sort blueprints chronologically for history chart
    sorted_blueprints = sorted(user_blueprints, key=lambda b: b.created_at)
    
    for bp in sorted_blueprints:
        if bp.status == "completed" and bp.analysis_results:
            ar = bp.analysis_results
            total_errors += ar.total_errors
            total_violations += ar.total_violations
            sum_compliance_scores += ar.compliance_score
            completed_count += 1
            
            # Record score history
            compliance_history.append({
                "date": bp.created_at.strftime("%b %d"),
                "name": bp.original_name[:15] + "..." if len(bp.original_name) > 15 else bp.original_name,
                "score": ar.compliance_score
            })
            
            # Parse raw JSON to count severity categories
            try:
                raw_data = json.loads(ar.raw_json)
                errors_list = raw_data.get("errors", [])
                for err in errors_list:
                    sev = err.get("severity", "Medium")
                    if sev in severity_breakdown:
                        severity_breakdown[sev] += 1
            except Exception:
                pass
                
    # Averages
    avg_score = (sum_compliance_scores / completed_count) if completed_count > 0 else 100.0
    
    # Pending count
    pending_count = sum(1 for bp in user_blueprints if bp.status in ["pending", "processing"])
    
    # Recent blueprints (last 5, sorted desc)
    recent_blueprints = db.query(models.Blueprint).filter(
        models.Blueprint.owner_id == current_user.id
    ).order_by(models.Blueprint.created_at.desc()).limit(5).all()
    
    return {
        "total_blueprints": total_blueprints,
        "total_errors": total_errors,
        "total_violations": total_violations,
        "average_compliance_score": round(avg_score, 1),
        "severity_breakdown": severity_breakdown,
        "recent_blueprints": recent_blueprints,
        "compliance_history": compliance_history,
        
        # CamelCase compatibility
        "totalBlueprints": total_blueprints,
        "completedAnalysis": completed_count,
        "pendingAnalysis": pending_count,
        "complianceScore": round(avg_score, 1)
    }
