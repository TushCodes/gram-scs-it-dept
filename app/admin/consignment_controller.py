import io
import logging
import re

from flask import flash, jsonify, redirect, render_template, request, send_file, url_for
from openpyxl import Workbook, load_workbook
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from sqlalchemy.exc import DatabaseError, IntegrityError, OperationalError, ProgrammingError

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


def _is_missing_column_error(error):
    """Return True when the database rejected a query because a column is absent."""
    original = getattr(error, "orig", None)
    if original is None:
        return False

    pgcode = getattr(original, "pgcode", None)
    if pgcode == "42703":
        return True

    return original.__class__.__name__ == "UndefinedColumn"


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
                "pickup_address": getattr(c, "pickup_address", None),
                "pickup_tag": getattr(c, "pickup_tag", None),
                "pickup_date": getattr(c, "pickup_date", None),
                "drop_pincode": c.drop_pincode,
                "drop_address": getattr(c, "drop_address", None),
                "drop_tag": getattr(c, "drop_tag", None),
                "drop_date": getattr(c, "drop_date", None),
                "eta": c.eta,
            }
            for c in consignments
        ]
        return render_template(
            "admin/consignments.html",
            consignments=rows,
        )
    except ProgrammingError as error:
        db.session.rollback()
        if _is_missing_column_error(error):
            logger.exception("Schema mismatch loading admin panel")
            return render_template(
                "admin/consignments.html",
                consignments=[],
                error="Database schema needs an update. Missing consignment fields.",
            )

        logger.exception("Database error loading admin panel")
        return render_template(
            "admin/consignments.html",
            consignments=[],
            error="Unable to load data. Please try again.",
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


@admin_bp.route("/admin/consignments/list", methods=["GET"], endpoint="consignments_list_api")
@require_admin
def consignments_list_api():
    """API endpoint for paginated, searchable, and sortable consignments."""
    try:
        # Get parameters from request
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 10, type=int)
        search = request.args.get("search", "", type=str).strip()
        sort_by = request.args.get("sort_by", "id", type=str)
        sort_order = request.args.get("sort_order", "asc", type=str)

        # Validate pagination parameters
        page = max(1, page)
        per_page = max(1, min(100, per_page))  # Limit to max 100 per page

        # Validate sort parameters
        allowed_sort_columns = {
            "id", "consignment_number", "status", "pickup_pincode",
            "drop_pincode", "pickup_tag", "drop_tag", "pickup_date", "drop_date"
        }
        sort_by = sort_by if sort_by in allowed_sort_columns else "id"
        sort_order = "asc" if sort_order.lower() == "asc" else "desc"

        # Build base query
        query = Consignment.query

        # Apply search filter if provided
        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                db.or_(
                    Consignment.consignment_number.ilike(search_pattern),
                    Consignment.status.ilike(search_pattern),
                    Consignment.pickup_tag.ilike(search_pattern),
                    Consignment.drop_tag.ilike(search_pattern),
                    Consignment.pickup_pincode.ilike(search_pattern),
                    Consignment.drop_pincode.ilike(search_pattern),
                    Consignment.pickup_address.ilike(search_pattern),
                    Consignment.drop_address.ilike(search_pattern),
                )
            )

        # Get total count before pagination
        total = query.count()

        # Apply sorting
        sort_column = getattr(Consignment, sort_by)
        if sort_order == "desc":
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())

        # Apply pagination
        paginated = query.paginate(page=page, per_page=per_page, error_out=False)

        # Serialize results
        rows = [
            {
                "id": c.id,
                "consignment_number": c.consignment_number,
                "status": c.status,
                "pickup_pincode": c.pickup_pincode,
                "pickup_address": getattr(c, "pickup_address", None),
                "pickup_tag": getattr(c, "pickup_tag", None),
                "pickup_date": getattr(c, "pickup_date", None),
                "drop_pincode": c.drop_pincode,
                "drop_address": getattr(c, "drop_address", None),
                "drop_tag": getattr(c, "drop_tag", None),
                "drop_date": getattr(c, "drop_date", None),
                "eta": c.eta,
            }
            for c in paginated.items
        ]

        return jsonify({
            "success": True,
            "rows": rows,
            "page": page,
            "per_page": per_page,
            "total": total,
            "pages": paginated.pages,
            "has_prev": paginated.has_prev,
            "has_next": paginated.has_next,
        })

    except ProgrammingError as error:
        db.session.rollback()
        if _is_missing_column_error(error):
            logger.exception("Schema mismatch in consignments API")
            return jsonify({
                "success": False,
                "error": "Database schema needs an update. Missing consignment fields."
            }), 500

        logger.exception("Database error in consignments API")
        return jsonify({
            "success": False,
            "error": "Unable to load data. Please try again."
        }), 500
    except (OperationalError, DatabaseError):
        db.session.rollback()
        logger.exception("Database error in consignments API")
        return jsonify({
            "success": False,
            "error": "Database connection error. Please try again."
        }), 500
    except Exception as e:
        logger.exception("Unexpected error in consignments API")
        return jsonify({
            "success": False,
            "error": "An unexpected error occurred."
        }), 500


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

            pickup_tag = str(row.get("pickup_tag") or "").strip()
            pickup_date = str(row.get("pickup_date") or "").strip()
            drop_tag = str(row.get("drop_tag") or "").strip()
            drop_date = str(row.get("drop_date") or "").strip()

            validated_rows.append({
                "id": row_id,
                "consignment_number": consignment_number,
                "status": status,
                "pickup_pincode": pickup_pincode,
                "pickup_address": str(row.get("pickup_address") or "").strip(),
                "pickup_tag": pickup_tag,
                "pickup_date": pickup_date,
                "drop_pincode": drop_pincode,
                "drop_address": str(row.get("drop_address") or "").strip(),
                "drop_tag": drop_tag,
                "drop_date": drop_date,
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
            consignment.pickup_address = row.get("pickup_address")
            consignment.pickup_tag = row.get("pickup_tag")
            consignment.pickup_date = row.get("pickup_date")
            consignment.drop_pincode = row["drop_pincode"]
            consignment.drop_address = row.get("drop_address")
            consignment.drop_tag = row.get("drop_tag")
            consignment.drop_date = row.get("drop_date")
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
    except ProgrammingError as error:
        db.session.rollback()
        if _is_missing_column_error(error):
            logger.exception("Schema mismatch in admin save")
            return jsonify({"success": False, "message": "Database schema needs an update. Missing consignment fields."}), 500

        logger.exception("Database error in admin save")
        return jsonify({"success": False, "message": "Database connection error. Please try again."}), 500
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
        pickup_address_idx = header_index.get("pickup_address")
        pickup_pincode_idx = header_index.get("pickup_pincode")
        pickup_tag_idx = header_index.get("pickup_tag")
        pickup_date_idx = header_index.get("pickup_date")
        drop_address_idx = header_index.get("drop_address")
        drop_pincode_idx = header_index.get("drop_pincode")
        drop_tag_idx = header_index.get("drop_tag")
        drop_date_idx = header_index.get("drop_date")
        eta_idx = header_index.get("eta")

        # Required headers: consignment_number and status.
        if None in (consignment_idx, status_idx):
            flash("Required headers: consignment_number, status", "danger")
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
            pickup_address = str(row[pickup_address_idx] if pickup_address_idx is not None and row[pickup_address_idx] is not None else "").strip()
            pickup_pincode = normalize_indian_pincode(row[pickup_pincode_idx] if pickup_pincode_idx is not None and row[pickup_pincode_idx] is not None else "", "pickup_pincode")
            pickup_tag = str(row[pickup_tag_idx] if pickup_tag_idx is not None and row[pickup_tag_idx] is not None else "").strip()
            pickup_date = str(row[pickup_date_idx] if pickup_date_idx is not None and row[pickup_date_idx] is not None else "").strip()
            drop_address = str(row[drop_address_idx] if drop_address_idx is not None and row[drop_address_idx] is not None else "").strip()
            drop_pincode = normalize_indian_pincode(row[drop_pincode_idx] if drop_pincode_idx is not None and row[drop_pincode_idx] is not None else "", "drop_pincode")
            drop_tag = str(row[drop_tag_idx] if drop_tag_idx is not None and row[drop_tag_idx] is not None else "").strip()
            drop_date = str(row[drop_date_idx] if drop_date_idx is not None and row[drop_date_idx] is not None else "").strip()
            eta = str(row[eta_idx] if eta_idx is not None and row[eta_idx] is not None else "").strip()

            if consignment_number in existing_numbers or consignment_number in file_seen:
                skipped_count += 1
                continue

            consignment = Consignment(
                consignment_number=consignment_number,
                status=status,
                pickup_address=pickup_address,
                pickup_pincode=pickup_pincode,
                pickup_tag=pickup_tag,
                pickup_date=pickup_date,
                drop_address=drop_address,
                drop_pincode=drop_pincode,
                drop_tag=drop_tag,
                drop_date=drop_date,
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
            "consignment_number",
            "status",
            "pickup_tag",
            "drop_pincode",
            "pickup_date",
            "drop_date",
            "pickup_address",
            "drop_address",
        ])

        for row in rows:
            sheet.append([
                row.consignment_number,
                row.status,
                getattr(row, "pickup_tag", ""),
                row.drop_pincode,
                getattr(row, "pickup_date", ""),
                getattr(row, "drop_date", ""),
                getattr(row, "pickup_address", ""),
                getattr(row, "drop_address", ""),
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

        table_data = [["Consignment #", "Status", "Pickup Tag", "Drop Pin", "Pickup Date", "Drop Estimated"]]
        for row in rows:
            table_data.append([
                row.consignment_number or "",
                row.status or "",
                getattr(row, "pickup_tag", "") or "",
                row.drop_pincode or "",
                getattr(row, "pickup_date", "") or "",
                getattr(row, "drop_date", "") or "",
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
            Paragraph("Internal Consignment MIS", styles["Heading2"]),
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
            "pickup_address",
            "pickup_pincode",
            "pickup_tag",
            "pickup_date",
            "drop_address",
            "drop_pincode",
            "drop_tag",
            "drop_date",
        ])

        sheet.append([
            "CN001",
            "In Transit",
            "123 Main Street, New Delhi",
            "110017",
            "PICKUP-001",
            "2026-05-10",
            "456 Marine Drive, Mumbai",
            "400001",
            "DROP-001",
            "2026-05-12",
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
