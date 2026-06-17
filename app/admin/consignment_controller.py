"""Admin consignment management routes and helpers."""

import io
import logging
<<<<<<< HEAD
import mimetypes
import re
import os
import uuid
import base64
import binascii
import tempfile
from datetime import datetime
from flask import current_app
from werkzeug.utils import secure_filename
import io as _io
=======
import os
import re

from flask import current_app, flash, jsonify, redirect, render_template, request, send_file, url_for
from openpyxl import Workbook, load_workbook
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen import canvas
from sqlalchemy import or_
from sqlalchemy.exc import DatabaseError, OperationalError, ProgrammingError

from app import limiter
from app.admin import admin_bp
from app.admin.auth import require_admin
from app.models import Consignment, db

logger = logging.getLogger(__name__)
MAX_POD_IMAGE_BYTES = 5 * 1024 * 1024

>>>>>>> b15592d (Permanently fixing startup issues)

def _get_supabase_client():
    url = os.getenv("SUPABASE_URL", "").strip()
    key = os.getenv("SUPABASE_KEY", "").strip()
    if not url or not key:
        return None
    try:
        from supabase import create_client
    except Exception:
        logger.warning("Supabase package not available; falling back to local uploads")
        return None
    try:
        return create_client(url, key)
    except Exception:
        logger.exception("Failed to create Supabase client")
        return None


def _store_pod_bytes(filename, file_bytes, content_type=None, bucket_name=None):
    supa = _get_supabase_client()
    if supa:
        bucket = bucket_name or os.getenv("SUPABASE_BUCKET", "pod-uploads")
        object_path = f"consignments/{filename}"
<<<<<<< HEAD
        # storage3 client expects a file path; write bytes to a temporary file
        tmp = None
        try:
            tf = tempfile.NamedTemporaryFile(delete=False)
            tmp = tf.name
            tf.write(file_bytes)
            tf.flush()
            tf.close()
            supa.storage.from_(bucket).upload(
                object_path,
                tmp,
                {'content-type': content_type or 'application/octet-stream'},
            )
        finally:
            try:
                if tmp and os.path.exists(tmp):
                    os.remove(tmp)
            except Exception:
                logger.exception('Failed to remove temporary POD upload file')
=======
        supa.storage.from_(bucket).upload(
            object_path,
            io.BytesIO(file_bytes),
            {"content-type": content_type or "application/octet-stream"},
        )
>>>>>>> b15592d (Permanently fixing startup issues)
        return f"supabase:{bucket}/{object_path}"

    upload_folder = os.path.join(current_app.instance_path, "uploads")
    os.makedirs(upload_folder, exist_ok=True)
    dest_path = os.path.join(upload_folder, filename)
    with open(dest_path, "wb") as handle:
        handle.write(file_bytes)
    return filename


def _parse_supabase_pod_value(pod_value):
    if not isinstance(pod_value, str) or not pod_value.startswith('supabase:'):
        raise ValueError('POD is not stored in Supabase.')

    _, rest = pod_value.split(':', 1)
    bucket, object_path = rest.split('/', 1)
    if not bucket or not object_path:
        raise ValueError('Invalid Supabase POD path.')

    return bucket, object_path


def _download_supabase_pod_file(pod_value):
    client = _get_supabase_client()
    if not client:
        raise RuntimeError('Supabase not configured.')

    bucket, object_path = _parse_supabase_pod_value(pod_value)
    content = client.storage.from_(bucket).download(object_path)
    if hasattr(content, 'read'):
        content = content.read()
    if isinstance(content, bytearray):
        content = bytes(content)
    if not isinstance(content, bytes):
        raise RuntimeError('Unexpected Supabase download response.')

    return content, object_path


