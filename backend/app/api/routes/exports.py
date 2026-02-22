"""Export API - PDF and CSV."""
from io import BytesIO, StringIO
from datetime import date, timedelta

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import csv

from app.api.deps import get_current_user
from app.database import get_db
from app.models.organization import Organization, Property
from app.models.user import User
from app.models.engine import EngineRun, Recommendation

router = APIRouter(prefix="/exports", tags=["exports"])


@router.get("/billing.csv")
async def export_billing_csv(
    property_id: str | None = None,
    year: int = Query(..., ge=2020, le=2030),
    month: int = Query(..., ge=1, le=12),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """CSV export for billing invoice."""
    from app.api.routes.billing import get_invoice

    invoice = await get_invoice(
        property_id=property_id,
        year=year,
        month=month,
        db=db,
        current_user=current_user,
    )
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "property_id", "property_name", "base_fee", "realized_lift", "gop_lift",
        "revenue_share_pct", "revenue_share_on_gop", "revenue_share_amount", "total",
    ])
    for item in invoice.get("items", []):
        writer.writerow([
            item["property_id"],
            item["property_name"],
            item["base_fee"],
            item["realized_lift"],
            item["gop_lift"],
            item["revenue_share_pct"],
            item["revenue_share_on_gop"],
            item["revenue_share_amount"],
            item["total"],
        ])
    writer.writerow([])
    writer.writerow(["total_base_fee", invoice.get("total_base_fee", 0)])
    writer.writerow(["total_revenue_share", invoice.get("total_revenue_share", 0)])
    writer.writerow(["grand_total", invoice.get("grand_total", 0)])
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=billing_{year}_{month:02d}.csv"},
    )


@router.get("/billing.pdf")
async def export_billing_pdf(
    property_id: str | None = None,
    year: int = Query(..., ge=2020, le=2030),
    month: int = Query(..., ge=1, le=12),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """PDF export for billing invoice and YoY report."""
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet

    from app.api.routes.billing import get_invoice, yoy_report

    invoice = await get_invoice(
        property_id=property_id,
        year=year,
        month=month,
        db=db,
        current_user=current_user,
    )
    today = date.today()
    MONTHS = [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December",
    ]

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=0.6 * inch,
        rightMargin=0.6 * inch,
        topMargin=0.6 * inch,
        bottomMargin=0.6 * inch,
    )
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph("RateMaster Billing Report", styles["Title"]))
    elements.append(Paragraph(
        f"Invoice: {MONTHS[month - 1]} {year} · Generated {today.isoformat()}",
        styles["Normal"],
    ))
    elements.append(Spacer(1, 0.3 * inch))

    # Invoice table
    if invoice.get("items"):
        inv_data = [["Property", "Base Fee", "Realized Lift", "GOP Lift", "Rev Share %", "Rev Share Amt", "Total"]]
        for item in invoice["items"]:
            inv_data.append([
                item["property_name"],
                f"${item['base_fee']:,.2f}",
                f"${item['realized_lift']:,.0f}",
                f"${item['gop_lift']:,.0f}",
                f"{item['revenue_share_pct']}%",
                f"${item['revenue_share_amount']:,.2f}",
                f"${item['total']:,.2f}",
            ])
        inv_data.append([
            "Total", "",
            "",
            "",
            "",
            f"${invoice['total_revenue_share']:,.2f}",
            f"${invoice['grand_total']:,.2f}",
        ])
        t = Table(inv_data)
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#334155")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 10),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
            ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#1e293b")),
            ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
        ]))
        elements.append(t)
    else:
        elements.append(Paragraph("No invoice data for this period.", styles["Normal"]))

    # YoY section (if property selected)
    if property_id:
        try:
            yoy = await yoy_report(property_id=property_id, db=db, current_user=current_user)
            elements.append(Spacer(1, 0.4 * inch))
            elements.append(Paragraph("Year-over-Year Trends", styles["Heading2"]))
            if yoy.get("data_trends"):
                yoy_data = [["Year", "Type", "Revenue", "Rows"]]
                for t in yoy["data_trends"]:
                    yoy_data.append([
                        str(t["year"]),
                        "Prior year" if t["snapshot_type"] == "prior_year" else "Current",
                        f"${t['total_revenue']:,.0f}",
                        str(t["row_count"]),
                    ])
                t2 = Table(yoy_data)
                t2.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#334155")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                ]))
                elements.append(t2)
            if yoy.get("trends"):
                elements.append(Spacer(1, 0.2 * inch))
                elements.append(Paragraph("Applied Recommendations", styles["Normal"]))
                rec_data = [["Year", "Total Lift", "Applied Count"]]
                for t in yoy["trends"]:
                    rec_data.append([t["year"], f"${t['total_lift']:,.0f}", str(t["applied_count"])])
                t3 = Table(rec_data)
                t3.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#334155")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                ]))
                elements.append(t3)
        except Exception:
            pass

    doc.build(elements)
    buffer.seek(0)
    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=billing_report_{year}_{month:02d}.pdf"},
    )


