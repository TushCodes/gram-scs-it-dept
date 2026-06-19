# Use Case Diagram
<img width="1422" height="517" alt="image" src="https://github.com/user-attachments/assets/b8354daa-7230-406e-8082-73ac0351e716" />

# Component Diagram
<img width="560" height="343" alt="image" src="https://github.com/user-attachments/assets/dfbb8033-8469-44ce-a015-4b355a7e84d0" />

# Track Your Shipment : Sequence Diagram
<img width="1633" height="718" alt="image" src="https://github.com/user-attachments/assets/4ba33710-34aa-4926-a684-4595f621b7ae" />

# Admin / POD Setup

## Local admin login

- Username: `admin`
- Password: `secret123`

## Required production env vars

- `SECRET_KEY`
- `ADMIN_PASSWORD_HASH`
- `DATABASE_URL`
- `SUPABASE_URL` and `SUPABASE_KEY` for POD storage in production
- Optional: `SUPABASE_BUCKET` (defaults to `pod-uploads`)

## POD flow

- Choose an image in the consignment modal.
- Click the modal Save button to persist the row and its POD image.
- Clicking Cancel discards the staged image and reverts to the last saved state.

## Run locally

```bash
PORT=10002 python run.py
```

`run.py` will automatically create/use the project `.venv` and install `requirements.txt` when the active Python interpreter is missing runtime dependencies such as Flask. You can also install dependencies manually with:

```bash
python -m pip install -r requirements.txt
```

