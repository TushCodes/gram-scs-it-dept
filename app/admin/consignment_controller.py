import io
import logging
import re

from flask import flash, jsonify, redirect, render_template, request, send_file, url_for
from openpyxl import Workbook, load_workbook
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from sqlalchemy.exc import DatabaseError, IntegrityError, OperationalError

from app import limiter
from app.admin import admin_bp
from app.admin.auth import require_admin
from app.models import Consignment, db
from app.services.logistics import (
    normalize_consignment_number,
    normalize_indian_pincode,
    normalize_status,
)

logger = logging.getLogger(__name__)


@admin_bp.route("/admin/consignments", methods=["GET"], endpoint="consignments_panel")
@require_admin
def consignments_panel():
    try:
        consignments = Consignment.query.order_by(Consignment.id.asc()).all()
        rows = [
            {
                "id": c.id,
                "consignment_number": c.consignment_number,
                "status": c.status,
                "pickup_pincode": c.pickup_pincode,
                "drop_pincode": c.drop_pincode,
                "eta": c.eta,
            }
            for c in consignments
        ]
        return render_template(
            "admin/consignments.html",
            consignments=rows,
        )
    except (OperationalError, DatabaseError):
        logger.exception("Database error loading admin panel")
        return render_template(
            "admin/consignments.html",
            consignments=[],
            error="Unable to load data. Please try again.",
        )
    except Exception:
        logger.exception("Unexpected error in admin panel")
        return render_template(
            "admin/consignments.html",
            consignments=[],
            error="An unexpected error occurred.",
        )


def _normalize_header(value):
    return re.sub(r"[^a-z0-9]+", "_", str(value or "").strip().lower()).strip("_")


@admin_bp.route("/admin/consignments/save", methods=["POST"], endpoint="consignments_save")
@limiter.limit("25 per minute")
@require_admin
def consignments_save():
    payload = request.get_json(silent=True) or {}
    rows = payload.get("rows", [])
    deleted_ids = payload.get("deleted_ids", [])

    if not isinstance(rows, list) or not isinstance(deleted_ids, list):
        return jsonify({"success": False, "message": "Invalid request payload."}), 400

    try:
        existing = {c.id: c for c in Consignment.query.all()}
        validated_deleted_ids = set()

        for raw_deleted_id in deleted_ids:
            try:
                deleted_id = int(raw_deleted_id)
            except (TypeError, ValueError):
                return jsonify({"success": False, "message": f"Invalid deleted row id: {raw_deleted_id}"}), 400

            if deleted_id not in existing:
                return jsonify({"success": False, "message": f"Deleted row id {deleted_id} not found."}), 400

            validated_deleted_ids.add(deleted_id)

        seen_numbers = set()
        validated_rows = []

        for row in rows:
            row_id = row.get("id")
            try:
                consignment_number = normalize_consignment_number(row.get("consignment_number"))
                status = normalize_status(row.get("status"))
                pickup_pincode = normalize_indian_pincode(row.get("pickup_pincode"), "pickup_pincode")
                drop_pincode = normalize_indian_pincode(row.get("drop_pincode"), "drop_pincode")
            except ValueError as error:
                return jsonify({"success": False, "message": str(error)}), 400

            eta = str(row.get("eta") or "").strip()

            if consignment_number in seen_numbers:
                return jsonify({
                    "success": False,
                    "message": f"Duplicate consignment number in sheet: {consignment_number}"
                }), 400
            seen_numbers.add(consignment_number)

            if row_id:
                try:
                    row_id = int(row_id)
                except (TypeError, ValueError):
                    return jsonify({"success": False, "message": f"Invalid row id: {row_id}"}), 400

                if row_id not in existing:
                    return jsonify({"success": False, "message": f"Row id {row_id} not found."}), 400

                if row_id in validated_deleted_ids:
                    return jsonify({
                        "success": False,
                        "message": f"Row id {row_id} cannot be updated and deleted in the same save."
                    }), 400
            else:
                row_id = None

            validated_rows.append({
                "id": row_id,
                "consignment_number": consignment_number,
                "status": status,
                "pickup_pincode": pickup_pincode,
                "drop_pincode": drop_pincode,
                "eta": eta,
            })

        for deleted_id in validated_deleted_ids:
            db.session.delete(existing[deleted_id])

        for row in validated_rows:
            if row["id"]:
                consignment = existing[row["id"]]
            else:
                consignment = Consignment()
                db.session.add(consignment)

            consignment.consignment_number = row["consignment_number"]
            consignment.status = row["status"]
            consignment.pickup_pincode = row["pickup_pincode"]
            consignment.drop_pincode = row["drop_pincode"]
            consignment.eta = row["eta"]

        db.session.commit()
        return jsonify({
            "success": True,
            "message": "Sheet saved successfully.",
            "deleted_count": len(validated_deleted_ids),
        })

    except IntegrityError:
        db.session.rollback()
        logger.exception("Integrity error in admin save")
        return jsonify({"success": False, "message": "Duplicate consignment number already exists."}), 400
    except (OperationalError, DatabaseError):
        db.session.rollback()
        logger.exception("Database error in admin save")
        return jsonify({"success": False, "message": "Database connection error. Please try again."}), 500
    except ValueError as error:
        db.session.rollback()
        logger.exception("Validation error in admin save")
        return jsonify({"success": False, "message": str(error)}), 400
    except Exception:
        db.session.rollback()
        logger.exception("Unexpected error in admin save")
        return jsonify({"success": False, "message": "An unexpected error occurred. Please try again."}), 500