@router.get("/contribution.csv")
async def export_contribution_csv(
    property_id: str | None = None,
    horizon_days: int = Query(30, ge=1, le=90),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """CSV export for finance - contribution report."""
    query = (
        select(
            Recommendation.stay_date,
            Recommendation.suggested_bar,
            Recommendation.current_bar,
            Recommendation.delta_dollars,
            Recommendation.delta_pct,
            Recommendation.applied,
            EngineRun.property_id,
        )
        .join(EngineRun)
        .join(Property)
        .join(Organization)
        .where(Organization.owner_id == current_user.id)
    )
    if property_id:
        query = query.where(EngineRun.property_id == property_id)

    result = await db.execute(query)
    rows = result.all()

    today = date.today()
    horizon = today + timedelta(days=horizon_days)
    filtered = [
        r for r in rows
        if r.stay_date and today <= date.fromisoformat(r.stay_date) <= horizon
    ]

    output = StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "stay_date", "suggested_bar", "current_bar", "delta_dollars",
        "delta_pct", "applied", "property_id", "baseline_methodology"
    ])
    for r in filtered:
        writer.writerow([
            r.stay_date,
            r.suggested_bar,
            r.current_bar,
            r.delta_dollars,
            r.delta_pct,
            r.applied,
            r.property_id,
            "historical_adr_baseline",
        ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=contribution.csv"},
    )


@router.get("/contribution.pdf")
async def export_contribution_pdf(
    property_id: str | None = None,
    horizon_days: int = Query(30, ge=1, le=90),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """PDF monthly performance and contribution report - well structured."""
    from io import BytesIO
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.units import inch
    from reportlab.platypus import (
        SimpleDocTemplate,
        Table,
        TableStyle,
        Paragraph,
        Spacer,
    )
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

    today = date.today()

    # Summary
    from app.api.routes.contribution import contribution_summary, top_wins
    summary = await contribution_summary(
        property_id=property_id,
        horizon_days=horizon_days,
        db=db,
        current_user=current_user,
    )
    wins = await top_wins(
        property_id=property_id,
        limit=10,
        db=db,
        current_user=current_user,
    )

    # Recommendations
    query = (
        select(Recommendation)
        .join(EngineRun)
        .join(Property)
        .join(Organization)
        .where(Organization.owner_id == current_user.id)
    )
    if property_id:
        query = query.where(EngineRun.property_id == property_id)
    query = query.order_by(Recommendation.stay_date).limit(200)
    result = await db.execute(query)
    rows = result.scalars().all()

    prop_name = "All properties"
    if property_id:
        prop_result = await db.execute(select(Property).where(Property.id == property_id))
        prop = prop_result.scalar_one_or_none()
        if prop:
            prop_name = prop.name

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=0.6 * inch,
        rightMargin=0.6 * inch,
        topMargin=0.6 * inch,
        bottomMargin=0.6 * inch,
    )
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name="Section",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=11,
        spaceAfter=6,
    ))
    styles.add(ParagraphStyle(
        name="Meta",
        parent=styles["Normal"],
        fontSize=9,
        textColor=colors.HexColor("#64748b"),
        spaceAfter=16,
    ))
    elements = []

    # Title and meta
    elements.append(Paragraph("RateMaster Contribution Report", styles["Title"]))
    elements.append(Paragraph(
        f"{prop_name} · Generated {today.isoformat()}",
        styles["Meta"],
    ))

    # Summary cards (3 columns)
    summary_data = [
        [
            "Projected Lift (30d)",
            f"${summary.get('projected_lift_30d', 0):,.0f}",
            "vs baseline",
        ],
        [
            "Realized MTD",
            f"${summary.get('realized_lift_mtd', 0):,.0f}",
            "applied",
        ],
        [
            "Est. GOP Lift",
            f"${summary.get('estimated_gop_lift', 0):,.0f}",
            "flow-through",
        ],
    ]
    summary_table = Table(summary_data, colWidths=[2.2 * inch, 1.5 * inch, 1.3 * inch])
    summary_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#1e293b")),
        ("TEXTCOLOR", (0, 0), (0, -1), colors.white),
        ("BACKGROUND", (1, 0), (1, -1), colors.HexColor("#0f172a")),
        ("TEXTCOLOR", (1, 0), (1, -1), colors.HexColor("#22d3ee")),
        ("BACKGROUND", (2, 0), (2, -1), colors.HexColor("#0f172a")),
        ("TEXTCOLOR", (2, 0), (2, -1), colors.HexColor("#94a3b8")),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (0, -1), 9),
        ("FONTSIZE", (1, 0), (1, -1), 12),
        ("FONTSIZE", (2, 0), (2, -1), 8),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#334155")),
        ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#334155")),
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 20))

    # Applied vs Not Applied
    elements.append(Paragraph("Applied vs Not Applied", styles["Section"]))
    applied_count = summary.get("applied_count", 0)
    total_count = summary.get("recommendations_in_horizon", 0)
    elements.append(Paragraph(
        f"{applied_count} applied of {total_count} in horizon.",
        styles["Normal"],
    ))
    elements.append(Spacer(1, 16))

    # Recommendations table
    elements.append(Paragraph("Recommendations", styles["Section"]))
    rec_data = [["Stay Date", "Suggested BAR", "Current", "Delta", "Applied"]]
    for r in rows:
        suggested = f"${float(r.suggested_bar or 0):,.0f}" if r.suggested_bar else "—"
        current = f"${float(r.current_bar or 0):,.0f}" if r.current_bar else "—"
        delta = f"+${float(r.delta_dollars or 0):,.0f}" if r.delta_dollars else "—"
        rec_data.append([
            r.stay_date or "",
            suggested,
            current,
            delta,
            "Yes" if r.applied else "No",
        ])

    if len(rec_data) > 1:
        rec_table = Table(
            rec_data,
            colWidths=[1.1 * inch, 1.2 * inch, 1.1 * inch, 1.1 * inch, 0.9 * inch],
            repeatRows=1,
        )
        rec_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#334155")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 10),
            ("FONTSIZE", (0, 1), (-1, -1), 9),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#475569")),
            ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#475569")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
        ]))
        elements.append(rec_table)
    else:
        elements.append(Paragraph("No recommendations.", styles["Normal"]))
    elements.append(Spacer(1, 20))

    # Top Opportunities
    elements.append(Paragraph("Top Opportunities", styles["Section"]))
    wins_data = [["Stay Date", "Delta", "Status"]]
    for w in wins:
        wins_data.append([
            w["stay_date"],
            f"+${w['delta_dollars']:,.0f}",
            "Applied" if w["applied"] else "Pending",
        ])

    if len(wins_data) > 1:
        wins_table = Table(wins_data, colWidths=[1.5 * inch, 1.5 * inch, 1.5 * inch])
        wins_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#334155")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 10),
            ("FONTSIZE", (0, 1), (-1, -1), 9),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#475569")),
            ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#475569")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
        ]))
        elements.append(wins_table)
    else:
        elements.append(Paragraph("No opportunities.", styles["Normal"]))
    elements.append(Spacer(1, 24))

    # Footer
    elements.append(Paragraph(
        "Baseline methodology: historical ADR baseline. Audit: engine run outputs stored with run_id.",
        styles["Meta"],
    ))

    doc.build(elements)
    buffer.seek(0)

    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=contribution_report.pdf"},
    )