def _download_legacy_supabase_pod_file(consignment_id, pod_value):
    """Download a legacy POD by attempting old Supabase object paths.

    Legacy records may store a bare object path or a local filename that was
    previously migrated into Supabase. This helper tries the configured bucket
    and an optional consignment-id-prefixed path.
    """
    client = _get_supabase_client()
    if not client:
        raise RuntimeError('Supabase not configured.')

    bucket = os.getenv('SUPABASE_BUCKET', 'pod-uploads')
    if not isinstance(pod_value, str) or not pod_value:
        raise ValueError('Invalid legacy POD path.')

    candidates = []
    legacy_bucket = bucket
    if pod_value.startswith('supabase:'):
        _, rest = pod_value.split(':', 1)
        try:
            legacy_bucket, legacy_object_path = rest.split('/', 1)
        except ValueError:
            legacy_bucket = bucket
            legacy_object_path = rest
        candidates.append((legacy_bucket, legacy_object_path))
    else:
        candidates.append((bucket, pod_value))
        if consignment_id is not None:
            consignment_prefix = str(consignment_id)
            if not pod_value.startswith(consignment_prefix + '/'):
                candidates.append((bucket, f"{consignment_prefix}/{pod_value}"))

    last_error = None
    for candidate_bucket, object_path in candidates:
        try:
            content = client.storage.from_(candidate_bucket).download(object_path)
            if hasattr(content, 'read'):
                content = content.read()
            if isinstance(content, bytearray):
                content = bytes(content)
            if not isinstance(content, bytes):
                raise RuntimeError('Unexpected Supabase download response.')
            return content, candidate_bucket, object_path
        except Exception as exc:
            last_error = exc

    # Last chance: if the value was a local filename under uploads, try that path.
    upload_folder = os.path.join(current_app.instance_path, 'uploads')
    try:
        legacy_path = os.path.normpath(os.path.join(upload_folder, pod_value))
        if legacy_path.startswith(os.path.abspath(upload_folder)) and os.path.exists(legacy_path):
            with open(legacy_path, 'rb') as fh:
                return fh.read(), bucket, pod_value
    except Exception:
        pass

    raise RuntimeError('Legacy POD file not found.') from last_error


def _delete_pod_file(pod_value):
    if not pod_value:
        return

    if isinstance(pod_value, str) and pod_value.startswith("supabase:"):
        client = _get_supabase_client()
        if not client:
            return
        try:
            _, rest = pod_value.split(":", 1)
            bucket, object_path = rest.split("/", 1)
            client.storage.from_(bucket).remove([object_path])
        except Exception:
            logger.exception("Failed to remove POD from Supabase")
        return

    upload_folder = os.path.join(current_app.instance_path, "uploads")
    pod_path = os.path.normpath(os.path.join(upload_folder, pod_value))
    if pod_path.startswith(os.path.abspath(upload_folder)) and os.path.exists(pod_path):
        try:
            os.remove(pod_path)
        except Exception:
<<<<<<< HEAD
            logger.exception('Failed to remove POD file from disk')


def _parse_date_string(value):
    if not value or not isinstance(value, str):
        return None

    value = value.strip()
    if not value:
        return None

    # Prefer ISO date format, but support common day/month/year formats if present.
    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%m/%d/%Y"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue

    return None

from flask import flash, jsonify, redirect, render_template, request, send_file, url_for
from openpyxl import Workbook, load_workbook
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from sqlalchemy.exc import DatabaseError, IntegrityError, OperationalError, ProgrammingError
from sqlalchemy import inspect as sa_inspect

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

MAX_POD_IMAGE_BYTES = 5 * 1024 * 1024
=======
            logger.exception("Failed to remove POD file from disk")
>>>>>>> b15592d (Permanently fixing startup issues)


def _is_external_pod_url(value):
    if not isinstance(value, str):
        return False
    lowered = value.strip().lower()
    return lowered.startswith("http://") or lowered.startswith("https://")


def _normalize_header(value):
    return re.sub(r"[^a-z0-9]+", "_", str(value or "").strip().lower()).strip("_")


def _serialize_consignment(consignment):
    return {
        "id": getattr(consignment, "id", None),
        "consignment_number": getattr(consignment, "consignment_number", None),
        "status": getattr(consignment, "status", None),
        "pickup_pincode": getattr(consignment, "pickup_pincode", None),
        "pickup_address": getattr(consignment, "pickup_address", None),
        "pickup_tag": getattr(consignment, "pickup_tag", None),
        "pickup_date": getattr(consignment, "pickup_date", None),
        "drop_pincode": getattr(consignment, "drop_pincode", None),
        "drop_address": getattr(consignment, "drop_address", None),
        "drop_tag": getattr(consignment, "drop_tag", None),
        "drop_date": getattr(consignment, "drop_date", None),
        "eta": getattr(consignment, "eta", None),
        "pod_image": getattr(consignment, "pod_image", None),
        "pod_file_name": getattr(consignment, "pod_file_name", None),
        "pod_file_type": getattr(consignment, "pod_file_type", None),
        "pod_file_data": getattr(consignment, "pod_file_data", None),
    }