@admin_bp.route("/admin/consignments/import", methods=["POST"], endpoint="consignments_import_excel")
@limiter.limit("10 per minute")
@require_admin
def consignments_import_excel():
    upload = request.files.get("file")
    if not upload or not upload.filename:
        flash("Please choose an Excel file (.xlsx).", "danger")
        return redirect(url_for("admin.consignments_panel"))

    filename = upload.filename.lower()
    if not filename.endswith(".xlsx"):
        flash("Only .xlsx files are supported.", "danger")
        return redirect(url_for("admin.consignments_panel"))

    try:
        workbook = load_workbook(upload, data_only=True)
        sheet = workbook.active

        header_cells = next(sheet.iter_rows(min_row=1, max_row=1, values_only=True), None)
        if not header_cells:
            flash("Excel file is empty.", "danger")
            return redirect(url_for("admin.consignments_panel"))

        normalized_headers = [_normalize_header(cell) for cell in header_cells]
        header_index = {name: idx for idx, name in enumerate(normalized_headers) if name}

        consignment_idx = header_index.get("consignment_number")
        status_idx = header_index.get("status")
        pickup_idx = header_index.get("pickup_pincode")
        drop_idx = header_index.get("drop_pincode")
        eta_idx = header_index.get("eta")

        if None in (consignment_idx, status_idx, pickup_idx, drop_idx):
            flash("Required headers: consignment_number, status, pickup_pincode, drop_pincode", "danger")
            return redirect(url_for("admin.consignments_panel"))

        existing_numbers = {c.consignment_number for c in Consignment.query.with_entities(Consignment.consignment_number).all()}
        file_seen = set()
        added_count = 0
        skipped_count = 0

        for row in sheet.iter_rows(min_row=2, values_only=True):
            if not row or all(value is None or str(value).strip() == "" for value in row):
                continue

            consignment_number = normalize_consignment_number(row[consignment_idx])
            status = normalize_status(row[status_idx])
            pickup_pincode = normalize_indian_pincode(row[pickup_idx], "pickup_pincode")
            drop_pincode = normalize_indian_pincode(row[drop_idx], "drop_pincode")
            eta = str(row[eta_idx] if eta_idx is not None and row[eta_idx] is not None else "").strip()

            if consignment_number in existing_numbers or consignment_number in file_seen:
                skipped_count += 1
                continue

            consignment = Consignment(
                consignment_number=consignment_number,
                status=status,
                pickup_pincode=pickup_pincode,
                drop_pincode=drop_pincode,
                eta=eta,
            )

            db.session.add(consignment)
            file_seen.add(consignment_number)
            existing_numbers.add(consignment_number)
            added_count += 1

        db.session.commit()
        flash(f"Import completed. Added: {added_count}, skipped duplicates: {skipped_count}.", "success")
        return redirect(url_for("admin.consignments_panel"))
    except ValueError as error:
        db.session.rollback()
        flash(str(error), "danger")
        return redirect(url_for("admin.consignments_panel"))
    except Exception:
        db.session.rollback()
        logger.exception("Unexpected error in Excel import")
        flash("Failed to import Excel file.", "danger")
        return redirect(url_for("admin.consignments_panel"))


