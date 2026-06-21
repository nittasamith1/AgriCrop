"""
AgriCrop – Report Service
Generates professional PDF reports for disease predictions, soil moisture,
and combined analytics using ReportLab.
"""

import io
from datetime import datetime
from typing import List, Optional, Dict, Any

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak,
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from loguru import logger

from backend.config import settings
from backend.services.firebase_service import FirestoreService
from backend.services.storage_service import storage_service
from backend.utils.helpers import generate_id, utc_now

_report_svc = FirestoreService(settings.COLLECTION_REPORTS)


class ReportService:
    """
    Generates and stores PDF reports for AgriCrop users.
    """

    # ── Color Palette ─────────────────────────────────────────────────────────
    PRIMARY = colors.HexColor("#1a7c3e")
    SECONDARY = colors.HexColor("#2563eb")
    ACCENT = colors.HexColor("#f59e0b")
    LIGHT_BG = colors.HexColor("#f0fdf4")
    RED = colors.HexColor("#dc2626")
    GREY = colors.HexColor("#6b7280")
    WHITE = colors.white
    BLACK = colors.black

    def _base_styles(self):
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(
            "AgriTitle",
            parent=styles["Title"],
            fontSize=22,
            textColor=self.PRIMARY,
            spaceAfter=6,
            alignment=TA_CENTER,
        ))
        styles.add(ParagraphStyle(
            "SectionHeader",
            parent=styles["Heading2"],
            fontSize=13,
            textColor=self.PRIMARY,
            spaceBefore=12,
            spaceAfter=4,
        ))
        styles.add(ParagraphStyle(
            "BodySmall",
            parent=styles["Normal"],
            fontSize=9,
            textColor=self.GREY,
        ))
        return styles

    def _draw_header(self, canvas, doc):
        """Page header with app name and logo placeholder."""
        canvas.saveState()
        canvas.setFillColor(self.PRIMARY)
        canvas.rect(0, A4[1] - 2 * cm, A4[0], 2 * cm, fill=True, stroke=False)
        canvas.setFillColor(self.WHITE)
        canvas.setFont("Helvetica-Bold", 16)
        canvas.drawString(1 * cm, A4[1] - 1.4 * cm, "🌱 AgriCrop Intelligence Network")
        canvas.setFont("Helvetica", 9)
        canvas.drawRightString(A4[0] - 1 * cm, A4[1] - 1.4 * cm,
                               f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC")
        canvas.restoreState()

    def _draw_footer(self, canvas, doc):
        """Page footer with page number."""
        canvas.saveState()
        canvas.setFillColor(self.GREY)
        canvas.setFont("Helvetica", 8)
        canvas.drawString(1 * cm, 0.7 * cm, "AgriCrop – AI Precision Agriculture Platform")
        canvas.drawRightString(A4[0] - 1 * cm, 0.7 * cm, f"Page {doc.page}")
        canvas.restoreState()

    def generate_disease_report(
        self,
        user_id: str,
        user_name: str,
        predictions: List[Dict[str, Any]],
        report_id: Optional[str] = None,
    ) -> bytes:
        """
        Generate a disease prediction PDF report.
        Returns raw PDF bytes.
        """
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=1.5 * cm,
            leftMargin=1.5 * cm,
            topMargin=3 * cm,
            bottomMargin=2 * cm,
        )
        styles = self._base_styles()
        story = []

        # Title
        story.append(Paragraph("Plant Disease Detection Report", styles["AgriTitle"]))
        story.append(Spacer(1, 0.3 * cm))
        story.append(Paragraph(f"Farmer: <b>{user_name}</b> | User ID: {user_id}", styles["BodySmall"]))
        story.append(HRFlowable(width="100%", thickness=1, color=self.PRIMARY))
        story.append(Spacer(1, 0.5 * cm))

        # Summary table
        story.append(Paragraph("Summary", styles["SectionHeader"]))
        summary_data = [
            ["Total Scans", "Diseased", "Healthy", "Severe Cases"],
            [
                str(len(predictions)),
                str(sum(1 for p in predictions if p.get("disease_name", "") != "Healthy")),
                str(sum(1 for p in predictions if p.get("disease_name", "") == "Healthy")),
                str(sum(1 for p in predictions if p.get("severity") == "severe")),
            ]
        ]
        summary_table = Table(summary_data, colWidths=[4 * cm] * 4)
        summary_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), self.PRIMARY),
            ("TEXTCOLOR", (0, 0), (-1, 0), self.WHITE),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("GRID", (0, 0), (-1, -1), 0.5, self.GREY),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [self.LIGHT_BG, self.WHITE]),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(summary_table)
        story.append(Spacer(1, 0.7 * cm))

        # Detailed prediction records
        story.append(Paragraph("Detailed Prediction Records", styles["SectionHeader"]))
        pred_data = [["Date", "Disease", "Confidence", "Severity", "Crop"]]
        for p in predictions:
            dt = p.get("created_at", "N/A")
            if hasattr(dt, "strftime"):
                dt = dt.strftime("%Y-%m-%d %H:%M")
            pred_data.append([
                str(dt)[:16],
                p.get("disease_name", "Unknown"),
                f"{p.get('confidence', 0) * 100:.1f}%",
                p.get("severity", "N/A").capitalize(),
                p.get("crop_type", "N/A"),
            ])
        pred_table = Table(pred_data, colWidths=[3.5 * cm, 5 * cm, 3 * cm, 3 * cm, 3 * cm])
        pred_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), self.SECONDARY),
            ("TEXTCOLOR", (0, 0), (-1, 0), self.WHITE),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("GRID", (0, 0), (-1, -1), 0.3, self.GREY),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [self.WHITE, self.LIGHT_BG]),
        ]))
        story.append(pred_table)

        doc.build(
            story,
            onFirstPage=lambda c, d: (self._draw_header(c, d), self._draw_footer(c, d)),
            onLaterPages=lambda c, d: (self._draw_header(c, d), self._draw_footer(c, d)),
        )
        return buffer.getvalue()

    def generate_soil_report(
        self,
        user_id: str,
        user_name: str,
        predictions: List[Dict[str, Any]],
    ) -> bytes:
        """Generate a soil moisture prediction PDF report."""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer, pagesize=A4,
            rightMargin=1.5 * cm, leftMargin=1.5 * cm,
            topMargin=3 * cm, bottomMargin=2 * cm,
        )
        styles = self._base_styles()
        story = []

        story.append(Paragraph("Soil Moisture Prediction Report", styles["AgriTitle"]))
        story.append(Spacer(1, 0.3 * cm))
        story.append(Paragraph(f"Farmer: <b>{user_name}</b> | User ID: {user_id}", styles["BodySmall"]))
        story.append(HRFlowable(width="100%", thickness=1, color=self.PRIMARY))
        story.append(Spacer(1, 0.5 * cm))

        story.append(Paragraph("Soil Prediction Records", styles["SectionHeader"]))
        data = [["Date", "Moisture %", "Water Req (mm)", "Irrigation", "Type"]]
        for p in predictions:
            dt = p.get("created_at", "N/A")
            if hasattr(dt, "strftime"):
                dt = dt.strftime("%Y-%m-%d %H:%M")
            data.append([
                str(dt)[:16],
                f"{p.get('predicted_moisture', 0):.1f}%",
                f"{p.get('water_requirement_mm', 0):.1f}",
                "Yes" if p.get("irrigation_recommended") else "No",
                p.get("irrigation_type", "none").capitalize(),
            ])
        table = Table(data, colWidths=[3.5 * cm, 3.5 * cm, 4 * cm, 3 * cm, 4 * cm])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), self.PRIMARY),
            ("TEXTCOLOR", (0, 0), (-1, 0), self.WHITE),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("GRID", (0, 0), (-1, -1), 0.3, self.GREY),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [self.WHITE, self.LIGHT_BG]),
        ]))
        story.append(table)

        doc.build(
            story,
            onFirstPage=lambda c, d: (self._draw_header(c, d), self._draw_footer(c, d)),
            onLaterPages=lambda c, d: (self._draw_header(c, d), self._draw_footer(c, d)),
        )
        return buffer.getvalue()

    def save_report_record(
        self, report_id: str, user_id: str, report_type: str, file_url: str
    ) -> dict:
        """Persist report metadata to Firestore."""
        now = utc_now()
        doc = {
            "report_id": report_id,
            "user_id": user_id,
            "report_type": report_type,
            "file_url": file_url,
            "file_name": f"{report_type}_report_{report_id}.pdf",
            "created_at": now,
        }
        _report_svc.create(report_id, doc)
        return doc

    def get_user_reports(self, user_id: str, limit: int = 20) -> List[dict]:
        return _report_svc.query("user_id", "==", user_id, order_by="created_at", limit=limit)


# Module-level singleton
report_service = ReportService()