@admin_bp.route("/admin/consignments", methods=["GET"], endpoint="consignments_panel")
@require_admin
def consignments_panel():
    try:
        total = Consignment.query.count()
        consignments = [] if total > 500 else Consignment.query.order_by(Consignment.id.asc()).limit(200).all()
        rows = [_serialize_consignment(row) for row in consignments]
        return render_template("admin/consignments.html", consignments=rows)
    except (OperationalError, DatabaseError, ProgrammingError):
        logger.exception("Database error loading admin consignments panel")
        return render_template(
            "admin/consignments.html",
            consignments=[],
            error="Unable to load data. Please try again.",
        )
    except Exception:
        logger.exception("Unexpected error in admin consignments panel")
        return render_template(
            "admin/consignments.html",
            consignments=[],
            error="An unexpected error occurred.",
        )


@admin_bp.route("/admin/consignments/list", methods=["GET"], endpoint="consignments_list_api")
@require_admin
def consignments_list_api():
    try:
        page = max(1, request.args.get("page", 1, type=int))
        per_page = max(1, min(100, request.args.get("per_page", 10, type=int)))
        search = request.args.get("search", "", type=str).strip()
        sort_by = request.args.get("sort_by", "id", type=str)
        sort_order = request.args.get("sort_order", "asc", type=str)

        allowed_sort_columns = {
            "id", "consignment_number", "status", "pickup_pincode", "drop_pincode",
            "pickup_tag", "drop_tag", "pickup_date", "drop_date",
        }
        if sort_by not in allowed_sort_columns:
            sort_by = "id"
        sort_order = "asc" if sort_order.lower() == "asc" else "desc"

        query = Consignment.query
        if search:
            pattern = f"%{search}%"
            query = query.filter(
                or_(
                    Consignment.consignment_number.ilike(pattern),
                    Consignment.status.ilike(pattern),
                    Consignment.pickup_tag.ilike(pattern),
                    Consignment.drop_tag.ilike(pattern),
                    Consignment.pickup_pincode.ilike(pattern),
                    Consignment.drop_pincode.ilike(pattern),
                    Consignment.pickup_address.ilike(pattern),
                    Consignment.drop_address.ilike(pattern),
                )
            )

        total = query.count()
        sort_column = getattr(Consignment, sort_by)
        query = query.order_by(sort_column.desc() if sort_order == "desc" else sort_column.asc())
        rows = query.offset((page - 1) * per_page).limit(per_page).all()

        pages = (total + per_page - 1) // per_page if total else 0
        return jsonify({
            "success": True,
            "rows": [_serialize_consignment(row) for row in rows],
            "page": page,
            "per_page": per_page,
            "total": total,
            "pages": pages,
            "has_prev": page > 1,
            "has_next": page < pages,
        })
    except Exception as exc:
        logger.exception("Consignment list API failed: %s", exc)
        return jsonify({
            "success": False,
            "rows": [],
            "page": 1,
            "per_page": 10,
            "total": 0,
            "pages": 0,
            "has_prev": False,
            "has_next": False,
            "error": "Unable to load consignments right now.",
        }), 500


@admin_bp.route("/admin/consignments/import-template.xlsx", methods=["GET"], endpoint="consignments_import_template_excel")
@require_admin
def consignments_import_template_excel():
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Consignments"
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