@router.get("/contribution.html")
async def export_contribution_html(
    property_id: str | None = None,
    horizon_days: int = Query(30, ge=1, le=90),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """HTML contribution report - clean, printable structure."""
    from datetime import date as date_type

    today = date_type.today()

    # Summary
    from app.api.routes.contribution import contribution_summary
    summary = await contribution_summary(
        property_id=property_id,
        horizon_days=horizon_days,
        db=db,
        current_user=current_user,
    )

    # Top wins
    from app.api.routes.contribution import top_wins
    wins = await top_wins(
        property_id=property_id,
        limit=10,
        db=db,
        current_user=current_user,
    )

    # Recommendations table
    query = (
        select(Recommendation)
        .join(EngineRun)
        .join(Property)
        .join(Organization)
        .where(Organization.owner_id == current_user.id)
    )
    if property_id:
        query = query.where(EngineRun.property_id == property_id)
    query = query.order_by(Recommendation.stay_date).limit(200)
    result = await db.execute(query)
    rows = result.scalars().all()

    prop_name = "All properties"
    if property_id:
        prop_result = await db.execute(select(Property).where(Property.id == property_id))
        prop = prop_result.scalar_one_or_none()
        if prop:
            prop_name = prop.name

    html = _build_contribution_html(
        summary=summary,
        top_wins=wins,
        rows=rows,
        property_name=prop_name,
        report_date=today.isoformat(),
    )
    return StreamingResponse(
        iter([html]),
        media_type="text/html; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=contribution_report.html"},
    )


