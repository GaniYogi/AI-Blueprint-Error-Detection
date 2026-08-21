import os
import sys
import json

# Add backend directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def run_verification():
    print("==================================================")
    print("      AI BLUEPRINT SERVICE VERIFICATION SCRIPT    ")
    print("==================================================")
    
    # 1. Test configuration & imports
    print("\n[1/4] Verifying imports and directory structures...")
    try:
      from app.core.config import settings
      from app.db.database import Base, engine, SessionLocal
      from app.db import models
      from app.engine.analysis_engine import BlueprintAnalysisEngine
      from app.engine.report_generator import BlueprintReportGenerator
      print("  -> Configuration loaded successfully.")
      print(f"  -> Upload dir: {settings.UPLOAD_DIR}")
      print(f"  -> Reports dir: {settings.REPORTS_DIR}")
    except Exception as e:
      print(f"  -> ERROR: Import failed: {e}")
      sys.exit(1)
      
    # 2. Test Database Setup
    print("\n[2/4] Verifying database connectivity and migrations...")
    try:
      Base.metadata.create_all(bind=engine)
      db = SessionLocal()
      
      # Populate default rules
      from app.routers.rules import init_default_rules
      init_default_rules(db)
      
      rules_count = db.query(models.ComplianceRule).count()
      print(f"  -> Database tables initialized.")
      print(f"  -> Default compliance rules loaded: {rules_count} items.")
      
      rules_dict = {r.rule_key: r.current_value for r in db.query(models.ComplianceRule).all()}
      db.close()
    except Exception as e:
      print(f"  -> ERROR: Database setup failed: {e}")
      sys.exit(1)

    # 3. Test Blueprint Analysis Engine
    print("\n[3/4] Testing Blueprint Analysis Engine (Mock/Real pipeline)...")
    temp_blueprint_path = os.path.join(settings.UPLOAD_DIR, "test_blueprint.png")
    # Write a valid small image file to mimic blueprint upload
    from PIL import Image as PILImage
    dummy_img = PILImage.new("RGB", (400, 300), color=(255, 255, 255))
    dummy_img.save(temp_blueprint_path, format="PNG")
        
    try:
      engine_runner = BlueprintAnalysisEngine(
          upload_dir=str(settings.UPLOAD_DIR),
          models_dir=str(settings.MODELS_DIR)
      )
      
      analysis = engine_runner.run_analysis(temp_blueprint_path, rules_dict)
      print("  -> Analysis executed successfully.")
      print(f"  -> Compliance Score calculated: {analysis['compliance_score']}%")
      print(f"  -> Total errors detected: {analysis['total_errors']}")
      print(f"  -> Total code violations: {analysis['total_violations']}")
    except Exception as e:
      print(f"  -> ERROR: Blueprint analysis engine failed: {e}")
      if os.path.exists(temp_blueprint_path):
          os.remove(temp_blueprint_path)
      sys.exit(1)

    # 4. Test PDF Report Generation
    print("\n[4/4] Testing PDF Report generation...")
    test_pdf_filename = "test_verification_report.pdf"
    test_pdf_path = os.path.join(settings.REPORTS_DIR, test_pdf_filename)
    try:
      report_gen = BlueprintReportGenerator(reports_dir=str(settings.REPORTS_DIR))
      report_gen.generate_pdf(
          blueprint_name="Verification test layout",
          analysis_results=analysis,
          output_path=test_pdf_path
      )
      print("  -> PDF Report built successfully.")
      print(f"  -> Report path: {test_pdf_path}")
    except Exception as e:
      print(f"  -> ERROR: Report generation failed: {e}")
      if os.path.exists(temp_blueprint_path):
          os.remove(temp_blueprint_path)
      sys.exit(1)

    # Clean up temp file
    if os.path.exists(temp_blueprint_path):
        os.remove(temp_blueprint_path)
        
    print("\n==================================================")
    print("        ALL BACKEND SERVICES ARE OPERATIONAL      ")
    print("==================================================")

if __name__ == "__main__":
    run_verification()