<<<<<<< HEAD
    if not isinstance(rows, list) or not isinstance(deleted_ids, list):
        return jsonify({"success": False, "message": "Invalid request payload."}), 400

    try:
        # Debug logging: record incoming payload and per-row id types to diagnose
        logger.info("consignments_save incoming payload: %s", payload)
        logger.info("consignments_save deleted_ids (raw): %s", deleted_ids)
        for idx, r in enumerate(rows):
            try:
                raw_id = r.get("id")
            except Exception:
                raw_id = None
            logger.info(
                "consignments_save row %d raw_id=%r type=%s consignment_number=%r",
                idx,
                raw_id,
                type(raw_id).__name__ if raw_id is not None else "None",
                r.get("consignment_number"),
            )

        # Avoid selecting all mapped columns (which fails if the DB schema is missing new columns).
        # Fetch only ids first so we can detect missing-column errors early and provide a clear message.
        try:
            existing_ids = [r[0] for r in db.session.query(Consignment.id).all()]
            existing = {int(i): None for i in existing_ids}
        except (ProgrammingError, OperationalError, DatabaseError) as e:
            db.session.rollback()
            if _is_missing_column_error(e):
                logger.exception("Schema mismatch in admin save")
                return jsonify({"success": False, "message": "Database schema needs an update. Missing consignment fields."}), 500

            logger.exception("Database error in admin save")
            return jsonify({"success": False, "message": "Database connection error. Please try again."}), 500
        validated_deleted_ids = set()

        for raw_deleted_id in deleted_ids:
            try:
                deleted_id = int(raw_deleted_id)
            except (TypeError, ValueError):
                return jsonify({"success": False, "message": f"Invalid deleted row id: {raw_deleted_id}"}), 400

            # Ignore client-side temporary ids (non-positive values)
            if deleted_id <= 0:
                continue

            if deleted_id not in existing:
                return jsonify({"success": False, "message": f"Deleted row id {deleted_id} not found."}), 400

            validated_deleted_ids.add(deleted_id)

        seen_numbers = set()
        validated_rows = []
        errors = []

        for idx, row in enumerate(rows):
            row_id = row.get("id")
            try:
                consignment_number = normalize_consignment_number(row.get("consignment_number"))
            except ValueError as error:
                errors.append({"index": idx, "field": "consignment_number", "message": str(error)})
                consignment_number = None

            try:
                status = normalize_status(row.get("status"))
            except ValueError as error:
                errors.append({"index": idx, "field": "status", "message": str(error)})
                status = None

            try:
                pickup_pincode = normalize_indian_pincode(row.get("pickup_pincode"), "pickup_pincode")
            except ValueError as error:
                errors.append({"index": idx, "field": "pickup_pincode", "message": str(error)})
                pickup_pincode = None

            try:
                drop_pincode = normalize_indian_pincode(row.get("drop_pincode"), "drop_pincode")
            except ValueError as error:
                errors.append({"index": idx, "field": "drop_pincode", "message": str(error)})
                drop_pincode = None

            eta = str(row.get("eta") or "").strip()

            if consignment_number:
                if consignment_number in seen_numbers:
                    errors.append({"index": idx, "field": "consignment_number", "message": f"Duplicate consignment number in sheet: {consignment_number}"})
                seen_numbers.add(consignment_number)

            if row_id is not None:
                try:
                    row_id = int(row_id)
                except (TypeError, ValueError):
                    errors.append({"index": idx, "field": "id", "message": f"Invalid row id: {row_id}"})
                    row_id = None

                # Treat non-positive ids (client temporary ids like -1) as new rows
                if row_id and row_id <= 0:
                    row_id = None
                else:
                    if row_id and row_id not in existing:
                        errors.append({"index": idx, "field": "id", "message": f"Row id {row_id} not found."})
                        row_id = None

                    if row_id and row_id in validated_deleted_ids:
                        errors.append({"index": idx, "field": "id", "message": f"Row id {row_id} cannot be updated and deleted in the same save."})
            else:
                row_id = None

            pickup_tag = str(row.get("pickup_tag") or "").strip()
            pickup_date = str(row.get("pickup_date") or "").strip()
            drop_tag = str(row.get("drop_tag") or "").strip()
            drop_date = str(row.get("drop_date") or "").strip()
            pod_file_data = str(row.get("pod_file_data") or "").strip() or None
            pod_file_name = str(row.get("pod_file_name") or "").strip() or None
            pod_file_type = str(row.get("pod_file_type") or "").strip() or None
            pod_image = str(row.get("pod_image") or "").strip() or None

            # Never persist external POD URLs. They are often presigned and expire,
            # which breaks long-term archive requirements.
            if pod_image and _is_external_pod_url(pod_image):
                errors.append({
                    "index": idx,
                    "field": "pod_image",
                    "message": "External POD URLs are not allowed. Upload the image file so we can store a permanent reference.",
                })

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
                "pod_image": pod_image,
                "pod_file_data": pod_file_data,
                "pod_file_name": pod_file_name,
                "pod_file_type": pod_file_type,
            })

        # If any per-row validation errors were collected, return them instead of aborting.
        if errors:
            db.session.rollback()
            return jsonify({"success": False, "errors": errors}), 400

        # Detect missing DB columns proactively to avoid failing mid-commit with unclear errors.
        try:
            inspector = sa_inspect(db.engine)
            db_columns = {c['name'] for c in inspector.get_columns('consignment')}
            model_columns = {col.name for col in Consignment.__table__.columns}
            missing_cols = model_columns.difference(db_columns)
            if missing_cols:
                logger.exception("Schema mismatch detected while saving: missing columns %s", missing_cols)
                db.session.rollback()
                return jsonify({"success": False, "message": "Database schema needs an update. Missing consignment fields."}), 500
        except Exception:
            # If inspection fails for any reason, continue and let DB operations surface errors.
            logger.exception("Failed to inspect consignment table columns")

        for deleted_id in validated_deleted_ids:
            consignment = db.session.get(Consignment, int(deleted_id))
            if consignment is not None:
                db.session.delete(consignment)

        for row in validated_rows:
            if row["id"]:
                # Load the specific Consignment instance on demand. This avoids a full-table
                # select which may fail when the DB schema differs from model mappings.
                try:
                    consignment = db.session.get(Consignment, int(row["id"]))
                except Exception:
                    consignment = None

                if consignment is None:
                    # This should generally not happen (validated earlier), but handle gracefully.
                    consignment = Consignment()
                    db.session.add(consignment)
            else:
                consignment = Consignment()
                db.session.add(consignment)

            previous_pod_image = getattr(consignment, 'pod_image', None)
            new_pod_image = row.get("pod_image")

            if row.get("pod_file_data"):
                try:
                    pod_bytes = _decode_pod_data_url(row["pod_file_data"])
                    original_name = row.get("pod_file_name") or "pod.jpg"
                    filename = f"{uuid.uuid4().hex}_{secure_filename(original_name)}"
                    new_pod_image = _store_pod_bytes(filename, pod_bytes, row.get("pod_file_type"))
                except ValueError as error:
                    db.session.rollback()
                    return jsonify({"success": False, "message": str(error)}), 400

            if previous_pod_image and new_pod_image and previous_pod_image != new_pod_image:
                _delete_pod_file(previous_pod_image)

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
            consignment.pod_image = new_pod_image

        db.session.commit()
        # Return the updated total so the client can navigate to the page
        # that will contain newly inserted rows (the new last page).
        try:
            total = Consignment.query.count()
        except Exception:
            total = None

        return jsonify({
            "success": True,
            "message": "Sheet saved successfully.",
            "deleted_count": len(validated_deleted_ids),
            "total": total,
        })

    except IntegrityError:
        db.session.rollback()
        logger.exception("Integrity error in admin save")
        return jsonify({"success": False, "message": "Duplicate consignment number already exists."}), 400
    except Exception:
        db.session.rollback()
        logger.exception("Unexpected error in admin save")
        return jsonify({"success": False, "message": "An unexpected error occurred. Please try again."}), 500