def _build_contribution_html(
    summary: dict,
    top_wins: list,
    rows: list,
    property_name: str,
    report_date: str,
) -> str:
    """Build a clean HTML report."""
    rows_html = ""
    for r in rows:
        suggested = f"${float(r.suggested_bar or 0):,.0f}" if r.suggested_bar else "—"
        current = f"${float(r.current_bar or 0):,.0f}" if r.current_bar else "—"
        delta = f"+${float(r.delta_dollars or 0):,.0f}" if r.delta_dollars else "—"
        delta_cell = f'<td class="positive">{delta}</td>' if r.delta_dollars else f"<td>{delta}</td>"
        applied = "Yes" if r.applied else "No"
        rows_html += f"""
        <tr>
            <td>{r.stay_date or ""}</td>
            <td>{suggested}</td>
            <td>{current}</td>
            {delta_cell}
            <td>{applied}</td>
        </tr>"""

    wins_html = ""
    for w in top_wins:
        wins_html += f"""
        <tr>
            <td>{w["stay_date"]}</td>
            <td class="positive">+${w["delta_dollars"]:,.0f}</td>
            <td>{w["applied"] and "Applied" or "Pending"}</td>
        </tr>"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RateMaster Contribution Report</title>
    <style>
        * {{ box-sizing: border-box; }}
        body {{ font-family: system-ui, -apple-system, sans-serif; margin: 0; padding: 2rem; background: #0f172a; color: #e2e8f0; line-height: 1.6; }}
        .container {{ max-width: 900px; margin: 0 auto; }}
        h1 {{ font-size: 1.75rem; color: #22d3ee; margin: 0 0 0.25rem 0; }}
        .meta {{ color: #94a3b8; font-size: 0.875rem; margin-bottom: 2rem; }}
        .summary-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; margin-bottom: 2rem; }}
        .summary-card {{ background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1); border-radius: 0.5rem; padding: 1.25rem; }}
        .summary-card h3 {{ font-size: 0.75rem; color: #94a3b8; font-weight: 500; margin: 0 0 0.5rem 0; text-transform: uppercase; letter-spacing: 0.05em; }}
        .summary-card .value {{ font-size: 1.5rem; font-weight: 700; }}
        .summary-card .value.cyan {{ color: #22d3ee; }}
        .summary-card .value.emerald {{ color: #34d399; }}
        .summary-card .value.violet {{ color: #a78bfa; }}
        section {{ margin-bottom: 2rem; }}
        section h2 {{ font-size: 1rem; color: #94a3b8; font-weight: 600; margin: 0 0 1rem 0; }}
        table {{ width: 100%; border-collapse: collapse; font-size: 0.875rem; }}
        th, td {{ padding: 0.75rem 1rem; text-align: left; border-bottom: 1px solid rgba(255,255,255,0.08); }}
        th {{ color: #94a3b8; font-weight: 500; }}
        td {{ color: #e2e8f0; }}
        .positive {{ color: #34d399; }}
        .footer {{ margin-top: 2rem; padding-top: 1rem; border-top: 1px solid rgba(255,255,255,0.1); font-size: 0.75rem; color: #64748b; }}
        @media print {{ body {{ background: #fff; color: #1e293b; }} .summary-card {{ background: #f8fafc; border-color: #e2e8f0; }} th, td {{ border-color: #e2e8f0; }} th {{ color: #64748b; }} td {{ color: #1e293b; }} .summary-card .value {{ color: inherit; }} .positive {{ color: #059669; }} }}
    </style>
</head>
<body>
    <div class="container">
        <h1>RateMaster Contribution Report</h1>
        <p class="meta">{property_name} · Generated {report_date}</p>

        <div class="summary-grid">
            <div class="summary-card">
                <h3>Projected Lift (30d)</h3>
                <div class="value cyan">${summary.get("projected_lift_30d", 0):,.0f}</div>
                <p class="meta" style="margin:0.25rem 0 0 0;">vs baseline</p>
            </div>
            <div class="summary-card">
                <h3>Realized MTD</h3>
                <div class="value emerald">${summary.get("realized_lift_mtd", 0):,.0f}</div>
                <p class="meta" style="margin:0.25rem 0 0 0;">applied recommendations</p>
            </div>
            <div class="summary-card">
                <h3>Est. GOP Lift</h3>
                <div class="value violet">${summary.get("estimated_gop_lift", 0):,.0f}</div>
                <p class="meta" style="margin:0.25rem 0 0 0;">flow-through applied</p>
            </div>
        </div>

        <section>
            <h2>Applied vs Not Applied</h2>
            <p>{summary.get("applied_count", 0)} applied of {summary.get("recommendations_in_horizon", 0)} in horizon.</p>
        </section>

        <section>
            <h2>Recommendations</h2>
            <table>
                <thead>
                    <tr>
                        <th>Stay Date</th>
                        <th>Suggested BAR</th>
                        <th>Current</th>
                        <th>Delta</th>
                        <th>Applied</th>
                    </tr>
                </thead>
                <tbody>
                    {rows_html or "<tr><td colspan='5'>No recommendations.</td></tr>"}
                </tbody>
            </table>
        </section>

        <section>
            <h2>Top Opportunities</h2>
            <table>
                <thead>
                    <tr>
                        <th>Stay Date</th>
                        <th>Delta</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
                    {wins_html or "<tr><td colspan='3'>No opportunities.</td></tr>"}
                </tbody>
            </table>
        </section>

        <div class="footer">
            Baseline methodology: historical ADR baseline. Audit: engine run outputs stored with run_id.
        </div>
    </div>
</body>
</html>"""
