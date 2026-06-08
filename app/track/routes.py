import logging
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

        # Supabase-stored value: "supabase:bucket/path"
        if isinstance(pod_path, str) and pod_path.startswith("supabase:"):
            # import helper lazily to avoid circular imports
            try:
                from app.admin.consignment_controller import _get_supabase_client
            except Exception:
                _get_supabase_client = None

            client = None
            if _get_supabase_client:
                client = _get_supabase_client()

            if not client:
                return jsonify({"success": False, "message": "Supabase not configured."}), 500

            try:
                _, rest = pod_path.split(":", 1)
                bucket, object_path = rest.split("/", 1)
                # create a short signed url and redirect the client to it
                ttl = int(os.getenv('SUPABASE_SIGNED_URL_TTL', '30'))
                signed = client.storage.from_(bucket).create_signed_url(object_path, ttl)
                url = None
                if isinstance(signed, dict):
                    url = signed.get('signedURL') or signed.get('signed_url') or signed.get('signedUrl')
                if not url:
                    pub = client.storage.from_(bucket).get_public_url(object_path)
                    url = pub.get('publicURL') or pub.get('publicUrl')
                if not url:
                    return jsonify({"success": False, "message": "Unable to generate POD URL."}), 500

                return redirect(url)
            except Exception:
                logger.exception('Error generating Supabase POD URL')
                return jsonify({"success": False, "message": "Failed to serve POD."}), 500

        # Otherwise treat as local filename under instance/uploads
        upload_folder = os.path.join(current_app.instance_path, "uploads")
        safe_path = os.path.normpath(os.path.join(upload_folder, pod_path))
        if not safe_path.startswith(os.path.abspath(upload_folder)):
            return jsonify({"success": False, "message": "Invalid POD path."}), 400

        logger.info(f"POD PATH: {safe_path}")
        if not os.path.exists(safe_path):
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