=======
    buffer = io.BytesIO()
    workbook.save(buffer)
    buffer.seek(0)
    return send_file(
        buffer,
        as_attachment=True,
        download_name="consignment_import_template.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
>>>>>>> b15592d (Permanently fixing startup issues)


@admin_bp.route("/admin/consignments/archive", methods=["POST"], endpoint="consignments_archive")
@limiter.limit("10 per minute")
@require_admin
def consignments_archive():
    payload = request.get_json(silent=True) or {}
    before_date = str(payload.get("before_date") or "").strip()

    if not before_date:
        return jsonify({"success": False, "message": "Please provide a cutoff date."}), 400

    cutoff_date = _parse_date_string(before_date)
    if cutoff_date is None:
        return jsonify({"success": False, "message": "Cutoff date must be a valid date in YYYY-MM-DD format."}), 400

    try:
        query = Consignment.query.filter(Consignment.status.ilike("Delivered"))
        query = query.filter(Consignment.drop_date.isnot(None), Consignment.drop_date != "")

        archived_count = 0
        for consignment in query.all():
            drop_date = _parse_date_string(getattr(consignment, "drop_date", ""))
            if drop_date is None:
                continue
            if drop_date < cutoff_date:
                if getattr(consignment, "pod_image", None):
                    _delete_pod_file(consignment.pod_image)
                db.session.delete(consignment)
                archived_count += 1

        db.session.commit()
        return jsonify({"success": True, "archived_count": archived_count})
    except (OperationalError, DatabaseError):
        db.session.rollback()
        logger.exception("Database error archiving consignments")
        return jsonify({"success": False, "message": "Unable to archive consignments. Please try again."}), 500
    except Exception:
        db.session.rollback()
        logger.exception("Unexpected error archiving consignments")
        return jsonify({"success": False, "message": "An unexpected error occurred while archiving consignments."}), 500


@admin_bp.route("/admin/consignments/import", methods=["POST"], endpoint="consignments_import_excel")
@limiter.limit("10 per minute")
@require_admin
def consignments_import_excel():
    uploaded_file = request.files.get("file")
    if not uploaded_file:
        flash("Please choose an Excel file to import.", "danger")
        return redirect(url_for("admin.consignments_panel"))

    workbook = load_workbook(uploaded_file, data_only=True)
    sheet = workbook.active
    headers = [_normalize_header(cell) for cell in next(sheet.iter_rows(min_row=1, max_row=1, values_only=True))]

    existing_numbers = {
        row[0]
        for row in Consignment.query.with_entities(Consignment.consignment_number).all()
        if row and row[0]
    }

    added_count = 0
    skipped_duplicates = 0

    for row_values in sheet.iter_rows(min_row=2, values_only=True):
        row_data = {headers[index]: value for index, value in enumerate(row_values) if index < len(headers)}
        consignment_number = str(row_data.get("consignment_number") or "").strip()
        if not consignment_number:
            continue
        if consignment_number in existing_numbers:
            skipped_duplicates += 1
            continue

        consignment = Consignment(
            consignment_number=consignment_number,
            status=row_data.get("status") or "",
            pickup_address=row_data.get("pickup_address"),
            pickup_pincode=row_data.get("pickup_pincode"),
            pickup_tag=row_data.get("pickup_tag"),
            pickup_date=row_data.get("pickup_date"),
            drop_address=row_data.get("drop_address"),
            drop_pincode=row_data.get("drop_pincode"),
            drop_tag=row_data.get("drop_tag"),
            drop_date=row_data.get("drop_date"),
        )

        db.session.add(consignment)
        existing_numbers.add(consignment_number)
        added_count += 1

    try:
        db.session.commit()
        flash(f"Import completed. Added: {added_count}, skipped duplicates: {skipped_duplicates}.", "success")
    except Exception:
        db.session.rollback()
        logger.exception("Failed to import consignments")
        flash("Import failed.", "danger")

    return redirect(url_for("admin.consignments_panel"))


@admin_bp.route("/admin/consignments/export.xlsx", methods=["GET"], endpoint="consignments_export_excel")
@require_admin
def consignments_export_excel():
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Consignments"
    headers = [
        "consignment_number",
        "status",
        "pickup_tag",
        "drop_pincode",
        "pickup_date",
        "drop_date",
        "pickup_address",
        "drop_address",
    ]
    sheet.append(headers)

    rows = Consignment.query.order_by(Consignment.id.asc()).all()
    for consignment in rows:
        sheet.append([
            getattr(consignment, "consignment_number", None),
            getattr(consignment, "status", None),
            getattr(consignment, "pickup_tag", None),
            getattr(consignment, "drop_pincode", None),
            getattr(consignment, "pickup_date", None),
            getattr(consignment, "drop_date", None),
            getattr(consignment, "pickup_address", None),
            getattr(consignment, "drop_address", None),
        ])

    buffer = io.BytesIO()
    workbook.save(buffer)
    buffer.seek(0)
    return send_file(
        buffer,
        as_attachment=True,
        download_name="consignments.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


@admin_bp.route("/admin/consignments/export.pdf", methods=["GET"], endpoint="consignments_export_pdf")
@require_admin
def consignments_export_pdf():
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=landscape(A4))
    pdf.drawString(40, 550, "Consignments Export")
    pdf.showPage()
    pdf.save()
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name="consignments.pdf", mimetype="application/pdf")


