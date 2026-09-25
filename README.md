# MaternaSense

## AI-Powered Maternal & Newborn Continuity Intelligence

MaternaSense is a research and educational clinical decision-support prototype for maintaining a longitudinal maternal and newborn care timeline. It connects antenatal, delivery, newborn, and postnatal records and shows how model-estimated risk evolves as new records are added.

> This system is intended for research and educational decision support. It does not replace professional medical judgment or provide a medical diagnosis.

## Current Foundation

- Dataset inspection is documented in `docs/DATASET_ANALYSIS.md` and `docs/DATA_QUALITY_REPORT.md`.
- Supplied CSVs are preserved unchanged in `data/raw/`.
- No cross-file patient linkage is claimed: the attachments contain no reliable patient IDs or dates.
- Synthetic longitudinal sequences are kept separately in `data/synthetic/` for clearly labelled continuity demonstrations.
- React, Vite, and TypeScript frontend foundation is in `frontend/`.
- Flask API health boundary is in `backend/`.

## Data Strategy

`Maternal_Risk.csv` and `Dataset - Updated.csv` are candidate cross-sectional baseline sources with explicit risk labels. `Final.csv` is a wide maternal-child survey snapshot without one authoritative risk target. These datasets are not concatenated. An LSTM must not be described as learning real patient trajectories from these files; sequence demonstrations use explicitly synthetic records until true longitudinal data is available.

## Run the Frontend

```powershell
cd frontend
npm install
npm run dev
```

## Run the Backend

```powershell
cd backend
..\.venv64\Scripts\Activate.ps1
pip install -r requirements.txt
python seed_demo.py
python app.py
```

Recreate the clean synthetic low/moderate/high demonstration set explicitly:

```powershell
python seed_demo.py --reset
```

The API health endpoint is `http://127.0.0.1:5000/api/health`.

Seed the local demonstration database with synthetic records:

```powershell
cd backend
python seed_demo.py
```

Demo login: `demo@maternasense.local` / `demo-password`.

## Analyze and Generate Demo Data

```powershell
python scripts/analyze_datasets.py
python scripts/generate_synthetic_longitudinal.py
```

## Train the Baseline Model

The baseline uses only `Maternal_Risk.csv`, whose supplied target is `RiskLevel`. It removes exact duplicate rows and uses a reproducible row-level split because no patient identifier exists.

```powershell
python -m pip install -r ml/requirements.txt
python ml/train_xgboost.py
python ml/evaluate.py
python ml/train_lstm.py
```

Metrics are written to `ml/artifacts/evaluation.json` and `ml/artifacts/lstm_evaluation.json` only after evaluation actually runs. The LSTM metrics describe synthetic sequence research data, not real linked patient trajectories. These are not clinical validation results.

## Configuration

Copy `.env.example` to `.env` and set a real `DATABASE_URL`, JWT secret, and Supabase values before connecting persistence. `ML_MODE=demo` is the honest default until trained artifacts and evaluation results exist.

## Planned Implementation Phases

1. Database models, migrations, authentication, and seed data.
2. Patient workflow, timeline APIs, and validated forms.
3. Deterministic demo inference, risk history, explanations, and alerts.
4. Dataset preprocessing, XGBoost baseline, evaluation, and synthetic-sequence LSTM demonstration.
5. Reports, architecture documentation, accessibility, security hardening, and tests.
