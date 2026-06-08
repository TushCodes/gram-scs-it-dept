import logging
import mimetypes
import re
import io
import os
import requests

from flask import Blueprint, render_template, request
from flask import jsonify, redirect, send_file, current_app
from sqlalchemy.exc import DatabaseError, OperationalError

from app.models import db
from app.track.models import TrackConsignment

logger = logging.getLogger(__name__)

track_bp = Blueprint("track", __name__, template_folder="templates")

CONSIGNMENT_NUMBER_PATTERN = re.compile(r"^[A-Za-z0-9]{1,16}$")


@track_bp.route("/track", methods=["GET", "POST"])
def track_page():
    consignment = None
    error_message = None

    if request.method == "POST":
        number = (request.form.get("consignment_number") or "").strip().upper()

        if not number:
            error_message = "Please enter a consignment number."
            logger.warning("Rejected empty consignment lookup request")
        elif not CONSIGNMENT_NUMBER_PATTERN.fullmatch(number):
            error_message = "Invalid consignment number format."
            logger.warning("Rejected invalid consignment number: %s", number)
        else:
            logger.info("Track lookup received for consignment %s", number)
            try:
                consignment = TrackConsignment.query.filter_by(consignment_number=number).first()

                if consignment:
                    logger.info("Shipment found for consignment %s", number)
                else:
                    logger.info("Shipment not found for consignment %s", number)
                    error_message = "Consignment not found. Please check the number and try again."
            except (OperationalError, DatabaseError) as error:
                logger.error("Database error while tracking %s: %s", number, error)
                error_message = "Unable to connect to database. Please try again later."
            except Exception:
                logger.exception("Unexpected error while tracking %s", number)
                error_message = "An unexpected error occurred. Please try again."

    return render_template(
        "track/track.html",
        consignment=consignment,
        error_message=error_message,
    )


@track_bp.route("/track/pod/<consignment_number>", methods=["GET"], endpoint="consignment_pod")
def consignment_pod(consignment_number):
    """Serve or stream the POD for a consignment identified by number.

    This mirrors the admin POD-serving behavior but looks up by consignment number
    so the public Track page can download the POD.
    """
    try:
        number = (consignment_number or "").strip().upper()
        if not number:
            return jsonify({"success": False, "message": "Consignment number required."}), 400

        consignment = TrackConsignment.query.filter_by(consignment_number=number).first()
        if not consignment or not getattr(consignment, "pod_image", None):
            return jsonify({"success": False, "message": "No POD found."}), 404

        pod_path = consignment.pod_image
        # If it's already a full URL, attempt to proxy and force download
        if isinstance(pod_path, str) and (pod_path.startswith("http://") or pod_path.startswith("https://")):
            try:
                resp = requests.get(pod_path, stream=True, timeout=15)
                resp.raise_for_status()
                content_bytes = resp.content
                ctype = resp.headers.get("content-type", None)
                filename = f"{number}_pod.jpg"

                # Try to convert to JPEG to ensure consistent .jpg download
                try:
                    from PIL import Image
                    img = Image.open(io.BytesIO(content_bytes))
                    out = io.BytesIO()
                    rgb = img.convert("RGB")
                    rgb.save(out, format="JPEG", quality=85)
                    out.seek(0)
                    return send_file(out, as_attachment=True, download_name=filename, mimetype='image/jpeg')
                except Exception:
                    # fallback to proxying original bytes with original content-type
                    content = io.BytesIO(content_bytes)
                    return send_file(content, as_attachment=True, download_name=filename, mimetype=ctype)
            except Exception:
                return jsonify({"success": False, "message": "Failed to retrieve external POD."}), 502

        # Supabase-stored value: "supabase:bucket/path". Keep this route as the
        # permanent public download endpoint and stream bytes directly instead of
        # redirecting users to a temporary storage URL.
        if isinstance(pod_path, str) and pod_path.startswith("supabase:"):
            try:
                from app.admin.consignment_controller import _download_supabase_pod_file

                content_bytes, object_path = _download_supabase_pod_file(pod_path)
                mimetype, _ = mimetypes.guess_type(object_path)
                filename = os.path.basename(object_path) or f"{number}_pod.jpg"
                return send_file(
                    io.BytesIO(content_bytes),
                    as_attachment=True,
                    download_name=filename,
                    mimetype=mimetype or "application/octet-stream",
                )
            except RuntimeError as error:
                logger.exception('Error downloading Supabase POD file')
                return jsonify({"success": False, "message": str(error)}), 500
            except Exception:
                logger.exception('Error serving Supabase POD file')
                return jsonify({"success": False, "message": "Failed to serve POD."}), 500

        # Otherwise treat as local filename under instance/uploads
        upload_folder = os.path.join(current_app.instance_path, "uploads")
        safe_path = os.path.normpath(os.path.join(upload_folder, pod_path))
        if not safe_path.startswith(os.path.abspath(upload_folder)):
            return jsonify({"success": False, "message": "Invalid POD path."}), 400

        if not os.path.exists(safe_path):
            try:
                from app.admin.consignment_controller import _download_legacy_supabase_pod_file

                content_bytes, bucket, object_path = _download_legacy_supabase_pod_file(
                    getattr(consignment, "id", None),
                    pod_path,
                )
                consignment.pod_image = f"supabase:{bucket}/{object_path}"
                db.session.commit()
                mimetype, _ = mimetypes.guess_type(object_path)
                filename = os.path.basename(object_path) or f"{number}_pod.jpg"
                return send_file(
                    io.BytesIO(content_bytes),
                    as_attachment=True,
                    download_name=filename,
                    mimetype=mimetype or "application/octet-stream",
                )
            except Exception:
                db.session.rollback()
                logger.exception('Legacy local POD was not found locally or in Supabase')
                return jsonify({"success": False, "message": "POD file missing."}), 404

        # serve as attachment so browsers download; convert to JPEG for consistent .jpg
        try:
            from PIL import Image
            with open(safe_path, 'rb') as fh:
                img = Image.open(fh)
                out = io.BytesIO()
                rgb = img.convert("RGB")
                rgb.save(out, format="JPEG", quality=85)
                out.seek(0)
                return send_file(out, as_attachment=True, download_name=f"{number}_pod.jpg", mimetype='image/jpeg')
        except Exception:
            # if conversion fails, send the original file with its filename
            return send_file(safe_path, as_attachment=True, download_name=os.path.basename(safe_path))
    except Exception:
        return jsonify({"success": False, "message": "Failed to serve POD."}), 500