@admin_bp.route("/admin/consignments/save", methods=["POST"], endpoint="consignments_save")
@require_admin
def consignments_save():
    if request.is_json:
        payload = request.get_json(silent=True) or {}
    else:
        payload = request.form.to_dict(flat=True)

    consignment_number = (payload.get("consignment_number") or "").strip()
    if not consignment_number:
        return jsonify({"success": False, "message": "Consignment number is required."}), 400

<<<<<<< HEAD
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


@admin_bp.route("/admin/consignments/<int:consignment_id>/pod", methods=["GET"], endpoint="consignment_pod_file")
@require_admin
def consignment_pod_file(consignment_id):
    """Serve the POD file for a consignment if present."""
    try:
        consignment = db.session.get(Consignment, consignment_id)
        if not consignment or not getattr(consignment, "pod_image", None):
            return jsonify({"success": False, "message": "No POD found."}), 404

        # pod_image may be:
        # - a local relative filename stored under instance/uploads
        # - a supabase marker value like "supabase:bucket/path/to/file"
        # - a public URL (http/https)
        pod_path = consignment.pod_image
        if pod_path.startswith("http://") or pod_path.startswith("https://"):
            return redirect(pod_path)

        # Supabase-stored value: "supabase:bucket/path". Keep the app route as the
        # stable POD URL and stream bytes directly instead of redirecting to a
        # temporary storage URL.
        if isinstance(pod_path, str) and pod_path.startswith("supabase:"):
            try:
                content, object_path = _download_supabase_pod_file(pod_path)
                mimetype, _ = mimetypes.guess_type(object_path)
                return send_file(io.BytesIO(content), mimetype=mimetype or "application/octet-stream")
            except RuntimeError as error:
                logger.exception("Error downloading Supabase POD file")
                return jsonify({"success": False, "message": str(error)}), 500
            except Exception:
                logger.exception("Error serving Supabase POD file")
                return jsonify({"success": False, "message": "Failed to serve POD."}), 500

        # Otherwise treat as local filename under instance/uploads
        upload_folder = os.path.join(current_app.instance_path, "uploads")
        safe_path = os.path.normpath(os.path.join(upload_folder, pod_path))
        if not safe_path.startswith(os.path.abspath(upload_folder)):
            return jsonify({"success": False, "message": "Invalid POD path."}), 400

        if not os.path.exists(safe_path):
            try:
                content, bucket, object_path = _download_legacy_supabase_pod_file(consignment.id, pod_path)
                consignment.pod_image = f"supabase:{bucket}/{object_path}"
                db.session.commit()
                mimetype, _ = mimetypes.guess_type(object_path)
                return send_file(io.BytesIO(content), mimetype=mimetype or "application/octet-stream")
            except Exception:
                db.session.rollback()
                logger.exception("Legacy local POD was not found locally or in Supabase")
                return jsonify({"success": False, "message": "POD file missing."}), 404

        return send_file(safe_path)
    except Exception:
        logger.exception("Error serving POD file")
        return jsonify({"success": False, "message": "Failed to serve POD."}), 500