@admin_bp.route("/admin/consignments/export.xlsx", methods=["GET"], endpoint="consignments_export_excel")
@require_admin
def consignments_export_excel():
    try:
        rows = Consignment.query.order_by(Consignment.id.asc()).all()

        workbook = Workbook()
        sheet = workbook.active
        sheet.title = "Internal Consignments"

        sheet.append([
            "id",
            "consignment_number",
            "status",
            "pickup_pincode",
            "drop_pincode",
            "eta",
        ])

        for row in rows:
            sheet.append([
                row.id,
                row.consignment_number,
                row.status,
                row.pickup_pincode,
                row.drop_pincode,
                row.eta,
            ])

        output = io.BytesIO()
        workbook.save(output)
        output.seek(0)

        return send_file(
            output,
            as_attachment=True,
            download_name="internal_consignments.xlsx",
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    except Exception:
        logger.exception("Excel export failed")
        return jsonify({"success": False, "message": "Failed to export Excel."}), 500


@admin_bp.route("/admin/consignments/export.pdf", methods=["GET"], endpoint="consignments_export_pdf")
@require_admin
def consignments_export_pdf():
    try:
        rows = Consignment.query.order_by(Consignment.id.asc()).all()

        output = io.BytesIO()
        doc = SimpleDocTemplate(output, pagesize=landscape(A4), leftMargin=24, rightMargin=24, topMargin=24, bottomMargin=24)
        styles = getSampleStyleSheet()

        table_data = [["ID", "Consignment #", "Status", "Pickup", "Drop", "ETA"]]
        for row in rows:
            table_data.append([
                str(row.id),
                row.consignment_number or "",
                row.status or "",
                row.pickup_pincode or "",
                row.drop_pincode or "",
                row.eta or "",
            ])

        table = Table(table_data, repeatRows=1)
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E9ECEF")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#6C757D")),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]))

        content = [
            Paragraph("Internal Consignment Sheet", styles["Heading2"]),
            Spacer(1, 8),
            table,
        ]

        doc.build(content)
        output.seek(0)

        return send_file(
            output,
            as_attachment=True,
            download_name="internal_consignments.pdf",
            mimetype="application/pdf",
        )
    except Exception:
        logger.exception("PDF export failed")
        return jsonify({"success": False, "message": "Failed to export PDF."}), 500


@admin_bp.route("/admin/consignments/import-template.xlsx", methods=["GET"], endpoint="consignments_import_template_excel")
@require_admin
def consignments_import_template_excel():
    try:
        workbook = Workbook()
        sheet = workbook.active
        sheet.title = "Import Template"

        sheet.append([
            "consignment_number",
            "status",
            "pickup_pincode",
            "drop_pincode",
            "eta",
        ])

        sheet.append([
            "CN001",
            "In Transit",
            "110017",
            "400001",
            "2-3 days",
        ])

        output = io.BytesIO()
        workbook.save(output)
        output.seek(0)

        return send_file(
            output,
            as_attachment=True,
            download_name="internal_consignments_import_template.xlsx",
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    except Exception:
        logger.exception("Template export failed")
        return jsonify({"success": False, "message": "Failed to generate import template."}), 500
