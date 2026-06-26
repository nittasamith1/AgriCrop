"""
AgriCrop – Report Generation Service
Generates PDF and CSV reports of predictions and analytics.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from io import BytesIO
from loguru import logger
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib import colors

from backend.config import settings
from backend.services.firebase_service import FirestoreService
from backend.services.storage_service import storage_service
from backend.utils.helpers import generate_id, utc_now

_report_svc = FirestoreService(settings.COLLECTION_REPORTS)
_disease_svc = FirestoreService(settings.COLLECTION_DISEASE_PREDICTIONS)
_soil_svc = FirestoreService(settings.COLLECTION_SOIL_PREDICTIONS)


class ReportService:
    """Generates and manages PDF/CSV reports."""

    def generate_disease_report(
        self,
        user_id: str,
        prediction_ids: List[str],
    ) -> Dict[str, Any]:
        """
        Generate a PDF report of disease predictions.
        """
        try:
            report_id = generate_id("report")
            now = utc_now()

            # Fetch predictions
            predictions = []
            for pred_id in prediction_ids:
                pred = _disease_svc.get(pred_id)
                if pred:
                    predictions.append(pred)

            if not predictions:
                logger.warning(f"No predictions found for report {report_id}")
                raise ValueError("No predictions found")

            # Generate PDF
            pdf_bytes = self._create_disease_pdf(predictions, user_id)

            # Upload to storage
            filename = f"disease_report_{report_id}.pdf"
            pdf_url = storage_service.upload_report_pdf(pdf_bytes, filename, user_id)

            # Store report metadata
            report_doc = {
                "report_id": report_id,
                "user_id": user_id,
                "report_type": "disease",
                "title": "Disease Detection Report",
                "prediction_ids": prediction_ids,
                "prediction_count": len(predictions),
                "pdf_url": pdf_url,
                "created_at": now,
            }
            _report_svc.create(report_id, report_doc)

            logger.info(f"✅ Disease report generated: {report_id}")
            return report_doc

        except Exception as e:
            logger.error(f"Failed to generate disease report: {e}")
            raise

    def _create_disease_pdf(
        self,
        predictions: List[Dict],
        user_id: str,
    ) -> bytes:
        """
        Create a disease prediction PDF document.
        """
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        story = []
        styles = getSampleStyleSheet()

        # Title
        title_style = ParagraphStyle(
            "CustomTitle",
            parent=styles["Heading1"],
            fontSize=24,
            textColor=colors.HexColor("#2E7D32"),
            spaceAfter=30,
            alignment=1,  # Center
        )
        story.append(Paragraph("🌾 AgriCrop Disease Report", title_style))
        story.append(Spacer(1, 0.3 * inch))

        # Report metadata
        meta_text = f"Generated: {utc_now().strftime('%Y-%m-%d %H:%M:%S UTC')}"
        story.append(Paragraph(meta_text, styles["Normal"]))
        story.append(Spacer(1, 0.3 * inch))

        # Predictions table
        table_data = [
            ["Date", "Disease", "Confidence", "Severity", "Treatment"]
        ]

        for pred in predictions:
            treatments = ", ".join(pred.get("treatments", [])[:1])
            table_data.append([
                pred.get("created_at", "N/A")[:10],
                pred.get("disease_name", "N/A"),
                f"{pred.get('confidence', 0):.1%}",
                pred.get("severity", "N/A"),
                treatments[:30] + "...",
            ])

        table = Table(table_data, colWidths=[1.5*inch, 1.5*inch, 1*inch, 1*inch, 1.5*inch])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2E7D32")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 10),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
            ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
            ("GRID", (0, 0), (-1, -1), 1, colors.black),
        ]))
        story.append(table)

        # Build PDF
        doc.build(story)
        return buffer.getvalue()

    def get_reports(
        self,
        user_id: str,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """
        Get user reports.
        """
        try:
            reports = _report_svc.query(
                "user_id", "==", user_id,
                order_by="created_at",
                descending=True,
                limit=limit,
            )
            return reports
        except Exception as e:
            logger.error(f"Failed to get reports for {user_id}: {e}")
            return []

    def get_report(
        self,
        report_id: str,
        user_id: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Get a specific report (with user access check).
        """
        try:
            report = _report_svc.get(report_id)
            if report and report.get("user_id") == user_id:
                return report
            return None
        except Exception as e:
            logger.error(f"Failed to get report {report_id}: {e}")
            return None


# Singleton instance
report_service = ReportService()