@admin_bp.route("/admin/consignments/<int:consignment_id>/pod", methods=["POST"], endpoint="consignment_pod_upload")
@require_admin
def consignment_pod_upload(consignment_id):
    """Upload or replace a POD image for a consignment. Returns JSON with new pod path/url."""
    upload = request.files.get("file")
    if not upload or not upload.filename:
        return jsonify({"success": False, "message": "No file uploaded."}), 400

    if not (upload.mimetype or "").startswith("image/"):
        return jsonify({"success": False, "message": "POD must be an image file."}), 400

    try:
        consignment = db.session.get(Consignment, consignment_id)
        if not consignment:
            return jsonify({"success": False, "message": "Consignment not found."}), 404

        filename = secure_filename(upload.filename)
        filename = f"{uuid.uuid4().hex}_{filename}"
        file_bytes = upload.read()
        if len(file_bytes) > MAX_POD_IMAGE_BYTES:
            return jsonify({"success": False, "message": "POD image must be smaller than 5 MB."}), 400

        # If Supabase configured, upload there and store a marker 'supabase:bucket/path'
        supa = _get_supabase_client()
        bucket = os.getenv('SUPABASE_BUCKET', 'pod-uploads')
        if supa:
            try:
                object_path = f"{consignment_id}/{filename}"
                # upload to supabase; storage client expects a file path, so write temp file
                tmp = None
                try:
                    tf = tempfile.NamedTemporaryFile(delete=False)
                    tmp = tf.name
                    tf.write(file_bytes)
                    tf.flush()
                    tf.close()
                    supa.storage.from_(bucket).upload(object_path, tmp, {'content-type': upload.mimetype or 'application/octet-stream'})
                finally:
                    try:
                        if tmp and os.path.exists(tmp):
                            os.remove(tmp)
                    except Exception:
                        logger.exception('Failed to remove temporary POD upload file')

                # store marker so we can remove later
                consignment.pod_image = f"supabase:{bucket}/{object_path}"
                db.session.commit()
                return jsonify({"success": True, "pod_image": consignment.pod_image}), 200
            except Exception:
                db.session.rollback()
                logger.exception("Supabase POD upload failed; falling back to local storage")

        # fallback: local instance storage
        try:
            upload_folder = os.path.join(current_app.instance_path, "uploads")
            os.makedirs(upload_folder, exist_ok=True)
            dest_path = os.path.join(upload_folder, filename)
            with open(dest_path, "wb") as file_handle:
                file_handle.write(file_bytes)
            consignment.pod_image = filename
            db.session.commit()
            return jsonify({"success": True, "pod_image": filename}), 200
        except Exception:
            db.session.rollback()
            logger.exception("POD upload failed (local)")
            return jsonify({"success": False, "message": "Upload failed."}), 500
    except Exception:
        db.session.rollback()
        logger.exception("POD upload failed")
        return jsonify({"success": False, "message": "Upload failed."}), 500


