# Kidney Stone Detection

A local web application for reviewing kidney ultrasound images with a trained
image-classification model. The application provides account registration and
login, image predictions with Grad-CAM overlays, per-user prediction history,
and administrator account management.

> **Medical-use notice:** This project is for research and educational use. Its
> model output is not a diagnosis and must not be used to make treatment
> decisions. Have scans assessed by a qualified clinician.

## Run with Docker Compose

Docker Desktop (including Docker Compose) is required. From the project root:

1. Copy `ml/.env.example` to `ml/.env`.
2. Replace `POSTGRES_PASSWORD` and `SECRET_KEY` with unique random values. The
   database password should use URL-safe characters. Set `COOKIE_SECURE=true`
   only when the app is served over HTTPS.
3. Start the application:

   ```powershell
   docker compose --env-file ml/.env -f ml/docker-compose.yml up --build
   ```

4. Open <http://localhost:3000>. The API is available at
   <http://localhost:8000/health>.

The Compose file expects the trained model at `ml/models/kidney_model.keras`
and its optional metadata at `ml/models/model_info.json`. The included model
can be used as-is. PostgreSQL data and uploaded images are stored in named
Docker volumes. To stop the services, press Ctrl+C and run
`docker compose --env-file ml/.env -f ml/docker-compose.yml down`.

For an optional administrator account, set `ADMIN_EMAIL` and `ADMIN_PASSWORD`
in `ml/.env` before the first start. Do not use sample or development secrets
in a deployment. After signing in with that account, open the **Admin** page to
review users or disable and restore accounts.

## Run locally on Windows

Run the backend and frontend in separate PowerShell windows. The backend
virtual environment and frontend dependencies must be installed first:

```powershell
Set-Location backend
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
$env:SECRET_KEY = "replace-with-a-random-secret-of-at-least-32-characters"
$env:MODEL_PATH = "..\ml\models\kidney_model.keras"
# Optional: configure an administrator before the first backend startup.
# $env:ADMIN_EMAIL = "admin@example.com"
# $env:ADMIN_PASSWORD = "replace-with-a-strong-password"
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

In another window:

```powershell
Set-Location frontend
npm install
npm run dev
```

Open <http://localhost:5173>. In local development the backend uses SQLite by
default and the Vite development server proxies `/api` requests to port 8000.
The app requires Python 3.12 for its pinned TensorFlow dependency and Node.js
with npm.

## Run backend tests

From the project root, install the optional test dependencies and run the
backend API suite:

```powershell
Set-Location backend
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest
```

## Model training

The training and evaluation scripts are in `ml/src`; the labeled raw dataset
is included under `ml/data/raw`. The preparation script finds the class folders
inside the bundled dataset directory. To retrain, install `ml/requirements.txt`
and run:

```powershell
Set-Location ml
.\.venv\Scripts\python.exe .\src\prepare_data.py
.\.venv\Scripts\python.exe .\src\train.py --model mobilenet
.\.venv\Scripts\python.exe .\src\evaluate.py
```

Preparing data replaces the existing `ml/data/splits` contents. Make a backup
if you need to preserve the current prepared split. Evaluation metrics in
`ml/reports` describe the included model's reported test split and are not a
guarantee of clinical performance or generalization.
