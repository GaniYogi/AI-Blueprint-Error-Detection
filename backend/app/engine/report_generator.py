import os
import datetime
from typing import Dict, Any
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

class BlueprintReportGenerator:
    def __init__(self, reports_dir: str):
        self.reports_dir = reports_dir
        os.makedirs(reports_dir, exist_ok=True)

    def generate_pdf(self, blueprint_name: str, analysis_results: Dict[str, Any], output_path: str) -> str:
        """
        Generates a professional architectural compliance and error analysis PDF report.
        """
        doc = SimpleDocTemplate(
            output_path,
            pagesize=letter,
            rightMargin=54,
            leftMargin=54,
            topMargin=54,
            bottomMargin=54
        )

        styles = getSampleStyleSheet()
        
        # Define Custom Styles
        primary_color = colors.HexColor("#1e293b")  # Dark Slate
        accent_color = colors.HexColor("#4f46e5")   # Indigo
        success_color = colors.HexColor("#10b981")  # Emerald
        warning_color = colors.HexColor("#f59e0b")  # Amber
        error_color = colors.HexColor("#f43f5e")    # Rose
        light_bg = colors.HexColor("#f8fafc")       # Slate 50
        
        title_style = ParagraphStyle(
            'CoverTitle',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=28,
            leading=34,
            textColor=primary_color,
            spaceAfter=15
        )
        
        subtitle_style = ParagraphStyle(
            'CoverSubtitle',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=14,
            leading=18,
            textColor=colors.HexColor("#64748b"),
            spaceAfter=40
        )
        
        h1_style = ParagraphStyle(
            'Heading1_Custom',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=20,
            leading=24,
            textColor=primary_color,
            spaceAfter=15,
            spaceBefore=15,
            keepWithNext=True
        )

        h2_style = ParagraphStyle(
            'Heading2_Custom',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=14,
            leading=18,
            textColor=accent_color,
            spaceAfter=10,
            spaceBefore=10,
            keepWithNext=True
        )

        body_style = ParagraphStyle(
            'Body_Custom',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=10,
            leading=14,
            textColor=colors.HexColor("#334155"),
            spaceAfter=8
        )
        
        body_bold = ParagraphStyle(
            'Body_Bold_Custom',
            parent=body_style,
            fontName='Helvetica-Bold'
        )

        meta_label_style = ParagraphStyle(
            'MetaLabel',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=10,
            leading=14,
            textColor=primary_color
        )

        meta_val_style = ParagraphStyle(
            'MetaValue',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=10,
            leading=14,
            textColor=colors.HexColor("#475569")
        )

        story = []

        # ----------------------------------------------------
        # COVER PAGE
        # ----------------------------------------------------
        # Decorative top bar
        bar_data = [['']]
        bar_table = Table(bar_data, colWidths=[504], rowHeights=[6])
        bar_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), accent_color),
            ('TOPPADDING', (0,0), (-1,-1), 0),
            ('BOTTOMPADDING', (0,0), (-1,-1), 0),
        ]))
        story.append(bar_table)
        story.append(Spacer(1, 40))
        
        story.append(Paragraph("AI BLUEPRINT ERROR DETECTION", title_style))
        story.append(Paragraph("Architectural & Code Compliance Analysis Report", subtitle_style))
        
        story.append(Spacer(1, 50))
        
        # Summary Card (Visual Callout)
        score = analysis_results.get("compliance_score", 100.0)
        risk = analysis_results.get("risk_assessment", "Unknown")
        total_errors = analysis_results.get("total_errors", 0)
        total_violations = analysis_results.get("total_violations", 0)
        
        score_color = success_color if score >= 85 else (warning_color if score >= 70 else error_color)
        
        summary_card_data = [
            [
                Paragraph("COMPLIANCE SCORE", ParagraphStyle('CardLbl1', parent=body_bold, textColor=colors.HexColor("#64748b"), fontSize=9, alignment=1)),
                Paragraph("TOTAL ERRORS", ParagraphStyle('CardLbl2', parent=body_bold, textColor=colors.HexColor("#64748b"), fontSize=9, alignment=1)),
                Paragraph("BUILDING CODE VIOLATIONS", ParagraphStyle('CardLbl3', parent=body_bold, textColor=colors.HexColor("#64748b"), fontSize=9, alignment=1))
            ],
            [
                Paragraph(f"{score}%", ParagraphStyle('CardVal1', parent=body_bold, textColor=score_color, fontSize=28, alignment=1)),
                Paragraph(str(total_errors), ParagraphStyle('CardVal2', parent=body_bold, textColor=primary_color, fontSize=28, alignment=1)),
                Paragraph(str(total_violations), ParagraphStyle('CardVal3', parent=body_bold, textColor=error_color, fontSize=28, alignment=1))
            ],
            [
                Paragraph(f"Risk Rating: <b>{risk}</b>", ParagraphStyle('CardSub1', parent=body_style, textColor=colors.HexColor("#475569"), fontSize=10, alignment=1)),
                Paragraph("Detected structural issues", ParagraphStyle('CardSub2', parent=body_style, textColor=colors.HexColor("#475569"), fontSize=10, alignment=1)),
                Paragraph("Regulatory failures", ParagraphStyle('CardSub3', parent=body_style, textColor=colors.HexColor("#475569"), fontSize=10, alignment=1))
            ]
        ]
        
        summary_table = Table(summary_card_data, colWidths=[168, 168, 168])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), light_bg),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#e2e8f0")),
            ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
            ('TOPPADDING', (0,0), (-1,-1), 15),
            ('BOTTOMPADDING', (0,0), (-1,-1), 15),
        ]))
        story.append(summary_table)
        
        story.append(Spacer(1, 80))
        
        # Document Metadata block
        meta_data = [
            [Paragraph("Blueprint Name:", meta_label_style), Paragraph(blueprint_name, meta_val_style)],
            [Paragraph("Analysis Date:", meta_label_style), Paragraph(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), meta_val_style)],
            [Paragraph("AI System Version:", meta_label_style), Paragraph("BlueprintAI v1.2 (YOLOv8 + EasyOCR)", meta_val_style)],
            [Paragraph("Report ID:", meta_label_style), Paragraph(os.path.basename(output_path).replace(".pdf", ""), meta_val_style)]
        ]
        meta_table = Table(meta_data, colWidths=[120, 384])
        meta_table.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ]))
        story.append(meta_table)
        
        story.append(PageBreak())

        # ----------------------------------------------------
        # EXECUTIVE SUMMARY & OBJECTS
        # ----------------------------------------------------
        story.append(Paragraph("1. Executive Summary", h1_style))
        story.append(Paragraph(
            "This document presents a comprehensive code compliance audit and design error detection report compiled by the "
            "AI Blueprint Error Detection engine. The uploaded design file has been analyzed for geometric, structural, and "
            "regulatory errors using advanced computer vision networks and automated rule checks.",
            body_style
        ))
        
        # Basic list of detected objects
        story.append(Paragraph("Objects Identified on Plan", h2_style))
        story.append(Paragraph(
            "The computer vision model scanned the blueprint and mapped the following architectural components:",
            body_style
        ))
        
        detected_objs = analysis_results.get("detected_objects", [])
        # Count objects by label
        counts = {}
        for obj in detected_objs:
            lbl = obj.get("label", "Unknown").capitalize()
            counts[lbl] = counts.get(lbl, 0) + 1
            
        obj_table_data = [[Paragraph("<b>Component</b>", body_style), Paragraph("<b>Count Detected</b>", body_style)]]
        for lbl, count in sorted(counts.items()):
            obj_table_data.append([Paragraph(lbl, body_style), Paragraph(str(count), body_style)])
            
        if len(obj_table_data) == 1:
            obj_table_data.append([Paragraph("No objects detected", body_style), Paragraph("0", body_style)])
            
        obj_table = Table(obj_table_data, colWidths=[252, 252])
        obj_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#e2e8f0")),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
            ('TOPPADDING', (0,0), (-1,-1), 6),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
        ]))
        story.append(obj_table)
        
        story.append(Spacer(1, 20))

        # ----------------------------------------------------
        # ERRORS & WARNINGS SECTION
        # ----------------------------------------------------
        story.append(Paragraph("2. Design & Layout Errors", h1_style))
        story.append(Paragraph(
            "The following architectural discrepancies, geometric conflicts, and layout issues were flagged:",
            body_style
        ))
        
        errors_list = analysis_results.get("errors", [])
        err_table_data = [[
            Paragraph("<b>ID</b>", body_style),
            Paragraph("<b>Error Type</b>", body_style),
            Paragraph("<b>Description</b>", body_style),
            Paragraph("<b>Severity</b>", body_style)
        ]]
        
        for err in errors_list:
            sev = err.get("severity", "Medium")
            sev_color = error_color if sev in ["Critical", "High"] else (warning_color if sev == "Medium" else accent_color)
            err_table_data.append([
                Paragraph(err.get("id", "N/A"), body_style),
                Paragraph(err.get("type", "Unknown").replace("_", " ").capitalize(), body_style),
                Paragraph(err.get("description", ""), body_style),
                Paragraph(f"<font color='{sev_color.hexval()}'><b>{sev}</b></font>", body_style)
            ])
            
        if len(err_table_data) == 1:
            err_table_data.append([Paragraph("-", body_style), Paragraph("None", body_style), Paragraph("No errors detected on this plan.", body_style), Paragraph("N/A", body_style)])
            
        err_table = Table(err_table_data, colWidths=[40, 100, 280, 84])
        err_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#e2e8f0")),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('BOTTOMPADDING', (0,0), (-1,-1), 8),
            ('TOPPADDING', (0,0), (-1,-1), 8),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
        ]))
        story.append(err_table)
        
        story.append(PageBreak())

        # ----------------------------------------------------
        # CODE COMPLIANCE AUDIT
        # ----------------------------------------------------
        story.append(Paragraph("3. Building Code Compliance Audit", h1_style))
        story.append(Paragraph(
            "The building rules engine tested the layout dimensions and spatial ratios against regional residential building code standards:",
            body_style
        ))
        
        checks_list = analysis_results.get("compliance_checks", [])
        chk_table_data = [[
            Paragraph("<b>Rule</b>", body_style),
            Paragraph("<b>Category</b>", body_style),
            Paragraph("<b>Threshold</b>", body_style),
            Paragraph("<b>Actual</b>", body_style),
            Paragraph("<b>Status</b>", body_style)
        ]]
        
        for chk in checks_list:
            status_txt = chk.get("status", "PASS")
            status_color = success_color if status_txt == "PASS" else error_color
            
            chk_table_data.append([
                Paragraph(f"<b>{chk.get('name', 'Rule')}</b><br/><font color='#64748b' size='8'>{chk.get('description', '')}</font>", body_style),
                Paragraph(chk.get("category", "General").capitalize(), body_style),
                Paragraph(chk.get("threshold", ""), body_style),
                Paragraph(chk.get("actual", ""), body_style),
                Paragraph(f"<font color='{status_color.hexval()}'><b>{status_txt}</b></font>", body_style)
            ])
            
        chk_table = Table(chk_table_data, colWidths=[164, 80, 80, 110, 70])
        chk_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#e2e8f0")),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('BOTTOMPADDING', (0,0), (-1,-1), 8),
            ('TOPPADDING', (0,0), (-1,-1), 8),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
        ]))
        story.append(chk_table)
        
        story.append(Spacer(1, 20))

        # ----------------------------------------------------
        # RECOMMENDATIONS
        # ----------------------------------------------------
        story.append(KeepTogether([
            Paragraph("4. Key Recommendations", h1_style),
            Paragraph(
                "Based on the detected violations and layout errors, we recommend carrying out the following corrective actions:",
                body_style
            )
        ]))
        
        recs = analysis_results.get("recommendations", [])
        for idx, rec in enumerate(recs):
            story.append(Paragraph(f"<b>{idx + 1}.</b> {rec}", body_style))
            
        story.append(Spacer(1, 40))
        
        # Sign-off Block
        sign_off_data = [
            [Paragraph("<b>Prepared by:</b>", body_style), Paragraph("<b>Approved by:</b>", body_style)],
            [Paragraph("AI Blueprint Compliance Engine (Auto-Generated)", body_style), Paragraph("_______________________________", body_style)],
            [Paragraph("BlueprintAI Systems Inc.", body_style), Paragraph("Licensed Professional Architect / Engineer", body_style)]
        ]
        sign_off_table = Table(sign_off_data, colWidths=[252, 252])
        sign_off_table.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('TOPPADDING', (0,0), (-1,-1), 2),
            ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ]))
        
        story.append(KeepTogether([sign_off_table]))

        # Build Document
        doc.build(story)
        return output_path