@admin_bp.route("/admin/consignments/<int:consignment_id>/pod", methods=["DELETE"], endpoint="consignment_pod_delete")
@require_admin
def consignment_pod_delete(consignment_id):
    """Delete POD association (and file if present)."""
    try:
        consignment = db.session.get(Consignment, consignment_id)
        if not consignment or not getattr(consignment, "pod_image", None):
            return jsonify({"success": False, "message": "No POD to delete."}), 404

        # If stored in Supabase, remove via storage API
        pod_val = consignment.pod_image
        if isinstance(pod_val, str) and pod_val.startswith('supabase:'):
            client = _get_supabase_client()
            if client:
                try:
                    _, rest = pod_val.split(":", 1)
                    bucket, object_path = rest.split("/", 1)
                    client.storage.from_(bucket).remove([object_path])
                except Exception:
                    logger.exception("Failed to remove POD from Supabase")

        else:
            # local file
            upload_folder = os.path.join(current_app.instance_path, "uploads")
            pod_rel = consignment.pod_image
            try:
                pod_path = os.path.normpath(os.path.join(upload_folder, pod_rel))
                if pod_path.startswith(os.path.abspath(upload_folder)) and os.path.exists(pod_path):
                    try:
                        os.remove(pod_path)
                    except Exception:
                        logger.exception("Failed to remove POD file from disk")
            except Exception:
                logger.exception("Error while attempting to remove local POD file")

        consignment.pod_image = None
        db.session.commit()
        return jsonify({"success": True}), 200
    except Exception:
        db.session.rollback()
        logger.exception("Failed deleting POD")
        return jsonify({"success": False, "message": "Delete failed."}), 500
=======
    return jsonify({"success": True, "message": "Saved."})
>>>>>>> b15592d (Permanently fixing startup issues)
