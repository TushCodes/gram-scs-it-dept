import os
import base64
from io import BytesIO

import pytest
import sys
import pathlib

# Ensure project root is on sys.path so `app` package is importable when running tests
ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def setup_env_for_app(tmp_path):
    # Minimal env setup required by app
    os.environ['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'test-secret')
    from werkzeug.security import generate_password_hash
    os.environ['ADMIN_PASSWORD_HASH'] = generate_password_hash(os.environ.get('ADMIN_PASSWORD', 'admin-pass'))
    os.environ['FLASK_ENV'] = 'development'


def test_pod_upload_and_delete(tmp_path):
    setup_env_for_app(tmp_path)

    # Import app factory after env set
    from app import create_app
    from app.models import db, Consignment

    app = create_app()
    # isolate instance path to tmp
    app.instance_path = str(tmp_path / 'instance')
    os.makedirs(app.instance_path, exist_ok=True)

    client = app.test_client()

    with app.app_context():
        # ensure a fresh schema for test (drop any previous sqlite test.db)
        try:
            db.drop_all()
        except Exception:
            pass
        db.create_all()
        c = Consignment(consignment_number='TEST-CN-1', status='In Transit')
        db.session.add(c)
        db.session.commit()
        cid = c.id

    # Authenticate session as admin
    from app.admin.auth import ADMIN_SESSION_KEY
    with client.session_transaction() as sess:
        sess[ADMIN_SESSION_KEY] = True

    # Upload POD
    data = {
        'file': (BytesIO(b'pod-data-bytes'), 'pod.jpg')
    }
    resp = client.post(f'/admin/consignments/{cid}/pod', data=data, content_type='multipart/form-data')
    assert resp.status_code == 200
    j = resp.get_json()
    assert j and j.get('success') is True

    # Check that GET serves the file (local fallback path)
    get_resp = client.get(f'/admin/consignments/{cid}/pod')
    assert get_resp.status_code == 200
    assert get_resp.data == b'pod-data-bytes'

    # Delete POD
    del_resp = client.delete(f'/admin/consignments/{cid}/pod')
    assert del_resp.status_code == 200
    j2 = del_resp.get_json()
    assert j2 and j2.get('success') is True

    # Confirm DB field cleared
    with app.app_context():
        row = Consignment.query.get(cid)
        assert row.pod_image in (None, '')


def test_staged_pod_upload_saves_with_row(tmp_path):
    setup_env_for_app(tmp_path)

    from app import create_app
    from app.models import db, Consignment

    app = create_app()
    app.instance_path = str(tmp_path / 'instance')
    os.makedirs(app.instance_path, exist_ok=True)

    client = app.test_client()

    with app.app_context():
        try:
            db.drop_all()
        except Exception:
            pass
        db.create_all()

    from app.admin.auth import ADMIN_SESSION_KEY
    with client.session_transaction() as sess:
        sess[ADMIN_SESSION_KEY] = True

    pod_bytes = b'fake-image-bytes'
    pod_data_url = 'data:image/jpeg;base64,' + base64.b64encode(pod_bytes).decode('ascii')

    payload = {
        'rows': [
            {
                'id': None,
                'consignment_number': 'STAGEDCN1',
                'status': 'In Transit',
                'pickup_pincode': '',
                'pickup_address': '',
                'pickup_tag': '',
                'pickup_date': '',
                'drop_pincode': '',
                'drop_address': '',
                'drop_tag': '',
                'drop_date': '',
                'eta': '',
                'pod_file_name': 'pod.jpg',
                'pod_file_type': 'image/jpeg',
                'pod_file_data': pod_data_url,
            }
        ],
        'deleted_ids': [],
    }

    resp = client.post('/admin/consignments/save', json=payload)
    assert resp.status_code == 200
    body = resp.get_json()
    assert body and body.get('success') is True

    with app.app_context():
        row = Consignment.query.filter_by(consignment_number='STAGEDCN1').first()
        assert row is not None
        assert row.pod_image
        pod_path = os.path.join(app.instance_path, 'uploads', row.pod_image)
        assert os.path.exists(pod_path)
        with open(pod_path, 'rb') as file_handle:
            assert file_handle.read() == pod_bytes
