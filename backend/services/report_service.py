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
        user_name: str,
        predictions: List[Dict],
    ) -> bytes:
        """
        Generate a PDF report of disease predictions.
        """
        try:
            # Generate PDF
            pdf_bytes = self._create_disease_pdf(predictions, user_name)
            return pdf_bytes
        except Exception as e:
            logger.error(f"Failed to generate disease report: {e}")
            raise

    def generate_soil_report(
        self,
        user_id: str,
        user_name: str,
        predictions: List[Dict],
    ) -> bytes:
        """
        Generate a PDF report of soil predictions.
        """
        try:
            # Generate PDF
            pdf_bytes = self._create_soil_pdf(predictions, user_name)
            return pdf_bytes
        except Exception as e:
            logger.error(f"Failed to generate soil report: {e}")
            raise

    def generate_combined_report(
        self,
        user_id: str,
        user_name: str,
        disease_preds: List[Dict],
        soil_preds: List[Dict],
    ) -> bytes:
        """
        Generate a combined PDF report of disease and soil predictions.
        """
        try:
            pdf_bytes = self._create_combined_pdf(disease_preds, soil_preds, user_name)
            return pdf_bytes
        except Exception as e:
            logger.error(f"Failed to generate combined report: {e}")
            raise

    def save_report_record(self, report_id: str, user_id: str, report_type: str, file_url: str) -> Dict[str, Any]:
        report_doc = {
            "report_id": report_id,
            "user_id": user_id,
            "report_type": report_type,
            "title": f"{report_type.capitalize()} Detection Report",
            "file_url": file_url,
            "created_at": utc_now(),
        }
        _report_svc.create(report_id, report_doc)
        return report_doc

    def get_user_reports(self, user_id: str) -> List[Dict[str, Any]]:
        return _report_svc.query("user_id", "==", user_id, order_by="created_at", descending=True)

    def _create_disease_pdf(
        self,
        predictions: List[Dict],
        user_name: str,
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

    def _create_soil_pdf(
        self,
        predictions: List[Dict],
        user_name: str,
    ) -> bytes:
        """
        Create a soil prediction PDF document.
        """
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        story = []
        self._add_soil_story(story, predictions, user_name)
        doc.build(story)
        return buffer.getvalue()

    def _add_soil_story(self, story, predictions, user_name):
        styles = getSampleStyleSheet()
        # Title
        title_style = ParagraphStyle(
            "SoilTitle",
            parent=styles["Heading1"],
            fontSize=24,
            textColor=colors.HexColor("#2563EB"),
            spaceAfter=30,
            alignment=1,
        )
        story.append(Paragraph("💧 AgriCrop Soil Moisture Report", title_style))
        story.append(Spacer(1, 0.3 * inch))

        # Metadata
        story.append(Paragraph(f"Farmer: {user_name}", styles["Normal"]))
        story.append(Paragraph(f"Generated: {utc_now().strftime('%Y-%m-%d %H:%M:%S UTC')}", styles["Normal"]))
        story.append(Spacer(1, 0.3 * inch))

        # Table
        table_data = [["Date", "Soil Type", "Moisture", "Irrigation", "Type"]]
        for p in predictions:
            table_data.append([
                str(p.get("created_at", "N/A"))[:10],
                p.get("soil_type", "N/A"),
                f"{p.get('predicted_moisture', 0):.1f}%",
                "YES" if p.get("irrigation_recommended") else "NO",
                p.get("irrigation_type", "none"),
            ])

        table = Table(table_data, colWidths=[1.5*inch, 1.2*inch, 1.2*inch, 1.2*inch, 1.4*inch])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2563EB")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("GRID", (0, 0), (-1, -1), 1, colors.black),
        ]))
        story.append(table)

    def _create_disease_pdf(
        self,
        predictions: List[Dict],
        user_name: str,
    ) -> bytes:
        """
        Create a disease prediction PDF document.
        """
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        story = []
        self._add_disease_story(story, predictions, user_name)
        doc.build(story)
        return buffer.getvalue()

    def _add_disease_story(self, story, predictions, user_name):
        styles = getSampleStyleSheet()
        # Title
        title_style = ParagraphStyle(
            "DiseaseTitle",
            parent=styles["Heading1"],
            fontSize=24,
            textColor=colors.HexColor("#2E7D32"),
            spaceAfter=30,
            alignment=1,  # Center
        )
        story.append(Paragraph("🌾 AgriCrop Disease Report", title_style))
        story.append(Spacer(1, 0.3 * inch))

        # Report metadata
        story.append(Paragraph(f"Farmer: {user_name}", styles["Normal"]))
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
                str(pred.get("created_at", "N/A"))[:10],
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

    def _create_combined_pdf(
        self,
        disease_preds: List[Dict],
        soil_preds: List[Dict],
        user_name: str,
    ) -> bytes:
        """
        Create a combined prediction PDF document.
        """
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        story = []
        styles = getSampleStyleSheet()

        # Combined Title
        title_style = ParagraphStyle(
            "CombinedTitle",
            parent=styles["Heading1"],
            fontSize=28,
            textColor=colors.HexColor("#1F2937"),
            spaceAfter=40,
            alignment=1,
        )
        story.append(Paragraph("🚜 AgriCrop Complete Farm Report", title_style))
        story.append(Spacer(1, 0.5 * inch))

        self._add_disease_story(story, disease_preds, user_name)
        story.append(PageBreak())
        self._add_soil_story(story, soil_preds, user_name)

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
