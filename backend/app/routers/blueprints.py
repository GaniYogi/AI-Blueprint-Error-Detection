import os
import shutil
import uuid
import json
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session, joinedload
from typing import List
from app.db.database import get_db, SessionLocal
from app.db import models
from app.schemas import schemas
from app.core import auth
from app.core.config import settings
from app.engine.analysis_engine import BlueprintAnalysisEngine
from app.engine.report_generator import BlueprintReportGenerator

router = APIRouter(prefix="/blueprints", tags=["Blueprints"])

# Background Task for processing blueprints
def analyze_blueprint_task(blueprint_id: int):
    db = SessionLocal()
    try:
        # Load blueprint
        blueprint = db.query(models.Blueprint).filter(models.Blueprint.id == blueprint_id).first()
        if not blueprint:
            print(f"Blueprint {blueprint_id} not found in background task.")
            return

        blueprint.status = "processing"
        db.commit()

        # Load current active compliance rules
        rules = db.query(models.ComplianceRule).all()
        rules_dict = {r.rule_key: r.current_value for r in rules}

        # Analyze
        engine = BlueprintAnalysisEngine(
            upload_dir=str(settings.UPLOAD_DIR),
            models_dir=str(settings.MODELS_DIR)
        )
        
        analysis_result = engine.run_analysis(blueprint.file_path, rules_dict)

        # Create or update AnalysisResult row
        res_row = db.query(models.AnalysisResult).filter(models.AnalysisResult.blueprint_id == blueprint_id).first()
        if not res_row:
            res_row = models.AnalysisResult(
                blueprint_id=blueprint_id,
                compliance_score=analysis_result["compliance_score"],
                total_errors=analysis_result["total_errors"],
                total_violations=analysis_result["total_violations"],
                raw_json=json.dumps(analysis_result)
            )
            db.add(res_row)
        else:
            res_row.compliance_score = analysis_result["compliance_score"]
            res_row.total_errors = analysis_result["total_errors"]
            res_row.total_violations = analysis_result["total_violations"]
            res_row.raw_json = json.dumps(analysis_result)
            
        db.commit()

        # Generate PDF Report
        report_generator = BlueprintReportGenerator(reports_dir=str(settings.REPORTS_DIR))
        report_filename = f"report_{blueprint.id}_{uuid.uuid4().hex[:8]}.pdf"
        report_path = os.path.join(str(settings.REPORTS_DIR), report_filename)
        
        report_generator.generate_pdf(
            blueprint_name=blueprint.original_name,
            analysis_results=analysis_result,
            output_path=report_path
        )

        # Register report in DB
        # Delete old reports if any exist (e.g. on re-run)
        db.query(models.Report).filter(models.Report.blueprint_id == blueprint_id).delete()
        
        report_row = models.Report(
            blueprint_id=blueprint_id,
            filename=report_filename,
            file_path=report_path
        )
        db.add(report_row)
        
        # Complete
        blueprint.status = "completed"
        blueprint.error_message = None
        db.commit()
        print(f"Background analysis completed for blueprint ID: {blueprint_id}")

    except Exception as e:
        db.rollback()
        # Set blueprint status as failed
        blueprint = db.query(models.Blueprint).filter(models.Blueprint.id == blueprint_id).first()
        if blueprint:
            blueprint.status = "failed"
            blueprint.error_message = str(e)
            db.commit()
        print(f"Error in background task for blueprint {blueprint_id}: {e}")
    finally:
        db.close()


@router.post("/upload", response_model=schemas.BlueprintUploadResponse)
def upload_blueprint(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    # Validate extension
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in [".png", ".jpg", ".jpeg", ".pdf"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid file format. Only JPG, PNG, and PDF blueprints are supported."
        )

    # Ensure upload path exists
    settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    # Save file
    file_id = uuid.uuid4().hex
    safe_filename = f"{file_id}{ext}"
    dest_path = settings.UPLOAD_DIR / safe_filename

    try:
        with open(dest_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not save file: {e}")

    # File size
    file_size = os.path.getsize(dest_path)

    # Create Blueprint record
    db_blueprint = models.Blueprint(
        filename=safe_filename,
        original_name=file.filename,
        file_path=str(dest_path),
        file_size=file_size,
        content_type=file.content_type or "application/octet-stream",
        owner_id=current_user.id,
        status="pending"
    )
    db.add(db_blueprint)
    db.commit()
    db.refresh(db_blueprint)

    # Queue background analysis task
    background_tasks.add_task(analyze_blueprint_task, db_blueprint.id)

    return {
        "success": True,
        "filename": db_blueprint.filename,
        "id": db_blueprint.id,
        "message": "Blueprint uploaded successfully."
    }


@router.get("/", response_model=List[schemas.BlueprintResponse])
def list_blueprints(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    return db.query(models.Blueprint).filter(
        models.Blueprint.owner_id == current_user.id
    ).order_by(models.Blueprint.created_at.desc()).all()


@router.get("/{blueprint_id}", response_model=schemas.BlueprintDetailResponse)
def get_blueprint(
    blueprint_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    blueprint = db.query(models.Blueprint).options(
        joinedload(models.Blueprint.analysis_results),
        joinedload(models.Blueprint.reports)
    ).filter(
        models.Blueprint.id == blueprint_id,
        models.Blueprint.owner_id == current_user.id
    ).first()
    
    if not blueprint:
        raise HTTPException(status_code=404, detail="Blueprint not found.")
    return blueprint


@router.post("/{blueprint_id}/analyze", response_model=schemas.BlueprintResponse)
def trigger_analysis(
    blueprint_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    blueprint = db.query(models.Blueprint).filter(
        models.Blueprint.id == blueprint_id,
        models.Blueprint.owner_id == current_user.id
    ).first()
    
    if not blueprint:
        raise HTTPException(status_code=404, detail="Blueprint not found.")
        
    blueprint.status = "pending"
    db.commit()
    
    background_tasks.add_task(analyze_blueprint_task, blueprint.id)
    return blueprint


@router.get("/{blueprint_id}/report", response_class=FileResponse)
def download_report(
    blueprint_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    blueprint = db.query(models.Blueprint).filter(
        models.Blueprint.id == blueprint_id,
        models.Blueprint.owner_id == current_user.id
    ).first()
    
    if not blueprint:
        raise HTTPException(status_code=404, detail="Blueprint not found.")
        
    report = db.query(models.Report).filter(models.Report.blueprint_id == blueprint_id).first()
    if not report or not os.path.exists(report.file_path):
        raise HTTPException(status_code=404, detail="Report PDF not found. Ensure analysis is completed.")
        
    return FileResponse(
        report.file_path,
        media_type="application/pdf",
        filename=f"Report_{blueprint.original_name.replace(' ', '_')}.pdf"
    )

@router.get("/{blueprint_id}/image")
def view_blueprint_image(
    blueprint_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    blueprint = db.query(models.Blueprint).filter(
        models.Blueprint.id == blueprint_id,
        models.Blueprint.owner_id == current_user.id
    ).first()
    
    if not blueprint or not os.path.exists(blueprint.file_path):
        raise HTTPException(status_code=404, detail="Blueprint image file not found.")
        
    return FileResponse(blueprint.file_path, media_type=blueprint.content_type)
